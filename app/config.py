import os
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    # Thiết lập các biến môi trường
    API_KEY = os.environ["API_KEY"]
    
    KEY_API_GPT = os.environ["KEY_API_GPT"]
    NUM_DOC = os.environ["NUM_DOC"]
    LLM_NAME = os.environ["LLM_NAME"]
    OPENAI_LLM = os.environ["OPENAI_LLM"]
    GOOGLE_LLM = os.environ["GOOGLE_LLM"]
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    CLARIFAI_USER_ID = os.environ["CLARIFAI_USER_ID"]
    CLARIFAI_APP_ID = os.environ["CLARIFAI_APP_ID"]
    CLARIFAI_API_KEY = os.environ["CLARIFAI_API_KEY"]
    CLARIFAI_MODEL_ID = os.environ["CLARIFAI_MODEL_ID"]

    # Đường dẫn gốc của dự án
    DIR_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Tạo một thể hiện của lớp Settings để sử dụng trong ứng dụng
settings = Settings()
