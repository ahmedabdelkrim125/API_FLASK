from flask_bcrypt import Bcrypt
from datetime import datetime, time
# Import db from app.py
from app import db

bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # user or owner
    
    def __init__(self, name=None, email=None, password=None, phone=None, role='user'):
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if password is not None:
            self.password = password
        if phone is not None:
            self.phone = phone
        if role is not None:
            self.role = role
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    fields = db.relationship('Field', backref='owner', lazy=True)
    team_memberships = db.relationship('TeamMember', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role
        }

class OTP(db.Model):
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def __init__(self, email=None, otp_code=None, expires_at=None):
        if email is not None:
            self.email = email
        if otp_code is not None:
            self.otp_code = otp_code
        if expires_at is not None:
            self.expires_at = expires_at

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # User who created the team (team leader)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    leader = db.relationship('User', foreign_keys=[leader_id])
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='team', lazy=True)
    
    def __init__(self, name=None, leader_id=None):
        if name is not None:
            self.name = name
        if leader_id is not None:
            self.leader_id = leader_id
    
    def to_dict(self):
        # Count members without using len() on the relationship
        members_count = db.session.query(TeamMember).filter(TeamMember.team_id == self.id).count()
        return {
            'id': self.id,
            'name': self.name,
            'leader_id': self.leader_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'members_count': members_count
        }

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # member or leader
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a user can only be a member of a team once
    __table_args__ = (db.UniqueConstraint('team_id', 'user_id', name='unique_team_user'),)
    
    def __init__(self, team_id=None, user_id=None, role='member'):
        if team_id is not None:
            self.team_id = team_id
        if user_id is not None:
            self.user_id = user_id
        if role is not None:
            self.role = role
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='EGP')  # EGP, USD, etc.
    payment_method = db.Column(db.String(50), nullable=False)  # vodafone_cash, etisalat_cash, orange_cash, we_pay, visa, mastercard
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)  # External payment gateway transaction ID
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    booking = db.relationship('Booking', backref='payment', lazy=True)
    user = db.relationship('User', backref='payments', lazy=True)
    
    def __init__(self, booking_id=None, user_id=None, amount=None, currency='EGP', payment_method=None):
        if booking_id is not None:
            self.booking_id = booking_id
        if user_id is not None:
            self.user_id = user_id
        if amount is not None:
            self.amount = amount
        if currency is not None:
            self.currency = currency
        if payment_method is not None:
            self.payment_method = payment_method
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Field(db.Model):
    __tablename__ = 'fields'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    governorate = db.Column(db.String(50), nullable=False)  # cairo or giza
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    opening_time = db.Column(db.Time, nullable=False, default=lambda: time(8, 0))  # Default 8:00 AM
    closing_time = db.Column(db.Time, nullable=False, default=lambda: time(22, 0))  # Default 10:00 PM
    
    # Relationships
    bookings = db.relationship('Booking', backref='field', lazy=True)
    reviews = db.relationship('Review', backref='field', lazy=True)
    facilities = db.relationship('Facility', backref='field', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name=None, location=None, governorate=None, price_per_hour=None, description=None, 
                 image=None, owner_id=None, latitude=None, longitude=None, opening_time=None, closing_time=None):
        if name is not None:
            self.name = name
        if location is not None:
            self.location = location
        if governorate is not None:
            self.governorate = governorate
        if price_per_hour is not None:
            self.price_per_hour = price_per_hour
        if description is not None:
            self.description = description
        if image is not None:
            self.image = image
        if owner_id is not None:
            self.owner_id = owner_id
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if opening_time is not None:
            self.opening_time = opening_time
        if closing_time is not None:
            self.closing_time = closing_time
    
    def to_dict(self):
        # Access facilities through a direct query to avoid relationship issues
        from models import Facility
        facilities_list = []
        try:
            facilities = Facility.query.filter_by(field_id=self.id).all()
            facilities_list = [facility.to_dict() for facility in facilities]
        except:
            # If we can't access facilities, return empty list
            pass
        
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'governorate': self.governorate,
            'price_per_hour': self.price_per_hour,
            'description': self.description,
            'image': self.image,
            'owner_id': self.owner_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'opening_time': self.opening_time.isoformat() if self.opening_time else None,
            'closing_time': self.closing_time.isoformat() if self.closing_time else None,
            'facilities': facilities_list
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='confirmed')  # confirmed, cancelled
    
    # Database-level constraint to prevent double bookings
    __table_args__ = (
        db.CheckConstraint(
            "start_time < end_time", 
            name='check_start_before_end'
        ),
    )
    
    def __init__(self, user_id=None, team_id=None, field_id=None, date=None, start_time=None, end_time=None, total_price=None, status='confirmed'):
        if user_id is not None:
            self.user_id = user_id
        if team_id is not None:
            self.team_id = team_id
        if field_id is not None:
            self.field_id = field_id
        if date is not None:
            self.date = date
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        if total_price is not None:
            self.total_price = total_price
        if status is not None:
            self.status = status
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'field_id': self.field_id,
            'date': self.date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_price': self.total_price,
            'status': self.status
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id=None, field_id=None, rating=None, comment=None):
        if user_id is not None:
            self.user_id = user_id
        if field_id is not None:
            self.field_id = field_id
        if rating is not None:
            self.rating = rating
        if comment is not None:
            self.comment = comment
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'field_id': self.field_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }

class Facility(db.Model):
    __tablename__ = 'facilities'
    
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def __init__(self, field_id=None, name=None):
        if field_id is not None:
            self.field_id = field_id
        if name is not None:
            self.name = name
    
    def to_dict(self):
        return {
            'id': self.id,
            'field_id': self.field_id,
            'name': self.name
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # booking_confirmation, booking_cancellation, payment_success, etc.
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    field = db.relationship('Field', backref=db.backref('analytics', lazy=True))
    user = db.relationship('User', backref=db.backref('analytics', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'value': self.value,
            'date': self.date.isoformat() if self.date else None,
            'field_id': self.field_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
