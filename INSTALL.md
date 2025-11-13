# Installation Guide

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

## Setup Instructions

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python init_db.py
   ```

5. **(Optional) Seed the database with sample data**:
   ```bash
   python seed_data.py
   ```

6. **Run the application**:
   ```bash
   python run.py
   ```

## Troubleshooting

If you encounter any import errors in your IDE before installing dependencies, this is normal. The errors will disappear once you've installed the required packages using `pip install -r requirements.txt`.

The required packages are:
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Bcrypt
- Flask-CORS
- PyMySQL
- psycopg2
- python-dotenv