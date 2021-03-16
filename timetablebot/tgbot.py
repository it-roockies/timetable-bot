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
# Enable logging
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

USER_ID = 1  # default 1 but when we want to update a user we just put its id
USER_ENDPOINT = "http://127.0.0.1:8000/api/booking/user/"
ACCESS_TOKEN_ENDPOINT = "http://127.0.0.1:8000/api/booking/token/"
QUESTIONS_ENDPOINT = "http://127.0.0.1:8000/api/assessment/question/"
ANSWER_ENDPOINT = "http://127.0.0.1:8000/api/assessment/answer/"
UPDATE_USER_INFO_ENDPOINT = f"http://127.0.0.1:8000/api/booking/user/{USER_ID}"
logger = logging.getLogger(__name__)

STUDENT_ID, DATE_OF_BIRTH, EDUCATION_YEAR, FACULTY, SUBJECTS, TEACHER, QUESTION, ANSWER = range(8)
reg_data = {}
def start(update: Update, context: CallbackContext) -> int:
    telegram_id = update.message.from_user.id
    print(telegram_id)
    # print(telegram_id)
    data = {
        "telegram_id": telegram_id
    }
    print("I am here")
    response = requests.get(url=USER_ENDPOINT, data=data)
    time.sleep(2)
    print(response.json())


    if "telegram_id" in response.json():
        reply_keyboard = [['fizika', 'matematika', 'informatika']]
        update.message.reply_text(
            "Thank you so much"
            "Please choose which subject do you want to give your comments",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SUBJECTS
    else:
        update.message.reply_text(
        "Hello, this bot serves you to assess teacher in TTPU."
        "Please enter your student id in numbers like: (12259)"
        "If you do not want to assess teachers simply click here /cancel."
        )
        return STUDENT_ID

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Ok, If you want to add more value to TTPU we are here'
        "Just click here /start "
    )

    return ConversationHandler.END

def student_id(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    student_id = update.message.text
    context.user_data['username'] = student_id
    context.user_data['telegram_id'] = user.id
    update.message.reply_text(
        "I see.Great, please enter your date of birth altogether(DDMMYYYY)"
    )
    return DATE_OF_BIRTH

def date_of_birth(update: Update, context: CallbackContext) -> int:
    date_of_birth = update.message.text
    context.user_data['password'] = str(date_of_birth)
    context.user_data['raw_password'] = date_of_birth
    print(context.user_data['raw_password'])

    reply_keyboard = [['1', '2', '3', '4']]
    update.message.reply_text(
        "Thank you so much for your patience and effort."
        "Please tell me about your education year"
        "for example (1, 2, 3, 4)",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDUCATION_YEAR

def education_year(update: Update, context: CallbackContext) -> int:
    education_year = update.message.text
    context.user_data['education_year'] = int(education_year)
    update.message.reply_text(
        "Now you need to tell me your faculty"
    )
    return FACULTY
def faculty(update: Update, context: CallbackContext) -> int:
    faculty = update.message.text
    context.user_data['faculty'] = faculty
    # creating a new user
    data = {
        "username": context.user_data['username'],
        "password": context.user_data['password'],
        "faculty": context.user_data['faculty'],
        "education_year": context.user_data['education_year'],
        "telegram_id": context.user_data['telegram_id'],
        "raw_password": context.user_data['raw_password']
    }
    requests.post(url=USER_ENDPOINT, data=data)
    time.sleep(2)

    reply_keyboard = [['fizika', 'matematika', 'informatika']]
    update.message.reply_text(
        "Thank you so much"
        "Please choose which subject do you want to give your comments",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return SUBJECTS

def subjects(update: Update, context: CallbackContext) -> int:
    # get authorization token if user starts from subjects
    telegram_id = update.message.from_user.id
    body = {
        "telegram_id": telegram_id
    }
    response = requests.get(url=USER_ENDPOINT, data=body)
    time.sleep(2)
    user = response.json()
    print(user)
    # get access token

    get_token_body = {
        "username": user['username'],
        "password": user['raw_password']
    }
    response = requests.post(url=ACCESS_TOKEN_ENDPOINT, data=get_token_body)
    time.sleep(2)
    access_token = response.json()['token']
    print(access_token)
    context.user_data['token'] = access_token

    subject = update.message.text
    context.user_data['subject'] = subject
    reply_keyboard = [['mirahmad', 'anvar', 'botir']]
    update.message.reply_text(
        "You need to choose which teacher you wanna comment ",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TEACHER

def teacher(update: Update, context: CallbackContext) -> int:
    teacher = update.message.text
    context.user_data['teacher'] = teacher
    access_token = context.user_data['token']
    # get a question from database
    response = requests.get(url=QUESTIONS_ENDPOINT,
                            headers={"Authorization": f"Token {access_token}"}
                            )
    # letting server some time
    time.sleep(2)
    question1 = response.json()[0]['question_text']  # just default question
    context.user_data['question'] = 1  # just default id
    update.message.reply_text(
        "Please, answer to this question"
        f"{question1}"
    )

    return ANSWER


def answer(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    context.user_data['answer'] = answer

    data = {
        "question": context.user_data['question'],
        "answer": context.user_data['answer'],
        "subject": context.user_data['subject'],
        "teacher": context.user_data['teacher']
    }
    access_token = context.user_data['token']
    header = {
        "Authorization": f"Token {access_token}"
    }
    # post answer
    requests.post(url=ANSWER_ENDPOINT, data=data, headers=header)
    time.sleep(2)
    update.message.reply_text(
        "Thank you for your time and effort"
        "You have added value to our growth"
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


