import asyncio
import logging
import sqlite3
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = '8256923838:AAHDGyhHPEIngHAzTKAAXh0tiEH-rwpCXZk'
WEATHER_API_KEY = '0a464e64a7076ed7db04926c95fe758b' 
# Налаштування логування (Пункт 8)
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАНИХ (Пункт 9) ---
def init_db():
    conn = sqlite3.connect('sports_shop.db')
    cursor = conn.cursor()
    # Таблиця користувачів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- КЛАВІАТУРИ (Пункт 5) ---
# Головне меню (Reply)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏋️ Підібрати інвентар"), KeyboardButton(text="🌤 Погода для спорту")],
        [KeyboardButton(text="ℹ️ Про нас"), KeyboardButton(text="🆘 Допомога")]
    ],
    resize_keyboard=True
)

# Меню вибору спорту (Inline)
def get_sport_keyboard():
    buttons = [
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="sport_football")],
        [InlineKeyboardButton(text="🎾 Теніс", callback_data="sport_tennis")],
        [InlineKeyboardButton(text="🥊 Бокс", callback_data="sport_boxing")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- РОБОТА З API (Пункт 7) ---
def get_weather(city="Kyiv"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ua"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"Погода в Києві: {temp}°C, {desc}."
        else:
            return "Не вдалося отримати погоду."
    except Exception as e:
        logging.error(f"API Error: {e}")
        return "Помилка з'єднання з сервером погоди."

# --- ОБРОБНИКИ КОМАНД (Пункт 2, 3) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Зберігаємо юзера в БД
    conn = sqlite3.connect('sports_shop.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()
    
    await message.answer(f"Привіт, {message.from_user.first_name}! Я допоможу підібрати спортивний інвентар.", reply_markup=main_menu)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Оберіть категорію в меню, щоб отримати рекомендації.")

@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    await message.answer("Цей бот створено в рамках лабораторної роботи на тему Aiogram.")

# --- ОБРОБКА ТЕКСТУ ТА КНОПОК МЕНЮ ---

@dp.message(F.text == "🏋️ Підібрати інвентар")
async def process_equipment(message: types.Message):
    await message.answer("Який вид спорту вас цікавить?", reply_markup=get_sport_keyboard())

@dp.message(F.text == "🌤 Погода для спорту")
async def process_weather(message: types.Message):
    weather_info = get_weather()
    rec = "Можна бігати на вулиці! 🏃" if "дощ" not in weather_info else "Краще піти в зал 🏠"
    await message.answer(f"{weather_info}\n\nПорада: {rec}")

@dp.message(F.text == "ℹ️ Про нас")
async def process_about(message: types.Message):
    await message.answer("Ми - найкращий віртуальний магазин спорттоварів.")

# --- ОБРОБКА INLINE КНОПОК (Пункт 6) ---

@dp.callback_query(F.data.startswith("sport_"))
async def callback_sport(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action == "football":
        text = "Для футболу вам знадобляться:\n- Бутси (Nike/Adidas)\n- М'яч (розмір 5)\n- Щитки"
        img_url = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg"
    elif action == "tennis":
        text = "Для тенісу вам знадобляться:\n- Ракетка (Wilson/Head)\n- Набір м'ячів\n- Зручні кросівки"
    elif action == "boxing":
        text = "Для боксу вам знадобляться:\n- Рукавиці (12-14 унцій)\n- Капа\n- Бинти"
    
    await callback.message.answer(text)
    await callback.answer() # Завершуємо анімацію завантаження кнопки

# --- ОБРОБКА ФОТО (Пункт 4) ---

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.reply("Круте фото! Це ви на тренуванні? 💪")

# --- ОБРОБКА ІНШОГО (Ехо) ---
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("Я не розумію цю команду. Скористайтеся меню.")

# --- ЗАПУСК ---
async def main():
    print("Бот запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):

        print("Бот зупинено")
