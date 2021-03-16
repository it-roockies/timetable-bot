from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import logging
import time
import os
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
    get_questions,
    create_answer,
)
from timetablebot.utils import build_menu


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
logger.info(f"Starting telegram bot with TOKEN: {TOKEN}")

STUDENT_ID, DATE_OF_BIRTH, EDUCATION_YEAR, FACULTY, SUBJECTS, TEACHER, QUESTION, ANSWER = range(8)


def get_student_id(update: Update):
    update.message.reply_text(
        "Please enter your student id in numbers like: (12259) "
        "If you do not want to assess teachers simply click here /cancel."
    )
    return STUDENT_ID


def get_date_of_birth(update: Update):
    update.message.reply_text(
        "I see. Great, please enter your date of birth altogether (DDMMYYYY)"
    )
    return DATE_OF_BIRTH


def get_education_year(update: Update):
    reply_keyboard = [['1', '2', '3', '4']]
    update.message.reply_text(
        "Please tell me about your education year "
        "for example (1, 2, 3, 4)",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDUCATION_YEAR


def get_faculty(update: Update):
    update.message.reply_text("Now you need to tell me your faculty")
    return FACULTY


def get_subject(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get subjects from server.")
    subjects = get_subjects(telegram_id)
    context.user_data['subjects'] = subjects

    reply_keyboard = [subject['name'] for subject in subjects]
    update.message.reply_text(
        "Please choose which subject do you want to give your comments",
        reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 3), one_time_keyboard=True)
    )

    return SUBJECTS


def get_teacher(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Get teachers from server.")
    teachers = get_teachers(telegram_id)
    context.user_data['teachers'] = teachers

    reply_keyboard = [teacher['short'] for teacher in teachers]

    update.message.reply_text(
        "You need to choose which teacher you wanna comment ",
        reply_markup=ReplyKeyboardMarkup(build_menu(reply_keyboard, 5), one_time_keyboard=True)
    )
    return TEACHER


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Hello, this bot serves you to assess teacher in TTPU.")

    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: New user started the bot.")
    userinfo = get_userinfo(telegram_id)

    if 'id' in userinfo and userinfo['faculty'] is not None and userinfo['education_year'] is not None:
        logger.info(f"{telegram_id}: User has already registered.")
        return get_subject(update, context)
    elif 'id' in userinfo:
        logger.info(f"{telegram_id}: User has already registered, but has not faculty or education_year.")
        return get_education_year(update)
    else:
        logger.info(f"{telegram_id}: User is not yet registered.")
        return get_student_id(update)


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Ok, If you want to add more value to TTPU we are here'
        "Just click here /start "
    )
    return ConversationHandler.END


def student_id(update: Update, context: CallbackContext) -> int:
    context.user_data['username'] = update.message.text.strip()
    return get_date_of_birth(update)


def date_of_birth(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much.")
    
    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Check if user exist in Database.")
    userinfo = create_telegram_user(
        telegram_id=update.message.from_user.id,
        username=context.user_data['username'],
        email=update.message.text.strip()
    )
    if 'id' in userinfo:
        logger.info(f"{telegram_id}: User exist in Database.")
        return get_education_year(update)
    else:
        logger.info(f"{telegram_id}: User is not exist in Database.")
        update.message.reply_text("Unfortunately, we could not find you in our system.")
        return get_student_id(update)


def education_year(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much for your patience and effort.")
    context.user_data['education_year'] = int(update.message.text)
    return get_faculty(update)


def faculty(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Cool. One more thing.")

    telegram_id = update.message.from_user.id
    logger.info(f"{telegram_id}: Update users education_year and faculty.")
    update_telegram_user(
        telegram_id=telegram_id,
        education_year=context.user_data['education_year'],
        faculty=update.message.text
    )

    return get_subject(update, context)


def subjects(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Thank you so much.")
    context.user_data['subject'] = update.message.text
    return get_teacher(update, context)


def teacher(update: Update, context: CallbackContext) -> int:
    context.user_data['teacher'] = update.message.text

    # get a question from database
    questions = get_questions(update.message.from_user.id)

    if len(questions) == 0:
        update.message.reply_text("Sorry, but there are no querstions.")
        return ConversationHandler.END

    question1 = questions[0]['question_text']  # just default question
    context.user_data['question'] = questions[0]['id'] # just default id
    update.message.reply_text(question1)

    return ANSWER


def answer(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    subject = next(subject['id'] for subject in context.user_data['subjects'] if subject['name'] == context.user_data['subject'])
    teacher = next(teacher['id'] for teacher in context.user_data['teachers'] if teacher['short'] == context.user_data['teacher'])

    # post answer
    create_answer(
        telegram_id=telegram_id,
        subject=subject,
        teacher=teacher,
        question=context.user_data['question'],
        answer=update.message.text,
    )
    update.message.reply_text(
        "Thank you for your time and effort. "
        "You have added value to our growth. "
        "Do you want to give comment click here /start "
    )
    return ConversationHandler.END

def main() -> None:
    updater = Updater(token=TOKEN)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STUDENT_ID: [MessageHandler(Filters.text & ~Filters.command, student_id)],
            DATE_OF_BIRTH: [MessageHandler(Filters.text & ~Filters.command, date_of_birth)],
            EDUCATION_YEAR: [MessageHandler(Filters.text & ~Filters.command, education_year)],
            FACULTY: [MessageHandler(Filters.text & ~Filters.command, faculty)],
            SUBJECTS: [MessageHandler(Filters.text & ~Filters.command, subjects)],
            TEACHER: [MessageHandler(Filters.text & ~Filters.command, teacher)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )

    dispatcher.add_handler(handler=conv_handler)

    updater.start_polling()

    updater.idle()



if __name__ == '__main__':
    main()


