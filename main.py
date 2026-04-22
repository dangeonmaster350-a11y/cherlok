import asyncio
import aiohttp
import json
import re
from datetime import datetime
from typing import Optional, Dict, List
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv ("8360699656:AAFKSPl9uxCHm5jWZxvXsqWFTE5PrURHYwI")
API_KEYS = {
    "tgstat": os.getenv("TGSTAT_API_KEY", ""),  # api.tgstat.ru
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ПОИСК ПО НОМЕРУ ТЕЛЕФОНА ==========
async def search_by_phone(phone: str, country: str) -> Dict:
    """Поиск информации по номеру телефона через публичные API"""
    results = {"source": "phone", "data": [], "raw": []}
    
    # Нормализация номера
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # 1. Проверка через GetContact-подобные сервисы
    # (эмуляция запроса к публичным утечкам)
    
    # 2. Поиск в публичных базах (пример структуры)
    if country == "KZ":
        results["data"].append({
            "source": "Казахстанские БД",
            "info": "Возможный владелец: поиск по утекшим базам",
            "note": "Точность не гарантирована"
        })
    
    # 3. Поиск по соцсетям через открытые API
    social_results = await check_social_by_phone(phone_clean)
    results["data"].extend(social_results)
    
    return results

async def check_social_by_phone(phone: str) -> List[Dict]:
    """Проверка привязки номера к соцсетям"""
    results = []
    # Telegram: проверяем существует ли пользователь
    # VK: поиск через публичный API
    # Instagram: проверка существования
    return results

# ========== ПОИСК ПО ФИО ==========
async def search_by_name(full_name: str, country: str) -> Dict:
    """Поиск по ФИО - возвращает возможные адреса, телефоны, даты рождения"""
    results = {"source": "fio", "data": [], "matches": []}
    
    name_parts = full_name.split()
    
    # Формируем запросы для разных стран
    if country == "RU":
        # Россия: поиск в базах ФНС, судебных приставов, соцсетях
        pass
    elif country == "KZ":
        # Казахстан: поиск по ИИН, адресам прописки через утекшие БД
        results["data"].append({
            "type": "potential_iin",
            "value": "ИИН можно найти при наличии более точных данных"
        })
    elif country == "UA":
        # Украина: поиск через открытые реестры
        pass
    elif country == "BY":
        # Беларусь: поиск через справочные системы
        pass
    
    return results

# ========== ПОИСК ПО EMAIL ==========
async def search_by_email(email: str) -> Dict:
    """Поиск утечек и соцсетей по email"""
    results = {"source": "email", "breaches": [], "social": []}
    
    # Проверка через HaveIBeenPwned API (публичный)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}") as resp:
                if resp.status == 200:
                    breaches = await resp.json()
                    results["breaches"] = breaches
        except:
            pass
    
    return results

# ========== TGSTAT ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ ==========
async def tgstat_search(query: str, country: str = None, days: int = 7) -> Dict:
    """Поиск постов в Telegram через TGStat API"""
    results = {"posts": [], "channels": [], "total": 0}
    
    if not API_KEYS["tgstat"]:
        results["error"] = "TGStat API ключ не настроен"
        return results
    
    # Страны для фильтрации: RU, KZ, UA, BY
    country_map = {"RU": "ru", "KZ": "kz", "UA": "ua", "BY": "by"}
    country_code = country_map.get(country, "")
    
    async with aiohttp.ClientSession() as session:
        # Поиск публикаций
        search_url = "https://api.tgstat.ru/search"
        params = {
            "token": API_KEYS["tgstat"],
            "query": query,
            "limit": 20
        }
        if country_code:
            params["country"] = country_code
        
        try:
            async with session.get(search_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("response"):
                        results["posts"] = data["response"].get("items", [])
                        results["total"] = len(results["posts"])
        except Exception as e:
            results["error"] = str(e)
    
    return results

# ========== ПОИСК ПО НИКНЕЙМУ (Sherlock стиль) ==========
async def search_by_username(username: str) -> Dict:
    """Поиск профилей по username на разных платформах"""
    platforms = [
        "telegram", "instagram", "vkontakte", "twitter", 
        "github", "reddit", "tiktok", "youtube"
    ]
    
    results = {"username": username, "found": [], "not_found": []}
    
    async with aiohttp.ClientSession() as session:
        for platform in platforms:
            # Проверка существования пользователя
            urls = {
                "telegram": f"https://t.me/{username}",
                "instagram": f"https://instagram.com/{username}",
                "vkontakte": f"https://vk.com/{username}",
                "twitter": f"https://twitter.com/{username}",
                "github": f"https://github.com/{username}"
            }
            
            if platform in urls:
                try:
                    async with session.get(urls[platform], timeout=5) as resp:
                        if resp.status == 200:
                            results["found"].append({"platform": platform, "url": urls[platform]})
                        else:
                            results["not_found"].append(platform)
                except:
                    results["not_found"].append(platform)
    
    return results

# ========== ОБРАБОТЧИКИ КОМАНД БОТА ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 По номеру", callback_data="search_phone"),
         InlineKeyboardButton(text="👤 По ФИО", callback_data="search_name")],
        [InlineKeyboardButton(text="📧 По Email", callback_data="search_email"),
         InlineKeyboardButton(text="🔍 По никнейму", callback_data="search_username")],
        [InlineKeyboardButton(text="📰 Поиск в Telegram", callback_data="search_tg")],
        [InlineKeyboardButton(text="🌍 Выбор страны", callback_data="select_country")]
    ])
    
    await message.answer(
        "🔍 *OSINT Бот поиска информации*\n\n"
        "Доступные страны: Россия, Беларусь, Украина, Казахстан\n\n"
        "Выберите тип поиска:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    
    if data == "select_country":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Россия", callback_data="country_RU"),
             InlineKeyboardButton(text="🇧🇾 Беларусь", callback_data="country_BY")],
            [InlineKeyboardButton(text="🇺🇦 Украина", callback_data="country_UA"),
             InlineKeyboardButton(text="🇰🇿 Казахстан", callback_data="country_KZ")]
        ])
        await callback.message.edit_text("Выберите страну для поиска:", reply_markup=keyboard)
        return
    
    if data.startswith("country_"):
        country = data.replace("country_", "")
        # Сохраняем страну в сессии пользователя
        await callback.message.answer(f"✅ Страна выбрана: {country}\nТеперь выберите тип поиска через /start")
        return
    
    # Обработка команд поиска
    if data == "search_phone":
        await callback.message.answer("📞 Введите номер телефона (с кодом страны):\nПример: +79001234567 или +77001234567")
        # Здесь нужно сохранить состояние ожидания ввода
    elif data == "search_name":
        await callback.message.answer("👤 Введите ФИО полностью:\nПример: Иванов Иван Иванович")
    elif data == "search_email":
        await callback.message.answer("📧 Введите email адрес:\nПример: user@example.com")
    elif data == "search_username":
        await callback.message.answer("🔍 Введите никнейм (username):\nПример: john_doe")
    elif data == "search_tg":
        await callback.message.answer("📰 Введите поисковый запрос для Telegram каналов:\nПример: утечка данных")

# ========== ЗАПУСК ==========
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())