import json

import pandas as pd

from utils import bold, escape, underline


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

    summary = underline(bold(escape('Summary for [ {}, [{}], {} ]'.format(
        state_name, '; '.join(district_names), date_str)))) + '\n\n'

    for (age, vaccine), grouped_value in groups.items():
        summary += escape('Centers with slot availability for ') + bold(
            escape('age: {}+ years and vaccine: "{}":'.format(age, vaccine))) + '\n'
        indices = grouped_value.values
        names = df.loc[indices, 'name'].values
        for name in names:
            summary += escape('- ' + name) + '\n'
        summary += '\n\n'

    print(summary)

    return summary
