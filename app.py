# app.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ КОД
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime, timedelta
import os
import json
import logging
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import random
import string
from functools import wraps
import traceback

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VogueEliteWeb')

app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-12345-secure-vogue-elite-premium')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'fashion_store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['JSON_AS_ASCII'] = False

# Создаем необходимые директории
for folder in ['instance', 'static/uploads', 'static/uploads/products']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Константы магазина
SHOP_NAME = "VOGUE ÉLITE"
SHOP_SLOGAN = "Искусство стиля"
SHOP_PHONE = "+7 (495) 123-45-67"
SHOP_EMAIL = "info@vogue-elite.ru"
SUPPORT_USERNAME = "@Lexaa_161"
FREE_DELIVERY_THRESHOLD = 200000  # 200,000 рублей
DELIVERY_COST = 2000  # 2,000 рублей
WEB_APP_URL = "https://fashionstorebot.onrender.com"
CURRENCY = "₽"

# Эмодзи для использования в шаблонах
class Emoji:
    LOGO = "✨"
    STAR = "⭐"
    VIP = "👑"
    LOCK = "🔒"
    CHECK = "✅"
    CANCEL = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    USER = "👤"
    MONEY = "💰"
    DRESS = "👗"
    SUIT = "👔"
    BLAZER = "🥼"
    PANTS = "👖"
    SKIRT = "👚"
    OUTERWEAR = "🧥"
    ACCESSORIES = "🧣"
    SHOES = "👠"
    BAG = "👜"
    JEWELRY = "💍"
    CART = "🛍️"
    FAVORITE = "❤️"
    ORDER = "📦"
    DELIVERY = "🚚"
    SIZE = "📏"
    COLOR = "🎨"
    CATEGORY = "🏷️"
    ARTICLE = "🔖"
    VIEW = "👁️"
    NEW = "🆕"
    EXCLUSIVE = "💎"
    BESTSELLER = "🔥"
    SALE = "🏷️"
    SUPPORT = "📞"
    WEBSITE = "🌐"
    PHONE = "📱"
    CLOCK = "⏰"
    MESSAGE = "💬"
    LINK = "🔗"
    FILTER = "🔍"
    NEXT = "➡️"
    BACK = "⬅️"
    SETTINGS = "⚙️"
    ADMIN = "🛡️"
    BROADCAST = "📢"
    STATS = "📊"
    USERS = "👥"
    KEYBOARD = "⌨️"
    BOT = "🤖"
    DATABASE = "🗄️"
    GIFT = "🎁"
    ATELIER = "✂️"
    TAG = "🏷️"
    FIRE = "🔥"
    HEART = "💖"
    SHIELD = "🛡️"
    CROWN = "👑"
    GEM = "💎"
    RING = "💍"
    WATCH = "⌚"
    PERFUME = "💄"
    SCISSORS = "✂️"
    TRUCK = "🚚"
    GLOBE = "🌍"
    FLAG = "🏁"
    SHOP = "🛒"
    BUG = "🐛"
    REFRESH = "🔄"

# Категории товаров
class Categories:
    DRESSES = "Платья"
    SUITS = "Костюмы"
    BLOUSES = "Блузы"
    PANTS = "Брюки"
    SKIRTS = "Юбки"
    JACKETS = "Куртки"
    COATS = "Пальто"
    ACCESSORIES = "Аксессуары"
    SHOES = "Обувь"
    BAGS = "Сумки"
    JEWELRY = "Украшения"
    PERFUMES = "Парфюмерия"
    WATCHES = "Часы"
    LINGERIE = "Нижнее белье"
    SWIMWEAR = "Купальники"

# Бренды
class Brands:
    GUCCI = "Gucci"
    CHANEL = "Chanel"
    Dior = "Dior"
    LOUIS_VUITTON = "Louis Vuitton"
    HERMES = "Hermès"
    PRADA = "Prada"
    VERSACE = "Versace"
    ARMANI = "Armani"
    BURBERRY = "Burberry"
    BALENCIAGA = "Balenciaga"
    SAINT_LAURENT = "Saint Laurent"
    VALENTINO = "Valentino"
    FENDI = "Fendi"
    DOLCE_ABBANA = "Dolce & Gabbana"
    BOTTEGA_VENETA = "Bottega Veneta"
    VOGUE_ELITE = "VOGUE ÉLITE"

# Настройка базы данных
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо войти в систему.'
login_manager.login_message_category = 'warning'

# Декоратор для API ответов
def api_response(func):
    """Декоратор для API маршрутов, возвращающий JSON"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, dict):
                return jsonify(result)
            elif isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict):
                return jsonify(result[0]), result[1]
            return result
        except Exception as e:
            logger.error(f"API Error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    return wrapper

# Модели базы данных
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True, unique=True)
    password_hash = db.Column(db.String(200), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_vip = db.Column(db.Boolean, default=False)
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(50), unique=True, nullable=True)
    notification_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def get_cart_count(self):
        return Cart.query.filter_by(user_id=self.id).count()
    
    def get_cart_total(self):
        cart_items = Cart.query.filter_by(user_id=self.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items if item.product)
        return total
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    detailed_description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    discount = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=True)
    size = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(100), nullable=True)
    material = db.Column(db.String(200), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    season = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    images = db.Column(db.Text, nullable=True)
    is_new = db.Column(db.Boolean, default=False)
    is_hit = db.Column(db.Boolean, default=False)
    is_exclusive = db.Column(db.Boolean, default=False)
    is_limited = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    stock = db.Column(db.Integer, default=0)
    reserved = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float, nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    care_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_formatted_price(self):
        return f"{int(self.price):,}".replace(",", " ")
    
    def get_formatted_old_price(self):
        if self.old_price:
            return f"{int(self.old_price):,}".replace(",", " ")
        return None
    
    def get_discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
    def get_images_list(self):
        if self.images:
            try:
                return json.loads(self.images)
            except:
                return []
        return []
    
    def __repr__(self):
        return f'<Product {self.article} - {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='new')  # new, processing, shipped, delivered, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    delivery_cost = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_type = db.Column(db.String(50), default='courier')
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    promo_code = db.Column(db.String(50), nullable=True)
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    items_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    def get_formatted_total(self):
        return f"{int(self.total_amount):,}".replace(",", " ")
    
    def get_formatted_final(self):
        return f"{int(self.final_amount):,}".replace(",", " ")
    
    def get_items(self):
        try:
            return json.loads(self.items_json)
        except:
            return []
    
    def get_status_display(self):
        status_map = {
            'new': 'Новый',
            'processing': 'В обработке',
            'shipped': 'Отправлен',
            'delivered': 'Доставлен',
            'cancelled': 'Отменен'
        }
        return status_map.get(self.status, self.status)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    selected_size = db.Column(db.String(50), nullable=True)
    selected_color = db.Column(db.String(50), nullable=True)
    price_at_addition = db.Column(db.Float, nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_entries', lazy=True))
    
    def get_total(self):
        return self.product.price * self.quantity
    
    def __repr__(self):
        return f'<Cart {self.user_id} - {self.product_id}>'

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    discount_percent = db.Column(db.Integer, default=0)
    discount_amount = db.Column(db.Float, default=0.0)
    min_order_amount = db.Column(db.Float, default=0.0)
    usage_limit = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self, order_amount=0):
        if not self.is_active:
            return False
        
        if self.valid_from and datetime.utcnow() < self.valid_from:
            return False
        
        if self.valid_until and datetime.utcnow() > self.valid_until:
            return False
        
        if self.min_order_amount > 0 and order_amount < self.min_order_amount:
            return False
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        
        return True
    
    def get_discount(self, order_amount):
        if self.discount_amount > 0:
            return min(self.discount_amount, order_amount)
        elif self.discount_percent > 0:
            return order_amount * self.discount_percent / 100
        return 0
    
    def __repr__(self):
        return f'<PromoCode {self.code}>'

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('wishlist_entries', lazy=True))
    
    def __repr__(self):
        return f'<Wishlist {self.user_id} - {self.product_id}>'

class CompareList(db.Model):
    __tablename__ = 'compare_list'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('compare_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('compare_entries', lazy=True))
    
    def __repr__(self):
        return f'<CompareList {self.user_id} - {self.product_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    
    def __repr__(self):
        return f'<Notification {self.title}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Инициализация базы данных
def init_database():
    """Инициализация базы данных с тестовыми данными"""
    with app.app_context():
        try:
            # Создаем таблицы
            db.create_all()
            logger.info("Таблицы базы данных созданы")
            
            # Проверяем, нужно ли создавать тестовые данные
            if User.query.count() == 0:
                logger.info("Создание тестовых данных...")
                
                # Создаем администратора
                admin = User(
                    username='admin',
                    first_name='Администратор',
                    last_name='VOGUE ÉLITE',
                    email='admin@vogue-elite.ru',
                    phone='+7 (999) 999-99-99',
                    is_admin=True,
                    is_vip=True,
                    referral_code='ADMIN001',
                    notification_enabled=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Создаем тестового пользователя
                test_user = User(
                    username='vip_client',
                    first_name='Анна',
                    last_name='Иванова',
                    email='anna@example.com',
                    phone='+7 (999) 888-77-66',
                    is_admin=False,
                    is_vip=True,
                    total_orders=15,
                    total_spent=1500000,
                    referral_code='VIP001',
                    notification_enabled=True
                )
                test_user.set_password('test123')
                db.session.add(test_user)
                
                # Создаем обычного пользователя
                regular_user = User(
                    username='regular_user',
                    first_name='Мария',
                    last_name='Петрова',
                    email='maria@example.com',
                    phone='+7 (999) 777-66-55',
                    is_admin=False,
                    is_vip=False,
                    total_orders=3,
                    total_spent=450000,
                    referral_code='USER001',
                    notification_enabled=True
                )
                regular_user.set_password('user123')
                db.session.add(regular_user)
                
                db.session.commit()
                logger.info("Созданы тестовые пользователи")
            
            if Product.query.count() == 0:
                logger.info("Создание товаров...")
                
                # Список люксовых товаров (цены в рублях)
                luxury_products = [
                    # Платья
                    {
                        'article': 'VE2024001',
                        'name': 'Вечернее платье Gucci Première с кристаллами Swarovski',
                        'description': 'Эксклюзивное вечернее платье от Gucci с ручной вышивкой кристаллами Swarovski, выполненное из французского кружева и натурального шелка.',
                        'detailed_description': 'Это платье является частью лимитированной коллекции Gucci Première. Каждое платье создается вручную итальянскими мастерами в течение 200 часов. Используется уникальное сочетание французского кружева Leavers, натурального шелка из Комо и более 5000 кристаллов Swarovski.',
                        'price': 1250000,
                        'old_price': 1450000,
                        'discount': 14,
                        'category': Categories.DRESSES,
                        'subcategory': 'Вечерние платья',
                        'size': 'XS,S,M,L,XL',
                        'color': 'Черный, Золотой',
                        'material': 'Натуральный шелк, Французское кружево, Кристаллы Swarovski',
                        'brand': Brands.GUCCI,
                        'season': 'Осень-Зима 2024',
                        'country': 'Италия',
                        'image_url': '/static/img/products/product-1.jpg',
                        'images': json.dumps([
                            '/static/img/products/product-1.jpg',
                            '/static/img/products/product-2.jpg',
                            '/static/img/products/product-3.jpg'
                        ]),
                        'is_new': True,
                        'is_exclusive': True,
                        'is_limited': True,
                        'stock': 3,
                        'weight': 1.2,
                        'dimensions': 'Длина: 145 см, Обхват груди: 86-96 см',
                        'care_instructions': 'Только химчистка. Хранить в защитном чехле при комнатной температуре.'
                    },
                    {
                        'article': 'VE2024002',
                        'name': 'Коктейльное платье Dior New Look из итальянского шелка',
                        'description': 'Элегантное коктейльное платье в стиле New Look от Christian Dior из итальянского шелка с запахом и поясом.',
                        'detailed_description': 'Платье вдохновлено архивными моделями Dior 1950-х годов. Выполнено из двойного итальянского шелка с запахом, подчеркивающим талию. Пояс из натуральной кожи с фирменной пряжкой CD.',
                        'price': 650000,
                        'old_price': None,
                        'discount': 0,
                        'category': Categories.DRESSES,
                        'subcategory': 'Коктейльные платья',
                        'size': 'XS,S,M,L',
                        'color': 'Белый, Черный, Бордовый',
                        'material': 'Итальянский шелк, Натуральная кожа',
                        'brand': Brands.Dior,
                        'season': 'Весна-Лето 2024',
                        'country': 'Франция',
                        'image_url': '/static/img/products/product-2.jpg',
                        'is_new': True,
                        'is_hit': True,
                        'stock': 12,
                        'weight': 0.8
                    },
                    
                    # Костюмы
                    {
                        'article': 'VE2024003',
                        'name': 'Костюм-тройка Brioni из супер-150 шерсти',
                        'description': 'Премиальный костюм-тройка от Brioni из шерсти супер-150 с подкладкой из натурального шелка.',
                        'detailed_description': 'Костюм сшит по индивидуальным лекалам из шерсти супер-150 (Super 150s). Подкладка жилета и пиджака выполнена из натурального шелка. Все пуговицы из перламутра. Ручная работа более 80 часов.',
                        'price': 850000,
                        'old_price': 950000,
                        'discount': 11,
                        'category': Categories.SUITS,
                        'subcategory': 'Классические костюмы',
                        'size': '46,48,50,52,54,56',
                        'color': 'Темно-синий, Серый, Черный',
                        'material': 'Шерсть супер-150, Натуральный шелк',
                        'brand': 'Brioni',
                        'season': 'Круглогодичный',
                        'country': 'Италия',
                        'image_url': '/static/img/products/product-3.jpg',
                        'is_exclusive': True,
                        'stock': 8
                    },
                    
                    # Сумки
                    {
                        'article': 'VE2024004',
                        'name': 'Сумка Hermès Birkin 30 из кожи Niloticus Crocodile',
                        'description': 'Легендарная сумка Hermès Birkin 30 из кожи нильского крокодила с бриллиантовой застежкой.',
                        'detailed_description': 'Сумка ручной работы из кожи нильского крокодила исключительного качества. Застежка украшена бриллиантами общим весом 2.5 карата. Фурнитура из белого золота 18к. Время изготовления: более 48 часов ручной работы.',
                        'price': 8500000,
                        'old_price': 9200000,
                        'discount': 8,
                        'category': Categories.BAGS,
                        'subcategory': 'Клатчи',
                        'size': '30 см',
                        'color': 'Черный, Бордо, Изумрудный',
                        'material': 'Кожа нильского крокодила, Белое золото, Бриллианты',
                        'brand': Brands.HERMES,
                        'season': 'Круглогодичный',
                        'country': 'Франция',
                        'image_url': '/static/img/products/product-4.jpg',
                        'is_exclusive': True,
                        'is_limited': True,
                        'stock': 1
                    },
                    
                    # Обувь
                    {
                        'article': 'VE2024005',
                        'name': 'Туфли Christian Louboutin So Kate 120mm',
                        'description': 'Культовые туфли-лодочки Christian Louboutin So Kate с красной подошвой высотой 120 мм.',
                        'detailed_description': 'Туфли из лаковой кожи с фирменной красной подошвой. Высота каблука 120 мм. Ручная отделка итальянскими мастерами. Колодка обеспечивает максимальный комфорт при ходьбе.',
                        'price': 185000,
                        'old_price': 210000,
                        'discount': 12,
                        'category': Categories.SHOES,
                        'subcategory': 'Туфли-лодочки',
                        'size': '35,36,37,38,39,40',
                        'color': 'Черный, Красный, Нюдовый',
                        'material': 'Лаковая кожа',
                        'brand': 'Christian Louboutin',
                        'season': 'Круглогодичный',
                        'country': 'Италия',
                        'image_url': '/static/img/products/product-5.jpg',
                        'is_new': True,
                        'is_hit': True,
                        'stock': 15
                    },
                    
                    # Украшения
                    {
                        'article': 'VE2024006',
                        'name': 'Ожерелье Cartier Love из белого золота с бриллиантами',
                        'description': 'Эксклюзивное ожерелье из коллекции Cartier Love из белого золота 18к с бриллиантами.',
                        'detailed_description': 'Ожерелье состоит из 127 бриллиантов общим весом 3.85 карата. Застежка в виде винта - символ коллекции Love. Каждый бриллиант имеет сертификат GIA.',
                        'price': 4200000,
                        'old_price': None,
                        'discount': 0,
                        'category': Categories.JEWELRY,
                        'subcategory': 'Ожерелья',
                        'size': 'Длина 45 см',
                        'color': 'Белое золото',
                        'material': 'Белое золото 18к, Бриллианты',
                        'brand': 'Cartier',
                        'season': 'Круглогодичный',
                        'country': 'Франция',
                        'image_url': '/static/img/products/product-6.jpg',
                        'is_exclusive': True,
                        'stock': 2
                    },
                    
                    # Пальто
                    {
                        'article': 'VE2024007',
                        'name': 'Кашемировое пальто Max Mara Teddy Bear',
                        'description': 'Знаменитое пальто Max Mara Teddy Bear из двойного кашемира с капюшоном.',
                        'detailed_description': 'Пальто из двойного итальянского кашемира плотностью 450 гр/м². Утеплено гусиным пухом. Капюшон отстегивается. Карманы с магнитными застежками.',
                        'price': 450000,
                        'old_price': 520000,
                        'discount': 13,
                        'category': Categories.COATS,
                        'subcategory': 'Зимние пальто',
                        'size': 'XS,S,M,L,XL',
                        'color': 'Песочный, Черный, Кремовый',
                        'material': 'Двойной кашемир, Гусиный пух',
                        'brand': 'Max Mara',
                        'season': 'Осень-Зима',
                        'country': 'Италия',
                        'image_url': '/static/img/products/product-7.jpg',
                        'is_hit': True,
                        'stock': 10
                    },
                    
                    # Часы
                    {
                        'article': 'VE2024008',
                        'name': 'Наручные часы Rolex Datejust 41',
                        'description': 'Классические часы Rolex Datejust 41 из белого золота с бриллиантовым циферблатом.',
                        'detailed_description': 'Часы из белого золота 18к. Циферблат украшен 78 бриллиантами. Автоматический механизм с запасом хода 70 часов. Водонепроницаемость 100 метров. Сертификат COSC.',
                        'price': 3800000,
                        'old_price': 4100000,
                        'discount': 7,
                        'category': 'Часы',
                        'subcategory': 'Мужские часы',
                        'size': '41 мм',
                        'color': 'Белое золото',
                        'material': 'Белое золото 18к, Сапфировое стекло, Бриллианты',
                        'brand': 'Rolex',
                        'season': 'Круглогодичный',
                        'country': 'Швейцария',
                        'image_url': '/static/img/products/product-8.jpg',
                        'is_exclusive': True,
                        'stock': 3
                    },
                    
                    # Парфюмерия
                    {
                        'article': 'VE2024009',
                        'name': 'Парфюм Chanel №5 Parfum',
                        'description': 'Культовый парфюм Chanel №5 в версии Parfum, лимитированная коллекция.',
                        'detailed_description': 'Parfum концентрация 30%. Флакон из хрусталя Baccarat ручной работы. Ограниченный тираж 1000 экземпляров в мире. В комплекте: флакон, сертификат, бархатный чехол.',
                        'price': 350000,
                        'old_price': None,
                        'discount': 0,
                        'category': 'Парфюмерия',
                        'subcategory': 'Женские ароматы',
                        'size': '250 мл',
                        'color': 'Прозрачный',
                        'material': 'Хрусталь Baccarat',
                        'brand': Brands.CHANEL,
                        'season': 'Круглогодичный',
                        'country': 'Франция',
                        'image_url': '/static/img/products/product-9.jpg',
                        'is_limited': True,
                        'stock': 5
                    },
                    
                    # Аксессуары
                    {
                        'article': 'VE2024010',
                        'name': 'Шелковый шарф Hermès 90x90 из коллекции "Легенды Парижа"',
                        'description': 'Шелковый шарф Hermès размером 90x90 см из коллекции "Легенды Парижа", ручная роспись.',
                        'detailed_description': 'Шарф из 100% натурального шелка twill. Ручная роспись французскими художниками. Ограниченная серия 500 экземпляров. Упакован в фирменную оранжевую коробку Hermès.',
                        'price': 280000,
                        'old_price': 320000,
                        'discount': 13,
                        'category': Categories.ACCESSORIES,
                        'subcategory': 'Шарфы',
                        'size': '90x90 см',
                        'color': 'Синий, Золотой, Белый',
                        'material': 'Натуральный шелк',
                        'brand': Brands.HERMES,
                        'season': 'Весна-Осень',
                        'country': 'Франция',
                        'image_url': '/static/img/products/product-10.jpg',
                        'is_new': True,
                        'stock': 7
                    }
                ]
                
                # Добавляем товары в базу
                for prod_data in luxury_products:
                    product = Product(**prod_data)
                    db.session.add(product)
                
                db.session.commit()
                logger.info(f"Создано {len(luxury_products)} люксовых товаров")
            
            if PromoCode.query.count() == 0:
                logger.info("Создание промокодов...")
                
                # Создаем промокоды
                promo_codes = [
                    {
                        'code': 'WELCOME15',
                        'description': 'Приветственная скидка для новых клиентов',
                        'discount_percent': 15,
                        'min_order_amount': 0,
                        'usage_limit': 1000,
                        'valid_until': datetime(2024, 12, 31)
                    },
                    {
                        'code': 'VIP25',
                        'description': 'Скидка для VIP клиентов',
                        'discount_percent': 25,
                        'min_order_amount': 500000,
                        'usage_limit': 500,
                        'valid_until': datetime(2024, 12, 31)
                    },
                    {
                        'code': 'SUMMER2024',
                        'description': 'Скидка на летнюю коллекцию',
                        'discount_percent': 20,
                        'min_order_amount': 300000,
                        'usage_limit': 300,
                        'valid_until': datetime(2024, 8, 31)
                    },
                    {
                        'code': 'FIRSTORDER',
                        'description': 'Скидка на первый заказ',
                        'discount_percent': 10,
                        'min_order_amount': 100000,
                        'usage_limit': 2000,
                        'valid_until': datetime(2024, 12, 31)
                    }
                ]
                
                for promo_data in promo_codes:
                    promo = PromoCode(**promo_data)
                    db.session.add(promo)
                
                db.session.commit()
                logger.info("Созданы промокоды")
            
            logger.info("Инициализация базы данных завершена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            db.session.rollback()

# Контекстный процессор для передачи данных во все шаблоны
@app.context_processor
def inject_globals():
    cart_count = 0
    cart_total = 0
    
    if current_user.is_authenticated:
        cart_count = current_user.get_cart_count()
        cart_total = current_user.get_cart_total()
    
    return {
        'shop_name': SHOP_NAME,
        'shop_slogan': SHOP_SLOGAN,
        'shop_phone': SHOP_PHONE,
        'shop_email': SHOP_EMAIL,
        'support_username': SUPPORT_USERNAME,
        'emoji': Emoji,
        'categories': Categories,
        'brands': Brands,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'delivery_cost': DELIVERY_COST,
        'currency': CURRENCY,
        'web_app_url': WEB_APP_URL,
        'current_year': datetime.now().year,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'current_user': current_user,
        'format_price': lambda price: f"{int(price):,}".replace(",", " ") if price else "0"
    }

# Форматирование чисел
@app.template_filter('format_price')
def format_price_filter(price):
    if price is None:
        return "0"
    return f"{int(price):,}".replace(",", " ")

# Главная страница
@app.route('/')
def index():
    try:
        new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(Product.created_at.desc()).limit(8).all()
        hit_products = Product.query.filter_by(is_hit=True, is_active=True).order_by(db.func.random()).limit(8).all()
        exclusive_products = Product.query.filter_by(is_exclusive=True, is_active=True).order_by(db.func.random()).limit(8).all()
        
        # Статистика магазина
        total_products = Product.query.filter_by(is_active=True).count()
        total_categories = db.session.query(Product.category).distinct().count()
        
        return render_template('index.html',
                             new_products=new_products,
                             hit_products=hit_products,
                             exclusive_products=exclusive_products,
                             total_products=total_products,
                             total_categories=total_categories)
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        flash('Произошла ошибка при загрузке главной страницы', 'error')
        return render_template('index.html',
                             new_products=[],
                             hit_products=[],
                             exclusive_products=[],
                             total_products=0,
                             total_categories=0)

# Каталог товаров
@app.route('/catalog')
def catalog_page():
    try:
        category = request.args.get('category', 'all')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        query = Product.query.filter_by(is_active=True)
        
        if category != 'all':
            query = query.filter_by(category=category)
        
        # Сортировка
        sort = request.args.get('sort', 'newest')
        if sort == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort == 'discount':
            query = query.filter(Product.discount > 0).order_by(Product.discount.desc())
        elif sort == 'popular':
            query = query.order_by(Product.is_hit.desc(), Product.created_at.desc())
        else:  # newest
            query = query.order_by(Product.created_at.desc())
        
        products = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Получаем все категории для фильтра
        categories = db.session.query(Product.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        # Получаем бренды
        brands = db.session.query(Product.brand).distinct().all()
        brands = [b[0] for b in brands if b[0]]
        
        # Получаем цены для фильтра
        min_price = db.session.query(db.func.min(Product.price)).filter_by(is_active=True).scalar() or 0
        max_price = db.session.query(db.func.max(Product.price)).filter_by(is_active=True).scalar() or 100000
        
        return render_template('catalog.html',
                             products=products,
                             categories=categories,
                             brands=brands,
                             min_price=int(min_price),
                             max_price=int(max_price),
                             current_category=category,
                             current_sort=sort,
                             current_page=page)
    except Exception as e:
        logger.error(f"Ошибка загрузки каталога: {e}")
        flash('Произошла ошибка при загрузке каталога', 'error')
        return redirect(url_for('index'))

# Страница товара
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        if not product.is_active:
            flash('Этот товар временно недоступен', 'warning')
            return redirect(url_for('catalog_page'))
        
        # Получаем изображения
        images = product.get_images_list()
        if product.image_url and product.image_url not in images:
            images.insert(0, product.image_url)
        
        # Аналогичные товары
        similar_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id,
            Product.is_active == True
        ).order_by(db.func.random()).limit(4).all()
        
        # Получаем размеры и цвета
        sizes = []
        if product.size:
            sizes = [s.strip() for s in product.size.split(',')]
        
        colors = []
        if product.color:
            colors = [c.strip() for c in product.color.split(',')]
        
        # Проверяем, есть ли товар в избранном
        in_wishlist = False
        if current_user.is_authenticated:
            in_wishlist = Wishlist.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first() is not None
        
        # Проверяем, есть ли товар в сравнении
        in_compare = False
        if current_user.is_authenticated:
            in_compare = CompareList.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first() is not None
        
        return render_template('product.html',
                             product=product,
                             images=images,
                             similar_products=similar_products,
                             sizes=sizes,
                             colors=colors,
                             in_wishlist=in_wishlist,
                             in_compare=in_compare)
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы товара {product_id}: {e}")
        flash('Товар не найден', 'error')
        return redirect(url_for('catalog_page'))

# Корзина
@app.route('/cart')
@login_required
def cart_page():
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        # Проверяем доступность товаров
        unavailable_items = []
        available_items = []
        total = 0
        
        for item in cart_items:
            if item.product and item.product.is_active and item.product.stock >= item.quantity:
                item_total = item.product.price * item.quantity
                total += item_total
                available_items.append({
                    'item': item,
                    'total': item_total
                })
            else:
                unavailable_items.append(item)
        
        # Удаляем недоступные товары
        for item in unavailable_items:
            db.session.delete(item)
        
        if unavailable_items:
            db.session.commit()
            flash(f'{len(unavailable_items)} товар(ов) были удалены из корзины (закончились или недоступны)', 'warning')
        
        # Расчет доставки
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
        return render_template('cart.html',
                             cart_items=available_items,
                             total=total,
                             delivery_cost=delivery_cost,
                             final_amount=final_amount,
                             free_delivery_threshold=FREE_DELIVERY_THRESHOLD)
    except Exception as e:
        logger.error(f"Ошибка загрузки корзины: {e}")
        flash('Произошла ошибка при загрузке корзины', 'error')
        return redirect(url_for('index'))

# Оформление заказа
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            flash('Ваша корзина пуста', 'warning')
            return redirect(url_for('cart_page'))
        
        # Проверяем наличие всех товаров
        for item in cart_items:
            if not item.product or not item.product.is_active or item.product.stock < item.quantity:
                product_name = item.product.name if item.product else "Неизвестный товар"
                flash(f'Товар "{product_name}" недоступен в нужном количестве', 'error')
                return redirect(url_for('cart_page'))
        
        total = sum(item.product.price * item.quantity for item in cart_items)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
        if request.method == 'POST':
            # Получаем данные формы
            delivery_address = request.form.get('delivery_address')
            delivery_type = request.form.get('delivery_type', 'courier')
            payment_method = request.form.get('payment_method', 'card')
            promo_code = request.form.get('promo_code')
            customer_notes = request.form.get('customer_notes')
            
            # Проверяем промокод
            discount_amount = 0
            if promo_code:
                promo = PromoCode.query.filter_by(code=promo_code, is_active=True).first()
                if promo and promo.is_valid(total):
                    discount_amount = promo.get_discount(total)
                    promo.used_count += 1
                else:
                    flash('Промокод недействителен', 'warning')
            
            # Обновляем итоговую сумму с учетом скидки
            final_amount = total + delivery_cost - discount_amount
            
            # Создаем номер заказа
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            order_number = f"VE{timestamp}{current_user.id:04d}"
            
            # Подготавливаем данные товаров
            items_data = []
            for item in cart_items:
                item_data = {
                    'product_id': item.product_id,
                    'name': item.product.name,
                    'article': item.product.article,
                    'price': item.product.price,
                    'quantity': item.quantity,
                    'size': item.selected_size,
                    'color': item.selected_color,
                    'total': item.product.price * item.quantity
                }
                items_data.append(item_data)
                
                # Обновляем остатки на складе
                item.product.stock -= item.quantity
                item.product.reserved += item.quantity
            
            # Создаем заказ
            order = Order(
                order_number=order_number,
                user_id=current_user.id,
                total_amount=total,
                discount_amount=discount_amount,
                delivery_cost=delivery_cost,
                final_amount=final_amount,
                delivery_address=delivery_address,
                delivery_type=delivery_type,
                payment_method=payment_method,
                promo_code=promo_code if discount_amount > 0 else None,
                customer_notes=customer_notes,
                items_json=json.dumps(items_data, ensure_ascii=False, indent=2)
            )
            
            # Очищаем корзину
            Cart.query.filter_by(user_id=current_user.id).delete()
            
            # Обновляем статистику пользователя
            current_user.total_orders += 1
            current_user.total_spent += final_amount
            current_user.last_activity = datetime.utcnow()
            
            # Присваиваем VIP статус при достижении порога
            if current_user.total_spent >= 1000000 and not current_user.is_vip:
                current_user.is_vip = True
                flash('Поздравляем! Вы получили VIP статус!', 'success')
            
            db.session.add(order)
            db.session.commit()
            
            flash(f'Заказ #{order_number} успешно оформлен! Сумма: {format_price_filter(final_amount)} {CURRENCY}', 'success')
            return redirect(url_for('order_success', order_id=order.id))
        
        return render_template('checkout.html',
                             cart_items=cart_items,
                             total=total,
                             delivery_cost=delivery_cost,
                             final_amount=final_amount,
                             user=current_user)
    except Exception as e:
        logger.error(f"Ошибка оформления заказа: {e}")
        flash('Произошла ошибка при оформлении заказа', 'error')
        return redirect(url_for('cart_page'))

# Страница успешного оформления заказа
@app.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.user_id != current_user.id and not current_user.is_admin:
            flash('Доступ запрещен', 'error')
            return redirect(url_for('index'))
        
        return render_template('order_success.html', order=order)
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы успешного заказа: {e}")
        flash('Произошла ошибка', 'error')
        return redirect(url_for('orders'))

# История заказов
@app.route('/orders')
@login_required
def orders():
    try:
        user_orders = Order.query.filter_by(user_id=current_user.id)\
            .order_by(Order.created_at.desc()).all()
        
        return render_template('orders.html', orders=user_orders)
    except Exception as e:
        logger.error(f"Ошибка загрузки истории заказов: {e}")
        flash('Произошла ошибка при загрузке истории заказов', 'error')
        return redirect(url_for('index'))

# Профиль пользователя
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    try:
        if request.method == 'POST':
            # Обновление профиля
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.phone = request.form.get('phone', current_user.phone)
            current_user.email = request.form.get('email', current_user.email)
            
            # Смена пароля
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password and confirm_password:
                if new_password == confirm_password:
                    current_user.set_password(new_password)
                    flash('Пароль успешно изменен', 'success')
                else:
                    flash('Пароли не совпадают', 'error')
            
            # Настройки уведомлений
            current_user.notification_enabled = 'notifications' in request.form
            
            db.session.commit()
            flash('Профиль успешно обновлен', 'success')
            return redirect(url_for('profile'))
        
        return render_template('profile.html', user=current_user)
    except Exception as e:
        logger.error(f"Ошибка загрузки профиля: {e}")
        flash('Произошла ошибка при загрузке профиля', 'error')
        return redirect(url_for('index'))

# Админ-панель
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Статистика
        total_users = User.query.count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_orders = Order.query.count()
        total_revenue = db.session.query(db.func.sum(Order.final_amount)).scalar() or 0
        
        # Последние заказы
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        
        # Последние пользователи
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Популярные категории
        category_stats = db.session.query(
            Product.category,
            db.func.count(Product.id).label('count'),
            db.func.sum(Product.price * Product.stock).label('total_value')
        ).filter_by(is_active=True).group_by(Product.category).all()
        
        # Статистика по дням
        daily_stats = []
        for i in range(7):
            day = datetime.now().date() - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            
            day_orders = Order.query.filter(
                Order.created_at >= day_start,
                Order.created_at <= day_end
            ).all()
            
            day_revenue = sum(order.final_amount for order in day_orders)
            daily_stats.append({
                'date': day,
                'orders': len(day_orders),
                'revenue': day_revenue
            })
        
        return render_template('admin.html',
                             total_users=total_users,
                             total_products=total_products,
                             total_orders=total_orders,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders,
                             recent_users=recent_users,
                             category_stats=category_stats,
                             daily_stats=daily_stats)
    except Exception as e:
        logger.error(f"Ошибка загрузки админ-панели: {e}")
        flash('Произошла ошибка при загрузке админ-панели', 'error')
        return redirect(url_for('index'))

# ==================== API МАРШРУТЫ ====================

# API для управления товарами
@app.route('/api/products', methods=['GET'])
@api_response
def api_products():
    """API для получения списка товаров"""
    try:
        category = request.args.get('category', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Product.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.offset(offset).limit(limit).all()
        
        products_data = []
        for product in products:
            product_data = {
                'id': product.id,
                'article': product.article,
                'name': product.name,
                'description': product.description or '',
                'detailed_description': product.detailed_description or '',
                'price': product.price,
                'old_price': product.old_price,
                'discount': product.discount,
                'category': product.category,
                'subcategory': product.subcategory,
                'brand': product.brand or '',
                'image_url': product.image_url or '/static/img/placeholder.jpg',
                'images': product.get_images_list(),
                'stock': product.stock,
                'is_new': product.is_new,
                'is_hit': product.is_hit,
                'is_exclusive': product.is_exclusive,
                'is_limited': product.is_limited,
                'color': product.color or '',
                'size': product.size or '',
                'material': product.material or '',
                'country': product.country or '',
                'season': product.season or '',
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }
            products_data.append(product_data)
        
        total_products = Product.query.filter_by(is_active=True).count()
        
        return {
            'success': True,
            'products': products_data,
            'count': len(products_data),
            'total': total_products,
            'offset': offset,
            'limit': limit
        }
    except Exception as e:
        logger.error(f"Ошибка API /api/products: {e}")
        return {
            'success': False,
            'message': 'Произошла ошибка при получении товаров',
            'products': []
        }, 500

# API для получения товара по ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
@api_response
def api_get_product_by_id(product_id):
    """API для получения товара по ID"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return {
                'success': False,
                'message': 'Товар не найден'
            }, 404
        
        # Формируем ответ
        images = product.get_images_list()
        if product.image_url and product.image_url not in images:
            images.insert(0, product.image_url)
        
        product_data = {
            'id': product.id,
            'article': product.article,
            'name': product.name,
            'description': product.description or '',
            'detailed_description': product.detailed_description or '',
            'price': product.price,
            'old_price': product.old_price,
            'discount': product.discount,
            'category': product.category,
            'subcategory': product.subcategory or '',
            'brand': product.brand or '',
            'image_url': product.image_url or '/static/img/placeholder.jpg',
            'images': images,
            'stock': product.stock,
            'is_new': product.is_new,
            'is_hit': product.is_hit,
            'is_exclusive': product.is_exclusive,
            'is_limited': product.is_limited,
            'color': product.color or '',
            'size': product.size or '',
            'material': product.material or '',
            'country': product.country or '',
            'season': product.season or '',
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }
        
        return {
            'success': True,
            'product': product_data
        }
            
    except Exception as e:
        logger.error(f"Ошибка получения товара {product_id}: {e}")
        return {
            'success': False,
            'message': 'Ошибка получения товара'
        }, 500

# API для добавления в корзину
@app.route('/api/cart/add', methods=['POST'])
@login_required
@api_response
def api_add_to_cart():
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        size = data.get('size')
        color = data.get('color')
        
        if not product_id:
            return {'success': False, 'message': 'Не указан ID товара'}, 400
        
        product = Product.query.get(product_id)
        if not product:
            return {'success': False, 'message': 'Товар не найден'}, 404
        
        if not product.is_active:
            return {'success': False, 'message': 'Товар временно недоступен'}, 400
        
        # Проверяем наличие
        if product.stock < quantity:
            return {'success': False, 'message': 'Недостаточно товара на складе'}, 400
        
        # Проверяем, есть ли уже в корзине
        existing_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            selected_size=size,
            selected_color=color
        ).first()
        
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if product.stock < new_quantity:
                return {'success': False, 'message': 'Недостаточно товара на складе для добавления указанного количества'}, 400
            existing_item.quantity = new_quantity
            existing_item.added_at = datetime.utcnow()
        else:
            cart_item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                quantity=quantity,
                selected_size=size,
                selected_color=color,
                price_at_addition=product.price
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        # Получаем обновленное количество товаров в корзине
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(item.product.price * item.quantity for item in cart_items if item.product)
        
        return {
            'success': True,
            'message': 'Товар добавлен в корзину',
            'cart_count': cart_count,
            'cart_total': cart_total,
            'product_name': product.name,
            'product_price': product.price
        }
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Произошла ошибка при добавлении в корзину'}, 500

# API для обновления корзины
@app.route('/api/cart/update', methods=['POST'])
@login_required
@api_response
def api_update_cart():
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')
        
        if not cart_item_id or quantity is None:
            return {'success': False, 'message': 'Не указаны необходимые данные'}, 400
        
        cart_item = Cart.query.get(cart_item_id)
        if not cart_item or cart_item.user_id != current_user.id:
            return {'success': False, 'message': 'Элемент корзины не найден'}, 404
        
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            if cart_item.product.stock < quantity:
                return {'success': False, 'message': 'Недостаточно товара на складе'}, 400
            cart_item.quantity = quantity
        
        db.session.commit()
        
        # Пересчитываем итоги
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items if item.product)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
        return {
            'success': True,
            'message': 'Корзина обновлена',
            'total': total,
            'delivery_cost': delivery_cost,
            'final_amount': final_amount,
            'cart_count': len(cart_items)
        }
    except Exception as e:
        logger.error(f"Ошибка обновления корзины: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Произошла ошибка при обновлении корзины'}, 500

# API для удаления из корзины
@app.route('/api/cart/remove/<int:cart_item_id>', methods=['DELETE'])
@login_required
@api_response
def api_remove_from_cart(cart_item_id):
    try:
        cart_item = Cart.query.get(cart_item_id)
        if not cart_item or cart_item.user_id != current_user.id:
            return {'success': False, 'message': 'Элемент корзины не найден'}, 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        # Пересчитываем итоги
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items if item.product)
        cart_count = len(cart_items)
        
        return {
            'success': True,
            'message': 'Товар удален из корзины',
            'total': total,
            'cart_count': cart_count
        }
    except Exception as e:
        logger.error(f"Ошибка удаления из корзины: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Произошла ошибка при удалении из корзины'}, 500

# API для синхронизации корзины
@app.route('/api/cart/sync', methods=['GET', 'POST'])
@login_required
@api_response
def api_cart_sync_handler():
    """API для синхронизации корзины с сервером"""
    try:
        if request.method == 'GET':
            # Получение текущей корзины
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            cart_data = []
            
            for item in cart_items:
                if item.product:
                    cart_data.append({
                        'id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product.name,
                        'product_article': item.product.article,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'selected_size': item.selected_size,
                        'selected_color': item.selected_color,
                        'image_url': item.product.image_url or '/static/img/placeholder.jpg',
                        'stock': item.product.stock,
                        'is_available': item.product.is_active and item.product.stock >= item.quantity
                    })
            
            return {
                'success': True,
                'cart_items': cart_data,
                'count': len(cart_data),
                'user_id': current_user.id
            }
            
        elif request.method == 'POST':
            # Синхронизация корзины
            data = request.json or {}
            items = data.get('items', [])
            
            if not items:
                return {'success': False, 'message': 'Нет данных для синхронизации'}, 400
            
            # Очищаем текущую корзину пользователя
            Cart.query.filter_by(user_id=current_user.id).delete()
            
            # Добавляем товары из запроса
            for item_data in items:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity', 1)
                
                product = Product.query.get(product_id)
                if product and product.is_active:
                    cart_item = Cart(
                        user_id=current_user.id,
                        product_id=product_id,
                        quantity=quantity,
                        selected_size=item_data.get('size'),
                        selected_color=item_data.get('color'),
                        price_at_addition=product.price
                    )
                    db.session.add(cart_item)
            
            db.session.commit()
            
            # Получаем обновленную корзину
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            cart_data = []
            
            for item in cart_items:
                if item.product:
                    cart_data.append({
                        'id': item.id,
                        'product_id': item.product_id,
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'image_url': item.product.image_url or '/static/img/placeholder.jpg',
                        'selected_size': item.selected_size,
                        'selected_color': item.selected_color
                    })
            
            return {
                'success': True,
                'message': 'Корзина синхронизирована',
                'cart': cart_data,
                'count': len(cart_data)
            }
            
    except Exception as e:
        logger.error(f"Ошибка синхронизации корзины: {e}")
        db.session.rollback()
        return {
            'success': False,
            'message': 'Ошибка синхронизации корзины'
        }, 500

# API для получения корзины
@app.route('/api/cart', methods=['GET'])
@api_response
def api_get_cart():
    """API для получения корзины"""
    try:
        cart_items = []
        cart_count = 0
        cart_total = 0
        
        # Если пользователь авторизован - получаем из базы
        if current_user.is_authenticated:
            cart_items_query = Cart.query.filter_by(user_id=current_user.id).all()
            cart_count = len(cart_items_query)
            cart_total = sum(item.product.price * item.quantity for item in cart_items_query if item.product)
            
            # Формируем данные корзины
            for item in cart_items_query:
                if item.product:
                    cart_items.append({
                        'id': item.id,
                        'product_id': item.product_id,
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'image_url': item.product.image_url or '/static/img/placeholder.jpg',
                        'size': item.selected_size,
                        'color': item.selected_color,
                        'stock': item.product.stock,
                        'is_available': item.product.is_active and item.product.stock >= item.quantity
                    })
        
        return {
            'success': True,
            'cart': cart_items,
            'count': cart_count,
            'total': cart_total,
            'is_authenticated': current_user.is_authenticated
        }
    except Exception as e:
        logger.error(f"Ошибка API cart: {e}")
        return {
            'success': False, 
            'message': 'Ошибка получения корзины', 
            'cart': [], 
            'count': 0, 
            'total': 0
        }, 500

# API для работы с избранным
@app.route('/api/wishlist', methods=['GET', 'POST'])
@login_required
@api_response
def api_wishlist_handler():
    """API для работы с избранным"""
    try:
        if request.method == 'GET':
            # Получаем избранное пользователя
            wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
            wishlist_data = []
            
            for item in wishlist_items:
                if item.product:
                    wishlist_data.append({
                        'id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product.name,
                        'product_price': item.product.price,
                        'product_image': item.product.image_url or '/static/img/placeholder.jpg',
                        'product_category': item.product.category,
                        'added_at': item.added_at.isoformat() if item.added_at else None
                    })
            
            return {
                'success': True,
                'wishlist': wishlist_data,
                'count': len(wishlist_data)
            }
            
        elif request.method == 'POST':
            # Добавление/удаление из избранного
            data = request.get_json(silent=True) or {}
            action = data.get('action', 'sync')
            
            if action == 'add':
                product_id = data.get('product_id')
                if not product_id:
                    return {'success': False, 'message': 'Не указан product_id'}, 400
                
                # Проверяем, есть ли уже в избранном
                existing = Wishlist.query.filter_by(
                    user_id=current_user.id,
                    product_id=product_id
                ).first()
                
                if not existing:
                    wishlist_item = Wishlist(
                        user_id=current_user.id,
                        product_id=product_id
                    )
                    db.session.add(wishlist_item)
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Товар добавлен в избранное'
                }
                
            elif action == 'remove':
                product_id = data.get('product_id')
                if product_id:
                    Wishlist.query.filter_by(
                        user_id=current_user.id,
                        product_id=product_id
                    ).delete()
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Товар удален из избранного'
                }
                
            else:  # sync
                wishlist = data.get('wishlist', [])
                logger.info(f"Wishlist sync for user {current_user.id}: {len(wishlist)} items")
                
                # Синхронизируем с базой данных
                current_wishlist = Wishlist.query.filter_by(user_id=current_user.id).all()
                current_product_ids = [item.product_id for item in current_wishlist]
                
                # Добавляем новые
                for product_id in wishlist:
                    if product_id not in current_product_ids:
                        wishlist_item = Wishlist(
                            user_id=current_user.id,
                            product_id=product_id
                        )
                        db.session.add(wishlist_item)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Избранное синхронизировано',
                    'count': len(wishlist)
                }
            
    except Exception as e:
        logger.error(f"Ошибка API wishlist: {e}")
        db.session.rollback()
        return {
            'success': False,
            'message': 'Ошибка работы с избранным'
        }, 500

# API для работы со списком сравнения
@app.route('/api/compare', methods=['GET', 'POST'])
@login_required
@api_response
def api_compare_handler():
    """API для работы со списком сравнения"""
    try:
        if request.method == 'GET':
            # Получаем список сравнения
            compare_items = CompareList.query.filter_by(user_id=current_user.id).all()
            compare_data = []
            
            for item in compare_items:
                if item.product:
                    compare_data.append({
                        'id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product.name,
                        'product_price': item.product.price,
                        'product_image': item.product.image_url or '/static/img/placeholder.jpg',
                        'product_category': item.product.category,
                        'added_at': item.added_at.isoformat() if item.added_at else None
                    })
            
            return {
                'success': True,
                'compare': compare_data,
                'count': len(compare_data)
            }
            
        elif request.method == 'POST':
            # Добавление/удаление из списка сравнения
            data = request.get_json(silent=True) or {}
            action = data.get('action', 'sync')
            
            if action == 'add':
                product_id = data.get('product_id')
                if not product_id:
                    return {'success': False, 'message': 'Не указан product_id'}, 400
                
                # Проверяем, есть ли уже в сравнении
                existing = CompareList.query.filter_by(
                    user_id=current_user.id,
                    product_id=product_id
                ).first()
                
                if not existing:
                    compare_item = CompareList(
                        user_id=current_user.id,
                        product_id=product_id
                    )
                    db.session.add(compare_item)
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Товар добавлен в сравнение'
                }
                
            elif action == 'remove':
                product_id = data.get('product_id')
                if product_id:
                    CompareList.query.filter_by(
                        user_id=current_user.id,
                        product_id=product_id
                    ).delete()
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Товар удален из сравнения'
                }
                
            else:  # sync
                compare_list = data.get('compare', [])
                logger.info(f"Compare list sync for user {current_user.id}: {len(compare_list)} items")
                
                # Синхронизируем с базой данных
                current_compare = CompareList.query.filter_by(user_id=current_user.id).all()
                current_product_ids = [item.product_id for item in current_compare]
                
                # Добавляем новые
                for product_id in compare_list:
                    if product_id not in current_product_ids:
                        compare_item = CompareList(
                            user_id=current_user.id,
                            product_id=product_id
                        )
                        db.session.add(compare_item)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Список сравнения синхронизирован',
                    'count': len(compare_list)
                }
            
    except Exception as e:
        logger.error(f"Ошибка API compare: {e}")
        db.session.rollback()
        return {
            'success': False,
            'message': 'Ошибка работы со списком сравнения'
        }, 500

# API для получения непрочитанных уведомлений
@app.route('/api/notifications/unread', methods=['GET'])
@login_required
@api_response
def api_get_unread_notifications():
    """API для получения непрочитанных уведомлений"""
    try:
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'created_at': notification.created_at.isoformat() if notification.created_at else None
            })
        
        return {
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data)
        }
    except Exception as e:
        logger.error(f"Ошибка API notifications: {e}")
        return {
            'success': False,
            'message': 'Ошибка получения уведомлений',
            'notifications': []
        }, 500

# API для проверки авторизации
@app.route('/api/auth/check', methods=['GET'])
@api_response
def api_auth_check():
    """API для проверки авторизации"""
    try:
        if current_user.is_authenticated:
            user_data = {
                'id': current_user.id,
                'telegram_id': current_user.telegram_id,
                'username': current_user.username,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'email': current_user.email,
                'phone': current_user.phone,
                'is_admin': current_user.is_admin,
                'is_vip': current_user.is_vip,
                'total_orders': current_user.total_orders,
                'total_spent': current_user.total_spent,
                'referral_code': current_user.referral_code,
                'notification_enabled': current_user.notification_enabled,
                'avatar_url': f'/static/img/users/{current_user.id}.jpg' if os.path.exists(f'static/img/users/{current_user.id}.jpg') else '/static/img/users/default.jpg'
            }
            return {
                'success': True,
                'user': user_data,
                'is_authenticated': True
            }
        else:
            return {
                'success': True,
                'user': None,
                'is_authenticated': False
            }
    except Exception as e:
        logger.error(f"Ошибка API auth/check: {e}")
        return {
            'success': False,
            'message': 'Ошибка проверки авторизации',
            'user': None,
            'is_authenticated': False
        }, 500

# API для входа
@app.route('/api/auth/login', methods=['POST'])
@api_response
def api_login():
    """API для входа"""
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {
                'success': False,
                'message': 'Email и пароль обязательны'
            }, 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_activity = datetime.utcnow()
            db.session.commit()
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_vip': user.is_vip,
                'is_admin': user.is_admin
            }
            
            return {
                'success': True,
                'message': 'Вход выполнен успешно',
                'user': user_data,
                'redirect': url_for('index')
            }
        else:
            return {
                'success': False,
                'message': 'Неверный email или пароль'
            }, 401
            
    except Exception as e:
        logger.error(f"Ошибка API login: {e}")
        return {
            'success': False,
            'message': 'Ошибка входа'
        }, 500

# API для выхода
@app.route('/api/auth/logout', methods=['POST'])
@login_required
@api_response
def api_logout():
    """API для выхода"""
    try:
        logout_user()
        return {
            'success': True,
            'message': 'Выход выполнен успешно',
            'redirect': url_for('index')
        }
    except Exception as e:
        logger.error(f"Ошибка API logout: {e}")
        return {
            'success': False,
            'message': 'Ошибка выхода'
        }, 500

# API для гостевого доступа
@app.route('/api/auth/guest', methods=['GET'])
@api_response
def api_auth_guest():
    """API для гостевого доступа"""
    return {
        'success': True,
        'user': None,
        'is_authenticated': False
    }

# API для трекинга аналитики
@app.route('/api/analytics/track', methods=['POST'])
@api_response
def api_analytics_track():
    """API для трекинга аналитики"""
    try:
        data = request.get_json(silent=True) or {}
        
        # Здесь можно сохранять данные аналитики в базу
        event_type = data.get('event', 'unknown')
        logger.info(f"Analytics tracked: {event_type}")
        
        return {'success': True}
    except Exception as e:
        logger.error(f"Ошибка API analytics: {e}")
        return {'success': False}, 500

# API для получения категорий
@app.route('/api/categories', methods=['GET'])
@api_response
def api_get_categories():
    """API для получения категорий товаров"""
    try:
        categories = db.session.query(
            Product.category,
            db.func.count(Product.id).label('count')
        ).filter_by(is_active=True).group_by(Product.category).all()
        
        categories_data = []
        for category, count in categories:
            if category:  # Пропускаем пустые категории
                categories_data.append({
                    'name': category,
                    'count': count,
                    'url': url_for('catalog_page', category=category)
                })
        
        return {
            'success': True,
            'categories': categories_data,
            'total': len(categories_data)
        }
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {e}")
        return {
            'success': False,
            'message': 'Ошибка получения категорий',
            'categories': []
        }, 500

# API для получения брендов
@app.route('/api/brands', methods=['GET'])
@api_response
def api_get_brands():
    """API для получения брендов"""
    try:
        brands = db.session.query(
            Product.brand,
            db.func.count(Product.id).label('count')
        ).filter(
            Product.is_active == True,
            Product.brand.isnot(None),
            Product.brand != ''
        ).group_by(Product.brand).all()
        
        brands_data = []
        for brand, count in brands:
            if brand:
                brands_data.append({
                    'name': brand,
                    'count': count
                })
        
        return {
            'success': True,
            'brands': brands_data,
            'total': len(brands_data)
        }
    except Exception as e:
        logger.error(f"Ошибка получения брендов: {e}")
        return {
            'success': False,
            'message': 'Ошибка получения брендов',
            'brands': []
        }, 500

# API для получения фильтров
@app.route('/api/filters', methods=['GET'])
@api_response
def api_get_filters():
    """API для получения доступных фильтров"""
    try:
        # Цены
        min_price_result = db.session.query(db.func.min(Product.price)).filter_by(is_active=True).scalar()
        max_price_result = db.session.query(db.func.max(Product.price)).filter_by(is_active=True).scalar()
        
        min_price = int(min_price_result) if min_price_result else 0
        max_price = int(max_price_result) if max_price_result else 100000
        
        # Цвета
        color_rows = db.session.query(Product.color).filter(
            Product.is_active == True,
            Product.color.isnot(None),
            Product.color != ''
        ).distinct().all()
        
        colors = []
        for row in color_rows:
            if row[0]:
                color_list = [c.strip() for c in row[0].split(',') if c.strip()]
                colors.extend(color_list)
        
        colors = list(set(colors))[:20]  # Уникальные цвета, максимум 20
        
        # Размеры
        size_rows = db.session.query(Product.size).filter(
            Product.is_active == True,
            Product.size.isnot(None),
            Product.size != ''
        ).distinct().all()
        
        sizes = []
        for row in size_rows:
            if row[0]:
                size_list = [s.strip() for s in row[0].split(',') if s.strip()]
                sizes.extend(size_list)
        
        sizes = list(set(sizes))
        
        return {
            'success': True,
            'filters': {
                'price': {
                    'min': min_price,
                    'max': max_price
                },
                'colors': colors,
                'sizes': sizes
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения фильтров: {e}")
        return {
            'success': False,
            'message': 'Ошибка получения фильтров'
        }, 500

# API для поиска товаров
@app.route('/api/search', methods=['GET'])
@api_response
def api_search():
    """API для поиска товаров"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return {
                'success': True,
                'results': [],
                'count': 0
            }
        
        # Поиск товаров
        search_query = f"%{query}%"
        products = Product.query.filter(
            Product.is_active == True,
            (Product.name.ilike(search_query)) |
            (Product.description.ilike(search_query)) |
            (Product.category.ilike(search_query)) |
            (Product.brand.ilike(search_query))
        ).limit(limit).all()
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'price': product.price,
                'discount': product.discount,
                'image_url': product.image_url or '/static/img/placeholder.jpg',
                'url': url_for('product_detail', product_id=product.id)
            })
        
        return {
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        }
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return {
            'success': False,
            'message': 'Ошибка поиска',
            'results': []
        }, 500

# API для проверки промокода
@app.route('/api/promo/check', methods=['POST'])
@api_response
def api_check_promo_code():
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        code = data.get('code')
        order_amount = data.get('order_amount', 0)
        
        if not code:
            return {'success': False, 'message': 'Не указан промокод'}, 400
        
        promo = PromoCode.query.filter_by(code=code, is_active=True).first()
        
        if not promo:
            return {'success': False, 'message': 'Промокод не найден'}, 404
        
        if not promo.is_valid(order_amount):
            return {
                'success': False,
                'message': 'Промокод недействителен или условия не выполнены'
            }, 400
        
        discount_amount = promo.get_discount(order_amount)
        new_amount = order_amount - discount_amount
        
        return {
            'success': True,
            'promo_code': promo.code,
            'description': promo.description,
            'discount_percent': promo.discount_percent,
            'discount_amount': promo.discount_amount,
            'calculated_discount': discount_amount,
            'min_order_amount': promo.min_order_amount,
            'new_total': new_amount
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки промокода: {e}")
        return {'success': False, 'message': 'Ошибка проверки промокода'}, 500

# API для получения пользователя по telegram_id
@app.route('/api/user/telegram/<int:telegram_id>', methods=['GET'])
@api_response
def api_get_user_by_telegram(telegram_id):
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if user:
            user_data = {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'is_vip': user.is_vip,
                'total_orders': user.total_orders,
                'total_spent': user.total_spent,
                'referral_code': user.referral_code,
                'notification_enabled': user.notification_enabled,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_activity': user.last_activity.isoformat() if user.last_activity else None
            }
            return {'success': True, 'user': user_data}
        else:
            return {'success': False, 'message': 'Пользователь не найден'}, 404
            
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по telegram_id: {e}")
        return {'success': False, 'message': 'Ошибка сервера'}, 500

# API для создания пользователя из Telegram
@app.route('/api/user/telegram/create', methods=['POST'])
@api_response
def api_create_user_from_telegram():
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        telegram_id = data.get('telegram_id')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not telegram_id or not first_name:
            return {'success': False, 'message': 'Необходимы telegram_id и first_name'}, 400
        
        # Проверяем, существует ли пользователь
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if user:
            # Обновляем данные
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_activity = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'user_id': user.id,
                'message': 'Пользователь обновлен',
                'is_new': False
            }
        else:
            # Создаем нового пользователя
            referral_code = f"VIP{telegram_id:06d}"
            
            # Проверяем уникальность referral_code
            while User.query.filter_by(referral_code=referral_code).first():
                referral_code = f"VIP{random.randint(100000, 999999)}"
            
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referral_code=referral_code,
                notification_enabled=True,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'user_id': user.id,
                'message': 'Пользователь создан',
                'is_new': True,
                'referral_code': referral_code
            }
            
    except Exception as e:
        logger.error(f"Ошибка создания пользователя из Telegram: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Ошибка сервера'}, 500

# API для создания заказа
@app.route('/api/order/create', methods=['POST'])
@login_required
@api_response
def api_create_order():
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        # Получаем товары из корзины
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            return {'success': False, 'message': 'Корзина пуста'}, 400
        
        # Проверяем наличие всех товаров
        unavailable_items = []
        for item in cart_items:
            if not item.product or not item.product.is_active or item.product.stock < item.quantity:
                unavailable_items.append(item)
        
        if unavailable_items:
            return {
                'success': False,
                'message': 'Некоторые товары в корзине недоступны',
                'unavailable_items': [item.product.name for item in unavailable_items if item.product]
            }, 400
        
        # Рассчитываем сумму
        total = sum(item.product.price * item.quantity for item in cart_items)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        
        # Проверяем промокод
        promo_code = data.get('promo_code')
        discount_amount = 0
        
        if promo_code:
            promo = PromoCode.query.filter_by(code=promo_code, is_active=True).first()
            if promo and promo.is_valid(total):
                discount_amount = promo.get_discount(total)
                promo.used_count += 1
            else:
                return {'success': False, 'message': 'Промокод недействителен'}, 400
        
        final_amount = total + delivery_cost - discount_amount
        
        # Создаем номер заказа
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        order_number = f"VE{timestamp}{current_user.id:04d}"
        
        # Подготавливаем данные товаров
        items_data = []
        for item in cart_items:
            item_data = {
                'product_id': item.product_id,
                'name': item.product.name,
                'article': item.product.article,
                'price': item.product.price,
                'quantity': item.quantity,
                'size': item.selected_size,
                'color': item.selected_color,
                'total': item.product.price * item.quantity
            }
            items_data.append(item_data)
            
            # Обновляем остатки на складе
            item.product.stock -= item.quantity
            item.product.reserved += item.quantity
        
        # Создаем заказ
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total,
            discount_amount=discount_amount,
            delivery_cost=delivery_cost,
            final_amount=final_amount,
            delivery_address=data.get('delivery_address', ''),
            delivery_type=data.get('delivery_type', 'courier'),
            payment_method=data.get('payment_method', 'card'),
            promo_code=promo_code if discount_amount > 0 else None,
            customer_notes=data.get('customer_notes', ''),
            items_json=json.dumps(items_data, ensure_ascii=False, indent=2)
        )
        
        # Очищаем корзину
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        # Обновляем статистику пользователя
        current_user.total_orders += 1
        current_user.total_spent += final_amount
        current_user.last_activity = datetime.utcnow()
        
        # Присваиваем VIP статус при достижении порога
        if current_user.total_spent >= 1000000 and not current_user.is_vip:
            current_user.is_vip = True
        
        db.session.add(order)
        db.session.commit()
        
        return {
            'success': True,
            'order_number': order_number,
            'message': 'Заказ успешно создан!',
            'order_id': order.id,
            'final_amount': final_amount,
            'delivery_cost': delivery_cost,
            'discount_amount': discount_amount
        }
    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Произошла ошибка при создании заказа'}, 500

# API для получения статистики магазина
@app.route('/api/stats')
@login_required
@api_response
def api_stats():
    if not current_user.is_admin:
        return {'success': False, 'message': 'Доступ запрещен'}, 403
    
    try:
        # Общая статистика
        total_users = User.query.count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_orders = Order.query.count()
        total_revenue = db.session.query(db.func.sum(Order.final_amount)).scalar() or 0
        
        # Статистика за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_orders = Order.query.filter(Order.created_at >= thirty_days_ago).count()
        recent_revenue = db.session.query(db.func.sum(Order.final_amount)).filter(
            Order.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Статистика по категориям
        category_stats = []
        categories = db.session.query(Product.category).distinct().all()
        for category in categories:
            if category[0]:
                count = Product.query.filter_by(category=category[0], is_active=True).count()
                category_stats.append({
                    'category': category[0],
                    'count': count
                })
        
        # Топ товаров
        top_products = Product.query.filter_by(is_active=True).order_by(
            Product.is_hit.desc(), Product.created_at.desc()
        ).limit(10).all()
        
        top_products_data = []
        for product in top_products:
            top_products_data.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock': product.stock,
                'is_hit': product.is_hit,
                'is_new': product.is_new
            })
        
        return {
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_products': total_products,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'recent_users': recent_users,
                'recent_orders': recent_orders,
                'recent_revenue': recent_revenue,
                'category_stats': category_stats,
                'top_products': top_products_data
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {'success': False, 'message': 'Ошибка получения статистики'}, 500

# API для рассылки уведомлений
@app.route('/api/notify', methods=['POST'])
@login_required
@api_response
def api_send_notification():
    if not current_user.is_admin:
        return {'success': False, 'message': 'Доступ запрещен'}, 403
    
    try:
        data = request.json
        if not data:
            return {'success': False, 'message': 'Отсутствуют данные'}, 400
        
        message = data.get('message')
        target = data.get('target', 'all')  # all, vip, new
        
        if not message:
            return {'success': False, 'message': 'Не указано сообщение'}, 400
        
        # Получаем пользователей для рассылки
        if target == 'vip':
            users = User.query.filter_by(is_vip=True, notification_enabled=True).all()
        elif target == 'new':
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            users = User.query.filter(
                User.created_at >= thirty_days_ago,
                User.notification_enabled == True
            ).all()
        else:  # all
            users = User.query.filter_by(notification_enabled=True).all()
        
        # Создаем уведомления для каждого пользователя
        for user in users:
            notification = Notification(
                user_id=user.id,
                title='Сообщение от администратора',
                message=message,
                type='info'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Уведомление отправлено {len(users)} пользователям',
            'recipients_count': len(users)
        }
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
        db.session.rollback()
        return {'success': False, 'message': 'Ошибка отправки уведомления'}, 500

# ==================== СТАНДАРТНЫЕ МАРШРУТЫ ====================

# Вход в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not email or not password:
            flash('Пожалуйста, заполните все поля', 'warning')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_activity = datetime.utcnow()
            db.session.commit()
            
            flash(f'Добро пожаловать, {user.first_name}!', 'success')
            
            # Перенаправляем на страницу, с которой пришел пользователь
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html')

# Вход через Telegram
@app.route('/login/telegram')
def login_telegram():
    # Это заглушка для Telegram авторизации
    # В реальном приложении здесь будет OAuth авторизация через Telegram
    
    # Для демонстрации создаем тестового пользователя
    flash('Telegram авторизация временно недоступна. Используйте стандартный вход.', 'info')
    return redirect(url_for('login'))

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Валидация
        errors = []
        
        if not first_name:
            errors.append('Имя обязательно')
        
        if not email:
            errors.append('Email обязателен')
        elif User.query.filter_by(email=email).first():
            errors.append('Пользователь с таким email уже существует')
        
        if not password:
            errors.append('Пароль обязателен')
        elif len(password) < 6:
            errors.append('Пароль должен быть не менее 6 символов')
        elif password != confirm_password:
            errors.append('Пароли не совпадают')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Создаем пользователя
        referral_code = f"USER{random.randint(100000, 999999)}"
        while User.query.filter_by(referral_code=referral_code).first():
            referral_code = f"USER{random.randint(100000, 999999)}"
        
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            referral_code=referral_code,
            notification_enabled=True,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'Регистрация успешна! Добро пожаловать, {user.first_name}!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

# Избранное
@app.route('/wishlist')
@login_required
def wishlist_page():
    try:
        wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        products = [item.product for item in wishlist_items if item.product and item.product.is_active]
        
        return render_template('wishlist.html', products=products)
    except Exception as e:
        logger.error(f"Ошибка загрузки избранного: {e}")
        flash('Произошла ошибка при загрузке избранного', 'error')
        return redirect(url_for('index'))

# Сравнение
@app.route('/compare')
@login_required
def compare_page():
    try:
        compare_items = CompareList.query.filter_by(user_id=current_user.id).all()
        products = [item.product for item in compare_items if item.product and item.product.is_active]
        
        # Ограничиваем количество товаров для сравнения
        if len(products) > 4:
            products = products[:4]
            flash('Для сравнения отображается максимум 4 товара', 'info')
        
        return render_template('compare.html', products=products)
    except Exception as e:
        logger.error(f"Ошибка загрузки сравнения: {e}")
        flash('Произошла ошибка при загрузке сравнения', 'error')
        return redirect(url_for('index'))

# Уведомления
@app.route('/notifications')
@login_required
def notifications_page():
    try:
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc()).all()
        
        # Помечаем все как прочитанные
        for notification in notifications:
            if not notification.is_read:
                notification.is_read = True
        
        db.session.commit()
        
        return render_template('notifications.html', notifications=notifications)
    except Exception as e:
        logger.error(f"Ошибка загрузки уведомлений: {e}")
        flash('Произошла ошибка при загрузке уведомлений', 'error')
        return redirect(url_for('index'))

# Страница 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Страница 403
@app.errorhandler(403)
def forbidden(e):
    flash('Доступ запрещен', 'danger')
    return redirect(url_for('index'))

# Страница 500
@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Internal Server Error: {e}")
    return render_template('500.html'), 500

# Health check
@app.route('/health')
@api_response
def health_check():
    try:
        # Проверяем соединение с базой данных
        db.session.execute('SELECT 1')
        
        # Проверяем доступность ключевых таблиц
        tables_ok = True
        for table in ['users', 'products', 'orders', 'cart']:
            try:
                db.session.execute(f'SELECT 1 FROM {table} LIMIT 1')
            except:
                tables_ok = False
        
        return {
            'status': 'healthy' if tables_ok else 'degraded',
            'database': 'connected',
            'tables': tables_ok,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, 500

# API для тестирования
@app.route('/api/test')
@api_response
def api_test():
    return {
        'success': True,
        'message': 'API работает корректно',
        'timestamp': datetime.utcnow().isoformat(),
        'shop_name': SHOP_NAME
    }

# Статические файлы
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Главная функция запуска
if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()
    
    # Получаем параметры запуска
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Выводим информацию о запуске
    print(f"""
    {'='*70}
    {Emoji.LOGO} VOGUE ÉLITE Luxury Fashion Store {Emoji.LOGO}
    {'='*70}
    {Emoji.WEBSITE} Адрес: http://{host}:{port}
    {Emoji.BUG} Режим отладки: {debug}
    {Emoji.DATABASE} База данных: {app.config['SQLALCHEMY_DATABASE_URI']}
    {Emoji.SHOP} Магазин: {SHOP_NAME}
    {Emoji.PHONE} Телефон: {SHOP_PHONE}
    {Emoji.MESSAGE} Поддержка: {SUPPORT_USERNAME}
    {Emoji.MONEY} Валюта: {CURRENCY}
    {Emoji.DELIVERY} Бесплатная доставка от: {FREE_DELIVERY_THRESHOLD:,} {CURRENCY}
    {'='*70}
    """)
    
    # Создаем дополнительные тестовые данные, если нужно
    with app.app_context():
        if debug and Product.query.count() < 20:
            try:
                # Добавляем больше товаров для тестирования
                extra_products = []
                categories_list = [
                    Categories.DRESSES, Categories.SUITS, Categories.BLOUSES,
                    Categories.PANTS, Categories.SKIRTS, Categories.JACKETS,
                    Categories.COATS, Categories.SHOES, Categories.BAGS,
                    Categories.JEWELRY, Categories.ACCESSORIES
                ]
                
                brands_list = [
                    Brands.GUCCI, Brands.CHANEL, Brands.Dior, Brands.LOUIS_VUITTON,
                    Brands.HERMES, Brands.PRADA, Brands.VERSACE, Brands.ARMANI,
                    Brands.BURBERRY, Brands.BALENCIAGA, Brands.VOGUE_ELITE
                ]
                
                for i in range(11, 51):
                    category = random.choice(categories_list)
                    brand = random.choice(brands_list)
                    
                    # Определяем цену в зависимости от категории и бренда
                    base_price = random.randint(50000, 500000)
                    if brand in [Brands.HERMES, Brands.CHANEL]:
                        base_price *= 3
                    elif brand in [Brands.GUCCI, Brands.Dior, Brands.LOUIS_VUITTON]:
                        base_price *= 2
                    
                    # Случайная скидка
                    discount = random.choice([0, 0, 0, 5, 10, 15, 20])
                    old_price = base_price * (1 + discount/100) if discount > 0 else None
                    
                    product = Product(
                        article=f'VE{2024000 + i}',
                        name=f'{brand} {category} Коллекция {i}',
                        description=f'Эксклюзивный {category.lower()} от {brand}. Премиальное качество и дизайн.',
                        price=base_price,
                        old_price=old_price,
                        discount=discount,
                        category=category,
                        brand=brand,
                        image_url=f'/static/img/products/product-{(i % 10) + 1}.jpg',
                        stock=random.randint(1, 20),
                        is_new=random.choice([True, False]),
                        is_hit=random.choice([True, False]),
                        is_active=True,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365))
                    )
                    extra_products.append(product)
                
                db.session.add_all(extra_products)
                db.session.commit()
                logger.info(f"Добавлено {len(extra_products)} тестовых товаров")
            except Exception as e:
                logger.error(f"Ошибка добавления тестовых товаров: {e}")
    
    # Запускаем приложение
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
        raise
