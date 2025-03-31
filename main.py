import logging
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# Инициализация бота и диспетчера
API_TOKEN = 'YOUR_BOT_TOKEN'  # Замените на свой токен
ADMIN_ID = 123456789  # Замените на свой Telegram ID для доступа администратора

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определение состояний для разных операций
class OrderStates(StatesGroup):
    """
    Состояния для FSM при оформлении заказа
    """
    selecting_product = State()  # Выбор товара
    selecting_quantity = State()  # Выбор количества
    confirming_order = State()   # Подтверждение заказа
    checking_status = State()    # Проверка статуса заказа

class AdminStates(StatesGroup):
    """
    Состояния для FSM при работе с админскими функциями
    """
    updating_stock = State()             # Обновление запасов
    selecting_product_to_update = State() # Выбор товара для обновления
    entering_new_stock = State()         # Ввод нового количества
    
    viewing_orders = State()             # Просмотр заказов
    viewing_order_details = State()      # Просмотр деталей заказа
    changing_order_status = State()      # Изменение статуса заказа

# Создание роутеров
main_router = Router()
order_router = Router()
admin_router = Router()

# Инициализация базы данных
def init_db():
    """
    Создает базу данных SQLite со всеми необходимыми таблицами
    и добавляет тестовые товары, если таблица товаров пуста
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    # Создание таблицы товаров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # Создание таблицы заказов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        total_price REAL NOT NULL
    )
    ''')
    
    # Создание таблицы позиций заказа
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Создание таблицы пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        full_name TEXT,
        is_admin INTEGER DEFAULT 0
    )
    ''')
    
    # Вставка тестовых товаров, если таблица пуста
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Футболка', 'Хлопковая футболка, размеры S-XL', 550.00, 50),
            ('Джинсы', 'Классические джинсы, размеры 28-36', 1099.00, 30),
            ('Кроссовки', 'Спортивные кроссовки, размеры 36-45', 1850.00, 25),
            ('Куртка', 'Демисезонная куртка, размеры S-XXL', 2200.00, 15),
            ('Шапка', 'Теплая зимняя шапка', 450.00, 40)
        ]
        cursor.executemany('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)', sample_products)
    
    # Установка статуса администратора
    cursor.execute('INSERT OR IGNORE INTO users (user_id, is_admin) VALUES (?, 1)', (ADMIN_ID,))
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# Вспомогательные функции для работы с базой данных
def get_products() -> List[Tuple]:
    """
    Получает список всех товаров из базы данных
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products')
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id: int) -> Optional[Tuple]:
    """
    Получает товар по его ID
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def update_product_stock(product_id: int, new_stock: int) -> None:
    """
    Обновляет количество товара на складе
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    conn.commit()
    conn.close()
    logger.info(f"Обновлен запас товара с ID {product_id} на {new_stock}")

def create_order(user_id: int, cart: Dict[int, int], total_price: float) -> int:
    """
    Создает новый заказ и добавляет товары из корзины
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    # Создание заказа
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO orders (user_id, order_date, status, total_price) VALUES (?, ?, ?, ?)',
        (user_id, order_date, 'Новый', total_price)
    )
    order_id = cursor.lastrowid
    
    # Добавление позиций заказа
    for product_id, quantity in cart.items():
        product = get_product_by_id(product_id)
        if product:
            price = product[3]  # price at index 3
            cursor.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, product_id, quantity, price)
            )
            
            # Обновление запасов
            new_stock = product[4] - quantity  # stock at index 4
            cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    
    conn.commit()
    conn.close()
    logger.info(f"Создан заказ {order_id} для пользователя {user_id}")
    
    return order_id

def get_order_status(order_id: int, user_id: int) -> Optional[str]:
    """
    Получает статус заказа
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT status FROM orders WHERE id = ? AND user_id = ?',
        (order_id, user_id)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return None

def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает детали заказа: информацию о заказе и товарах в нем
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    # Получение информации о заказе
    cursor.execute(
        'SELECT id, user_id, order_date, status, total_price FROM orders WHERE id = ?',
        (order_id,)
    )
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return None
    
    # Получение информации о пользователе
    cursor.execute(
        'SELECT username, full_name FROM users WHERE user_id = ?',
        (order[1],)  # user_id at index 1
    )
    user_info = cursor.fetchone() or ("Неизвестно", "Неизвестный пользователь")
    
    # Получение товаров в заказе
    cursor.execute(
        '''
        SELECT p.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
        ''',
        (order_id,)
    )
    items = cursor.fetchall()
    
    conn.close()
    return {
        'order': order,
        'user_info': user_info,
        'items': items
    }

def get_all_orders(limit: int = 10, status_filter: Optional[str] = None) -> List[Tuple]:
    """
    Получает список всех заказов, опционально фильтруя по статусу
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    query = '''
    SELECT o.id, u.full_name, o.order_date, o.status, o.total_price, COUNT(oi.id) as items_count
    FROM orders o
    LEFT JOIN users u ON o.user_id = u.user_id
    LEFT JOIN order_items oi ON o.id = oi.order_id
    '''
    
    params = []
    if status_filter:
        query += ' WHERE o.status = ?'
        params.append(status_filter)
    
    query += '''
    GROUP BY o.id
    ORDER BY o.order_date DESC
    LIMIT ?
    '''
    params.append(limit)
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    conn.close()
    return orders

def update_order_status(order_id: int, new_status: str) -> bool:
    """
    Обновляет статус заказа
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE orders SET status = ? WHERE id = ?',
        (new_status, order_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if success:
        logger.info(f"Обновлен статус заказа {order_id} на '{new_status}'")
    
    return success

def register_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """
    Регистрирует пользователя в системе
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
        (user_id, username, full_name)
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Зарегистрирован пользователь: {user_id} ({full_name})")

def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором
    """
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result and result[0] == 1:
        return True
    return False

# Обработчики команд
@main_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start
    Отправляет приветственное сообщение и регистрирует пользователя в системе
    """
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в наш интернет-магазин.\n"
        f"Используйте команды:\n"
        f"/catalog - просмотр каталога товаров\n"
        f"/order - создать новый заказ\n"
        f"/status - проверить статус заказа"
    )
    
    # Добавление команды для администратора
    if is_admin(message.from_user.id):
        await message.answer(
            f"Дополнительные команды для администратора:\n"
            f"/stock - управление запасами товаров\n"
            f"/orders - просмотр и управление заказами"
        )

@main_router.message(Command('catalog'))
async def cmd_catalog(message: Message) -> None:
    """
    Обработчик команды /catalog
    Показывает список доступных товаров с описанием и ценой
    """
    products = get_products()
    
    if not products:
        await message.answer("В каталоге пока нет товаров.")
        return
    
    response = "📋 Каталог товаров:\n\n"
    
    for product in products:
        product_id, name, description, price, stock = product
        status = "✅ В наличии" if stock > 0 else "❌ Нет в наличии"
        response += f"🔹 <b>{name}</b> - {price:.2f} грн.\n{description}\nСтатус: {status}\n\n"
    
    await message.answer(response, parse_mode="HTML")

@order_router.message(Command('order'))
async def cmd_order(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /order
    Начинает процесс создания нового заказа
    """
    # Проверка наличия товаров
    products = get_products()
    available_products = [p for p in products if p[4] > 0]  # p[4] is stock
    
    if not available_products:
        await message.answer("Извините, но сейчас нет товаров в наличии.")
        return
    
    # Создание клавиатуры с доступными товарами
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{p[1]} - {p[3]:.2f} грн. (В наличии: {p[4]})",
                callback_data=f"add_to_cart:{p[0]}"
            )] for p in available_products
        ]
    )
    
    await message.answer("Выберите товар для добавления в корзину:", reply_markup=markup)
    await state.set_state(OrderStates.selecting_product)

# Обработчик выбора товара для корзины
@order_router.callback_query(F.data.startswith('add_to_cart:'), OrderStates.selecting_product)
async def process_add_to_cart(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора товара для добавления в корзину
    Запрашивает количество товара
    """
    product_id = int(callback_query.data.split(':')[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback_query.answer("Товар не найден")
        return
    
    # Сохранение выбранного товара в состояние
    await state.update_data(selected_product_id=product_id)
    data = await state.get_data()
    if 'cart' not in data:
        await state.update_data(cart={})
    
    # Запрос количества
    max_quantity = min(10, product[4])  # Ограничение до 10 или доступного количества
    buttons = []
    
    # Создаем ряды по 5 кнопок
    for i in range(1, max_quantity + 1, 5):
        row = []
        for j in range(i, min(i + 5, max_quantity + 1)):
            row.append(InlineKeyboardButton(
                text=str(j),
                callback_data=f"quantity:{j}"
            ))
        buttons.append(row)
    
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback_query.message.edit_text(
        f"Выбран товар: {product[1]}\nЦена: {product[3]:.2f} грн.\nУкажите количество:",
        reply_markup=markup
    )
    
    await callback_query.answer()
    await state.set_state(OrderStates.selecting_quantity)

# Обработчик выбора количества
@order_router.callback_query(F.data.startswith('quantity:'), OrderStates.selecting_quantity)
async def process_quantity_selection(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора количества товара
    Добавляет выбранное количество в корзину
    """
    quantity = int(callback_query.data.split(':')[1])
    
    # Получение данных из состояния
    data = await state.get_data()
    product_id = data['selected_product_id']
    product = get_product_by_id(product_id)
    
    if 'cart' not in data:
        cart = {}
    else:
        cart = data['cart']
    
    # Добавление в корзину или обновление количества
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    
    # Расчет итоговой суммы корзины
    cart_total = 0
    cart_details = []
    
    for pid, qty in cart.items():
        p = get_product_by_id(pid)
        if p:
            item_total = p[3] * qty  # price * quantity
            cart_total += item_total
            cart_details.append(f"{p[1]} x {qty} = {item_total:.2f} грн.")
    
    # Обновление данных состояния
    await state.update_data(cart=cart, cart_total=cart_total)
    
    # Показ содержимого корзины и опций
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить еще", callback_data="cart:add_more"),
                InlineKeyboardButton(text="Оформить заказ", callback_data="cart:checkout")
            ],
            [
                InlineKeyboardButton(text="Очистить корзину", callback_data="cart:clear")
            ]
        ]
    )
    
    await callback_query.message.edit_text(
        f"Товар добавлен в корзину! 🛒\n\n"
        f"Содержимое корзины:\n"
        f"{chr(10).join(cart_details)}\n\n"
        f"Итого: {cart_total:.2f} грн.",
        reply_markup=markup
    )
    
    await callback_query.answer()

# Обработчик действий с корзиной
@order_router.callback_query(F.data.startswith('cart:'), OrderStates.selecting_quantity)
async def process_cart_action(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик действий с корзиной (добавить еще, оформить заказ, очистить)
    """
    action = callback_query.data.split(':')[1]
    
    if action == 'add_more':
        # Показать каталог товаров снова
        products = get_products()
        available_products = [p for p in products if p[4] > 0]
        
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{p[1]} - {p[3]:.2f} руб. (В наличии: {p[4]})",
                    callback_data=f"add_to_cart:{p[0]}"
                )] for p in available_products
            ]
        )
        
        await callback_query.message.edit_text(
            "Выберите товар для добавления в корзину:",
            reply_markup=markup
        )
        
        await state.set_state(OrderStates.selecting_product)
    
    elif action == 'checkout':
        # Оформление заказа
        data = await state.get_data()
        cart = data['cart']
        cart_total = data['cart_total']
        
        # Проверка доступности товаров
        all_available = True
        for product_id, quantity in cart.items():
            product = get_product_by_id(product_id)
            if product and product[4] < quantity:  # stock < requested quantity
                all_available = False
                await callback_query.message.answer(
                    f"Извините, товара '{product[1]}' осталось только {product[4]} шт."
                )
        
        if not all_available:
            await callback_query.answer()
            return
        
        # Создание заказа
        order_id = create_order(
            callback_query.from_user.id,
            cart,
            cart_total
        )
        
        await callback_query.message.edit_text(
            f"✅ Заказ №{order_id} успешно оформлен!\n"
                            f"Сумма заказа: {cart_total:.2f} грн.\n\n"
            f"Вы можете проверить статус заказа командой /status"
        )
        
        # Очистка состояния
        await state.clear()
    
    elif action == 'clear':
        # Очистка корзины
        await state.update_data(cart={}, cart_total=0)
        
        await callback_query.message.edit_text(
            "Корзина очищена. Для создания нового заказа используйте команду /order"
        )
        
        await state.clear()
    
    await callback_query.answer()

@order_router.message(Command('status'))
async def cmd_status(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /status
    Запрашивает номер заказа для проверки статуса
    """
    await message.answer("Введите номер заказа для проверки статуса:")
    await state.set_state(OrderStates.checking_status)

@order_router.message(OrderStates.checking_status)
async def process_status_check(message: Message, state: FSMContext) -> None:
    """
    Обработчик ввода номера заказа
    Показывает статус и детали заказа
    """
    try:
        order_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заказа (число).")
        return
    
    # Проверка существования заказа
    status = get_order_status(order_id, message.from_user.id)
    
    if not status:
        await message.answer("Заказ не найден или принадлежит другому пользователю.")
        await state.clear()
        return
    
    # Получение деталей заказа
    details = get_order_details(order_id)
    
    if not details:
        await message.answer("Ошибка при получении деталей заказа.")
        await state.clear()
        return
    
    order = details['order']
    items = details['items']
    
    # Форматирование ответа
    response = f"📦 Заказ №{order[0]}\n"
    response += f"Дата: {order[2]}\n"
    response += f"Статус: {order[3]}\n\n"
    
    response += "Товары:\n"
    for item in items:
        name, quantity, price = item
        response += f"- {name} x {quantity} = {price * quantity:.2f} грн.\n"
    
    response += f"\nИтого: {order[4]:.2f} грн."
    
    await message.answer(response)
    await state.clear()

@admin_router.message(Command('stock'))
async def cmd_stock(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /stock (только для администратора)
    Показывает текущие запасы товаров и предлагает обновить их
    """
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    products = get_products()
    
    if not products:
        await message.answer("В каталоге пока нет товаров.")
        return
    
    # Показ текущих запасов
    response = "📊 Текущие запасы товаров:\n\n"
    
    for product in products:
        product_id, name, _, price, stock = product
        response += f"ID: {product_id} | {name} - {stock} шт. | {price:.2f} грн.\n"
    
    response += "\nДля обновления запасов выберите товар:"
    
    # Создание клавиатуры для обновления запасов
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Обновить запас: {p[1]}",
                callback_data=f"update_stock:{p[0]}"
            )] for p in products
        ]
    )
    
    await message.answer(response, reply_markup=markup)
    await state.set_state(AdminStates.updating_stock)

@admin_router.callback_query(F.data.startswith('update_stock:'), AdminStates.updating_stock)
async def process_stock_update_selection(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора товара для обновления запасов
    """
    # Проверка прав администратора
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("У вас нет прав для выполнения этой операции.")
        return
    
    product_id = int(callback_query.data.split(':')[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback_query.answer("Товар не найден")
        return
    
    # Сохранение выбранного товара в состояние
    await state.update_data(
        update_product_id=product_id,
        update_product_name=product[1],
        current_stock=product[4]
    )
    
    await callback_query.message.edit_text(
        f"Товар: {product[1]}\nТекущий запас: {product[4]} шт.\n\n"
        f"Введите новое количество товара на складе:"
    )
    
    await callback_query.answer()
    await state.set_state(AdminStates.entering_new_stock)

@admin_router.message(AdminStates.entering_new_stock)
async def process_new_stock_value(message: Message, state: FSMContext) -> None:
    """
    Обработчик ввода нового количества товара на складе
    """
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой операции.")
        await state.clear()
        return
    
    try:
        new_stock = int(message.text.strip())
        if new_stock < 0:
            raise ValueError("Количество не может быть отрицательным")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное количество (целое неотрицательное число).")
        return
    
    # Получение данных из состояния
    data = await state.get_data()
    product_id = data['update_product_id']
    product_name = data['update_product_name']
    current_stock = data['current_stock']
    
    # Обновление запаса в базе данных
    update_product_stock(product_id, new_stock)
    
    await message.answer(
        f"✅ Запас товара '{product_name}' обновлен!\n"
        f"Было: {current_stock} шт.\n"
        f"Стало: {new_stock} шт."
    )
    
    await state.clear()

@admin_router.message(Command('orders'))
async def cmd_orders(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /orders (только для администратора)
    Показывает список последних заказов с возможностью фильтрации
    """
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    # Создание клавиатуры для выбора фильтра статуса
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Все заказы", callback_data="filter_orders:all"),
                InlineKeyboardButton(text="Новые", callback_data="filter_orders:Новый")
            ],
            [
                InlineKeyboardButton(text="В обработке", callback_data="filter_orders:В обработке"),
                InlineKeyboardButton(text="Отправлен", callback_data="filter_orders:Отправлен")
            ],
            [
                InlineKeyboardButton(text="Доставлен", callback_data="filter_orders:Доставлен"),
                InlineKeyboardButton(text="Отменен", callback_data="filter_orders:Отменен")
            ]
        ]
    )
    
    await message.answer("Выберите фильтр для просмотра заказов:", reply_markup=markup)
    await state.set_state(AdminStates.viewing_orders)

@admin_router.callback_query(F.data.startswith('filter_orders:'), AdminStates.viewing_orders)
async def process_orders_filter(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора фильтра для просмотра заказов
    """
    # Проверка прав администратора
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("У вас нет прав для выполнения этой операции.")
        return
    
    filter_value = callback_query.data.split(':')[1]
    
    # Получение заказов с выбранным фильтром
    status_filter = None if filter_value == 'all' else filter_value
    orders = get_all_orders(limit=15, status_filter=status_filter)
    
    if not orders:
        await callback_query.message.edit_text("Заказы не найдены.")
        await callback_query.answer()
        await state.clear()
        return
    
    # Вывод списка заказов
    response = f"📋 Список заказов (фильтр: {filter_value}):\n\n"
    
    for order in orders:
        order_id, customer_name, order_date, status, total_price, items_count = order
        response += (
            f"🔸 <b>Заказ №{order_id}</b>\n"
            f"Клиент: {customer_name}\n"
            f"Дата: {order_date}\n"
            f"Статус: {status}\n"
            f"Сумма: {total_price:.2f} грн.\n"
            f"Позиций: {items_count}\n\n"
        )
    
    # Добавление инструкции для просмотра деталей
    response += "Для просмотра деталей и управления заказом, введите номер заказа:"
    
    await callback_query.message.edit_text(response, parse_mode="HTML")
    await callback_query.answer()
    await state.set_state(AdminStates.viewing_order_details)

@admin_router.message(AdminStates.viewing_order_details)
async def process_order_details_request(message: Message, state: FSMContext) -> None:
    """
    Обработчик запроса деталей заказа по его номеру
    """
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой операции.")
        await state.clear()
        return
    
    try:
        order_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заказа (число).")
        return
    
    # Получение деталей заказа
    details = get_order_details(order_id)
    
    if not details:
        await message.answer("Заказ с указанным номером не найден.")
        return
    
    order = details['order']
    user_info = details['user_info']
    items = details['items']
    
    # Форматирование ответа с деталями заказа
    response = f"📦 <b>Детали заказа №{order[0]}</b>\n\n"
    
    # Информация о пользователе
    response += f"👤 <b>Клиент:</b> {user_info[1]}"
    if user_info[0]:  # username
        response += f" (@{user_info[0]})"
    response += f"\n<b>ID пользователя:</b> {order[1]}\n\n"
    
    # Информация о заказе
    response += f"<b>Дата заказа:</b> {order[2]}\n"
    response += f"<b>Статус:</b> {order[3]}\n\n"
    
    # Товары в заказе
    response += "<b>Товары в заказе:</b>\n"
    total_items = 0
    for item in items:
        name, quantity, price = item
        total_items += quantity
        response += f"• {name} x {quantity} = {price * quantity:.2f} грн.\n"
    
    response += f"\n<b>Всего товаров:</b> {total_items} шт."
    response += f"\n<b>Итого:</b> {order[4]:.2f} грн."
    
    # Клавиатура для управления статусом заказа
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="В обработке", callback_data=f"status:{order_id}:В обработке"),
                InlineKeyboardButton(text="Отправлен", callback_data=f"status:{order_id}:Отправлен")
            ],
            [
                InlineKeyboardButton(text="Доставлен", callback_data=f"status:{order_id}:Доставлен"),
                InlineKeyboardButton(text="Отменен", callback_data=f"status:{order_id}:Отменен")
            ],
            [
                InlineKeyboardButton(text="« Назад к списку", callback_data="filter_orders:all")
            ]
        ]
    )
    
    # Сохраняем ID заказа в состоянии
    await state.update_data(current_order_id=order_id)
    
    await message.answer(response, reply_markup=markup, parse_mode="HTML")
    await state.set_state(AdminStates.changing_order_status)

@admin_router.callback_query(F.data.startswith('status:'), AdminStates.changing_order_status)
async def process_status_change(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик изменения статуса заказа
    """
    # Проверка прав администратора
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("У вас нет прав для выполнения этой операции.")
        return
    
    # Парсинг данных callback
    _, order_id, new_status = callback_query.data.split(':')
    order_id = int(order_id)
    
    # Обновление статуса заказа
    success = update_order_status(order_id, new_status)
    
    if success:
        await callback_query.answer(f"Статус заказа №{order_id} изменен на '{new_status}'")
        
        # Обновление сообщения с деталями заказа
        details = get_order_details(order_id)
        
        if details:
            order = details['order']
            user_info = details['user_info']
            items = details['items']
            
            response = f"📦 <b>Детали заказа №{order[0]}</b>\n\n"
            
            # Информация о пользователе
            response += f"👤 <b>Клиент:</b> {user_info[1]}"
            if user_info[0]:  # username
                response += f" (@{user_info[0]})"
            response += f"\n<b>ID пользователя:</b> {order[1]}\n\n"
            
            # Информация о заказе с обновленным статусом
            response += f"<b>Дата заказа:</b> {order[2]}\n"
            response += f"<b>Статус:</b> {order[3]} ✅\n\n"
            
            # Товары в заказе
            response += "<b>Товары в заказе:</b>\n"
            total_items = 0
            for item in items:
                name, quantity, price = item
                total_items += quantity
                response += f"• {name} x {quantity} = {price * quantity:.2f} грн.\n"
            
            response += f"\n<b>Всего товаров:</b> {total_items} шт."
            response += f"\n<b>Итого:</b> {order[4]:.2f} грн."
            
            # Обновленная клавиатура
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="В обработке", callback_data=f"status:{order_id}:В обработке"),
                        InlineKeyboardButton(text="Отправлен", callback_data=f"status:{order_id}:Отправлен")
                    ],
                    [
                        InlineKeyboardButton(text="Доставлен", callback_data=f"status:{order_id}:Доставлен"),
                        InlineKeyboardButton(text="Отменен", callback_data=f"status:{order_id}:Отменен")
                    ],
                    [
                        InlineKeyboardButton(text="« Назад к списку", callback_data="filter_orders:all")
                    ]
                ]
            )
            
            await callback_query.message.edit_text(response, reply_markup=markup, parse_mode="HTML")
    else:
        await callback_query.answer("Не удалось обновить статус заказа.")

@admin_router.callback_query(F.data.startswith('filter_orders:'), AdminStates.changing_order_status)
async def back_to_orders_list(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик возврата к списку заказов из просмотра деталей
    """
    # Перенаправляем на обработчик фильтрации заказов
    await state.set_state(AdminStates.viewing_orders)
    await process_orders_filter(callback_query, state)

async def main() -> None:
    # Инициализация базы данных
    init_db()
    
    # Настройка хранилища состояний
    storage = MemoryStorage()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(main_router)
    dp.include_router(order_router)
    dp.include_router(admin_router)
    
    # Запуск бота
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")