import base64
import os
import io
import csv
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import google.generativeai as genai
from openai import OpenAI
import re
import logging
from chatbot.services.files_chat_agent import FilesChatAgent
from app.config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Cấu hình Gemini + OpenAI
genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_vision_model = genai.GenerativeModel(settings.GOOGLE_LLM)
openai_client = OpenAI(api_key=settings.KEY_API_GPT)

# Paths
base_dir = settings.DIR_ROOT
model_folder = os.path.join(base_dir, "utils", "models")
current_model_file = os.path.join(model_folder, "current_model.txt")
current_labels_file = os.path.join(model_folder, "current_labels.txt")

def load_current_model():
    if not os.path.exists(current_model_file):
        raise HTTPException(status_code=404, detail="Chưa có model nào được chọn.")
    with open(current_model_file, "r") as f:
        model_filename = f.read().strip()
    model_path = os.path.join(model_folder, model_filename)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"Model '{model_filename}' không tồn tại.")
    return tf.keras.models.load_model(model_path)

def load_breed_list():
    if not os.path.exists(current_labels_file):
        raise HTTPException(status_code=404, detail="Chưa chọn file label tương ứng.")
    with open(current_labels_file, "r", encoding="utf-8") as f:
        label_filename = f.read().strip()
    label_path = os.path.join(model_folder, label_filename)
    if not os.path.exists(label_path):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file label: {label_filename}")
    with open(label_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        return [row[0] for row in reader]

def get_gemini_image_response(image_bytes: bytes, prompt: str):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return gemini_vision_model.generate_content([prompt, image]).text

def get_openai_image_response(image_bytes: bytes, prompt: str):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    response = openai_client.chat.completions.create(
        model=settings.OPENAI_LLM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }],
        max_tokens=1000
    )
    return response.choices[0].message.content

def extract_breed(text: str) -> str:
    if not text:
        return "Không xác định"

    # Loại bỏ các dấu ** (nếu có trong văn bản)
    text = text.replace("**", "")

    # Tách câu đầu tiên trước dấu chấm hoặc dấu phẩy
    first_sentence = re.split(r'[.,:]', text)[0].strip()

    # Tách các từ, bao gồm cả nội dung trong ngoặc
    # Sử dụng regex để giữ các từ trong ngoặc như một đơn vị
    words = re.findall(r'\([^)]+\)|[\w\-]+', first_sentence)

    # Bỏ qua từ đầu tiên nếu nó có chữ cái đầu in hoa
    if words and words[0][0].isupper():
        words = words[1:]

    # Lọc các từ có chữ cái đầu in hoa
    capitalized_words = [word for word in words if word[0].isupper()]

    # Kết hợp các từ thành tên giống
    breed = " ".join(capitalized_words)

    # Trả về giống tìm được nếu đủ điều kiện
    return breed if 3 <= len(breed) <= 50 else "Không xác định"

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(..., description="Tải ảnh chó/mèo muốn nhận diện"),
    vector_store_path: str = Query(..., description="Đường dẫn FAISS (VD: app/utils/data/data_vector)"),
    use_faiss: bool = Query(True, description="Có sử dụng FAISS hay không")
):
    """
    API dùng AI để nhận diện giống chó/mèo.

    Tham số:
    - `vector_store_path`: Đường dẫn FAISS.
    - `use_faiss`: Có sử dụng FAISS hay không.

    Trả về:
    - `dict`: Giống mà AI nhận diện, giống mà LLM nhận diện, thông tin về giống...
    """
    try:
        contents = await file.read()
        breed_list = load_breed_list()
        responses = {}

        # Dự đoán giống sử dụng mô hình AI
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img = img.resize((256, 256))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
        model = load_current_model()
        prediction = model.predict(img_array)
        predicted_class_index = np.argmax(prediction[0])
        predicted_breed = breed_list[predicted_class_index]
        responses["model"] = {"answer": f"AI model dự đoán: {predicted_breed}"}

        # Xử lý FAISS nếu được yêu cầu
        if use_faiss:
            if os.path.exists(vector_store_path):
                try:
                    faiss_agent = FilesChatAgent(vector_store_path)
                    faiss_response = faiss_agent.get_workflow().compile().invoke(
                        input={"question": f"Thông tin về giống {predicted_breed}"}
                    )
                    faiss_english = faiss_response.get("generation", "")
                    faiss_translated = gemini_vision_model.generate_content([
                        f"Dưới đây là thông tin bằng tiếng Anh về giống {predicted_breed}. Hãy dịch sang tiếng Việt mạch lạc, dễ hiểu:\n\n{faiss_english}"
                    ]).text
                    responses["faiss"] = {
                        "answer": faiss_translated,
                        "sources": [doc.metadata.get("file_name", "unknown") for doc in faiss_response.get("documents", [])]
                    }
                except Exception as e:
                    responses["faiss"] = {"error": f"Không thể xử lý FAISS: {str(e)}"}
            else:
                responses["faiss"] = {"error": "Không tìm thấy FAISS vector store."}

        # Lựa chọn LLM dựa trên cấu hình
        logger.info(f"SELECTED_LLM hiện tại: {settings.SELECTED_LLM}")
        selected_llm = settings.SELECTED_LLM
        if selected_llm not in ["openai", "gemini"]:
            raise HTTPException(status_code=400, detail=f"SELECTED_LLM không hợp lệ: {selected_llm}")

        responses[selected_llm] = {}
        try:
            prompt = (
                "Cung cấp mô tả chi tiết về giống chó/mèo này, bao gồm các đặc điểm ngoại hình, tính cách, nguồn gốc, "
                "và các thông tin liên quan như kích thước, màu lông, môi trường sống phù hợp, và các đặc trưng nổi bật. "
                "Không đề cập đến việc xem hoặc phân tích hình ảnh."
            )
            description = (
                get_openai_image_response(contents, prompt) if selected_llm == "openai"
                else get_gemini_image_response(contents, prompt)
            )
            detected_breed = extract_breed(description)
            detected_words = set(detected_breed.lower().split())
            predicted_words = set(predicted_breed.lower().split())
            match_result = "ĐÚNG" if detected_words & predicted_words else "SAI"
            responses[selected_llm] = {
                "match": match_result,
                "description": description,
                "detected_breed": detected_breed or "Không xác định"
            }
        except Exception as e:
            responses[selected_llm] = {"error": f"Lỗi khi gọi {selected_llm}: {str(e)}"}

        # Đặt output cuối cùng
        if "error" in responses[selected_llm]:
            responses["final"] = {"error": responses[selected_llm]["error"]}
        else:
            if use_faiss and "faiss" in responses and "error" not in responses["faiss"] and responses[selected_llm]["match"] == "ĐÚNG":
                # Nếu match là ĐÚNG và FAISS khả dụng, sử dụng FAISS
                responses["final"] = {
                    "answer": responses["faiss"]["answer"],
                    "sources": responses["faiss"]["sources"],
                    "detected_breed": responses[selected_llm]["detected_breed"],
                    "match": responses[selected_llm]["match"]
                }
            else:
                # Nếu match là SAI hoặc FAISS không khả dụng, sử dụng LLM
                responses["final"] = {
                    "answer": responses[selected_llm]["description"],
                    "detected_breed": responses[selected_llm]["detected_breed"],
                    "match": responses[selected_llm]["match"]
                }

        return {
            "predicted_breed": predicted_breed,
            "responses": responses
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý ảnh: {str(e)}")