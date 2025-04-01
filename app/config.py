import os
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
load_dotenv()

class Settings:
    """
    Lớp cấu hình chung cho ứng dụng, quản lý các biến môi trường.
    
    Attributes:
        DIR_ROOT (str): Đường dẫn thư mục gốc của dự án.
    """

    # Cấu hình LLM
    KEY_API_GPT = os.environ["KEY_API_GPT"]
    NUM_DOC = os.environ["NUM_DOC"]
    LLM_NAME = os.environ["LLM_NAME"]
    OPENAI_LLM = os.environ["OPENAI_LLM"]

    # Cấu hình chung cho API
    API_KEY = os.environ["API_KEY"]
    DIR_ROOT = os.path.dirname(os.path.abspath(".env"))

# Tạo một thể hiện của lớp Settings để sử dụng trong ứng dụng
settings = Settings()
