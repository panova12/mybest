import json
import asyncio
import logging
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
import google.generativeai as genai

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# КОНФИГУРАЦИЯ
# ========================
class Config:
    def __init__(self):
        self.BOT_TOKEN = ""
        self.GEMINI_API_KEY = ""        self.BASE_URL = f"https://api.telegram.org/bot{self.BOT_TOKEN}"
        self.PARSE_MODE = "HTML"
        self.POLL_TIMEOUT = 30
        
        # URL сервисов
        self.CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
        self.LIBRETRANSLATE_URL = "https://libretranslate.com/translate"

# ========================
# ОСНОВНОЙ КЛАСС БОТА
# ========================
class TravelBot:
    def __init__(self, config: Config):
        self.config = config
        self.offset = 0
        self.user_states = {}
        self.ai_context = {}
        self.currency_cache = {'rates': {}, 'last_update': None}
        self.session = None
        
        # Инициализация Gemini с правильной моделью
        try:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            # Используем правильную модель
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini AI успешно подключен (модель: gemini-1.5-flash)")
            
            # Тестовая генерация для проверки
            test_response = self.gemini_model.generate_content("Привет")
            logger.info(f"✅ Тест Gemini успешен: {test_response.text[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini: {e}")
            # Список доступных моделей для отладки
            try:
                available_models = genai.list_models()
                logger.info(f"📋 Доступные модели: {[m.name for m in available_models[:5]]}")
            except:
                pass
            self.gemini_model = None

    # --- СЕТЕВОЕ ЯДРО ---
    async def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Асинхронный HTTP запрос"""
        url = f"{self.config.BASE_URL}/{endpoint}"
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params, timeout=20) as resp:
                    return await resp.json()
            else:
                async with self.session.post(url, json=data, timeout=20) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"❌ Сетевая ошибка: {e}")
            return None

    # --- ЛОГИКА ВАЛЮТ ---
    async def update_currency_rates(self):
        """Обновляет кэш валют раз в час"""
        now = datetime.now()
        if self.currency_cache['last_update'] and (now - self.currency_cache['last_update']).seconds < 3600:
            return

        try:
            async with self.session.get(self.config.CBR_URL) as resp:
                text = await resp.read()
                root = ET.fromstring(text.decode('windows-1251'))
                rates = {'RUB': 1.0}
                
                for valute in root.findall('Valute'):
                    char_code = valute.find('CharCode')
                    value = valute.find('Value')
                    nominal = valute.find('Nominal')
                    
                    if char_code is not None and value is not None and nominal is not None:
                        code = char_code.text
                        value_float = float(value.text.replace(',', '.'))
                        nominal_int = int(nominal.text)
                        rates[code] = value_float / nominal_int
                
                self.currency_cache['rates'] = rates
                self.currency_cache['last_update'] = now
                logger.info("💰 Курсы валют обновлены")
                
        except Exception as e:
            logger.error(f"❌ Курсы валют недоступны: {e}")
            # Статические курсы как запасной вариант
            static_rates = {
                'USD': 92.5, 'EUR': 101.0, 'GBP': 118.0,
                'JPY': 0.58, 'CNY': 12.7, 'CHF': 102.5,
                'RUB': 1.0, 'AUD': 60.5, 'CAD': 67.8
            }
            self.currency_cache['rates'] = static_rates

    async def convert_currency(self, amount: float, from_curr: str, to_curr: str):
        """Конвертация валюты"""
        await self.update_currency_rates()
        rates = self.currency_cache['rates']
        
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()
        
        if from_curr not in rates or to_curr not in rates:
            return None
        
        result = (amount * rates[from_curr]) / rates[to_curr]
        return round(result, 2)

    # --- ЛОГИКА ПЕРЕВОДА ---
    async def translate_text(self, text: str, target_lang: str):
        """Перевод текста"""
        # Используем Gemini для перевода если доступен
        if self.gemini_model:
            try:
                prompt = f"Translate this to {target_lang}: {text}"
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content, prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"❌ Ошибка перевода Gemini: {e}")
        
        # Запасной вариант через LibreTranslate
        try:
            # Определяем исходный язык
            has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in text)
            source_lang = "ru" if has_cyrillic else "en"
            
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            async with self.session.post(
                self.config.LIBRETRANSLATE_URL,
                json=data,
                timeout=10
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('translatedText', text)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка LibreTranslate: {e}")
        
        # Запасной словарь
        translations = {
            'привет': {'en': 'Hello', 'es': 'Hola', 'fr': 'Bonjour', 'de': 'Hallo', 'zh': '你好', 'ja': 'こんにちは'},
            'спасибо': {'en': 'Thank you', 'es': 'Gracias', 'fr': 'Merci', 'de': 'Danke', 'zh': '谢谢', 'ja': 'ありがとう'},
            'да': {'en': 'Yes', 'es': 'Sí', 'fr': 'Oui', 'de': 'Ja', 'zh': '是', 'ja': 'はい'},
            'нет': {'en': 'No', 'es': 'No', 'fr': 'Non', 'de': 'Nein', 'zh': '不', 'ja': 'いいえ'},
            'как дела': {'en': 'How are you?', 'es': '¿Cómo estás?', 'fr': 'Comment ça va?', 'de': 'Wie geht es dir?', 'zh': '你好吗？', 'ja': 'お元気ですか？'},
            'пока': {'en': 'Bye', 'es': 'Adiós', 'fr': 'Au revoir', 'de': 'Tschüss', 'zh': '再见', 'ja': 'さようなら'},
            'любовь': {'en': 'Love', 'es': 'Amor', 'fr': 'Amour', 'de': 'Liebe', 'zh': '爱', 'ja': '愛'},
            'мир': {'en': 'Peace', 'es': 'Paz', 'fr': 'Paix', 'de': 'Frieden', 'zh': '和平', 'ja': '平和'}
        }
        
        text_lower = text.lower()
        for russian, lang_dict in translations.items():
            if russian in text_lower:
                return lang_dict.get(target_lang, text)
        
        return text

    # --- AI ПОМОЩНИК ---
    async def get_ai_response(self, question: str, user_id: int):
        """Получить ответ от AI"""
        if not self.gemini_model:
            # Локальные ответы если Gemini недоступен
            local_responses = {
                'привет': 'Привет! Чем могу помочь? 🤖',
                'как дела': 'Отлично! Готов помочь с конвертацией валют или переводом текстов! 💱',
                'что ты умеешь': 'Могу:\n1. Конвертировать валюты\n2. Переводить текст\n3. Отвечать на вопросы\n4. Показывать курсы валют',
                'кто ты': 'Я Telegram-бот с интеграцией AI!',
                'время': f'⏰ Текущее время: {datetime.now().strftime("%H:%M")}',
                'дата': f'📅 Сегодня: {datetime.now().strftime("%d.%m.%Y")}',
            }
            
            question_lower = question.lower()
            for key in local_responses:
                if key in question_lower:
                    return local_responses[key]
            
            return "🤖 AI временно недоступен. Попробуйте функции конвертера или переводчика!"
        
        try:
            # Инициализируем контекст
            if user_id not in self.ai_context:
                self.ai_context[user_id] = []
            
            # Добавляем вопрос в контекст
            self.ai_context[user_id].append(f"User: {question}")
            
            # Ограничиваем историю (последние 5 сообщений)
            if len(self.ai_context[user_id]) > 10:
                self.ai_context[user_id] = self.ai_context[user_id][-10:]
            
            # Создаем промпт с контекстом
            context = "\n".join(self.ai_context[user_id][-3:])  # Берем последние 3 сообщения
            full_prompt = f"{context}\n\nОтветь кратко и по делу:"
            
            # Генерируем ответ через Gemini
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )
            
            if response and hasattr(response, 'text'):
                answer = response.text.strip()
                self.ai_context[user_id].append(f"AI: {answer[:100]}...")
                return answer
                
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini при генерации: {e}")
            # Пробуем без контекста
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    question,
                    generation_config={
                        "temperature": 0.7,
                        "max_output_tokens": 300,
                    }
                )
                if response and hasattr(response, 'text'):
                    return response.text.strip()
            except:
                pass
        
        return "🤖 Извините, не могу получить ответ от AI. Попробуйте позже."

    # --- ОБРАБОТКА СООБЩЕНИЙ ---
    async def handle_message(self, msg: dict):
        """Обработка входящего сообщения"""
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        text = msg.get('text', '').strip()
        
        # Получаем состояние пользователя
        state = self.user_states.get(user_id, 'MENU')
        
        logger.info(f"📨 [{user_id}]: {text} (state: {state})")
        
        # Обработка команд
        if text == "/start":
            self.user_states[user_id] = 'MENU'
            await self.send_menu(chat_id)
            return
        
        if text == "/clear":
            if user_id in self.ai_context:
                del self.ai_context[user_id]
            await self.send_message(chat_id, "🧹 Контекст AI очищен!")
            return
        
        if text == "/help":
            help_text = """
📋 <b>ПОМОЩЬ И КОМАНДЫ</b>

<b>Основные команды:</b>
/start - Главное меню
/help - Эта справка
/clear - Очистить историю AI

<b>Функции (нажмите кнопку или введите номер):</b>
1️⃣ <b>Валюта</b> - Конвертер валют
2️⃣ <b>Переводчик</b> - Перевод текста
3️⃣ <b>AI Помощник</b> - Вопросы к AI

<b>Примеры использования:</b>
• Конвертер: <code>100 USD RUB</code>
• Переводчик: <code>en привет</code>
• AI: любой вопрос на русском или английском

<b>Доступные валюты:</b> USD, EUR, RUB, GBP, JPY, CNY, CHF, AUD, CAD

<b>Доступные языки:</b> en, es, fr, de, zh, ja, ru
"""
            await self.send_message(chat_id, help_text)
            return
        
        if text == "/status":
            status = f"""
📊 <b>СТАТУС БОТА</b>

• Бот работает: ✅
• Пользователей: {len(self.user_states)}
• Gemini AI: {'✅' if self.gemini_model else '❌'}
• Кеш валют: {'✅' if self.currency_cache['rates'] else '❌'}
• Сообщений в очереди: {self.offset}

<b>Время сервера:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            await self.send_message(chat_id, status)
            return
        
        # Машина состояний
        if state == 'MENU':
            if text in ["1", "1️⃣", "Валюта", "валюта", "конвертер"]:
                self.user_states[user_id] = 'CURRENCY'
                await self.send_message(
                    chat_id,
                    "💰 <b>КОНВЕРТЕР ВАЛЮТ</b>\n\n"
                    "<b>Формат:</b> <code>СУММА ВАЛЮТА1 ВАЛЮТА2</code>\n\n"
                    "<b>Примеры:</b>\n"
                    "<code>100 USD RUB</code> - доллары в рубли\n"
                    "<code>5000 RUB EUR</code> - рубли в евро\n"
                    "<code>50.5 EUR USD</code> - евро в доллары\n\n"
                    "<b>Доступные валюты:</b>\n"
                    "USD, EUR, RUB, GBP, JPY, CNY, CHF, AUD, CAD"
                )
                
            elif text in ["2", "2️⃣", "Переводчик", "переводчик", "перевод"]:
                self.user_states[user_id] = 'TRANSLATE'
                await self.send_message(
                    chat_id,
                    "🌍 <b>ПЕРЕВОДЧИК</b>\n\n"
                    "<b>Формат:</b> <code>язык текст</code>\n\n"
                    "<b>Примеры:</b>\n"
                    "<code>en привет</code> - на английский\n"
                    "<code>es спасибо</code> - на испанский\n"
                    "<code>fr любовь</code> - на французский\n\n"
                    "<b>Доступные языки:</b>\n"
                    "en (английский), es (испанский), fr (французский)\n"
                    "de (немецкий), zh (китайский), ja (японский), ru (русский)"
                )
                
            elif text in ["3", "3️⃣", "AI", "ai", "бот", "помощник"]:
                self.user_states[user_id] = 'AI_CHAT'
                await self.send_message(
                    chat_id,
                    "🤖 <b>AI ПОМОЩНИК (Gemini 1.5 Flash)</b>\n\n"
                    "Задайте любой вопрос на русском или английском!\n\n"
                    "<b>Примеры вопросов:</b>\n"
                    "• Объясни квантовую физику простыми словами\n"
                    "• Напиши короткий рассказ про кота\n"
                    "• Как работает искусственный интеллект?\n\n"
                    "<i>Используйте /clear для очистки истории диалога</i>"
                )
                
            else:
                await self.send_menu(chat_id)

        elif state == 'CURRENCY':
            try:
                parts = text.split()
                if len(parts) == 3:
                    amount = float(parts[0])
                    from_curr = parts[1].upper()
                    to_curr = parts[2].upper()
                    
                    result = await self.convert_currency(amount, from_curr, to_curr)
                    
                    if result is not None:
                        # Получаем текущие курсы для информации
                        await self.update_currency_rates()
                        rates = self.currency_cache['rates']
                        from_rate = rates.get(from_curr, 0)
                        to_rate = rates.get(to_curr, 0)
                        
                        response = f"""
💱 <b>РЕЗУЛЬТАТ КОНВЕРТАЦИИ</b>

<code>{amount} {from_curr} = {result} {to_curr}</code>

<b>Курсы:</b>
1 {from_curr} = {from_rate:.4f} RUB
1 {to_curr} = {to_rate:.4f} RUB
1 {from_curr} = {(from_rate/to_rate):.4f} {to_curr}

<i>Данные ЦБ РФ • Обновлено: {datetime.now().strftime('%H:%M')}</i>
"""
                    else:
                        response = "❌ <b>Ошибка!</b> Проверьте коды валют.\nДоступные: USD, EUR, RUB, GBP, JPY, CNY, CHF, AUD, CAD"
                    
                    await self.send_message(chat_id, response)
                    self.user_states[user_id] = 'MENU'
                    await asyncio.sleep(1)
                    await self.send_menu(chat_id)
                    
                else:
                    await self.send_message(
                        chat_id,
                        "❌ <b>Неверный формат!</b>\n\n"
                        "Используйте: <code>СУММА ВАЛЮТА1 ВАЛЮТА2</code>\n\n"
                        "<b>Пример:</b> <code>100 USD RUB</code>"
                    )
                    
            except ValueError:
                await self.send_message(chat_id, "❌ <b>Ошибка суммы!</b> Используйте числа. Пример: <code>100.5 USD EUR</code>")
            except Exception as e:
                await self.send_message(chat_id, f"❌ <b>Ошибка:</b> {str(e)[:100]}")
                self.user_states[user_id] = 'MENU'

        elif state == 'TRANSLATE':
            parts = text.split(maxsplit=1)
            if len(parts) == 2:
                lang, word = parts
                lang = lang.lower()
                
                # Проверяем язык
                valid_langs = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ru']
                if lang not in valid_langs:
                    response = f"❌ <b>Неверный язык!</b>\n\nДоступные: {', '.join(valid_langs)}"
                    await self.send_message(chat_id, response)
                    return
                
                # Показываем индикатор загрузки
                await self.send_message(chat_id, "⏳ <i>Перевожу...</i>")
                
                translated = await self.translate_text(word, lang)
                
                # Эмодзи для языков
                lang_emojis = {
                    'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪',
                    'zh': '🇨🇳', 'ja': '🇯🇵', 'ru': '🇷🇺'
                }
                emoji = lang_emojis.get(lang, '🌐')
                
                response = f"""
{emoji} <b>ПЕРЕВОД</b>

<b>Оригинал:</b> {word}
<b>Язык:</b> {lang.upper()} {emoji}
<b>Перевод:</b> {translated}
"""
                await self.send_message(chat_id, response)
                self.user_states[user_id] = 'MENU'
                await asyncio.sleep(1)
                await self.send_menu(chat_id)
                
            else:
                await self.send_message(
                    chat_id,
                    "❌ <b>Неверный формат!</b>\n\n"
                    "Используйте: <code>язык текст</code>\n\n"
                    "<b>Пример:</b> <code>en привет</code>"
                )

        elif state == 'AI_CHAT':
            await self.send_message(chat_id, "🤔 <i>Думаю...</i>")
            response = await self.get_ai_response(text, user_id)
            await self.send_message(chat_id, response)

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ---
    async def send_message(self, chat_id: int, text: str, reply_markup: dict = None):
        """Отправить сообщение"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': self.config.PARSE_MODE,
            'disable_web_page_preview': True
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        await self.make_request('POST', 'sendMessage', data)

    async def send_menu(self, chat_id: int):
        """Отправить главное меню"""
        keyboard = {
            "keyboard": [
                [{"text": "1️⃣ Валюта"}, {"text": "2️⃣ Переводчик"}],
                [{"text": "3️⃣ AI Помощник"}, {"text": "❓ Помощь"}],
                [{"text": "🔄 Обновить меню"}, {"text": "📊 Статус"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        
        await self.send_message(
            chat_id,
            "🤖 <b>УНИВЕРСАЛЬНЫЙ TELEGRAM БОТ</b>\n\n"
            "<i>Быстрый доступ к функциям:</i>\n\n"
            "1️⃣ <b>Конвертер валют</b> 💱\n"
            "2️⃣ <b>Переводчик текста</b> 🌍\n"
            "3️⃣ <b>AI помощник (Gemini)</b> 🤖\n\n"
            "Выберите действие:",
            keyboard
        )

    async def run(self):
        """Основной цикл бота"""
        # Создаем сессию с оптимизированными параметрами
        connector = aiohttp.TCPConnector(
            limit=100,
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        logger.info("=" * 50)
        logger.info("🚀 ЗАПУСК УНИВЕРСАЛЬНОГО БОТА")
        logger.info("=" * 50)
        logger.info(f"🤖 Бот: @{await self.get_bot_info()}")
        logger.info(f"💰 Gemini: {'✅' if self.gemini_model else '❌'}")
        logger.info("📡 Ожидание сообщений...")
        
        try:
            while True:
                try:
                    params = {
                        'offset': self.offset,
                        'timeout': self.config.POLL_TIMEOUT,
                        'limit': 100
                    }
                    
                    # Получаем обновления
                    data = await self.make_request('GET', 'getUpdates', params=params)
                    
                    if data and data.get('ok'):
                        updates = data.get('result', [])
                        
                        if updates:
                            logger.info(f"📥 Получено {len(updates)} сообщений")
                            
                        for update in updates:
                            self.offset = update['update_id'] + 1
                            
                            if 'message' in update:
                                # Запускаем обработку сообщения
                                asyncio.create_task(self.handle_message(update['message']))
                    
                    # Небольшая пауза между запросами
                    await asyncio.sleep(0.1)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"⚠️ Ошибка в цикле: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Получен сигнал остановки...")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            await self.session.close()
            logger.info("👋 Бот остановлен")

    async def get_bot_info(self):
        """Получить информацию о боте"""
        try:
            data = await self.make_request('GET', 'getMe')
            if data and data.get('ok'):
                bot_info = data['result']
                return bot_info.get('username', 'неизвестно')
        except:
            pass
        return "неизвестно"

# ========================
# ЗАПУСК
# ========================
async def main():
    """Точка входа"""
    config = Config()
    bot = TravelBot(config)
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен пользователем")

if __name__ == "__main__":
    asyncio.run(main())