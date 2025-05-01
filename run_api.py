from app.main import app
from app.routers.config import update_env_from_llm_txt
import uvicorn

# Cập nhật .env từ llm.txt khi khởi động
update_env_from_llm_txt()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=55010, workers=1)