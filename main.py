import logging
import requests
from datetime import datetime, timedelta, timezone
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import json
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

recovered, duration, smell, training_before, training_before_duration, timeset, utc_1, choice, start_test, reminder_day, reminder_setup_today, reminder_setup_tomorrow = range(12)

logger = logging.getLogger(__name__)

# UTC
# UTC
# UTC

def create_callback_zone(action, num):
    """ Create the callback data associated to each button"""
    return ";".join([action, str(num)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_timezone(num=None):
    keyboard = []
    if not num:
        num = 0

    data_ignore = create_callback_zone("IGNORE", num)

    row = []
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    row.append(InlineKeyboardButton("↑", callback_data=create_callback_zone("PLUS", num)))
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    keyboard.append(row)

    row = []
    row.append(InlineKeyboardButton("UTC", callback_data=data_ignore))
    if num >= 0:
        row.append(InlineKeyboardButton(f"+ {num}", callback_data=data_ignore))
    else:
        row.append(InlineKeyboardButton(f"- {abs(num)}", callback_data=data_ignore))
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    row.append(InlineKeyboardButton("OK", callback_data=create_callback_zone("OKAY", num)))
    keyboard.append(row)

    row = []
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    row.append(InlineKeyboardButton("↓", callback_data=create_callback_zone("MINUS", num)))
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def process_utc_selection(bot, update):
    data = (False, None)
    query = update.callback_query
    (action, num) = separate_callback_data(query.data)
    num = int(num)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=query.id)

    elif action == "OKAY":
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
            )
        data = True, num

    elif action == "PLUS" and num <= 13:
        num += 1
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_timezone(num))

    elif action == "MINUS" and num >= -11:
        num -= 1
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_timezone(num))

    return data

# JSON
# JSON
# JSON

def json_secret_name(names=None):
    with open("names.json", "r+") as file:
        content = json.load(file)
        if names is None:
            return content["user_names"]["users"]
        else:
            content["user_names"]["users"] = names

        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_editor(user, key=None, value=None):
    user = str(user)
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if user not in content["reminder"].keys():
            content["reminder"][user] = {"utc": 3, "reminder": [], "scents": []}

        if len(content["reminder"][user]["reminder"]) == 0:
            content["reminder"][user]["reminder"].insert(0, {})

        content["reminder"][user]["reminder"][0][key] = value

        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_getter(user, ):
    with open("reminder.json") as file:
        content = json.load(file)
        element = content["reminder"][user]["reminder"][0]
        _time = element["time"]
        r_id = element["id"]

        return _time, r_id
        

def json_deleter(user, r_id=None, current=False):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        reminder = content["reminder"][user]["reminder"]
        if not current:
            for i in range(len(reminder)):
                if reminder[i]["id"] == r_id:
                    del reminder[i]
                    break
        else:
            del reminder[0]
            
        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_utc(user, utc=None):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if utc is None:
            return content["reminder"][user]["utc"]
        else:
            content["reminder"][user]["utc"] = utc
            file.seek(0)
            json.dump(content, file)
            file.truncate()


def json_scents(user, scents=None):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if scents is None:
            return content["reminder"][user]["scents"]
        else:
            content["reminder"][user]["scents"] = scents
            file.seek(0)
            json.dump(content, file)
            file.truncate()


def json_ans_editor(user):
    with open("answers.json", "r+") as file:
        content = json.load(file)
        if user not in content["my_users"].keys():
            content["my_users"][user] = {"answers": []}

        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_ans(user, answers=None):
    with open("answers.json", "r+") as file:
        content = json.load(file)
        if answers is None:
            return content["my_users"][user]["answers"]
        else:
            content["my_users"][user]["answers"] = answers
            file.seek(0)
            json.dump(content, file)
            file.truncate()


def json_special_getter(usernames):
    with open("answers.json") as file:
        content = json.load(file)
        output = []
        
        for i in usernames:
            output.append(i)
            output.append(content["my_users"][i])

        return output


def json_reminder_list(user):
    with open("reminder.json") as file:
        content = json.load(file)

        if len(content["reminder"][user]["reminder"]) == 0:
            return 0
        else:
            return 1

# SEND PHOTO
# SEND PHOTO 
# SEND PHOTO 

def sendImage(img_url, message):
    url = "https://api.telegram.org/bot{}/sendPhoto".format("1925710739:AAGs3ARdPPScQyUu_LZNjmUbhtUhKWRqhw8");

    files = {'photo': open('photos/{}'.format(img_url), 'rb')}
    data = {'chat_id' : message.chat.id}

    r = requests.post(url, files=files, data=data)
    print(r.status_code, r.reason, r.content)
 

# TIME ZONE
# TIME ZONE
# TIME ZONE

def utc_time(update, context):
    update.message.reply_text("Выбери временную зону, в которой проживаешь", reply_markup=create_timezone())
    return utc_1


def utc_1_ans(update, context):
    reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback", "/reminer_stop"]]
    selected, num = process_utc_selection(context.bot, update)
    if selected:
        chat_id = str(update.callback_query.from_user.id)
        json_utc(chat_id, utc=num)
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=f"Ты выбрал + {num}" if num >= 0 else f"Ты выбрал UTC - {abs(num)}",
                        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

        return ConversationHandler.END

# REMINDER
# REMINDER
# REMINDER

def notification(context):
    job = context.job
    _update = job.context[4]
    chat_id = str(_update.message.chat.id)

    if json_reminder_list(chat_id) == 1:
        if len(job.context) == 5:
            _time, username, r_id = job.context[1], job.context[2], job.context[3]
            context.bot.send_message(job.context[0], text=f"\U0001F4A1* Reminder *\U0001F4A1\n\nНапоминание: Время - {_time}.", parse_mode="markdown")
        
        json_deleter(username, r_id=r_id)

    return ConversationHandler.END


def all_reminder(update, context):
    reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback"]]

    username = str(update.message["chat"]["id"])
    with open("reminder.json") as file:
        content = json.load(file)
        reminder = content["reminder"][username]["reminder"]

        if len(reminder) == 0 or reminder[0] == {'null': None}:
            update.message.reply_text(f"\U0001F4C3* Следующее напоминание *\U0001F4C3\n\nНапоминаний нет!", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        else:
            update.message.reply_text("\U0001F4CB* Следующее напоминание *\U0001F4CB", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

            _time = reminder[0]["time"]

            update.message.reply_text(f"Time: {_time}")

    ConversationHandler.END


def reminder(update, context):
    reply_keyboard = [["Сегодня", "Завтра"]]
 
    update.message.reply_text("\U0001F553* Создание напоминания *\U0001F553\n\nНа какой день хочешь поставить напоминание?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

    return reminder_day


def reminder_setup_tomorrow_ans(update, context):
    ans_reminder_time = update.message.text

    chat_id = str(update.message.chat.id)
    r_id = random.randint(0, 100000)

    reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback", "/reminder_stop"]]

    if len(ans_reminder_time) == 5 and ans_reminder_time[:2].isnumeric() and ans_reminder_time[3:].isnumeric() and int(ans_reminder_time[:2]) >= 0 and int(ans_reminder_time[:2]) <= 24 and int(ans_reminder_time[3:]) <= 59 and int(ans_reminder_time[3:]) >= 0 and ans_reminder_time[2] == ":":

        if int(ans_reminder_time[:2]) == 24:
            ans_reminder_time = ans_reminder_time.replace('24', '00')

        json_editor(chat_id, "time", ans_reminder_time)
        json_editor(chat_id, "id", r_id)

        chat_id = str(update.message["chat"]["id"])
        format_time, r_id = json_getter(chat_id)
        num = json_utc(chat_id)

        hour, minute = int(ans_reminder_time[:2]), int(ans_reminder_time[3:])
        hourss = ans_reminder_time[:2]
        minutess = ans_reminder_time[3:]

        tzinfo = timezone(timedelta(hours=num))
        datetime.now(tzinfo)
        
        today = str(datetime.now(tzinfo))

        the_day = today[8:10]
        the_month = today[5:7]
        the_year = today[:4]
        the_date = the_day + "/" + the_month + "/" + the_year

        seconds = datetime.timestamp(datetime.strptime(the_date, "%d/%m/%Y") + timedelta(hours=hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600)) + 86400

        print(seconds)

        if seconds < 0:
            context.bot.send_message(chat_id=chat_id, text=f"\U0000274C* Ошибка напоминания *\U0000274C\n\nВыбранное время находится в прошлом", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
            json_deleter(chat_id, r_id=r_id)
            context.bot.send_message(chat_id=update.message.chat.id, text="\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра", parse_mode="markdown")

            return reminder_setup_tomorrow

        else:
            context.bot.send_message(chat_id=chat_id,
                                        text=f"*\U0001F4CC Напоминание сохранено *\U0001F4CC\n\nВремя: {hourss}:{minutess}\nНажми /reminder_stop чтобы отменить напоминание", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

            context.job_queue.run_once(notification, seconds, context=[chat_id, format_time, chat_id, r_id, update], name=chat_id)

            return ConversationHandler.END


    else:
        update.message.reply_text("\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        return reminder_setup_tomorrow
    
    return ConversationHandler.END


def reminder_day_ans(update, context):
    ans_reminder_day = update.message.text

    if ans_reminder_day == "Сегодня":
        update.message.reply_text("\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра")

        return reminder_setup_today

    elif ans_reminder_day == "Завтра":
        update.message.reply_text("\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра")

        return reminder_setup_tomorrow
        

def reminder_setup_today_ans(update, context):
    ans_reminder_time = update.message.text

    chat_id = str(update.message.chat.id)
    r_id = random.randint(0, 100000)

    reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback", "/reminder_stop"]]

    if len(ans_reminder_time) == 5 and ans_reminder_time[:2].isnumeric() and ans_reminder_time[3:].isnumeric() and int(ans_reminder_time[:2]) >= 0 and int(ans_reminder_time[:2]) <= 24 and int(ans_reminder_time[3:]) <= 59 and int(ans_reminder_time[3:]) >= 0:

        if int(ans_reminder_time[:2]) == 24:
            ans_reminder_time = ans_reminder_time.replace('24', '00')

        json_editor(chat_id, "time", ans_reminder_time)
        json_editor(chat_id, "id", r_id)

        chat_id = str(update.message["chat"]["id"])
        format_time, r_id = json_getter(chat_id)
        num = json_utc(chat_id)

        hour, minute = int(ans_reminder_time[:2]), int(ans_reminder_time[3:])
        hourss = ans_reminder_time[:2]
        minutess = ans_reminder_time[3:]

        tzinfo = timezone(timedelta(hours=num))
        datetime.now(tzinfo)
        
        today = str(datetime.now(tzinfo))

        the_day = today[8:10]
        the_month = today[5:7]
        the_year = today[:4]
        the_date = the_day + "/" + the_month + "/" + the_year

        seconds = datetime.timestamp(datetime.strptime(the_date, "%d/%m/%Y") + timedelta(hours=hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600))

        if seconds < 0:
            context.bot.send_message(chat_id=chat_id, text=f"\U0000274C* Ошибка напоминания *\U0000274C\n\nВыбранное время находится в прошлом", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
            json_deleter(chat_id, r_id=r_id)
            context.bot.send_message(chat_id=update.message.chat.id, text="\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра")

            return reminder_setup_today

        else:
            context.bot.send_message(chat_id=chat_id,
                                        text=f"*\U0001F4CC Напоминание сохранено *\U0001F4CC\n\nВремя: {hourss}:{minutess}\nНажми /reminder_stop чтобы отменить напоминание", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

            context.job_queue.run_once(notification, seconds, context=[chat_id, format_time, chat_id, r_id, update], name=chat_id)

        return ConversationHandler.END

    else:
        update.message.reply_text("\U0001F553* Создание напоминания *\U0001F553\n\nНа какое время хочешь поставить следующее напоминание\nфомат - ЧЧ:ММ. Например, 09:50 это 9:50 утра", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        return reminder_setup_today
    

def cancel(update, context):
    username = str(update.message["chat"]["id"])
    logger.info("User %s canceled the reminder setup.", username)
    json_deleter(username, current=True)
    update.message.reply_text('\U0001F53A *Создание напоминания* \U0001F53A'
                              '\n\nНапоминание отменено')

    return ConversationHandler.END

def reminder_stop(update, context):
    username = str(update.message["chat"]["id"])
    logger.info("User %s canceled the reminder setup.", username)
    json_deleter(username, current=True)
    update.message.reply_text('\U0001F53A *Создание напоминания* \U0001F53A'
                              '\n\nНапоминание отменено', reply_markup=ReplyKeyboardRemove(), parse_mode="markdown")

    return ConversationHandler.END

# QUESTIONS
# QUESTIONS
# QUESTIONS

def start(update, context):
    reply_keyboard = [["Начать"]]
    username = str(update.message.chat.username)
    
    if username != "None" and username != None:
        json_ans_editor(username)
        json_ans(username, [])

    json_editor(update.message.chat.id)

    names = json_secret_name()

    if username not in names and username != "None" and username != None:
        names.append(username)
        json_secret_name(names)

    answers = json_ans(username)

    sent_text = "Привет, я бот, который будет помогать тебе тренировать обоняние и визуализировать запахи из основного набора для обонятельного тренинга (это эфирные масла: лимон, роза, гвоздика и эвкалипт). Чуть позже мы добавим и другие запахи."

    update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

    answers.append(sent_text)
    #json_ans(username, answers)

    return recovered


def recovered_ans(update, context):
    ans_begin = update.message.text

    username = str(update.message.chat.username)
    answers = json_ans(username)

    if ans_begin == "Начать":
        reply_keyboard = [["Да", "Нет"]]

        answers.append(ans_begin)

        sent_text = "Ответь, пожалуйста, на несколько вопросов) Переболел(а) ли ты COVID-19?"

        update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        answers.append(sent_text)
            
        json_ans(username, answers)

        return duration

    else:
        reply_keyboard = [["Начать"]]

        update.message.reply_text("Если хочешь лечиться, напиши \"Начать\"",
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      resize_keyboard=True))

        return recovered


def duration_ans(update, context):
    ans_recovered = update.message.text

    username = str(update.message.chat.username)
    answers = json_ans(username)

    if ans_recovered == "Да":
        reply_keyboard = [[
            "<1 месяца", "1-3 месяца", "3-6 месяцев", "6-9 месяцев",
            ">9 месяцев"
        ]]

        answers.append(ans_recovered)

        sent_text = "Сколько времени назад был отрицательный мазок на COVID-19/закончились симптомы?"

        update.message.reply_text(sent_text,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        answers.append(sent_text)

        json_ans(username, answers)

        return smell

    elif ans_recovered == "Нет":
        return smell_ans(update, context)

    else:
        return duration


def smell_ans(update, context):
    duration_list = [
        "<1 месяца", "1-3 месяца", "3-6 месяцев", "6-9 месяцев", ">9 месяцев"
    ]

    duration_number = update.message.text
    username = str(update.message.chat.username)
    answers = json_ans(username)

    if duration_number in duration_list or duration_number == "Нет":
        reply_keyboard = [["Отсутствует", "Снижено"]]

        answers.append(duration_number)

        sent_text = "Обоняние снижено или отсутствует?"

        update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        answers.append(sent_text)

        json_ans(username, answers)

        return training_before

    else:
        return smell


def training_before_ans(update, context):
    ans_smell = update.message.text

    username = str(update.message.chat.username)
    answers = json_ans(username)

    if ans_smell == "Отсутствует" or ans_smell == "Снижено":
        reply_keyboard = [["Да", "Нет"]]

        answers.append(ans_smell)

        sent_text = "Делал(а) ли раньше обонятельный тренинг?"

        update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

        answers.append(sent_text)

        json_ans(username, answers)

        return training_before_duration

    else:
        return training_before


def training_before_duration_ans(update, context):
    ans_training_before = update.message.text
    
    username = str(update.message.chat.username)
    answers = json_ans(username)

    if ans_training_before == "Да":
        reply_keyboard = [[
            "<1 месяца", "1-3 месяца", "3-6 месяцев", "6-9 месяцев",
            ">9 месяцев"
        ]]

        answers.append(ans_training_before)

        sent_text = "Сколько по времени?"

        update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        answers.append(sent_text)

        json_ans(username, answers)

        return timeset

    elif ans_training_before == "Нет":
        return timeset_ans(update, context)

    else:
        reply_keyboard = [["Да", "Нет"]]

        update.message.reply_text("Делал(а) ли раньше обонятельный тренинг?",
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      resize_keyboard=True))

        return training_before_duration


def timeset_ans(update, context):
    ans_training_before_duration = update.message.text
    training_before_duration_list = [
        "<1 месяца", "1-3 месяца", "3-6 месяцев", "6-9 месяцев", ">9 месяцев"
    ]
    
    username = str(update.message.chat.username)
    answers = json_ans(username)

    if ans_training_before_duration in training_before_duration_list or ans_training_before_duration == "Нет":
        answers.append(ans_training_before_duration)

        reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback"]]

        sent_text = "Меню команд:\n\nЧтобы изменить временную зону, напиши /time\nЧтобы создать новое напоминание, напиши /reminder (рекомендуется делать тест минимум 2 раза в день)\nЧтобы посмотреть все напоминания, напиши /list\nЧтобы начать тест, напиши /test\nДля обратной связи напиши /feedback"

        update.message.reply_text(sent_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

        json_ans(username, answers)

        return ConversationHandler.END

    else:
        return training_before_duration

# TEST
# TEST
# TEST

def test(update, context):
    reply_keyboard = [[
        "Закончить", "Роза", "Лимон", "Эвкалипт", "Гвоздика", "Очистить"
    ]]

    update.message.reply_text("Выбери те запахи из набора, которые у тебя есть, и нажми «закончить»", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
    
    return choice


def choice_ans(update, context):
    chat_id = str(update.message.chat.id)
    _choice = update.message.text

    choice_list = json_scents(chat_id)
    
    full_choice = ["Роза", "Лимон", "Эвкалипт", "Гвоздика"]

    if _choice not in choice_list and _choice in full_choice:
        choice_list.append(_choice)
        json_scents(chat_id, choice_list)

    if _choice == "Очистить":
        json_scents(chat_id, [])

    elif _choice == "Закончить" and len(choice_list) != 0:
        update.message.reply_text("Выбранные запахи:",
                                  reply_markup=ReplyKeyboardRemove())
        for i in choice_list:
            update.message.reply_text("• " + i)

        reply_keyboard = [["Начать"]]
        update.message.reply_text("Подготовь набор для тренинга")
        update.message.reply_text("Готов начать тест?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

        return start_test

    else:
        return choice


def start_test_ans(update, context):
    chat_id = str(update.message.chat.id)
    choice_list = json_scents(chat_id)
    message_text = update.message.text

    if len(choice_list) == 0 and message_text == "/feedback":
        return feedback(update, context)
    
    if len(choice_list) > 1:
        if message_text == "Да" or message_text == "Начать":
            update.message.reply_text("Подготовь эфирное масло '" + choice_list[0] + "' и нюхай 30 секунд")

            context.job_queue.run_once(prepare, 2, context = [update], name = chat_id)

            context.job_queue.run_once(the_timer, 32, context = [update], name = chat_id)

    elif len(choice_list) == 1:
        if message_text == "Да" or message_text == "Начать":
            update.message.reply_text("Подготовь эфирное масло '" + choice_list[0] + "' и нюхай 30 секунд")
        
            context.job_queue.run_once(prepare, 2, context = [update], name = chat_id)

            context.job_queue.run_once(the_timer, 32, context = [update], name = chat_id)


def prepare(context):
    job = context.job
    update = job.context[0]
    r = random.randint(1, 4)

    chat_id = str(update.message.chat.id)
    choice_list = json_scents(chat_id)

    if choice_list[0] == "Роза":
        img_url = "rose_"

    elif choice_list[0] == "Лимон":
        img_url = "lemon_"

    elif choice_list[0] == "Эвкалипт":
        img_url = "eucalyptus_"

    elif choice_list[0] == "Гвоздика":
        img_url = "carnation_"

    img_url += str(r) + ".jpg"

    json_scents(chat_id, choice_list[1:])

    sendImage(img_url, update.message)


def the_timer(context):
    job = context.job
    update = job.context[0]

    chat_id = str(update.message.chat.id)
    choice_list = json_scents(chat_id)

    if len(choice_list) == 0:        
        reply_keyboard = [["/time", "/reminder", "/list", "/test", "/feedback"]]

        context.bot.send_message(chat_id, text="Ты молодец! Уже выбрал время следующего напоминания?\nНажми в меню /reminder\nПомни, что тренинг необходимо выполнять минимум 2 раза в день", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))

    else:
        reply_keyboard = [["Да"]]
        update.message.reply_text("Продолжить?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    
        return start_test

# FEEDBACK
# FEEDBACK
# FEEDBACK

def feedback(update, context):
    update.message.reply_text("Спустя месяц тренировки, пожалуйста, напиши, есть ли у тебя улучшения, а так же любые отзывы и предложения отправляй на почту training.anosmia@gmail.com Успехов!")

    return ConversationHandler.END


def secret(update, context):
    chat_id = str(update.message.chat.id)

    if chat_id == "890422904" or chat_id == "353412556":
        usernames = json_secret_name()

        all_answers = json_special_getter(usernames)

        for i in all_answers:
            update.message.reply_text(i)
        
    return ConversationHandler.END



def send_ping_1(context):
    job = context.job
    _update = job.context[0]
    print("yay")

    _update.message.reply_text("ping")

    context.job_queue.run_once(send_ping_2, 30, context=[_update], name="ping_2")


def send_ping_2(context):
    job = context.job
    _update = job.context[0]
    print("yey")

    _update.message.reply_text("pong")

    context.job_queue.run_once(send_ping_1, 30, context=[_update], name="ping_1")


def pinging(update, context):
    chat_id = str(update.message.chat.id)

    if chat_id == "890422904":
        context.job_queue.run_once(send_ping_1, 5, context=[update], name="ping_1")
        return ConversationHandler.END

def main():
    updater = Updater("1925710739:AAGs3ARdPPScQyUu_LZNjmUbhtUhKWRqhw8", use_context=True)

    dp = updater.dispatcher

    all_reminder_handler = CommandHandler("list", all_reminder)

    conv_feedback_handler = CommandHandler("feedback", feedback)

    conv_secret_handler = CommandHandler("secret", secret)

    conv_cancel_handler = CommandHandler("reminder_stop", reminder_stop)

    conv_pinging_handler = CommandHandler("pinging", pinging)

    all_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            recovered: [MessageHandler(Filters.text, recovered_ans)],
            duration: [MessageHandler(Filters.text, duration_ans)],
            smell: [MessageHandler(Filters.text, smell_ans)],
            training_before: [MessageHandler(Filters.text, training_before_ans)],
            training_before_duration: [MessageHandler(Filters.text, training_before_duration_ans)],
            timeset: [MessageHandler(Filters.text, timeset_ans)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_handler_reminder = ConversationHandler(
        entry_points=[CommandHandler("reminder", reminder)],
        states={
            reminder_day: [MessageHandler(Filters.text, reminder_day_ans)],
            reminder_setup_today: [MessageHandler(Filters.text, reminder_setup_today_ans)],
            reminder_setup_tomorrow: [MessageHandler(Filters.text, reminder_setup_tomorrow_ans)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_handler_utc = ConversationHandler(
        entry_points=[CommandHandler("time", utc_time)],
        states={
            utc_1: [CallbackQueryHandler(utc_1_ans)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_handler_test = ConversationHandler(
        entry_points=[CommandHandler("test", test)],
        states={
            choice: [MessageHandler(Filters.text, choice_ans)],
            start_test: [MessageHandler(Filters.text, start_test_ans)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dp.add_handler(all_reminder_handler)

    dp.add_handler(all_handler)

    dp.add_handler(conv_handler_utc)

    dp.add_handler(conv_handler_reminder)

    dp.add_handler(conv_handler_test)

    dp.add_handler(conv_feedback_handler)

    dp.add_handler(conv_secret_handler)

    dp.add_handler(conv_cancel_handler)

    dp.add_handler(conv_pinging_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
