# Football Fields Booking API

A Flask-based REST API for managing football fields in Cairo and Giza, Egypt. This API allows users to browse, book, and review football fields, while field owners can manage their fields and bookings.

## Features

- User authentication (JWT)
- Browse football fields by location
- View field details including pricing, facilities, and images
- Book fields for specific dates and times
- Review and rate fields
- Field owner dashboard for managing fields and bookings

## Technologies Used

- Flask
- SQLAlchemy (ORM)
- JWT for authentication
- SQLite (default, can be configured for MySQL/PostgreSQL)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables (copy .env.example to .env and modify as needed)
5. Initialize the database:
   ```
   python init_db.py
   ```
6. Seed the database with sample data (optional):
   ```
   python seed_data.py
   ```
7. Run the application:
   ```
   python app.py
   ```

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login and get access token

### Fields
- `GET /api/fields?governorate=giza` - Get fields (filter by governorate)
- `GET /api/fields/<id>` - Get field details
- `POST /api/fields` - Create a new field (owners only)
- `PUT /api/fields/<id>` - Update a field (owners only)

### Bookings
- `POST /api/bookings` - Create a new booking
- `GET /api/bookings/user/<id>` - Get user bookings
- `GET /api/bookings/field/<id>` - Get field bookings (owners only)

### Reviews
- `POST /api/reviews` - Create a new review

## Database Schema

The application uses 5 main tables:

1. **Users** - Store user information (players and field owners)
   - id, name, email, password, phone, role

2. **Fields** - Football field information
   - id, name, location, governorate, price_per_hour, description, image, owner_id

3. **Bookings** - Booking records
   - id, user_id, field_id, date, start_time, end_time, total_price, status

4. **Reviews** - User reviews and ratings
   - id, user_id, field_id, rating, comment

5. **Facilities** - Amenities offered by each field
   - id, field_id, name

## Sample Data

The API includes sample football fields in Cairo and Giza:

- ON Time Field – 6th of October – 250 EGP/hour
- Al Ahly Field – Nasr City – 400 EGP/hour
- Zamalek Field – Mohandessin – 350 EGP/hour
- Nogoom October Field – Sheikh Zayed – 250 EGP/hour
- Abtal Masr Field – Haram – 180 EGP/hour

## License

This project is licensed under the MIT License.