from datetime import datetime, timedelta
import requests
import pandas as pd
import json
import sys
import os


def get_districts(state_like):
    district_ids = []
    district_names = []
    state_name = state_like

    states_resp = requests.get(
        'https://cdn-api.co-vin.in/api/v2/admin/location/states')
    if states_resp.status_code == 200:
        states_resp.json()['states']
        state_id, state_name = next(((state['state_id'], state['state_name']) for state in states_resp.json()[
            'states'] if state_like.lower() in state['state_name'].lower()), ('', ''))

        districts_resp = requests.get(
            'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}'.format(state_id))
        if districts_resp.status_code == 200:
            for district in districts_resp.json()['districts']:
                if districts_like and any([dl.lower() in district['district_name'].lower() for dl in districts_like]):
                    district_ids.append(district['district_id'])
                    district_names.append(district['district_name'])
        else:
            raise RuntimeError(
                "Error getting districts for state like {} - {}".format(state_like, resp.status_code))
    else:
        raise RuntimeError(
            "Error getting states list {}".format(resp.status_code))
    return {'district_ids': district_ids, 'district_names': district_names, 'state_name': state_name}


def get_centers_for_districts(date_str, district_ids):
    all_centers = []
    for did in district_ids:
        resp = requests.get(
            'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict',
            params={'district_id': did, 'date': date_str})
        if resp.status_code == 200:
            centers = resp.json()['centers']
            all_centers += centers
        else:
            raise RuntimeError("Unable to fetch calendar by district id {} Error {}".format(
                did, resp.status_code))
    return all_centers


def flatten_sessions_columns(df, centers):
    temp = []
    for center in centers:
        for session in center['sessions']:
            temp.append(session)

    df1 = pd.DataFrame(
        temp)[['date', 'available_capacity', 'min_age_limit', 'vaccine', 'slots']]
    df[df1.columns.to_list()] = df1
    return df


def create_final_data_frame_for_centers(centers):
    df = pd.read_json(json.dumps(centers))
    selected_cols = ['center_id', 'name', 'address', 'from',
                     'to', 'fee_type', 'block_name', 'pincode']
    df = df[selected_cols]

    df = flatten_sessions_columns(df, centers)

    return df


def filtered_dataframe(df):
    # you can filter the data according to your requirements!
    non_empty_slots_mask = df['slots'].apply(
        lambda x: None if x == [] else x).notnull()
    df = df.loc[(df['available_capacity'] > 0)
                & non_empty_slots_mask]
    return df


def get_summary_text(state_name, district_names, date_str, df):
    df = df[['min_age_limit', 'vaccine', 'name']]
    grouped = df.groupby(['min_age_limit', 'vaccine'])
    groups = grouped.groups

    summary = '---Summary for [{} | [{}] | {}]---\n'.format(
        state_name, ', '.join(district_names), date_str)
    for (age, vaccine), grouped_value in groups.items():
        summary += 'Centers with slot availability for min age={} and vaccine={}:\n'.format(
            age, vaccine)
        indices = grouped_value.values
        names = df.loc[indices, 'name'].values
        for name in names:
            summary += '- {}\n'.format(name)
        summary += '-----\n'

    print(summary)

    return summary


def send_to_telegram(state_name, district_names, date_str, file_name, df=None):
    token = os.environ['TELEGRAM_TOKEN']
    resp = requests.get(
        'https://api.telegram.org/bot{}/getUpdates'.format(token))
    if resp.ok:
        if not df:
            df = pd.read_csv(file_name)
        summary = get_summary_text(state_name, district_names, date_str, df)

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
                token), data={'chat_id': chat_id, 'text': summary})
            if sendresp.ok:
                print(
                    'Successfully sent text {} to Telegram group!'.format(summary))
            else:
                print(
                    'Failed to send text {} to Telegram group! - {}'.foramt(summary, sendresp.content))
    else:
        print('Failed to get Telegram group chat! - {}'.foramt(resp.content))


def fetch_and_dump_slots(date_str, state_like, districts_like=None):
    try:
        districts_data = get_districts(state_like)
        district_ids = districts_data['district_ids']
        district_names = districts_data['district_names']
        state_name = districts_data['state_name']

        centers = get_centers_for_districts(date_str, district_ids)

        df = create_final_data_frame_for_centers(centers)

        df = filtered_dataframe(df)

        if len(df) > 0:
            file_name = 'available_slots_{}_{}_{}.csv'.format(
                state_name.replace(' ', ''), '-'.join([dn.replace(' ', '') for dn in district_names]), date_str)

            df.to_csv(file_name)

            # you can even send that data to a telegram bot or anywhere you want!
            send_to_telegram(state_name, district_names, date_str, file_name)

            print("File saved as {}!".format(file_name))
        else:
            print('No available slots were found for date={}, state_like={}, districts_like=[{}]'.format(
                date_str, state_like, ' '.join(districts_like)))
    except RuntimeError as error:
        print('Some error occurred while processing: {}'.format(error))


if __name__ == '__main__':
    next_date = datetime.now().date() + timedelta(days=1)
    next_date_str = datetime.strftime(next_date, '%d-%m-%Y')
    if len(sys.argv) >= 2:
        state_like = sys.argv[1]
        districts_like = sys.argv[2:]
        fetch_and_dump_slots(next_date_str, state_like=state_like,
                             districts_like=districts_like)
    else:
        print(
            'please pass arguments of the form: <STATE_LIKE> [<DISTRICT_LIKE_1> <DISTRICT_LIKE_2>..]')
