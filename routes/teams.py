from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Team, TeamMember, User, Booking
from utils import t, create_response, create_error_response

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams', methods=['POST'])
@jwt_required()
def create_team():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify(create_error_response('required_field_missing')), 400
            
        # Create new team
        team = Team(
            name=data['name'],
            leader_id=user.id
        )
        
        db.session.add(team)
        db.session.flush()  # Get the team ID without committing
        
        # Add creator as team leader
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role='leader'
        )
        
        db.session.add(team_member)
        db.session.commit()
        
        return jsonify(create_response('team_created_successfully', {
            'team': team.to_dict(),
            'member': team_member.to_dict()
        })), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@teams_bp.route('/teams', methods=['GET'])
@jwt_required()
def get_teams():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get query parameters
        search = request.args.get('search')  # Search in team name
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
        query = Team.query
        
        # Search in team name
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(Team.name.ilike(search_term))
        
        # Apply sorting
        if sort_by == 'name':
            order_column = Team.name
        elif sort_by == 'created_at':
            order_column = Team.created_at
        else:
            order_column = Team.id  # Default sort by id
        
        if sort_order == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Apply pagination
        paginated_teams = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        teams_data = []
        for team in paginated_teams.items:
            # Get team members count
            members_count = db.session.query(TeamMember).filter(TeamMember.team_id == team.id).count()
            
            team_data = team.to_dict()
            team_data['members_count'] = members_count
            teams_data.append(team_data)
        
        return jsonify({
            'message': 'Teams retrieved successfully',
            'teams': teams_data,
            'pagination': {
                'page': paginated_teams.page,
                'pages': paginated_teams.pages,
                'per_page': paginated_teams.per_page,
                'total': paginated_teams.total,
                'has_next': paginated_teams.has_next,
                'has_prev': paginated_teams.has_prev,
                'next_num': paginated_teams.next_num,
                'prev_num': paginated_teams.prev_num
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error retrieving teams', 'error': str(e)}), 500

@teams_bp.route('/teams/<int:id>', methods=['GET'])
@jwt_required()
def get_team(id):
    try:
        team = Team.query.get(id)
        if not team:
            return jsonify(create_error_response('team_not_found')), 404
        
        # Get team members
        members = TeamMember.query.filter_by(team_id=id).all()
        members_data = []
        for member in members:
            user = User.query.get(member.user_id)
            if user:
                members_data.append({
                    'id': member.id,
                    'user': user.to_dict(),
                    'role': member.role,
                    'joined_at': member.joined_at.isoformat() if member.joined_at else None
                })
        
        team_data = team.to_dict()
        team_data['members'] = members_data
        
        return jsonify({
            'team': team_data
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching team', 'error': str(e)}), 500

@teams_bp.route('/teams/<int:id>', methods=['PUT'])
@jwt_required()
def update_team(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        team = Team.query.get(id)
        
        if not team:
            return jsonify(create_error_response('team_not_found')), 404
            
        # Check if user is team leader
        if team.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Update team name if provided
        if 'name' in data:
            team.name = data['name']
            
        db.session.commit()
        
        return jsonify(create_response('team_updated_successfully', {'team': team.to_dict()}))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@teams_bp.route('/teams/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_team(id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        team = Team.query.get(id)
        
        if not team:
            return jsonify(create_error_response('team_not_found')), 404
            
        # Check if user is team leader
        if team.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        db.session.delete(team)
        db.session.commit()
        
        return jsonify(create_response('team_deleted_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@teams_bp.route('/teams/find-players', methods=['POST'])
@jwt_required()
def find_players():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Create a request to find players
        # In a real application, this would be stored in a database
        # For now, we'll just return a success message
        return jsonify({
            'message': 'Player search request submitted successfully'
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error submitting player search request', 'error': str(e)}), 500

@teams_bp.route('/teams/join', methods=['POST'])
@jwt_required()
def join_team():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('team_id'):
            return jsonify({'message': 'Team ID is required'}), 400
        
        team_id = data['team_id']
        
        # Check if team exists
        team = Team.query.get(team_id)
        if not team:
            return jsonify({'message': 'Team not found'}), 404
        
        # Check if user is already a member
        existing_membership = TeamMember.query.filter_by(team_id=team_id, user_id=user.id).first()
        if existing_membership:
            return jsonify({'message': 'You are already a member of this team'}), 409
        
        # Add user to team as a member
        team_member = TeamMember(team_id=team_id, user_id=user.id, role='member')
        db.session.add(team_member)
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully joined team',
            'team_member': team_member.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error joining team', 'error': str(e)}), 500

@teams_bp.route('/teams/<int:team_id>/members', methods=['POST'])
@jwt_required()
def add_team_member(team_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        team = Team.query.get(team_id)
        
        if not team:
            return jsonify(create_error_response('team_not_found')), 404
            
        # Check if user is team leader
        if team.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        data = request.get_json()
        
        # Validate required fields
        if not data.get('user_id'):
            return jsonify(create_error_response('required_field_missing')), 400
            
        # Check if user exists
        member_user = User.query.get(data['user_id'])
        if not member_user:
            return jsonify(create_error_response('user_not_found')), 404
            
        # Check if user is already a member
        existing_member = TeamMember.query.filter_by(team_id=team.id, user_id=member_user.id).first()
        if existing_member:
            return jsonify(create_error_response('user_already_team_member')), 409
            
        # Add user to team as member
        team_member = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            role='member'
        )
        
        db.session.add(team_member)
        db.session.commit()
        
        return jsonify(create_response('team_member_added_successfully', {'member': team_member.to_dict()})), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@teams_bp.route('/teams/<int:team_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_team_member(team_id, member_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        team = Team.query.get(team_id)
        
        if not team:
            return jsonify(create_error_response('team_not_found')), 404
            
        # Check if user is team leader
        if team.leader_id != user.id:
            return jsonify(create_error_response('unauthorized')), 403
            
        # Prevent removing the team leader
        if member_id == team.leader_id:
            return jsonify(create_error_response('cannot_remove_team_leader')), 400
            
        # Check if member exists
        team_member = TeamMember.query.filter_by(team_id=team.id, user_id=member_id).first()
        if not team_member:
            return jsonify(create_error_response('team_member_not_found')), 404
            
        db.session.delete(team_member)
        db.session.commit()
        
        return jsonify(create_response('team_member_removed_successfully'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@teams_bp.route('/teams/schedule', methods=['GET'])
@jwt_required()
def get_team_schedule():
    try:
        # Get all teams and their bookings
        teams = Team.query.all()
        schedule = []
        
        for team in teams:
            # Get team bookings
            bookings = Booking.query.filter_by(team_id=team.id).all()
            booking_data = [booking.to_dict() for booking in bookings]
            
            schedule.append({
                'team': team.to_dict(),
                'bookings': booking_data
            })
        
        return jsonify({
            'schedule': schedule
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching schedule', 'error': str(e)}), 500
