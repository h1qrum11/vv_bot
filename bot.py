import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession  # Модуль сессий

# Токен бота
API_TOKEN = '8653046435:AAGhLqpA4CREIjNVDyWaPOPYFM5-DU8j0eQ'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Указываем рабочий публичный прокси (если этот перестанет работать, можно заменить на другой IP:PORT)
PROXY_URL = "http://185.162.231.134:80" 

# Инициализация бота с использованием рабочего внешнего прокси
session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher()

# Инициализация базы данных SQLite
conn = sqlite3.connect('scores.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        points INTEGER DEFAULT 0
    )
''')
conn.commit()

# Полный словарь: ключ -> (балл, сокращенное описание сути)
KEYWORDS = {
    # Управление провинцией
    "sancakdevelopment": (2, "Улучшение инфраструктуры провинции"),
    "disasteraid": (3, "Распределение ресурсов населению"),
    "revenuegrowth": (2, "Реформа сбора налогов"),
    "banditsuppression": (2, "Восстановление безопасности дорог"),
    "taxcollection": (1, "Разумный сбор без бунтов"),
    "tradeexpansion": (2, "Караванные пути и ярмарки"),
    "mosqueconstruction": (1, "Финансирование духовного авторитета"),
    "madrasaopening": (1, "Создание образовательного учреждения"),
    
    # Личные качества
    "militarytraining": (1, "Военная подготовка и стратегия"),
    "diplomaticstudy": (1, "Искусство переговоров и этикет"),
    "languagestudy": (1, "Изучение иностранных наречий"),
    "craftlearning": (1, "Занятия наукой и каллиграфией"),
    "campaignparticipation": (2, "Боевой опыт под командованием"),
    "campaignvictory": (3, "Лидерство и демонстрация силы"),

    # Семья и династия
    "daughterbirth": (1, "Укрепление династической линии"),
    "sonbirth": (2, "Появление потенциального наследника"),
    "alliancemarriage": (2, "Связи с влиятельными семьями"),

    # Религия и репутация
    "charitywork": (2, "Помощь бедным и нуждающимся"),
    "ulemasupport": (1, "Союз с религиозной элитой"),
    "pilgrimage": (3, "Демонстрация набожности и смирения"),

    # Дворцовые игры
    "vizieralliance": (2, "Доступ к управлению государством"),
    "pashaalliance": (2, "Усиление влияния в армии"),
    "intriguesupport": (1, "Вмешательство в политические планы"),
    "blackmailsearch": (2, "Давление в политической борьбе"),
    "conspiracyexpose": (3, "Получение доверия султана"),

    # Рискованные интриги
    "briberyaction": (2, "Усиление административного контроля"),
    "allypoaching": (3, "Ослабление позиций конкурента"),
    "rivaldiscredit": (2, "Скрытый подрыв чужой репутации"),
    "sabotageplan": (3, "Организация скрытой неудачи соперника"),
    "validesupport": (3, "Сильнейший политический бонус двора"),
    "favoritesupport": (3, "Доступ к личному влиянию на правителя"),

    # Штрафы: Управление
    "provincerevolt": (-3, "Восстание и слабость управления"),
    "faminecrisis": (-2, "Нехватка еды в регионе"),
    "corruptionscandal": (-3, "Раскрытие фактов взяточничества"),
    "revenuedrop": (-2, "Ухудшение экономики из-за контроля"),
    "sultancomplaints": (-2, "Опасный сигнал потери доверия"),

    # Штрафы: Личная репутация
    "failedcampaign": (-3, "Провал военной операции"),
    "ulemaconflict": (-2, "Снижение религиозной поддержки"),
    "sultandisrespect": (-3, "Серьёзные последствия для статуса"),

    # Штрафы: Проваленные интриги
    "exposedbribery": (-3, "Удар по репутации среди элиты"),
    "exposedlies": (-2, "Подрыв доверия к действиям правителя"),
    "failedconspiracy": (-3, "Ухудшение положения при дворе"),
    "lostally": (-2, "Ослабление позиций и влияния"),
    "spynetworkexposed": (-3, "Серьёзный удар по влиянию"),
    "treasonsuspicion": (-3, "Тяжёлые последствия для будущего")
}

# Команда для просмотра счета и топа
@dp.message(Command(commands=['points', 'top']))
async def show_scores(message: types.Message):
    if message.text.startswith('/points'):
        cursor.execute("SELECT points FROM users WHERE id = ?", (message.from_user.id,))
        row = cursor.fetchone()
        score = row[0] if row else 0
        await message.reply(f"Счет: {score}")
        
    elif message.text.startswith('/top'):
        cursor.execute("SELECT name, points FROM users ORDER BY points DESC")
        rows = cursor.fetchall()
        
        if not rows:
            await message.reply("Топ пуст")
            return
            
        top_list = "\n".join([f"{i}. {name}: {pts}" for i, (name, pts) in enumerate(rows, 1)])
        await message.reply(f"Топ:\n{top_list}")

# Проверка ключевых слов и начисление/вычитание баллов
@dp.message()
async def check_keywords(message: types.Message):
    if not message.text:
        return

    text = message.text.lower()
    points_to_add = 0
    reason = ""

    # Ищем ключевое слово и извлекаем данные
    for keyword, data in KEYWORDS.items():
        if keyword in text:
            points_to_add = data[0]
            reason = data[1]
            break

    # Начисляем или списываем баллы
    if points_to_add != 0:
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        cursor.execute('''
            INSERT INTO users (id, name, points) 
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET points = points + ?, name = excluded.name
        ''', (user_id, user_name, points_to_add, points_to_add))
        conn.commit()

        cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        current_points = row[0] if row else 0

        sign = "+" if points_to_add > 0 else ""
        await message.reply(f"{sign}{points_to_add} ({reason})! Всего: {current_points}")

# Запуск
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        conn.close()
