import telebot
import sqlite3
import secrets

# Замените на ваш токен
BOT_TOKEN = "12345678_qwaszxerfdcvtyghbnuijkm"
# Замените на ID администратора
ADMIN_ID = 12345678

bot = telebot.TeleBot(BOT_TOKEN)

# Подключение к базе данных (используем ваше подключение)
conn = sqlite3.connect('anon_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Проверка и создание таблиц - уже есть в вашем коде, оставляем как есть
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        unique_code TEXT UNIQUE
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    recipient_id INTEGER,
    message TEXT,
    reply_to INTEGER DEFAULT NULL,  -- ID родительского сообщения
    message_level INTEGER DEFAULT 0,
    content_type TEXT DEFAULT 'text',
    file_id TEXT DEFAULT NULL,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id),
    FOREIGN KEY (reply_to) REFERENCES messages(id)
    )
''')
conn.commit()

# Функция для получения всех ID пользователей из базы данных
def get_all_user_ids(db_cursor):
    """
    Получает все ID пользователей из таблицы users.
    """
    db_cursor.execute("SELECT user_id FROM users")
    rows = db_cursor.fetchall()
    return [row[0] for row in rows]

# Обработчик команды /broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else None
        if text:
            # Используем уже существующее подключение к базе данных
            try:
                user_ids = get_all_user_ids(cursor)

                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, text,parse_mode= "Markdown")
                    except telebot.apihelper.ApiTelegramException as e:
                        if e.result_json['description'] == 'Forbidden: bot was blocked by the user':
                            print(f"Пользователь {user_id} заблокировал бота.")
                            # Опционально: удаление пользователя из базы
                            # cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                            # conn.commit()
                        else:
                            print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
                    except Exception as e:
                        print(f"Непредвиденная ошибка при отправке сообщения пользователю {user_id}: {e}")
                bot.reply_to(message, "Сообщение отправлено!")
            except Exception as e:
                print(f"Ошибка при работе с базой: {e}")
                bot.reply_to(message, "Произошла ошибка при отправке сообщения.")

        else:
            bot.reply_to(message, "Введите текст для рассылки после команды /broadcast")

    else:
        bot.reply_to(message, "Неизвестная команда. /help")

# Функции для работы с базой данных
def get_user_code(user_id):
    cursor.execute("SELECT unique_code FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_user_id_by_code(code):
    cursor.execute("SELECT user_id FROM users WHERE unique_code = ?", (code,))
    result = cursor.fetchone()
    return result[0] if result else None

def add_user(user_id, unique_code):
    cursor.execute("INSERT INTO users (user_id, unique_code) VALUES (?, ?)", (user_id, unique_code))
    conn.commit()

def add_message(sender_id, recipient_id, message, reply_to=None, message_level=0, content_type='text', file_id=None):
    cursor.execute("INSERT INTO messages (sender_id, recipient_id, message, reply_to, message_level, content_type, file_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (sender_id, recipient_id, message, reply_to, message_level, content_type, file_id))
    conn.commit()
    return cursor.lastrowid

def get_message(message_id):
    cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    return cursor.fetchone()

#####################################
#####################################
#####################################
#####################################
#####################################
#####################################

@bot.message_handler(commands=['start','link'])
def start(message):
    user_id = message.from_user.id
    if len(message.text.split()) > 1:
        handle_start_with_code(message)
        return
    user_code = get_user_code(user_id)
    if not user_code:
        unique_code = secrets.token_urlsafe(8)
        add_user(user_id, unique_code)
        link = f"t.me/{bot.get_me().username}?start={unique_code}"
        bot.send_message(user_id,f"🚀 Добро пожаловать в бота для получения анонимных сообщений!\n\nКак это работает?🤔\n\n1) Вы получаете уникальную ссылку и размещаете её где угодно (например , описание профиля) 🔗\n2) Любой желающий может отправить вам анонимное сообщение , фото , видео , GIF или стикер! 📩\n3) После получения анонимного сообщения вы можете на его ответить , поддерживая анонимный разговор 🚀\n\nЧего ты ждёшь? Нажимай на /link и начни получать анонимные вопросы уже сегодня! 🚀")
        bot.send_message(user_id, f"🔗 Ваша ссылка для анонимных сообщений:\n{link}")
    else:
        link = f"t.me/{bot.get_me().username}?start={user_code}"
        bot.send_message(user_id, f"🔗 Ваша ссылка уже создана:\n{link}")

@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.from_user.id
    bot.send_message(user_id,f"Как это работает?🤔\n\n1) Вы получаете уникальную ссылку и размещаете её где угодно (например , описание профиля) 🔗\n2) Любой желающий может отправить вам анонимное сообщение , фото , видео , GIF или стикер! 📩\n3) После получения анонимного сообщения вы можете на его ответить , поддерживая анонимный разговор 🚀/")

@bot.message_handler(commands=['stats'])
def stats(message):
    bot.send_message(message.from_user.id, f"📊 Статистика вашей ссылки за последние... А где она?\n\nМы не собираем подобного рода информацию в целях конфиденциальности. Поэтому , вы можете доверять боту 😉")

# Обработка перехода по ссылке
def handle_start_with_code(message):
    code = message.text.split()[1]
    recipient_id = get_user_id_by_code(code)
    if recipient_id:
        bot.send_message(message.from_user.id, "📩 Вы можете отправить анонимное сообщение этому пользователю. Введите ваше сообщение или отправьте фото, видео, GIF или стикер:")
        bot.register_next_step_handler(message, lambda msg: process_anonymous_message(msg, recipient_id))
    else:
        bot.send_message(message.from_user.id, "Что-то пошло не так 🤔")

# Обработка анонимных сообщений (текст, фото, видео, GIF, стикер)
def process_anonymous_message(message, recipient_id):
    sender_id = message.from_user.id
    content_type = message.content_type
    file_id = None
    caption = None

    if content_type == 'photo':
        file_id = message.photo[-1].file_id
        caption = message.caption
    elif content_type == 'video':
        file_id = message.video.file_id
        caption = message.caption
    elif content_type == 'animation':
        file_id = message.animation.file_id
        caption = message.caption
    elif content_type == 'sticker':
        file_id = message.sticker.file_id
    elif content_type == 'text':
        pass # Текстовые сообщения обрабатываются как и раньше
    else:
        bot.send_message(sender_id, "Данный тип сообщения не поддерживается :(")
        return

    message_id = add_message(sender_id, recipient_id, message.text if content_type == 'text' else caption, content_type=content_type, file_id=file_id)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Ответить 💌", callback_data=f"reply_{message_id}"))

    if content_type == 'text':
        bot.send_message(recipient_id, f"Вам пришло новое анонимное сообщение! 💌\n\n{message.text}", reply_markup=markup)
    elif content_type == 'photo':
        bot.send_photo(recipient_id, file_id, caption=f"Вам пришло новое анонимное сообщение! 💌\n\n{caption if caption else ''}", reply_markup=markup)
    elif content_type == 'video':
        bot.send_video(recipient_id, file_id, caption=f"Вам пришло новое анонимное сообщение! 💌\n\n{caption if caption else ''}", reply_markup=markup)
    elif content_type == 'animation':
        bot.send_animation(recipient_id, file_id, caption=f"Вам пришло новое анонимное сообщение! 💌\n\n{caption if caption else ''}", reply_markup=markup)
    elif content_type == 'sticker':
        bot.send_sticker(recipient_id, file_id, reply_markup=markup)
    bot.send_message(sender_id, "💬")
    bot.send_message(sender_id, "🚀 Ваше сообщение отправлено!")

# Обработка нажатия на кнопку "Ответить"
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def callback_reply(call):
    message_id = int(call.data.split('_')[1])
    bot.send_message(call.from_user.id, f"📩 Введите ответ на сообщение или отправьте фото, видео или GIF:")
    bot.register_next_step_handler(call.message, lambda msg: process_reply_to_message(msg, message_id))

# Обработка ответа на сообщение
def process_reply_to_message(message, reply_to_id):
    sender_id = message.from_user.id
    original_message = get_message(reply_to_id)

    if original_message:
        recipient_id = original_message[1]
        message_level = original_message[5] + 1
        content_type = message.content_type
        file_id = None
        caption = None

        if content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption
        elif content_type == 'video':
            file_id = message.video.file_id
            caption = message.caption
        elif content_type == 'animation':
            file_id = message.animation.file_id
            caption = message.caption
        elif content_type == 'sticker':
            bot.send_message(sender_id,"Стикеры нельзя отправлять в ответ!")
        elif content_type == 'text':
            pass # Текстовые сообщения обрабатываются как и раньше
        else:
            bot.send_message(sender_id, "Данный тип сообщения не поддерживается.")
            return

        reply_message_id = add_message(sender_id, recipient_id, message.text if content_type == 'text' else caption, reply_to=reply_to_id, message_level=message_level, content_type=content_type, file_id=file_id)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Ответить 💌", callback_data=f"reply_{reply_message_id}"))

        indent = "" * message_level
        if content_type == 'text':
            bot.send_message(recipient_id, f"💌 Ответ на сообщение:\n\n{indent}{message.text}", reply_markup=markup)
        elif content_type == 'photo':
            bot.send_photo(recipient_id, file_id, caption=f"💌 Ответ на сообщение:\n\n{indent}{caption if caption else ''}", reply_markup=markup)
        elif content_type == 'video':
            bot.send_video(recipient_id, file_id, caption=f"💌 Ответ на сообщение:\n\n{indent}{caption if caption else ''}", reply_markup=markup)
        elif content_type == 'animation':
            bot.send_animation(recipient_id, file_id, caption=f"💌 Ответ на сообщение:\n\n{indent}{caption if caption else ''}", reply_markup=markup)
        elif content_type == 'sticker':
            bot.send_sticker(recipient_id, file_id, reply_markup=markup)
        bot.send_message(sender_id, f"🚀 Ваш ответ на сообщение отправлен!")
    else:
        bot.send_message(sender_id, "🤔 Что-то пошло не так\n\nВозможно , бот был обновлён\n\n📩 Если есть возможность , попросите владельца ссылки обновить её через бота.")

@bot.message_handler(commands=['disable_link'])
def disable_link(message):
    bot.send_message(message.from_user.id,f'🚫 Отключить ссылку вы можете , написав в поддержку бота (см. описание бота)')

bot.infinity_polling()
