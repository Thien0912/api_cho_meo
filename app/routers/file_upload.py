from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import FileResponse
from uuid import uuid4
import os
import shutil
from fastapi import Request
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
CURRENT_APK_PATH = os.path.join(DOWNLOAD_FOLDER, "current_apk.txt")

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
    file: UploadFile = File(..., description="Chọn file mô hình AI (.keras)"),
    custom_filename: str = Form(..., description="Tên mô hình AI"),
    accuracy: float = Form(..., description="Độ chính xác"),
    labels_csv: UploadFile = File(None, description="Chọn file label cho mô hình AI (.csv)"),
    api_key: str = get_api_key,
):
    """
    API để upload mô hình AI.

    Tham số:
    - `file`: Tệp mô hình (keras).
    - `custom_filename`: Tên mô hình.
    - `accuracy`: Độ chính xác.
    - `labels_csv`: File nhãn (csv).

    Trả về:
    - `filename`: Tên file đã lưu.
    - `download_url`: Đường dẫn tải file.
    - `custom_filename`: Tên tùy chỉnh.
    - `accuracy`: Độ chính xác.
    - `labels_csv`: Tên file nhãn (nếu có).
    """
    try:
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
        label_filename = None
        if labels_csv:
            label_filename = safe_name.replace(".keras", "_labels.csv")
            label_path = os.path.join(MODEL_FOLDER, label_filename)
            with open(label_path, "wb") as label_buffer:
                shutil.copyfileobj(labels_csv.file, label_buffer)

        # Lấy ngày giờ upload hiện tại
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Lưu độ chính xác và ngày upload vào file
        save_model_accuracy(safe_name, accuracy, upload_date)

        # Tạo download_url
        download_url = f"/files/{safe_name}"

        return FileUpload(
            filename=safe_name,
            download_url=download_url,
            custom_filename=custom_filename,
            accuracy=accuracy,
            labels_csv=label_filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý file: {str(e)}")
    
# Hàm tải lên tệp APK
@router.post("/upload-apk/")
async def upload_apk(
    request: Request,
    file: UploadFile = File(..., description="Chọn tệp APK (.apk)"),
    custom_filename: str = Form(..., description="Tên tùy chỉnh cho tệp APK"),
    api_key: str = get_api_key,
):
    """
    API để upload tệp APK.

    Tham số:
    - `file`: Tệp APK (.apk).
    - `custom_filename`: Tên tùy chỉnh cho tệp APK.

    Trả về:
    - `custom_filename`: Tên tùy chỉnh của tệp APK.
    - `filename`: Tên tệp thực tế được lưu.
    - `upload_date`: Ngày giờ upload.
    """
    # Kiểm tra định dạng tệp
    if not file.filename.endswith(".apk"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận tệp .apk")

    # Làm sạch tên file
    safe_name = sanitize_filename(custom_filename)
    if not safe_name.endswith(".apk"):
        safe_name += ".apk"

    # Đường dẫn lưu file
    file_path = os.path.join(DOWNLOAD_FOLDER, safe_name)

    # Ghi file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Lấy ngày giờ upload
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "custom_filename": custom_filename,
        "filename": safe_name,
        "upload_date": upload_date
    }

@router.get("/apks/current/")
async def get_current_apk(api_key: str = get_api_key):
    """
    API để xem tệp APK hiện tại (được chọn để sử dụng).

    Trả về:
    - `apk`: Tên tệp APK hiện tại (nếu có).
    - `upload_date`: Ngày tải lên của APK hiện tại (nếu có).
    """
    if os.path.exists(CURRENT_APK_PATH):
        with open(CURRENT_APK_PATH, "r") as f:
            current_apk = f.read().strip()
        if current_apk:
            apk_path = os.path.join(DOWNLOAD_FOLDER, current_apk)
            if os.path.exists(apk_path):
                upload_date = datetime.fromtimestamp(os.path.getmtime(apk_path)).strftime("%Y-%m-%d %H:%M:%S")
                return {"apk": current_apk, "upload_date": upload_date}
    return {"apk": "", "upload_date": ""}

# Hiển thị danh sách các tệp APK đã upload
@router.get("/apks/")
async def list_uploaded_apks():
    """
    API để xem danh sách các tệsse APK đã upload.

    Trả về:
    - `apks`: Danh sách các tệp APK với tên tệp và ngày upload.
    """
    files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith(".apk")]
    apks = [
        {
            "filename": f,
            "upload_date": datetime.fromtimestamp(os.path.getmtime(os.path.join(DOWNLOAD_FOLDER, f))).strftime("%Y-%m-%d %H:%M:%S")
        } for f in files
    ]
    return {"apks": apks}

# Chọn tệp APK để sử dụng
@router.post("/apks/select/")
async def select_apk(
    filename: str = Form(..., description="Tên tệp APK muốn sử dụng"),
    api_key: str = get_api_key,
):
    """
    API để chọn tệp APK muốn sử dụng.

    Tham số:
    - `filename`: Tên tệp APK.

    Trả về:
    - `message`: Xác nhận tệp APK đã được chọn.
    """
    apk_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(apk_path) or not filename.endswith(".apk"):
        raise HTTPException(status_code=404, detail="Tệp APK không tồn tại hoặc không hợp lệ")

    with open(CURRENT_APK_PATH, "w") as f:
        f.write(filename)

    return {"message": f"Tệp APK {filename} đã được chọn"}

@router.get("/apks/current/download/")
async def download_current_apk(api_key: str = None, request: Request = None):

    """
    API để tải về APK đang sử dụng.

    Tham số:
    - `api_key`: Fast API key.

    Trả về:
    - `string`: Đường dẫn tải về file APK và thông tin của file APK.
    """
    # Kiểm tra API key từ query parameter
    if api_key != settings.API_KEY:
        # Nếu không có trong query, thử lấy từ header
        api_key_header = request.headers.get("API-Key") if request else None
        if api_key_header != settings.API_KEY:
            raise HTTPException(status_code=403, detail="Could not validate API Key")

    # Đọc tên file APK hiện tại từ current_apk.txt
    if not os.path.exists(CURRENT_APK_PATH):
        raise HTTPException(status_code=404, detail="No APK selected")
    
    with open(CURRENT_APK_PATH, "r") as f:
        current_apk = f.read().strip()
    
    if not current_apk:
        raise HTTPException(status_code=404, detail="No APK selected")
    
    # Tạo đường dẫn đến file APK
    file_path = os.path.join(DOWNLOAD_FOLDER, current_apk)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="APK file not found")
    
    # Trả về file APK để tải
    return FileResponse(
        path=file_path,
        filename=current_apk,
        media_type="application/vnd.android.package-archive"
    )

@router.get("/models/")
async def list_uploaded_models():
    """
    API để xem các mô hình đã upload.

    Trả về:
    - `string`: Tên mô hình, độ chính xác, ngày upload.
    """
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
def select_model(
    filename: str = Form(..., description="Tên mô hình AI muốn sử dụng")
):
    """
    API chọn mô hình AI muốn sử dụng.

    Tham số:
    - `filename`: Tên mô hình.

    Trả về:
    - `string`: Tên mô hình và tên file label được sử dụng.
    """
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
    """
    API xem mô hình AI được sử dụng.

    Trả về:
    - `string`: Tên mô hình và tên file label được sử dụng.
    """
    current = {}
    if os.path.exists(CURRENT_MODEL_PATH):
        with open(CURRENT_MODEL_PATH, "r") as f:
            current["model"] = f.read().strip()
    if os.path.exists(CURRENT_LABEL_PATH):
        with open(CURRENT_LABEL_PATH, "r") as f:
            current["labels"] = f.read().strip()
    return current

@router.get("/models/{filename}/labels")
def get_model_labels(
    filename: str = Path(..., description="Tên mô hình AI muốn xem label")
):
    """
    API xem file label của một mô hình AI.

    Trả về:
    - `string`: Đường dẫn tải file label của mô hình AI.
    """
    label_path = os.path.join(MODEL_FOLDER, filename.replace(".keras", "_labels.csv"))
    if not os.path.exists(label_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file nhãn cho mô hình này")
    return FileResponse(label_path, filename=os.path.basename(label_path))

@router.delete("/models/{filename}")
def delete_model(
    filename: str = Path(..., description="Tên tệp mô hình muốn xóa")
):
    """
    API xóa một mô hình AI.

    Tham số:
    - `filename`: Tên mô hình muốn xóa.

    Trả về:
    - `string`: Tên mô hình AI đã xóa.
    """
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

# Thêm router xóa APK
@router.delete("/apks/{filename}")
async def delete_apk(
    filename: str = Path(..., description="Tên tệp APK muốn xóa"),
    api_key: str = get_api_key,
):
    """
    API để xóa một tệp APK.

    Tham số:
    - `filename`: Tên tệp APK muốn xóa.

    Trả về:
    - `message`: Thông báo xác nhận xóa tệp APK.
    """
    apk_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(apk_path) or not filename.endswith(".apk"):
        raise HTTPException(status_code=404, detail="Tệp APK không tồn tại hoặc không hợp lệ")

    # Kiểm tra nếu APK đang được chọn
    if os.path.exists(CURRENT_APK_PATH):
        with open(CURRENT_APK_PATH, "r") as f:
            current_apk = f.read().strip()
        if current_apk == filename:
            with open(CURRENT_APK_PATH, "w") as f:
                f.write("")  # Xóa thông tin APK hiện tại

    # Xóa tệp APK
    os.remove(apk_path)

    return {"message": f"Tệp APK {filename} đã được xóa"}