import json
from datetime import datetime, timedelta

import requests


def get_districts(state_like, districts_like):
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
