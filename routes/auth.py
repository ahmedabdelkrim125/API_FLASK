from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models import db, User, OTP
from datetime import datetime, timedelta
from utils import t, create_response, create_error_response
import random
import string

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify(create_error_response('email_already_exists')), 409
            
        # Create new user
        new_user = User(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            role=data.get('role', 'user')
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        token = create_access_token(identity={'id': new_user.id, 'role': new_user.role})
        return jsonify(create_response('user_created_successfully', {
            'user': new_user.to_dict(),
            'token': token
        })), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify(create_error_response('required_field_missing')), 400
            
        # Check if user exists and password is correct
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            token = create_access_token(identity={'id': user.id, 'role': user.role})
            return jsonify(create_response('user_logged_in_successfully', {
                'user': user.to_dict(),
                'token': token
            })), 200
        else:
            return jsonify(create_error_response('invalid_email_or_password')), 401
            
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email'):
            return jsonify(create_error_response('required_field_missing')), 400
            
        # Check if user exists
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify(create_error_response('user_not_found')), 404
            
        # Generate OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP expires in 10 minutes
        
        # Save OTP to database
        otp = OTP(
            email=user.email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # In a real application, you would send the OTP via email/SMS
        # For now, we'll just return it in the response
        return jsonify(create_response('otp_sent_successfully', {
            'message': f'OTP sent to {user.email}',
            'otp': otp_code  # Remove this in production
        })), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'otp', 'new_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
                
        # Check if user exists
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify(create_error_response('user_not_found')), 404
            
        # Verify OTP
        otp_record = OTP.query.filter_by(email=data['email'], otp_code=data['otp']).first()
        if not otp_record or otp_record.used or otp_record.expires_at < datetime.utcnow():
            return jsonify(create_error_response('invalid_otp')), 400
            
        # Update user password
        user.set_password(data['new_password'])
        otp_record.used = True
        db.session.commit()
        
        return jsonify(create_response('password_reset_successfully')), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500