import json
import os

import requests

from cowin_data_utils import get_summary_text


def send_to_telegram(state_name, district_names, date_str, file_name, df):
    token = os.environ['TELEGRAM_TOKEN']
    resp = requests.get(
        'https://api.telegram.org/bot{}/getUpdates'.format(token))
    if resp.ok:
        summary = get_summary_text(state_name, district_names, date_str, df)

        print(summary)

        result = resp.json()['result']
        chat_ids = [update['my_chat_member']['chat']['id']
                    for update in result if 'id' in update.get('my_chat_member', {}).get('chat', {})]
        file = open(file_name, 'rb')

        for chat_id in chat_ids:
            sendresp = requests.post('https://api.telegram.org/bot{}/sendDocument'.format(token),
                                     data={'chat_id': chat_id}, files={'document': file})
            if sendresp.ok:
                print(
                    'Successfully sent document {} to Telegram group!'.format(file_name))
            else:
                print(
                    'Failed to send document {} to Telegram group! - {}'.foramt(file_name, sendresp.content))

            sendresp = requests.post('https://api.telegram.org/bot{}/sendMessage'.format(
                token), data={'chat_id': chat_id, 'text': summary, 'parse_mode': 'MarkdownV2'})
            if sendresp.ok:
                print(
                    'Successfully sent text {} to Telegram group!'.format(summary))
            else:
                print(
                    'Failed to send text {} to Telegram group! - {}'.format(summary, sendresp.content))
    else:
        print('Failed to get Telegram group chat! - {}'.foramt(resp.content))
