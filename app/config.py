from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logging
import importlib

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đường dẫn đến .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')

# Tải file .env nếu tồn tại
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    API_KEY: str = "default_api_key"
    KEY_API_GPT: str = "default_gpt_key"
    GEMINI_API_KEY: str = "default_gemini_key"
    LLM_NAME: str = "openai"
    OPENAI_LLM: str = "gpt-4-turbo"
    GOOGLE_LLM: str = "gemini-1.5-flash"
    NUM_DOC: str = "5"
    SELECTED_LLM: str = "openai"
    DIR_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    class Config:
        env_file = dotenv_path
        env_file_encoding = "utf-8"
        case_sensitive = True

# Tạo một thể hiện của Settings
settings = Settings()

# Hàm làm mới settings
def refresh_settings():
    global settings
    load_dotenv(dotenv_path=dotenv_path, override=True)
    settings = Settings()
    logger.info(f"Đã làm mới settings, SELECTED_LLM: {settings.SELECTED_LLM}")
    # Reload các module liên quan để đồng bộ settings
    import app.config
    importlib.reload(app.config)
    logger.info(f"Sau khi reload app.config, SELECTED_LLM: {app.config.settings.SELECTED_LLM}")
    try:
        import app.routers.config
        importlib.reload(app.routers.config)
        logger.info(f"Sau khi reload app.routers.config, SELECTED_LLM: {app.routers.config.settings.SELECTED_LLM}")
    except AttributeError:
        logger.error("Không thể reload app.routers.config hoặc settings không tồn tại")
    try:
        import app.routers.chatbot
        importlib.reload(app.routers.chatbot)
        logger.info(f"Sau khi reload app.routers.chatbot, SELECTED_LLM: {app.routers.chatbot.settings.SELECTED_LLM}")
    except AttributeError:
        logger.error("Không thể reload app.routers.chatbot hoặc settings không tồn tại")