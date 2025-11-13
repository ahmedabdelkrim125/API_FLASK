from setuptools import setup, find_packages

setup(
    name="football-fields-api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.0.5",
        "Flask-JWT-Extended==4.5.3",
        "Flask-Bcrypt==1.0.1",
        "Flask-Cors==4.0.0",
        "PyMySQL==1.1.0",
        "psycopg2==2.9.7",
        "python-dotenv==1.0.0"
    ],
    entry_points={
        'console_scripts': [
            'football-fields-api=run:main',
        ],
    },
)