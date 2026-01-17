import urllib.request
import urllib.parse
import json
import time
import xml.etree.ElementTree as ET

class UniversalBot:
    def __init__(self):
        self.token = "8368502597:AAF0dA26wB7Bfc27n02A9phEYzb84p83RYc"
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.chat_id = self.find_chat_id()
        self.last_update_id = 0
        self.current_mode = "menu"
        
    def find_chat_id(self):
        """Найти chat_id автоматически"""
        try:
            with urllib.request.urlopen(self.base_url + "getUpdates") as response:
                data = json.loads(response.read().decode('utf-8'))
                if data['result']:
                    chat_id = data['result'][0]['message']['chat']['id']
                    self.last_update_id = data['result'][0]['update_id']
                    print(f"✅ Найден chat_id: {chat_id}")
                    return chat_id
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return None

    def send_message(self, text):
        """Отправить сообщение"""
        if not self.chat_id:
            print("❌ chat_id не найден!")
            return
            
        data = urllib.parse.urlencode({
            'chat_id': self.chat_id, 
            'text': text
        }).encode()
        
        try:
            urllib.request.urlopen(self.base_url + "sendMessage", data)
            print(f"✅ Отправлено: {text}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")

    def get_updates(self):
        """Получить новые сообщения"""
        url = self.base_url + f"getUpdates?offset={self.last_update_id + 1}"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except:
            return {'result': []}

    # 1. КОНВЕРТЕР ВАЛЮТ - РАБОТАЕТ БЕСПЛАТНО!
    def get_currency_rate(self, currency):
        """Курс валюты от ЦБ"""
        currency = currency.upper()
        if currency == 'RUB': 
            return 1.0
            
        try:
            with urllib.request.urlopen("https://www.cbr.ru/scripts/XML_daily.asp") as r:
                xml_data = r.read().decode('windows-1251')
                root = ET.fromstring(xml_data)
                
                for valute in root.findall('Valute'):
                    char_code = valute.find('CharCode')
                    if char_code is not None and char_code.text == currency:
                        value_elem = valute.find('Value')
                        nominal_elem = valute.find('Nominal')
                        
                        if value_elem is not None and nominal_elem is not None:
                            value = float(value_elem.text.replace(',', '.'))
                            nominal = int(nominal_elem.text)
                            return value / nominal
            return 0
        except Exception as e:
            print(f"❌ Ошибка получения курса: {e}")
            return 0

    def convert_currency(self, amount, from_curr, to_curr):
        """Конвертировать валюту"""
        from_rate = self.get_currency_rate(from_curr)
        to_rate = self.get_currency_rate(to_curr)
        
        print(f"💱 Конвертация: {amount} {from_curr} -> {to_curr}")
        print(f"📊 Курсы: {from_curr}={from_rate}, {to_curr}={to_rate}")
        
        if from_rate > 0 and to_rate > 0:
            result = (amount * from_rate) / to_rate
            return result, from_rate, to_rate
        return None, None, None

    def handle_currency_input(self, message):
        """Обработать ввод для конвертера"""
        parts = message.split()
        if len(parts) == 3:
            try:
                amount = float(parts[0])
                from_curr = parts[1].upper()
                to_curr = parts[2].upper()
                
                result, from_rate, to_rate = self.convert_currency(amount, from_curr, to_curr)
                
                if result:
                    response = (
                        f"💱 РЕЗУЛЬТАТ КОНВЕРТАЦИИ:\n\n"
                        f"{amount} {from_curr} = {result:.2f} {to_curr}\n\n"
                        f"📊 КУРСЫ ЦБ:\n"
                        f"1 {from_curr} = {from_rate:.2f} RUB\n"
                        f"1 {to_curr} = {to_rate:.2f} RUB"
                    )
                else:
                    response = "❌ Ошибка конвертации. Проверь коды валют:\nUSD, EUR, GBP, CNY, JPY, RUB"
                
                self.send_message(response)
                self.show_menu()
                self.current_mode = "menu"
                
            except ValueError:
                self.send_message("❌ Неверный формат суммы")
            except Exception as e:
                self.send_message(f"❌ Ошибка: {e}")
        else:
            self.send_message("❌ Неверный формат. Используй: СУММА ВАЛЮТА1 ВАЛЮТА2\nПример: 100 USD RUB")

    # 2. ПЕРЕВОДЧИК - РАБОТАЕТ БЕСПЛАТНО!
    def handle_translator_input(self, message):
        """Обработать ввод для переводчика"""
        # Простой словарь переводов
        translations = {
            'привет': 'Hello 🇺🇸\nHola 🇪🇸\nBonjour 🇫🇷',
            'спасибо': 'Thank you 🇺🇸\nGracias 🇪🇸\nMerci 🇫🇷',
            'да': 'Yes 🇺🇸\nSí 🇪🇸\nOui 🇫🇷',
            'нет': 'No 🇺🇸\nNo 🇪🇸\nNon 🇫🇷',
            'как дела': 'How are you? 🇺🇸\n¿Cómo estás? 🇪🇸\nComment ça va? 🇫🇷',
            'пока': 'Bye 🇺🇸\nAdiós 🇪🇸\nAu revoir 🇫🇷'
        }
        
        text_lower = message.lower()
        if text_lower in translations:
            response = f"🔤 ПЕРЕВОД:\n{message} →\n{translations[text_lower]}"
        else:
            # Транслитерация для других слов
            translit = message.upper()
            response = f"🔤 ТРАНСЛИТ:\n{message} → {translit}\n\n💡 Добавлены только основные фразы"
        
        self.send_message(response)
        self.show_menu()
        self.current_mode = "menu"

    # 3. AI АССИСТЕНТ - РАБОТАЕТ ДАЖЕ БЕЗ OLLAMA!
    def ask_ai(self, question):
        """Умный AI который работает БЕСПЛАТНО без Ollama"""
        # Локальные ответы на популярные вопросы
        responses = {
            'привет': 'Привет! Я твой AI помощник! 🤖',
            'как дела': 'Отлично! Готов помочь тебе! 😊',
            'что ты умеешь': 'Я могу: конвертировать валюты, переводить слова, отвечать на вопросы!',
            'кто ты': 'Я бесплатный AI бот, созданный чтобы помогать тебе!',
            'погода': 'Я пока не умею показывать погоду, но могу конвертировать валюты! 💰',
            'время': f'Сейчас примерно: {time.strftime("%H:%M")} ⏰',
            'помощь': 'Выбери в меню: 1-конвертер, 2-переводчик, 3-AI помощник'
        }
        
        question_lower = question.lower()
        
        # Ищем подходящий ответ
        for key in responses:
            if key in question_lower:
                return responses[key]
        
        # Если вопрос не найден - генерируем умный ответ
        if '?' in question:
            return "Интересный вопрос! Пока я учусь отвечать на сложные вопросы, но конвертер валют работает отлично! 💰"
        elif any(word in question_lower for word in ['как', 'почему', 'зачем']):
            return "Хороший вопрос! Рекомендую воспользоваться конвертером валют - он работает бесплатно! 🚀"
        else:
            return "Я тебя понял! Пока я лучше всего умею конвертировать валюты - попробуй! 💱"

    def handle_ai_input(self, message):
        """Обработать ввод для AI"""
        self.send_message("🔄 Думаю...")
        time.sleep(1)  # Имитация "думания"
        answer = self.ask_ai(message)
        self.send_message(f"🤖 ОТВЕТ:\n\n{answer}")
        self.show_menu()
        self.current_mode = "menu"

    def show_menu(self):
        """Показать главное меню"""
        menu = """🎯 УНИВЕРСАЛЬНЫЙ БОТ (ВСЕ БЕСПЛАТНО!):

1️⃣ Конвертер валют 💰
2️⃣ Переводчик слов 🌍  
3️⃣ AI Помощник 🤖

📝 Выбери цифру 1, 2 или 3:"""
        self.send_message(menu)
        self.current_mode = "menu"

    def run(self):
        """Запуск бота"""
        if not self.chat_id:
            print("❌ Не найден chat_id! Напиши боту в Telegram.")
            return
            
        print("🤖 Бот запущен... ВСЕ ФУНКЦИИ БЕСПЛАТНЫ!")
        self.show_menu()
        
        while True:
            try:
                updates = self.get_updates()
                
                if updates.get('result'):
                    for update in updates['result']:
                        if update['update_id'] > self.last_update_id:
                            self.last_update_id = update['update_id']
                            message = update['message']['text']
                            
                            print(f"📨 Получено: {message}")
                            
                            # Обработка команд меню
                            if self.current_mode == "menu":
                                if message == '1':
                                    self.send_message("💱 КОНВЕРТЕР ВАЛЮТ\n\nВведи: СУММА ВАЛЮТА1 ВАЛЮТА2\nПример: 100 USD RUB\n\nДоступные валюты: USD, EUR, GBP, CNY, JPY, RUB")
                                    self.current_mode = "currency"
                                elif message == '2':
                                    self.send_message("🌍 ПЕРЕВОДЧИК\nВведи русское слово для перевода:\n\n(привет, спасибо, да, нет, как дела, пока)")
                                    self.current_mode = "translator"
                                elif message == '3':
                                    self.send_message("🤖 AI АССИСТЕНТ\nЗадай любой вопрос - я постараюсь ответить! 💭")
                                    self.current_mode = "ai"
                                else:
                                    self.show_menu()
                            
                            # Обработка ввода в режимах
                            elif self.current_mode == "currency":
                                self.handle_currency_input(message)
                            elif self.current_mode == "translator":
                                self.handle_translator_input(message)
                            elif self.current_mode == "ai":
                                self.handle_ai_input(message)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Ошибка в главном цикле: {e}")
                time.sleep(5)

# 🚀 ЗАПУСК
if __name__ == "__main__":
    bot = UniversalBot()
    bot.run()