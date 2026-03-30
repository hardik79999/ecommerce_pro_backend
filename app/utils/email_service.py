import random
from datetime import datetime, timedelta
from app.models import OTP
from app.extensions import db

def generate_and_send_otp(user, action_type):
    # 6-digit random OTP generate karna
    otp_code = str(random.randint(100000, 999999))
    
    # OTP 10 minute me expire ho jayega
    expires = datetime.utcnow() + timedelta(minutes=10)

    new_otp = OTP(
        user_id=user.id,
        otp_code=otp_code,
        action=action_type,
        expires_at=expires
    )
    db.session.add(new_otp)
    
    # Asli project me yahan Flask-Mail ka code aata hai.
    # Abhi testing ke liye hum ise terminal me print kar rahe hain:
    print(f"\n{'='*50}")
    print(f"📧 MOCK EMAIL SENT TO: {user.email}")
    print(f"🔐 YOUR SECRET OTP IS: {otp_code}")
    print(f"⚙️ ACTION TYPE: {action_type.name}")
    print(f"{'='*50}\n")

    return otp_code




# app/utils/email_service.py
from flask_mail import Message
from app.extensions import mail
from flask import current_app
from twilio.rest import Client

def send_verification_email(user_email, otp, verification_link):
    try:
        print(f"--- TRYING TO SEND EMAIL TO: {user_email} ---") # Ye terminal me dikhega
        
        msg = Message('Verify Your E-Commerce Account', 
                      sender=current_app.config['MAIL_USERNAME'], 
                      recipients=[user_email])
        
        msg.body = f"Hello!\n\nYour Email OTP is: {otp}\n\nOr click this secure link to verify your email (Valid for 10 mins):\n{verification_link}"
        
        mail.send(msg)
        print("✅ SUCCESS: Email sent successfully!")
        
    except Exception as e:
        print(f"❌ EMAIL FAILED ERROR: {e}") # Asli galti yahan print hogi!

# (Niche aapka send_sms_otp wala function waise hi rahega)

def send_sms_otp(user_phone, otp):
    # Twilio se SMS bhejne ka logic
    try:
        client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
        message = client.messages.create(
            body=f"Your E-Commerce Verification OTP is: {otp}. Do not share it.",
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=user_phone
        )
        return True
    except Exception as e:
        print(f"Twilio SMS Failed (Check Account Setup): {e}")
        return False