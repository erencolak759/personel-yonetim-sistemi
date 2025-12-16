import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hr_portal_secret_key_2025')
    DEBUG = os.environ.get('DEBUG', True)