from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Payment, Booking, User, Notification, Analytics
from datetime import datetime, date
from utils import t, create_response, create_error_response
import json
import uuid

payments_bp = Blueprint('payments', __name__)

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

@payments_bp.route('/payments', methods=['POST'])
@jwt_required()
def create_payment():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['booking_id', 'amount', 'payment_method']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
                
        # Check if booking exists and belongs to user
        booking = Booking.query.get(data['booking_id'])
        if not booking:
            return jsonify(create_error_response('booking_not_found')), 404
            
        if booking.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Check if booking is already paid
        existing_payment = Payment.query.filter_by(booking_id=booking.id).first()
        if existing_payment and existing_payment.status == 'completed':
            return jsonify(create_error_response('payment_already_completed')), 400
            
        # Create new payment
        payment = Payment(
            booking_id=booking.id,
            user_id=user.id,
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            payment_method=data['payment_method']
        )
        payment.transaction_id = str(uuid.uuid4())
        payment.status = 'pending'
        
        db.session.add(payment)
        db.session.commit()
        
        # Create notification for the field owner
        field_owner = User.query.get(booking.field.owner_id)
        if field_owner:
            notification = Notification(
                user_id=field_owner.id,
                title=t('new_payment_received'),
                message=f"{user.name} has made a payment of ${data['amount']} for booking #{booking.id}",
                type='payment'
            )
            db.session.add(notification)
            db.session.commit()
        
        return jsonify(create_response('payment_initiated', {'payment': payment.to_dict()})), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@payments_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_user_payments():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get all payments for the user with pagination
        paginated_payments = Payment.query.filter_by(user_id=user.id).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'payments': [payment.to_dict() for payment in paginated_payments.items],
            'pagination': {
                'page': paginated_payments.page,
                'pages': paginated_payments.pages,
                'per_page': paginated_payments.per_page,
                'total': paginated_payments.total,
                'has_next': paginated_payments.has_next,
                'has_prev': paginated_payments.has_prev,
                'next_num': paginated_payments.next_num,
                'prev_num': paginated_payments.prev_num
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching payments', 'error': str(e)}), 500

@payments_bp.route('/payments/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get payment
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404
        
        # Check if payment belongs to user
        if payment.user_id != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching payment', 'error': str(e)}), 500

@payments_bp.route('/payments/methods', methods=['GET'])
def get_payment_methods():
    try:
        payment_methods = [
            {'id': 'vodafone_cash', 'name': 'Vodafone Cash'},
            {'id': 'etisalat_cash', 'name': 'Etisalat Cash'},
            {'id': 'orange_cash', 'name': 'Orange Cash'},
            {'id': 'we_pay', 'name': 'We Pay'},
            {'id': 'visa', 'name': 'Visa'},
            {'id': 'mastercard', 'name': 'MasterCard'}
        ]
        
        return jsonify({
            'payment_methods': payment_methods
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching payment methods', 'error': str(e)}), 500

@payments_bp.route('/payments/<int:id>', methods=['PUT'])
@jwt_required()
def update_payment_status(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        payment = Payment.query.get(id)
        
        if not payment:
            return jsonify(create_error_response('payment_not_found')), 404
            
        # Only admins can update payment status
        if user.role != 'admin':
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        new_status = data.get('status')
        
        # Validate status
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        if new_status not in valid_statuses:
            return jsonify(create_error_response('invalid_status')), 400
            
        # Update payment status
        old_status = payment.status
        payment.status = new_status
        payment.completed_at = datetime.utcnow() if new_status == 'completed' else None
        db.session.commit()
        
        # Create notification for the user
        booking = Booking.query.get(payment.booking_id)
        if booking:
            status_messages = {
                'completed': 'Payment completed successfully',
                'failed': 'Payment failed',
                'refunded': 'Payment refunded'
            }
            
            notification = Notification(
                user_id=booking.user_id,
                title=t('payment_status_updated'),
                message=f"Your payment for booking #{booking.id} has been {new_status}: {status_messages.get(new_status, '')}",
                type='payment'
            )
            db.session.add(notification)
            db.session.commit()
            
            # Update analytics for completed payments
            if new_status == 'completed' and old_status != 'completed':
                analytics = Analytics(
                    metric_name='revenue',
                    value=payment.amount,
                    date=date.today(),
                    user_id=booking.user_id,
                    field_id=booking.field_id
                )
                db.session.add(analytics)
                db.session.commit()
        
        return jsonify(create_response('payment_status_updated', {'payment': payment.to_dict()}))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@payments_bp.route('/payments/<int:payment_id>/refund', methods=['POST'])
@jwt_required()
def refund_payment(payment_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get payment
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404
        
        # Check if payment belongs to user or user is admin
        if payment.user_id != user.id and user.role != 'admin':
            return jsonify({'message': 'Access denied'}), 403
        
        # Check if payment can be refunded
        if payment.status != 'completed':
            return jsonify({'message': 'Only completed payments can be refunded'}), 400
        
        # Check if payment is already refunded
        if payment.status == 'refunded':
            return jsonify({'message': 'Payment is already refunded'}), 400
        
        # Get the booking for the payment
        booking = Booking.query.get(payment.booking_id)
        
        # In a real application, you would integrate with payment gateways to process the refund
        # For now, we'll simulate a successful refund
        payment.status = 'refunded'
        db.session.commit()
        
        # Create notification for refund success
        create_notification(
            user_id=user.id,
            title="Refund Processed",
            message=f"Your refund of {payment.amount} EGP for booking #{booking.id} has been processed successfully.",
            notification_type="refund_processed"
        )
        
        # Track refund analytics
        analytics = Analytics(
            metric_name="payment_refunded",
            value=float(payment.amount),
            date=date.today(),
            user_id=user.id,
            field_id=booking.field_id
        )
        db.session.add(analytics)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment refunded successfully',
            'payment': payment.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error refunding payment', 'error': str(e)}), 500

@payments_bp.route('/payments/booking/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_payments_by_booking(booking_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if booking exists
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Check if booking belongs to user or user is admin
        if booking.user_id != user.id and user.role != 'admin':
            return jsonify({'message': 'Access denied'}), 403
        
        # Get all payments for the booking
        payments = Payment.query.filter_by(booking_id=booking_id).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching payments', 'error': str(e)}), 500