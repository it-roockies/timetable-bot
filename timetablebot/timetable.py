import os
import logging
import requests

logger = logging.getLogger(__name__)

TIMETABLE_URL = os.environ.get("TIMETABLE_URL")
TIMETABLE_TOKEN = os.environ.get("TIMETABLE_TOKEN")

TELEGRAM_USER_ENDPOINT = f"{TIMETABLE_URL}/api/telegramuser/"
TELEGRAM_BOT_ENDPOINT = f"{TIMETABLE_URL}/api/telegrambot/"
SUBJECT_ENDPOINT = f"{TIMETABLE_URL}/api/subject/"
TEACHER_ENDPOINT = f"{TIMETABLE_URL}/api/teacher/"
GROUP_ENDPOINT = f"{TIMETABLE_URL}/api/group/"
TODAY_LESSON_ENDPOINT = f"{TIMETABLE_URL}/api/grouplesson/"
MESSAGE_ENDPOINT = f"{TIMETABLE_URL}/api/message/"

QUESTION_ENDPOINT = f"{TIMETABLE_URL}/api/question/"
ANSWER_ENDPOINT = f"{TIMETABLE_URL}/api/answer/"
CHOICE_ENDPOINT = f"{TIMETABLE_URL}/api/choice/"


def request(*, method: str, url: str, telegram_id=None, data=None):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
    }
    if telegram_id is not None:
        headers.update({
            'Telegram-ID': f'{telegram_id}',
        })

    try:
        response = requests.request(method=method, url=url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception(str(e))
        if hasattr(e, "response"):
            logger.debug(e.response.text)
        return None


def get_userinfo(telegram_id: str):
    return request(method="GET", url=TELEGRAM_USER_ENDPOINT, telegram_id=telegram_id)


def create_telegram_user(telegram_id: str, username: str, date_of_birth: str):
    data = {
        'telegram_id': f'{telegram_id}',
        'username': username,
        'date_of_birth': date_of_birth,
    }
    return request(method="POST", url=TELEGRAM_BOT_ENDPOINT, data=data)


def update_telegram_user(telegram_id: str, group: int):
    data = {
        "group": {
            "id": group,
        },
    }
    return request(method="POST", url=TELEGRAM_USER_ENDPOINT, telegram_id=telegram_id, data=data)


class Message(object):
    def __init__(self, messages):
        self.messages = {
            message['message_id']: message['text']
            for message in messages
        }

    def __getattribute__(self, item):
        messages = super(Message, self).__getattribute__('messages')
        if item not in messages:
            logger.error(f"{item} is not in messages")
            return item
        return messages[item]


def get_messages():
    response = request(method="GET", url=MESSAGE_ENDPOINT)
    return Message(response)


def get_today(telegram_id: str, group: str, date: str, minutes: int):
    data = {
        'group': group,
        'date': date,
        'minutes': minutes
    }
    return request(method="GET", url=TODAY_LESSON_ENDPOINT, telegram_id=telegram_id, data=data)


def get_subjects(telegram_id: str):
    response = requests.get(url=SUBJECT_ENDPOINT, telegram_id=telegram_id)
    return response.json()


def get_teachers(telegram_id: str):
    return request(method="GET", url=TEACHER_ENDPOINT, telegram_id=telegram_id)


def get_choices(telegram_id: str):
    return request(method="GET", url=CHOICE_ENDPOINT, telegram_id=telegram_id)


def get_groups(telegram_id: str):
    return request(method="GET", url=GROUP_ENDPOINT, telegram_id=telegram_id)


def get_questions(telegram_id: str):
    return request(method="GET", url=QUESTION_ENDPOINT, telegram_id=telegram_id)


def create_answer(telegram_id: str, subject: int, teacher: int, question: int, answer: str):
    data = {
        "subject": subject,
        "teacher": teacher,
        "question": question,
        "answer": answer,
    }
    return request(method="POST", url=ANSWER_ENDPOINT, telegram_id=telegram_id, data=data)
