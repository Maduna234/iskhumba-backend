import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret')

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Sandile@2004')
    DB_NAME = os.getenv('DB_NAME', 'iskhumba_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))

    # Escape '@' in password if present
    if DB_PASSWORD:
        escaped = DB_PASSWORD.replace('@', '%40')
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{escaped}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    CORS_ORIGINS = ['http://localhost:5001', 'http://127.0.0.1:5001', 'http://localhost:3000']