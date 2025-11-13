# Football Fields API - Postman Collection

This document explains how to use the Postman collection for testing the Football Fields API.

## Collection Overview

The Postman collection includes requests for all API endpoints, organized into logical folders:

1. **Authentication** - User registration, login, and password recovery
2. **Fields** - Football field management
3. **Bookings** - Field booking functionality
4. **Reviews** - Field review system
5. **Teams** - Team management features
6. **Payments** - Payment processing
7. **Clubs** - Club details and information

## How to Import the Collection

1. Open Postman
2. Click on "Import" in the top left corner
3. Select the `Football_Fields_API_Complete_Collection.json` file
4. The collection will be imported with all requests organized in folders

## Environment Variables

The collection uses a variable `{{token}}` for JWT authentication. After logging in:

1. Copy the access token from the login response
2. In Postman, go to the "Environment" tab
3. Set the `token` variable to the copied JWT token
4. Now all authenticated requests will use this token

## Testing the API

### 1. Start the Application
Make sure the Flask application is running:
```bash
python run.py
```

### 2. Register a User
Use the "Register" request in the Authentication folder to create a new user.

### 3. Login
Use the "Login" request to authenticate and get a JWT token.

### 4. Set the Token
Copy the token from the login response and set it in your Postman environment.

### 5. Test Endpoints
Now you can test any of the authenticated endpoints using the token.

## Available Payment Methods

The payment system supports these methods:
- `vodafone_cash`
- `etisalat_cash`
- `orange_cash`
- `we_pay`
- `visa`
- `mastercard`

## Team Roles

- **Leader**: Can create teams and remove members
- **Member**: Can join teams and participate in bookings

## Club Details

Club information includes:
- Club owner information
- All fields owned by the club
- Registered teams
- Booking schedules
- Reviews and ratings
- Facilities across all fields

## Notes

- The API runs on `http://127.0.0.1:5000` by default
- All API endpoints are prefixed with `/api`
- JWT tokens expire after 1 hour
- Some endpoints require specific user roles (user/owner)