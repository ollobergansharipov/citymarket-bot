import asyncio
import sqlite3
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, FSInputFile
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= BOT =================
TOKEN = "8490794543:AAG6Bw4bGp0ut_N30JqaVPDRHYgFSwttiac"  # <-- Bu yerga bot tokeningizni yozing
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER,
    product TEXT,
    price INTEGER,
    quantity INTEGER,
    PRIMARY KEY (user_id, product)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    phone TEXT,
    items TEXT,
    status TEXT
)
""")
conn.commit()

# ================= MENULAR =================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🥤 Ichimliklar")],
        [KeyboardButton(text="🍰 Qandolat mahsulotlari")],
        [KeyboardButton(text="🛒 Savat")]
    ],
    resize_keyboard=True
)

phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Orqaga")]
    ],
    resize_keyboard=True
)

# ================= ADMIN =================
ADMINS = [5279279010]  # <-- O'Z IDINGNI YOZ

def admin_order_buttons(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{order_id}")
            ]
        ]
    )

# ================= START =================
@dp.message(CommandStart())
async def start_handler(message: Message):
    logo = FSInputFile("IMG/rasmiy rasm.jpg")
    await message.answer_photo(
        photo=logo,
        caption="Assalomu aleykum!!! 🛒CITY MARKET do'konimizning rasmiy botiga xush kelibsiz!\nBo‘limni tanlang:",
        reply_markup=main_menu
    )

# ================= ADD TO CART =================
def add_to_cart(user_id, product, price):
    cursor.execute(
        "SELECT quantity FROM cart WHERE user_id=? AND product=?",
        (user_id, product)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE cart SET quantity=quantity+1 WHERE user_id=? AND product=?",
            (user_id, product)
        )
    else:
        cursor.execute(
            "INSERT INTO cart VALUES (?, ?, ?, 1)",
            (user_id, product, price)
        )
    conn.commit()

# ================= PRODUCTS =================
@dp.message(F.text == "🥤 Ichimliklar")
async def drinks(message: Message):
    cola_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Savatga", callback_data="add_Coca-Cola_15000")]
        ]
    )
    cola = FSInputFile("IMG/Kola.jpg")
    await message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
    await message.answer_photo(
        photo=cola,
        caption="🥤 Coca-Cola 1.5L\n💰 15 000 so‘m",
        reply_markup=cola_kb
    )
@dp.message(F.text == "🍰 Qandolat mahsulotlari")
async def sweets(message: Message):
    choco_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Savatga", callback_data="add_Millenium_8000")]
        ]
    )
    choco = FSInputFile("IMG/Millenium.jpg")
    await message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
    await message.answer_photo(
        photo=choco,
        caption="🍫 Millenium shokolad\n💰 8 000 so‘m",
        reply_markup=choco_kb
    )

# ================= ADD CALLBACK =================
@dp.callback_query(F.data.startswith("add_"))
async def add_callback(call: CallbackQuery):
    _, name, price = call.data.split("_")
    add_to_cart(call.from_user.id, name, int(price))
    await call.answer("✅ Savatga qo‘shildi")

# ================= CART HANDLER =================
async def show_cart(message: Message):
    cursor.execute(
        "SELECT product, price, quantity FROM cart WHERE user_id=?",
        (message.from_user.id,)
    )
    items = cursor.fetchall()

    if not items:
        await message.answer("🛒 Savat")
        return

    total = sum(price * qty for _, price, qty in items)
    text = "🛒 Savatingiz:\n\n"
    inline_keyboard = []

    for product, price, qty in items:
        text += f"{product} x{qty} = {price * qty} so‘m\n"
        inline_keyboard.append([
            InlineKeyboardButton(text=f"➖ {product}", callback_data=f"decrease_{product}"),
            InlineKeyboardButton(text=str(qty), callback_data="none"),
            InlineKeyboardButton(text=f"➕ {product}", callback_data=f"increase_{product}"),
            InlineKeyboardButton(text="❌", callback_data=f"remove_{product}")
        ])
    await message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
    inline_keyboard.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="order")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    await message.answer(f"{text}\n💰 Jami: {total} so‘m", reply_markup=keyboard)

# ================= SHOW CART MESSAGE =================
@dp.message(F.text == "🛒 Savat")
async def show_cart_message(message: Message):
    await show_cart(message)

# ================= INCREASE / DECREASE / REMOVE =================
@dp.callback_query(F.data.startswith("increase_"))
async def increase_item(call: CallbackQuery):
    product = call.data.split("_")[1]
    cursor.execute(
        "UPDATE cart SET quantity = quantity + 1 WHERE user_id=? AND product=?",
        (call.from_user.id, product)
    )
    conn.commit()
    await call.answer("✅ Miqdor oshirildi")
    await show_cart(call.message)

@dp.callback_query(F.data.startswith("decrease_"))
async def decrease_item(call: CallbackQuery):
    product = call.data.split("_")[1]
    cursor.execute(
        "SELECT quantity FROM cart WHERE user_id=? AND product=?",
        (call.from_user.id, product)
    )
    qty = cursor.fetchone()[0]
    if qty > 1:
        cursor.execute(
            "UPDATE cart SET quantity = quantity - 1 WHERE user_id=? AND product=?",
            (call.from_user.id, product)
        )
    else:
        cursor.execute(
            "DELETE FROM cart WHERE user_id=? AND product=?",
            (call.from_user.id, product)
        )
    conn.commit()
    await call.answer("✅ Miqdor yangilandi")
    await show_cart(call.message)

@dp.callback_query(F.data.startswith("remove_"))
async def remove_item(call: CallbackQuery):
    product = call.data.split("_")[1]
    cursor.execute(
        "DELETE FROM cart WHERE user_id=? AND product=?",
        (call.from_user.id, product)
    )
    conn.commit()
    await call.answer("❌ Mahsulot o‘chirildi")
    await show_cart(call.message)

# ================= PAYMENT TYPE =================
def payment_type_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 Naqd to‘lov", callback_data="cash"),
                InlineKeyboardButton(text="💳 Onlayn to‘lov", callback_data="online")
            ]
        ]
    )
    return keyboard

# ================= ORDER =================
@dp.callback_query(F.data == "order")
async def order(call: CallbackQuery):
    await call.message.answer(
        "To‘lov turini tanlang:",
        reply_markup=payment_type_keyboard()
    )
    await message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
    await call.answer()

# ================= ONLINE PAYMENT FSM =================
class OnlinePaymentStates(StatesGroup):
    waiting_for_card = State()
    waiting_for_expiry = State()
    waiting_for_cvv = State()

# ================= PAYMENT TYPE CALLBACK =================
@dp.callback_query(F.data.in_({"cash", "online"}))
async def process_payment_type(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    # Naqd to‘lov
    if call.data == "cash":
        await call.message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
        await call.message.answer(
            "✅ Siz naqd pul to'lov usulini tanladingiz.\nTo'lovni mahsulot yetib borganda qilasiz\n"
            "📞 Iltimos, telefon raqamingizni yuboring:",
            reply_markup=phone_kb
        )
    # Onlayn to‘lov FSM
    else:
        cursor.execute("SELECT product, price, quantity FROM cart WHERE user_id=?", (user_id,))
        items = cursor.fetchall()
        if not items:
            await call.message.answer("🛒 Savat bo‘sh")
            return

        items_text = ""
        total = 0
        for product, price, qty in items:
            items_text += f"{product} x{qty}\n"
            total += price * qty

        await state.update_data(items_text=items_text, total=total)
        await call.message.answer("💳 Karta raqamingizni kiriting (16 raqam):")
        await state.set_state(OnlinePaymentStates.waiting_for_card)
    await call.message.answer("⬅️ Orqaga tugmasi orqali menyuga qaytishingiz mumkin", reply_markup=back_kb)
    await call.answer()

# ================= FSM HANDLERS =================
@dp.message(OnlinePaymentStates.waiting_for_card)
async def online_card_number(message: Message, state: FSMContext):
    card = message.text.replace(" ", "")
    if not re.fullmatch(r"\d{16}", card):
        await message.answer("❌ Karta raqam noto‘g‘ri. Iltimos 16 raqam kiriting.")
        return
    await state.update_data(card=card)
    await message.answer("✅ Karta raqami qabul qilindi.\nIltimos amal qilish muddatini kiriting (MM/YY):")
    await state.set_state(OnlinePaymentStates.waiting_for_expiry)

@dp.message(OnlinePaymentStates.waiting_for_expiry)
async def online_expiry_date(message: Message, state: FSMContext):
    expiry = message.text.strip()
    if not re.fullmatch(r"(0[1-9]|1[0-2])/([2-9][0-9])", expiry):
        await message.answer("❌ Amal qilish muddati noto‘g‘ri. Format: MM/YY, masalan 12/26")
        return
    await state.update_data(expiry=expiry)
    await message.answer("✅ Amal qilish muddati qabul qilindi.\nIltimos CVV kodini kiriting (3 raqam):")
    await state.set_state(OnlinePaymentStates.waiting_for_cvv)

@dp.message(OnlinePaymentStates.waiting_for_cvv)
async def online_cvv(message: Message, state: FSMContext):
    cvv = message.text.strip()
    if not re.fullmatch(r"\d{3}", cvv):
        await message.answer("❌ CVV noto‘g‘ri, 3 raqam kiriting.")
        return

    data = await state.get_data()
    items_text = data['items_text']
    total = data['total']
    card = data['card']
    expiry = data['expiry']

    # ================= TO'LOV SIMULATSIYASI =================
    await message.answer(f"✅ To‘lov qabul qilindi!\n💳 Karta: {card}\n⏳ Amal qilish muddati: {expiry}\n💰 Summasi: {total} so‘m\nBuyurtmangiz tasdiqlandi!")

    # Buyurtmani saqlash
    cursor.execute(
        "INSERT INTO orders (user_id, phone, items, status) VALUES (?, ?, ?, ?)",
        (message.from_user.id, "", items_text, "To'langan")
    )
    conn.commit()
    order_id = cursor.lastrowid

    for admin in ADMINS:
        await bot.send_message(
            admin,
            f"🆕 BUYURTMA #{order_id}\n\n{items_text}",
            reply_markup=admin_order_buttons(order_id)
        )

    # Savatni tozalash
    cursor.execute("DELETE FROM cart WHERE user_id=?", (message.from_user.id,))
    conn.commit()
    await state.clear()

# ================= PHONE =================
@dp.message(F.contact)
async def get_phone(message: Message):
    phone = message.contact.phone_number
    user_id = message.from_user.id

    cursor.execute(
        "SELECT product, price, quantity FROM cart WHERE user_id=?",
        (user_id,)
    )
    items = cursor.fetchall()

    if not items:
        await message.answer("🛒 Savat bo‘sh")
        return

    items_text = ""
    total = sum(price * qty for _, price, qty in items)
    for product, price, qty in items:
        items_text += f"{product} x{qty}\n"

    cursor.execute(
        "INSERT INTO orders (user_id, phone, items, status) VALUES (?, ?, ?, ?)",
        (user_id, phone, items_text, "Kutilmoqda")
    )
    conn.commit()
    order_id = cursor.lastrowid

    for admin in ADMINS:
        await bot.send_message(
            admin,
            f"🆕 BUYURTMA #{order_id}\n📞 {phone}\n\n{items_text}",
            reply_markup=admin_order_buttons(order_id)
        )

    cursor.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()

    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi!\n💰 Jami summa: {total} so‘m\n"
        "📦 Mahsulot yetkazilganda naqd pulni to‘lashingiz mumkin.",
        reply_markup=main_menu
    )

# ================= ADMIN CONFIRM / REJECT =================
@dp.callback_query(F.data.startswith(("confirm_", "reject_")))
async def admin_order_callback(call: CallbackQuery):
    action, order_id = call.data.split("_")
    order_id = int(order_id)

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?", (order_id,))
    user_id = cursor.fetchone()[0]

    if action == "confirm":
        cursor.execute("UPDATE orders SET status='Tasdiqlangan' WHERE order_id=?", (order_id,))
        user_msg = "✅ Buyurtmangiz tasdiqlandi!"
    else:
        cursor.execute("UPDATE orders SET status='Rad etilgan' WHERE order_id=?", (order_id,))
        user_msg = "❌ Buyurtmangiz rad etildi"

    conn.commit()
    await bot.send_message(user_id, user_msg)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer(f"Buyurtma {action}")

# ================= ADMIN VIEW ALL ORDERS =================
@dp.message(F.text == "/orders")
async def admin_orders_panel(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz bu buyurtmalarni ko‘ra olmaysiz.")
        return

    cursor.execute("SELECT order_id, user_id, phone, items, status FROM orders ORDER BY order_id DESC")
    all_orders = cursor.fetchall()

    if not all_orders:
        await message.answer("Hozir hech qanday buyurtma yo'q 📭")
        return

    for order_id, user_id, phone, items, status in all_orders:
        text = (
            f"🆔 Buyurtma #{order_id}\n"
            f"👤 Foydalanuvchi ID: {user_id}\n"
            f"📞 Telefon: {phone}\n"
            f"🛒 Mahsulotlar:\n{items}\n"
            f"📌 Holati: {status}"
        )

        markup = InlineKeyboardMarkup()
        if status in ["Kutilmoqda", "To'langan"]:
            markup.add(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
            )

        await message.answer(text, reply_markup=markup)
@dp.message(F.text == "⬅️ Orqaga")
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu)
# ================= RUN =================
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())