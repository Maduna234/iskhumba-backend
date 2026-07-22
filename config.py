import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env if present

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')

    # Render sets DATABASE_URL automatically when you attach a PostgreSQL DB
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    # SQLAlchemy 1.4+ uses this directly (postgresql://...)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary credentials (set these in Render environment)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    # Local upload fallback (not used if Cloudinary is configured)
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # CORS – allow your frontend domain
    CORS_ORIGINS = [
        'https://maduna234.github.io',
        'http://localhost:5001',   # for local testing
        'http://127.0.0.1:5001'
    ]
