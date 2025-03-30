from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
otp_db = {}
# FastAPI Mail Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


# Async Email Sending Function
async def send_otp_email(email: EmailStr, user_name: str, otp: str):
    subject = "Your OTP for Secure Access"

    body = f"""\
    Dear {user_name},

    Your OTP is: {otp}.

    This OTP is valid for 5 minutes and can only be used once.
    Please do not share this code with anyone.

    If you did not request this code, please contact our support
    team immediately at {os.getenv("SUPPORT_EMAIL", "chandan18305@gmail.com")}.

    Thank you for using {os.getenv("APP_NAME", "Your Company Name")}!

    Best regards,
    {os.getenv("APP_NAME", "Your Company Name")}
    """
    #  it store the otp and expiration time in the  otp_db (in database)
    otp_db[email] = {
        "otp": str(otp),
        "expires_at": datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 minutes
    }

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="plain"
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print("OTP email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
