from pydantic import BaseModel

class Mail(BaseModel):
    mail_to: str
    mail_title: str
    mail_noi_dung: str
