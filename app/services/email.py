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
async def send_otp_email(email: EmailStr, otp: str):
    subject = "Your OTP Code for AI Interview App"
    body = f"Your OTP code for Interview Genie is: {otp}. It is valid for 5 minutes."

    #  it store the otp and expiration time in the  otp_db (in database)
    otp_db[email] = {
        "otp": str(otp),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)  # OTP expires in 10 minutes
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
    except Exception as e:
        print(f"Error sending email: {e}")
