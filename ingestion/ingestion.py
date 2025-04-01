import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingestion.service_manager import ServiceManager
from langchain_community.vectorstores import FAISS

class Ingestion:
    """
    Lớp thực hiện quá trình ingest dữ liệu từ các tệp văn bản vào vector store.
    """

    def __init__(self, embedding_model_name: str):
        """
        Khởi tạo Ingestion với mô hình embedding cụ thể.

        Args:
            embedding_model_name (str): Tên của mô hình embedding được sử dụng.
        """
        self.chunk_size = 2000  # Kích thước đoạn văn bản tối đa khi chia nhỏ
        self.chunk_overlap = int(self.chunk_size * 0.2)  # Độ chồng chéo giữa các đoạn văn bản
        self.embedding_model = ServiceManager().get_embedding_model(embedding_model_name)

    def ingestion_folder(self, path_input_folder: str, path_vector_store: str):
        """
        Đọc tất cả các tệp văn bản trong thư mục, xử lý và lưu vào vector store.
        
        Args:
            path_input_folder (str): Đường dẫn thư mục chứa các file văn bản.
            path_vector_store (str): Đường dẫn để lưu vector store.
        """
        all_docs = []  # Danh sách lưu trữ toàn bộ tài liệu

        # Duyệt qua toàn bộ thư mục và tệp tin
        for root, _, files in os.walk(path_input_folder):
            for file in files:
                if file.endswith('.txt'):  # Xử lý tệp văn bản .txt
                    file_path = os.path.join(root, file)
                    print(f"Đang xử lý file: {file_path}")
                    docs = self.process_txt(file_path)
                    all_docs.extend(docs)

        # Kiểm tra xem có tài liệu nào không
        if not all_docs:
            raise ValueError("Không có tài liệu nào được xử lý!")

        # Tạo vector store từ các đoạn văn bản đã xử lý
        vectorstore = FAISS.from_documents(all_docs, self.embedding_model)
        vectorstore.save_local(path_vector_store)
        print(f"Đã tạo và lưu chỉ mục vào '{path_vector_store}'")

    def process_txt(self, path_file: str):
        """
        Xử lý tệp văn bản, làm sạch và chia nhỏ thành các đoạn văn bản có kích thước phù hợp.

        Args:
            path_file (str): Đường dẫn đến tệp văn bản cần xử lý.

        Returns:
            list: Danh sách các đoạn văn bản đã được xử lý.
        """
        # Đọc nội dung tệp văn bản
        with open(path_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Làm sạch nội dung văn bản
        content = self.clean_text(content)

        # Tạo bộ chia nhỏ văn bản
        text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        # Chia nhỏ văn bản thành các đoạn
        docs = text_splitter.create_documents([content])

        # Thêm thông tin metadata cho từng đoạn văn bản
        for idx, doc in enumerate(docs):
            doc.metadata["file_name"] = os.path.basename(path_file)
            doc.metadata["chunk_size"] = self.chunk_size
            doc.metadata["index"] = idx

        return docs

    def clean_text(self, text):
        """
        Làm sạch văn bản: Xóa ký tự đặc biệt, khoảng trắng thừa và các ký tự không mong muốn.

        Args:
            text (str): Nội dung văn bản cần làm sạch.

        Returns:
            str: Văn bản đã được làm sạch.
        """
        text = re.sub(r'\n+', '\n', text)  # Xóa dòng trống thừa
        text = re.sub(r'[^\w\s.,!?;:]', '', text)  # Chỉ giữ lại ký tự chữ, số và dấu câu
        text = text.strip()  # Xóa khoảng trắng thừa đầu và cuối câu
        return text

if __name__ == "__main__":
    data_dir = 'data/data_in/'
    vector_store_path = 'data/data_vector/'

    # Khởi tạo và chạy Ingestion
    ingestion = Ingestion(embedding_model_name='openai')
    ingestion.ingestion_folder(data_dir, vector_store_path)
