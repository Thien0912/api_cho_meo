from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
from app.config import settings, refresh_settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])

def load_config(file_path: str) -> dict:
    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        logger.info(f"Đã đọc config từ {file_path}: {config}")
        return config
    except FileNotFoundError:
        logger.error(f"File {file_path} không tồn tại")
        raise Exception(f"File {file_path} không tồn tại")
    except Exception as e:
        logger.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
        raise Exception(f"Lỗi khi đọc file {file_path}: {str(e)}")

def update_env_from_llm_txt():
    try:
        llm_txt_path = os.path.join("utils", "LLM", "llm.txt")
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        config = load_config(llm_txt_path)
        with open(dotenv_path, "w") as env_file:
            for key, value in config.items():
                env_file.write(f"{key}={value}\n")
        # Tải lại .env và làm mới settings
        logger.info(f"Trước khi gọi refresh_settings, SELECTED_LLM: {settings.SELECTED_LLM}")
        refresh_settings()
        from app.config import settings as refreshed_settings
        logger.info(f"Sau khi gọi refresh_settings, SELECTED_LLM: {refreshed_settings.SELECTED_LLM}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật .env từ llm.txt: {str(e)}")
        return False

# Model cho request body của endpoint update
class UpdateConfigRequest(BaseModel):
    KEY_API_GPT: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENAI_LLM: str | None = None
    GOOGLE_LLM: str | None = None
    SELECTED_LLM: str | None = None

@router.get("/config")
async def get_config():

    """
    API để xem các thiết lập môi trường.

    Trả về:
    - `string`: Các thiết lập môi trường như key API GPT, key API Gemini, mô hình của OpenAI, mô hình của Gemini, LLM được sử dụng...
    """
    file_path = os.path.join("utils", "LLM", "llm.txt")
    config = load_config(file_path)
    # Cập nhật .env từ llm.txt
    update_env_from_llm_txt()
    return config

@router.post("/update")
async def update_config(request: UpdateConfigRequest):

    """
    API để cập nhật thiết lập môi trường.

    Tham số:
    - `KEY_API_GPT`: API key của GPT(OpenAI).
    - `GEMINI_API_KEY`: API key của Gemini.
    - `OPENAI_LLM`: Mô hình OpenAI.
    - `GOOGLE_LLM`: Mô hình Gemini.
    - `SELECTED_LLM`: LLM được sử dụng.

    Trả về:
    - `string`: Trả về thiết lập được thay đổi.
    """
    file_path = os.path.join("utils", "LLM", "llm.txt")
    
    logger.info(f"Nhận request cập nhật: {request.dict()}")

    # Đọc config hiện tại từ llm.txt
    try:
        config = load_config(file_path)
    except Exception as e:
        # Tạo config mặc định nếu file không tồn tại
        config = {
            "API_KEY": "default_api_key",
            "KEY_API_GPT": "default_gpt_key",
            "GEMINI_API_KEY": "default_gemini_key",
            "LLM_NAME": "openai",
            "OPENAI_LLM": "gpt-4-turbo",
            "GOOGLE_LLM": "gemini-1.5-flash",
            "NUM_DOC": "5",
            "SELECTED_LLM": "openai"
        }
        logger.info("Sử dụng config mặc định vì llm.txt không tồn tại")

    # Kiểm tra xem có giá trị nào cần cập nhật không
    has_changes = False
    if request.KEY_API_GPT is not None and request.KEY_API_GPT != config.get("KEY_API_GPT"):
        config["KEY_API_GPT"] = request.KEY_API_GPT
        has_changes = True
    if request.GEMINI_API_KEY is not None and request.GEMINI_API_KEY != config.get("GEMINI_API_KEY"):
        config["GEMINI_API_KEY"] = request.GEMINI_API_KEY
        has_changes = True
    if request.OPENAI_LLM is not None and request.OPENAI_LLM != config.get("OPENAI_LLM"):
        config["OPENAI_LLM"] = request.OPENAI_LLM
        has_changes = True
    if request.GOOGLE_LLM is not None and request.GOOGLE_LLM != config.get("GOOGLE_LLM"):
        config["GOOGLE_LLM"] = request.GOOGLE_LLM
        has_changes = True
    if request.SELECTED_LLM is not None and request.SELECTED_LLM != config.get("SELECTED_LLM"):
        if request.SELECTED_LLM not in ["openai", "gemini"]:
            raise HTTPException(status_code=400, detail="SELECTED_LLM phải là 'openai' hoặc 'gemini'")
        config["SELECTED_LLM"] = request.SELECTED_LLM
        has_changes = True

    if not has_changes:
        logger.info("Không có thay đổi để cập nhật")
        return {"message": "Không có thay đổi để cập nhật", "updated_config": config}

    # Ghi lại vào llm.txt
    try:
        with open(file_path, "w") as file:
            for key, value in config.items():
                file.write(f"{key}={value}\n")
        logger.info(f"Đã ghi config mới vào {file_path}: {config}")
    except Exception as e:
        logger.error(f"Lỗi khi ghi vào llm.txt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi ghi vào llm.txt: {str(e)}")

    # Cập nhật .env từ llm.txt
    if not update_env_from_llm_txt():
        logger.error("Lỗi khi cập nhật .env từ llm.txt")
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật .env từ llm.txt")

    return {"message": "Đã cập nhật llm.txt và .env thành công", "updated_config": config}