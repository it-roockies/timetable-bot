import os
import requests

TIMETABLE_URL = os.environ.get("TIMETABLE_URL")
TIMETABLE_TOKEN = os.environ.get("TIMETABLE_TOKEN")

TELEGRAM_USER_ENDPOINT = f"{TIMETABLE_URL}/api/telegramuser/"
TELEGRAM_BOT_ENDPOINT = f"{TIMETABLE_URL}/api/telegrambot/"
SUBJECT_ENDPOINT = f"{TIMETABLE_URL}/api/subject/"
TEACHER_ENDPOINT = f"{TIMETABLE_URL}/api/teacher/"

QUESTION_ENDPOINT = f"{TIMETABLE_URL}/api/question/"
ANSWER_ENDPOINT = f"{TIMETABLE_URL}/api/answer/"


def get_userinfo(telegram_id: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    response = requests.get(url=TELEGRAM_USER_ENDPOINT, headers=headers)
    return response.json()


def create_telegram_user(telegram_id: str, username: str, email: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
    }
    data = {
        'telegram_id': f'{telegram_id}',
        'username': username,
        'email': email,
    }
    response = requests.post(url=TELEGRAM_BOT_ENDPOINT, headers=headers, data=data)
    return response.json()


def update_telegram_user(telegram_id: str, education_year: int, faculty: str):
    headers = {
        'Authorization': f'Bot {TIMETABLE_TOKEN}',
        'Telegram-ID': f'{telegram_id}'
    }
    data = {
        'education_year': education_year,
        'faculty': faculty,
    }
    response = requests.post(url=TELEGRAM_USER_ENDPOINT, headers=headers, data=data)
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