# sync.py
import sqlite3
import json
import requests
import time
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VogueEliteSync')

class DatabaseSync:
    def __init__(self):
        self.web_db_path = 'instance/fashion_store.db'
        self.bot_db_path = 'fashion_store.db'
        self.web_app_url = 'http://localhost:8080'
        
    def sync_products(self):
        """Синхронизация товаров между веб-приложением и ботом"""
        try:
            # Подключаемся к обеим базам данных
            web_conn = sqlite3.connect(self.web_db_path)
            bot_conn = sqlite3.connect(self.bot_db_path)
            
            web_cursor = web_conn.cursor()
            bot_cursor = bot_conn.cursor()
            
            # Получаем все активные товары из веб-базы
            web_cursor.execute('''
                SELECT id, article, name, description, price, 
                       old_price, discount, category, image_url,
                       is_new, is_hit, is_exclusive, is_limited,
                       stock, brand, color, size
                FROM products 
                WHERE is_active = 1
            ''')
            
            web_products = web_cursor.fetchall()
            
            # Создаем или обновляем таблицу товаров в боте
            bot_cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    article TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    old_price REAL,
                    discount INTEGER DEFAULT 0,
                    category TEXT NOT NULL,
                    image_url TEXT,
                    is_new INTEGER DEFAULT 0,
                    is_hit INTEGER DEFAULT 0,
                    is_exclusive INTEGER DEFAULT 0,
                    is_limited INTEGER DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    brand TEXT,
                    color TEXT,
                    size TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Синхронизируем каждый товар
            for product in web_products:
                bot_cursor.execute('''
                    INSERT OR REPLACE INTO products 
                    (id, article, name, description, price, old_price, 
                     discount, category, image_url, is_new, is_hit, 
                     is_exclusive, is_limited, stock, brand, color, size, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', product)
            
            bot_conn.commit()
            
            # Синхронизация пользователей
            self.sync_users(web_cursor, bot_cursor)
            
            web_conn.close()
            bot_conn.close()
            
            logger.info(f"Синхронизировано {len(web_products)} товаров")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            return False
    
    def sync_users(self, web_cursor, bot_cursor):
        """Синхронизация пользователей"""
        try:
            web_cursor.execute('''
                SELECT id, telegram_id, username, first_name, last_name,
                       email, phone, is_admin, is_vip, total_orders, total_spent,
                       referral_code, created_at
                FROM users
            ''')
            
            web_users = web_cursor.fetchall()
            
            bot_cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    email TEXT,
                    phone TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_vip INTEGER DEFAULT 0,
                    total_orders INTEGER DEFAULT 0,
                    total_spent REAL DEFAULT 0,
                    referral_code TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for user in web_users:
                bot_cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (id, telegram_id, username, first_name, last_name,
                     email, phone, is_admin, is_vip, total_orders, total_spent,
                     referral_code, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', user)
            
            logger.info(f"Синхронизировано {len(web_users)} пользователей")
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации пользователей: {e}")
    
    def sync_cart(self, user_id):
        """Синхронизация корзины пользователя"""
        try:
            # Эта функция будет вызываться при входе пользователя
            # и синхронизировать корзину между платформами
            
            web_conn = sqlite3.connect(self.web_db_path)
            bot_conn = sqlite3.connect(self.bot_db_path)
            
            web_cursor = web_conn.cursor()
            bot_cursor = bot_conn.cursor()
            
            # Получаем корзину из веб-приложения
            web_cursor.execute('''
                SELECT c.id, c.product_id, c.quantity, c.selected_size, c.selected_color
                FROM cart c
                WHERE c.user_id = ?
            ''', (user_id,))
            
            web_cart = web_cursor.fetchall()
            
            # Создаем таблицу корзины в боте
            bot_cursor.execute('''
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    selected_size TEXT,
                    selected_color TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Удаляем старую корзину в боте
            bot_cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            
            # Добавляем элементы корзины
            for item in web_cart:
                _, product_id, quantity, size, color = item
                bot_cursor.execute('''
                    INSERT INTO cart (user_id, product_id, quantity, selected_size, selected_color)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, product_id, quantity, size, color))
            
            bot_conn.commit()
            web_conn.close()
            bot_conn.close()
            
            logger.info(f"Синхронизирована корзина пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации корзины: {e}")
            return False
    
    def get_user_by_telegram(self, telegram_id):
        """Получение пользователя по telegram_id"""
        try:
            web_conn = sqlite3.connect(self.web_db_path)
            cursor = web_conn.cursor()
            
            cursor.execute('''
                SELECT id, username, first_name, last_name, email, phone,
                       is_admin, is_vip, referral_code
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            user = cursor.fetchone()
            web_conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'first_name': user[2],
                    'last_name': user[3],
                    'email': user[4],
                    'phone': user[5],
                    'is_admin': bool(user[6]),
                    'is_vip': bool(user[7]),
                    'referral_code': user[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    def create_user_from_telegram(self, telegram_user):
        """Создание пользователя из Telegram"""
        try:
            web_conn = sqlite3.connect(self.web_db_path)
            cursor = web_conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_user.id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Обновляем данные
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_activity = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (telegram_user.username, telegram_user.first_name, telegram_user.last_name, telegram_user.id))
            else:
                # Создаем нового пользователя
                referral_code = f"VIP{telegram_user.id:06d}"
                cursor.execute('''
                    INSERT INTO users 
                    (telegram_id, username, first_name, last_name, 
                     referral_code, created_at, last_activity)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (telegram_user.id, telegram_user.username, 
                      telegram_user.first_name, telegram_user.last_name, referral_code))
            
            web_conn.commit()
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_user.id,))
            user_id = cursor.fetchone()[0]
            
            web_conn.close()
            
            # Создаем соответствующую запись в базе бота
            bot_conn = sqlite3.connect(self.bot_db_path)
            bot_cursor = bot_conn.cursor()
            
            bot_cursor.execute('''
                INSERT OR REPLACE INTO users 
                (id, telegram_id, username, first_name, last_name, referral_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, telegram_user.id, telegram_user.username,
                  telegram_user.first_name, telegram_user.last_name, referral_code))
            
            bot_conn.commit()
            bot_conn.close()
            
            logger.info(f"Создан/обновлен пользователь: {telegram_user.first_name} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return None

if __name__ == '__main__':
    sync = DatabaseSync()
    sync.sync_products()
    print("Синхронизация завершена!")
