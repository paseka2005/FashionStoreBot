# config.py
import os
from datetime import timedelta

# Базовые настройки
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345-secure-vogue-elite-premium'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/fashion_store.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Настройки магазина
    SHOP_NAME = "VOGUE ÉLITE"
    SHOP_SLOGAN = "Искусство стиля"
    SHOP_PHONE = "+7 (495) 123-45-67"
    SHOP_EMAIL = "info@vogue-elite.ru"
    SUPPORT_USERNAME = "@Lexaa_161"
    FREE_DELIVERY_THRESHOLD = 200000
    DELIVERY_COST = 2000
    CURRENCY = "₽"
    
    # Настройки API
    API_PREFIX = '/api'
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
