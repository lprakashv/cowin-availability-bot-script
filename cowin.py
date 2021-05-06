from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import json
import sys

slots = []


def fetch_slots(date_str, state_like='Karnataka', district_like='Bangalore'):
    district_ids = []

    states_resp = requests.get(
        'https://cdn-api.co-vin.in/api/v2/admin/location/states')
    if states_resp.status_code == 200:
        states_resp.json()['states']
        state_id = next((state['state_id'] for state in states_resp.json()[
                        'states'] if state_like.lower() in state['state_name'].lower()), '')

        districts_resp = requests.get(
            'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}'.format(state_id))
        if districts_resp.status_code == 200:
            for district in districts_resp.json()['districts']:
                if district_like.lower() in district['district_name'].lower():
                    district_ids.append(district['district_id'])
        else:
            print(
                "Error getting districts for state like {} - {}".format(state_like, resp.status_code))
            return
    else:
        print("Error getting states list {}".format(resp.status_code))
        return

    final = pd.DataFrame()
    for did in district_ids:
        resp = requests.get(
            'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict',
            params={'district_id': did, 'date': date_str})
        if resp.status_code == 200:
            centers = resp.json()['centers']
            df = pd.read_json(json.dumps(centers))
            selected_cols = ['center_id', 'name', 'address', 'from',
                             'to', 'fee_type', 'block_name', 'pincode']
            df = df[selected_cols]

            temp = []
            for center in centers:
                for session in center['sessions']:
                    temp.append(session)

            df1 = pd.DataFrame(
                temp)[['date', 'available_capacity', 'min_age_limit', 'vaccine', 'slots']]
            df[df1.columns.to_list()] = df1

            final = final.append(df)
        else:
            print("Error {}".format(resp.status_code))
    if len(final) > 0:
        file_name = 'available_slots_{}_{}.csv'.format(
            state_like, district_like, date_str)

        final = final[final['available_capacity'] > 0]

        # you can filter the data according to your requirements!

        # final = final[(final['min_age_limit'] < 30) & (final['available_capacity'] > 0)]

        final.to_csv(file_name)

        # you can even send that data to a telegram bot or anywhere you want!
        send_to_telegram(file_name)

        print("File saved as {}!".format(file_name))


def send_to_telegram(file_name):
    file = open(file_name, 'rb')
    resp = requests.post('https://api.telegram.org/bot1815140163:AAGpKyCWDpWHhKkcK9Ojls_EzuJLpzqfyt8/sendDocument',
                         data={'chat_id': -513272224}, files={'document': file})
    if resp.ok:
        print('Successfully sent document {} to Telegram group!'.format(file_name))
    else:
        print('Failed to send document {} to Telegram group! - {}'.foramt(file_name, resp.content))


if __name__ == '__main__':
    current_date = datetime.now().date()
    current_date += timedelta(days=1)
    next_date_str = "{}-{}-{}".format(current_date.day,
                                      current_date.month, current_date.year)
    state_like = 'Karnataka'
    district_like = 'Bangalore'
    if len(sys.argv) >= 3:
        state_like = sys.argv[1]
        district_like = sys.argv[2]
    fetch_slots(next_date_str, state_like=state_like,
                district_like=district_like)
