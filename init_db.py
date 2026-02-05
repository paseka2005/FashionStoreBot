# init_db.py
from app import app, db

with app.app_context():
    print("Создание таблиц базы данных...")
    db.create_all()
    print("Таблицы успешно созданы!")
    
    # Проверим, что таблицы созданы
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Созданные таблицы: {tables}")
