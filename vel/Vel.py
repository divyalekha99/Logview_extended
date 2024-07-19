from dash import jupyter_dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback, State
import pandas as pd 
import pm4py
import logview
from logview.utils import LogViewBuilder
from logview.predicate import *

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
        self.predicate= ""
        # self.predicates = []

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
    
    def initLogView(self):
        self.log = pm4py.format_dataframe(self.df, case_id=self.CASE_ID_COL, activity_key=self.ACTIVITY_COL, timestamp_key=self.TIMESTAMP_COL)
        self.log_view = LogViewBuilder.build_log_view(self.log)
        return self.log_view

    # def runQuery(self, Qname, attribute, value):
    #     if self.predicate == 'EqToConstant':
    #         query = Query(Qname, EqToConstant(attribute, value))
    #         result_set_query, complement_result_set_query = self.log_view.evaluate_query('rs_SCC', self.log, query)
    #         return result_set_query, complement_result_set_query

    def applyInputPredicate(self, value):
        print("in")
        result = html.Div([])
        if value == 'EqToConstant':
            self.predicate = 'EqToConstant'
            print("inin")
            result = html.Div([
                        html.Label('Attribute Key:'),
                        dcc.Dropdown(id='attribute-key', 
                                    options=[{'label': i, 'value': i} for i in self.df.columns]),
                        html.Label('Value:'),
                        dcc.Dropdown(id='attribute-value')
            @callback(
                Output('attribute-value', 'options'),
                [Input('attribute-key', 'value')]
            )
            def set_values_dropdown(selected_key):
                print("in options")
                unique_values = self.df[selected_key].unique()
                return [{'label': v, 'value': v} for v in unique_values]
            @callback(
                Output('query-result', 'children'),  
                [Input('attribute-value', 'value')]
            )
            def perform_query(selected_value):
                    return result

    def getPredicates(self):
        self.predicates = logview.predicate.__all__
        print(logview.predicate.__all__)
        return self.predicates


    def getLog(self):
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
            html.Div(id='datatable-interactivity-container'),
            html.Button('Update Columns', id='update-columns-button', n_clicks=0),
            html.Div(id='update-status'),
            dcc.Store(id='stored-selected-columns')
        ])

        @app.callback(
            Output('stored-selected-columns', 'data'),
            Input('datatable-interactivity', 'selected_columns')
        )
        def store_selected_columns(selected_columns):
            return selected_columns
        
        @app.callback(
            Output('update-status', 'children'),
            Input('update-columns-button', 'n_clicks'),
            State('stored-selected-columns', 'data')
        )
        
        def update_column_names(n_clicks, selected_columns):
            if n_clicks > 0 and selected_columns:
                if len(selected_columns) >= 3:
                    self.changeDefaultNames(selected_columns[0], selected_columns[1], selected_columns[2])
                    return f"Updated Columns: CASE_ID_COL: {self.CASE_ID_COL}, TIMESTAMP_COL: {self.TIMESTAMP_COL}, ACTIVITY_COL: {self.ACTIVITY_COL}"
                else:
                    return "Please select at least 3 columns to update CASE_ID_COL, TIMESTAMP_COL, and ACTIVITY_COL."
            return "No columns selected for update."


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
    

    def displayPredicates(self):

        app = Dash(__name__)
        app.layout = html.Div([
            dcc.Dropdown(self.getPredicates(), id='pandas-dropdown-2'),
            # html.Div(id='pandas-output-container-2'),
            html.Div(id='predicate-inputs'), 
            html.Div(id='predicate-output') 
        ])

        @callback(
            Output('predicate-inputs', 'children'),
            Input('pandas-dropdown-2', 'value')
        )
        def update_output(value):
            print("calling")
            return self.applyInputPredicate(value)
            # return f'You have selected {value}'
        
        return app
    
    # def displayList(self):
    # dynamic selction

    # def getInputPredicate(self):

    #     app = Dash(__name__)
        
    #     predicates = self.getPredicates()
    #     app.layout = html.Div([
    #     dcc.Dropdown(
    #         id='predicate-selector',
    #         options=[{'label': i, 'value': i} for i in predicates],
    #         value=predicates[0]  # Default value
    #     ),
    #     html.Div(id='predicate-inputs'),  # Placeholder for dynamic inputs
    #     html.Button('Apply Predicate', id='apply-predicate-btn'),
    #     html.Div(id='predicate-output')  # Placeholder for output
    #     ])
    #     @app.callback(
    #         Output('predicate-inputs', 'children'),
    #         Input('predicate-selector', 'value')
    #     )
    #     def update_inputs(selected_predicate):
    #         if selected_predicate == 'SumAggregate':
    #             return html.Div([
    #                 html.Label('Aggregate column:'),
    #                 dcc.Input(id='amount-input', type='text'),
    #                 html.Label('Group By:'),
    #                 dcc.Input(id='group-by-input', type='text')
    #             ])
    #         
    #         return html.Div([])  # Return an empty div for predicates without additional inputs
    #     @app.callback(
    #         Output('predicate-output', 'children'),
    #         Input('apply-predicate-btn', 'n_clicks'),
    #         State('predicate-selector', 'value'),
    #         State('amount-input', 'value'),
    #         State('group-by-input', 'value')
    #     )
    #     def apply_predicate(n_clicks, selected_predicate, amount, group_by):
    #         if n_clicks is None:
    #             return ''  # No action if button hasn't been clicked

    #         if selected_predicate == 'SumAggregate':
    #             return f'Applying {selected_predicate} with amount={amount} and group_by={group_by.split(",")}'
    #         

    #         return 'Predicate applied'

    #     # if __name__ == '__main__':
    #     #     app.run_server(debug=True)
    #     return app


