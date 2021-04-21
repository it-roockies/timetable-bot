from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import time
import os
from datetime import date, time, datetime, timedelta
from pytz import timezone
import json
import requests
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)



from timetablebot.timetable import (
    get_userinfo,
    create_telegram_user,
    update_telegram_user,
    get_subjects,
    get_teachers,
    get_groups,
    get_questions,
    create_answer,
    get_choices,
    get_today,
    get_messages,
    notify_user,
    get_subjects_for_term,
    get_teacher_for_term,
    get_free_rooms,
    INVALID_USER
)
from timetablebot.utils import build_menu


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
logger.info(f"Starting telegram bot with TOKEN: {TOKEN}")

(
    STUDENT_ID,
    DATE_OF_BIRTH,
    GROUP,
    CHOOSING,
    BOOKING,
    ROOM,
    TODAY,
    NOW,
    SEMESTER,
    MODULE,
    TUTOR,
    SUBJECTS,
    TEACHER,
    ASSESS,
    ANSWER,
) = range(15)
STUDENT = 0
level_in_group = {'19': 1, '18': 2, '17': 3, 'G': 0}

def this_day_info(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    user_info = get_userinfo(telegram_id)
    if user_info is None:
        return backend_error(update, context)
    group = user_info['group']['name']
    global date
    date = date.today()
    minutes = datetime.now().minute + datetime.now().hour * 60
    # get today's lessons
    today_lessons = get_today(
        telegram_id=telegram_id,
        group=group,
        date=date,
        minutes=minutes
    )
    return today_lessons

def is_in(obj: list, value: str):
    """helps to handle malware choice """
    for i in obj:
        if value in i:
            return True
    return False

def backend_error(update, context):
    update.message.reply_text('Sorry, some error happened in our system\nCome back later.')
    return ConversationHandler.END

def reform_day(obj):
    """formats lesson to human friendly format"""
    today_lsn = ''
    for lesson in obj['today_lessons']:
        full_lsn = ''
        for k, v in dict(lesson).items():
            lsn = f"{k}:     {v} \n"
            full_lsn += lsn
            today_lsn += f"{lsn}"
        today_lsn += '\n\n'
    return today_lsn

def get_booking_from_user(update, context):
    answer = update.message.text
    if answer not in ['Yes', 'No']:
        msg = "You entered unknown answer please choose valid one"
        update.message.reply_text(msg)
        return get_date_of_booking(update, context)
    if answer == 'Yes':
        pass
    else:
        global STUDENT
        STUDENT += 1

def get_date_of_booking(update, context):
    day = date.today()  # get today's date
    weekday_today = day.weekday()  # which number in week
    end_date = day + timedelta(5 - weekday_today)  # get end of the week
    weekday_end_date = end_date.weekday()  # which number in week
    day_of_the_week = {0: f'Monday {day + timedelta(0-day.weekday())}',
                       1: f'Tuesday {day + timedelta(1-day.weekday())}',
                       2: f'Wednesday {day + timedelta(2-day.weekday())}',
                       3: f'Thursday {day + timedelta(3-day.weekday())}',
                       4: f'Friday {day + timedelta(4-day.weekday())}',
                       5: f'Saturday {day + timedelta(5-day.weekday())}'
                       }
    days = [[day_of_the_week[day]] for day in range(weekday_today, weekday_end_date + 1)]
    reply_keyboard = ReplyKeyboardMarkup(days, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Choose booking date:", reply_markup=reply_keyboard)
    return BOOKING

def presently(update: Update, context: CallbackContext):
    lesson = this_day_info(update, context)
    lesson = reform_day(lesson)
    update.message.reply_text(lesson)


def at_present(update: Update, context: CallbackContext):
    today_lessons = this_day_info(update, context)
    if 'message' in today_lessons:
        update.message.reply_text(today_lessons['message'])
    msg = today_lessons['now_lesson']
    if 'message' in today_lessons:
        update.message.reply_text(today_lessons["message"])
    if 'message' in msg:
        lesson = msg['message']
    else:
        lesson = ''
        for k, v in msg.items():
            row = f"{k}:    {v} \n"
            lesson += row
    update.message.reply_text(lesson)

def timetable(update: Update, context: CallbackContext):
    timetable_keyboard = [['Today', 'Now', 'Stop']]
    reply_keyboard = ReplyKeyboardMarkup(timetable_keyboard, resize_keyboard=True, one_time_keyboard=True)
    message = "Please, choose which type?"
    update.effective_message.reply_text(message, reply_markup=reply_keyboard)
    return CHOOSING

def questionnaire(update: Update, context: CallbackContext):
    questionnaire_keyboard = [['Quick', 'Slow', 'Stop']]
    reply_keyboard = ReplyKeyboardMarkup(questionnaire_keyboard, one_time_keyboard=True, resize_keyboard=True)
    message = "You have a choice to choose the mode of questionnaire"
    update.effective_message.reply_text(message, reply_markup=reply_keyboard)
    return CHOOSING

def today(update: Update, context: CallbackContext):
    """returns today's lessons for user"""
    today_lessons = this_day_info(update, context)  # get today's lesson
    choice_keyboard = [['Timetable', 'Questionnaire'], ['Stop']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    if 'message' in today_lessons:
        update.message.reply_text(today_lessons['message'], reply_markup=keyboard)
        return CHOOSING

    lesson_text = reform_day(today_lessons)

    update.message.reply_text(f'today you have:\n {lesson_text} Please choose what do you want?', reply_markup=keyboard)
    return CHOOSING

def unknown_function(update: Update, context: CallbackContext):
    """handles unknown functionalities of bot"""
    msg = "You want some unknown functionality from bot. \nPlease choose valid functionality"
    choice_keyboard = [['Timetable', 'Questionnaire'], ['Stop']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(msg, reply_markup=keyboard)
    return CHOOSING

def now(update: Update, context: CallbackContext):
    """returns what should user need to do right now"""
    choice_keyboard = [['Timetable', 'Questionnaire'], ['Stop']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    today_lessons = this_day_info(update, context)  # get today's lesson
    if today_lessons is None:
        return backend_error(update, context)
    if 'message' in today_lessons:
        update.message.reply_text(today_lessons['message'], reply_markup=keyboard)
        return CHOOSING
    msg = today_lessons['now_lesson']
    if 'message' in today_lessons:
        update.message.reply_text(f'{today_lessons["message"]}. Please choose what do you want?', reply_markup=keyboard)
        return CHOOSING
    if 'message' in msg:
        lesson = msg['message']
    else:
        lesson = ''
        for k, v in msg.items():
            row = f"{k}:    {v} \n"
            lesson += row
    update.message.reply_text(f'{lesson}. Please choose what do you want?', reply_markup=keyboard)
    return CHOOSING


def get_student_id(update: Update, context: CallbackContext):
    messages = context.user_data['messages']
    update.message.reply_text(messages.USERNAME)
    return STUDENT_ID


def get_date_of_birth(update: Update, context: CallbackContext):
    messages = context.user_data['messages']
    if context.user_data['failure'] == 1:
        update.message.reply_text(messages.BIRTH_AGAIN)
    else:
        update.message.reply_text(messages.BIRTH)
    return DATE_OF_BIRTH


def get_term(update: Update, context: CallbackContext):
    questions = [question for question in get_questions(telegram_id=update.message.from_user.id)]
    if len(questions) == 0:
        update.message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    get_term_message = 'Please, choose which semester are you going to give your feedback?'
    reply_keyboard = [['1', '2'], ['Stop']]
    context.user_data['term_choice'] = reply_keyboard
    keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(get_term_message, reply_markup=keyboard)
    return SEMESTER

def get_tutors(update: Update, context: CallbackContext):
    subject = context.user_data['subject']
    telegram_id = update.message.from_user.id
    teachers = get_teacher_for_term(telegram_id=telegram_id, subject=subject)
    if teachers is None:
        return backend_error(update, context)
    reply_keyboard = ReplyKeyboardMarkup([teachers['teachers'], ['Stop']], one_time_keyboard=True, resize_keyboard=True)
    context.user_data['term_teacher_choice'] = [teachers['teachers'], ['Stop']]
    update.message.reply_text('Please, Choose which teacher to comment', reply_markup=reply_keyboard)
    return TUTOR


def choice(update, context):
    choice_keyboard = [['Timetable', 'Questionnaire'], ['Stop']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(f'Please choose what do you want?',
                              reply_markup=keyboard)
    return CHOOSING


def get_group(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get groups from server.")
    groups = get_groups(telegram_id)
    if groups is None:
        return backend_error(update, context)
    context.user_data['groups'] = groups

    reply_keyboard = [group['name'] for group in groups]
    messages = context.user_data['messages']
    update.message.reply_text(messages.GROUP,
                              reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 4), one_time_keyboard=True,
                                                               resize_keyboard=True))

    return GROUP


def get_subject(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get subjects from server.")
    userinfo = get_userinfo(telegram_id=telegram_id)
    if userinfo is None:
        return backend_error(update, context)
    minutes = datetime.now().minute + datetime.now().hour * 60
    today_lesson = get_today(telegram_id=telegram_id, group=userinfo['group']['name'], date=date.today(),
                             minutes=minutes)  # get today's lesson for a certain group
    if today_lesson is None:
        return backend_error(update, context)
    if len(today_lesson) == 1 and 'message' in today_lesson:
        update.message.reply_text('today you have no classes. That is why you can`t assess.')
        return ConversationHandler.END

    subjects = []
    teachers = []
    # checking duplicate subjects in choosing list
    for lesson in today_lesson['today_lessons']:
        if lesson['subject'] not in subjects:
            subjects.append(lesson['subject'])
            teachers.append(lesson['teacher'])
        else:
            if lesson['teacher'] not in teachers:
                subjects.append(lesson['subject'])
    context.user_data['subjects'] = subjects
    reply_keyboard = subjects  # [subject['name'] for subject in subjects]
    messages = context.user_data['messages']
    update.message.reply_text(messages.COMMENTSUBJECT,
                              reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 3),
                                                               one_time_keyboard=True, resize_keyboard=True))
    return SUBJECTS


def get_teacher(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    # logger.info(f"{telegram_id}: Get teachers from server.")

    # reply_keyboard = [teacher['short'] for teacher in teachers]
    subject = context.user_data['subject']
    userinfo = get_userinfo(telegram_id=telegram_id)
    if userinfo is None:
        return backend_error(update, context)
    minutes = datetime.now().minute + datetime.now().hour * 60
    today_lesson = get_today(telegram_id=telegram_id, group=userinfo['group']['name'], date=date.today(),
                             minutes=minutes)  # get today's lesson

    if 'message' in today_lesson:
        update.message.reply_text(today_lesson['message'])
        return CHOOSING
    teacher = [lesson['teacher'] for lesson in today_lesson['today_lessons'] if
               lesson['subject'] == context.user_data['subject']]
    context.user_data['teacher'] = teacher[0]

    questions = [question for question in get_questions(update.message.from_user.id) if question['quick_mode']]
    context.user_data["questions"] = questions

    context.user_data['current'] = 0

    if len(context.user_data['questions']) == 0:
        update.message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    update.message.reply_text(
        f"You are assessing professor {teacher[0]} "
    )

    return ask_question(update=update, context=context)

    # return TEACHER


def start(update: Update, context: CallbackContext) -> int:
    messages = get_messages()
    context.user_data['failure'] = 0
    if messages is None:  # checking if some error happens in server
        return backend_error(update=update, context=context)
    context.user_data['messages'] = messages  # getting messages in database
    update.message.reply_text(messages.START, reply_markup=ReplyKeyboardRemove())
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: New user started the bot.")
    user_info = get_userinfo(telegram_id)
    if user_info and 'id' in user_info and user_info['group'] is not None:
        logger.info(f"{telegram_id}: User has already registered.")
        return choice(update, context)
    elif user_info and 'id' in user_info:
        logger.info(f"{telegram_id}: User has already registered, but has not faculty or education_year.")
        return get_group(update, context)
    else:
        logger.info(f"{telegram_id}: User is not yet registered.")
        return get_student_id(update, context)


def cancel(update: Update, context: CallbackContext) -> int:
    messages = context.user_data['messages']
    update.message.reply_text(messages.CANCEL, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def student_id(update: Update, context: CallbackContext) -> int:
    """ get username of a student in our format """
    upcoming_username = update.message.text.strip()
    username = 'u' + upcoming_username[len(upcoming_username)-5:]
    context.user_data['username'] = username
    return get_date_of_birth(update, context)


def date_of_birth(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much.")
    if len(update.message.text.strip()) != 10:
        update.message.reply_text('You entered wrong format of your date of birth, please enter correctly.')
        return get_date_of_birth(update, context)
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Check if user exist in Database.")
    user_info = create_telegram_user(
        telegram_id=update.message.from_user.id,
        username=context.user_data['username'],
        date_of_birth=update.message.text.strip(),
        key=context.user_data['failure']
    )
    if user_info and type(user_info) == dict and 'id' in user_info:
        logger.info(f"{telegram_id}: User exist in Database.")
        return get_group(update, context)
    elif user_info == INVALID_USER:
        context.user_data['failure'] = 1
        return get_date_of_birth(update, context)
    logger.info(f"{telegram_id}: User is not exist in Database.")
    messages = context.user_data['messages']
    update.message.reply_text(messages.NOTFOUND)
    return get_student_id(update, context)


def group(update: Update, context: CallbackContext) -> int:
    group_name = update.message.text
    telegram_id = update.message.from_user.id
    group = next((group['id'] for group in context.user_data['groups'] if group['name'] == group_name), None)
    if group is None:
        logger.info(f"{telegram_id}: User entered wrong group {group_name}.")
        update.message.reply_text("You entered wrong group name.", reply_markup=ReplyKeyboardRemove())
        return get_group(update, context)

    logger.info(f"{telegram_id}: Update users group {group_name}.")
    update.message.reply_text("Thank you so much for your patience and effort.")

    context.user_data['group'] = group_name
    update_telegram_user(telegram_id=telegram_id, group=int(group))
    choice_keyboard = [['Timetable', 'Questionnaire'], ['Stop']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text('Please choose what do you want?', reply_markup=keyboard)
    return CHOOSING


def choose_function(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Thank you working with us.', reply_markup=ReplyKeyboardRemove())
    if update.message.text == 'Timetable':
        return timetable(update, context)
    elif update.message.text == 'Questionnaire':
        return questionnaire(update, context)
    elif update.message.text == 'Booking\nroom':
        return get_date_of_booking(update, context)
    elif update.message.text == 'Quick':
        return get_subject(update, context)
    elif update.message.text == 'Today':
        return today(update, context)
    elif update.message.text == 'Now':
        return now(update, context)
    elif update.message.text == 'Stop':
        messages = context.user_data['messages']
        update.message.reply_text(messages.CANCEL, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif update.message.text == 'Slow':
        return get_term(update, context)
    else:
        return unknown_function(update, context)


# def booking(update: Update, context: CallbackContext) -> int:
#     day = update.message.text.split(' ')[1]
#     telegram_id = update.message.from_user.id
#     free_rooms = get_free_rooms(telegram_id=telegram_id, date=day)
#     text = ''
#     rooms = []
#     for room in free_rooms:
#         for k, v in room.items():
#             if k == 'classroom':
#                 rooms.append(v)
#             text += f'{k}:   {v}\n'
#         text += '\n'
#     keyboard = ReplyKeyboardMarkup(build_menu(rooms, 4))
#     update.message.reply_text(f'Here is free rooms, Choose one:\n\n {text}', reply_markup=keyboard)
#     return ROOM
#
# def room(update: Update, context: CallbackContext) -> int:
#     chosen_room = update.message.text
#
#     if STUDENT == 1:  # first student is responsible
#         keyboard = [['Yes', 'No']]
#         reply_keyboard = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
#         update.message.reply_text(f"Are you sure you are going to be a responsible for {chosen_room} room?",
#                                   reply_markup=reply_keyboard
#                                   )
#
#         return get_booking_from_user(update, context)
#
def semester(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    group = get_userinfo(telegram_id)['group']['name']

    # find which level of this user
    if not is_in(obj=context.user_data['term_choice'], value=update.message.text):  # check if choice entered correctly
        wrong_choice_message = 'You entered inappropriate choice, please try again.'
        update.message.reply_text(wrong_choice_message)
        return get_term(update, context)
    if update.message.text == 'Stop':
        messages = context.user_data['messages']
        update.message.reply_text(messages.CANCEL, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    term = update.message.text
    if 'G' in group:
        level = level_in_group['G']
    else:
        key = group[-2:]
        level = level_in_group[key]
    context.user_data['level'] = level
    modules = get_subjects_for_term(telegram_id=telegram_id, level=int(level), term=int(term))
    if modules is None:
        update.message.reply_text('It seems you are PY student. We are working on Your level now.')
        return ConversationHandler.END
    reply_keyboard = ReplyKeyboardMarkup([modules['subjects'], ['Stop']], resize_keyboard=True, one_time_keyboard=True)
    context.user_data['term_subject_choice'] = [modules['subjects'], ['Stop']]
    update.message.reply_text('Please, Choose which module to comment', reply_markup=reply_keyboard)
    return MODULE


def module(update: Update, context: CallbackContext) -> int:
    if not is_in(obj=context.user_data['term_subject_choice'], value=update.message.text):  # check if choice entered correctly
        wrong_choice_message = 'You entered inappropriate choice, please try again.'
        update.message.reply_text(wrong_choice_message)
        return get_term(update, context)
    if update.message.text == 'Stop':
        messages = context.user_data['messages']
        update.message.reply_text(messages.CANCEL, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    subject = update.message.text
    context.user_data['subject'] = subject
    return get_tutors(update, context)


def tutor(update: Update, context: CallbackContext) -> int:
    if not is_in(obj=context.user_data['term_teacher_choice'], value=update.message.text):  # check if choice entered correctly
        wrong_choice_message = 'You entered inappropriate choice, please try again.'
        update.message.reply_text(wrong_choice_message)
        return get_tutors(update, context)
    if update.message.text == 'Stop':
        messages = context.user_data['messages']
        update.message.reply_text(messages.CANCEL, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    context.user_data['teacher'] = update.message.text
    questions = [question for question in get_questions(update.message.from_user.id) if not question['quick_mode']]

    context.user_data["questions"] = questions
    context.user_data['current'] = 0

    if len(context.user_data['questions']) == 0:
        update.effective_message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    return ask_question(update=update, context=context)

def subjects(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much."
                              , reply_markup=ReplyKeyboardRemove(),
                              )
    if update.message.text not in context.user_data['subjects']:
        update.message.reply_text('You entered wrong subject,please enter correctly!')
        return get_subject(update, context)
    context.user_data['subject'] = update.message.text
    return get_teacher(update, context)


# using inline mode to give value of teacher and subject
# use it
def assess(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = json.loads('{'+query.data+'}')
    telegram_id = data['tg']
    context.user_data["questions"] = [question for question in get_questions(telegram_id=telegram_id) if question['quick_mode']]
    context.user_data['current'] = 0

    if len(context.user_data['questions']) == 0:
        update.effective_message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    len_of_data = len(query.data.split(' '))
    teacher = data['t']
    context.user_data['subject'] = data['s']
    context.user_data['teacher'] = teacher
    assessed_object = data['s'] + ' ' + data['t']
    query.edit_message_text(text=f"you assess {assessed_object}")
    return ask_question(update=update, context=context)


def teacher(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    context.user_data["questions"] = [question for question in get_questions(telegram_id=telegram_id) if question['quick_mode']]

    context.user_data['current'] = 0

    if len(context.user_data['questions']) == 0:
        update.effective_message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    return ask_question(update=update, context=context)


def ask_question(update, context):
    """asks question from user"""
    questions = context.user_data["questions"]
    current = context.user_data["current"]
    current_question = questions[current]
    question_text = current_question['question_text']
    if current_question['choice'] is None:
        update.effective_message.reply_text(question_text, reply_markup=ReplyKeyboardRemove())
        return ANSWER
    else:
        reply_keyboard = [json.loads(choice['variant']) for choice in get_choices(update.message.from_user.id) if
                          choice['id'] == current_question['choice']]
        update.effective_message.reply_text(question_text,
                                            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                             resize_keyboard=True)
                                            )

        return ANSWER


def answer(update: Update, context: CallbackContext) -> int:
    telegram_id = update.effective_message.from_user.id
    messages = get_messages()
    context.user_data['messages'] = messages
    questions = context.user_data["questions"]
    subjects = get_subjects(telegram_id)  # getting all subjects from database
    teachers = get_teachers(telegram_id)  # getting all teachers from database
    subject = [subject['id'] for subject in subjects if subject['short'] == context.user_data['subject']]
    teacher = [teacher['id'] for teacher in teachers if teacher['short'] == context.user_data['teacher']]
    if len(subject) == 0 and len(teacher) == 0:
        subject = [subject['id'] for subject in subjects if subject['name'] == context.user_data['subject']]
        teacher = [teacher['id'] for teacher in teachers if teacher['firstname'] + ' ' + teacher['lastname'] == context.user_data['teacher']]
    current = context.user_data["current"]
    question = questions[current]
    # post answer
    create_answer(
        telegram_id=telegram_id,
        subject=subject[0],
        teacher=teacher[0],
        question=question["id"],
        answer=update.effective_message.text,
    )

    if current < len(questions) - 1:
        context.user_data['current'] = current + 1
        return ask_question(update=update, context=context)
    else:
        messages = context.user_data['messages']
        update.effective_message.reply_text(messages.END,
                                            reply_markup=ReplyKeyboardRemove(),
                                            )
        return ConversationHandler.END


def notify(context: CallbackContext):
    period = context.job.context['period']
    moment = date.today()  # get today's date
    data = notify_user(period=period, date=moment)  # default period

    for i in data:  # iterating each lesson of a given period
        if len(i['telegram_ids']) != 0:
            for j in i['telegram_ids']:
                keyboard = [
                    [InlineKeyboardButton("Assess",
                                          callback_data=f'"s":"{i["subject"]}","t":"{i["teachers"][0]}","tg":"{j}"')]
                    ]
                context.bot.send_message(chat_id=j, text=f"You have just finished:\n{i['subject']} - {i['teachers'][0]}"
                                                         f" when ideas are hot and emotions are strong that is the time"
                                                         f" to assess the lesson.",
                                         reply_markup=InlineKeyboardMarkup(keyboard), disable_notification=True)

def main() -> None:
    updater = Updater(token=TOKEN)

    dispatcher = updater.dispatcher
    today_handler = CommandHandler('today', presently)
    now_handler = CommandHandler('now', at_present)
    assess_handler = CallbackQueryHandler(assess)
# STUDENT_ID, DATE_OF_BIRTH, GROUP, CHOOSING, TODAY, NOW, SUBJECTS, TEACHER, ASSESS, ANSWER
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(assess)],
        states={
            STUDENT_ID: [MessageHandler(Filters.text & ~Filters.command, student_id)],
            DATE_OF_BIRTH: [MessageHandler(Filters.text & ~Filters.command, date_of_birth)],
            GROUP: [MessageHandler(Filters.text & ~Filters.command, group)],
            CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_function)],
#            BOOKING: [MessageHandler(Filters.text & ~Filters.command, booking)],
#            ROOM: [MessageHandler(Filters.text & ~Filters.command, room)],
            TODAY: [MessageHandler(Filters.text & ~Filters.command, today)],
            NOW: [MessageHandler(Filters.text & ~Filters.command, now)],
            SEMESTER: [MessageHandler(Filters.text & ~Filters.command, semester)],
            MODULE: [MessageHandler(Filters.text & ~Filters.command, module)],
            TUTOR: [MessageHandler(Filters.text & ~Filters.command, tutor)],
            SUBJECTS: [MessageHandler(Filters.text & ~Filters.command, subjects)],
            TEACHER: [MessageHandler(Filters.text & ~Filters.command, teacher)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(handler=conv_handler)
    dispatcher.add_handler(handler=today_handler)
    dispatcher.add_handler(handler=now_handler)
    dispatcher.add_handler(handler=assess_handler)
    updater.job_queue.run_daily(notify, time=time(10, 5, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "1"})
    updater.job_queue.run_daily(notify, time=time(11, 25, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "2"})

    updater.job_queue.run_daily(notify, time=time(13, 5, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "3"})

    updater.job_queue.run_daily(notify, time=time(14, 25, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "4"})

    updater.job_queue.run_daily(notify, time=time(15, 45, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "5"})

    updater.job_queue.run_daily(notify, time=time(17, 5, 0, tzinfo=timezone("Asia/Tashkent")),
                                days=(0, 1, 2, 3, 4, 5), context={"period": "6"})

    # updater.job_queue.run_daily(notify, time=time(18, 54, 0, tzinfo=timezone("Asia/Tashkent")),
    #                             days=(0, 1, 2, 3, 4, 5), context={"period": "test"})
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
