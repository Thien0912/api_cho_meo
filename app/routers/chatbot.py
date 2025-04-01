from fastapi import APIRouter, HTTPException
from chatbot.services.files_chat_agent import FilesChatAgent
from app.config import settings

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Đảm bảo rằng LLM_NAME được cấu hình chính xác
settings.LLM_NAME = "openai"

# Load FAISS một lần khi server khởi động
VECTOR_STORE_PATH = r"app\python_rag_llm_base_public\data\data_vector"
chat_agent = FilesChatAgent(VECTOR_STORE_PATH).get_workflow().compile()

@router.get("/ask")
def ask_question(question: str):
    """
    Trả lời câu hỏi về giống chó/mèo từ dữ liệu trong FAISS vector store đã có sẵn.
    """
    try:
        # Gọi FilesChatAgent để trả lời câu hỏi
        chat_response = chat_agent.invoke(input={"question": question})

        return {"chat_response": chat_response["generation"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
