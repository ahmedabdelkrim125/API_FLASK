from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Review, Field, User, Notification
from datetime import datetime
from utils import t, create_response, create_error_response

reviews_bp = Blueprint('reviews', __name__)

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

@reviews_bp.route('/reviews', methods=['POST'])
@jwt_required()
def create_review():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['field_id', 'rating']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
                
        # Check if field exists
        field = Field.query.get(data['field_id'])
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
            
        # Validate rating (1-5)
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify(create_error_response('invalid_rating')), 400
            
        # Check if user has already reviewed this field
        existing_review = Review.query.filter_by(user_id=user.id, field_id=field.id).first()
        if existing_review:
            return jsonify(create_error_response('review_already_exists')), 409
            
        # Create new review
        review = Review(
            user_id=user.id,
            field_id=field.id,
            rating=rating,
            comment=data.get('comment', '')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Create notification for the field owner
        notification = Notification(
            user_id=field.owner_id,
            title=t('new_review_received'),
            message=f"{user.name} has left a {rating}-star review for your field {field.name}",
            type='review'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify(create_response('review_created_successfully', {'review': review.to_dict()})), 201
        
    except ValueError:
        return jsonify(create_error_response('invalid_rating_format')), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@reviews_bp.route('/fields/<int:field_id>/reviews', methods=['GET'])
def get_field_reviews(field_id):
    try:
        # Check if field exists
        field = Field.query.get(field_id)
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get all reviews for the field with pagination
        paginated_reviews = Review.query.filter_by(field_id=field_id).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'reviews': [review.to_dict() for review in paginated_reviews.items],
            'pagination': {
                'page': paginated_reviews.page,
                'pages': paginated_reviews.pages,
                'per_page': paginated_reviews.per_page,
                'total': paginated_reviews.total,
                'has_next': paginated_reviews.has_next,
                'has_prev': paginated_reviews.has_prev,
                'next_num': paginated_reviews.next_num,
                'prev_num': paginated_reviews.prev_num
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching reviews', 'error': str(e)}), 500

@reviews_bp.route('/reviews/<int:id>', methods=['PUT'])
@jwt_required()
def update_review(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        review = Review.query.get(id)
        
        if not review:
            return jsonify(create_error_response('review_not_found')), 404
            
        # Check if user owns the review
        if review.user_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Update rating if provided
        if 'rating' in data:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                return jsonify(create_error_response('invalid_rating')), 400
            review.rating = rating
            
        # Update comment if provided
        if 'comment' in data:
            review.comment = data['comment']
            
        db.session.commit()
        
        return jsonify(create_response('review_updated_successfully', {'review': review.to_dict()}))
        
    except ValueError:
        return jsonify(create_error_response('invalid_rating_format')), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@reviews_bp.route('/reviews/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_review(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        review = Review.query.get(id)
        
        if not review:
            return jsonify(create_error_response('review_not_found')), 404
            
        # Check permissions (user owns review or is admin)
        if review.user_id != user.id and user.role != 'admin':
            return jsonify(create_error_response('unauthorized')), 403
            
        db.session.delete(review)
        db.session.commit()
        
        return jsonify(create_response('review_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

