import os
import requests

TIMETABLE_URL = os.environ.get("TIMETABLE_URL")
TIMETABLE_TOKEN = os.environ.get("TIMETABLE_TOKEN")

TELEGRAM_USER_ENDPOINT = f"{TIMETABLE_URL}/api/telegramuser/"
TELEGRAM_BOT_ENDPOINT = f"{TIMETABLE_URL}/api/telegrambot/"
SUBJECT_ENDPOINT = f"{TIMETABLE_URL}/api/subject/"
TEACHER_ENDPOINT = f"{TIMETABLE_URL}/api/teacher/"
GROUP_ENDPOINT = f"{TIMETABLE_URL}/api/group/"
TODAY_LESSON_ENDPOINT = f"{TIMETABLE_URL}/api/grouplesson/"

QUESTION_ENDPOINT = f"{TIMETABLE_URL}/api/question/"
ANSWER_ENDPOINT = f"{TIMETABLE_URL}/api/answer/"
CHOICE_ENDPOINT = f"{TIMETABLE_URL}/api/choice/"


def get_userinfo(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=TELEGRAM_USER_ENDPOINT, headers=headers)
    return response.json()


def create_telegram_user(telegram_id: str, username: str, date_of_birth: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
    }
    data = {
        'telegram_id': f'{telegram_id}',
        'username': username,
        'date_of_birth': date_of_birth,
    }
    response = requests.post(url=TELEGRAM_BOT_ENDPOINT, headers=headers, data=data)
    return response.json()


def update_telegram_user(telegram_id: str, group: int):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}',
        'Content-Type': 'application/json'
    }
    print(group)
    # data = {
    #     "group": {"id": group}
    # }
    payload = "{\n    \"group\": {\"id\": %d }\n}" %group
    response = requests.request("POST", url=TELEGRAM_USER_ENDPOINT, headers=headers, data=payload)
    return response.json()

def get_today(telegram_id: str, group: str, date: str, minutes: int):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    data = {
        'group': group,
        'date': date,
        'minutes': minutes
    }
    response = requests.get(url=TODAY_LESSON_ENDPOINT, headers=headers, data=data)
    return response.json()

def get_subjects(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=SUBJECT_ENDPOINT, headers=headers)
    return response.json()


def get_teachers(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=TEACHER_ENDPOINT, headers=headers)
    return response.json()

def get_choices(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=CHOICE_ENDPOINT, headers=headers)
    return response.json()


def get_groups(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=GROUP_ENDPOINT, headers=headers)
    return response.json()


def get_questions(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=QUESTION_ENDPOINT, headers=headers)
    return response.json()


def create_answer(telegram_id: str, subject: int, teacher: int, question: int, answer: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    data = {
        "subject": subject,
        "teacher": teacher,
        "question": question,
        "answer": answer,
    }
    response = requests.post(url=ANSWER_ENDPOINT, headers=headers, data=data)
    return response.json()
