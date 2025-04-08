import smtplib
from email.mime.text import MIMEText

# Email configuration
smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = 'admin@gmail.com'
sender_password = 'rihxkkzrzoafktkt'  # Use App Password if 2FA is enabled
recipient_email = 'chandan27112004@gmail.com'
subject = 'Test Email'
body = 'This is a test email.'

# Create the email
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = sender_email
msg['To'] = recipient_email

try:
    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Upgrade to a secure connection
    server.login(sender_email, sender_password)  # Log in to the server
    server.sendmail(sender_email, recipient_email, msg.as_string())  # Send the email
    print('Email sent successfully!')
except Exception as e:
    print(f'Error sending email: {e}')
finally:
    server.quit()  # Close the connection
