import telebot
from telebot import types
import json
import logging
from datetime import datetime, timedelta
import time
import threading
import random
import sqlite3
import os
import requests
import hashlib
import urllib.parse
from typing import Optional, Dict, List, Any

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VogueEliteBot')

# Конфигурация бота
class Config:
    # Ваши данные
    BOT_TOKEN = '8445063044:AAGwsp4PGsSInBDYfAwVWeOq6FNEgZHqImc'
    ADMIN_IDS = [1217487530]  # Ваш ID
    WEB_APP_URL = 'https://fashionstorebot.onrender.com'
    SHOP_NAME = "VOGUE ÉLITE"
    SHOP_SLOGAN = "Искусство стиля"
    SHOP_PHONE = "+7 (495) 123-45-67"
    SHOP_EMAIL = "info@vogue-elite.ru"
    SUPPORT_USERNAME = "@Lexaa_161"
    FREE_DELIVERY_THRESHOLD = 20000
    DELIVERY_COST = 500
    DATABASE_PATH = 'fashion_store.db'
    CURRENCY = "₽"
    SYNC_INTERVAL = 300  # 5 минут

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
    HOME = "🏠"
    SEARCH = "🔎"
    REFRESH = "🔄"
    DOWNLOAD = "📥"
    UPLOAD = "📤"
    BELL = "🔔"
    CALENDAR = "📅"
    CHART = "📈"
    CARD = "💳"
    SHOPPING = "🛒"
    COUPON = "🎟️"
    QUALITY = "💎"
    SPEED = "⚡"
    SECURITY = "🔐"
    AWARD = "🏆"
    DIAMOND = "💠"
    TRASH = "🗑️"
    PLUS = "➕"
    MINUS = "➖"
    PERSON = "👤"
    AT = "✉️"
    ID = "🆔"
    LIST = "📋"
    PACKAGE = "📦"
    EYES = "👀"

# Класс для работы с базой данных бота
class BotDatabase:
    def __init__(self, db_path=Config.DATABASE_PATH):
        self.db_path = db_path
        self.web_app_url = Config.WEB_APP_URL
        self.conn = None
        self.init_connection()
        self.init_db()
    
    def init_connection(self):
        """Инициализация соединения с базой данных"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Подключение к базе данных установлено: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    def init_db(self):
        """Инициализация структуры базы данных"""
        cursor = self.conn.cursor()
        
        # Основная таблица пользователей бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                web_user_id INTEGER,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                language_code TEXT DEFAULT 'ru',
                is_admin INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                referral_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notifications_enabled INTEGER DEFAULT 1,
                cart_synced INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица кэша товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_products_cache (
                id INTEGER PRIMARY KEY,
                article TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                detailed_description TEXT,
                price REAL NOT NULL,
                old_price REAL,
                discount INTEGER DEFAULT 0,
                category TEXT NOT NULL,
                subcategory TEXT,
                size TEXT,
                color TEXT,
                material TEXT,
                brand TEXT,
                season TEXT,
                country TEXT,
                image_url TEXT,
                images TEXT,
                is_new INTEGER DEFAULT 0,
                is_hit INTEGER DEFAULT 0,
                is_exclusive INTEGER DEFAULT 0,
                is_limited INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                stock INTEGER DEFAULT 0,
                weight REAL,
                dimensions TEXT,
                care_instructions TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица состояний пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id)
            )
        ''')
        
        # Таблица истории действий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id)
            )
        ''')
        
        # Таблица промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                discount_percent INTEGER DEFAULT 0,
                discount_amount REAL,
                min_order_amount REAL DEFAULT 0,
                usage_limit INTEGER,
                used_count INTEGER DEFAULT 0,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица корзины
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                selected_size TEXT,
                selected_color TEXT,
                price_at_addition REAL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_to_web INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id),
                FOREIGN KEY (product_id) REFERENCES bot_products_cache (id)
            )
        ''')
        
        # Таблица избранного
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id),
                FOREIGN KEY (product_id) REFERENCES bot_products_cache (id)
            )
        ''')
        
        # Таблица просмотренных товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id),
                FOREIGN KEY (product_id) REFERENCES bot_products_cache (id)
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                total_amount REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                delivery_cost REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                delivery_address TEXT,
                delivery_type TEXT DEFAULT 'courier',
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                promo_code TEXT,
                customer_notes TEXT,
                admin_notes TEXT,
                items_json TEXT NOT NULL,
                telegram_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users (telegram_id)
            )
        ''')
        
        # Добавляем администраторов
        for admin_id in Config.ADMIN_IDS:
            cursor.execute('''
                INSERT OR IGNORE INTO bot_users 
                (telegram_id, username, first_name, is_admin, is_vip, referral_code)
                VALUES (?, ?, ?, 1, 1, ?)
            ''', (admin_id, 'admin', 'Администратор', f'ADMIN{admin_id}'))
        
        # Добавляем тестовые товары
        test_products = [
            (1, 'VOGUE001', 'Эксклюзивное вечернее платье', 'Роскошное платье премиум-класса',
             'Эксклюзивное вечернее платье из натурального шелка с ручной вышибкой', 45000, 52000,
             15, 'Платья', 'Вечерние платья', 'XS,S,M,L,XL', 'Черный, Золотой, Белый',
             'Шелк, Кружево', 'VOGUE ÉLITE', 'Весна-Лето 2024', 'Италия',
             'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&h=1200&fit=crop&q=80',
             json.dumps([
                'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&h=1200&fit=crop&q=80',
                'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800&h=1200&fit=crop&q=80'
             ]), 1, 0, 1, 0, 1, 8, 0.8, 'Длина: 120см, Обхват: 90см',
             'Только химчистка. Не стирать. Хранить в сухом месте.',
             '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            
            (2, 'VOGUE002', 'Кашемировый костюм', 'Изысканный костюм из итальянского кашемира',
             'Премиальный костюм из итальянского кашемира с золотой ручной вышибкой', 68000, 0,
             0, 'Костюмы', 'Деловые костюмы', '44,46,48,50,52', 'Серый, Синий, Черный',
             'Кашемир, Шелк', 'VOGUE ÉLITE', 'Осень-Зима 2024', 'Италия',
             'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&h=1200&fit=crop&q=80',
             json.dumps([
                'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&h=1200&fit=crop&q=80'
             ]), 0, 1, 1, 1, 1, 5, 1.2, 'Длина: 130см, Обхват: 100см',
             'Химчистка. Не отбеливать.',
             '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            
            (3, 'VOGUE003', 'Кожаная сумка', 'Лимитированная сумка из кожи крокодила',
             'Эксклюзивная сумка из кожи крокодила с платиновой фурнитурой', 125000, 150000,
             17, 'Сумки', 'Кожаные сумки', 'Один размер', 'Черный, Коричневый',
             'Кожа крокодила, Платина', 'VOGUE ÉLITE', 'Круглогодичная', 'Франция',
             'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&h=1200&fit=crop&q=80',
             json.dumps([
                'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&h=1200&fit=crop&q=80'
             ]), 1, 1, 1, 1, 1, 3, 0.5, '30x20x10 см',
             'Протирать сухой тканью. Избегать воды.',
             '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            
            (4, 'VOGUE004', 'Шелковая блуза', 'Элегантная блуза из натурального шелка',
             'Изысканная блуза из натурального шелка с французскими кружевами', 28000, 35000,
             20, 'Блузы', 'Вечерние блузы', 'XS,S,M,L', 'Белый, Бежевый, Розовый',
             'Шелк, Кружево', 'VOGUE ÉLITE', 'Весна-Лето 2024', 'Франция',
             'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800&h=1200&fit=crop&q=80',
             json.dumps([
                'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800&h=1200&fit=crop&q=80'
             ]), 1, 0, 0, 0, 1, 12, 0.3, 'Длина: 70см, Обхват: 85см',
             'Ручная стирка. Не выжимать.',
             '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            
            (5, 'VOGUE005', 'Кожаные туфли', 'Роскошные кожаные туфли ручной работы',
             'Туфли из итальянской кожи с ручной строчкой', 42000, 50000,
             16, 'Обувь', 'Туфли', '36,37,38,39,40', 'Черный, Коричневый, Бордовый',
             'Натуральная кожа, Замша', 'VOGUE ÉLITE', 'Круглогодичная', 'Италия',
             'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=800&h=1200&fit=crop&q=80',
             json.dumps([
                'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=800&h=1200&fit=crop&q=80'
             ]), 0, 1, 0, 0, 1, 15, 0.6, 'Размеры: 36-40',
             'Использовать защитные спреи. Чистить специальными средствами.',
             '2024-01-01 10:00:00', '2024-01-01 10:00:00')
        ]
        
        for product in test_products:
            cursor.execute('''
                INSERT OR REPLACE INTO bot_products_cache 
                (id, article, name, description, detailed_description, price, old_price, 
                 discount, category, subcategory, size, color, material, brand, season, 
                 country, image_url, images, is_new, is_hit, is_exclusive, is_limited, 
                 is_active, stock, weight, dimensions, care_instructions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
        
        # Добавляем тестовые промокоды
        test_promo_codes = [
            ('WELCOME15', 'Приветственная скидка для новых клиентов', 15, None, 0, 1000, 0, None, '2024-12-31 23:59:59'),
            ('VIP25', 'Скидка для VIP клиентов', 25, None, 50000, 500, 0, None, '2024-12-31 23:59:59'),
            ('SUMMER2024', 'Скидка на летнюю коллекцию', 20, None, 30000, 300, 0, None, '2024-08-31 23:59:59'),
            ('FIRSTORDER', 'Скидка на первый заказ', 10, None, 10000, 2000, 0, None, '2024-12-31 23:59:59'),
            ('ELITE30', 'Эксклюзивная скидка VOGUE ÉLITE', 30, None, 100000, 100, 0, None, '2024-12-31 23:59:59')
        ]
        
        for promo in test_promo_codes:
            cursor.execute('''
                INSERT OR IGNORE INTO bot_promo_codes 
                (code, description, discount_percent, discount_amount, min_order_amount, usage_limit, used_count, valid_from, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', promo)
        
        self.conn.commit()
        logger.info("База данных бота инициализирована с тестовыми данными")
    
    def sync_with_webapp(self):
        """Синхронизация с веб-приложением"""
        try:
            logger.info("Начинаю синхронизацию с веб-приложением...")
            
            # Синхронизация товаров
            products_synced = self.sync_products()
            
            # Синхронизация пользователей
            users_synced = self.sync_users()
            
            # Синхронизация промокодов
            promos_synced = self.sync_promo_codes()
            
            logger.info(f"Синхронизация завершена: товары={products_synced}, пользователи={users_synced}, промокоды={promos_synced}")
            return products_synced and users_synced and promos_synced
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации с веб-приложением: {e}")
            return False
    
    def sync_products(self):
        """Синхронизация товаров с веб-приложением"""
        try:
            url = f"{self.web_app_url}/api/products"
            logger.info(f"Запрос товаров с {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    products = data.get('products', [])
                    
                    cursor = self.conn.cursor()
                    synced_count = 0
                    
                    for product in products:
                        try:
                            # Преобразуем изображения в JSON строку
                            images = json.dumps(product.get('images', [])) if product.get('images') else None
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO bot_products_cache 
                                (id, article, name, description, detailed_description, price, old_price, 
                                 discount, category, subcategory, size, color, material, brand, season, 
                                 country, image_url, images, is_new, is_hit, is_exclusive, is_limited, 
                                 is_active, stock, weight, dimensions, care_instructions, created_at, updated_at, last_synced)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (
                                product['id'],
                                product.get('article', ''),
                                product.get('name', ''),
                                product.get('description', ''),
                                product.get('detailed_description', ''),
                                product.get('price', 0),
                                product.get('old_price'),
                                product.get('discount', 0),
                                product.get('category', ''),
                                product.get('subcategory'),
                                product.get('size'),
                                product.get('color'),
                                product.get('material'),
                                product.get('brand'),
                                product.get('season'),
                                product.get('country'),
                                product.get('image_url', ''),
                                images,
                                product.get('is_new', False),
                                product.get('is_hit', False),
                                product.get('is_exclusive', False),
                                product.get('is_limited', False),
                                True,  # is_active
                                product.get('stock', 0),
                                product.get('weight'),
                                product.get('dimensions'),
                                product.get('care_instructions'),
                                product.get('created_at'),
                                product.get('updated_at')
                            ))
                            
                            if cursor.rowcount > 0:
                                synced_count += 1
                                
                        except Exception as e:
                            logger.error(f"Ошибка синхронизации товара {product.get('id')}: {e}")
                    
                    self.conn.commit()
                    logger.info(f"Синхронизировано товаров: {synced_count}")
                    return True
                else:
                    logger.warning(f"API вернуло ошибку: {data.get('message')}")
                    # Если API недоступно, используем локальные данные
                    return True
            else:
                logger.warning(f"Ошибка HTTP при синхронизации товаров: {response.status_code}")
                # Если API недоступно, используем локальные данные
                return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при синхронизации товаров: {e}")
            # Если API недоступно, используем локальные данные
            return True
        except Exception as e:
            logger.error(f"Неожиданная ошибка при синхронизации товаров: {e}")
            return True
    
    def sync_users(self):
        """Синхронизация пользователей с веб-приложением"""
        try:
            # Получаем всех пользователей бота
            cursor = self.conn.cursor()
            cursor.execute('SELECT telegram_id, username, first_name, last_name FROM bot_users WHERE web_user_id IS NULL')
            bot_users = cursor.fetchall()
            
            if not bot_users:
                return True
            
            logger.info(f"Найдено {len(bot_users)} пользователей для синхронизации")
            
            for bot_user in bot_users:
                telegram_id = bot_user['telegram_id']
                
                try:
                    # Создаем пользователя в веб-приложении
                    url = f"{self.web_app_url}/api/user/telegram/create"
                    user_data = {
                        'telegram_id': telegram_id,
                        'username': bot_user['username'],
                        'first_name': bot_user['first_name'],
                        'last_name': bot_user['last_name']
                    }
                    
                    response = requests.post(url, json=user_data, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            cursor.execute('''
                                UPDATE bot_users 
                                SET web_user_id = ?
                                WHERE telegram_id = ?
                            ''', (data['user_id'], telegram_id))
                            logger.info(f"Пользователь {telegram_id} синхронизирован с веб-приложением")
                    else:
                        logger.warning(f"Ошибка создания пользователя {telegram_id}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Ошибка синхронизации пользователя {telegram_id}: {e}")
            
            self.conn.commit()
            logger.info("Синхронизация пользователей завершена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации пользователей: {e}")
            return False
    
    def force_clear_all_states(self):
        """Принудительная очистка всех состояний пользователей (экстренная функция)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM bot_user_states')
            self.conn.commit()
            logger.info("Все состояния пользователей очищены принудительно")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки состояний: {e}")
            return False
    
    def clear_user_state_by_id(self, user_id: int):
        """Принудительная очистка состояния конкретного пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM bot_user_states WHERE user_id = ?', (user_id,))
            self.conn.commit()
            logger.info(f"Состояние пользователя {user_id} очищено принудительно")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка очистки состояния пользователя: {e}")
            return False
    
    def sync_promo_codes(self):
        """Синхронизация промокодов (используем локальные)"""
        # В этой версии используем локальные промокоды
        return True
    
    def register_user(self, telegram_id: int, username: str, first_name: str, 
                     last_name: str = None, language_code: str = 'ru') -> Dict[str, Any]:
        """Регистрация или обновление пользователя"""
        try:
            cursor = self.conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute('SELECT * FROM bot_users WHERE telegram_id = ?', (telegram_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Обновляем данные пользователя
                cursor.execute('''
                    UPDATE bot_users 
                    SET username = ?, first_name = ?, last_name = ?, language_code = ?,
                        last_activity = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (username, first_name, last_name, language_code, telegram_id))
                
                is_new = False
                logger.info(f"Пользователь обновлен: {first_name} (@{username})")
            else:
                # Создаем нового пользователя
                referral_code = f"VIP{random.randint(100000, 999999)}"
                while True:
                    cursor.execute("SELECT 1 FROM bot_users WHERE referral_code = ?", (referral_code,))
                    if not cursor.fetchone():
                        break
                    referral_code = f"VIP{random.randint(100000, 999999)}"
                
                cursor.execute('''
                    INSERT INTO bot_users 
                    (telegram_id, username, first_name, last_name, language_code, referral_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name, language_code, referral_code))
                
                # Логируем действие
                cursor.execute('''
                    INSERT INTO bot_user_actions (user_id, action_type, action_data)
                    VALUES (?, ?, ?)
                ''', (telegram_id, 'registration', json.dumps({
                    'referral_code': referral_code,
                    'source': 'telegram_bot'
                })))
                
                is_new = True
                logger.info(f"Новый пользователь зарегистрирован: {first_name} (@{username}) ID: {telegram_id}")
            
            self.conn.commit()
            
            # Получаем данные пользователя
            cursor.execute('SELECT * FROM bot_users WHERE telegram_id = ?', (telegram_id,))
            user_data = dict(cursor.fetchone())
            
            return {
                'success': True,
                'is_new': is_new,
                'user': user_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            self.conn.rollback()
            return {'success': False, 'error': str(e)}
    
    def update_user_activity(self, telegram_id: int):
        """Обновление времени последней активности пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE bot_users 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления активности пользователя: {e}")
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM bot_users WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    def get_user_stats(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение статистики пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT total_orders, total_spent, is_vip, referral_code,
                       (SELECT COUNT(*) FROM bot_user_actions WHERE user_id = ?) as total_actions,
                       (SELECT COUNT(*) FROM bot_cart WHERE user_id = ?) as cart_items,
                       (SELECT COUNT(*) FROM bot_favorites WHERE user_id = ?) as favorite_items,
                       (SELECT COUNT(DISTINCT product_id) FROM bot_view_history WHERE user_id = ?) as viewed_items,
                       (SELECT COUNT(*) FROM bot_orders WHERE user_id = ?) as total_orders_count
                FROM bot_users 
                WHERE telegram_id = ?
            ''', (telegram_id, telegram_id, telegram_id, telegram_id, telegram_id, telegram_id))
            
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя: {e}")
            return None
    
    def get_products(self, category: str = None, limit: int = 10, offset: int = 0, 
                    filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Получение товаров с фильтрацией"""
        try:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM bot_products_cache WHERE is_active = 1'
            params = []
            
            if category and category != 'all':
                query += ' AND category = ?'
                params.append(category)
            
            if filters:
                if filters.get('is_new'):
                    query += ' AND is_new = 1'
                if filters.get('is_hit'):
                    query += ' AND is_hit = 1'
                if filters.get('is_exclusive'):
                    query += ' AND is_exclusive = 1'
                if filters.get('min_price'):
                    query += ' AND price >= ?'
                    params.append(filters['min_price'])
                if filters.get('max_price'):
                    query += ' AND price <= ?'
                    params.append(filters['max_price'])
                if filters.get('brand'):
                    query += ' AND brand = ?'
                    params.append(filters['brand'])
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения товаров: {e}")
            return []
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получение товара по ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM bot_products_cache WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения товара: {e}")
            return None
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск товаров"""
        try:
            cursor = self.conn.cursor()
            search_term = f'%{query}%'
            cursor.execute('''
                SELECT * FROM bot_products_cache 
                WHERE is_active = 1 AND (name LIKE ? OR description LIKE ? OR article LIKE ? OR brand LIKE ?)
                LIMIT ?
            ''', (search_term, search_term, search_term, search_term, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска товаров: {e}")
            return []
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1, 
                   size: str = None, color: str = None) -> bool:
        """Добавление товара в корзину"""
        try:
            # Проверяем наличие товара
            product = self.get_product(product_id)
            if not product or product['stock'] < quantity:
                return False
            
            cursor = self.conn.cursor()
            
            # Проверяем, есть ли уже такой товар в корзине
            cursor.execute('''
                SELECT id, quantity FROM bot_cart 
                WHERE user_id = ? AND product_id = ? AND selected_size = ? AND selected_color = ?
            ''', (user_id, product_id, size, color))
            
            existing_item = cursor.fetchone()
            
            if existing_item:
                # Обновляем количество
                new_quantity = existing_item['quantity'] + quantity
                if product['stock'] < new_quantity:
                    return False
                
                cursor.execute('''
                    UPDATE bot_cart 
                    SET quantity = ?, added_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (new_quantity, existing_item['id']))
            else:
                # Добавляем новый товар
                cursor.execute('''
                    INSERT INTO bot_cart 
                    (user_id, product_id, quantity, selected_size, selected_color, price_at_addition)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, product_id, quantity, size, color, product['price']))
            
            # Обновляем активность пользователя
            self.update_user_activity(user_id)
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'add_to_cart', json.dumps({
                'product_id': product_id,
                'quantity': quantity,
                'size': size,
                'color': color
            })))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления в корзину: {e}")
            self.conn.rollback()
            return False
    
    def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение корзины пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT c.*, p.name, p.price, p.image_url, p.stock, p.is_active,
                       p.article, p.brand, p.category
                FROM bot_cart c
                JOIN bot_products_cache p ON c.product_id = p.id
                WHERE c.user_id = ?
                ORDER BY c.added_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            cart_items = []
            
            for row in rows:
                item = dict(row)
                item['total'] = item['price'] * item['quantity']
                cart_items.append(item)
            
            return cart_items
            
        except Exception as e:
            logger.error(f"Ошибка получения корзины: {e}")
            return []
    
    def get_cart_total(self, user_id: int) -> Dict[str, Any]:
        """Расчет итогов корзины"""
        try:
            cart_items = self.get_cart(user_id)
            
            subtotal = sum(item['total'] for item in cart_items)
            delivery_cost = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD else Config.DELIVERY_COST
            total = subtotal + delivery_cost
            
            return {
                'subtotal': subtotal,
                'delivery_cost': delivery_cost,
                'total': total,
                'item_count': len(cart_items),
                'free_delivery_threshold': Config.FREE_DELIVERY_THRESHOLD,
                'needs_for_free_delivery': max(0, Config.FREE_DELIVERY_THRESHOLD - subtotal)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета корзины: {e}")
            return {'subtotal': 0, 'delivery_cost': 0, 'total': 0, 'item_count': 0}
    
    def update_cart_item(self, cart_item_id: int, quantity: int, user_id: int) -> bool:
        """Обновление количества товара в корзине"""
        try:
            cursor = self.conn.cursor()
            
            # Проверяем принадлежность товара пользователю
            cursor.execute('SELECT product_id FROM bot_cart WHERE id = ? AND user_id = ?', 
                         (cart_item_id, user_id))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            product_id = result['product_id']
            product = self.get_product(product_id)
            
            if not product or product['stock'] < quantity:
                return False
            
            if quantity <= 0:
                cursor.execute('DELETE FROM bot_cart WHERE id = ?', (cart_item_id,))
            else:
                cursor.execute('UPDATE bot_cart SET quantity = ? WHERE id = ?', (quantity, cart_item_id))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'update_cart', json.dumps({
                'cart_item_id': cart_item_id,
                'quantity': quantity
            })))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления корзины: {e}")
            self.conn.rollback()
            return False
    
    def remove_from_cart(self, cart_item_id: int, user_id: int) -> bool:
        """Удаление товара из корзины"""
        try:
            cursor = self.conn.cursor()
            
            # Проверяем принадлежность товара пользователю
            cursor.execute('SELECT 1 FROM bot_cart WHERE id = ? AND user_id = ?', 
                         (cart_item_id, user_id))
            if not cursor.fetchone():
                return False
            
            cursor.execute('DELETE FROM bot_cart WHERE id = ?', (cart_item_id,))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'remove_from_cart', json.dumps({
                'cart_item_id': cart_item_id
            })))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из корзины: {e}")
            self.conn.rollback()
            return False
    
    def clear_cart(self, user_id: int) -> bool:
        """Очистка корзины пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM bot_cart WHERE user_id = ?', (user_id,))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'clear_cart', json.dumps({})))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки корзины: {e}")
            self.conn.rollback()
            return False
    
    def add_to_favorites(self, user_id: int, product_id: int) -> bool:
        """Добавление товара в избранное"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO bot_favorites (user_id, product_id)
                VALUES (?, ?)
            ''', (user_id, product_id))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'add_to_favorites', json.dumps({
                'product_id': product_id
            })))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")
            self.conn.rollback()
            return False
    
    def remove_from_favorites(self, user_id: int, product_id: int) -> bool:
        """Удаление товара из избранного"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM bot_favorites WHERE user_id = ? AND product_id = ?', 
                         (user_id, product_id))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'remove_from_favorites', json.dumps({
                'product_id': product_id
            })))
            
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка удаления из избранного: {e}")
            self.conn.rollback()
            return False
    
    def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение избранных товаров пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT p.* 
                FROM bot_products_cache p
                JOIN bot_favorites f ON p.id = f.product_id
                WHERE f.user_id = ? AND p.is_active = 1
                ORDER BY f.added_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения избранного: {e}")
            return []
    
    def add_to_view_history(self, user_id: int, product_id: int):
        """Добавление товара в историю просмотров"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO bot_view_history (user_id, product_id)
                VALUES (?, ?)
            ''', (user_id, product_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка добавления в историю просмотров: {e}")
    
    def get_view_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории просмотров"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT p.* 
                FROM bot_products_cache p
                JOIN bot_view_history v ON p.id = v.product_id
                WHERE v.user_id = ? AND p.is_active = 1
                ORDER BY v.viewed_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения истории просмотров: {e}")
            return []
    
    def save_user_state(self, user_id: int, state: str, data: Dict[str, Any] = None):
        """Сохранение состояния пользователя"""
        try:
            cursor = self.conn.cursor()
            data_json = json.dumps(data) if data else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO bot_user_states (user_id, state, data)
                VALUES (?, ?, ?)
            ''', (user_id, state, data_json))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния пользователя: {e}")
    
    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение состояния пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT state, data FROM bot_user_states WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['data']) if row['data'] else None
                return {'state': row['state'], 'data': data}
            return None
        except Exception as e:
            logger.error(f"Ошибка получения состояния пользователя: {e}")
            return None
    
    def clear_user_state(self, user_id: int):
        """Очистка состояния пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM bot_user_states WHERE user_id = ?', (user_id,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки состояния пользователя: {e}")
    
    def log_user_action(self, user_id: int, action_type: str, action_data: Dict[str, Any] = None):
        """Логирование действий пользователя"""
        try:
            cursor = self.conn.cursor()
            data_json = json.dumps(action_data) if action_data else None
            
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, action_type, data_json))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования действия пользователя: {e}")
    
    def get_promo_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Получение информации о промокоде"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM bot_promo_codes 
                WHERE code = ? AND is_active = 1 
                AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
            ''', (code,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения промокода: {e}")
            return None
    
    def check_promo_code(self, code: str, order_amount: float) -> Dict[str, Any]:
        """Проверка промокода"""
        try:
            promo = self.get_promo_code(code)
            
            if not promo:
                return {'valid': False, 'message': 'Промокод не найден'}
            
            if promo['min_order_amount'] > 0 and order_amount < promo['min_order_amount']:
                return {
                    'valid': False, 
                    'message': f'Минимальная сумма заказа для этого промокода: {promo["min_order_amount"]:,.0f} {Config.CURRENCY}'
                }
            
            if promo['usage_limit'] and promo['used_count'] >= promo['usage_limit']:
                return {'valid': False, 'message': 'Лимит использования промокода исчерпан'}
            
            # Рассчитываем скидку
            discount = 0
            if promo['discount_percent'] > 0:
                discount = order_amount * promo['discount_percent'] / 100
            elif promo['discount_amount'] > 0:
                discount = min(promo['discount_amount'], order_amount)
            
            return {
                'valid': True,
                'discount': discount,
                'discount_percent': promo['discount_percent'],
                'discount_amount': promo['discount_amount'],
                'description': promo['description'],
                'new_total': order_amount - discount
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки промокода: {e}")
            return {'valid': False, 'message': 'Ошибка проверки промокода'}
    
    def create_order(self, user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заказа"""
        try:
            # Проверяем товары в корзине
            cart_items = self.get_cart(user_id)
            if not cart_items:
                return {'success': False, 'message': 'Корзина пуста'}
            
            # Проверяем наличие товаров
            unavailable_items = []
            for item in cart_items:
                if item['stock'] < item['quantity']:
                    unavailable_items.append(item['name'])
            
            if unavailable_items:
                items_list = "\n".join([f"• {name}" for name in unavailable_items[:3]])
                return {'success': False, 'message': f'Некоторые товары закончились:\n{items_list}'}
            
            # Рассчитываем сумму
            subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
            delivery_cost = 0 if subtotal >= Config.FREE_DELIVERY_THRESHOLD else Config.DELIVERY_COST
            
            # Применяем промокод если есть
            promo_code = order_data.get('promo_code')
            discount = 0
            if promo_code:
                promo_check = self.check_promo_code(promo_code, subtotal)
                if promo_check['valid']:
                    discount = promo_check['discount']
            
            final_amount = subtotal + delivery_cost - discount
            
            # Генерируем номер заказа
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            order_number = f"TG{timestamp}{user_id:04d}"
            
            # Подготавливаем данные товаров
            items_data = []
            for item in cart_items:
                item_data = {
                    'product_id': item['product_id'],
                    'name': item['name'],
                    'article': item['article'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'size': item['selected_size'],
                    'color': item['selected_color'],
                    'total': item['price'] * item['quantity']
                }
                items_data.append(item_data)
            
            # Создаем заказ
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO bot_orders 
                (order_number, user_id, total_amount, discount_amount, delivery_cost, final_amount,
                 delivery_address, delivery_type, payment_method, promo_code, customer_notes, items_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_number,
                user_id,
                subtotal,
                discount,
                delivery_cost,
                final_amount,
                order_data.get('address', ''),
                order_data.get('delivery_type', 'courier'),
                order_data.get('payment_method', 'card'),
                promo_code,
                order_data.get('notes', ''),
                json.dumps(items_data)
            ))
            
            order_id = cursor.lastrowid
            
            # Обновляем остатки товаров
            for item in cart_items:
                cursor.execute('''
                    UPDATE bot_products_cache 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            # Очищаем корзину
            cursor.execute('DELETE FROM bot_cart WHERE user_id = ?', (user_id,))
            
            # Обновляем статистику пользователя
            cursor.execute('''
                UPDATE bot_users 
                SET total_orders = total_orders + 1, 
                    total_spent = total_spent + ?,
                    last_activity = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (final_amount, user_id))
            
            # Присваиваем VIP статус при достижении порога
            cursor.execute('SELECT total_spent FROM bot_users WHERE telegram_id = ?', (user_id,))
            total_spent = cursor.fetchone()['total_spent']
            
            if total_spent >= 100000:
                cursor.execute('UPDATE bot_users SET is_vip = 1 WHERE telegram_id = ?', (user_id,))
            
            # Обновляем использование промокода
            if promo_code:
                cursor.execute('''
                    UPDATE bot_promo_codes 
                    SET used_count = used_count + 1 
                    WHERE code = ?
                ''', (promo_code,))
            
            # Логируем действие
            cursor.execute('''
                INSERT INTO bot_user_actions (user_id, action_type, action_data)
                VALUES (?, ?, ?)
            ''', (user_id, 'create_order', json.dumps({
                'order_number': order_number,
                'order_id': order_id,
                'amount': final_amount
            })))
            
            self.conn.commit()
            
            # Получаем данные заказа
            cursor.execute('SELECT * FROM bot_orders WHERE id = ?', (order_id,))
            order = dict(cursor.fetchone())
            
            return {
                'success': True,
                'order': order,
                'order_number': order_number,
                'message': 'Заказ успешно создан!'
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {e}")
            self.conn.rollback()
            return {'success': False, 'message': f'Ошибка создания заказа: {str(e)}'}
    
    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение заказов пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM bot_orders 
                WHERE user_id = ? 
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id,))
            
            rows = cursor.fetchall()
            orders = []
            
            for row in rows:
                order = dict(row)
                # Парсим товары заказа
                if order.get('items_json'):
                    order['items'] = json.loads(order['items_json'])
                else:
                    order['items'] = []
                orders.append(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"Ошибка получения заказов пользователя: {e}")
            return []
    
    def get_order(self, order_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение заказа по ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM bot_orders WHERE id = ? AND user_id = ?', (order_id, user_id))
            row = cursor.fetchone()
            
            if row:
                order = dict(row)
                if order.get('items_json'):
                    order['items'] = json.loads(order['items_json'])
                else:
                    order['items'] = []
                return order
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения заказа: {e}")
            return None
    
    def get_categories(self) -> List[str]:
        """Получение списка категорий"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM bot_products_cache WHERE is_active = 1 ORDER BY category')
            rows = cursor.fetchall()
            return [row['category'] for row in rows if row['category']]
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []
    
    def get_brands(self) -> List[str]:
        """Получение списка брендов"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT DISTINCT brand FROM bot_products_cache WHERE is_active = 1 AND brand IS NOT NULL ORDER BY brand')
            rows = cursor.fetchall()
            return [row['brand'] for row in rows if row['brand']]
        except Exception as e:
            logger.error(f"Ошибка получения брендов: {e}")
            return []
    
    def get_all_users(self, include_admins: bool = False) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        try:
            cursor = self.conn.cursor()
            
            if include_admins:
                cursor.execute('SELECT telegram_id, first_name, username, is_vip, is_admin FROM bot_users')
            else:
                cursor.execute('SELECT telegram_id, first_name, username, is_vip FROM bot_users WHERE is_admin = 0')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    def get_vip_users(self) -> List[Dict[str, Any]]:
        """Получение списка VIP пользователей"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT telegram_id, first_name, username FROM bot_users WHERE is_vip = 1')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения списка VIP пользователей: {e}")
            return []
    
    def get_active_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получение активных пользователей за последние N дней"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f'''
                SELECT telegram_id, first_name, username, last_activity 
                FROM bot_users 
                WHERE last_activity > datetime('now', '-{days} days')
                ORDER BY last_activity DESC
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Получение системной статистики"""
        try:
            cursor = self.conn.cursor()
            stats = {}
            
            # Статистика пользователей
            cursor.execute('SELECT COUNT(*) as total_users FROM bot_users')
            stats['total_users'] = cursor.fetchone()['total_users']
            
            cursor.execute('SELECT COUNT(*) as vip_users FROM bot_users WHERE is_vip = 1')
            stats['vip_users'] = cursor.fetchone()['vip_users']
            
            cursor.execute('SELECT COUNT(*) as active_today FROM bot_users WHERE last_activity > datetime("now", "-1 day")')
            stats['active_today'] = cursor.fetchone()['active_today']
            
            cursor.execute('SELECT COUNT(*) as active_week FROM bot_users WHERE last_activity > datetime("now", "-7 days")')
            stats['active_week'] = cursor.fetchone()['active_week']
            
            # Статистика товаров
            cursor.execute('SELECT COUNT(*) as total_products FROM bot_products_cache WHERE is_active = 1')
            stats['total_products'] = cursor.fetchone()['total_products']
            
            cursor.execute('SELECT COUNT(*) as new_products FROM bot_products_cache WHERE is_new = 1 AND is_active = 1')
            stats['new_products'] = cursor.fetchone()['new_products']
            
            cursor.execute('SELECT COUNT(*) as exclusive_products FROM bot_products_cache WHERE is_exclusive = 1 AND is_active = 1')
            stats['exclusive_products'] = cursor.fetchone()['exclusive_products']
            
            cursor.execute('SELECT SUM(stock * price) as total_inventory_value FROM bot_products_cache WHERE is_active = 1')
            stats['inventory_value'] = cursor.fetchone()['inventory_value'] or 0
            
            # Статистика корзин
            cursor.execute('SELECT COUNT(DISTINCT user_id) as users_with_cart FROM bot_cart')
            stats['users_with_cart'] = cursor.fetchone()['users_with_cart']
            
            cursor.execute('SELECT COUNT(*) as total_cart_items FROM bot_cart')
            stats['total_cart_items'] = cursor.fetchone()['total_cart_items']
            
            # Статистика избранного
            cursor.execute('SELECT COUNT(DISTINCT user_id) as users_with_favorites FROM bot_favorites')
            stats['users_with_favorites'] = cursor.fetchone()['users_with_favorites']
            
            cursor.execute('SELECT COUNT(*) as total_favorites FROM bot_favorites')
            stats['total_favorites'] = cursor.fetchone()['total_favorites']
            
            # Статистика заказов
            cursor.execute('SELECT COUNT(*) as total_orders FROM bot_orders')
            stats['total_orders'] = cursor.fetchone()['total_orders']
            
            cursor.execute('SELECT SUM(final_amount) as total_revenue FROM bot_orders')
            stats['total_revenue'] = cursor.fetchone()['total_revenue'] or 0
            
            cursor.execute('SELECT status, COUNT(*) as count FROM bot_orders GROUP BY status')
            stats['orders_by_status'] = dict(cursor.fetchall())
            
            # Статистика действий
            cursor.execute('SELECT COUNT(*) as total_actions FROM bot_user_actions')
            stats['total_actions'] = cursor.fetchone()['total_actions']
            
            cursor.execute('SELECT action_type, COUNT(*) as count FROM bot_user_actions GROUP BY action_type')
            stats['actions_by_type'] = dict(cursor.fetchall())
            
            # Статистика по категориям
            cursor.execute('SELECT category, COUNT(*) as count FROM bot_products_cache WHERE is_active = 1 GROUP BY category')
            stats['categories'] = dict(cursor.fetchall())
            
            # Статистика по брендам
            cursor.execute('SELECT brand, COUNT(*) as count FROM bot_products_cache WHERE is_active = 1 AND brand IS NOT NULL GROUP BY brand')
            stats['brands'] = dict(cursor.fetchall())
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения системной статистики: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Очистка старых данных"""
        try:
            cursor = self.conn.cursor()
            
            # Очищаем старые состояния пользователей (старше 1 дня)
            cursor.execute('DELETE FROM bot_user_states WHERE created_at < datetime("now", "-1 day")')
            states_deleted = cursor.rowcount
            
            # Очищаем старую историю просмотров (старше 90 дней)
            cursor.execute('DELETE FROM bot_view_history WHERE viewed_at < datetime("now", "-90 days")')
            views_deleted = cursor.rowcount
            
            # Очищаем старые действия (старше 180 дней)
            cursor.execute('DELETE FROM bot_user_actions WHERE created_at < datetime("now", "-180 days")')
            actions_deleted = cursor.rowcount
            
            self.conn.commit()
            
            if any([states_deleted, views_deleted, actions_deleted]):
                logger.info(f"Очищены данные: состояния={states_deleted}, просмотры={views_deleted}, действия={actions_deleted}")
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}")
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")

class VogueEliteBot:
    def __init__(self):
        # Проверяем токен бота
        if not Config.BOT_TOKEN:
            logger.error("Не указан токен бота!")
            raise ValueError("Токен бота не указан")
        
        # Инициализация бота
        self.bot = telebot.TeleBot(Config.BOT_TOKEN, parse_mode='HTML')
        self.db = BotDatabase()
        self.web_app_url = Config.WEB_APP_URL
        
        # Интервалы для фоновых задач
        self.sync_interval = Config.SYNC_INTERVAL
        self.cleanup_interval = 3600  # 1 час
        
        # Печатаем информацию о запуске
        self.print_startup_info()
        
        # Настройка обработчиков
        self.setup_handlers()
        
        # Запуск фоновых задач
        self.start_background_tasks()
        
        logger.info("Бот VOGUE ÉLITE успешно инициализирован")
    
    def print_startup_info(self):
        """Вывод информации о запуске бота"""
        print("="*70)
        print(f"{Emoji.LOGO} VOGUE ÉLITE TELEGRAM BOT {Emoji.LOGO}")
        print("="*70)
        print(f"{Emoji.BOT} Бот запущен и готов к работе")
        print(f"{Emoji.WEBSITE} Web App URL: {self.web_app_url}")
        print(f"{Emoji.ADMIN} Admin IDs: {', '.join(map(str, Config.ADMIN_IDS))}")
        print(f"{Emoji.DATABASE} База данных: {Config.DATABASE_PATH}")
        print(f"{Emoji.SHOP} Магазин: {Config.SHOP_NAME}")
        print(f"{Emoji.PHONE} Телефон: {Config.SHOP_PHONE}")
        print(f"{Emoji.MONEY} Валюта: {Config.CURRENCY}")
        print("="*70)
        
    def run(self):
        try:
            logger.info("Запускаю бота...")
            self.bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {e}")
    
    def start_background_tasks(self):
        """Запуск фоновых задач"""
        def sync_task():
            while True:
                try:
                    self.db.sync_with_webapp()
                except Exception as e:
                    logger.error(f"Ошибка в задаче синхронизации: {e}")
                time.sleep(self.sync_interval)
        
        def cleanup_task():
            while True:
                try:
                    self.db.cleanup_old_data()
                except Exception as e:
                    logger.error(f"Ошибка в задаче очистки: {e}")
                time.sleep(self.cleanup_interval)
        
        # Запускаем задачи в отдельных потоках
        threading.Thread(target=sync_task, daemon=True).start()
        threading.Thread(target=cleanup_task, daemon=True).start()
        
        logger.info("Фоновые задачи запущены")
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Обработчик команды /start
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            try:
                # Регистрируем или обновляем пользователя
                user_data = self.db.register_user(
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.first_name,
                    message.from_user.last_name,
                    message.from_user.language_code
                )
                
                if user_data['success']:
                    # Логируем действие
                    self.db.log_user_action(message.from_user.id, 'start_command')
                    
                    # Отправляем приветственное сообщение
                    welcome_text = f"""
{Emoji.LOGO} <b>ДОБРО ПОЖАЛОВАТЬ В {Config.SHOP_NAME}!</b>

{Emoji.VIP} <b>Здравствуйте, {message.from_user.first_name}!</b>

{Config.SHOP_SLOGAN}

{Emoji.STAR} <b>Ваши привилегии:</b>
• {Emoji.EXCLUSIVE} Эксклюзивные коллекции от ведущих дизайнеров
• {Emoji.ATELIER} Индивидуальный пошив на заказ
• {Emoji.GIFT} Подарочная упаковка и VIP обслуживание
• {Emoji.DELIVERY} Бесплатная доставка от {Config.FREE_DELIVERY_THRESHOLD:,} {Config.CURRENCY}
• {Emoji.SUPPORT} Персональный консьерж 24/7

{Emoji.NEXT} <b>Используйте меню ниже для навигации:</b>
{Emoji.DRESS} Каталог - Просмотр коллекций
{Emoji.CART} Корзина - Управление покупок
{Emoji.ORDER} Заказы - История и статусы
{Emoji.USER} Профиль - Личный кабинет
{Emoji.SUPPORT} Поддержка - Консультация и помощь
{Emoji.SEARCH} Поиск - Поиск товаров

{Emoji.WEBSITE} <b>Веб-версия магазина:</b>
<a href="{self.web_app_url}">{self.web_app_url}</a>

{Emoji.MESSAGE} <b>Поддержка 24/7:</b> {Config.SUPPORT_USERNAME}
{Emoji.PHONE} <b>Телефон:</b> {Config.SHOP_PHONE}
"""
                    
                    markup = self.create_main_keyboard(message.chat.id)
                    self.bot.send_message(
                        message.chat.id,
                        welcome_text,
                        reply_markup=markup,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    
                    # Если это новый пользователь, отправляем дополнительные инструкции
                    if user_data.get('is_new'):
                        time.sleep(1)
                        self.bot.send_message(
                            message.chat.id,
                            f"{Emoji.INFO} <b>Быстрый старт:</b>\n\n"
                            f"1. Используйте кнопки меню для навигации\n"
                            f"2. Для поиска товара отправьте его название\n"
                            f"3. Используйте промокод WELCOME15 для скидки 15%\n"
                            f"4. Для помощи используйте команду /help",
                            parse_mode='HTML'
                        )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        f"{Emoji.WARNING} Произошла ошибка при регистрации. Пожалуйста, попробуйте позже."
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка обработки команды /start: {e}")
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Произошла ошибка. Пожалуйста, попробуйте позже."
                )
        
        # Обработчик текстовых сообщений
        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def handle_text(message):
            self.process_text_message(message)
        
        # Обработчик callback-запросов
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.process_callback_query(call)
    
    def process_text_message(self, message):
        try:
            text = message.text.strip()
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            logger.info(f"Получено сообщение: '{text}' от {user_id}")
            
            # Обновляем активность пользователя
            self.db.update_user_activity(user_id)
            
            # ========== КОМАНДЫ МЕНЮ (кнопки) - ОБРАБОТКА В ПЕРВУЮ ОЧЕРЕДЬ ==========
            # Сначала проверяем кнопки меню, чтобы они всегда работали правильно
            if text == "👗 Каталог":
                self.show_catalog_categories(message)
                return
            elif text == "🛍️ Корзина":
                self.show_cart(message)
                return
            elif text == "📦 Заказы":
                self.show_orders(message)
                return
            elif text == "👤 Профиль":
                self.show_profile(message)
                return
            elif text == "💖 Избранное":
                self.show_favorites(message)
                return
            elif text == "📞 Поддержка":
                self.show_support(message)
                return
            elif text == "🔎 Поиск":
                self.start_search(message)
                return
            elif text == "🏷️ Скидки":
                self.show_discounts(message)
                return
            elif text == "🌐 Веб-версия":
                self.open_web_app(message)
                return
            elif text == "🏠 Главная":
                self.bot.send_message(
                    chat_id,
                    f"{Emoji.HOME} <b>Главная страница</b>\n\n"
                    f"Используйте меню для навигации по магазину.",
                    reply_markup=self.create_main_keyboard(chat_id),
                    parse_mode='HTML'
                )
                return
            elif text == "🛡️ Админ-панель" and user_id in Config.ADMIN_IDS:
                self.show_admin_panel(message)
                return
            
            # ========== КОМАНДЫ ЧЕРЕЗ СЛЕШ ==========
            elif text == "/start" or text == "/help":
                self.db.clear_user_state(user_id)
                # Очищаем состояние и вызываем старт
                return
            elif text == "/catalog" or text == "/каталог":
                self.db.clear_user_state(user_id)
                self.show_catalog_categories(message)
                return
            elif text == "/cart" or text == "/корзина":
                self.db.clear_user_state(user_id)
                self.show_cart(message)
                return
            elif text == "/orders" or text == "/заказы":
                self.db.clear_user_state(user_id)
                self.show_orders(message)
                return
            elif text == "/profile" or text == "/профиль":
                self.db.clear_user_state(user_id)
                self.show_profile(message)
                return
            elif text == "/favorites" or text == "/избранное":
                self.db.clear_user_state(user_id)
                self.show_favorites(message)
                return
            elif text == "/support" or text == "/поддержка":
                self.db.clear_user_state(user_id)
                self.show_support(message)
                return
            elif text == "/search" or text == "/поиск":
                self.db.clear_user_state(user_id)
                self.start_search(message)
                return
            elif text == "/discount" or text == "/скидки":
                self.db.clear_user_state(user_id)
                self.show_discounts(message)
                return
            elif text == "/web" or text == "/веб":
                self.db.clear_user_state(user_id)
                self.open_web_app(message)
                return
            elif text == "/admin" or text == "/админ":
                if user_id in Config.ADMIN_IDS:
                    self.db.clear_user_state(user_id)
                    self.show_admin_panel(message)
                else:
                    self.bot.send_message(
                        chat_id,
                        f"{Emoji.LOCK} Доступ запрещен",
                        parse_mode='HTML'
                    )
                return
            elif text == "/reset":
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    chat_id,
                    f"{Emoji.REFRESH} <b>Состояние сброшено</b>\n\n"
                    f"Ваше состояние было очищено. Теперь вы можете использовать меню.",
                    reply_markup=self.create_main_keyboard(chat_id),
                    parse_mode='HTML'
                )
                return
            
            # ========== АДМИНИСТРАТОРСКИЕ КОМАНДЫ ==========
            if user_id in Config.ADMIN_IDS:
                if text == "/clear_state":
                    success = self.db.force_clear_all_states()
                    if success:
                        self.bot.send_message(
                            chat_id,
                            f"{Emoji.CHECK} <b>ВСЕ СОСТОЯНИЯ ОЧИЩЕНЫ</b>\n\n"
                            f"Все состояния пользователей были принудительно очищены.",
                            parse_mode='HTML'
                        )
                    else:
                        self.bot.send_message(
                            chat_id,
                            f"{Emoji.WARNING} Ошибка при очистке состояний",
                            parse_mode='HTML'
                        )
                    return
                
                elif text == "/clear_state_all":
                    success = self.db.clear_user_state_by_id(user_id)
                    if success:
                        self.bot.send_message(
                            chat_id,
                            f"{Emoji.CHECK} Ваше состояние очищено",
                            parse_mode='HTML'
                        )
                    else:
                        self.bot.send_message(
                            chat_id,
                            f"{Emoji.WARNING} Состояние не найдено или уже очищено",
                            parse_mode='HTML'
                        )
                    return
                
                elif text == "/sync_now":
                    success = self.db.sync_with_webapp()
                    self.bot.send_message(
                        chat_id,
                        f"{Emoji.REFRESH} Синхронизация: {'Успешно' if success else 'Ошибка'}",
                        parse_mode='HTML'
                    )
                    return
            
            # ========== ПРОМОКОДЫ ==========
            promo_codes = ['WELCOME15', 'VIP25', 'SUMMER2024', 'FIRSTORDER', 'ELITE30']
            if text.upper() in promo_codes:
                self.process_promo_code_input(message, text.upper())
                return
            
            # Теперь проверяем состояния пользователя ТОЛЬКО если это не команда меню
            user_state = self.db.get_user_state(user_id)
            
            if user_state:
                state_action = user_state.get('state')
                state_data = user_state.get('data', {})
                
                # ========== ОБРАБОТКА СОСТОЯНИЙ ==========
                if state_action == 'waiting_order_address':
                    self.process_order_address(message, state_data)
                    return
                elif state_action == 'waiting_order_notes':
                    self.process_order_notes(message, state_data)
                    return
                elif state_action == 'waiting_broadcast_message':
                    self.process_broadcast_message(message, state_data)
                    return
                elif state_action == 'waiting_broadcast_target':
                    self.process_broadcast_target(message, state_data)
                    return
                elif state_action == 'waiting_search_query':
                    self.process_search_query(message, state_data)
                    return
                elif state_action == 'waiting_promo_code':
                    self.process_promo_code(message, state_data)
                    return
                else:
                    # Неизвестное состояние - очищаем
                    self.db.clear_user_state(user_id)
                    # Продолжаем обработку как обычное сообщение
            
            # ========== БЫСТРЫЙ ПОИСК ==========
            if len(text) >= 2:
                self.process_search(message, text)
                return
            
            # ========== СООБЩЕНИЕ НЕ РАСПОЗНАНО ==========
            help_text = f"""
{Emoji.INFO} <b>Используйте меню для навигации:</b>

{Emoji.KEYBOARD} <b>Основные команды:</b>
/start - Главное меню
/reset - Сбросить состояние (если что-то не работает)
/catalog - Каталог товаров
/cart - Корзина покупок
/orders - История заказов
/profile - Личный кабинет
/favorites - Избранное
/support - Служба поддержки
/discount - Акции и скидки
/search - Поиск товаров
/web - Веб-версия магазина

{Emoji.ADMIN} <b>Администраторские команды:</b>
/clear_state - Очистить ВСЕ состояния (только админ)
/clear_state_all - Очистить своё состояние
/sync_now - Синхронизировать с сайтом

{Emoji.LINK} <b>Быстрые ссылки:</b>
• Нажмите на кнопки в меню
• Введите название товара для поиска
• Введите промокод (например: WELCOME15)
• Обратитесь к поддержке: {Config.SUPPORT_USERNAME}
"""
            
            self.bot.send_message(
                chat_id,
                help_text,
                parse_mode='HTML',
                reply_markup=self.create_main_keyboard(chat_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки текстового сообщения: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка. Пожалуйста, попробуйте позже."
            )
    
    def process_callback_query(self, call):
        """Обработка callback-запросов"""
        try:
            callback_data = call.data
            logger.info(f"Callback получен: {callback_data} от {call.from_user.id}")

            # Обновляем активность пользователя
            self.db.update_user_activity(call.from_user.id)

            # Обработка навигации по каталогу
            if callback_data == "show_catalog":
                self.show_catalog_categories(call)
            elif callback_data.startswith("cat_"):
                category = callback_data[4:]
                self.show_category_products(call, category)
            elif callback_data.startswith("product_"):
                product_id = int(callback_data[8:])
                self.show_product_detail(call, product_id)
            elif callback_data.startswith("page_"):
                parts = callback_data.split("_")
                if len(parts) >= 3:
                    category = parts[1]
                    page = int(parts[2])
                    self.show_category_products(call, category, page)

            # Обработка добавления товаров
            elif callback_data.startswith("add_to_cart_"):
                product_id = int(callback_data[12:])
                self.add_to_cart_from_callback(call, product_id)
            elif callback_data.startswith("add_favorite_"):
                product_id = int(callback_data[13:])
                self.add_to_favorites_from_callback(call, product_id)
            elif callback_data.startswith("remove_favorite_"):
                product_id = int(callback_data[16:])
                self.remove_from_favorites_from_callback(call, product_id)

            # Обработка корзины
            elif callback_data.startswith("cart_"):
                if callback_data == "cart_view":
                    self.show_cart(call)
                elif callback_data == "cart_clear":
                    self.clear_cart(call)
                elif callback_data.startswith("cart_update_"):
                    parts = callback_data.split("_")
                    if len(parts) >= 4:
                        cart_item_id = int(parts[2])
                        quantity = int(parts[3])
                        self.update_cart_item(call, cart_item_id, quantity)
                elif callback_data.startswith("cart_remove_"):
                    cart_item_id = int(callback_data[12:])
                    self.remove_from_cart(call, cart_item_id)
                elif callback_data == "cart_checkout":
                    self.start_checkout(call)

            # Обработка заказов
            elif callback_data.startswith("order_"):
                if callback_data == "order_list":
                    self.show_orders(call)
                elif callback_data.startswith("order_detail_"):
                    order_id = int(callback_data[13:])
                    self.show_order_detail(call, order_id)

            # Обработка веб-ссылок
            elif callback_data.startswith("web_"):
                if callback_data == "web_catalog":
                    self.open_web_catalog(call.message)
                elif callback_data == "web_cart":
                    self.open_web_cart(call.message)
                elif callback_data == "web_orders":
                    self.open_web_orders(call.message)
                elif callback_data == "web_profile":
                    self.open_web_profile(call.message)
                elif callback_data.startswith("web_catalog_"):
                    category = callback_data[12:]
                    self.open_web_catalog(call.message, category)
                elif callback_data.startswith("web_product_"):
                    product_id = callback_data[12:]
                    self.open_web_product(call.message, product_id)

            # Обработка админ-функций
            elif callback_data.startswith("admin_"):
                if callback_data == "admin_stats":
                    self.show_stats(call.message)
                elif callback_data == "admin_users":
                    self.show_users_list(call.message)
                elif callback_data == "admin_panel":
                    self.show_admin_panel(call.message)
                elif callback_data == "admin_database":
                    self.show_database_info(call.message)
                elif callback_data == "admin_settings":
                    self.show_admin_settings(call.message)
            
            # Обработка рассылки
            elif callback_data.startswith("broadcast_"):
                if callback_data == "broadcast_start":
                    self.start_broadcast(call.message)
                elif callback_data == "broadcast_send_all":
                    self.send_broadcast_to_users(call.from_user.id, {}, 'all')
                elif callback_data == "broadcast_send_vip":
                    self.send_broadcast_to_users(call.from_user.id, {}, 'vip')
                elif callback_data == "broadcast_cancel":
                    self.db.clear_user_state(call.from_user.id)
                    self.bot.edit_message_text(
                        f"{Emoji.CANCEL} Создание рассылки отменено.",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode='HTML'
                    )
            
            # Обработка статистики
            elif callback_data.startswith("stats_"):
                if callback_data == "stats_refresh":
                    self.show_stats(call.message)
            
            # Обработка промокодов
            elif callback_data.startswith("promo_"):
                if callback_data == "promo_apply":
                    self.start_promo_code_input(call.message)
            
            # Обработка реферального кода
            elif callback_data == "show_referral":
                self.show_referral_info(call.message)
            
            # Обработка избранного
            elif callback_data == "show_favorites":
                self.show_favorites(call.message)
            
            # Пустой callback (noop)
            elif callback_data == "noop":
                pass
            else:
                logger.warning(f"Неизвестный callback: {callback_data}")
            
            # Подтверждение получения callback
            self.bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
            try:
                self.bot.answer_callback_query(
                    call.id,
                    "Произошла ошибка при обработке запроса",
                    show_alert=True
                )
            except:
                pass
    
    def create_main_keyboard(self, chat_id):
        """Создание основной клавиатуры меню"""
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            row_width=2,
            one_time_keyboard=False
        )
        
        # Первый ряд: Каталог и Поиск
        markup.row(
            types.KeyboardButton(f"{Emoji.DRESS} Каталог"),
            types.KeyboardButton(f"{Emoji.SEARCH} Поиск")
        )
        
        # Второй ряд: Корзина и Избранное
        markup.row(
            types.KeyboardButton(f"{Emoji.CART} Корзина"),
            types.KeyboardButton(f"{Emoji.HEART} Избранное")
        )
        
        # Третий ряд: Заказы и Профиль
        markup.row(
            types.KeyboardButton(f"{Emoji.ORDER} Заказы"),
            types.KeyboardButton(f"{Emoji.USER} Профиль")
        )
        
        # Четвертый ряд: Поддержка и Скидки
        markup.row(
            types.KeyboardButton(f"{Emoji.SUPPORT} Поддержка"),
            types.KeyboardButton(f"{Emoji.SALE} Скидки")
        )
        
        # Пятый ряд: Веб-версия и Главная
        markup.row(
            types.KeyboardButton(f"{Emoji.WEBSITE} Веб-версия"),
            types.KeyboardButton(f"{Emoji.HOME} Главная")
        )
        
        # Шестой ряд: Админ-панель (только для администраторов)
        if chat_id in Config.ADMIN_IDS:
            markup.row(types.KeyboardButton(f"{Emoji.ADMIN} Админ-панель"))
        
        return markup
    
    def format_price(self, price):
        """Форматирование цены"""
        return f"{int(price):,}".replace(",", " ")
    
    def show_catalog_categories(self, message_or_call):
        """Показать категории каталога"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Получаем категории из базы данных
            categories = self.db.get_categories()
            
            if not categories:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.INFO} Каталог временно пуст. Пожалуйста, попробуйте позже.",
                    parse_mode='HTML'
                )
                return
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            # Добавляем кнопки категорий
            for category in categories:
                emoji = self.get_category_emoji(category)
                markup.add(types.InlineKeyboardButton(
                    f"{emoji} {category}",
                    callback_data=f"cat_{category}"
                ))
            
            # Добавляем кнопку "Все товары"
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.VIEW} Все товары",
                callback_data="cat_all"
            ))
            
            # Кнопка для открытия в веб-приложении
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Открыть в веб-версии",
                web_app=types.WebAppInfo(url=f"{self.web_app_url}/catalog")
            ))
            
            text = f"""
{Emoji.DRESS} <b>КАТАЛОГ {Config.SHOP_NAME}</b>

{Emoji.FILTER} <b>Выберите категорию:</b>

{Emoji.INFO} В каждой категории представлены эксклюзивные коллекции от ведущих мировых дизайнеров.

{Emoji.NEXT} Для просмотра товаров выберите категорию или откройте полную версию каталога в веб-приложении:
"""
            
            if is_callback:
                self.bot.edit_message_text(
                    text,
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_catalog_categories')
            
        except Exception as e:
            logger.error(f"Ошибка показа категорий каталога: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке категорий. Пожалуйста, попробуйте позже."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def get_category_emoji(self, category):
        """Получение эмодзи для категории"""
        emoji_map = {
            'Платья': Emoji.DRESS,
            'Костюмы': Emoji.SUIT,
            'Блузы': Emoji.BLAZER,
            'Брюки': Emoji.PANTS,
            'Юбки': Emoji.SKIRT,
            'Куртки': Emoji.OUTERWEAR,
            'Пальто': Emoji.OUTERWEAR,
            'Аксессуары': Emoji.ACCESSORIES,
            'Обувь': Emoji.SHOES,
            'Сумки': Emoji.BAG,
            'Украшения': Emoji.JEWELRY,
        }
        return emoji_map.get(category, Emoji.TAG)
    
    def show_category_products(self, call, category, page=1):
        """Показать товары выбранной категории"""
        try:
            products_per_page = 6
            offset = (page - 1) * products_per_page
            
            # Получаем товары из базы данных
            if category == 'all':
                products = self.db.get_products(
                    limit=products_per_page,
                    offset=offset
                )
            else:
                products = self.db.get_products(
                    category=category,
                    limit=products_per_page,
                    offset=offset
                )
            
            if not products:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} Открыть в веб-версии",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/catalog?category={category}")
                ))
                
                self.bot.edit_message_text(
                    f"{Emoji.INFO} <b>{category.upper() if category != 'all' else 'ВСЕ ТОВАРЫ'}</b>\n\n"
                    f"Товары этой категории временно отсутствуют или доступны в веб-версии магазина.\n\n"
                    f"Нажмите кнопку ниже для просмотра полного ассортимента:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                return
            
            # Отправляем товары
            for i, product in enumerate(products):
                product_text = self.format_product_message(product)
                
                markup = types.InlineKeyboardMarkup(row_width=3)
                
                # Кнопки действий
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.VIEW} Подробнее",
                        callback_data=f"product_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.HEART} В избранное",
                        callback_data=f"add_favorite_{product['id']}"
                    )
                )
                
                # Кнопка для веб-версии
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} Открыть на сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/product/{product['id']}")
                ))
                
                try:
                    if product.get('image_url'):
                        if i == 0:
                            # Для первого товара редактируем существующее сообщение
                            try:
                                self.bot.edit_message_media(
                                    types.InputMediaPhoto(
                                        product['image_url'],
                                        caption=product_text,
                                        parse_mode='HTML'
                                    ),
                                    call.message.chat.id,
                                    call.message.message_id,
                                    reply_markup=markup
                                )
                                continue
                            except:
                                pass
                        
                        self.bot.send_photo(
                            call.message.chat.id,
                            product['image_url'],
                            caption=product_text,
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                    else:
                        if i == 0:
                            self.bot.edit_message_text(
                                product_text,
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=markup,
                                parse_mode='HTML'
                            )
                        else:
                            self.bot.send_message(
                                call.message.chat.id,
                                product_text,
                                reply_markup=markup,
                                parse_mode='HTML'
                            )
                except Exception as e:
                    logger.error(f"Ошибка отправки товара {product['id']}: {e}")
                    self.bot.send_message(
                        call.message.chat.id,
                        product_text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
            
            # Создаем пагинацию
            total_count = len(products)
            if total_count == products_per_page:
                # Если показали полную страницу, возможно есть еще
                markup = types.InlineKeyboardMarkup(row_width=2)
                
                if page > 1:
                    markup.add(types.InlineKeyboardButton(
                        f"{Emoji.BACK} Назад",
                        callback_data=f"page_{category}_{page-1}"
                    ))
                
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.NEXT} Еще товары",
                    callback_data=f"page_{category}_{page+1}"
                ))
                
                self.bot.send_message(
                    call.message.chat.id,
                    f"{Emoji.INFO} Показано {len(products)} товаров. Хотите увидеть больше?",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(call.from_user.id, 'view_category', {
                'category': category,
                'page': page
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа товаров категории {category}: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка при загрузке товаров",
                show_alert=True
            )
    
    def format_product_message(self, product):
        """Форматирование сообщения о товаре"""
        # Форматируем цену
        price_text = f"{self.format_price(product['price'])} {Config.CURRENCY}"
        
        if product.get('old_price') and product['old_price'] > product['price']:
            discount = int(((product['old_price'] - product['price']) / product['old_price']) * 100)
            old_price_formatted = self.format_price(product['old_price'])
            new_price_formatted = self.format_price(product['price'])
            price_text = f"<s>{old_price_formatted} {Config.CURRENCY}</s>\n{new_price_formatted} {Config.CURRENCY}\n{Emoji.SALE} <b>-{discount}%</b>"
        
        # Форматируем бейджи
        badges = []
        if product.get('is_new'):
            badges.append(f"{Emoji.NEW} Новинка")
        if product.get('is_exclusive'):
            badges.append(f"{Emoji.EXCLUSIVE} Эксклюзив")
        if product.get('is_hit'):
            badges.append(f"{Emoji.FIRE} Хит продаж")
        if product.get('is_limited'):
            badges.append(f"{Emoji.GEM} Лимитированная серия")
        
        badges_text = " • ".join(badges) if badges else ""
        
        # Форматируем наличие
        stock = product.get('stock', 0)
        if stock > 10:
            stock_text = f"{Emoji.CHECK} В наличии: {stock} шт."
        elif stock > 0:
            stock_text = f"{Emoji.WARNING} Осталось мало: {stock} шт."
        else:
            stock_text = f"{Emoji.CANCEL} Нет в наличии"
        
        # Собираем сообщение
        message = f"""
{Emoji.TAG} <b>{product['name']}</b>

{Emoji.MONEY} <b>Цена:</b> {price_text}
{Emoji.CATEGORY} <b>Категория:</b> {product['category']}
{Emoji.ARTICLE} <b>Артикул:</b> {product['article']}
{Emoji.SHIELD} <b>Бренд:</b> {product.get('brand', 'VOGUE ÉLITE')}

{badges_text}

{stock_text}

{Emoji.INFO} <b>Описание:</b>
{product.get('description', 'Эксклюзивный товар премиум-класса')}
"""
        
        return message.strip()
    
    def show_product_detail(self, call, product_id):
        """Показать детальную информацию о товаре"""
        try:
            product = self.db.get_product(product_id)
            
            if not product:
                self.bot.answer_callback_query(
                    call.id,
                    "Товар не найден",
                    show_alert=True
                )
                return
            
            # Добавляем в историю просмотров
            self.db.add_to_view_history(call.from_user.id, product_id)
            
            # Форматируем сообщение
            product_text = self.format_product_detail(product)
            
            markup = types.InlineKeyboardMarkup(row_width=3)
            
            # Основные кнопки
            markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.CART} В корзину",
                    callback_data=f"add_to_cart_{product_id}"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.HEART} В избранное",
                    callback_data=f"add_favorite_{product_id}"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} На сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/product/{product_id}")
                )
            )
            
            # Кнопка назад
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад в каталог",
                callback_data="show_catalog"
            ))
            
            # Отправляем фото, если есть
            if product.get('image_url'):
                try:
                    self.bot.edit_message_media(
                        types.InputMediaPhoto(
                            product['image_url'],
                            caption=product_text,
                            parse_mode='HTML'
                        ),
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup
                    )
                except:
                    self.bot.edit_message_text(
                        product_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
            else:
                self.bot.edit_message_text(
                    product_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(call.from_user.id, 'view_product', {
                'product_id': product_id,
                'product_name': product['name']
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа деталей товара {product_id}: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка при загрузке товара",
                show_alert=True
            )
    
    def format_product_detail(self, product):
        """Форматирование детального описания товара"""
        # Форматируем цену
        price_text = f"{self.format_price(product['price'])} {Config.CURRENCY}"
        
        if product.get('old_price') and product['old_price'] > product['price']:
            discount = int(((product['old_price'] - product['price']) / product['old_price']) * 100)
            old_price_formatted = self.format_price(product['old_price'])
            new_price_formatted = self.format_price(product['price'])
            price_text = f"<s>{old_price_formatted} {Config.CURRENCY}</s>\n{new_price_formatted} {Config.CURRENCY}\n{Emoji.SALE} <b>-{discount}%</b>"
        
        # Форматируем бейджи
        badges = []
        if product.get('is_new'):
            badges.append(f"{Emoji.NEW} Новинка")
        if product.get('is_exclusive'):
            badges.append(f"{Emoji.EXCLUSIVE} Эксклюзив")
        if product.get('is_hit'):
            badges.append(f"{Emoji.FIRE} Хит продаж")
        if product.get('is_limited'):
            badges.append(f"{Emoji.GEM} Лимитированная серия")
        
        badges_text = " • ".join(badges) if badges else ""
        
        # Форматируем наличие
        stock = product.get('stock', 0)
        if stock > 10:
            stock_text = f"{Emoji.CHECK} В наличии: {stock} шт."
        elif stock > 0:
            stock_text = f"{Emoji.WARNING} Осталось мало: {stock} шт."
        else:
            stock_text = f"{Emoji.CANCEL} Нет в наличии"
        
        # Детали
        details = []
        if product.get('material'):
            details.append(f"{Emoji.TAG} <b>Материал:</b> {product['material']}")
        if product.get('color'):
            details.append(f"{Emoji.COLOR} <b>Цвета:</b> {product['color']}")
        if product.get('size'):
            details.append(f"{Emoji.SIZE} <b>Размеры:</b> {product['size']}")
        if product.get('country'):
            details.append(f"{Emoji.GLOBE} <b>Страна:</b> {product['country']}")
        if product.get('season'):
            details.append(f"{Emoji.CALENDAR} <b>Сезон:</b> {product.get('season', '')}")
        details_text = "\n".join(details) if details else ""
        
        # Описание
        description = product.get('detailed_description') or product.get('description') or 'Эксклюзивный товар премиум-класса'
        
        # Собираем полное сообщение
        message = f"""
{Emoji.TAG} <b>{product['name']}</b>

{Emoji.MONEY} <b>Цена:</b> {price_text}
{Emoji.CATEGORY} <b>Категория:</b> {product['category']}
{Emoji.ARTICLE} <b>Артикул:</b> {product['article']}
{Emoji.SHIELD} <b>Бренд:</b> {product.get('brand', 'VOGUE ÉLITE')}

{badges_text}

{stock_text}

{details_text}

{Emoji.INFO} <b>Описание:</b>
{description}
"""
        
        # Добавляем инструкции по уходу, если есть
        if product.get('care_instructions'):
            message += f"\n{Emoji.WARNING} <b>Уход:</b>\n{product['care_instructions']}"
        
        return message.strip()
    
    def add_to_cart_from_callback(self, call, product_id):
        """Добавление товара в корзину из callback"""
        try:
            user_id = call.from_user.id
            
            # Добавляем товар в корзину
            success = self.db.add_to_cart(user_id, product_id)
            
            if success:
                # Получаем данные товара
                product = self.db.get_product(product_id)
                
                # Получаем актуальные данные корзины
                cart_total = self.db.get_cart_total(user_id)
                
                # Отправляем подтверждение
                self.bot.answer_callback_query(
                    call.id,
                    f"Товар добавлен в корзину! Всего товаров: {cart_total['item_count']}",
                    show_alert=False
                )
                
                # Обновляем сообщение с товаром
                product_text = self.format_product_detail(product)
                markup = types.InlineKeyboardMarkup(row_width=3)
                
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} ✓ В корзине",
                        callback_data="noop"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.HEART} В избранное",
                        callback_data=f"add_favorite_{product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.WEBSITE} На сайте",
                        web_app=types.WebAppInfo(url=f"{self.web_app_url}/product/{product_id}")
                    )
                )
                
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.BACK} Назад в каталог",
                    callback_data="show_catalog"
                ))
                
                try:
                    self.bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup
                    )
                except:
                    pass
                
                # Логируем действие
                self.db.log_user_action(user_id, 'add_to_cart', {
                    'product_id': product_id,
                    'product_name': product['name'],
                    'price': product['price']
                })
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Не удалось добавить товар в корзину. Возможно, товара нет в наличии.",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка добавления в корзину из callback: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def add_to_favorites_from_callback(self, call, product_id):
        """Добавление товара в избранное из callback"""
        try:
            user_id = call.from_user.id
            
            # Добавляем товар в избранное
            success = self.db.add_to_favorites(user_id, product_id)
            
            if success:
                self.bot.answer_callback_query(
                    call.id,
                    "Товар добавлен в избранное!",
                    show_alert=False
                )
                
                # Обновляем кнопку
                markup = types.InlineKeyboardMarkup(row_width=3)
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.HEART} ✓ В избранном",
                        callback_data=f"remove_favorite_{product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.WEBSITE} На сайте",
                        web_app=types.WebAppInfo(url=f"{self.web_app_url}/product/{product_id}")
                    )
                )
                
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.BACK} Назад в каталог",
                    callback_data="show_catalog"
                ))
                
                try:
                    self.bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup
                    )
                except:
                    pass
                
                # Логируем действие
                self.db.log_user_action(user_id, 'add_to_favorites', {
                    'product_id': product_id
                })
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Не удалось добавить товар в избранное",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка добавления в избранное из callback: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def remove_from_favorites_from_callback(self, call, product_id):
        """Удаление товара из избранного из callback"""
        try:
            user_id = call.from_user.id
            
            # Удаляем товар из избранного
            success = self.db.remove_from_favorites(user_id, product_id)
            
            if success:
                self.bot.answer_callback_query(
                    call.id,
                    "Товар удален из избранного",
                    show_alert=False
                )
                
                # Обновляем кнопку
                markup = types.InlineKeyboardMarkup(row_width=3)
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.HEART} В избранное",
                        callback_data=f"add_favorite_{product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.WEBSITE} На сайте",
                        web_app=types.WebAppInfo(url=f"{self.web_app_url}/product/{product_id}")
                    )
                )
                
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.BACK} Назад в каталог",
                    callback_data="show_catalog"
                ))
                
                try:
                    self.bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup
                    )
                except:
                    pass
                
                # Логируем действие
                self.db.log_user_action(user_id, 'remove_from_favorites', {
                    'product_id': product_id
                })
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Товар не найден в избранном",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка удаления из избранного из callback: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def show_cart(self, message_or_call):
        """Показать корзину пользователя"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False

            # Очищаем состояние пользователя при просмотре корзины
            self.db.clear_user_state(user_id)

            # Получаем корзину пользователя
            cart_items = self.db.get_cart(user_id)
            cart_total = self.db.get_cart_total(user_id)

            if not cart_items:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Перейти в каталог",
                    callback_data="show_catalog"
                ))
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} Открыть корзину на сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/cart")
                ))
                
                text = f"""\
{Emoji.CART} <b>ВАША КОРЗИНА</b>

{Emoji.INFO} Ваша корзина пуста.

{Emoji.NEXT} Добавьте товары из каталога или откройте корзину в веб-версии магазина:"""

                if is_callback:
                    self.bot.edit_message_text(
                        text,
                        message.chat.id,
                        message.message_id,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        text,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
                return
                
            # Форматируем список товаров в корзине
            cart_text = f"""\
{Emoji.CART} <b>ВАША КОРЗИНА</b>

{Emoji.INFO} <b>Товары в корзине:</b>
"""
            
            for i, item in enumerate(cart_items, 1):
                item_total = self.format_price(item['total'])
                cart_text += f"\n{i}. <b>{item['name']}</b>"
                cart_text += f"\n   Количество: {item['quantity']} шт."
                cart_text += f"\n   Цена: {self.format_price(item['price'])} {Config.CURRENCY}"
                cart_text += f"\n   Сумма: {item_total} {Config.CURRENCY}\n"
            
            # Добавляем итоги
            subtotal = self.format_price(cart_total['subtotal'])
            delivery = self.format_price(cart_total['delivery_cost'])
            total = self.format_price(cart_total['total'])
            
            cart_text += f"""\

{Emoji.MONEY} <b>Промежуточный итог:</b> {subtotal} {Config.CURRENCY}
"""
            
            if cart_total['delivery_cost'] == 0:
                cart_text += f"{Emoji.DELIVERY} <b>Доставка:</b> {Emoji.CHECK} Бесплатно\n"
            else:
                cart_text += f"{Emoji.DELIVERY} <b>Доставка:</b> {delivery} {Config.CURRENCY}\n"
                if cart_total['needs_for_free_delivery'] > 0:
                    needs = self.format_price(cart_total['needs_for_free_delivery'])
                    cart_text += f"{Emoji.INFO} До бесплатной доставки: {needs} {Config.CURRENCY}\n"
            
            cart_text += f"\n{Emoji.MONEY} <b>Итого к оплате:</b> {total} {Config.CURRENCY}\n"
            
            # Создаем клавиатуру для управления корзиной
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Продолжить покупки",
                    callback_data="show_catalog"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.CARD} Оформить заказ",
                    callback_data="cart_checkout"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.TRASH} Очистить корзину",
                    callback_data="cart_clear"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} На сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/cart")
                )
            )
            
            if is_callback:
                self.bot.edit_message_text(
                    cart_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    cart_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            
            # Для каждого товара добавляем отдельное сообщение с управлением
            for item in cart_items:
                item_markup = types.InlineKeyboardMarkup(row_width=3)
                
                # Кнопки изменения количества
                if item['quantity'] > 1:
                    item_markup.add(
                        types.InlineKeyboardButton(
                            f"{Emoji.MINUS}",
                            callback_data=f"cart_update_{item['id']}_{item['quantity']-1}"
                        ),
                        types.InlineKeyboardButton(
                            f"{item['quantity']} шт.",
                            callback_data="noop"
                        ),
                        types.InlineKeyboardButton(
                            f"{Emoji.PLUS}",
                            callback_data=f"cart_update_{item['id']}_{item['quantity']+1}"
                        )
                    )
                else:
                    item_markup.add(
                        types.InlineKeyboardButton(
                            f"{item['quantity']} шт.",
                            callback_data="noop"
                        ),
                        types.InlineKeyboardButton(
                            f"{Emoji.PLUS}",
                            callback_data=f"cart_update_{item['id']}_{item['quantity']+1}"
                        )
                    )
                
                item_markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.CANCEL} Удалить",
                        callback_data=f"cart_remove_{item['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.VIEW} Подробнее",
                        callback_data=f"product_{item['product_id']}"
                    )
                )
                
                # Отправляем каждый товар отдельным сообщением
                item_text = f"<b>{item['name']}</b>\n"
                item_text += f"Артикул: {item['article']}\n"
                item_text += f"Цена: {self.format_price(item['price'])} {Config.CURRENCY}\n"
                item_text += f"Количество: {item['quantity']} шт.\n"
                item_text += f"Сумма: {self.format_price(item['total'])} {Config.CURRENCY}"
                
                if item.get('image_url'):
                    try:
                        self.bot.send_photo(
                            message.chat.id,
                            item['image_url'],
                            caption=item_text,
                            reply_markup=item_markup,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки фото товара: {e}")
                        self.bot.send_message(
                            message.chat.id,
                            item_text,
                            reply_markup=item_markup,
                            parse_mode="HTML"
                        )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        item_text,
                        reply_markup=item_markup,
                        parse_mode="HTML"
                    )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_cart', {
                'item_count': len(cart_items),
                'total': cart_total['total']
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа корзины: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке корзины. Пожалуйста, попробуйте позже."
            
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                is_callback = True
            else:
                message = message_or_call
                is_callback = False
                
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Не удалось отредактировать сообщение: {e}")
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode="HTML")
    
    def update_cart_item(self, call, cart_item_id, quantity):
        """Обновление количества товара в корзине"""
        try:
            user_id = call.from_user.id
            
            # Обновляем количество
            success = self.db.update_cart_item(cart_item_id, quantity, user_id)
            
            if success:
                if quantity <= 0:
                    self.bot.answer_callback_query(
                        call.id,
                        "Товар удален из корзины",
                        show_alert=False
                    )
                    
                    # Удаляем сообщение с товаром
                    try:
                        self.bot.delete_message(call.message.chat.id, call.message.message_id)
                    except:
                        pass
                    
                    # Показываем обновленную корзину
                    self.show_cart(call)
                else:
                    self.bot.answer_callback_query(
                        call.id,
                        f"Количество обновлено: {quantity} шт.",
                        show_alert=False
                    )
                    
                    # Обновляем сообщение с товаром
                    cart_total = self.db.get_cart_total(user_id)
                    
                    # Обновляем текст в сообщении
                    if call.message.caption:
                        # Это сообщение с фото
                        lines = call.message.caption.split('\n')
                        if len(lines) >= 4:
                            lines[2] = f"Количество: {quantity} шт."
                            price = float(lines[1].split(': ')[1].split(' ')[0].replace(' ', ''))
                            lines[3] = f"Сумма: {self.format_price(price * quantity)} {Config.CURRENCY}"
                            new_caption = '\n'.join(lines)
                            
                            try:
                                self.bot.edit_message_caption(
                                    caption=new_caption,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=call.message.reply_markup,
                                    parse_mode='HTML'
                                )
                            except:
                                pass
                    else:
                        # Это текстовое сообщение
                        lines = call.message.text.split('\n')
                        if len(lines) >= 4:
                            lines[2] = f"Количество: {quantity} шт."
                            price = float(lines[1].split(': ')[1].split(' ')[0].replace(' ', ''))
                            lines[3] = f"Сумма: {self.format_price(price * quantity)} {Config.CURRENCY}"
                            new_text = '\n'.join(lines)
                            
                            try:
                                self.bot.edit_message_text(
                                    new_text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=call.message.reply_markup,
                                    parse_mode='HTML'
                                )
                            except:
                                pass
                    
                    # Обновляем кнопки
                    item_markup = types.InlineKeyboardMarkup(row_width=3)
                    
                    if quantity > 1:
                        item_markup.add(
                            types.InlineKeyboardButton(
                                f"{Emoji.MINUS}",
                                callback_data=f"cart_update_{cart_item_id}_{quantity-1}"
                            ),
                            types.InlineKeyboardButton(
                                f"{quantity} шт.",
                                callback_data="noop"
                            ),
                            types.InlineKeyboardButton(
                                f"{Emoji.PLUS}",
                                callback_data=f"cart_update_{cart_item_id}_{quantity+1}"
                            )
                        )
                    else:
                        item_markup.add(
                            types.InlineKeyboardButton(
                                f"{quantity} шт.",
                                callback_data="noop"
                            ),
                            types.InlineKeyboardButton(
                                f"{Emoji.PLUS}",
                                callback_data=f"cart_update_{cart_item_id}_{quantity+1}"
                            )
                        )
                    
                    item_markup.add(
                        types.InlineKeyboardButton(
                            f"{Emoji.CANCEL} Удалить",
                            callback_data=f"cart_remove_{cart_item_id}"
                        ),
                        types.InlineKeyboardButton(
                            f"{Emoji.VIEW} Подробнее",
                            callback_data=f"product_{cart_item_id}"
                        )
                    )
                    
                    try:
                        self.bot.edit_message_reply_markup(
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=item_markup
                        )
                    except:
                        pass
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Не удалось обновить количество. Возможно, товара нет в наличии.",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка обновления корзины: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def remove_from_cart(self, call, cart_item_id):
        """Удаление товара из корзины"""
        try:
            user_id = call.from_user.id
            
            # Удаляем товар из корзины
            success = self.db.remove_from_cart(cart_item_id, user_id)
            
            if success:
                self.bot.answer_callback_query(
                    call.id,
                    "Товар удален из корзины",
                    show_alert=False
                )
                
                # Удаляем сообщение с товаром
                try:
                    self.bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                
                # Показываем обновленную корзину
                self.show_cart(call)
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Не удалось удалить товар из корзины",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка удаления из корзины: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def clear_cart(self, call):
        """Очистка корзины"""
        try:
            user_id = call.from_user.id
            
            # Очищаем корзину
            success = self.db.clear_cart(user_id)
            
            if success:
                self.bot.answer_callback_query(
                    call.id,
                    "Корзина очищена",
                    show_alert=False
                )
                
                # Обновляем сообщение
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Перейти в каталог",
                    callback_data="show_catalog"
                ))
                
                self.bot.edit_message_text(
                    f"{Emoji.CART} <b>ВАША КОРЗИНА</b>\n\n"
                    f"{Emoji.INFO} Ваша корзина пуста.\n\n"
                    f"{Emoji.NEXT} Добавьте товары из каталога:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                
                # Логируем действие
                self.db.log_user_action(user_id, 'clear_cart')
            else:
                self.bot.answer_callback_query(
                    call.id,
                    "Не удалось очистить корзину",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Ошибка очистки корзины: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def start_checkout(self, call):
        """Начало оформления заказа"""
        try:
            user_id = call.from_user.id
            
            # Получаем данные корзины
            cart_items = self.db.get_cart(user_id)
            cart_total = self.db.get_cart_total(user_id)
            
            if not cart_items:
                self.bot.answer_callback_query(
                    call.id,
                    "Ваша корзина пуста",
                    show_alert=True
                )
                return
            
            # Проверяем наличие товаров
            unavailable_items = []
            for item in cart_items:
                if item['stock'] < item['quantity']:
                    unavailable_items.append(item['name'])
            
            if unavailable_items:
                items_list = "\n".join([f"• {name}" for name in unavailable_items[:3]])
                if len(unavailable_items) > 3:
                    items_list += f"\n• ... и еще {len(unavailable_items) - 3} товаров"
                
                self.bot.answer_callback_query(
                    call.id,
                    f"Некоторые товары закончились:\n{items_list}",
                    show_alert=True
                )
                return
            
            # Запрашиваем адрес доставки
            self.db.save_user_state(
                user_id,
                'waiting_order_address',
                {
                    'cart_total': cart_total,
                    'cart_items': [
                        {
                            'id': item['id'],
                            'name': item['name'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        } for item in cart_items
                    ]
                }
            )
            
            # Спрашиваем адрес
            delivery_text = "Бесплатно" if cart_total['delivery_cost'] == 0 else f"{self.format_price(cart_total['delivery_cost'])} {Config.CURRENCY}"
            
            self.bot.edit_message_text(
                f"{Emoji.ORDER} <b>ОФОРМЛЕНИЕ ЗАКАЗА - ШАГ 1/3</b>\n\n"
                f"{Emoji.MONEY} <b>Сумма заказа:</b> {self.format_price(cart_total['total'])} {Config.CURRENCY}\n"
                f"{Emoji.DELIVERY} <b>Доставка:</b> {delivery_text}\n"
                f"{Emoji.PACKAGE} <b>Товаров:</b> {cart_total['item_count']} шт.\n\n"
                f"{Emoji.HOME} <b>Введите адрес доставки:</b>\n\n"
                f"{Emoji.INFO} <b>Пример:</b> г. Москва, ул. Тверская, д. 1, кв. 10\n\n"
                f"{Emoji.CANCEL} Для отмены отправьте /cancel",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка начала оформления заказа: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка",
                show_alert=True
            )
    
    def process_order_address(self, message, state_data):
        """Обработка адреса доставки"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Оформление заказа отменено.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            address = message.text.strip()
            
            if len(address) < 10:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Адрес слишком короткий. Пожалуйста, введите полный адрес."
                )
                return
            
            # Сохраняем адрес и переходим к следующему шагу
            state_data['address'] = address
            self.db.save_user_state(
                user_id,
                'waiting_order_notes',
                state_data
            )
            
            # Запрашиваем комментарий к заказу
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.ORDER} <b>ОФОРМЛЕНИЕ ЗАКАЗА - ШАГ 2/3</b>\n\n"
                f"{Emoji.HOME} <b>Адрес доставки:</b>\n{address}\n\n"
                f"{Emoji.MESSAGE} <b>Введите комментарий к заказу (необязательно):</b>\n\n"
                f"{Emoji.INFO} <b>Примеры:</b>\n"
                f"• Позвоните за час до доставки\n"
                f"• Оставить у двери\n"
                f"• Нужна подарочная упаковка\n\n"
                f"{Emoji.NEXT} Если комментарий не нужен, отправьте \"-\"\n"
                f"{Emoji.CANCEL} Для отмены отправьте /cancel",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки адреса заказа: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка. Пожалуйста, попробуйте снова."
            )
    
    def process_order_notes(self, message, state_data):
        """Обработка комментария к заказу"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Оформление заказа отменено.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            notes = message.text.strip() if message.text.strip() != '-' else ''
            
            # Создаем заказ
            order_data = {
                'address': state_data.get('address', ''),
                'notes': notes,
                'delivery_type': 'courier',
                'payment_method': 'card'
            }
            
            # Проверяем промокод
            promo_code = state_data.get('promo_code')
            if promo_code:
                order_data['promo_code'] = promo_code
            
            result = self.db.create_order(user_id, order_data)
            
            if result['success']:
                # Очищаем состояние
                self.db.clear_user_state(user_id)
                
                # Отправляем подтверждение
                order = result['order']
                order_number = result['order_number']
                
                order_text = f"""
{Emoji.CHECK} <b>ЗАКАЗ УСПЕШНО ОФОРМЛЕН!</b>

{Emoji.ORDER} <b>Номер заказа:</b> {order_number}
{Emoji.MONEY} <b>Сумма:</b> {self.format_price(order['final_amount'])} {Config.CURRENCY}
{Emoji.HOME} <b>Адрес доставки:</b> {order['delivery_address']}
{Emoji.CLOCK} <b>Дата:</b> {datetime.fromisoformat(order['created_at']).strftime('%d.%m.%Y %H:%M')}
{Emoji.SHIELD} <b>Статус:</b> Новый

{Emoji.INFO} <b>Детали заказа:</b>
"""
                
                items = json.loads(order['items_json'])
                for i, item in enumerate(items, 1):
                    order_text += f"\n{i}. {item['name']}"
                    order_text += f"\n   Количество: {item['quantity']} шт."
                    order_text += f"\n   Цена: {self.format_price(item['price'])} {Config.CURRENCY}"
                    order_text += f"\n   Сумма: {self.format_price(item['total'])} {Config.CURRENCY}\n"
                
                delivery_text = "Бесплатно" if order['delivery_cost'] == 0 else f"{self.format_price(order['delivery_cost'])} {Config.CURRENCY}"
                order_text += f"""
{Emoji.DELIVERY} <b>Доставка:</b> {delivery_text}
"""
                
                if order.get('promo_code'):
                    order_text += f"{Emoji.COUPON} <b>Промокод:</b> {order['promo_code']}\n"
                    if order['discount_amount'] > 0:
                        order_text += f"{Emoji.SALE} <b>Скидка:</b> {self.format_price(order['discount_amount'])} {Config.CURRENCY}\n"
                
                order_text += f"\n{Emoji.MONEY} <b>Итого к оплате:</b> {self.format_price(order['final_amount'])} {Config.CURRENCY}\n\n"
                
                if notes:
                    order_text += f"{Emoji.MESSAGE} <b>Комментарий:</b> {notes}\n\n"
                
                order_text += f"""
{Emoji.INFO} <b>Что дальше?</b>
1. Наш менеджер свяжется с вами для подтверждения заказа
2. После подтверждения вы получите счет на оплату
3. После оплаты товар будет отправлен вам

{Emoji.WEBSITE} <b>Отслеживать статус заказа можно:</b>
• В разделе "Заказы" в боте
• На сайте: {self.web_app_url}/orders
• Через поддержку: {Config.SUPPORT_USERNAME}
"""
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.ORDER} Мои заказы",
                    callback_data="order_list"
                ))
                
                self.bot.send_message(
                    message.chat.id,
                    order_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                
                # Обновляем меню
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.HOME} Возвращаю вас в главное меню:",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                
                # Логируем действие
                self.db.log_user_action(user_id, 'order_completed', {
                    'order_number': order_number,
                    'amount': order['final_amount']
                })
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} <b>Ошибка оформления заказа:</b>\n{result['message']}\n\n"
                    f"Пожалуйста, попробуйте снова.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки комментария заказа: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже."
            )
    
    def show_orders(self, message_or_call):
        """Показать историю заказов пользователя"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Получаем заказы пользователя
            orders = self.db.get_user_orders(user_id)
            
            if not orders:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Перейти в каталог",
                    callback_data="show_catalog"
                ))
                
                text = f"""
{Emoji.ORDER} <b>ВАША ИСТОРИЯ ЗАКАЗОВ</b>

{Emoji.INFO} У вас пока нет оформленных заказов.

{Emoji.NEXT} Сделайте первый заказ из каталога товаров:
"""
                
                if is_callback:
                    self.bot.edit_message_text(
                        text,
                        message.chat.id,
                        message.message_id,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                return
            
            # Показываем список заказов
            text = f"""
{Emoji.ORDER} <b>ВАША ИСТОРИЯ ЗАКАЗОВ</b>

{Emoji.INFO} У вас {len(orders)} заказов:
"""
            
            for i, order in enumerate(orders[:5], 1):
                status_emoji = self.get_status_emoji(order['status'])
                date = datetime.fromisoformat(order['created_at']).strftime('%d.%m.%Y')
                
                text += f"\n{i}. <b>Заказ #{order['order_number']}</b>"
                text += f"\n   {status_emoji} Статус: {self.get_status_text(order['status'])}"
                text += f"\n   {Emoji.CALENDAR} Дата: {date}"
                text += f"\n   {Emoji.MONEY} Сумма: {self.format_price(order['final_amount'])} {Config.CURRENCY}"
                
                # Кнопка для просмотра деталей
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.VIEW} Подробнее",
                    callback_data=f"order_detail_{order['id']}"
                ))
                
                if order.get('delivery_address'):
                    text += f"\n   {Emoji.HOME} Адрес: {order['delivery_address'][:30]}..."
                
                self.bot.send_message(
                    message.chat.id,
                    text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                text = ""  # Сбрасываем текст для следующего заказа
            
            # Если заказов больше 5, показываем только последние 5
            if len(orders) > 5:
                text += f"\n{Emoji.INFO} Показаны последние 5 заказов из {len(orders)}"
            
            # Основная клавиатура
            main_markup = types.InlineKeyboardMarkup(row_width=2)
            main_markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Каталог",
                    callback_data="show_catalog"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} На сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/orders")
                )
            )
            
            # Отправляем итоговое сообщение
            if is_callback:
                self.bot.edit_message_text(
                    f"{Emoji.ORDER} <b>ВАША ИСТОРИЯ ЗАКАЗОВ</b>\n\n"
                    f"{Emoji.INFO} Для просмотра деталей заказа нажмите кнопку \"Подробнее\" под каждым заказом.",
                    message.chat.id,
                    message.message_id,
                    reply_markup=main_markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.ORDER} <b>ВАША ИСТОРИЯ ЗАКАЗОВ</b>\n\n"
                    f"{Emoji.INFO} Для просмотра деталей заказа нажмите кнопку \"Подробнее\" под каждым заказом.",
                    reply_markup=main_markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_orders', {
                'order_count': len(orders)
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа истории заказов: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке истории заказов. Пожалуйста, попробуйте позже."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def get_status_emoji(self, status):
        """Получение эмодзи для статуса заказа"""
        emoji_map = {
            'new': Emoji.NEW,
            'processing': Emoji.CLOCK,
            'confirmed': Emoji.CHECK,
            'paid': Emoji.MONEY,
            'shipped': Emoji.TRUCK,
            'delivered': Emoji.CHECK,
            'cancelled': Emoji.CANCEL,
            'returned': Emoji.REFRESH
        }
        return emoji_map.get(status, Emoji.INFO)
    
    def get_status_text(self, status):
        """Получение текста для статуса заказа"""
        status_map = {
            'new': 'Новый',
            'processing': 'В обработке',
            'confirmed': 'Подтвержден',
            'paid': 'Оплачен',
            'shipped': 'Отправлен',
            'delivered': 'Доставлен',
            'cancelled': 'Отменен',
            'returned': 'Возврат'
        }
        return status_map.get(status, status)
    
    def show_order_detail(self, call, order_id):
        """Показать детали заказа"""
        try:
            user_id = call.from_user.id
            
            # Получаем заказ
            order = self.db.get_order(order_id, user_id)
            
            if not order:
                self.bot.answer_callback_query(
                    call.id,
                    "Заказ не найден",
                    show_alert=True
                )
                return
            
            # Форматируем детали заказа
            order_text = self.format_order_detail(order)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад к заказам",
                callback_data="order_list"
            ))
            
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} На сайте",
                web_app=types.WebAppInfo(url=f"{self.web_app_url}/order/{order['id']}")
            ))
            
            self.bot.edit_message_text(
                order_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_order_detail', {
                'order_id': order_id,
                'order_number': order['order_number']
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа деталей заказа {order_id}: {e}")
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка при загрузке заказа",
                show_alert=True
            )
    
    def format_order_detail(self, order):
        """Форматирование деталей заказа"""
        date = datetime.fromisoformat(order['created_at']).strftime('%d.%m.%Y %H:%M')
        status_emoji = self.get_status_emoji(order['status'])
        status_text = self.get_status_text(order['status'])
        
        text = f"""
{Emoji.ORDER} <b>ЗАКАЗ #{order['order_number']}</b>

{status_emoji} <b>Статус:</b> {status_text}
{Emoji.CALENDAR} <b>Дата заказа:</b> {date}
{Emoji.MONEY} <b>Сумма заказа:</b> {self.format_price(order['final_amount'])} {Config.CURRENCY}
{Emoji.HOME} <b>Адрес доставки:</b> {order.get('delivery_address', 'Не указан')}
{Emoji.DELIVERY} <b>Способ доставки:</b> {order.get('delivery_type', 'Курьер')}
{Emoji.CARD} <b>Способ оплаты:</b> {order.get('payment_method', 'Карта')}

{Emoji.PACKAGE} <b>Состав заказа:</b>
"""
        
        items = order.get('items', [])
        for i, item in enumerate(items, 1):
            text += f"\n{i}. <b>{item['name']}</b>"
            text += f"\n   Артикул: {item.get('article', '')}"
            text += f"\n   Количество: {item['quantity']} шт."
            text += f"\n   Цена: {self.format_price(item['price'])} {Config.CURRENCY}"
            if item.get('size'):
                text += f"\n   Размер: {item['size']}"
            if item.get('color'):
                text += f"\n   Цвет: {item['color']}"
            text += f"\n   Сумма: {self.format_price(item['total'])} {Config.CURRENCY}\n"
        
        # Итоги
        text += f"\n{Emoji.MONEY} <b>Промежуточный итог:</b> {self.format_price(order['total_amount'])} {Config.CURRENCY}\n"
        
        if order.get('promo_code'):
            text += f"{Emoji.COUPON} <b>Промокод:</b> {order['promo_code']}\n"
            if order['discount_amount'] > 0:
                text += f"{Emoji.SALE} <b>Скидка:</b> {self.format_price(order['discount_amount'])} {Config.CURRENCY}\n"
        
        delivery_text = "Бесплатно" if order['delivery_cost'] == 0 else f"{self.format_price(order['delivery_cost'])} {Config.CURRENCY}"
        text += f"{Emoji.DELIVERY} <b>Доставка:</b> {delivery_text}\n"
        
        text += f"\n{Emoji.MONEY} <b>Итого к оплате:</b> {self.format_price(order['final_amount'])} {Config.CURRENCY}\n"
        
        if order.get('customer_notes'):
            text += f"\n{Emoji.MESSAGE} <b>Комментарий:</b> {order['customer_notes']}\n"
        
        if order.get('admin_notes'):
            text += f"\n{Emoji.ADMIN} <b>Заметка администратора:</b> {order['admin_notes']}\n"
        
        # Статус оплаты
        payment_status = order.get('payment_status', 'pending')
        if payment_status == 'paid':
            text += f"\n{Emoji.MONEY} <b>Статус оплаты:</b> {Emoji.CHECK} Оплачено"
        elif payment_status == 'pending':
            text += f"\n{Emoji.MONEY} <b>Статус оплаты:</b> {Emoji.CLOCK} Ожидает оплаты"
        else:
            text += f"\n{Emoji.MONEY} <b>Статус оплаты:</b> {payment_status}"
        
        return text
    
    def show_profile(self, message_or_call):
        """Показать профиль пользователя"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Получаем данные пользователя
            user = self.db.get_user(user_id)
            stats = self.db.get_user_stats(user_id)
            
            if not user:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Профиль не найден. Пожалуйста, используйте /start",
                    parse_mode='HTML'
                )
                return
            
            # Форматируем профиль
            profile_text = self.format_profile(user, stats)
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.ORDER} Мои заказы",
                    callback_data="order_list"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.HEART} Избранное",
                    callback_data="show_favorites"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    f"{Emoji.CART} Корзина",
                    callback_data="cart_view"
                ),
                types.InlineKeyboardButton(
                    f"{Emoji.WEBSITE} На сайте",
                    web_app=types.WebAppInfo(url=f"{self.web_app_url}/profile")
                )
            )
            
            if user.get('referral_code'):
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.LINK} Реферальный код",
                    callback_data="show_referral"
                ))
            
            if is_callback:
                self.bot.edit_message_text(
                    profile_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    profile_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_profile')
            
        except Exception as e:
            logger.error(f"Ошибка показа профиля: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def format_profile(self, user, stats):
        """Форматирование профиля пользователя"""
        # Статус VIP
        if user.get('is_vip'):
            status_text = f"{Emoji.VIP} <b>VIP клиент</b>"
            benefits = f"\n{Emoji.STAR} <b>Ваши VIP-привилегии:</b>\n• Эксклюзивные скидки до 25%\n• Персональный стилист\n• Приоритетная доставка\n• Бесплатная подарочная упаковка"
        else:
            status_text = f"{Emoji.USER} <b>Стандартный клиент</b>"
            benefits = f"\n{Emoji.INFO} <b>Станьте VIP клиентом!</b>\nПри покупке на сумму от 100.000 {Config.CURRENCY} вы получаете VIP статус."
        
        # Статистика
        if stats:
            orders_text = f"{stats.get('total_orders', 0)}"
            spent_text = f"{self.format_price(stats.get('total_spent', 0))} {Config.CURRENCY}"
            cart_text = f"{stats.get('cart_items', 0)}"
            favorites_text = f"{stats.get('favorite_items', 0)}"
        else:
            orders_text = "0"
            spent_text = f"0 {Config.CURRENCY}"
            cart_text = "0"
            favorites_text = "0"
        
        # Дата регистрации
        if user.get('created_at'):
            reg_date = datetime.fromisoformat(user['created_at']).strftime('%d.%m.%Y')
        else:
            reg_date = "Неизвестно"
        
        # Реферальный код
        referral_info = ""
        if user.get('referral_code'):
            referral_info = f"\n{Emoji.LINK} <b>Реферальный код:</b> <code>{user['referral_code']}</code>"
            referral_info += f"\n{Emoji.INFO} Дайте этот код другу при регистрации, и вы оба получите бонусы!"
        
        # Собираем профиль
        text = f"""
{Emoji.USER} <b>ВАШ ПРОФИЛЬ</b>

{status_text}

{Emoji.ID} <b>Имя:</b> {user.get('first_name', 'Не указано')}
{Emoji.AT} <b>Логин:</b> @{user.get('username', 'не указан')}
{Emoji.CALENDAR} <b>Дата регистрации:</b> {reg_date}

{Emoji.STATS} <b>Статистика:</b>
{Emoji.ORDER} Заказов: {orders_text}
{Emoji.MONEY} Потрачено: {spent_text}
{Emoji.CART} В корзине: {cart_text} шт.
{Emoji.HEART} В избранном: {favorites_text} шт.

{benefits}
{referral_info}

{Emoji.NEXT} <b>Доступные действия:</b>
"""
        
        return text
    
    def show_referral_info(self, message):
        """Показать информацию о реферальном коде"""
        try:
            user = self.db.get_user(message.chat.id)
            
            if not user or not user.get('referral_code'):
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Реферальный код не найден.",
                    parse_mode='HTML'
                )
                return
            
            referral_text = f"""
{Emoji.LINK} <b>ВАШ РЕФЕРАЛЬНЫЙ КОД</b>

🎯 <b>Код:</b> <code>{user['referral_code']}</code>

{Emoji.INFO} <b>Как это работает:</b>
1. Дайте этот код другу при регистрации в боте
2. Когда друг сделает первый заказ, вы оба получите бонусы
3. Вы получите 5% от суммы его первого заказа
4. Ваш друг получит 10% скидку на первый заказ

{Emoji.GIFT} <b>Бонусы:</b>
• Вы: 5% от суммы первого заказа друга
• Друг: 10% скидка на первый заказ
• Максимальный бонус: 5.000 {Config.CURRENCY}

{Emoji.STAR} <b>Как поделиться:</b>
Просто отправьте этот код другу:
<code>{user['referral_code']}</code>

Или скопируйте сообщение ниже и отправьте:
👇👇👇
Привет! Присоединяйся к VOGUE ÉLITE - эксклюзивному бутику моды! 🛍️

Используй мой реферальный код <b>{user['referral_code']}</b> при регистрации и получи 10% скидку на первый заказ! ✨

Ссылка для регистрации: https://t.me/{(self.bot.get_me()).username}?start=ref_{user['referral_code']}
"""
            
            self.bot.send_message(
                message.chat.id,
                referral_text,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа реферальной информации: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка при загрузке информации о реферальном коде.",
                parse_mode='HTML'
            )
    
    def show_favorites(self, message_or_call):
        """Показать избранные товары"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Получаем избранные товары
            favorites = self.db.get_favorites(user_id)
            
            if not favorites:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Перейти в каталог",
                    callback_data="show_catalog"
                ))
                
                text = f"""
{Emoji.HEART} <b>ВАШЕ ИЗБРАННОЕ</b>

{Emoji.INFO} В избранном пока нет товаров.

{Emoji.NEXT} Добавьте товары в избранное из каталога:
"""
                
                if is_callback:
                    self.bot.edit_message_text(
                        text,
                        message.chat.id,
                        message.message_id,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                return
            
            # Показываем товары
            for i, product in enumerate(favorites[:10]):
                product_text = self.format_product_message(product)
                
                markup = types.InlineKeyboardMarkup(row_width=3)
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.VIEW} Подробнее",
                        callback_data=f"product_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.CANCEL} Удалить",
                        callback_data=f"remove_favorite_{product['id']}"
                    )
                )
                
                try:
                    if product.get('image_url'):
                        self.bot.send_photo(
                            message.chat.id,
                            product['image_url'],
                            caption=product_text,
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                    else:
                        self.bot.send_message(
                            message.chat.id,
                            product_text,
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки избранного товара: {e}")
            
            # Основное сообщение
            main_text = f"{Emoji.HEART} <b>ВАШЕ ИЗБРАННОЕ</b>\n\n{Emoji.INFO} Показано {min(10, len(favorites))} товаров из {len(favorites)}"
            
            if len(favorites) > 10:
                main_text += f"\n{Emoji.INFO} Показаны первые 10 товаров"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.DRESS} Каталог",
                callback_data="show_catalog"
            ))
            
            if is_callback:
                self.bot.edit_message_text(
                    main_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    main_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_favorites', {
                'count': len(favorites)
            })
            
        except Exception as e:
            logger.error(f"Ошибка показа избранного: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке избранного. Пожалуйста, попробуйте позже."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def show_support(self, message_or_call):
        """Показать информацию о поддержке"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            support_text = f"""
{Emoji.SUPPORT} <b>СЛУЖБА ПОДДЕРЖКИ {Config.SHOP_NAME}</b>

{Emoji.PHONE} <b>Контакты:</b>
📞 Телефон: {Config.SHOP_PHONE}
✈️ Telegram: {Config.SUPPORT_USERNAME}
📧 Email: {Config.SHOP_EMAIL}

{Emoji.CLOCK} <b>Часы работы:</b>
Пн-Пт: 10:00-22:00
Сб-Вс: 11:00-20:00

{Emoji.MESSAGE} <b>Услуги поддержки:</b>
• Консультация по товарам и размерам
• Помощь с выбором и оформлением заказа
• Отслеживание статуса заказа
• Возврат и обмен товаров
• Индивидуальный пошив на заказ
• VIP обслуживание

{Emoji.STAR} <b>Персональный консьерж</b>
Каждый клиент {Config.SHOP_NAME} получает персонального консьержа, 
который поможет с подбором образа, оформлением заказа и ответит на все вопросы.

{Emoji.LINK} <b>Связаться с поддержкой:</b>
"""
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.MESSAGE} Написать в поддержку",
                url=f"https://t.me/{Config.SUPPORT_USERNAME.replace('@', '')}"
            ))
            
            if is_callback:
                self.bot.edit_message_text(
                    support_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    support_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_support')
            
        except Exception as e:
            logger.error(f"Ошибка показа информации о поддержке: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке информации о поддержке."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def show_discounts(self, message_or_call):
        """Показать скидки и промокоды"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Получаем активные промокоды
            promo_codes = []
            for code in ['WELCOME15', 'VIP25', 'SUMMER2024', 'FIRSTORDER', 'ELITE30']:
                promo = self.db.get_promo_code(code)
                if promo:
                    promo_codes.append(promo)
            
            discounts_text = f"""
{Emoji.SALE} <b>АКЦИИ И ПРЕДЛОЖЕНИЯ {Config.SHOP_NAME}</b>

{Emoji.GIFT} <b>Текущие акции:</b>
"""
            
            if promo_codes:
                for promo in promo_codes:
                    discount_text = ""
                    if promo['discount_percent']:
                        discount_text = f"{promo['discount_percent']}%"
                    elif promo['discount_amount']:
                        discount_text = f"{self.format_price(promo['discount_amount'])} {Config.CURRENCY}"
                    
                    min_order = f"от {self.format_price(promo['min_order_amount'])} {Config.CURRENCY}" if promo['min_order_amount'] > 0 else "без ограничений"
                    
                    discounts_text += f"""
• <b>{promo['code']} - {discount_text}</b>
  {promo['description']}
  Минимальный заказ: {min_order}
"""
                    
                    if promo['usage_limit']:
                        remaining = promo['usage_limit'] - promo['used_count']
                        discounts_text += f"  Осталось: {remaining} из {promo['usage_limit']} использований\n"
            else:
                discounts_text += f"""
• <b>WELCOME15 - 15%</b>
  Приветственная скидка для новых клиентов
  Минимальный заказ: без ограничений

• <b>VIP25 - 25%</b>
  Скидка для VIP клиентов
  Минимальный заказ: от 50.000 {Config.CURRENCY}

• <b>SUMMER2024 - 20%</b>
  Скидка на летнюю коллекцию
  Минимальный заказ: от 30.000 {Config.CURRENCY}

• <b>FIRSTORDER - 10%</b>
  Скидка на первый заказ
  Минимальный заказ: от 10.000 {Config.CURRENCY}

• <b>ELITE30 - 30%</b>
  Эксклюзивная скидка VOGUE ÉLITE
  Минимальный заказ: от 100.000 {Config.CURRENCY}
"""
            
            discounts_text += f"""
{Emoji.INFO} <b>Как использовать промокод:</b>
1. Добавьте товары в корзину
2. При оформлении заказа введите промокод
3. Скидка применится автоматически

{Emoji.STAR} <b>Особые условия:</b>
• Скидки не суммируются
• Промокоды действуют до 31.12.2024
• Бесплатная доставка от {Config.FREE_DELIVERY_THRESHOLD:,} {Config.CURRENCY}
• Акции могут быть изменены или отменены

{Emoji.NEXT} <b>Станьте VIP клиентом:</b>
При покупке на сумму от 100.000 {Config.CURRENCY} вы получаете VIP статус
с дополнительными привилегиями и скидками!
"""
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.COUPON} Применить промокод",
                callback_data="promo_apply"
            ))
            
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Открыть магазин",
                web_app=types.WebAppInfo(url=self.web_app_url)
            ))
            
            if is_callback:
                self.bot.edit_message_text(
                    discounts_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    discounts_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_discounts')
            
        except Exception as e:
            logger.error(f"Ошибка показа скидок: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при загрузке информации о скидках."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def start_promo_code_input(self, message_or_call):
        """Начало ввода промокода"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Сохраняем состояние
            self.db.save_user_state(
                user_id,
                'waiting_promo_code',
                {}
            )
            
            text = f"""
{Emoji.COUPON} <b>ПРОВЕРКА ПРОМОКОДА</b>

Введите промокод для проверки:

{Emoji.INFO} <b>Примеры активных промокодов:</b>
• WELCOME15 - 15% скидка
• VIP25 - 25% скидка для VIP
• SUMMER2024 - 20% скидка
• FIRSTORDER - 10% на первый заказ
• ELITE30 - 30% эксклюзивная скидка

{Emoji.CANCEL} Для отмены отправьте /cancel
"""
            
            if is_callback:
                self.bot.edit_message_text(
                    text,
                    message.chat.id,
                    message.message_id,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка начала ввода промокода: {e}")
    
    def process_promo_code(self, message, state_data):
        """Обработка введенного промокода"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Проверка промокода отменена.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            promo_code = message.text.strip().upper()
            
            # Получаем информацию о промокоде
            promo = self.db.get_promo_code(promo_code)
            
            if not promo:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} <b>Промокод не найден</b>\n\n"
                    f"Проверьте правильность ввода или срок действия промокода.",
                    parse_mode='HTML'
                )
                return
            
            # Форматируем информацию
            discount_text = ""
            if promo['discount_percent']:
                discount_text = f"{promo['discount_percent']}%"
            elif promo['discount_amount']:
                discount_text = f"{self.format_price(promo['discount_amount'])} {Config.CURRENCY}"
            
            conditions = []
            if promo['min_order_amount'] > 0:
                conditions.append(f"• Минимальная сумма заказа: {self.format_price(promo['min_order_amount'])} {Config.CURRENCY}")
            if promo['usage_limit']:
                remaining = promo['usage_limit'] - promo['used_count']
                conditions.append(f"• Осталось использований: {remaining}")
            if promo['valid_until']:
                valid_date = datetime.strptime(promo['valid_until'], '%Y-%m-%d %H:%M:%S')
                conditions.append(f"• Действует до: {valid_date.strftime('%d.%m.%Y')}")
            
            conditions_text = "\n".join(conditions) if conditions else "• Без ограничений"
            
            promo_text = f"""
{Emoji.COUPON} <b>ПРОМОКОД АКТИВЕН!</b>

🎯 <b>Код:</b> <code>{promo['code']}</code>
💰 <b>Скидка:</b> {discount_text}
📝 <b>Описание:</b> {promo['description']}

📋 <b>Условия:</b>
{conditions_text}

{Emoji.INFO} <b>Как использовать:</b>
1. Добавьте товары в корзину
2. При оформлении заказа введите промокод
3. Скидка применится автоматически
"""
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.DRESS} Перейти в каталог",
                callback_data="show_catalog"
            ))
            
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.CART} Перейти в корзину",
                callback_data="cart_view"
            ))
            
            self.bot.send_message(
                message.chat.id,
                promo_text,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Очищаем состояние
            self.db.clear_user_state(user_id)
            
            # Логируем действие
            self.db.log_user_action(user_id, 'check_promo_code', {
                'code': promo_code,
                'valid': True
            })
            
        except Exception as e:
            logger.error(f"Ошибка обработки промокода: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка при проверке промокода."
            )
    
    def process_promo_code_input(self, message, promo_code):
        """Обработка прямого ввода промокода"""
        self.process_promo_code(message, {})
    
    def start_search(self, message_or_call):
        """Начало поиска товаров"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Сохраняем состояние
            self.db.save_user_state(
                user_id,
                'waiting_search_query',
                {}
            )
            
            text = f"""
{Emoji.SEARCH} <b>ПОИСК ТОВАРОВ</b>

Введите название товара, бренд или ключевые слова для поиска:

{Emoji.INFO} <b>Примеры запросов:</b>
• Платье
• Костюм VOGUE
• Кожаная сумка
• Шелковая блуза
• Кашемировое пальто

{Emoji.CANCEL} Для отмены отправьте /cancel
"""
            
            if is_callback:
                self.bot.edit_message_text(
                    text,
                    message.chat.id,
                    message.message_id,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка начала поиска: {e}")
    
    def process_search_query(self, message, state_data):
        """Обработка поискового запроса"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Поиск отменен.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            query = message.text.strip()
            
            # Ищем товары
            products = self.db.search_products(query, limit=10)
            
            # Очищаем состояние
            self.db.clear_user_state(user_id)
            
            if not products:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.DRESS} Перейти в каталог",
                    callback_data="show_catalog"
                ))
                
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.SEARCH} <b>ПОИСК: \"{query}\"</b>\n\n"
                    f"{Emoji.INFO} По вашему запросу ничего не найдено.\n\n"
                    f"Попробуйте изменить запрос или посмотрите товары в каталоге:",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                return
            
            # Показываем результаты
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.SEARCH} <b>РЕЗУЛЬТАТЫ ПОИСКА: \"{query}\"</b>\n\n"
                f"{Emoji.INFO} Найдено товаров: {len(products)}\n",
                parse_mode='HTML'
            )
            
            # Показываем найденные товары
            for product in products:
                product_text = self.format_product_message(product)
                
                markup = types.InlineKeyboardMarkup(row_width=3)
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.VIEW} Подробнее",
                        callback_data=f"product_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.HEART} В избранное",
                        callback_data=f"add_favorite_{product['id']}"
                    )
                )
                
                try:
                    if product.get('image_url'):
                        self.bot.send_photo(
                            message.chat.id,
                            product['image_url'],
                            caption=product_text,
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                    else:
                        self.bot.send_message(
                            message.chat.id,
                            product_text,
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки найденного товара: {e}")
            
            # Логируем действие
            self.db.log_user_action(user_id, 'search', {
                'query': query,
                'results': len(products)
            })
            
        except Exception as e:
            logger.error(f"Ошибка обработки поискового запроса: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка при поиске. Пожалуйста, попробуйте снова."
            )
    
    def process_search(self, message, query):
        """Обработка поиска из текстового сообщения"""
        try:
            user_id = message.from_user.id
            
            # Ищем товары
            products = self.db.search_products(query, limit=5)
            
            if not products:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.SEARCH} По запросу \"{query}\" ничего не найдено.\n\n"
                    f"Попробуйте уточнить запрос или используйте команду /search для расширенного поиска.",
                    parse_mode='HTML'
                )
                return
            
            # Показываем первые 3 товара
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.SEARCH} <b>НАЙДЕНО ПО ЗАПРОСУ \"{query}\":</b>\n\n"
                f"{Emoji.INFO} Найдено товаров: {len(products)}\n"
                f"Показаны первые {min(3, len(products))}",
                parse_mode='HTML'
            )
            
            for i, product in enumerate(products[:3]):
                product_text = f"""
{Emoji.TAG} <b>{product['name']}</b>

{Emoji.MONEY} <b>Цена:</b> {self.format_price(product['price'])} {Config.CURRENCY}
{Emoji.CATEGORY} <b>Категория:</b> {product['category']}
{Emoji.ARTICLE} <b>Артикул:</b> {product['article']}

{Emoji.INFO} <b>Описание:</b>
{product.get('description', '')[:100]}...
"""
                
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton(
                        f"{Emoji.VIEW} Подробнее",
                        callback_data=f"product_{product['id']}"
                    ),
                    types.InlineKeyboardButton(
                        f"{Emoji.CART} В корзину",
                        callback_data=f"add_to_cart_{product['id']}"
                    )
                )
                
                self.bot.send_message(
                    message.chat.id,
                    product_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            if len(products) > 3:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    f"{Emoji.SEARCH} Показать все результаты ({len(products)})",
                    callback_data="search_all"
                ))
                
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.INFO} Хотите увидеть все результаты поиска?",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'quick_search', {
                'query': query,
                'results': len(products)
            })
            
        except Exception as e:
            logger.error(f"Ошибка быстрого поиска: {e}")
    
    def open_web_app(self, message_or_call):
        """Открыть веб-приложение магазина"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            web_app_button = types.WebAppInfo(url=self.web_app_url)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Открыть Web Boutique",
                web_app=web_app_button
            ))
            
            web_app_text = f"""
{Emoji.WEBSITE} <b>WEB BOUTIQUE {Config.SHOP_NAME}</b>

{Emoji.STAR} Полная версия магазина с удобным интерфейсом:

{Emoji.CHECK} <b>Доступные функции:</b>
• Полный каталог с фильтрами и поиском
• Подробные карточки товаров с фото
• Выбор размера, цвета и других параметров
• Удобная корзина покупок
• Быстрое оформление заказа
• История всех заказов
• Личный кабинет с настройками
• Применение промокодов и скидок

{Emoji.SHIELD} <b>Безопасность:</b>
• Защищенные платежи
• Конфиденциальность данных
• SSL шифрование

{Emoji.LINK} <b>Ссылка:</b> {self.web_app_url}

{Emoji.NEXT} Нажмите кнопку ниже для открытия:
"""
            
            if is_callback:
                self.bot.edit_message_text(
                    web_app_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    web_app_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'open_web_app')
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-приложения: {e}")
            error_text = f"{Emoji.WARNING} Произошла ошибка при открытии веб-приложения."
            
            if is_callback:
                try:
                    self.bot.edit_message_text(
                        error_text,
                        message.chat.id,
                        message.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            else:
                self.bot.send_message(message.chat.id, error_text, parse_mode='HTML')
    
    def open_web_catalog(self, message, category=None):
        """Открыть каталог в веб-приложении"""
        try:
            url = f"{self.web_app_url}/catalog"
            if category:
                url += f"?category={urllib.parse.quote(category)}"
            
            web_app_button = types.WebAppInfo(url=url)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Открыть каталог",
                web_app=web_app_button
            ))
            
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.DRESS} <b>Открытие каталога</b>\n\n"
                f"Нажмите кнопку ниже для открытия каталога в веб-версии магазина:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-каталога: {e}")
    
    def open_web_cart(self, message):
        """Открыть корзину в веб-приложении"""
        try:
            web_app_button = types.WebAppInfo(url=f"{self.web_app_url}/cart")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.CART} Открыть корзину",
                web_app=web_app_button
            ))
            
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.CART} <b>Открытие корзины</b>\n\n"
                f"Нажмите кнопку ниже для открытия корзины в веб-версии магазина:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-корзина: {e}")
    
    def open_web_orders(self, message):
        """Открыть историю заказов в веб-приложении"""
        try:
            web_app_button = types.WebAppInfo(url=f"{self.web_app_url}/orders")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.ORDER} Открыть заказы",
                web_app=web_app_button
            ))
            
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.ORDER} <b>Открытие истории заказов</b>\n\n"
                f"Нажмите кнопку ниже для открытия истории заказов в веб-версии магазина:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-заказов: {e}")
    
    def open_web_profile(self, message):
        """Открыть профиль в веб-приложении"""
        try:
            web_app_button = types.WebAppInfo(url=f"{self.web_app_url}/profile")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.USER} Открыть профиль",
                web_app=web_app_button
            ))
            
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.USER} <b>Открытие профиля</b>\n\n"
                f"Нажмите кнопку ниже для открытия профиля в веб-версии магазина:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-профиля: {e}")
    
    def open_web_product(self, message, product_id):
        """Открыть товар в веб-приложении"""
        try:
            web_app_button = types.WebAppInfo(url=f"{self.web_app_url}/product/{product_id}")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Открыть на сайте",
                web_app=web_app_button
            ))
            
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.VIEW} <b>Открытие товара</b>\n\n"
                f"Нажмите кнопку ниже для открытия товара в веб-версии магазина:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка открытия веб-товара: {e}")
    
    

    def show_database_info(self, message):
        """Показать информацию о базе данных"""
        try:
            if message.chat.id not in Config.ADMIN_IDS:
                return
            
            # Получаем информацию о базе данных
            cursor = self.db.conn.cursor()
            
            # Размер базы данных
            db_size = os.path.getsize(Config.DATABASE_PATH) if os.path.exists(Config.DATABASE_PATH) else 0
            
            # Количество записей в таблицах
            tables = ['bot_users', 'bot_products_cache', 'bot_cart', 'bot_favorites', 'bot_orders', 'bot_user_actions']
            table_counts = {}
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                result = cursor.fetchone()
                table_counts[table] = result['count'] if result else 0
            
            db_info = f"""
{Emoji.DATABASE} <b>ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ</b>

{Emoji.INFO} <b>Общая информация:</b>
• Путь к файлу: {Config.DATABASE_PATH}
• Размер файла: {db_size / 1024 / 1024:.2f} MB
• Дата создания: {datetime.fromtimestamp(os.path.getctime(Config.DATABASE_PATH)).strftime('%d.%m.%Y %H:%M') if os.path.exists(Config.DATABASE_PATH) else 'Неизвестно'}

{Emoji.STATS} <b>Статистика таблиц:</b>
• Пользователи: {table_counts['bot_users']} записей
• Товары: {table_counts['bot_products_cache']} записей
• Корзина: {table_counts['bot_cart']} записей
• Избранное: {table_counts['bot_favorites']} записей
• Заказы: {table_counts['bot_orders']} записей
• Действия: {table_counts['bot_user_actions']} записей

{Emoji.CLOCK} <b>Последняя синхронизация:</b>
{self.db.sync_with_webapp()}

{Emoji.WARNING} <b>Внимание:</b>
• Регулярно делайте резервные копии базы данных
• Очищайте старые данные через настройки
"""
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад",
                callback_data="admin_panel"
            ))
            
            if hasattr(message, 'message_id'):
                self.bot.edit_message_text(
                    db_info,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    db_info,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка показа информации о БД: {e}")
    
    def show_admin_settings(self, message):
        """Показать настройки администратора"""
        try:
            if message.chat.id not in Config.ADMIN_IDS:
                return
            
            settings_text = f"""
{Emoji.SETTINGS} <b>НАСТРОЙКИ АДМИНИСТРАТОРА</b>

{Emoji.INFO} <b>Конфигурация бота:</b>
• Название магазина: {Config.SHOP_NAME}
• Web App URL: {Config.WEB_APP_URL}
• Администраторы: {len(Config.ADMIN_IDS)} пользователей
• Токен бота: {'Установлен' if Config.BOT_TOKEN else 'Не установлен'}
• База данных: {Config.DATABASE_PATH}
• Интервал синхронизации: {Config.SYNC_INTERVAL} секунд

{Emoji.MONEY} <b>Настройки доставки:</b>
• Бесплатная доставка от: {self.format_price(Config.FREE_DELIVERY_THRESHOLD)} {Config.CURRENCY}
• Стоимость доставки: {self.format_price(Config.DELIVERY_COST)} {Config.CURRENCY}

{Emoji.PHONE} <b>Контактная информация:</b>
• Телефон: {Config.SHOP_PHONE}
• Email: {Config.SHOP_EMAIL}
• Поддержка: {Config.SUPPORT_USERNAME}

{Emoji.WARNING} <b>Важно:</b>
• Изменение настроек требует перезапуска бота
• Токен бота должен храниться в секрете
• Регулярно проверяйте работоспособность веб-приложения
"""
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад",
                callback_data="admin_panel"
            ))
            
            if hasattr(message, 'message_id'):
                self.bot.edit_message_text(
                    settings_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    settings_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка показа настроек администратора: {e}")
    
    def show_stats(self, message_or_call):
        """Показать статистику магазина"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Проверяем права администратора
            if user_id not in Config.ADMIN_IDS:
                if is_callback:
                    self.bot.answer_callback_query(
                        message_or_call.id,
                        "Доступ запрещен",
                        show_alert=True
                    )
                return
            
            stats = self.db.get_system_stats()
            
            if not stats:
                stats_text = f"{Emoji.WARNING} Не удалось получить статистику."
            else:
                stats_text = f"""
{Emoji.STATS} <b>СТАТИСТИКА {Config.SHOP_NAME}</b>

{Emoji.USERS} <b>Пользователи:</b>
• Всего пользователей: {stats.get('total_users', 0)}
• VIP пользователей: {stats.get('vip_users', 0)}
• Активных сегодня: {stats.get('active_today', 0)}
• Активных за неделю: {stats.get('active_week', 0)}

{Emoji.DRESS} <b>Товары:</b>
• Всего товаров: {stats.get('total_products', 0)}
• Новинок: {stats.get('new_products', 0)}
• Эксклюзивных: {stats.get('exclusive_products', 0)}
• Стоимость запасов: {self.format_price(stats.get('inventory_value', 0))} {Config.CURRENCY}

{Emoji.CART} <b>Корзины:</b>
• Пользователей с корзиной: {stats.get('users_with_cart', 0)}
• Товаров в корзинах: {stats.get('total_cart_items', 0)}

{Emoji.HEART} <b>Избранное:</b>
• Пользователей с избранным: {stats.get('users_with_favorites', 0)}
• Товаров в избранном: {stats.get('total_favorites', 0)}

{Emoji.ORDER} <b>Заказы:</b>
• Всего заказов: {stats.get('total_orders', 0)}
• Общая выручка: {self.format_price(stats.get('total_revenue', 0))} {Config.CURRENCY}

{Emoji.CHART} <b>Статусы заказов:</b>
"""
                
                if stats.get('orders_by_status'):
                    for status, count in stats['orders_by_status'].items():
                        emoji = self.get_status_emoji(status)
                        status_text = self.get_status_text(status)
                        stats_text += f"• {emoji} {status_text}: {count}\n"
                
                stats_text += f"\n{Emoji.CLOCK} <b>Обновлено:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.REFRESH} Обновить",
                callback_data="stats_refresh"
            ))
            
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад",
                callback_data="admin_panel"
            ))
            
            if is_callback:
                self.bot.edit_message_text(
                    stats_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    stats_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_stats')
            
        except Exception as e:
            logger.error(f"Ошибка показа статистики: {e}")
            if is_callback:
                self.bot.answer_callback_query(
                    message_or_call.id,
                    "Ошибка загрузки статистики",
                    show_alert=True
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Произошла ошибка при загрузке статистики.",
                    parse_mode='HTML'
                )
    
    def show_users_list(self, message_or_call):
        """Показать список пользователей"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Проверяем права администратора
            if user_id not in Config.ADMIN_IDS:
                if is_callback:
                    self.bot.answer_callback_query(
                        message_or_call.id,
                        "Доступ запрещен",
                        show_alert=True
                    )
                return
            
            users = self.db.get_all_users(include_admins=True)
            
            if not users:
                users_text = "Нет пользователей в базе данных"
            else:
                # Группируем по VIP статусу
                vip_users = [u for u in users if u.get('is_vip')]
                regular_users = [u for u in users if not u.get('is_vip')]
                admin_users = [u for u in users if u.get('is_admin')]
                
                users_text = f"{Emoji.USERS} <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
                users_text += f"{Emoji.VIP} <b>VIP пользователи ({len(vip_users)}):</b>\n"
                
                for i, user in enumerate(vip_users[:10], 1):
                    admin_mark = " 👑" if user.get('is_admin') else ""
                    users_text += f"{i}. {user.get('first_name', 'Неизвестно')} "
                    if user.get('username'):
                        users_text += f"(@{user['username']})"
                    users_text += f"{admin_mark}\n"
                
                if len(vip_users) > 10:
                    users_text += f"... и еще {len(vip_users) - 10} VIP пользователей\n\n"
                else:
                    users_text += "\n"
                
                users_text += f"{Emoji.USER} <b>Обычные пользователи ({len(regular_users)}):</b>\n"
                
                for i, user in enumerate(regular_users[:10], 1):
                    users_text += f"{i}. {user.get('first_name', 'Неизвестно')} "
                    if user.get('username'):
                        users_text += f"(@{user['username']})"
                    users_text += f"\n"
                
                if len(regular_users) > 10:
                    users_text += f"... и еще {len(regular_users) - 10} пользователей\n\n"
                else:
                    users_text += "\n"
                
                users_text += f"{Emoji.ADMIN} <b>Администраторы ({len(admin_users)}):</b>\n"
                
                for user in admin_users:
                    users_text += f"• {user.get('first_name', 'Неизвестно')} "
                    if user.get('username'):
                        users_text += f"(@{user['username']})"
                    users_text += f"\n"
                
                users_text += f"\n{Emoji.STATS} <b>Итого:</b> {len(users)} пользователей"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.WEBSITE} Веб-админка",
                web_app=types.WebAppInfo(url=f"{self.web_app_url}/admin/users")
            ))
            
            markup.add(types.InlineKeyboardButton(
                f"{Emoji.BACK} Назад",
                callback_data="admin_panel"
            ))
            
            if is_callback:
                self.bot.edit_message_text(
                    users_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    users_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Логируем действие
            self.db.log_user_action(user_id, 'view_users_list')
            
        except Exception as e:
            logger.error(f"Ошибка показа списка пользователей: {e}")
            if is_callback:
                self.bot.answer_callback_query(
                    message_or_call.id,
                    "Ошибка загрузки списка пользователей",
                    show_alert=True
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Произошла ошибка при загрузке списка пользователей.",
                    parse_mode='HTML'
                )
    
    def start_broadcast(self, message_or_call):
        """Начать создание рассылки"""
        try:
            if hasattr(message_or_call, 'message'):
                message = message_or_call.message
                user_id = message_or_call.from_user.id
                is_callback = True
            else:
                message = message_or_call
                user_id = message.from_user.id
                is_callback = False
            
            # Проверяем права администратора
            if user_id not in Config.ADMIN_IDS:
                if is_callback:
                    self.bot.answer_callback_query(
                        message_or_call.id,
                        "Доступ запрещен",
                        show_alert=True
                    )
                return
            
            # Сохраняем состояние пользователя
            self.db.save_user_state(
                user_id,
                'waiting_broadcast_message',
                {'step': 'message'}
            )
            
            broadcast_text = f"""
{Emoji.BROADCAST} <b>СОЗДАНИЕ РАССЫЛКИ</b>

Отправьте сообщение для рассылки. Вы можете отправить:
• Текст с HTML разметкой
• Фото с подписью
• Только текст

{Emoji.INFO} <b>Доступные HTML теги:</b>
<code>&lt;b&gt;жирный&lt;/b&gt;</code>
<code>&lt;i&gt;курсив&lt;/i&gt;</code>
<code>&lt;u&gt;подчеркнутый&lt;/u&gt;</code>
<code>&lt;s&gt;зачеркнутый&lt;/s&gt;</code>
<code>&lt;code&gt;код&lt;/code&gt;</code>
<code>&lt;a href="URL"&gt;ссылка&lt;/a&gt;</code>

{Emoji.WARNING} <b>Внимание:</b>
• Не используйте теги &lt;script&gt;
• Максимальная длина: 4096 символов
• Фото должны быть не более 20MB

{Emoji.CANCEL} Для отмены отправьте /cancel
"""
            
            if is_callback:
                self.bot.edit_message_text(
                    broadcast_text,
                    message.chat.id,
                    message.message_id,
                    parse_mode='HTML'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    broadcast_text,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка начала рассылки: {e}")
            if is_callback:
                self.bot.answer_callback_query(
                    message_or_call.id,
                    "Ошибка создания рассылки",
                    show_alert=True
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Произошла ошибка при создании рассылки.",
                    parse_mode='HTML'
                )
    
    def process_broadcast_message(self, message, state_data):
        """Обработка сообщения для рассылки"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Создание рассылки отменено.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            # Подготавливаем данные для рассылки
            broadcast_data = {
                'message_type': 'text',
                'content': '',
                'photo_id': None,
                'entities': None
            }
            
            if message.text:
                broadcast_data['content'] = message.text
                broadcast_data['message_type'] = 'text'
                if message.entities:
                    broadcast_data['entities'] = [
                        {'type': e.type, 'offset': e.offset, 'length': e.length, 'url': getattr(e, 'url', None)}
                        for e in message.entities
                    ]
            elif message.photo:
                broadcast_data['photo_id'] = message.photo[-1].file_id
                broadcast_data['content'] = message.caption or ''
                broadcast_data['message_type'] = 'photo'
                if message.caption_entities:
                    broadcast_data['entities'] = [
                        {'type': e.type, 'offset': e.offset, 'length': e.length, 'url': getattr(e, 'url', None)}
                        for e in message.caption_entities
                    ]
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Поддерживаются только текст или фото с подписью."
                )
                return
            
            # Обновляем состояние
            state_data['broadcast_data'] = broadcast_data
            state_data['step'] = 'target'
            self.db.save_user_state(user_id, 'waiting_broadcast_target', state_data)
            
            # Показываем предварительный просмотр
            self.show_broadcast_preview(message, broadcast_data)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения для рассылки: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка. Пожалуйста, попробуйте снова."
            )
    
    def show_broadcast_preview(self, message, broadcast_data):
        """Показать предварительный просмотр рассылки"""
        try:
            preview_text = broadcast_data['content'][:200]
            if len(broadcast_data['content']) > 200:
                preview_text += "..."
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(f"{Emoji.USERS} Всем пользователям", callback_data="broadcast_send_all"),
                types.InlineKeyboardButton(f"{Emoji.VIP} Только VIP", callback_data="broadcast_send_vip")
            )
            markup.add(
                types.InlineKeyboardButton(f"{Emoji.CANCEL} Отменить", callback_data="broadcast_cancel"),
                types.InlineKeyboardButton(f"{Emoji.CHECK} Отправить всем", callback_data="broadcast_send_all")
            )
            
            info_text = f"""
{Emoji.BROADCAST} <b>ПРЕДПРОСМОТР РАССЫЛКИ</b>

{Emoji.INFO} <b>Тип:</b> {broadcast_data['message_type'].upper()}
{Emoji.MESSAGE} <b>Содержание:</b>
{preview_text}

👇 <b>Выберите аудиторию:</b>
"""
            
            if broadcast_data['photo_id']:
                try:
                    self.bot.send_photo(
                        message.chat.id,
                        broadcast_data['photo_id'],
                        caption=info_text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
                except:
                    self.bot.send_message(
                        message.chat.id,
                        info_text,
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
            else:
                self.bot.send_message(
                    message.chat.id,
                    info_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка показа предпросмотра рассылки: {e}")
    
    def process_broadcast_target(self, message, state_data):
        """Обработка выбора цели для рассылки"""
        try:
            user_id = message.from_user.id
            
            if message.text and message.text.strip() == '/cancel':
                self.db.clear_user_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.CANCEL} Создание рассылки отменено.",
                    reply_markup=self.create_main_keyboard(message.chat.id)
                )
                return
            
            target = message.text.strip().lower()
            
            if target not in ['всем', 'все', 'all', 'vip', 'вип']:
                self.bot.send_message(
                    message.chat.id,
                    f"{Emoji.WARNING} Пожалуйста, выберите аудиторию:\n"
                    f"• 'всем' - для всех пользователей\n"
                    f"• 'vip' - только для VIP пользователей"
                )
                return
            
            # Обработка выбора цели рассылки
            if target in ['всем', 'все', 'all']:
                self.send_broadcast_to_users(user_id, state_data['broadcast_data'], 'all')
            elif target in ['vip', 'вип']:
                self.send_broadcast_to_users(user_id, state_data['broadcast_data'], 'vip')
            
        except Exception as e:
            logger.error(f"Ошибка обработки цели рассылки: {e}")
            self.bot.send_message(
                message.chat.id,
                f"{Emoji.WARNING} Произошла ошибка. Пожалуйста, попробуйте снова."
            )
    
    def send_broadcast_to_users(self, admin_id, broadcast_data, target_type):
        """Отправка рассылки пользователям"""
        try:
            # Получаем пользователей в зависимости от цели
            if target_type == 'all':
                users = self.db.get_all_users()
                target_text = "всем пользователям"
            elif target_type == 'vip':
                users = self.db.get_vip_users()
                target_text = "VIP пользователям"
            else:
                return
            
            total_users = len(users)
            if total_users == 0:
                self.bot.send_message(
                    admin_id,
                    f"{Emoji.WARNING} Нет пользователей для рассылки."
                )
                return
            
            # Отправляем сообщение администратору о начале рассылки
            progress_msg = self.bot.send_message(
                admin_id,
                f"{Emoji.BROADCAST} <b>Начинаю рассылку...</b>\n\n"
                f"Цель: {target_text}\n"
                f"Количество пользователей: {total_users}\n"
                f"Отправлено: 0/{total_users}",
                parse_mode='HTML'
            )
            
            # Отправляем рассылку
            success_count = 0
            fail_count = 0
            
            for i, user in enumerate(users, 1):
                try:
                    telegram_id = user['telegram_id']
                    
                    if broadcast_data['message_type'] == 'photo':
                        # Отправляем фото с подписью
                        self.bot.send_photo(
                            telegram_id,
                            broadcast_data['photo_id'],
                            caption=broadcast_data['content'],
                            parse_mode='HTML'
                        )
                    else:
                        # Отправляем текст
                        self.bot.send_message(
                            telegram_id,
                            broadcast_data['content'],
                            parse_mode='HTML'
                        )
                    
                    success_count += 1
                    
                    # Обновляем прогресс каждые 10 пользователей
                    if i % 10 == 0 or i == total_users:
                        try:
                            self.bot.edit_message_text(
                                f"{Emoji.BROADCAST} <b>Рассылка в процессе...</b>\n\n"
                                f"Цель: {target_text}\n"
                                f"Количество пользователей: {total_users}\n"
                                f"Отправлено: {i}/{total_users}\n"
                                f"Успешно: {success_count}\n"
                                f"Ошибок: {fail_count}",
                                admin_id,
                                progress_msg.message_id,
                                parse_mode='HTML'
                            )
                        except:
                            pass
                    
                    # Небольшая задержка, чтобы не превысить лимиты Telegram
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Ошибка отправки рассылки пользователю {user.get('telegram_id')}: {e}")
            
            # Отправляем итоговый отчет
            self.bot.send_message(
                admin_id,
                f"{Emoji.CHECK} <b>РАССЫЛКА ЗАВЕРШЕНА!</b>\n\n"
                f"Цель: {target_text}\n"
                f"Всего пользователей: {total_users}\n"
                f"Успешно отправлено: {success_count}\n"
                f"Ошибок отправки: {fail_count}\n"
                f"Процент успеха: {success_count/total_users*100:.1f}%",
                parse_mode='HTML'
            )
            
            # Удаляем сообщение о прогрессе
            try:
                self.bot.delete_message(admin_id, progress_msg.message_id)
            except:
                pass
            
            # Очищаем состояние пользователя
            self.db.clear_user_state(admin_id)
            
            # Логируем действие
            self.db.log_user_action(admin_id, 'broadcast_sent', {
                'target_type': target_type,
                'total_users': total_users,
                'success_count': success_count,
                'fail_count': fail_count
            })
            
        except Exception as e:
            logger.error(f"Ошибка отправки рассылки: {e}")
            self.bot.send_message(
                admin_id,
                f"{Emoji.WARNING} Произошла ошибка при отправке рассылки: {str(e)}"
            )

# Запуск бота
if __name__ == "__main__":
    try:
        bot = VogueEliteBot()
        logger.info("Бот успешно запущен!")
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"Критическая ошибка: {e}")
