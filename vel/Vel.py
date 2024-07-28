from dash import jupyter_dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback, State
import pandas as pd 
import pm4py
import logview
from logview.utils import LogViewBuilder
from logview.predicate import *
from VelPredicate import VelPredicate
import inspect
from dash.exceptions import PreventUpdate
import os

# notebooks/dataset/Road_Traffic_Fine_Management_Process.csv
class Vel:
    def __init__(self, logName, fileType=".csv"):
        parent_dir = os.path.dirname(os.getcwd())
        print(f"Parent Directory: {parent_dir}")
        
        # Construct the path to the dataset
        self.logPath = os.path.join(parent_dir, "notebooks", "dataset", logName + fileType)
        print(f"Log Path: {self.logPath}")
        # "/Users/divyalekhas/Documents/Masters/Internship/logview/notebooks/dataset/Road_Traffic_Fine_Management_Process.csv"
        # + logName + fileType 
        self.CASE_ID_COL = 'Case ID'
        self.TIMESTAMP_COL = 'Complete Timestamp'
        self.ACTIVITY_COL = 'Activity'
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        self.name = ""
        self.predicate= ""
        self.selections = {}
        self.initLogView()
        # self.predicates = []

    # def readLog(self):
    #     self.df = pd.read_csv(self.logPath)
    #     self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
    #     return self.log
    
    def changeDefaultNames(self, caseId, timestamp, activity):
        self.CASE_ID_COL = caseId
        self.TIMESTAMP_COL = timestamp
        self.ACTIVITY_COL = activity
    
    def initLogView(self):
        self.log = pm4py.format_dataframe(self.df, case_id=self.CASE_ID_COL, activity_key=self.ACTIVITY_COL, timestamp_key=self.TIMESTAMP_COL)
        self.log_view = LogViewBuilder.build_log_view(self.log)
        return self.log_view

   
    def get_predicate_class(self, predicate_name):
        predicate_class_mappping = {
            'EqToConstant': EqToConstant,
            'NotEqToConstant': NotEqToConstant,
            'GreaterEqualToConstant': GreaterEqualToConstant,
            'LessEqualToConstant': LessEqualToConstant,
            'GreaterThanConstant': GreaterThanConstant,
            'LessThanConstant': LessThanConstant,
            'StartWith': StartWith,
            'EndWith': EndWith,
            'DurationWithin': DurationWithin,
            'SumAggregate': SumAggregate,
            # 'CountAggregate': CountAggregate,
            'MaxAggregate': MaxAggregate,
            'MinAggregate': MinAggregate
        }
        if predicate_name in predicate_class_mappping:
            return predicate_class_mappping[predicate_name]
        else:
            raise ValueError(f"No class found for value: {predicate_name}")
          
     
    def getPredicates(self):
        self.predicates = [pred for pred in logview.predicate.__all__ if pred not in ['Query', 'Union', 'CountAggregate']]
        return self.predicates


    def getLog(self):
        app = Dash(__name__)

        app.layout = html.Div([
        dash_table.DataTable(
            id='datatable-interactivity',
            columns=[
                {"name": i, "id": i, "deletable": True, "selectable": True} for i in self.log.columns
            ],
            data=self.log.to_dict('records'),
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
            html.Div(id='predicate-input1'),
            html.Div(id='predicate-output')
        ])

        @app.callback(
            Output('predicate-input1', 'children'),
            Input('pandas-dropdown-2', 'value')
        )
        def update_output(value):
            print("calling")
            if value is not None:
                
                pred = self.get_predicate_class(value)
                self.selections['predicate'] = pred
                print("Predicate: ", value)
                arg_names = VelPredicate.get_predicate_args(pred)
                
                if 'attribute_key' in arg_names and ('value' in arg_names or 'values' in arg_names):
                    print("in if")

                    return html.Div([
                        html.Label('Attribute Key:'),
                        dcc.Dropdown(id='attribute-key-dropdown', 
                                    options=[{'label': col, 'value': col} for col in self.df.columns]),
                        html.Div(id='value-options-container')
                    ])
                
                elif 'values' in arg_names and len(arg_names) == 1:
                    print("in elif:", pred)
                    unique_values = self.df['Activity'].unique()
                    print(f"unique_values: {unique_values}")

                    return html.Div([
                        html.Label('Values:'),
                        dcc.Dropdown(id='values-dropdown', 
                                    multi='values' in arg_names,
                                    options=[{'label': value, 'value': value} for value in unique_values])
                    ])
                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                        html.Label('Aggregate Column:'),
                        dcc.Dropdown(id='attribute-key-dropdown-groupby', 
                                    options=[{'label': col, 'value': col} for col in self.log.columns]),
                        html.Div(id='groupby-options-container')
                        ])
                    
                    elif value == 'DurationWithin':
                        return html.Div([
                            html.Label('Min Duration:'),
                            dcc.Input(id='min-duration', type='number'),
                            html.Label('Max Duration:'),
                            dcc.Input(id='max-duration', type='number')
                        ])
        
        # @callback to run the predicate for DurationWithin
        @app.callback(
            Output('predicate-output', 'children', allow_duplicate=True),
            [Input('min-duration', 'value'),
            Input('max-duration', 'value')],
            prevent_initial_call=True
        )
        def update_duration_output(min_duration, max_duration):
            if min_duration is None or max_duration is None:
                return []
            self.selections['min_duration'] = min_duration
            self.selections['max_duration'] = max_duration
            result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in result.columns],
                data=result.to_dict('records'),
                editable=False,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="multi",
                row_selectable="multi",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
                )
            return table
        @app.callback(
            Output('groupby-options-container', 'children'),
            Input('attribute-key-dropdown-groupby', 'value')
        )
        def update_groupby_options(selected_key):
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            return html.Div([
                html.Label('Group By Values:'),
                dcc.Dropdown(id='groupby-options',
                             multi=True,
                             options=[{'label': col, 'value': col} for col in self.log.columns])
                            
            ])
        @app.callback(
            Output('predicate-output', 'children', allow_duplicate=True),
            [Input('groupby-options', 'value')],
            prevent_initial_call=True
        )
        def update_groupby_output(selected_value):
            if selected_value is None:
                return []
            self.selections['values'] = selected_value
            # self.initLogView()
            result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in result.columns],
                data=result.to_dict('records'),
                editable=False,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="multi",
                row_selectable="multi",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
                )
            return table
        


        @app.callback(
            Output('predicate-output', 'children', allow_duplicate=True),
            Input('values-dropdown', 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_value):
            if selected_value is None:
                return html.Div("Please select a value from the dropdown.")
            else:
                self.selections['values'] = selected_value
                # self.initLogView()
                
                result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in result.columns],
                    data=result.to_dict('records'),
                    editable=False,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="multi",
                    row_selectable="multi",
                    row_deletable=True,
                    selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current=0,
                    page_size=10,
                    )
                
                return table


        @app.callback(
            Output('value-options-container', 'children'),
            Input('attribute-key-dropdown', 'value')
        )
        
        def update_value_options(selected_key):
            print(f"selected_key: {selected_key}")
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            unique_values = self.df[selected_key].unique()
            print(f"unique_values: {unique_values}")
            return html.Div([
                html.Label('Values:'),
                dcc.Dropdown(id='value-options', 
                            options=[{'label': value, 'value': value} for value in unique_values])
            ])

        @app.callback(
            Output('predicate-output', 'children'),
            [Input('value-options', 'value')]
        )
        def update_value_multi(selected_value):
            print("in options multi:", selected_value)
            if selected_value is None:
                return []
            self.selections['values'] = selected_value
            # self.initLogView()
            # VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)

            if result is None or result.empty:
                return html.Div("No data available for the selected predicate.")
            
            # Convert the result to a Dash table
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in result.columns],
                data=result.to_dict('records'),
                editable=False,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="multi",
                row_selectable="multi",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
                )
            
            return table

        return app

    def querryBuilder(self):
        
        app = Dash(__name__)

        app.layout = html.Div([
            html.H2("Query Builder"),
            html.Div([
                html.Label("Field:"),
                dcc.Input(id='field-input', type='text', value=''),
            ]),
            html.Div([
                html.Label("Operator:"),
                # predicate Div here
                # dcc.Dropdown(
                #     id='operator-dropdown',
                #     options=[
                #     
                #     ],
                #     value=''
                # ),
            ]),
            html.Div([
                html.Label("Value:"),
                dcc.Input(id='value-input', type='text', value=''),
            ]),
            html.Button('Construct Query', id='construct-query-button', n_clicks=0),
            html.Div(id='query-output', style={'marginTop': 20}),
        ])

# def applyInputPredicate(self, pred):
#         arg_names = VelPredicate.get_predicate_args(self.get_predicate_class(pred))
#         print("value: ", pred)
#         print("Arg names: ", arg_names)
#         result = html.Div([])
        
#         if 'attribute_key' in arg_names and ('value' in arg_names or 'values' in arg_names):
#             print("in if")
#             result = html.Div([
#                 html.Label('Attribute Key:'),
#                 dcc.Dropdown(id='attribute-key-dropdown', 
#                             options=[{'label': col, 'value': col} for col in self.df.columns]),
#                 html.Div(id='value-options-container')

#             ])
#             print("Before callback registration")
#             @callback(
#                 Output('value-options-container', 'children'),
#                 [Input('attribute-key-dropdown', 'value')]
#             )

#             def update_value_options(selected_key):
#                 print("IN callback registration")

#                 print(f"selected_key: {selected_key}")
#                 self.selections['attribute_key'] = selected_key
#                 unique_values = self.df[selected_key].unique()
#                 print(f"unique_values: {unique_values}")
#                 return html.Div([
#                     html.Label('Values:'),
#                     dcc.Dropdown(id='value-options', 
#                                 options=[{'label': value, 'value': value} for value in unique_values])
#                 ])
                 
#             print("After callback registration")
#             # This callback is now conditional based on whether 'values' is in arg_names
#             if 'values' in arg_names:
#                 @callback(
#                     Output('value-options', 'value'),
#                     [Input('value-options', 'value')]
#                 )
#                 def update_value_multi(selected_key):
#                     print("in options multi:", selected_key)
#                     self.selections['values'] = selected_key
#                     arg_names = VelPredicate.run_predicate(pred, self.log_view, self.df, self.selections)
#                     return selected_key
            
#          # Check for 'values' only
#         elif 'values' in arg_names and len(arg_names) == 1:
#             result = html.Div([
#                 html.Label('Values:'),
#                 dcc.Input(id='values-input')
#             ])

#         else:
#             print("in else")

#         # result.children = components
            
#         return result
#         # if value == 'EqToConstant':
#         #     self.predicate = 'EqToConstant'
#         #     result = html.Div([
#         #                 html.Label('Attribute Key:'),
#         #                 dcc.Dropdown(id='attribute-key', 
#         #                             options=[{'label': i, 'value': i} for i in self.df.columns]),
#         #                 html.Label('Value:'),
#         #                 dcc.Dropdown(id='attribute-value')  
#         #             ])
#         #     @callback(
#         #         Output('attribute-value', 'options'),
#         #         [Input('attribute-key', 'value')]
#         #     )
#         #     def set_values_dropdown(selected_key):
#         #         print("in options")
#         #         unique_values = self.df[selected_key].unique()
#         #         return [{'label': v, 'value': v} for v in unique_values]
#         #     @callback(
#         #         Output('query-result', 'children'),  
#         #         [Input('attribute-value', 'value')]
#         #     )
#         #     def perform_query(selected_value):
#         #             return result



# def applyInputPredicatenew(self, value):
#     arg_names = VelPredicate.get_predicate_args(self.get_predicate_class(value))
#     print("value: ", value)
#     print("Arg names: ", arg_names)
#     result = html.Div([])
#     if value == 'EqToConstant':
#         self.predicate = 'EqToConstant'
#         print("inin")
#         result = html.Div([
#                     html.Label('Attribute Key:'),
#                     dcc.Dropdown(id='attribute-key', 
#                                 options=[{'label': i, 'value': i} for i in self.df.columns]),
#                     html.Label('Value:'),
#                     dcc.Dropdown(id='attribute-value')  
#                 ])
#         print("Before callback\ registration")
#         @callback(
#             Output('attribute-value', 'options'),
#             [Input('attribute-key', 'value')]
#         )
#         def set_values_dropdown(selected_key):
#             print("in options")
#             unique_values = self.df[selected_key].unique()
#             return [{'label': v, 'value': v} for v in unique_values]
#         @callback(
#             Output('query-result', 'children'),  
#             [Input('attribute-value', 'value')]
#         )
#         def perform_query(selected_value):
#                 return result
