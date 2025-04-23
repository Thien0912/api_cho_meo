from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from uuid import uuid4
import os
import shutil
import json
from datetime import datetime

from app.models.file_upload import FileUpload
from app.security.security import get_api_key
from app.config import settings

# Tạo router
router = APIRouter(prefix="/upload-file", tags=["file-upload"])

# Thư mục lưu file thường và mô hình AI
DOWNLOAD_FOLDER = os.path.join(settings.DIR_ROOT, "utils", "download")
MODEL_FOLDER = os.path.join(settings.DIR_ROOT, "utils", "models")
CURRENT_MODEL_PATH = os.path.join(MODEL_FOLDER, "current_model.txt")
CURRENT_LABEL_PATH = os.path.join(MODEL_FOLDER, "current_labels.txt")
MODEL_ACCURACY_FILE = os.path.join(MODEL_FOLDER, "model_accuracies.json")

# Đảm bảo thư mục tồn tại
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

# Đảm bảo file chứa độ chính xác tồn tại
if not os.path.exists(MODEL_ACCURACY_FILE):
    with open(MODEL_ACCURACY_FILE, "w") as f:
        json.dump({}, f)

# Hàm xử lý tên file an toàn
def sanitize_filename(filename: str) -> str:
    return filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

# Hàm lưu độ chính xác vào file
def save_model_accuracy(filename: str, accuracy: float, upload_date: str):
    with open(MODEL_ACCURACY_FILE, "r") as f:
        model_accuracies = json.load(f)

    model_accuracies[filename] = {"accuracy": accuracy, "upload_date": upload_date}

    with open(MODEL_ACCURACY_FILE, "w") as f:
        json.dump(model_accuracies, f)

# Hàm tải lên file và lưu độ chính xác
@router.post("/upload/", response_model=FileUpload)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    custom_filename: str = Form(...),
    accuracy: float = Form(...),
    labels_csv: UploadFile = File(None),  # File CSV chứa nhãn nếu có
    api_key: str = get_api_key,
):
    file_extension = os.path.splitext(file.filename)[1]

    # Làm sạch tên file
    safe_name = sanitize_filename(custom_filename)
    if not safe_name.endswith(file_extension):
        safe_name += file_extension

    # Xác định đường dẫn lưu file
    if file_extension == ".keras":
        file_path = os.path.join(MODEL_FOLDER, safe_name)
    else:
        file_path = os.path.join(DOWNLOAD_FOLDER, safe_name)

    # Ghi file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Nếu có file nhãn kèm theo thì lưu với tên tương ứng
    if labels_csv:
        label_path = os.path.join(MODEL_FOLDER, safe_name.replace(".keras", "_labels.csv"))
        with open(label_path, "wb") as label_buffer:
            shutil.copyfileobj(labels_csv.file, label_buffer)

    # Lấy ngày giờ upload hiện tại
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Lưu độ chính xác và ngày upload vào file
    save_model_accuracy(safe_name, accuracy, upload_date)

    return FileUpload(
        filename=safe_name,
        download_url=f"/upload-file/download/{safe_name}",
        mail=None
    )

@router.get("/models/")
def list_uploaded_models():
    files = [f for f in os.listdir(MODEL_FOLDER) if f.endswith(".keras")]
    with open(MODEL_ACCURACY_FILE, "r") as f:
        model_accuracies = json.load(f)
    models_with_accuracy = [
        {
            "filename": f,
            "accuracy": model_accuracies.get(f, {}).get("accuracy", "N/A"),
            "upload_date": model_accuracies.get(f, {}).get("upload_date", "N/A")
        } for f in files
    ]
    return {"models": models_with_accuracy}

@router.post("/models/select/")
def select_model(filename: str = Form(...)):
    model_path = os.path.join(MODEL_FOLDER, filename)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model not found")

    with open(CURRENT_MODEL_PATH, "w") as f:
        f.write(filename)

    label_path = filename.replace(".keras", "_labels.csv")
    label_full_path = os.path.join(MODEL_FOLDER, label_path)
    if os.path.exists(label_full_path):
        with open(CURRENT_LABEL_PATH, "w") as f:
            f.write(label_path)

    return {"message": f"Model {filename} và file nhãn tương ứng đã được chọn"}

@router.get("/models/current/")
def get_current_model():
    current = {}
    if os.path.exists(CURRENT_MODEL_PATH):
        with open(CURRENT_MODEL_PATH, "r") as f:
            current["model"] = f.read().strip()
    if os.path.exists(CURRENT_LABEL_PATH):
        with open(CURRENT_LABEL_PATH, "r") as f:
            current["labels"] = f.read().strip()
    return current

@router.get("/models/{filename}/labels")
def get_model_labels(filename: str):
    label_path = os.path.join(MODEL_FOLDER, filename.replace(".keras", "_labels.csv"))
    if not os.path.exists(label_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file nhãn cho mô hình này")
    return FileResponse(label_path, filename=os.path.basename(label_path))

@router.delete("/models/{filename}")
def delete_model(filename: str):
    model_path = os.path.join(MODEL_FOLDER, filename)
    label_path = os.path.join(MODEL_FOLDER, filename.replace(".keras", "_labels.csv"))

    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model không tồn tại")

    with open(CURRENT_MODEL_PATH, "r") as f:
        current_model = f.read().strip()

    if current_model == filename:
        with open(CURRENT_MODEL_PATH, "w") as f:
            f.write("")
        if os.path.exists(CURRENT_LABEL_PATH):
            os.remove(CURRENT_LABEL_PATH)

    os.remove(model_path)
    if os.path.exists(label_path):
        os.remove(label_path)

    with open(MODEL_ACCURACY_FILE, "r") as f:
        model_accuracies = json.load(f)
    if filename in model_accuracies:
        del model_accuracies[filename]
    with open(MODEL_ACCURACY_FILE, "w") as f:
        json.dump(model_accuracies, f)

    return {"message": f"Đã xóa mô hình {filename} và file nhãn kèm theo (nếu có)"}