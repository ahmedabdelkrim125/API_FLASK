# Simple Postman Collection for Football Fields API

This is a simplified Postman collection for testing the Football Fields API. It contains the essential endpoints to get you started with testing the API.

## How to Import the Collection

1. Open Postman
2. Click on the "Import" button in the top left corner
3. Select the "Upload Files" tab
4. Choose the `Football_Fields_API_Simple_Collection.json` file from this directory
5. Click "Open" to import the collection

## How to Use the Collection

### 1. Authentication
- First, register a new user using the "Register" endpoint
- Then, log in using the "Login" endpoint to get a JWT token
- Copy the token from the response and set it in the collection variables

### 2. Setting the JWT Token
- Click on the collection name "Football Fields API - Simple Collection"
- Go to the "Variables" tab
- Set the value of the `token` variable to your JWT token (without the "Bearer " prefix)
- Click "Save"

### 3. Testing Endpoints
- You can now test all the endpoints in the collection
- The token will be automatically included in the Authorization header for protected endpoints

## Included Endpoints

### Authentication
- Register
- Login

### Fields
- Get All Fields
- Get Field by ID
- Create Field
- Update Field

### Bookings
- Create Booking
- Get User Bookings
- Get Field Bookings

### Reviews
- Create Review

## Notes
- Make sure the API server is running on `http://127.0.0.1:5000` before testing
- The sample data in the requests can be modified as needed
- Remember to update the token when it expires