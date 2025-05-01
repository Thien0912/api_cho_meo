from pydantic import BaseModel
from typing import Optional

class FileUpload(BaseModel):
    filename: str
    download_url: str
    custom_filename: Optional[str] = None
    accuracy: Optional[float] = None
    labels_csv: Optional[str] = None