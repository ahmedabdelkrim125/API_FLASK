from app import create_app
from models import db, OTP

app = create_app()

with app.app_context():
    otps = OTP.query.all()
    for i, otp in enumerate(otps):
        print(f'OTP {i+1}: {otp.otp_code}')
        print(f'  Email: {otp.email}')
        print(f'  Expires: {otp.expires_at}')
        print(f'  Used: {otp.used}')
        print()