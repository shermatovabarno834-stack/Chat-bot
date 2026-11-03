import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "9160638068:AAGtVpgYjmPJxStxsJIT89q9jxvaejfE8kQ"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

search_queue = []
active_chats = {}

class ChatState(StatesGroup):
    in_chat = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in active_chats:
        partner = active_chats.pop(message.from_user.id, None)
        if partner in active_chats:
            active_chats.pop(partner, None)
            await bot.send_message(partner, "⚠️ Suhbatdoshingiz suhbatni tark etdi.")
            
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Do'st qidirish")
    builder.adjust(1)
    
    await message.answer(
        "Salom! Anonim tanishuv botiga xush kelibsiz. "
        "Do'st topish uchun quyidagi tugmani bosing:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.text == "🔍 Do'st qidirish")
async def choose_search(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="👧 Qiz do'st qidirish", callback_data="search_female")
    builder.button(text="👦 O'g'il do'st qidirish", callback_data="search_male")
    builder.button(text="🌐 Random do'st qidirish", callback_data="search_random")
    builder.adjust(1)
    
    await message.answer("Kimni qidiryapsiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("search_"))
async def start_searching(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    await callback.message.edit_text("⏳ Mos keladigan suhbatdosh qidirilmoqda...")
    
    partner_id = None
    for p_id in search_queue:
        if p_id != user_id:
            partner_id = p_id
            break
            
    if partner_id:
        search_queue.remove(partner_id)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        await bot.send_message(user_id, "🎉 Suhbatdosh topildi! Yozishni boshlashingiz mumkin.\n(Suhbatni to'xtatish uchun /stop bosing)")
        await bot.send_message(partner_id, "🎉 Suhbatdosh topildi! Yozishni boshlashingiz mumkin.\n(Suhbatni to'xtatish uchun /stop bosing)")
    else:
        if user_id not in search_queue:
            search_queue.append(user_id)
        await callback.message.answer("⏳ Navbatga qo'shildingiz. Bo'sh suhbatdosh chiqishini kutamiz... Bekor qilish uchun /stop yuboring.")

@dp.message(Command("stop"))
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in search_queue:
        search_queue.remove(user_id)
        
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        if partner_id in active_chats:
            active_chats.pop(partner_id)
        await bot.send_message(partner_id, "⚠️ Suhbatdoshingiz suhbatni tark etdi.")
        await message.answer("🛑 Suhbat yakunlandi.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Siz hozir hech kim bilan gaplashmayapsiz yoki qidiruvda emassiz.")
    
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Do'st qidirish")
    await message.answer("Yangi qidiruv boshlash uchun bosing:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message()
async def pass_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await message.copy_to(partner_id)
    else:
        await message.answer("Iltimos, avval **🔍 Do'st qidirish** tugmasini bosing.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
  
