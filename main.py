import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Tokeningizni shu yerga yozing
TOKEN = "9160638068:AAGtVpgYjmPJxStxsJIT89q9jxvaejfE8kQ"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

# Admin ID raqami (O'zingizning Telegram ID'ingizni yozing)
ADMIN_ID = 123456789  # Buni o'z ID'ingizga o'zgartiring!

# Vaqtinchalik baza (Real loyihada SQLite/PostgreSQL ishlatiladi)
users_db = {}  # user_id: {name, age, gender, premium_until, invited_count, promo_code}
active_chats = {}  # chat_id: partner_id

# Promo kodlar bazasi
valid_promos = {"PREMIUM7": 7}  # 7 kunlik promo


# Holatlar (States)
class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()


# /start buyrug'i
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Agar foydalanuvchi birinchi marta kirayotgan bo'lsa
    if user_id not in users_db:
        users_db[user_id] = {
            "name": "Noma'lum",
            "age": "Noma'lum",
            "gender": "Noma'lum",
            "has_premium": False,
            "invited_count": 0
        }
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("💬 Suhbatdosh topish"))
    markup.row(KeyboardButton("👤 Anketam"), KeyboardButton("⚙️ Anketani sozlash"))
    markup.row(KeyboardButton("💎 Premium olish"), KeyboardButton("🎁 Promo-kod ishlatish"))
    
    # Admin uchun maxsus tugma
    if user_id == ADMIN_ID:
        markup.row(KeyboardButton("👑 Admin Panel"))

    await message.answer("Assalomu alaykum! Anonim chat botimizga xush kelibsiz. 🤖\n\nDavom etish uchun menyudan kerakli tugmani tanlang:", reply_markup=markup)


# Anketani sozlash tugmasi
@dp.message_handler(text="⚙️ Anketani sozlash")
async def setup_profile(message: types.Message):
    await message.answer("Keling, anketangizni sozlaymiz. Ismingizni kiriting:")
    await ProfileStates.waiting_for_name.set()


@dp.message_handler(state=ProfileStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer("Yoshingizni kiriting (masalan: 18):")
    await ProfileStates.waiting_for_age.set()


@dp.message_handler(state=ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(KeyboardButton("👨 Erkak"), KeyboardButton("👩 Ayol"))
    await message.answer("Jinsingizni tanlang:", reply_markup=markup)
    await ProfileStates.waiting_for_gender.set()


@dp.message_handler(state=ProfileStates.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with state.proxy() as data:
        name = data['name']
        age = data['age']
        gender = message.text
        
    users_db[user_id].update({
        "name": name,
        "age": age,
        "gender": gender
    })
    
    await state.finish()
    await message.answer(f"✅ Anketangiz muvaffaqiyatli saqlandi!\n\n📝 Ism: {name}\n🎂 Yosh: {age}\n🚻 Jins: {gender}", reply_markup=types.ReplyKeyboardRemove())
    await cmd_start(message)


# Anketamni ko'rish
@dp.message_handler(text="👤 Anketam")
async def show_my_profile(message: types.Message):
    user = users_db.get(message.from_user.id, {"name": "Kiritilmagan", "age": "-", "gender": "-"})
    await message.answer(f"Sizning anketangiz:\n\nIsm: {user['name']}\nYosh: {user['age']}\nJins: {user['gender']}")


# Premium bo'limi
@dp.message_handler(text="💎 Premium olish")
async def premium_info(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    text = (
        "💎 **Premium imkoniyatlari:**\n"
        "Suhbatdoshning jinsi, yoshi va ismini ko'rish imkoniyati!\n\n"
        "Uni olish uchun 2 ta yo'l bor:\n"
        "1️⃣ 5000 so'm to'lov qilish (Admin bilan bog'laning: @admin)\n"
        "2️⃣ Do'stingizni taklif qiling! Har 1 ta do'st uchun 7 kunlik premium beriladi.\n\n"
        f"🔗 Sizning taklif havolangiz:\n`{ref_link}`"
    )
    await message.answer(text, parse_mode="Markdown")


# Promo-kod ishlatish
@dp.message_handler(text="🎁 Promo-kod ishlatish")
async def promo_prompt(message: types.Message):
    await message.answer("Iltimos, promo-kodni kiriting:")
    # Bu yerda oddiy holatda matnni tekshiramiz


@dp.message_handler(lambda message: message.text in valid_promos)
async def apply_promo(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id]["has_premium"] = True
    await message.answer("🎉 Tabriklaymiz! Promo-kod muvaffaqiyatli faollashtirildi va sizga Premium berildi!")


# Admin panel
@dp.message_handler(text="👑 Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:+998941948482
        return await message.answer("Siz admin emassiz!")
        
    total_users = len(users_db)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"))
    markup.add(InlineKeyboardButton("📢 Xabar yuborish (Broadcast)", callback_data="admin_broadcast"))
    
    await message.answer(f"👑 Admin paneliga xush kelibsiz!\n\nJami foydalanuvchilar: {total_users} ta", reply_markup=markup)


@dp.callback_query_handler(text="admin_stats")
async def admin_stats_callback(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer(f"📊 Bot statistikasi:\nJami foydalanuvchilar: {len(users_db)} ta")
    await call.answer()


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
                        
