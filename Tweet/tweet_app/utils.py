import random
from django.core.mail import send_mail
from django.conf import settings
from textwrap import dedent

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    subject='Verify your email address for TweetApp'
    message_body = dedent(f"""
    Hello {email},

    Thank you for signing up with TweetApp — we’re excited to have you join our community!
    To complete your registration and activate your account, please verify your email address.

    Your one-time verification code (OTP) is:
                        
                        
                            {otp}

                        
    This code is valid for the next 2 minutes and can be used only once.
    If you didn’t request this code, please ignore this email — your account will remain inactive until the code is verified.

    Welcome aboard,
    The TweetApp Team
    support@tweetapp.com
    """)
    send_mail(subject, message_body, settings.EMAIL_HOST_USER, [email])