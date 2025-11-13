from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Team, TeamMember, User, Field, Booking, Review
from utils import t, create_response, create_error_response

clubs_bp = Blueprint('clubs', __name__)

@clubs_bp.route('/clubs', methods=['POST'])
@jwt_required()
def create_club():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify(create_error_response('required_field_missing')), 400
            
        # Create new club (as a team)
        club = Team(
            name=data['name'],
            leader_id=user.id
        )
        
        db.session.add(club)
        db.session.flush()  # Get the club ID without committing
        
        # Add creator as club leader
        club_member = TeamMember(
            team_id=club.id,
            user_id=user.id,
            role='leader'
        )
        
        db.session.add(club_member)
        db.session.commit()
        
        return jsonify(create_response('club_created_successfully', {
            'club': club.to_dict(),
            'member': club_member.to_dict()
        })), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@clubs_bp.route('/clubs/<int:id>', methods=['PUT'])
@jwt_required()
def update_club(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        club = Team.query.get(id)  # Club is stored as Team in the database
        
        if not club:
            return jsonify(create_error_response('club_not_found')), 404
            
        # Check if user is club leader
        if club.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Update club name if provided
        if 'name' in data:
            club.name = data['name']
            
        db.session.commit()
        
        return jsonify(create_response('club_updated_successfully', {'club': club.to_dict()}))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@clubs_bp.route('/clubs/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_club(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        club = Team.query.get(id)  # Club is stored as Team in the database
        
        if not club:
            return jsonify(create_error_response('club_not_found')), 404
            
        # Check if user is club leader
        if club.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        db.session.delete(club)
        db.session.commit()
        
        return jsonify(create_response('club_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@clubs_bp.route('/clubs/<int:club_id>/details', methods=['GET'])
def get_club_details(club_id):
    try:
        # Check if club (field owner) exists by checking if there are fields owned by this user
        owner_fields = Field.query.filter_by(owner_id=club_id).all()
        if not owner_fields:
            return jsonify(create_error_response('club_not_found')), 404
        
        # Get club information from the first field's owner
        club_owner = User.query.get(club_id)
        if not club_owner:
            return jsonify(create_error_response('club_not_found')), 404
        
        # Get all fields owned by this club
        fields = owner_fields
        
        # Calculate club statistics
        total_fields = len(fields)
        total_bookings = 0
        total_reviews = 0
        total_rating = 0
        field_ratings = []
        
        field_details = []
        for field in fields:
            # Get bookings for this field
            bookings = Booking.query.filter_by(field_id=field.id).all()
            total_bookings += len(bookings)
            
            # Get reviews for this field
            reviews = Review.query.filter_by(field_id=field.id).all()
            total_reviews += len(reviews)
            
            # Calculate average rating for this field
            field_avg_rating = 0
            if reviews:
                field_avg_rating = sum(review.rating for review in reviews) / len(reviews)
                field_ratings.append(field_avg_rating)
                total_rating += sum(review.rating for review in reviews)
            
            field_details.append({
                'id': field.id,
                'name': field.name,
                'location': field.location,
                'governorate': field.governorate,
                'price_per_hour': field.price_per_hour,
                'bookings_count': len(bookings),
                'reviews_count': len(reviews),
                'average_rating': round(field_avg_rating, 2) if reviews else 0
            })
        
        # Calculate overall club rating
        club_rating = 0
        if field_ratings:
            club_rating = sum(field_ratings) / len(field_ratings)
        
        # Get teams registered at this club's fields
        field_ids = [field.id for field in fields]
        teams = Team.query.join(Booking).filter(Booking.field_id.in_(field_ids)).distinct(Team.id).all()
        
        return jsonify(create_response('club_details_retrieved_successfully', {
            'club': {
                'id': club_owner.id,
                'name': club_owner.name,
                'email': club_owner.email,
                'phone': club_owner.phone,
                'total_fields': total_fields,
                'total_bookings': total_bookings,
                'total_reviews': total_reviews,
                'average_rating': round(club_rating, 2) if club_rating else 0,
                'registered_teams': len(teams),
                'fields': field_details
            }
        })), 200
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@clubs_bp.route('/clubs/search', methods=['GET'])
def search_clubs():
    try:
        # Get query parameters
        name = request.args.get('name')
        governorate = request.args.get('governorate')
        min_rating = request.args.get('min_rating', type=float)
        sort_by = request.args.get('sort_by', 'id')  # Default sort by id
        sort_order = request.args.get('sort_order', 'asc')  # Default ascending
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # First, get all field owners (clubs)
        owner_ids = db.session.query(Field.owner_id).distinct().all()
        owner_ids = [owner_id[0] for owner_id in owner_ids]
        
        # Build query for club owners
        query = User.query.filter(User.id.in_(owner_ids))
        
        # Search by club name
        if name:
            search_term = f"%{name.lower()}%"
            query = query.filter(User.name.ilike(search_term))
        
        # Get all clubs that match basic filters
        clubs = query.all()
        
        # Filter by governorate and rating
        filtered_clubs = []
        for club in clubs:
            # Get club's fields
            fields = Field.query.filter_by(owner_id=club.id).all()
            
            # Filter by governorate if provided
            if governorate:
                governorate_fields = [field for field in fields if field.governorate.lower() == governorate.lower()]
                if not governorate_fields:
                    continue  # Skip this club if no fields match governorate
            
            # Calculate club rating
            total_reviews = 0
            total_rating = 0
            for field in fields:
                reviews = Review.query.filter_by(field_id=field.id).all()
                total_reviews += len(reviews)
                total_rating += sum(review.rating for review in reviews)
            
            average_rating = 0
            if total_reviews > 0:
                average_rating = total_rating / total_reviews
            
            # Filter by minimum rating
            if min_rating is not None and average_rating < min_rating:
                continue  # Skip this club if rating is below minimum
            
            # Add club to filtered list with calculated rating
            club_data = {
                'user': club,
                'fields': fields,
                'average_rating': average_rating
            }
            filtered_clubs.append(club_data)
        
        # Apply sorting
        if sort_by == 'name':
            filtered_clubs.sort(key=lambda x: x['user'].name.lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'rating':
            filtered_clubs.sort(key=lambda x: x['average_rating'], reverse=(sort_order == 'desc'))
        else:
            # Default sort by id
            filtered_clubs.sort(key=lambda x: x['user'].id, reverse=(sort_order == 'desc'))
        
        # Apply pagination to filtered clubs
        total = len(filtered_clubs)
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1
        next_num = page + 1 if has_next else None
        prev_num = page - 1 if has_prev else None
        
        # Slice the filtered clubs for pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_clubs = filtered_clubs[start_idx:end_idx]
        
        # Format response data
        clubs_data = []
        for club_data in paginated_clubs:
            club = club_data['user']
            fields = club_data['fields']
            average_rating = club_data['average_rating']
            
            # Get club statistics
            total_fields = len(fields)
            total_bookings = 0
            total_reviews = 0
            
            for field in fields:
                bookings = Booking.query.filter_by(field_id=field.id).all()
                reviews = Review.query.filter_by(field_id=field.id).all()
                total_bookings += len(bookings)
                total_reviews += len(reviews)
            
            clubs_data.append({
                'id': club.id,
                'name': club.name,
                'email': club.email,
                'phone': club.phone,
                'total_fields': total_fields,
                'total_bookings': total_bookings,
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 2) if average_rating else 0
            })
        
        return jsonify(create_response('clubs_searched_successfully', {
            'clubs': clubs_data,
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
        })), 200
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@clubs_bp.route('/clubs/top-rated', methods=['GET'])
def get_top_rated_clubs():
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            limit = 10
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # First, get all field owners (clubs)
        owner_ids = db.session.query(Field.owner_id).distinct().all()
        owner_ids = [owner_id[0] for owner_id in owner_ids]
        
        # Get all clubs
        clubs = User.query.filter(User.id.in_(owner_ids)).all()
        
        # Calculate ratings for all clubs
        club_ratings = []
        for club in clubs:
            # Get club's fields
            fields = Field.query.filter_by(owner_id=club.id).all()
            
            # Calculate club rating
            total_reviews = 0
            total_rating = 0
            for field in fields:
                reviews = Review.query.filter_by(field_id=field.id).all()
                total_reviews += len(reviews)
                total_rating += sum(review.rating for review in reviews)
            
            average_rating = 0
            if total_reviews > 0:
                average_rating = total_rating / total_reviews
            
            club_ratings.append({
                'club': club,
                'fields': fields,
                'average_rating': average_rating,
                'total_reviews': total_reviews
            })
        
        # Sort by rating (descending) and then by number of reviews (descending) for ties
        club_ratings.sort(key=lambda x: (x['average_rating'], x['total_reviews']), reverse=True)
        
        # Limit to top clubs
        top_clubs = club_ratings[:limit]
        
        # Apply pagination to top clubs
        total = len(top_clubs)
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1
        next_num = page + 1 if has_next else None
        prev_num = page - 1 if has_prev else None
        
        # Slice the top clubs for pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_clubs = top_clubs[start_idx:end_idx]
        
        # Format response data
        clubs_data = []
        for club_data in paginated_clubs:
            club = club_data['club']
            fields = club_data['fields']
            average_rating = club_data['average_rating']
            
            # Get club statistics
            total_fields = len(fields)
            total_bookings = 0
            total_reviews = club_data['total_reviews']
            
            for field in fields:
                bookings = Booking.query.filter_by(field_id=field.id).all()
                total_bookings += len(bookings)
            
            clubs_data.append({
                'id': club.id,
                'name': club.name,
                'email': club.email,
                'phone': club.phone,
                'total_fields': total_fields,
                'total_bookings': total_bookings,
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 2) if average_rating else 0
            })
        
        return jsonify(create_response('top_rated_clubs_retrieved_successfully', {
            'clubs': clubs_data,
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
        })), 200
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500