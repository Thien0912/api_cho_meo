from pydantic import BaseModel

class Mail(BaseModel):
    mail_to: str
    subject: str
    body: str

class Gmail:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        mail = Mail(
            mail_to=to_email,
            subject=subject,
            body=body
        )
        # Xử lý gửi email ở đây
