from app import create_app
from models import db, User, Team, TeamMember

app = create_app()

with app.app_context():
    # Create a test user if not exists
    user = User.query.filter_by(email="test@example.com").first()
    if not user:
        user = User(name="Test User", email="test@example.com", role="user")
        user.set_password("newpassword123")
        db.session.add(user)
        db.session.commit()
        print("Created test user")
    else:
        print("Test user already exists")
    
    # Create a test team
    team = Team(name="Test Team", leader_id=user.id)
    db.session.add(team)
    db.session.commit()
    print(f"Created team: {team.name}")
    
    # Add user as team member
    team_member = TeamMember(team_id=team.id, user_id=user.id, role="leader")
    db.session.add(team_member)
    db.session.commit()
    print(f"Added user as team member with role: {team_member.role}")
    
    # Fetch and display team info
    fetched_team = Team.query.get(team.id)
    print(f"Team info: {fetched_team.to_dict()}")