from dash import jupyter_dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback
import pandas as pd 
import pm4py


# notebooks/dataset/Road_Traffic_Fine_Management_Process.csv
class Vel:
    def __init__(self, logName, fileType=".csv"):
        self.logPath = "/Users/divyalekhas/Documents/Masters/Internship/logview/notebooks/dataset/Road_Traffic_Fine_Management_Process.csv"
        # + logName + fileType 
        self.CASE_ID_COL = 'Case ID'
        self.TIMESTAMP_COL = 'Complete Timestamp'
        self.ACTIVITY_COL = 'Activity'
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        self.name = ""

    # path_to_log = "./dataset/Road_Traffic_Fine_Management_Process.csv"
    # df = pd.read_csv(path_to_log, dtype={'Resource': str, 'matricola': str}, parse_dates=[TIMESTAMP_COL])
    # df = df.sort_values([CASE_ID_COL, TIMESTAMP_COL], ignore_index=True)
    # log = pm4py.format_dataframe(df, case_id=CASE_ID_COL, activity_key=ACTIVITY_COL, timestamp_key=TIMESTAMP_COL)

    def readLog(self):
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        return self.log
    
    def changeDefaultNames(self, caseId, timestamp, activity):
        self.CASE_ID_COL = caseId
        self.TIMESTAMP_COL = timestamp
        self.ACTIVITY_COL = activity

    # def applyPredicate(self, predicate):
    #     query_s = Query('rs_sum_up', SumAggregate('amount', group_by=['case:concept:name']))

    def getNameApp(self):
        app = Dash(__name__)

        app.layout = html.Div([
        dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in self.df.columns
            ],
            data=self.df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current= 0,
            page_size= 10,
            ),
            html.Div(id='datatable-interactivity-container')
        ])

        @callback(
            Output('datatable-interactivity', 'style_data_conditional'),
            Input('datatable-interactivity', 'selected_columns')
        )
        def update_styles(selected_columns):
            return [{
                'if': { 'column_id': i },
                'background_color': '#D2F3FF'
            } for i in selected_columns]
        
        return app
        # @callback(
        #     Output('datatable-interactivity-container', "children"),
        #     Input('datatable-interactivity', "derived_virtual_data"),
        #     Input('datatable-interactivity', "derived_virtual_selected_rows"))
