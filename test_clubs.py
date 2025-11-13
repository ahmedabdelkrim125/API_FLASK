from app import create_app
from models import db, User, Field, Facility

app = create_app()

with app.app_context():
    # Create a test club owner if not exists
    club_owner = User.query.filter_by(email="clubowner@example.com").first()
    if not club_owner:
        club_owner = User(
            name="Test Club Owner",
            email="clubowner@example.com",
            role="owner"
        )
        club_owner.set_password("clubpassword123")
        db.session.add(club_owner)
        db.session.commit()
        print("Created club owner")
    else:
        print(f"Found club owner: {club_owner.name}")
    
    # Create a test field for the club
    field = Field.query.filter_by(owner_id=club_owner.id).first()
    if not field:
        field = Field(
            name="Test Club Field",
            location="Downtown",
            governorate="cairo",
            price_per_hour=300.0,
            description="Premium football field",
            owner_id=club_owner.id
        )
        db.session.add(field)
        db.session.commit()
        
        # Add some facilities
        facilities = ["Parking", "Changing Rooms", "Showers", "Cafeteria"]
        for facility_name in facilities:
            facility = Facility(
                field_id=field.id,
                name=facility_name
            )
            db.session.add(facility)
        
        db.session.commit()
        print("Created club field with facilities")
    else:
        print("Using existing club field")
    
    print(f"Club owner ID: {club_owner.id}")
    print(f"Field ID: {field.id}")