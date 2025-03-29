from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure FastAPI Mail
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USERNAME"),  # Use the environment variable
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),  # Use the environment variable
    MAIL_FROM=os.getenv("EMAIL_FROM"),  # Use the environment variable
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


async def send_otp_email(email: EmailStr, otp: str):
    subject = "Your OTP Code for AI Interview App"
    body = f"Your OTP code is: {otp}. It is valid for 10 minutes."

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="plain"
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Error sending email: {e}")
