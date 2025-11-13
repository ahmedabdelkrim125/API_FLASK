from app import create_app
from models import db, User, Field, Facility

def seed_data():
    app = create_app()
    
    with app.app_context():
        # Check if data already exists
        if Field.query.first():
            print("Data already exists. Skipping seeding.")
            return
        
        # Create sample field owners
        owner1 = User(name="Field Owner 1", email="owner1@example.com", phone="0123456789", role="owner")
        owner1.set_password("password123")
        
        owner2 = User(name="Field Owner 2", email="owner2@example.com", phone="0123456780", role="owner")
        owner2.set_password("password123")
        
        db.session.add(owner1)
        db.session.add(owner2)
        db.session.flush()
        
        # Create sample fields in Cairo and Giza
        fields_data = [
            {
                "name": "ON Time Field",
                "location": "6th of October",
                "governorate": "giza",
                "price_per_hour": 250.0,
                "description": "Well-maintained football field with excellent facilities",
                "latitude": 29.9409,
                "longitude": 30.9179,
                "owner_id": owner1.id
            },
            {
                "name": "Al Ahly Field",
                "location": "Nasr City",
                "governorate": "cairo",
                "price_per_hour": 400.0,
                "description": "Professional football field with premium amenities",
                "latitude": 30.0444,
                "longitude": 31.3472,
                "owner_id": owner2.id
            },
            {
                "name": "Zamalek Field",
                "location": "Mohandessin",
                "governorate": "cairo",
                "price_per_hour": 350.0,
                "description": "High-quality football pitch with changing rooms",
                "latitude": 30.0626,
                "longitude": 31.2077,
                "owner_id": owner1.id
            },
            {
                "name": "Nogoom October Field",
                "location": "Sheikh Zayed",
                "governorate": "giza",
                "price_per_hour": 250.0,
                "description": "Modern football field with synthetic turf",
                "latitude": 30.0203,
                "longitude": 30.9691,
                "owner_id": owner2.id
            },
            {
                "name": "Abtal Masr Field",
                "location": "Haram",
                "governorate": "giza",
                "price_per_hour": 180.0,
                "description": "Affordable football field with basic facilities",
                "latitude": 29.9886,
                "longitude": 31.1342,
                "owner_id": owner1.id
            }
        ]
        
        facilities_data = [
            ["Parking", "Changing Rooms", "Showers", "Cafeteria"],
            ["Parking", "Changing Rooms", "Showers", "Floodlights", "Cafeteria"],
            ["Parking", "Changing Rooms", "Showers", "Floodlights"],
            ["Parking", "Changing Rooms", "Showers", "Synthetic Turf"],
            ["Parking", "Changing Rooms"]
        ]
        
        for i, field_data in enumerate(fields_data):
            field = Field(**field_data)
            db.session.add(field)
            db.session.flush()
            
            # Add facilities for this field
            for facility_name in facilities_data[i]:
                facility = Facility()
                facility.field_id = field.id
                facility.name = facility_name
                db.session.add(facility)
        
        # Create sample users
        user1 = User(name="Ahmed Mohamed", email="ahmed@example.com", phone="0101234567", role="user")
        user1.set_password("password123")
        
        user2 = User(name="Sara Hassan", email="sara@example.com", phone="0112345678", role="user")
        user2.set_password("password123")
        
        db.session.add(user1)
        db.session.add(user2)
        
        db.session.commit()
        print("Sample data seeded successfully!")

if __name__ == "__main__":
    seed_data()