from bs4 import BeautifulSoup
import telebot
from telebot import types
import sqlite3
import time
import requests
import random

bot = telebot.TeleBot('5812525194:AAHEfg_WfkIEp-Q6c3N2ZSy4qpFqtvbpi30')

conn = sqlite3.connect('planner.sql')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                  (user_id INTEGER,
                  id INTEGER PRIMARY KEY,
                  task TEXT,
                  completed INTEGER DEFAULT 0)''')
conn.commit()
cursor.close()
conn.close()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, f'Привет, <b>{message.from_user.first_name}!</b>', parse_mode='html')
    if check_subscription(message.chat.id):
        bot.send_message(message.chat.id, '<i>Давай начнем</i>!\n'
                                          '<i>Я помогу тебе с планированием твоих дел!</i>\n\n'
                                          'Для начала работы перейди в меню /menu\n'
                                          'Не знаешь как работать? Переходи к руководству /about', parse_mode='html')
    else:
        bot.send_message(message.chat.id, "Для использования бота подпишитесь на канал @RICHMAN_Channel.\n"
                                          "Затем перезапустите бота")

    while True:
        scheduled_time_voice = "21:00"
        scheduled_time_image = "14:00"
        scheduled_time_text = "7:00"
        if time.strftime('%H:%M') == scheduled_time_voice:
            i = random.randint(1, 120)
            audio_file = open(f'voices/{i}.ogg', 'rb')
            bot.send_audio(message.chat.id, audio=audio_file)
        if time.strftime('%H:%M') == scheduled_time_image:
            response = requests.get('https://coolsen.ru/200-motiviruyushhih-kartinok-u-tebya-vse-poluchitsya/')
            soup = BeautifulSoup(response.text, 'html.parser')
            images = soup.find_all('img')
            image = random.choice(images)['src']
            bot.send_photo(message.chat.id, image)
        if time.strftime('%H:%M') == scheduled_time_text:
            bot.send_message(message.chat.id, '<i>Доброе утро! Пора распланировать сегодняшний день)</i>', parse_mode='html')
        time.sleep(60)


def check_subscription(chat_id):
    try:
        chat_member = bot.get_chat_member('@RICHMAN_Channel', chat_id)
        if chat_member.status == 'member' or chat_member.status == 'creator':
            return True
        else:
            return False
    except telebot.apihelper.ApiException as e:
        print(e)
        return False


# Обработчик команды /menu
@bot.message_handler(commands=['menu'])
def menu(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if check_subscription(message.chat.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('📅 РАСПИСАНИЕ')
        btn2 = types.KeyboardButton('📚 КНИГИ')
        btn3 = types.KeyboardButton('🔖 ЧЕК-ЛИСТЫ')
        btn4 = types.KeyboardButton('Порекомендовать друзьям')
        markup.row(btn1)
        markup.row(btn2, btn3)
        markup.row(btn4)
        bot.send_message(message.chat.id, 'Выбери пункт меню', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Для использования бота подпишитесь на канал @RICHMAN_Channel\n"
                                          "Затем перезапустите бота")


# Вызов меню Расписания
@bot.message_handler(func=lambda message: message.text == '📅 РАСПИСАНИЕ')
def callback_message_rs(message):
    bot.send_chat_action(message.chat.id, 'typing')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Посмотреть Задачи 📋')
    btn2 = types.KeyboardButton('Добавить Задачу ➕')
    btn3 = types.KeyboardButton('Удалить Задачу ➖')
    btn4 = types.KeyboardButton('Выполнить Задачу ✅')
    btn5 = types.KeyboardButton('Удалить все задачи ❌')
    btn6 = types.KeyboardButton('Назад ↩️')
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.row(btn4, btn5)
    markup.row(btn6)

    bot.send_message(message.chat.id, 'Выбери то, что тебе необходимо', reply_markup=markup)


# Обработка действий с расписанием
@bot.message_handler(func=lambda message: message.text == 'Посмотреть Задачи 📋')
def callback_check_list(message):
    bot.send_chat_action(message.chat.id, 'typing')
    conn_list = sqlite3.connect('planner.sql')
    cursor_list = conn_list.cursor()
    user_id = message.chat.id
    cursor_list.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    tasks = cursor_list.fetchall()

    if not tasks:
        bot.send_message(message.chat.id, '<i>Список задач пуст</i>', parse_mode='html')
    else:
        bot.send_message(message.chat.id, '<i>Ваши текущие задачи</i>', parse_mode='html')
        task_list = ''
        for task in tasks:
            task_id_list, task_text_list, completed_list = task[1:]  # передается 4 значения, а ожидается 3
            status = '✅' if completed_list else '❌'
            task_list += f'{task_id_list}. {task_text_list} {status}\n'

        bot.send_message(message.chat.id, task_list)

    conn_list.commit()
    cursor_list.close()
    conn_list.close()


@bot.message_handler(func=lambda message: message.text == 'Добавить Задачу ➕')
def callback_add_task(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, '<i>Введи задачу в формате: номер.задача</i>', parse_mode='html')

    bot.register_next_step_handler(message, text_add)


def text_add(anymessage):
    try:
        bot.send_chat_action(anymessage.chat.id, 'typing')
        conn_add = sqlite3.connect('planner.sql')
        cursor_add = conn_add.cursor()
        id_add = anymessage.text.split('.')[0]
        user_id = anymessage.chat.id

        cursor_add.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, id_add))
        existing_task = cursor_add.fetchone()

        if existing_task:
            bot.send_message(anymessage.chat.id, '<i>Задача с таким номером уже существует.</i>\n'
                                                 '<i>Попробуйте ещё раз.</i>', parse_mode='html')
        else:
            if int(id_add) <= 0 or str():
                bot.send_message(anymessage.chat.id, '<i>Номер задачи введен некорректно.</i>\n'
                                                     '<i>Попробуйте ещё раз.</i>', parse_mode='html')
            else:
                task_add = anymessage.text.split('.')[1].strip()
                cursor_add.execute("INSERT INTO tasks (user_id, id, task) VALUES (?, ?, ?)",
                                   (user_id, id_add, task_add))
                conn_add.commit()

                bot.send_message(anymessage.chat.id, '<i>Задача добавлена в список.</i>', parse_mode='html')

        cursor_add.close()
        conn_add.close()
    except ValueError:
        bot.send_message(anymessage.chat.id, '<i>Некорректное значение</i>\n'
                                             '<i>Попробуйте ещё раз.</i>', parse_mode='html')
    finally:
        callback_message_rs(anymessage)


@bot.message_handler(func=lambda message: message.text == 'Удалить Задачу ➖')
def callback_remove_task(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, '<i>Введи номер задачи, которую вы хотите удалить:</i>', parse_mode='html')

    bot.register_next_step_handler(message, text_rem)


def text_rem(difmessage):
    bot.send_chat_action(difmessage.chat.id, 'typing')
    try:
        conn_remove = sqlite3.connect('planner.sql')
        cursor_remove = conn_remove.cursor()
        task_id_delete = difmessage.text
        user_id = difmessage.chat.id

        # Проверяем, существует ли задача с указанным номером
        cursor_remove.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, task_id_delete))
        existing_task = cursor_remove.fetchone()

        if existing_task:
            cursor_remove.execute("DELETE FROM tasks WHERE user_id=? AND id=?", (user_id, task_id_delete))
            conn_remove.commit()
            bot.send_message(difmessage.chat.id, '<i>Задача удалена из списка.</i>', parse_mode='html')
        else:
            bot.send_message(difmessage.chat.id, '<i>Такой задачи не существует.</i>\n'
                                                 '<i>Попробуйте ещё раз.</i>', parse_mode='html')

        cursor_remove.close()
        conn_remove.close()

    finally:
        callback_message_rs(difmessage)


@bot.message_handler(func=lambda message: message.text == 'Выполнить Задачу ✅')
def callback_complete_task(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, '<i>Введи номер задачи, которую вы хотите отметить как выполненную:</i>',
                     parse_mode='html')

    bot.register_next_step_handler(message, text_complete)


def text_complete(onemessage):
    bot.send_chat_action(onemessage.chat.id, 'typing')
    conn_complete = sqlite3.connect('planner.sql')
    cursor_complete = conn_complete.cursor()
    task_id = onemessage.text
    user_id = onemessage.chat.id

    cursor_complete.execute("SELECT * FROM tasks WHERE user_id=? AND id=?", (user_id, task_id))
    existing_task = cursor_complete.fetchone()

    if existing_task:
        cursor_complete.execute("UPDATE tasks SET completed=1 WHERE user_id=? AND id=?", (user_id, task_id))
        conn_complete.commit()
        bot.send_message(onemessage.chat.id, '<i>Задача отмечена как выполненная.</i>', parse_mode='html')
    else:
        bot.send_message(onemessage.chat.id, '<i>Такой задачи не существует.</i>\n'
                                             '<i>Попробуйте ещё раз.</i>', parse_mode='html')

    cursor_complete.close()
    conn_complete.close()

    callback_message_rs(onemessage)


@bot.message_handler(func=lambda message: message.text == 'Удалить все задачи ❌')
def callback_delete_all_task(message):
    bot.send_chat_action(message.chat.id, 'typing')
    conn_delete = sqlite3.connect('planner.sql')
    cursor_delete = conn_delete.cursor()
    user_id = message.chat.id
    cursor_delete.execute("DELETE FROM tasks WHERE user_id=?", (user_id,))
    conn_delete.commit()
    cursor_delete.close()
    conn_delete.close()

    bot.send_message(message.chat.id, '<i>Все задачи удалены</i>', parse_mode='html')


@bot.message_handler(func=lambda message: message.text == 'Назад ↩️')
def callback_back(message):
    menu(message)


# Вызов и Обработка Книг
@bot.message_handler(func=lambda message: message.text == '📚 КНИГИ')
def callback_message_books(message):
    bot.send_chat_action(message.chat.id, 'upload_photo')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Скачать с Яндекс диск📀', url='https://disk.yandex.com.am/d/g4bAG-UUA03wkw'))
    markup.add(types.InlineKeyboardButton('Скачать с Гугл диск💿', url='https://drive.google.com/drive/folders'
                                                                      '/13eAWUd8ZaWuRn3NtVRKu8eIqL52r8_Bf'))

    file = open('photo/books.jpg', 'rb')
    bot.send_photo(message.chat.id, file, reply_markup=markup)


# Вызов Чек-листов
@bot.message_handler(func=lambda message: message.text == '🔖 ЧЕК-ЛИСТЫ')
def callback_message_lists(message):
    bot.send_chat_action(message.chat.id, 'typing')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🧠 Интеллект', callback_data='intel'))
    markup.add(types.InlineKeyboardButton('💬 Мастер Общения', callback_data='com'))
    markup.add(types.InlineKeyboardButton('😎 Харизма', callback_data='xar'))
    markup.add(types.InlineKeyboardButton('🎥 5 Вдохновляющих фильмов', callback_data='films'))
    markup.add(types.InlineKeyboardButton('👔 Волшебная одежда', callback_data='clothes'))

    bot.send_message(message.chat.id, 'Выбери один из Чек-Листов!', reply_markup=markup)


# Обработка Чек-листов
@bot.callback_query_handler(func=lambda callback: callback.data == 'intel')
def one(callback):
    bot.send_chat_action(callback.message.chat.id, 'upload_document')
    file = open('cheks/intel.pdf', 'rb')
    bot.send_document(callback.message.chat.id, file, caption='Интеллект: как стать умнее? \n\n'
                                                              '📌 Не забудь сохранить и поделиться им с другом.')


@bot.callback_query_handler(func=lambda callback: callback.data == 'com')
def two(callback):
    bot.send_chat_action(callback.message.chat.id, 'upload_document')
    file = open('cheks/com.pdf', 'rb')
    bot.send_document(callback.message.chat.id, file, caption='💬 Мастер Общения\n\n'
                                                              '📌Не забудь сохранить и поделиться им с другом.')


@bot.callback_query_handler(func=lambda callback: callback.data == 'xar')
def three(callback):
    bot.send_chat_action(callback.message.chat.id, 'upload_document')
    file = open('cheks/xar.pdf', 'rb')
    bot.send_document(callback.message.chat.id, file, caption='😎 Харизма как у Томаса Шелби\n\n'
                                                              '📌 Не забудь сохранить и поделиться им с другом.')


@bot.callback_query_handler(func=lambda callback: callback.data == 'films')
def three(callback):
    bot.send_chat_action(callback.message.chat.id, 'upload_document')
    file = open('cheks/films.pdf', 'rb')
    bot.send_document(callback.message.chat.id, file, caption='🎥 5 Самых Вдохновляющих Фильмов\n\n'
                                                              '📌 Не забудь сохранить и поделиться им с другом.')


@bot.callback_query_handler(func=lambda callback: callback.data == 'clothes')
def three(callback):
    bot.send_chat_action(callback.message.chat.id, 'upload_document')
    file = open('cheks/clothes.pdf', 'rb')
    bot.send_document(callback.message.chat.id, file, caption='👔 Волшебная одежда\n\n'
                                                              '📌 Не забудь сохранить и поделиться им с другом.')


@bot.message_handler(func=lambda message: message.text == 'Порекомендовать друзьям')
def callback_message_recomendation(message):
    pass


@bot.message_handler(commands=['about'])
def about(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, '<strong>Руководство по использованию</strong>\n\n'
                                      'Привет! Я - твой персональный помощник по планированию дел. '
                                      'Я помогу тебе структурировать твой день и не пропустить важные задачи.\n\n'
                                      'Чтобы начать работу со мной, введи команду /start.\n'
                                      'Если ты уже работал со мной раньше, можешь перейти сразу в меню командой /menu.\n\n'
                                      '❗️<i>Для использования всех функций бота, подпишись на канал @RICHMAN_Channel</i>.\n'
                                      '<i>После подписки перезапусти бота, чтобы активировать все функции.</i>❗️\n\n'
                                      'В меню /menu ты найдешь следующие пункты:\n'
                                      'РАСПИСАНИЕ, КНИГИ и ЧЕК-ЛИСТЫ.\n'
                                      'Выбери нужный пункт, чтобы получить доступ к соответствующей функции.\n\n'
                                      '- <strong>РАСПИСАНИЕ</strong> позволяет просматривать, добавлять, удалять и отмечать задачи как выполненные.\n'
                                      'Чтобы просмотреть текущие задачи, выбери пункт "Посмотреть Задачи 📋".\n'
                                      'Чтобы добавить новую задачу, выбери "Добавить Задачу ➕" и следуй инструкциям.\n'
                                      'Чтобы удалить задачу, выбери "Удалить Задачу ➖" и введи номер задачи.\n'
                                      'Чтобы отметить задачу как выполненную, выбери "Выполнить Задачу ✅" и введи номер задачи.\n'
                                      'Чтобы удалить все задачи, выбери "Удалить все задачи ❌".\n\n'
                                      '- <strong>КНИГИ</strong> позволяет скачать полезные книги для развития.\n'
                                      'Чтобы скачать книгу с Яндекс диска, выбери "Скачать с Яндекс диск📀".\n'
                                      'Чтобы скачать с Гугл диска, выбери "Скачать с Гугл диск💿".\n\n'
                                      '- <strong>ЧЕК-ЛИСТЫ</strong> позволяет скачать полезные чек-листы для повышения эффективности и развития.\n'
                                      'Чтобы выбрать чек-лист, выбери соответствующий пункт в меню.\n\n'
                                      'Пользуйся ботом с удовольствием!\n'
                                      'Если у тебя возникнут вопросы или проблемы, можешь обратиться к @Richman_IT.\n\n'
                                      '<b><i>Удачного планирования!</i></b>', parse_mode='html')


@bot.message_handler(commands=['help'])
def about(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, '<i>Возникли вопросы? Пиши: @Richman_IT.</i>\n'
                                      '<i>Удачного пользования!</i>', parse_mode='html')


@bot.message_handler(content_types=['text'])
def get_random_text(message):
    bot.send_message(message.chat.id, '<i>Извини, но я не понимаю тебя,</i>\n'
                                      '<i>Используй функции бота.</i>\n\n'
                                      '<i>Не знаешь как использовать бота? Нажимай /help </i>', parse_mode='html')


bot.polling(none_stop=True)
