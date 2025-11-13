from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Booking, Field, User, Notification
from datetime import datetime, date, time
from utils import t, create_response, create_error_response
import json

bookings_bp = Blueprint('bookings', __name__)

def create_notification(user_id, title, message, notification_type):
    """Helper function to create a notification"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {str(e)}")
        return None

@bookings_bp.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['field_id', 'date', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
        
        # Parse datetime fields
        booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Check if field exists
        field = Field.query.get(data['field_id'])
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
            
        # Check if the booking time is valid (within field hours)
        field_opening = field.opening_time if field.opening_time else time(8, 0)
        field_closing = field.closing_time if field.closing_time else time(22, 0)
        
        if start_time < field_opening or end_time > field_closing or start_time >= end_time:
            return jsonify(create_error_response('invalid_booking_time')), 400
            
        # Check if there's already a booking for this time slot
        overlapping_booking = Booking.query.filter(
            Booking.field_id == field.id,
            Booking.date == booking_date,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
            Booking.status != 'cancelled'
        ).first()
        
        if overlapping_booking:
            return jsonify(create_error_response('time_slot_unavailable')), 409
            
        # Calculate total price
        duration_hours = (datetime.combine(date.today(), end_time) - 
                         datetime.combine(date.today(), start_time)).seconds / 3600
        total_price = round(duration_hours * field.price_per_hour, 2)
        
        # Create new booking
        new_booking = Booking(
            user_id=user.id,
            field_id=field.id,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            status='pending'
        )
        
        db.session.add(new_booking)
        db.session.commit()
        
        return jsonify(create_response('booking_created_successfully', {'booking': new_booking.to_dict()})), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@bookings_bp.route('/bookings/<int:id>', methods=['GET'])
@jwt_required()
def get_booking(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        booking = Booking.query.get(id)
        
        if not booking:
            return jsonify(create_error_response('booking_not_found')), 404
            
        # Check permissions
        if user.role == 'user' and booking.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role == 'owner' and booking.field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['user', 'owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        return jsonify(create_response('booking_retrieved_successfully', {'booking': booking.to_dict()}))
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@bookings_bp.route('/bookings/<int:id>', methods=['PUT'])
@jwt_required()
def update_booking_status(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        booking = Booking.query.get(id)
        
        if not booking:
            return jsonify(create_error_response('booking_not_found')), 404
            
        # Check permissions
        if user.role == 'user' and booking.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role == 'owner' and booking.field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['user', 'owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        new_status = data.get('status')
        
        # Validate status
        valid_statuses = ['confirmed', 'cancelled', 'completed']
        if new_status not in valid_statuses:
            return jsonify(create_error_response('invalid_status')), 400
            
        # Update booking status
        booking.status = new_status
        db.session.commit()
        
        return jsonify(create_response('booking_status_updated', {'booking': booking.to_dict()}))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@bookings_bp.route('/bookings/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_booking(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        booking = Booking.query.get(id)
        
        if not booking:
            return jsonify(create_error_response('booking_not_found')), 404
            
        # Check permissions
        if user.role == 'user' and booking.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role == 'owner' and booking.field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['user', 'owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        db.session.delete(booking)
        db.session.commit()
        
        return jsonify(create_response('booking_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@bookings_bp.route('/bookings/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_bookings(user_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify(create_error_response('user_not_found')), 404
            
        # Check permissions
        if user.role == 'user' and user.id != user_id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role == 'owner':
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['user', 'owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get all bookings for the user with pagination
        bookings = Booking.query.filter_by(user_id=user_id).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify(create_response('user_bookings_retrieved_successfully', {
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': bookings.page,
                'pages': bookings.pages,
                'per_page': bookings.per_page,
                'total': bookings.total,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev,
                'next_num': bookings.next_num,
                'prev_num': bookings.prev_num
            }
        }))
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@bookings_bp.route('/bookings/field/<int:field_id>', methods=['GET'])
@jwt_required()
def get_field_bookings(field_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify(create_error_response('user_not_found')), 404
            
        # Check if field exists
        field = Field.query.get(field_id)
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
            
        # Check permissions
        if user.role == 'user':
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role == 'owner' and field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['user', 'owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get all bookings for the field with pagination
        bookings = Booking.query.filter_by(field_id=field_id).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify(create_response('field_bookings_retrieved_successfully', {
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': bookings.page,
                'pages': bookings.pages,
                'per_page': bookings.per_page,
                'total': bookings.total,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev,
                'next_num': bookings.next_num,
                'prev_num': bookings.prev_num
            }
        }))
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

# New endpoint for checking field availability
@bookings_bp.route('/bookings/field/<int:field_id>/availability', methods=['GET'])
@jwt_required()
def check_field_availability(field_id):
    try:
        # Check if field exists
        field = Field.query.get(field_id)
        if not field:
            return jsonify({'message': 'Field not found'}), 404
        
        # Get query parameters
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'message': 'Date parameter is required'}), 400
        
        # Parse date
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get all bookings for the field on the specified date (excluding cancelled bookings)
        bookings = Booking.query.filter(
            Booking.field_id == field_id,
            Booking.date == check_date,
            Booking.status != 'cancelled'
        ).order_by(Booking.start_time).all()
        
        # Convert bookings to a more usable format
        booked_slots = []
        for booking in bookings:
            booked_slots.append({
                'id': booking.id,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'status': booking.status
            })
        
        # Calculate available slots (assuming standard opening hours 8:00-22:00)
        available_slots = calculate_available_slots(bookings, check_date, field)
        
        return jsonify({
            'message': 'Field availability retrieved successfully',
            'field_id': field_id,
            'field_name': field.name,
            'date': check_date.isoformat(),
            'booked_slots': booked_slots,
            'available_slots': available_slots
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error checking field availability', 'error': str(e)}), 500

def calculate_available_slots(bookings, date, field):
    """
    Calculate available time slots based on existing bookings and field opening hours.
    """
    # Use field's opening and closing times, with defaults if not set
    opening_time = field.opening_time if field.opening_time else time(8, 0)  # Default 8:00 AM
    closing_time = field.closing_time if field.closing_time else time(22, 0)  # Default 10:00 PM
    
    # If no bookings, the entire day is available
    if not bookings:
        return [{
            'start_time': opening_time.isoformat(),
            'end_time': closing_time.isoformat()
        }]
    
    # Sort bookings by start time
    sorted_bookings = sorted(bookings, key=lambda x: x.start_time)
    
    available_slots = []
    
    # Check for available slot before first booking
    if sorted_bookings[0].start_time > opening_time:
        available_slots.append({
            'start_time': opening_time.isoformat(),
            'end_time': sorted_bookings[0].start_time.isoformat()
        })
    
    # Check for available slots between bookings
    for i in range(len(sorted_bookings) - 1):
        current_booking = sorted_bookings[i]
        next_booking = sorted_bookings[i + 1]
        
        # If there's a gap between bookings
        if current_booking.end_time < next_booking.start_time:
            available_slots.append({
                'start_time': current_booking.end_time.isoformat(),
                'end_time': next_booking.start_time.isoformat()
            })
    
    # Check for available slot after last booking
    if sorted_bookings[-1].end_time < closing_time:
        available_slots.append({
            'start_time': sorted_bookings[-1].end_time.isoformat(),
            'end_time': closing_time.isoformat()
        })
    
    return available_slots
