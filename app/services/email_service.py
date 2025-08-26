# # email_service.py

# import os
# from dotenv import load_dotenv
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# load_dotenv()

# conf = ConnectionConfig(
#     MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
#     MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
#     MAIL_FROM = os.getenv("MAIL_FROM"),
#     MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
#     MAIL_SERVER = os.getenv("MAIL_SERVER"),
#     MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true",
#     MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )

# async def send_otp_email(email: str, otp: str):
#     html = f"""
#     <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
#         <h2 style="text-align: center; color: #333;">Password Reset Request</h2>
#         <p>Hello,</p>
#         <p>Your One-Time Password (OTP) for password reset is:</p>
#         <p style="text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0; letter-spacing: 4px; padding: 10px; background-color: #f2f2f2; border-radius: 5px;">
#             {otp}
#         </p>
#         <p>This OTP is valid for <strong>10 minutes</strong>. If you did not request this, please ignore this email.</p>
#     </div>
#     """

#     message = MessageSchema(
#         subject="Your Password Reset OTP",
#         recipients=[email],
#         body=html,
#         subtype="html"
#     )

#     fm = FastMail(conf)
#     await fm.send_message(message)