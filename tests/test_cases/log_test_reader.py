import pm4py
import pandas as pd
from pathlib import Path


class LogTestReader:
    CASE_ID_COL = 'Case ID'
    TIMESTAMP_COL = 'Complete Timestamp'
    ACTIVITY_COL = 'Activity'

    @staticmethod
    def read_log(filename: str):
        path_to_log = Path(__file__).parent.resolve().joinpath(filename)
        df = pd.read_csv(path_to_log, dtype={'Resource': str, 'matricola': str}, parse_dates=[LogTestReader.TIMESTAMP_COL])
        df = df.sort_values([LogTestReader.CASE_ID_COL, LogTestReader.TIMESTAMP_COL], ignore_index=True)
        df = pm4py.format_dataframe(df, case_id=LogTestReader.CASE_ID_COL, activity_key=LogTestReader.ACTIVITY_COL, timestamp_key=LogTestReader.TIMESTAMP_COL)
        return df
