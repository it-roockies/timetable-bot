from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import logging
import time
import os
from datetime import date, datetime
import json
import requests
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
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
    get_messages
)
from timetablebot.utils import build_menu


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
logger.info(f"Starting telegram bot with TOKEN: {TOKEN}")

STUDENT_ID, DATE_OF_BIRTH, GROUP, CHOOSING, TODAY, NOW, SUBJECTS, TEACHER, QUESTION, ANSWER = range(10)

def this_day_info(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    user_info = get_userinfo(telegram_id)
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


def today(update: Update, context: CallbackContext):
    """returns today's lessons for user"""
    today_lessons = this_day_info(update, context)  # get today's lesson
    choice_keyboard = [['assessing', 'today', 'now']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    if 'message' in today_lessons:
        update.message.reply_text(today_lessons['message'], reply_markup=keyboard)
        return CHOOSING

    lesson_text = reform_day(today_lessons)

    update.message.reply_text(f'today you have:\n {lesson_text} Please choose what do you want?', reply_markup=keyboard)
    return CHOOSING

def now(update: Update, context: CallbackContext):
    """returns what should user need to do right now"""
    choice_keyboard = [['assessing', 'today', 'now']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    today_lessons = this_day_info(update, context)  # get today's lesson

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
    update.message.reply_text(messages.BIRTH)
    return DATE_OF_BIRTH


# def get_education_year(update: Update):
#     reply_keyboard = [['1', '2', '3', '4']]
#     update.message.reply_text(
#         "Please tell me about your education year "
#         "for example (1, 2, 3, 4)",
#         reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
#     )
#     return EDUCATION_YEAR


# def get_faculty(update: Update):
#     update.message.reply_text("Now you need to tell me your faculty")
#     return FACULTY
def choice(update, context):
    choice_keyboard = [['assessing', 'today', 'now']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(f'Please choose what do you want?',
                              reply_markup=keyboard)
    return CHOOSING

def get_group(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get groups from server.")
    groups = get_groups(telegram_id)
    context.user_data['groups'] = groups

    reply_keyboard = [group['name'] for group in groups]
    messages = context.user_data['messages']
    update.message.reply_text(messages.GROUP, reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 4), one_time_keyboard=True, resize_keyboard=True))

    return GROUP


def get_subject(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get subjects from server.")
    userinfo = get_userinfo(telegram_id=telegram_id)
    print(userinfo)
    minutes = datetime.now().minute + datetime.now().hour * 60
    today_lesson = get_today(telegram_id=telegram_id, group=userinfo['group']['name'], date=date.today(), minutes=minutes)  # get today's lesson
    if len(today_lesson) == 1 and 'message' in today_lesson:
        update.message.reply_text('today you have no classess. That is why you can`t assess.')
        return ConversationHandler.END
    subjects = [lesson['subject'] for lesson in today_lesson['today_lessons']]
    reply_keyboard = subjects  # [subject['name'] for subject in subjects]
    messages = context.user_data['messages']
    update.message.reply_text(messages.COMMENTSUBJECT, reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 3), one_time_keyboard=True, resize_keyboard=True))

    return SUBJECTS


def get_teacher(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    # logger.info(f"{telegram_id}: Get teachers from server.")

    # reply_keyboard = [teacher['short'] for teacher in teachers]
    subject = context.user_data['subject']
    userinfo = get_userinfo(telegram_id=telegram_id)
    minutes = datetime.now().minute + datetime.now().hour * 60
    today_lesson = get_today(telegram_id=telegram_id, group=userinfo['group']['name'], date=date.today(), minutes=minutes)  # get today's lesson
    print(today_lesson)
    if 'message' in today_lesson:
        update.message.reply_text(today_lesson['message'])
        return CHOOSING
    teacher = [lesson['teacher'] for lesson in today_lesson['today_lessons'] if lesson['subject'] == context.user_data['subject']]
    context.user_data['teacher'] = teacher[0]

    context.user_data["questions"] = get_questions(update.message.from_user.id)
    # print(get_questions(update.message.from_user.id))
    # if context.user_data['questions']['choice'] is None:

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
    context.user_data['messages'] = messages
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
    update.message.reply_text(messages.CANCEL)
    return ConversationHandler.END


def student_id(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text.strip()
    return get_date_of_birth(update, context)


def date_of_birth(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much.")

    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Check if user exist in Database.")
    user_info = create_telegram_user(
        telegram_id=update.message.from_user.id,
        username=context.user_data['username'],
        date_of_birth=update.message.text.strip()
    )
    if user_info and 'id' in user_info:
        logger.info(f"{telegram_id}: User exist in Database.")
        return get_group(update, context)
    else:
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

    choice_keyboard = [['assessing', 'today', 'now']]
    keyboard = ReplyKeyboardMarkup(keyboard=choice_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text('Please choose what do you want?', reply_markup=keyboard)
    return CHOOSING



def choose_function(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Thank you working with us.', reply_markup=ReplyKeyboardRemove())
    if update.message.text == 'assessing':
        return get_subject(update, context)
    elif update.message.text == 'today':
        return today(update, context)
    else:
        return now(update, context)

# def education_year(update: Update, context: CallbackContext) -> int:
#     update.message.reply_text("Thank you so much for your patience and effort.")
#     context.user_data['education_year'] = int(update.message.text)
#     return get_faculty(update)


# def faculty(update: Update, context: CallbackContext) -> int:
#     update.message.reply_text("Cool. One more thing.")

#     telegram_id = update.message.from_user.id
#     logger.info(f"{telegram_id}: Update users education_year and faculty.")
#     update_telegram_user(
#         telegram_id=telegram_id,
#         education_year=context.user_data['education_year'],
#         faculty=update.message.text
#     )

#     return get_subject(update, context)


def subjects(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much."
                              , reply_markup=ReplyKeyboardRemove(),
                              )
    context.user_data['subject'] = update.message.text
    return get_teacher(update, context)


def teacher(update: Update, context: CallbackContext) -> int:
    # context.user_data['teacher'] = update.message.text

    # get a question from database
    # print(get_choices(update.message.from_user.id))
    context.user_data["questions"] = get_questions(update.message.from_user.id)
    # print(get_questions(update.message.from_user.id))
    # if context.user_data['questions']['choice'] is None:

    context.user_data['current'] = 0

    if len(context.user_data['questions']) == 0:
        update.message.reply_text("Sorry, but there are no questions.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    return ask_question(update=update, context=context)


def ask_question(update, context):
    """asks question from user"""

    questions = context.user_data["questions"]
    current = context.user_data["current"]
    current_question = questions[current]
    question_text = current_question['question_text']
    if current_question['choice'] is None:
        update.message.reply_text(question_text, reply_markup=ReplyKeyboardRemove())
        return ANSWER
    else:
        reply_keyboard = [json.loads(choice['variant']) for choice in get_choices(update.message.from_user.id) if
                          choice['id'] == current_question['choice']]
        update.message.reply_text(question_text,
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
                                  )

        return ANSWER


def answer(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    questions = context.user_data["questions"]
    subjects = get_subjects(telegram_id)  # getting all subjects from database
    teachers = get_teachers(telegram_id)  # getting all teachers from database
    subject = [subject['id'] for subject in subjects if subject['short'] == context.user_data['subject']]
    teacher = [teacher['id'] for teacher in teachers if teacher['short'] == context.user_data['teacher']]


    current = context.user_data["current"]
    question = questions[current]
    # post answer
    create_answer(
        telegram_id=telegram_id,
        subject=subject[0],
        teacher=teacher[0],
        question=question["id"],
        answer=update.message.text,
    )

    if current < len(questions) - 1:
        context.user_data['current'] = current + 1
        return ask_question(update=update, context=context)
    else:
        messages = context.user_data['messages']
        update.message.reply_text(messages.END,
                                  reply_markup=ReplyKeyboardRemove(),
                                  )
        return ConversationHandler.END


def main() -> None:
    updater = Updater(token=TOKEN)

    dispatcher = updater.dispatcher
    today_handler = CommandHandler('today', presently)
    now_handler = CommandHandler('now', at_present)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STUDENT_ID: [MessageHandler(Filters.text & ~Filters.command, student_id)],
            DATE_OF_BIRTH: [MessageHandler(Filters.text & ~Filters.command, date_of_birth)],
            GROUP: [MessageHandler(Filters.text & ~Filters.command, group)],
            CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_function)],
            TODAY: [MessageHandler(Filters.text & ~Filters.command, today)],
            NOW: [MessageHandler(Filters.text & ~Filters.command, now)],
            SUBJECTS: [MessageHandler(Filters.text & ~Filters.command, subjects)],
            TEACHER: [MessageHandler(Filters.text & ~Filters.command, teacher)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )

    dispatcher.add_handler(handler=conv_handler)
    dispatcher.add_handler(handler=today_handler)
    dispatcher.add_handler(handler=now_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
