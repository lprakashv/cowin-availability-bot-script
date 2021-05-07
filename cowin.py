import json
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import requests

from cowin_api import get_centers_for_districts, get_districts
from cowin_data_utils import (create_final_data_frame_for_centers,
                              filtered_dataframe, flatten_sessions_columns,
                              get_summary_text)
from telegram_api import send_to_telegram


def fetch_and_dump_slots(date_str, state_like, districts_like=None):
    try:
        districts_data = get_districts(state_like, districts_like)
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
            send_to_telegram(state_name, district_names,
                             date_str, file_name, df)

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
