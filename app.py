from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime
import os
import json
import logging
import sqlite3

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VogueEliteWeb')

app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-12345-secure-vogue-elite')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fashion_store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Константы магазина
SHOP_NAME = "VOGUE ÉLITE"
SHOP_SLOGAN = "Искусство стиля"
SHOP_PHONE = "+7 (495) 123-45-67"
SHOP_EMAIL = "info@vogue-elite.ru"
SUPPORT_USERNAME = "@Lexaa_161"
FREE_DELIVERY_THRESHOLD = 20000
DELIVERY_COST = 500
WEB_APP_URL = "http://localhost:8080"  # URL для интеграции с ботом

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

# Настройка базы данных
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо войти в систему.'
login_manager.login_message_category = 'warning'

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

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
    images = db.Column(db.Text, nullable=True)  # JSON строки с изображениями
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

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='new')
    total_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    delivery_cost = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_type = db.Column(db.String(50), default='courier')
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), default='pending')
    promo_code = db.Column(db.String(50), nullable=True)
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    items_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создаем таблицы при первом запуске
with app.app_context():
    db.create_all()
    
    # Создаем тестового администратора если его нет
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        admin_user = User(
            username='admin',
            first_name='Администратор',
            email='admin@vogue-elite.ru',
            phone='+79999999999',
            is_admin=True,
            is_vip=True,
            referral_code='ADMIN001'
        )
        db.session.add(admin_user)
        db.session.commit()
        logger.info("Создан тестовый администратор")
    
    # Создаем тестовые товары если их нет
    if Product.query.count() == 0:
        test_products = []
        for i in range(1, 6):
            product = Product(
                article=f"VOGUE{str(i).zfill(3)}",
                name=f"Эксклюзивное платье {i}",
                description=f"Роскошное платье премиум-класса {i}",
                detailed_description=f"Эксклюзивное вечернее платье из коллекции {i}. Изготовлено из натурального шелка с ручной вышивкой.",
                price=25000 + i * 5000,
                old_price=30000 + i * 5000 if i % 2 == 0 else None,
                discount=15 if i % 2 == 0 else 0,
                category=Categories.DRESSES,
                subcategory="Вечерние платья",
                size="XS,S,M,L,XL",
                color="Черный, Белый, Красный",
                material="Шелк, Кружево",
                brand="VOGUE ÉLITE",
                season="Весна-Лето 2024",
                country="Италия",
                image_url="https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&h=1200&fit=crop&q=80",
                images=json.dumps([
                    "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&h=1200&fit=crop&q=80",
                    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800&h=1200&fit=crop&q=80"
                ]),
                is_new=True if i < 3 else False,
                is_hit=True if i % 2 == 0 else False,
                is_exclusive=True,
                is_limited=True if i == 1 else False,
                stock=10 - i,
                weight=0.8,
                dimensions="Длина: 120см, Обхват: 90см",
                care_instructions="Только химчистка. Не стирать. Хранить в сухом месте."
            )
            test_products.append(product)
        
        db.session.add_all(test_products)
        db.session.commit()
        logger.info(f"Создано {len(test_products)} тестовых товаров")

# Контекстный процессор для передачи данных во все шаблоны
@app.context_processor
def inject_globals():
    return {
        'shop_name': SHOP_NAME,
        'shop_slogan': SHOP_SLOGAN,
        'shop_phone': SHOP_PHONE,
        'shop_email': SHOP_EMAIL,
        'support_username': SUPPORT_USERNAME,
        'emoji': Emoji,
        'categories': Categories,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'delivery_cost': DELIVERY_COST,
        'web_app_url': WEB_APP_URL,
        'current_year': datetime.now().year
    }

# Главная страница
@app.route('/')
def index():
    try:
        new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(db.func.random()).limit(8).all()
        hit_products = Product.query.filter_by(is_hit=True, is_active=True).order_by(db.func.random()).limit(8).all()
        exclusive_products = Product.query.filter_by(is_exclusive=True, is_active=True).order_by(db.func.random()).limit(8).all()
        
        return render_template('index.html',
                             new_products=new_products,
                             hit_products=hit_products,
                             exclusive_products=exclusive_products)
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html',
                             new_products=[],
                             hit_products=[],
                             exclusive_products=[])

# Каталог
@app.route('/catalog')
def catalog_page():
    try:
        category = request.args.get('category', 'all')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        query = Product.query.filter_by(is_active=True)
        
        if category != 'all':
            query = query.filter_by(category=category)
        
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Получаем все категории для фильтра
        categories = db.session.query(Product.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        return render_template('catalog.html',
                             products=products,
                             categories=categories,
                             current_category=category)
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
        
        # Аналогичные товары
        similar_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id,
            Product.is_active == True
        ).order_by(db.func.random()).limit(4).all()
        
        # Парсинг изображений из JSON
        images = []
        if product.images:
            try:
                images = json.loads(product.images)
            except:
                images = []
        if product.image_url and product.image_url not in images:
            images.insert(0, product.image_url)
        
        return render_template('product.html',
                             product=product,
                             similar_products=similar_products,
                             images=images)
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
        total = 0
        available_items = []
        
        for item in cart_items:
            if item.product and item.product.is_active and item.product.stock >= item.quantity:
                total += item.product.price * item.quantity
                available_items.append(item)
            else:
                unavailable_items.append(item)
        
        # Удаляем недоступные товары
        for item in unavailable_items:
            db.session.delete(item)
        
        if unavailable_items:
            db.session.commit()
            flash(f'Некоторые товары были удалены из корзины (закончились или недоступны)', 'warning')
        
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
@app.route('/checkout')
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
                flash(f'Товар "{item.product.name if item.product else "Неизвестный"}" недоступен в нужном количестве', 'error')
                return redirect(url_for('cart_page'))
        
        total = sum(item.product.price * item.quantity for item in cart_items)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
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
@app.route('/profile')
@login_required
def profile():
    try:
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
            db.func.count(Product.id).label('count')
        ).filter_by(is_active=True).group_by(Product.category).all()
        
        return render_template('admin.html',
                             total_users=total_users,
                             total_products=total_products,
                             total_orders=total_orders,
                             total_revenue=total_revenue,
                             recent_orders=recent_orders,
                             recent_users=recent_users,
                             category_stats=category_stats)
    except Exception as e:
        logger.error(f"Ошибка загрузки админ-панели: {e}")
        flash('Произошла ошибка при загрузке админ-панели', 'error')
        return redirect(url_for('index'))

# API для управления товарами
@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        category = request.args.get('category', None)
        limit = request.args.get('limit', 50, type=int)
        
        query = Product.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.limit(limit).all()
        
        products_data = []
        for product in products:
            product_data = {
                'id': product.id,
                'article': product.article,
                'name': product.name,
                'description': product.description or '',
                'price': product.price,
                'old_price': product.old_price,
                'discount': product.discount,
                'category': product.category,
                'image_url': product.image_url or '',
                'stock': product.stock,
                'is_new': product.is_new,
                'is_hit': product.is_hit,
                'is_exclusive': product.is_exclusive,
                'brand': product.brand,
                'created_at': product.created_at.isoformat() if product.created_at else None
            }
            products_data.append(product_data)
        
        return jsonify({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        logger.error(f"Ошибка API /api/products: {e}")
        return jsonify({
            'success': False,
            'message': 'Произошла ошибка при получении товаров',
            'products': []
        }), 500

# API для добавления в корзину
@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Отсутствуют данные'}), 400
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        size = data.get('size')
        color = data.get('color')
        
        if not product_id:
            return jsonify({'success': False, 'message': 'Не указан ID товара'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Товар не найден'}), 404
        
        if not product.is_active:
            return jsonify({'success': False, 'message': 'Товар временно недоступен'}), 400
        
        # Проверяем наличие
        if product.stock < quantity:
            return jsonify({'success': False, 'message': 'Недостаточно товара на складе'}), 400
        
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
                return jsonify({'success': False, 'message': 'Недостаточно товара на складе для добавления указанного количества'}), 400
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
        
        return jsonify({
            'success': True,
            'message': 'Товар добавлен в корзину',
            'cart_count': cart_count
        })
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Произошла ошибка при добавлении в корзину'}), 500

# API для обновления корзины
@app.route('/api/cart/update', methods=['POST'])
@login_required
def api_update_cart():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Отсутствуют данные'}), 400
        
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')
        
        if not cart_item_id or quantity is None:
            return jsonify({'success': False, 'message': 'Не указаны необходимые данные'}), 400
        
        cart_item = Cart.query.get(cart_item_id)
        if not cart_item or cart_item.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Элемент корзины не найден'}), 404
        
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            if cart_item.product.stock < quantity:
                return jsonify({'success': False, 'message': 'Недостаточно товара на складе'}), 400
            cart_item.quantity = quantity
        
        db.session.commit()
        
        # Пересчитываем итоги
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items if item.product)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
        return jsonify({
            'success': True,
            'message': 'Корзина обновлена',
            'total': total,
            'delivery_cost': delivery_cost,
            'final_amount': final_amount,
            'cart_count': len(cart_items)
        })
    except Exception as e:
        logger.error(f"Ошибка обновления корзины: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Произошла ошибка при обновлении корзины'}), 500

# API для создания заказа
@app.route('/api/order/create', methods=['POST'])
@login_required
def api_create_order():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Отсутствуют данные'}), 400
        
        # Получаем товары из корзины
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Корзина пуста'}), 400
        
        # Проверяем наличие всех товаров
        unavailable_items = []
        for item in cart_items:
            if not item.product or not item.product.is_active or item.product.stock < item.quantity:
                unavailable_items.append(item)
        
        if unavailable_items:
            return jsonify({
                'success': False,
                'message': 'Некоторые товары в корзине недоступны',
                'unavailable_items': [item.product.name for item in unavailable_items if item.product]
            }), 400
        
        # Рассчитываем сумму
        total = sum(item.product.price * item.quantity for item in cart_items)
        delivery_cost = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_COST
        final_amount = total + delivery_cost
        
        # Создаем номер заказа
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        order_number = f"ORD{timestamp}{current_user.id:04d}"
        
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
            delivery_cost=delivery_cost,
            final_amount=final_amount,
            delivery_address=data.get('address', ''),
            delivery_type=data.get('delivery_type', 'courier'),
            payment_method=data.get('payment_method', 'card'),
            promo_code=data.get('promo_code'),
            customer_notes=data.get('notes', ''),
            items_json=json.dumps(items_data, ensure_ascii=False, indent=2)
        )
        
        # Очищаем корзину
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        # Обновляем статистику пользователя
        current_user.total_orders += 1
        current_user.total_spent += final_amount
        current_user.last_activity = datetime.utcnow()
        
        # Присваиваем VIP статус при достижении порога
        if current_user.total_spent >= 100000 and not current_user.is_vip:
            current_user.is_vip = True
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_number': order_number,
            'message': 'Заказ успешно создан!',
            'order_id': order.id
        })
    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Произошла ошибка при создании заказа'}), 500

# Простая аутентификация для теста
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Для демо-версии - простой вход
        if email == 'admin@vogue-elite.ru' and password == 'admin123':
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    username='admin',
                    first_name='Администратор',
                    email=email,
                    phone='+79999999999',
                    is_admin=True,
                    is_vip=True,
                    referral_code='ADMIN001'
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user, remember=True)
            flash('Вход выполнен успешно', 'success')
            return redirect(url_for('index'))
        else:
            # Создаем тестового пользователя
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    username=email.split('@')[0],
                    first_name='Тестовый',
                    last_name='Пользователь',
                    email=email,
                    phone='+70000000000',
                    is_admin=False,
                    is_vip=False,
                    referral_code=f'USER{datetime.now().strftime("%Y%m%d")}'
                )
                db.session.add(user)
                db.session.commit()
                flash('Создан тестовый пользователь', 'info')
            
            login_user(user, remember=True)
            flash('Вход выполнен успешно', 'success')
            return redirect(url_for('index'))
    
    return render_template('login.html')

# Авторизация через Telegram (заглушка)
@app.route('/login/telegram')
def login_telegram():
    flash('Telegram авторизация временно недоступна', 'warning')
    return redirect(url_for('index'))

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

# Обработчик ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    flash('Доступ запрещен', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Internal Server Error: {e}")
    return render_template('500.html'), 500

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# Запуск приложения
if __name__ == '__main__':
    # Создаем статические директории если их нет
    static_dirs = ['static', 'static/css', 'static/js', 'static/img', 'templates']
    for dir_path in static_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Создана директория: {dir_path}")
    
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Запуск приложения VOGUE ÉLITE")
    logger.info(f"Адрес: http://{host}:{port}")
    logger.info(f"Режим отладки: {debug}")
    logger.info(f"База данных: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.run(host=host, port=port, debug=debug)
