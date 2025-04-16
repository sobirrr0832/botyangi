import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from googletrans import Translator
from dotenv import load_dotenv

# .env faylidan API kalitlarini yuklash
load_dotenv()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot tokenini .env faylidan olish
API_TOKEN = os.getenv("BOT_TOKEN")

# Bot va dispatcher yaratish
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Google Translator
translator = Translator()

# Holat klassi
class TranslationState(StatesGroup):
    waiting_for_text = State()
    waiting_for_language = State()

# Til kodlari
LANGUAGES = {
    "🇺🇿 O'zbekcha": "uz",
    "🇸🇦 Arabcha": "ar",
    "🇹🇷 Turkcha": "tr"
}

# Klaviatura yaratish
def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for lang in LANGUAGES.keys():
        keyboard.add(KeyboardButton(lang))
    return keyboard

# /start komandasini qayta ishlash
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Assalomu alaykum! Men O'zbek, Arab va Turk tillari bo'yicha tarjimon botman.\n"
        "Tarjima qilmoqchi bo'lgan matningizni kiriting."
    )
    await TranslationState.waiting_for_text.set()

# Matnni qabul qilish
@dp.message_handler(state=TranslationState.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await message.reply("Iltimos, buyruq emas, tarjima qilmoqchi bo'lgan matningizni kiriting.")
        return
    
    await state.update_data(text=message.text)
    await message.reply("Qaysi tilga tarjima qilishni xohlaysiz?", reply_markup=get_language_keyboard())
    await TranslationState.waiting_for_language.set()

# Tilni qabul qilish va tarjima qilish
@dp.message_handler(state=TranslationState.waiting_for_language)
async def process_language(message: types.Message, state: FSMContext):
    language = message.text
    
    if language not in LANGUAGES:
        await message.reply("Iltimos, taqdim etilgan tillardan birini tanlang:", reply_markup=get_language_keyboard())
        return
    
    user_data = await state.get_data()
    text = user_data['text']
    target_lang = LANGUAGES[language]
    
    try:
        # Matndagi tilni avtomatik aniqlash
        detected = translator.detect(text)
        source_lang = detected.lang
        
        if source_lang == target_lang:
            await message.reply(f"Kiritilgan matn allaqachon {language} tilida.")
        else:
            # Tarjima qilish
            translated_text = translator.translate(text, dest=target_lang).text
            
            # Natijani yuborish
            source_lang_name = next((k for k, v in LANGUAGES.items() if v == source_lang), f"Aniqlanmagan til ({source_lang})")
            await message.reply(
                f"📝 Original matn ({source_lang_name}):\n{text}\n\n"
                f"🔄 Tarjima ({language}):\n{translated_text}"
            )
    except Exception as e:
        logging.error(f"Tarjima vaqtida xatolik: {e}")
        await message.reply("Tarjima vaqtida xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    
    # Yangi tarjima uchun botni qayta sozlash
    await message.reply("Yangi tarjima uchun matn kiriting:")
    await TranslationState.waiting_for_text.set()

# /help komandasini qayta ishlash
@dp.message_handler(commands=['help'], state='*')
async def help_command(message: types.Message):
    await message.reply(
        "Bot haqida qo'llanma:\n"
        "1. Tarjima qilmoqchi bo'lgan matningizni kiriting\n"
        "2. Qaysi tilga tarjima qilishni tanlang (O'zbek, Arab, Turk)\n"
        "3. Bot sizga tarjima natijasini ko'rsatadi\n\n"
        "Yangi tarjima boshlash uchun istalgan vaqtda /start buyrug'ini yuboring."
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
