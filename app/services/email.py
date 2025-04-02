import os
from email.message import EmailMessage
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import aiosmtplib

# Load environment variables
otp_db = {}

# SMTP Configuration
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USERNAME)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Use 465 for SSL or 587 for TLS

# Function to validate email format
def is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False

# Asynchronous function to send OTP email using aiosmtplib
async def send_otp_email(email: str, user_name: str, otp: str) -> dict:
    if not is_valid_email(email):
        print("Invalid email address.")
        return {"error": "Invalid email address"}

    subject = "Your OTP for Secure Access"
    body = f"""\
Dear {user_name},

Your OTP is: {otp}.

This OTP is valid for 5 minutes and can only be used once.
Please do not share this code with anyone.

If you did not request this code, please contact our support team immediately at {os.getenv("SUPPORT_EMAIL", "Your Email Detail")}.

Thank you for using {os.getenv("APP_NAME", "Your Company Name")}!

Best regards,
{os.getenv("APP_NAME", "Your Company Name")}
"""

    # Store OTP in the dictionary (for validation)
    otp_db[email] = {
        "otp": str(otp),
        "expires_at": datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 minutes
    }

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = email

        # Send email using aiosmtplib
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT) as server:
            await server.login(SMTP_USERNAME, SMTP_PASSWORD)  # Login
            await server.send_message(msg)  # Send email

        print("OTP email sent successfully!")
        return {"message": "OTP email sent successfully!"}

    except aiosmtplib.errors.SMTPAuthenticationError:
        print("Authentication error.")
        return {"error": "SMTP Authentication failed"}

    except aiosmtplib.errors.SMTPConnectError:
        print("Connection error.")
        return {"error": "Failed to connect to SMTP server"}

    except Exception as e:
        print(f"Error sending email: {e}")
        return {"error": str(e)}
