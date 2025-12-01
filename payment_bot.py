import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# --- КОНФІГУРАЦІЯ ---
# Вставте сюди ваші токени!
API_TOKEN = '8256923838:AAHgIWshAaPkD_6Son-VFHQsKylpjgkqO0c'      
PAYMENT_TOKEN = '1877036958:TEST:c6a5279d9339d736f1ed844566a58fd411ab3068'   

# Налаштування логування
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_balance(user_id, amount):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# --- КОМАНДИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Це фінансовий бот. 💰\nКоманди:\n/register - Зареєструватися\n/balance - Мій баланс\n/topup - Поповнити рахунок")

@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        await message.answer("Ви вже зареєстровані! ✅")
    else:
        cursor.execute('INSERT INTO users (user_id, username, balance) VALUES (?, ?, 0)', (user_id, message.from_user.username))
        conn.commit()
        await message.answer("Реєстрація успішна! Ваш баланс: 0 грн. 🎉")
    conn.close()

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    balance = get_user_balance(message.from_user.id)
    if balance is not None:
        await message.answer(f"💳 Ваш поточний баланс: {balance / 100:.2f} UAH")
    else:
        await message.answer("Ви не зареєстровані. Натисніть /register")

# --- ПЛАТІЖНА СИСТЕМА ---
@dp.message(Command("topup"))
async def cmd_topup(message: types.Message):
    if get_user_balance(message.from_user.id) is None:
        await message.answer("Спочатку зареєструйтесь через /register")
        return

    prices = [LabeledPrice(label="Поповнення балансу", amount=10000)] # 100.00 UAH
    
    await bot.send_invoice(
        message.chat.id,
        title="Поповнення гаманця",
        description="Поповнення внутрішнього рахунку на 100 грн",
        provider_token=PAYMENT_TOKEN,
        currency="UAH",
        photo_url="https://cdn-icons-png.flaticon.com/512/2454/2454269.png",
        photo_height=512, photo_width=512, photo_size=512,
        is_flexible=False,
        prices=prices,
        start_parameter="topup-balance",
        payload="internal-bot-payload"
    )

@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    total = message.successful_payment.total_amount
    update_balance(message.from_user.id, total)
    await message.answer(f"✅ Оплата пройшла успішно! Баланс поповнено на {total // 100} UAH.")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
