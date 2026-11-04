import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Tokeningiz
TOKEN = "9050259079:AAH5xhCPSnDZf9nAGD-TSRq-ZwVeRIEAOeE"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Foydalanuvchi anketalari va holatlari uchun vaqtinchalik xotira
users_data = {}  # {user_id: {"name": ..., "age": ..., "gender": ...}}
waiting_users = []  # Qidiruvdagi foydalanuvchilar navbati
active_chats = {}  # {user_id: partner_id}

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    in_chat = State()
    searching = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Agar chatda bo'lsa, sherigini ogohlantirib uzamiz
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id in active_chats:
            active_chats.pop(partner_id, None)
            try:
                await bot.send_message(partner_id, "❌ Suhbatdosh chatni tark etdi.\nYangi qidiruv uchun /start ni bosing.")
            except:
                pass

    if user_id in waiting_users:
        waiting_users.remove(user_id)

    await state.clear()

    # Agar foydalanuvchi allaqachon anketa to'ldirgan bo'lsa
    if user_id in users_data:
        kb = [
            [types.KeyboardButton(text="👥 Suhbatdosh qidirish")],
            [types.KeyboardButton(text="👤 Profilim")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Assalomu alaykum! Suhbatdosh topish uchun quyidagi tugmani bosing:", reply_markup=keyboard)
    else:
        # Yangi foydalanuvchi anketa to'ldirishni boshlaydi
        await state.set_state(Form.waiting_for_name)
        await message.answer("Salom! Taninishuv botiga xush kelibsiz.\nIsmingizni kiriting:")

@dp.message(Form.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.waiting_for_age)
    await message.answer("Yoshingiz nechida? (Masalan: 18)")

@dp.message(Form.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, yoshingizni faqat raqamlar bilan kiriting (masalan: 18):")
        return
    await state.update_data(age=message.text)
    await state.set_state(Form.waiting_for_gender)
    
    kb = [
        [types.KeyboardButton(text="👦 O'g'il bola"), types.KeyboardButton(text="👧 Qiz bola")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Jinsingizni tanlang:", reply_markup=keyboard)

@dp.message(Form.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text
    if gender not in ["👦 O'g'il bola", "👧 Qiz bola"]:
        await message.answer("Iltimos, tugmalardan birini bosing!")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    
    # Anketani saqlaymiz
    users_data[user_id] = {
        "name": data["name"],
        "age": data["age"],
        "gender": gender
    }

    await state.clear()
    kb = [
        [types.KeyboardButton(text="👥 Suhbatdosh qidirish")],
        [types.KeyboardButton(text="👤 Profilim")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("✅ Anketangiz muvaffaqiyatli saqlandi!", reply_markup=keyboard)

@dp.message(F.text == "👤 Profilim")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data:
        p = users_data[user_id]
        await message.answer(f"Sizning profilingiz:\n\nIsmi: {p['name']}\nYoshi: {p['age']}\nJinsi: {p['gender']}")
    else:
        await message.answer("Anketangiz topilmadi. Qaytadan boshlash uchun /start ni bosing.")

@dp.message(F.text == "👥 Suhbatdosh qidirish")
async def start_search(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id not in users_data:
        await message.answer("Avval anketangizni to'ldiring. /start ni bosing.")
        return

    if user_id in waiting_users:
        await message.answer("⏳ Siz allaqachon qidiruvdasiz...")
        return

    if user_id in active_chats:
        await message.answer("Siz allaqachon suhbatdasiz! Yangi suhbat uchun /next, to'xtatish uchun /stop ni bosing.")
        return

    await state.set_state(Form.searching)

    if waiting_users:
        # Navbatdan sherik topamiz
        partner_id = waiting_users.pop(0)
        
        # O'zaro bog'laymiz
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        # Ikkala foydalanuvchining anketasini olamiz
        user_p = users_data[user_id]
        partner_p = users_data[partner_id]

        # Chat buyruqlari klaviaturasi
        kb = [
            [types.KeyboardButton(text="/next"), types.KeyboardButton(text="/stop")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        # 1-foydalanuvchiga sherik anketasini yuboramiz
        await bot.send_message(
            user_id,
            f"🎉 Suhbatdosh topildi!\n\n"
            f"Ismi: {partner_p['name']}\n"
            f"Yoshi: {partner_p['age']}\n"
            f"Jinsi: {partner_p['gender']}\n\n"
            f"💬 Unga biron nima deb yozing\n"
            f"Keyingi suhbat uchun /next\n"
            f"Suhbatni to'xtatish uchun /stop",
            reply_markup=keyboard
        )

        # 2-foydalanuvchiga sherik anketasini yuboramiz
        await bot.send_message(
            partner_id,
            f"🎉 Suhbatdosh topildi!\n\n"
            f"Ismi: {user_p['name']}\n"
            f"Yoshi: {user_p['age']}\n"
            f"Jinsi: {user_p['gender']}\n\n"
            f"💬 Unga biron nima deb yozing\n"
            f"Keyingi suhbat uchun /next\n"
            f"Suhbatni to'xtatish uchun /stop",
            reply_markup=keyboard
        )
    else:
        waiting_users.append(user_id)
        kb = [[types.KeyboardButton(text="/stop")]]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("🔍 Suhbatdosh qidirilmoqda, iltimos kuting...", reply_markup=keyboard)

@dp.message(F.text == "/stop")
async def stop_chat(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id in active_chats:
            active_chats.pop(partner_id, None)
            kb_main = [
                [types.KeyboardButton(text="👥 Suhbatdosh qidirish")],
                [types.KeyboardButton(text="👤 Profilim")]
            ]
            keyboard_main = types.ReplyKeyboardMarkup(keyboard=kb_main, resize_keyboard=True)
            try:
                await bot.send_message(partner_id, "❌ Suhbatdosh suhbatni to'xtatdi.", reply_markup=keyboard_main)
            except:
                pass

    await state.clear()
    kb_main = [
        [types.KeyboardButton(text="👥 Suhbatdosh qidirish")],
        [types.KeyboardButton(text="👤 Profilim")]
    ]
    keyboard_main = types.ReplyKeyboardMarkup(keyboard=kb_main, resize_keyboard=True)
    await message.answer("❌ Suhbat to'xtatildi.", reply_markup=keyboard_main)

@dp.message(F.text == "/next")
async def next_chat(message: types.Message, state: FSMContext):
    # Avvalgi chatni to'xtatamiz
    await stop_chat(message, state)
    # Darhol yangi qidiruvni boshlaymiz
    await start_search(message, state)

# Suhbat paytidagi xabarlarni almashish
@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        try:
            if message.text:
                await bot.send_message(partner_id, message.text)
            elif message.photo:
                await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.voice:
                await bot.send_voice(partner_id, message.voice.file_id)
        except:
            await message.answer("❌ Xabar yuborishda xatolik yuz berdi.")
    else:
        await message.answer("Iltimos, avval '👥 Suhbatdosh qidirish' tugmasini bosing.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
