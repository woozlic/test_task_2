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


def return_ogg_binary(filename):
    # функция принимает название файла, который находится в этой же директории и возвращает ogg файл
    filepath, file_extension = os.path.splitext(filename)
    if file_extension.lower() != '.ogg':
        with open(filename, 'rb') as mp3:
            mp3_binary = mp3.read()
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(mp3_binary)
            new_filename = f'{filepath}.ogg'
            AudioSegment.from_mp3(f.name).export(new_filename, format='ogg')  # сохранить ogg файл
            with open(new_filename, 'rb') as ogg:
                ogg_binary = ogg.read()
                return ogg_binary
    else:
        return filename


def recognize(filename):
    # функция принимает имя файла, находящегося в той же директории и возвращает str распознанный текст
    ogg_binary = return_ogg_binary('sample.mp3')
    headers = {'Authorization': f'Bearer {IAM_TOKEN}'}

    params = {
        'lang': 'ru-RU',
        'folderId': ID_FOLDER,
        'sampleRateHeartz': 48000,
    }

    response = requests.post(URL, params=params, headers=headers, data=ogg_binary)

    decode_response = response.content.decode('UTF-8')
    text = json.loads(decode_response)
    return text['result']


def send_gmail(subject, text, to):
    # функция отправляет мэйл с gmail почты
    msg = MIMEText(text, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    server.starttls()
    server.ehlo()
    server.login(GMAIL_ACC, GMAIL_PASSWORD)
    server.sendmail(GMAIL_ACC, to, msg.as_string())
    server.quit()


def main():
    # функция обертка, которая все запускает
    str_input = str(input('Введите имя файла: '))
    email_to = str(input('Введите эл. почту: '))
    recognized_text = recognize(str_input)
    send_gmail('Результат распознавания', recognized_text, email_to)
    print('Мэил успешно отправлен!')


if __name__ == '__main__':
    main()
