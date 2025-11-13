from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Field, User, Booking
from datetime import datetime, time
from utils import t, create_response, create_error_response

fields_bp = Blueprint('fields', __name__)

@fields_bp.route('/fields', methods=['GET'])
def get_fields():
    try:
        # Get query parameters
        governorate = request.args.get('governorate')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search')  # Search in name or location
        sort_by = request.args.get('sort_by', 'id')  # Default sort by id
        sort_order = request.args.get('sort_order', 'asc')  # Default ascending
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Build query
        query = Field.query
        
        # Filter by governorate if provided
        if governorate:
            query = query.filter_by(governorate=governorate.lower())
        
        # Filter by price range
        if min_price is not None:
            query = query.filter(Field.price_per_hour >= min_price)
        if max_price is not None:
            query = query.filter(Field.price_per_hour <= max_price)
        
        # Search in name or location
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    Field.name.ilike(search_term),
                    Field.location.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort_by == 'name':
            order_column = Field.name
        elif sort_by == 'price':
            order_column = Field.price_per_hour
        elif sort_by == 'governorate':
            order_column = Field.governorate
        else:
            order_column = Field.id  # Default sort by id
        
        if sort_order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Apply pagination
        paginated_fields = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'fields': [field.to_dict() for field in paginated_fields.items],
            'pagination': {
                'page': paginated_fields.page,
                'pages': paginated_fields.pages,
                'per_page': paginated_fields.per_page,
                'total': paginated_fields.total,
                'has_next': paginated_fields.has_next,
                'has_prev': paginated_fields.has_prev,
                'next_num': paginated_fields.next_num,
                'prev_num': paginated_fields.prev_num
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching fields', 'error': str(e)}), 500

@fields_bp.route('/fields/<int:id>', methods=['GET'])
def get_field(id):
    try:
        field = Field.query.get(id)
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
        
        return jsonify(create_response('field_retrieved_successfully', {'field': field.to_dict()})), 200
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@fields_bp.route('/fields', methods=['POST'])
@jwt_required()
def create_field():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user is owner or admin
        if user.role not in ['owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'location', 'price_per_hour', 'governorate']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_error_response('required_field_missing')), 400
                
        # Create new field
        new_field = Field(
            name=data['name'],
            location=data['location'],
            description=data.get('description', ''),
            price_per_hour=data['price_per_hour'],
            governorate=data['governorate'],
            owner_id=user.id if user.role == 'owner' else None
        )
        
        db.session.add(new_field)
        db.session.commit()
        
        return jsonify(create_response('field_created_successfully', {'field': new_field.to_dict()})), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@fields_bp.route('/fields/<int:id>', methods=['PUT'])
@jwt_required()
def update_field(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        field = Field.query.get(id)
        
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
            
        # Check permissions
        if user.role == 'owner' and field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Update field
        field.name = data.get('name', field.name)
        field.location = data.get('location', field.location)
        field.description = data.get('description', field.description)
        field.price_per_hour = data.get('price_per_hour', field.price_per_hour)
        field.governorate = data.get('governorate', field.governorate)
        
        db.session.commit()
        
        return jsonify(create_response('field_updated_successfully', {'field': field.to_dict()}))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@fields_bp.route('/fields/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_field(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        field = Field.query.get(id)
        
        if not field:
            return jsonify(create_error_response('field_not_found')), 404
            
        # Check permissions
        if user.role == 'owner' and field.owner_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
        elif user.role not in ['owner', 'admin']:
            return jsonify(create_error_response('unauthorized')), 403
            
        db.session.delete(field)
        db.session.commit()
        
        return jsonify(create_response('field_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

# New endpoint for searching available fields
@fields_bp.route('/fields/available', methods=['GET'])
def search_available_fields():
    try:
        # Get query parameters
        date_str = request.args.get('date')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        governorate = request.args.get('governorate')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search')  # Search in name or location
        sort_by = request.args.get('sort_by', 'id')  # Default sort by id
        sort_order = request.args.get('sort_order', 'asc')  # Default ascending
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate required parameters
        if not date_str or not start_time_str or not end_time_str:
            return jsonify({
                'message': 'date, start_time, and end_time parameters are required'
            }), 400
        
        # Parse parameters
        try:
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({
                'message': 'Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time'
            }), 400
        
        # Validate time range
        if start_time >= end_time:
            return jsonify({
                'message': 'Start time must be before end time'
            }), 400
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Build query for fields
        query = Field.query
        
        # Filter by governorate if provided
        if governorate:
            query = query.filter_by(governorate=governorate.lower())
        
        # Filter by price range
        if min_price is not None:
            query = query.filter(Field.price_per_hour >= min_price)
        if max_price is not None:
            query = query.filter(Field.price_per_hour <= max_price)
        
        # Search in name or location
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    Field.name.ilike(search_term),
                    Field.location.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort_by == 'name':
            order_column = Field.name
        elif sort_by == 'price':
            order_column = Field.price_per_hour
        elif sort_by == 'governorate':
            order_column = Field.governorate
        else:
            order_column = Field.id  # Default sort by id
        
        if sort_order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Get all fields that match filters
        fields = query.all()
        
        # Filter fields that are available during the requested time
        available_fields = []
        
        for field in fields:
            # Check if the field is open during the requested time
            field_opening = field.opening_time if field.opening_time else time(8, 0)
            field_closing = field.closing_time if field.closing_time else time(22, 0)
            
            if start_time < field_opening or end_time > field_closing:
                # Field is closed during requested time
                continue
            
            # Check for overlapping bookings
            overlapping_booking = Booking.query.filter(
                Booking.field_id == field.id,
                Booking.date == search_date,
                Booking.start_time < end_time,
                Booking.end_time > start_time,
                Booking.status != 'cancelled'
            ).first()
            
            # If no overlapping booking, field is available
            if not overlapping_booking:
                available_fields.append(field)
        
        # Apply pagination to available fields
        # Since we've already filtered, we need to manually paginate
        total = len(available_fields)
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1
        next_num = page + 1 if has_next else None
        prev_num = page - 1 if has_prev else None
        
        # Slice the available fields for pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_fields = available_fields[start_idx:end_idx]
        
        return jsonify({
            'message': 'Available fields retrieved successfully',
            'date': search_date.isoformat(),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'available_fields_count': len(available_fields),
            'fields': [field.to_dict() for field in paginated_fields],
            'pagination': {
                'page': page,
                'pages': pages,
                'per_page': per_page,
                'total': total,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_num': next_num,
                'prev_num': prev_num
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error searching available fields', 'error': str(e)}), 500