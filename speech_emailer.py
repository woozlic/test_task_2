import json
import requests
from secret_codes import ID_FOLDER, IAM_TOKEN, GMAIL_ACC, GMAIL_PASSWORD
from pydub import AudioSegment
import tempfile
import os
import smtplib

from email.mime.text import MIMEText
from email.header import Header

server = smtplib.SMTP('smtp.gmail.com:587')

URL = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'


def return_ogg_binary(filename: str) -> bin:
    """
    Принимает название файла формата .ogg, wav или .mp3 в папке audio/, возвращает файл ogg в бинарном виде
    :param filename: имя файла
    :return: бинарный код ogg файла
    """
    folder = 'audio/'
    file = folder + filename
    filepath_and_name, file_extension = os.path.splitext(file)
    # filepath_and_name: audio/sample
    # file_extension: .mp3
    if file_extension.lower() != '.ogg':
        try:
            with open(file, 'rb') as mp3:
                mp3_binary = mp3.read()
                f = tempfile.NamedTemporaryFile(delete=False)
                f.write(mp3_binary)
                new_filename = f'{filepath_and_name}.ogg'
                AudioSegment.from_mp3(f.name).export(new_filename, format='ogg')  # сохранить ogg файл
            with open(new_filename, 'rb') as ogg:
                return ogg.read()
        except FileNotFoundError:
            print('Нет такого файла или директории')
    else:
        with open(file, 'rb') as ogg:
            return ogg.read()


def recognize(file_bin: bin) -> str:
    """
    Принимает бинарный код, возвращает распознанный с помощью Яндекс SpeechKit текст
    :param file_bin: файл .ogg в бинарном коде
    :return: распознанный текст
    """
    headers = {'Authorization': f'Bearer {IAM_TOKEN}'}

    params = {
        'lang': 'ru-RU',
        'folderId': ID_FOLDER,
        'sampleRateHeartz': 48000,
    }

    response = requests.post(URL, params=params, headers=headers, data=file_bin)

    decode_response = response.content.decode('UTF-8')
    text_json = json.loads(decode_response)
    if 'error_code' in text_json:
        error_message = text_json['error_message']
        if error_message == 'audio should be not empty':
            print('Такого файла не существует')
        elif error_message == 'audio duration should be less than 30s':
            print('Длина аудиофайла должна быть меньше 30 секунд')
        elif error_message == 'audio should be less than 1 mb':
            print('Размер аудиофайла должен быть меньше 1мб')
        elif error_message == 'rpc error: code = Unauthenticated desc = The token is invalid':
            print('Неправильный токен')
        else:
            print(f"Ошибка {text_json['error_code']}, {error_message}")
    else:
        return text_json['result']


def send_gmail(subject: str, text: str, to: str):
    """
    Отправляет мэил с заданной темой, текстом и получателем
    :param subject: Тема мэила
    :param text: Текст мэила
    :param to: Получатель
    :return:
    """
    msg = MIMEText(text, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    server.starttls()
    server.ehlo()
    try:
        server.login(GMAIL_ACC, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ACC, to, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        print('Неправильный логин и/или пароль')
    except smtplib.SMTPRecipientsRefused:
        print('Неправильный адрес почты')
    finally:
        server.quit()


def main():
    """
    Функция-обертка, которая все запускает. Для запуска необходим установленный ffmpeg
    """
    str_input = str(input('Введите имя файла: '))
    email_to = str(input('Введите эл. почту: '))
    binary = return_ogg_binary(str_input)
    recognized_text = recognize(binary)
    if recognized_text == '':
        print('Текст не удалось распознать')
    else:
        send_gmail('Результат распознавания', recognized_text, email_to)
        print(f'Мэил успешно отправлен {email_to}! Текст:\n{recognized_text}')


if __name__ == '__main__':
    main()
