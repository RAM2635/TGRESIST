import logging
from telebot import TeleBot, types
from openai import OpenAI
from gtts import gTTS

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Цвета и их значения
colors = {
    "Black": 0, "Brown": 1, "Red": 2, "Orange": 3, "Yellow": 4,
    "Green": 5, "Blue": 6, "Violet": 7, "Gray": 8, "White": 9,
    "Gold": -1, "Silver": -2
}

# Соответствие цветов для каждого кольца
band_colors = ["Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White"]
multiplier_colors = band_colors + ["Gold", "Silver"]
tolerance_colors = ["Brown", "Red", "Green", "Blue", "Violet", "Gray", "Gold", "Silver"]

# Эмодзи для каждого цвета
color_emojis = {
    "Black": "⬛️", "Brown": "🟫", "Red": "🟥", "Orange": "🟧", "Yellow": "🟨",
    "Green": "🟩", "Blue": "🟦", "Violet": "🟪", "Gray": "⬜️", "White": "⬜️",
    "Gold": "🟨", "Silver": "⬜️"
}

# Настройка OpenAI API
client = OpenAI(
    api_key="***",
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Функция для расчета номинала резистора
def calculate_resistance(band1, band2, multiplier, tolerance):
    base_value = (colors[band1] * 10 + colors[band2]) * (10 ** colors[multiplier])
    tolerance_value = f"{colors[tolerance]}%"
    if base_value >= 1e6:
        return f"{base_value / 1e6:.2f} MΩ", tolerance_value
    elif base_value >= 1e3:
        return f"{base_value / 1e3:.2f} kΩ", tolerance_value
    else:
        return f"{base_value:.2f} Ω", tolerance_value

# Функция для создания кнопок с цветами
def create_color_buttons(color_list, prefix):
    buttons = []
    row = []
    for color in color_list:
        button_text = f"{color_emojis[color]} {color}"
        row.append(types.InlineKeyboardButton(text=button_text, callback_data=f"{prefix}_{color}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return types.InlineKeyboardMarkup(buttons)

# Функция для взаимодействия с нейросетью
def ai_speak(text):
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo-1106", messages=[{"role": "user", "content": text}]
        )
        return chat_completion.choices[0].message['content']
    except Exception as e:
        logger.error(f"Error communicating with OpenAI: {e}")
        return "Ошибка при общении с нейросетью."

# Функция для озвучивания текста
def text_to_speech(text, filename="output.mp3"):
    tts = gTTS(text=text, lang='ru')
    tts.save(filename)
    return filename

# Основная функция бота
bot = TeleBot("***")  # Замените на токен вашего бота

def send_voice_message(chat_id, text):
    audio_file = text_to_speech(text)
    with open(audio_file, 'rb') as audio:
        bot.send_voice(chat_id, audio)

@bot.message_handler(commands=['start'])
def start(message):
    text = "Привет, дорогой пользователь! Давайте определим номинал вашего резистора. Выберите цвет первого кольца."
    keyboard = create_color_buttons(band_colors, "band1")
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    send_voice_message(message.chat.id, text)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    state = bot.user_data.get(call.from_user.id, {})

    if "band1" in data:
        state['band1'] = data.split('_')[1]
        text = f"Вы выбрали {state['band1']} для первого кольца. Теперь выберите цвет второго кольца."
        keyboard = create_color_buttons(band_colors, "band2")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
        send_voice_message(call.message.chat.id, text)

    elif "band2" in data:
        state['band2'] = data.split('_')[1]
        text = f"Вы выбрали {state['band2']} для второго кольца. Теперь выберите цвет третьего кольца (множитель)."
        keyboard = create_color_buttons(multiplier_colors, "multiplier")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
        send_voice_message(call.message.chat.id, text)

    elif "multiplier" in data:
        state['multiplier'] = data.split('_')[1]
        text = f"Вы выбрали {state['multiplier']} для третьего кольца. Теперь выберите цвет четвертого кольца (допуск)."
        keyboard = create_color_buttons(tolerance_colors, "tolerance")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
        send_voice_message(call.message.chat.id, text)

    elif "tolerance" in data:
        state['tolerance'] = data.split('_')[1]
        resistance, tolerance = calculate_resistance(state['band1'], state['band2'], state['multiplier'], state['tolerance'])
        text = f"Ваш резистор имеет номинал {resistance} с допуском {tolerance}. Спасибо за использование нашего бота!"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
        send_voice_message(call.message.chat.id, text)

    bot.user_data[call.from_user.id] = state

# Основная функция для запуска бота
def main():
    bot.polling()

if __name__ == '__main__':
    bot.user_data = {}
    main()







