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

from chatbot.services.files_chat_agent import FilesChatAgent
from app.config import settings

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
        max_tokens=100
    )
    return response.choices[0].message.content

import re

def extract_breed(text: str) -> str:
    if not text:
        return "Không xác định"

    # Loại bỏ các dấu ** (nếu có trong văn bản)
    text = text.replace("**", "")

    # Tách câu đầu tiên trước dấu chấm
    first_sentence = text.split('.')[0].strip()

    # Tách các từ trong câu
    words = first_sentence.split()

    # Bỏ qua từ đầu tiên nếu nó có chữ cái đầu in hoa (Ví dụ: "Đây", "Hình"...)
    if words[0][0].isupper():
        words = words[1:]

    # Lọc các từ có chữ đầu in hoa
    capitalized_words = [word for word in words if word[0].isupper()]

    # Kết hợp các từ thành tên giống
    breed = " ".join(capitalized_words)

    # Kiểm tra nếu giống có từ trong danh sách blacklist
    blacklist = {
        "ngoại hình", "tính cách", "sức khỏe", "chăm sóc", "kết luận", "tổng quan", "giới thiệu", "dinh dưỡng",
        "huấn luyện", "vận động", "chải lông", "tắm", "đầu", "mắt", "tai", "mõm", "chân", "đuôi", "lông", "màu lông",
        "kích thước", "tuổi thọ", "bệnh thường gặp", "tập luyện", "đặc điểm", "hình dáng", "tập tính", "hành vi",
        "ưu điểm", "nhược điểm", "cách nuôi", "thức ăn", "thể chất", "hình thể", "trọng lượng", "chiều cao",
        "đặc trưng", "đặc điểm nhận dạng", "thông tin thêm", "phân tích", "phân loại", "tương tác", "thân thiện", 
        "quan sát", "di truyền", "đặc điểm sinh học", "sinh lý", "giá cả", "môi trường sống", "tập quán", "bộ lông",
        "răng", "thân hình", "mô tả", "xuất xứ", "orange and white", "black and white", "liver and white", "giống"
    }

    if breed.lower() in blacklist:
        return "Không xác định"
    
    # Trả về giống tìm được nếu đủ điều kiện
    return breed if 3 <= len(breed) <= 50 else "Không xác định"

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    vector_store_path: str = Query(..., description="(Hiện tại không dùng FAISS)")
):
    try:
        contents = await file.read()
        breed_list = load_breed_list()
        responses = {}

        # Dự đoán bằng AI model
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

        # Dùng Gemini để mô tả và xác nhận giống
        try:
            prompt = "Hãy mô tả chi tiết và đầy đủ về giống chó hoặc mèo này."
            description = get_gemini_image_response(contents, prompt)
            detected_breed = extract_breed(description)  # Gọi hàm mới để trích xuất giống
            match_result = "ĐÚNG" if detected_breed == predicted_breed else "SAI"
            responses["gemini"] = {
                "match": match_result,
                "description": description,
                "detected_breed": detected_breed
            }

            # Trả kết quả final là Gemini luôn
            responses["final"] = {
                "match": match_result,
                "description": description,
                "detected_breed": detected_breed
            }

        except Exception as e:
            responses["gemini"] = {"error": str(e)}
            responses["final"] = {"error": str(e)}

        return {
            "predicted_breed": predicted_breed,
            "responses": responses
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý ảnh: {str(e)}")
