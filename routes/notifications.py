from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification, User
from utils import t, create_response, create_error_response

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_user_notifications():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Get query parameters
        is_read = request.args.get('is_read', type=lambda x: x.lower() == 'true')
        notification_type = request.args.get('type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
            
        # Build query
        query = Notification.query.filter_by(user_id=user.id)
        
        # Filter by read status if provided
        if is_read is not None:
            query = query.filter_by(is_read=is_read)
            
        # Filter by type if provided
        if notification_type:
            query = query.filter_by(type=notification_type)
            
        # Order by creation date (newest first)
        query = query.order_by(Notification.created_at.desc())
        
        # Apply pagination
        notifications = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify(create_response('notifications_retrieved_successfully', {
            'notifications': [notification.to_dict() for notification in notifications.items],
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev,
                'next_num': notifications.next_num,
                'prev_num': notifications.prev_num
            }
        })), 200
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@notifications_bp.route('/notifications/<int:id>', methods=['GET'])
@jwt_required()
def get_notification(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        notification = Notification.query.get(id)
        
        if not notification:
            return jsonify(create_error_response('notification_not_found')), 404
            
        # Check if user owns the notification
        if notification.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        return jsonify(create_response('notification_retrieved_successfully', {
            'notification': notification.to_dict()
        })), 200
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@notifications_bp.route('/notifications/<int:id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        notification = Notification.query.get(id)
        
        if not notification:
            return jsonify(create_error_response('notification_not_found')), 404
            
        # Check if user owns the notification
        if notification.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Mark as read
        notification.is_read = True
        db.session.commit()
        
        return jsonify(create_response('notification_marked_as_read'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@notifications_bp.route('/notifications/read', methods=['PUT'])
@jwt_required()
def mark_all_notifications_as_read():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Mark all user's notifications as read
        Notification.query.filter_by(user_id=user.id).update({'is_read': True})
        db.session.commit()
        
        return jsonify(create_response('all_notifications_marked_as_read'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@notifications_bp.route('/notifications/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_notification(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        notification = Notification.query.get(id)

        if not notification:
            return jsonify(create_error_response('notification_not_found')), 404
            
        # Check if user owns the notification
        if notification.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Delete notification
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify(create_response('notification_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@notifications_bp.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_notifications_count():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Count unread notifications
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        
        return jsonify(create_response('unread_count_retrieved_successfully', {
            'unread_count': unread_count
        })), 200
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500
