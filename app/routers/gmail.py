from app.models.mail import Mail

class Gmail:
    @staticmethod
    def send_email(mail: Mail):
        to_email = mail.mail_to
        subject = mail.mail_title
        body = mail.mail_noi_dung
        # Code gửi email ở đây
