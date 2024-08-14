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
from dash.dependencies import MATCH, ALL
import dash_bootstrap_components as dbc
import os
import dash
import feffery_antd_components as fac

# notebooks/dataset/Road_Traffic_Fine_Management_Process.csv
class Vel:
    def __init__(self, logName, fileType=".csv"):
        parent_dir = os.path.dirname(os.getcwd())
        print(f"Parent Directory: {parent_dir}")
        
        # Construct the path to the dataset
        self.logPath = os.path.join(parent_dir, "notebooks", "dataset", logName + fileType)
        print(f"Log Path: {self.logPath}")

        self.CASE_ID_COL = 'Case ID'
        self.TIMESTAMP_COL = 'Complete Timestamp'
        self.ACTIVITY_COL = 'Activity'
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        self.name = ""
        self.predicate= []
        self.attribute_key = []
        self.selections = {
                    'query_name': '',
                    'predicate_class': [],
                    'predicate': [],
                    'attribute_key': [],
                    'values': [],
                    'min_duration': [],
                    'max_duration': [],
                }
        # self.condition = {
        #     'Query1': {
        #         'query_name': '',
        #         'conditions': [
        #             {
        #                 'predicate_class': None,
        #                 'attribute_key': None,
        #                 'values': None,
        #                 'min_duration': None,
        #                 'max_duration': None
        #             },
        #             {
        #                 'predicate_class': None,
        #                 'attribute_key': None,
        #                 'values': None,
        #                 'min_duration': None,
        #                 'max_duration': None
        #             }
        #         ]
        #     }
        # }


        self.initLogView()
        self.index = 0
        self.query = ''
        self.conditions = {}  # To store all queries with their conditions


    def initialize_query(self, index):
        query_key = f'Query{index + 1}'
        if query_key not in self.conditions:
            self.conditions[query_key] = {
                'query_name': '',
                'conditions': []
            }

    def update_condition(self, index, condition_index, field, value):
        query_key = f'Query{index + 1}'
        if query_key in self.conditions:
            conditions = self.conditions[query_key]['conditions']
            while len(conditions) <= condition_index:
                conditions.append({
                    'predicate': None,
                    'predicate_class': None,
                    'attribute_key': None,
                    'values': None,
                    'min_duration_seconds': None,
                    'max_duration_seconds': None
                })
            conditions[condition_index][field] = value
        else:
            print(f"Query '{query_key}' not found. Please initialize it first.")




    def reset(self):
        self.selections = {
                    'predicate_class': [],
                    'predicate': [],
                    'attribute_key': [],
                    'values': [],
                    'min_duration': [],
                    'max_duration': [],
                }

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

    def calculate_case_durations(self):
        duration_df = self.df.groupby(self.CASE_ID_COL)[self.TIMESTAMP_COL].agg(['min', 'max'])
        duration_df['duration'] = (duration_df['max'] - duration_df['min']).dt.total_seconds()
        return duration_df['duration']

    def get_min_max_duration(self):
        durations = self.calculate_case_durations()
        min_duration = durations.min()
        max_duration = durations.max()

        min_duration_adjusted = max(0, min_duration)  
        max_duration_adjusted = min(max_duration, max_duration)  

        return min_duration_adjusted, max_duration_adjusted

   
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
    
    def layoutTest_(self):


        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        app.layout = html.Div([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Name:', type='primary'), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(id='qname', placeholder='Enter a value', size='medium'), width=3)
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Condition:', type='primary'), width="auto", align="center"),
                        dbc.Col(
                            fac.AntdSpace(
                                [
                                    fac.AntdRadioGroup(
                                        options=[
                                            {'label': f'{c}', 'value': c}
                                            for c in self.getPredicates()
                                        ],
                                        id='radios',
                                        optionType='button'
                                    )
                                ],
                                direction='horizontal'
                            )
                        )
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='predicate_info'), width=12)
                    ]),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_input'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_display'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_output_button'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton('Generate Output', id='submit', type='primary', disabled=True), width="auto", align="center"
                        )
                    ], className="mb-3"),

                    dbc.Spinner(
                        dbc.Row([
                            dbc.Col(
                                html.Div(id='predicate_output', style={'overflowX': 'auto'})
                            )
                        ], className="mb-3"), color="primary"),
                ]), className="mb-4", style={'padding': '20px', 'margin': '20px', 'backgroundColor': 'white', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 'borderRadius': '5px'}),

                # className="mb-4",
                # style={'padding': '20px', 'margin': '20px'}
            # ),
        ], style={'padding': '20px', 'margin': '20px'})

        
        @app.callback(
            Output("Query_display", "children", allow_duplicate=True),
            Input("qname", "value"),
            prevent_initial_call=True
        )
        def update_query_(qname):
            
            self.name = qname
            query_str = f"Query('{qname}', ('', ''))"
            return html.Div([
                html.Pre(query_str, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6'
                })
            ])

        @app.callback(
            Output("predicate_info", "children"),
            Input("radios", "value")
        )
        def update_predicate_info(value):
            if value is not None:
                descriptions = {
                    'EqToConstant': "Keeps cases that contain at least an event with the given attribute equal to a constant value.",
                    'NotEqToConstant': "Keeps cases that do not contain any event with the given attribute equal to a constant value.",
                    'GreaterEqualToConstant': "Keeps cases that contain at least an event with the given attribute greater than or equal to a constant value.",
                    'LessEqualToConstant': "Keeps cases that contain at least an event with the given attribute lower than or equal to a constant value.",
                    'GreaterThanConstant': "Keeps cases that contain at least an event with the given attribute greater than a constant value.",
                    'LessThanConstant': "Keeps cases that contain at least an event with the given attribute lower than a constant value.",
                    'StartWith': "Keeps cases starting with the specified activities.",
                    'EndWith': "Keeps cases ending with a given activity.",
                    'DurationWithin': "Keeps cases with durations within a specified range in seconds.",
                    'SumAggregate': "Sums the values of the specified attribute for the specified group of columns.",
                    'MaxAggregate': "Finds the maximum value of the specified attribute for the specified group of columns.",
                    'MinAggregate': "Finds the minimum value of the specified attribute for the specified group of columns."
                }
                
                icon_map = {
                    'EqToConstant': 'antd-equals',
                    'NotEqToConstant': 'antd-not-equal',
                    'GreaterEqualToConstant': 'antd-greater-than-equal',
                    'LessEqualToConstant': 'antd-less-than-equal',
                    'GreaterThanConstant': 'antd-greater-than',
                    'LessThanConstant': 'antd-less-than',
                    'StartWith': 'antd-play',
                    'EndWith': 'antd-stop',
                    'DurationWithin': 'antd-clock',
                    'SumAggregate': 'antd-sum',
                    'MaxAggregate': 'antd-arrow-up',
                    'MinAggregate': 'antd-arrow-down'
                }

                description = descriptions.get(value, "No description available.")
                icon_class = icon_map.get(value, 'antd-info-circle')

                return html.Div([
                    html.I(className=f'{icon_class}', style={'marginRight': '10px'}),
                    description
                ], style={'color': 'gray', 'fontSize': 'small', 'display': 'flex', 'alignItems': 'center'})
            return html.Div()

        @app.callback(
            Output("Query_input", "children"),
            Output("Query_display", "children", allow_duplicate=True),
            Output("submit", "disabled", allow_duplicate=True),
            Input("radios", "value"),
            prevent_initial_call=True
        )

        def update_output(value):

            if value is not None:
                
                pred = self.get_predicate_class(value)
                self.selections = {}
                self.selections['predicate'] = pred
                print("Predicate: ", value)
                arg_names = VelPredicate.get_predicate_args(pred)
                self.predicate = value
                
                query_str = f"Query('{self.name}', {value}('', '')"


                if 'attribute_key' in arg_names and ('values' in arg_names):

                    return html.Div([
                           dbc.Row([
                                 dbc.Col(fac.AntdText('Attribute Key:', type='primary'), width="auto", align="center"),
                                 dbc.Col(fac.AntdSelect(
                                      id='attribute_key_dropdown', 
                                      options=[{'label': col, 'value': col} for col in self.df.columns],
                                      style={'width': '100%'}
                                 ), width=2)
                            ], className="mb-3"),
                                dbc.Col(html.Div(id='value_options_container'))
                    ]), html.Div([
                        html.Pre(query_str, style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'border': '1px solid #dee2e6'
                        })
                    ]), True
                
                elif 'attribute_key' in arg_names and ('value' in arg_names):
                    

                    return html.Div([
                           dbc.Row([
                                    dbc.Col(fac.AntdText('Attribute Key:', type='primary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdSelect(
                                        id='attribute_key_dropdown', 
                                        options=[{'label': col, 'value': col} for col in self.df.columns],
                                        style={'width': '100%'}
                                    ), width=2)
                                ], className="mb-3"),
                                    dbc.Col(fac.AntdText('Value:', type='primary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdInput(id='value_input', placeholder='Enter a value', size='medium', style={'width': '100%'}), width=2)

                    ]), html.Div([
                        html.Pre(query_str, style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'border': '1px solid #dee2e6'
                        })
                    ]), True


                    # return html.Div([
                    #     html.Label('Attribute Key:'),
                    #     dcc.Dropdown(id='attribute-key-dropdown', 
                    #                 options=[{'label': col, 'value': col} for col in self.df.columns],
                    #                 style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
                    #     html.Div(id='value-options-container',
                    #              style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'})
                    # ])
                
                elif 'values' in arg_names and len(arg_names) == 1:
                    print("in elif:", pred)
                    self.attribute_key = None
                    unique_values = self.df['Activity'].unique()
                    print(f"unique_values: {unique_values}")

                    return html.Div([
                           dbc.Row([
                                 dbc.Col(fac.AntdText('Values:', type='primary'), width="auto", align="center"),
                                 dbc.Col(fac.AntdSelect(
                                      id='values_dropdown', 
                                      options=[{'label': value, 'value': value} for value in unique_values],
                                      mode='tags',
                                      style={'width': '100%'}
                                 ), width=2)
                            ], className="mb-3")
                    ]), html.Div([
                        html.Pre(query_str, style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'border': '1px solid #dee2e6'
                        })
                    ]), True

                    # return html.Div([
                    #     html.Label('Values:'),
                    #     dcc.Dropdown(id='values-dropdown', 
                    #                 multi='values' in arg_names,
                    #                 options=[{'label': value, 'value': value} for value in unique_values])
                    # ])
                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                            dbc.Row([
                                 dbc.Col(fac.AntdText('Aggregate Column:', type='primary'), width="auto", align="center"),
                                 dbc.Col(fac.AntdSelect(
                                      id='attribute_key_dropdown_groupby', 
                                      options=[{'label': col, 'value': col} for col in self.log.columns],
                                      style={'width': '100%'}
                                 ), width=2)
                            ], className="mb-3"),
                            dbc.Col(html.Div(id='groupby_options_container'))
                        ]), html.Div([
                        html.Pre(query_str, style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'border': '1px solid #dee2e6'
                        })
                    ]), True

                        # return html.Div([
                        # html.Label('Aggregate Column:'),
                        # dcc.Dropdown(id='attribute-key-dropdown-groupby', 
                        #             options=[{'label': col, 'value': col} for col in self.log.columns]),
                        # html.Div(id='groupby-options-container')
                        # ])
                    
                    elif value == 'DurationWithin':
                        self.attribute_key = None

                        return html.Div([
                               dbc.Row([
                                   dbc.Col(fac.AntdText('Min Duration:', type='primary'), width="auto", align="center"),
                                   dbc.Col(fac.AntdTimePicker(id='min_duration', placeholder='Enter a value', showNow= False , style={'width': '100%'}), width=2),
                                   dbc.Col(fac.AntdText('Max Duration:', type='primary'), width="auto", align="center"),    
                                   dbc.Col(fac.AntdTimePicker(id='max_duration', placeholder='Enter a value', showNow= False ,style={'width': '100%'}), width=2)])
                        ]), html.Div([
                        html.Pre(query_str, style={
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'border': '1px solid #dee2e6'
                        })
                    ]), True



        # @callback to run the predicate for DurationWithin
        @app.callback(
            # Output('predicate_output', 'children', allow_duplicate=True),
            Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            [Input('qname', 'value'),
            Input('min_duration', 'value'),
            Input('max_duration', 'value')],
            prevent_initial_call=True
        )
        def update_duration_output(qname, min_duration, max_duration):
            if min_duration is None or max_duration is None:
                return []
            self.selections['min_duration'] = min_duration
            self.selections['max_duration'] = max_duration
            # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            # table = dash_table.DataTable(
            #     columns=[{"name": i, "id": i} for i in result.columns],
            #     data=result.to_dict('records'),
            #     editable=False,
            #     filter_action="native",
            #     sort_action="native",
            #     sort_mode="multi",
            #     column_selectable="multi",
            #     row_selectable="multi",
            #     row_deletable=True,
            #     selected_columns=[],
            #     selected_rows=[],
            #     page_action="native",
            #     page_current=0,
            #     page_size=10,
            #     )
            query_str = f"Query('{qname}', {self.predicate}('{min_duration}', '{max_duration}'))"
            return html.Div([
                    html.Pre(query_str, style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-word',
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'border': '1px solid #dee2e6'
                    })
                ]), False
        

        # @callback to return the groupby options
        @app.callback(
            Output('groupby_options_container', 'children'),
            Output('Query_display', 'children', allow_duplicate=True),  
            Input('attribute_key_dropdown_groupby', 'value'),
            prevent_initial_call=True
        )
        def update_groupby_options(selected_key):
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key

            query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', ''))"

            return html.Div([
                html.Label('Group By Values:'),
                dcc.Dropdown(id='groupby_options',
                             multi=True,
                             options=[{'label': col, 'value': col} for col in self.log.columns])
                            
            ]), html.Div([
                    html.Pre(query_str, style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-word',
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'border': '1px solid #dee2e6'
                    })
                ])
        
        # @callback to run the predicate for groupby
        @app.callback(
            # Output('predicate_output', 'children', allow_duplicate=True),
            Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            [Input('qname', 'value'),
            Input('groupby_options', 'value')],
            prevent_initial_call=True
        )
        def update_groupby_output(qname, selected_value):
            if selected_value is None:
                return []
            self.selections['values'] = selected_value
            # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            # table = dash_table.DataTable(
            #     columns=[{"name": i, "id": i} for i in result.columns],
            #     data=result.to_dict('records'),
            #     editable=False,
            #     filter_action="native",
            #     sort_action="native",
            #     sort_mode="multi",
            #     column_selectable="multi",
            #     row_selectable="multi",
            #     row_deletable=True,
            #     selected_columns=[],
            #     selected_rows=[],
            #     page_action="native",
            #     page_current=0,
            #     page_size=10,
            #     )
            query_str = f"Query('{qname}', {self.predicate}('{self.attribute_key}', '{selected_value}'))"
            return html.Div([
                    html.Pre(query_str, style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-word',
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'border': '1px solid #dee2e6'
                    })
                ]), False
        

        # @callback to run the predicate for values
        @app.callback(
            # Output('predicate_output', 'children', allow_duplicate=True),
            Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            Input('values_dropdown', 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_value):
            if selected_value is None:
                return html.Div("Please select a value from the dropdown.")
            else:
                self.selections['values'] = selected_value
                
                # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
                # table = dash_table.DataTable(
                #     columns=[{"name": i, "id": i} for i in result.columns],
                #     data=result.to_dict('records'),
                #     editable=False,
                #     filter_action="native",
                #     sort_action="native",
                #     sort_mode="multi",
                #     column_selectable="multi",
                #     row_selectable="multi",
                #     row_deletable=True,
                #     selected_columns=[],
                #     selected_rows=[],
                #     page_action="native",
                #     page_current=0,
                #     page_size=10,
                #     )
                
                # return table

                query_str = f"Query('{self.name}', {self.predicate}('', '{selected_value}'))"
                return html.Div([
                    html.Pre(query_str, style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-word',
                        'backgroundColor': '#f8f9fa',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'border': '1px solid #dee2e6'
                    })
                ]), False
            
        @app.callback(
            # Output('predicate_output', 'children', allow_duplicate=True),
            Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            Input('attribute_key_dropdown', 'value'),
            Input('value_input', 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_key, selected_value):
            # if selected_value is None:
            #     return html.Div("Please select a value from the dropdown.")
            # else:
            try:
                converted_value = float(selected_value)
            except ValueError:
                return html.Div("Invalid value. Please enter a numeric value.")
    
            self.selections['values'] = converted_value
            self.selections['attribute_key'] = selected_key
            # self.selections['values'] = float(selected_value)
            
            # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
            # table = dash_table.DataTable(
            #     columns=[{"name": i, "id": i} for i in result.columns],
            #     data=result.to_dict('records'),
            #     editable=False,
            #     filter_action="native",
            #     sort_action="native",
            #     sort_mode="multi",
            #     column_selectable="multi",
            #     row_selectable="multi",
            #     row_deletable=True,
            #     selected_columns=[],
            #     selected_rows=[],
            #     page_action="native",
            #     page_current=0,
            #     page_size=10,
            #     )
            query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', '{selected_value}'))"
            return html.Div([
                html.Pre(query_str, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6'
                })
            ]), False
            # query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', '{selected_value}'))"
            # return table, html.Div([
            #     html.Pre(query_str, style={
            #         'whiteSpace': 'pre-wrap',
            #         'wordBreak': 'break-word',
            #         'backgroundColor': '#f8f9fa',
            #         'padding': '10px',
            #         'borderRadius': '5px',
            #         'border': '1px solid #dee2e6'
            #     })
            # ])

        # @callback to update the value options based on the selected attribute key
        @app.callback(
            Output('value_options_container', 'children'),
            Output('Query_display', 'children', allow_duplicate=True),
            Input('attribute_key_dropdown', 'value'),
            prevent_initial_call=True
        )
        
        def update_value_options(selected_key):
            print(f"selected_key: {selected_key}")
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            unique_values = self.df[selected_key].unique()
            print(f"unique_values: {unique_values}")
            self.attribute_key = selected_key
            query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', ''))"

            return html.Div([
                   dbc.Row([
                            dbc.Col(fac.AntdText('Values:', type='primary'), width="auto", align="center"),
                            dbc.Col(fac.AntdSelect(
                                id='value_options', 
                                options=[{'label': value, 'value': value} for value in unique_values],
                                mode='tags',
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3")
            ]), html.Div([
                html.Pre(query_str, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6'
                })
            ])

           

        @app.callback(
            # Output('predicate_output', 'children'),
            Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            [Input('value_options', 'value')],
            prevent_initial_call=True
        )

        def update_value_multi(selected_value):
            print("in options multi:", selected_value)
            if selected_value is None:
                return []
            self.selections['values'] = selected_value
            query_str = f"Query('{self.name}', {self.predicate}('{self.attribute_key}', '{selected_value}'))"
            
            return html.Div([
                html.Pre(query_str, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6'
                })
            ]), False
            # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)

            # if result is None or result.empty:
            #     return html.Div("No data available for the selected predicate.")
            
            # Convert the result to a Dash table
            # table = dash_table.DataTable(
            #     columns=[{"name": i, "id": i} for i in result.columns],
            #     data=result.to_dict('records'),
            #     editable=False,
            #     filter_action="native",
            #     sort_action="native",
            #     sort_mode="multi",
            #     column_selectable="multi",
            #     row_selectable="multi",
            #     row_deletable=True,
            #     selected_columns=[],
            #     selected_rows=[],
            #     page_action="native",
            #     page_current=0,
            #     page_size=10,
            #     )
            
            # return table

        @app.callback(
            Output("predicate_output", "children"),
            [Input("submit", "nClicks")],
        )
        def on_button_click(n):
            if n >= 1:
                result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)

                if result is None or result.empty:
                    return html.Div("No data available for the selected predicate.")

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


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # app = dash.Dash(__name__)
    



    def Query_Builder_(self):


        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        app.layout = html.Div([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Name:', type='secondary'), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(id='qname', placeholder='Enter a value', size='middle'), width=3)
                    ], className="mb-3"),

                html.Div(id='condition-container' , children=[
                    
                    html.Div(id='condition-0', children=[

                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Query Condition{self.index + 1}:', type='secondary'), width="auto", align="center"),
                            dbc.Col(
                                fac.AntdSpace(
                                    [
                                        fac.AntdRadioGroup(
                                            options=[
                                                {'label': f'{c}', 'value': c}
                                                for c in self.getPredicates()
                                            ],
                                            # id=f'radios{self.index + 1}',
                                            id = {'type': 'radios', 'index': self.index},
                                            optionType='button'
                                        )
                                    ],
                                    direction='horizontal'
                                )
                            )
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(html.Div(
                                # id='predicate_info',
                                id = {'type': 'predicate-info', 'index': self.index},
                                
                                ), width=12)
                        ]),

                        dbc.Row([
                            dbc.Col(html.Div(
                                id = {'type': 'Query_input', 'index': self.index }                                
                                ))
                        ], className="mb-3"),

                        
                    ])
                ]),
                    dbc.Row([
                            dbc.Col(
                                fac.AntdButton(
                                    'Add Condition', 
                                    id='add-condition-button', 
                                    type='primary', 
                                    nClicks=0,
                                    icon=fac.AntdIcon(icon = 'antd-plus-square-two-tone')
                                ), 
                                width="auto", align="center"
                            )
                        ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_display'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_output_button'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton('Generate Output', id='submit', type='primary', nClicks=0, disabled=True), width="auto", align="center"
                        )
                    ], className="mb-3"),

                    dbc.Spinner(
                        dbc.Row([
                            dbc.Col(
                                html.Div(id='predicate_output', style={'overflowX': 'auto'})
                            )
                        ], className="mb-3"), color="primary"),
                ]), className="mb-4", style={'padding': '20px', 'margin': '20px', 'backgroundColor': 'white', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 'borderRadius': '5px'}),

        ], style={'padding': '20px', 'margin': '20px'}, id="Query_container")


        # @callback to add a new condition
        @app.callback(
        Output('condition-container', 'children'),
        Input('add-condition-button', 'nClicks'),
        State('condition-container', 'children')
        )
        def add_condition(nClicks, children):
            print("out add condition")
            if nClicks > 0:
                print("in add condition")
                if children is None:
                    children = []

                new_index = len(children)
                self.index = new_index
                new_condition = html.Div(id=f'condition-{new_index}', children=[
                    dbc.Row([
                        dbc.Col(fac.AntdText(f'Query Condition {new_index + 1}:', type='secondary'), width="auto", align="center"),
                        dbc.Col(
                            fac.AntdSpace(
                                [
                                    fac.AntdRadioGroup(
                                        options=[
                                            {'label': f'{c}', 'value': c}
                                            for c in self.getPredicates()
                                        ],
                                        # id='radios',
                                        optionType='button',
                                        id={'type': 'radios', 'index': new_index }
                                        # optionType='button'
                                    )
                                ],
                                direction='horizontal'
                            )
                        )
                    ], className="mb-3"),

                    dbc.Row([
                            dbc.Col(html.Div(
                                # id='predicate_info'
                                id={'type': 'predicate-info', 'index': new_index },
                                ), width=12)
                        ]),

                        dbc.Row([
                            dbc.Col(html.Div(
                                # id='Query_input'
                                id={'type': 'Query_input', 'index': new_index }
                                ))
                        ], className="mb-3"),

                        # dbc.Row([
                        #     dbc.Col(
                        #         fac.AntdButton(
                        #             'Add Condition', 
                        #             id='add-condition-button', 
                        #             type='primary', 
                        #             nClicks=0,
                        #             icon=fac.AntdIcon(icon = 'antd-plus-square-two-tone')
                        #         ), 
                        #         width="auto", align="center"
                        #     )
                        # ], className="mb-3"),
                    ])
                children.append(new_condition)

            return children
        
        @app.callback(
            Output("Query_display", "children"),
            [   
                Input("qname", "value"),
                Input({'type': 'attribute_key_dropdown', 'index': ALL}, "value"),
                # Input({'type': 'value_input', 'index': ALL}, "value"),
                Input({'type': 'value_options', 'index': ALL}, "value")
            ],
            prevent_initial_call=True
        )
        def update_query_display(qname, attribute_keys, value_options):
            query_str = ""
            self.reset()
            self.selections['query_name'] = qname
            print("in update_query_display", attribute_keys, value_options)

            for idx, (key, val_opts) in enumerate(zip(attribute_keys, value_options)):
                print("in update_query_display1:", key, val_opts)
                if key or val_opts:
                    predicate = self.predicate[idx]
                    value =  val_opts
                    print("in update_query_display2:", predicate, value)
                    pred_class = self.get_predicate_class(predicate)
                    self.selections['predicate_class'].append(pred_class)
                    self.selections['predicate'].append(predicate)
                    self.selections['attribute_key'].append(key)
                    self.selections['values'].append(value)
                    print("In update Selections:", self.selections)
                    if query_str:
                        query_str += f",({predicate}('{key}', '{value}'))"
                    else:
                        query_str = f"Query('{qname}', {predicate}('{key}', '{value}'))"
            print("Query String:", query_str)
            return html.Pre(query_str, style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-word',
                'backgroundColor': '#f8f9fa',
                'padding': '10px',
                'borderRadius': '5px',
                'border': '1px solid #dee2e6'
            })


        @app.callback(
            # Output("predicate_info", "children"),
            # Input("radios", "value")
            Output({'type': 'predicate-info', 'index': MATCH}, "children"),
            Input({'type': 'radios', 'index': MATCH}, "value")
        )
        def update_predicate_info(value):
            print("VALUE:", value)
            if value is not None:
                descriptions = {
                    'EqToConstant': "Keeps cases that contain at least an event with the given attribute equal to a constant value.",
                    'NotEqToConstant': "Keeps cases that do not contain any event with the given attribute equal to a constant value.",
                    'GreaterEqualToConstant': "Keeps cases that contain at least an event with the given attribute greater than or equal to a constant value.",
                    'LessEqualToConstant': "Keeps cases that contain at least an event with the given attribute lower than or equal to a constant value.",
                    'GreaterThanConstant': "Keeps cases that contain at least an event with the given attribute greater than a constant value.",
                    'LessThanConstant': "Keeps cases that contain at least an event with the given attribute lower than a constant value.",
                    'StartWith': "Keeps cases starting with the specified activities.",
                    'EndWith': "Keeps cases ending with a given activity.",
                    'DurationWithin': "Keeps cases with durations within a specified range in seconds.",
                    'SumAggregate': "Sums the values of the specified attribute for the specified group of columns.",
                    'MaxAggregate': "Finds the maximum value of the specified attribute for the specified group of columns.",
                    'MinAggregate': "Finds the minimum value of the specified attribute for the specified group of columns."
                }
                
                icon_map = {
                    'EqToConstant': 'antd-carry-out',
                    'NotEqToConstant': 'antd-not-equal',
                    'GreaterEqualToConstant': 'antd-greater-than-equal',
                    'LessEqualToConstant': 'antd-less-than-equal',
                    'GreaterThanConstant': 'antd-greater-than',
                    'LessThanConstant': 'antd-less-than',
                    'StartWith': 'antd-play',
                    'EndWith': 'antd-stop',
                    'DurationWithin': 'antd-clock',
                    'SumAggregate': 'antd-sum',
                    'MaxAggregate': 'antd-arrow-up',
                    'MinAggregate': 'antd-arrow-down'
                }

                description = descriptions.get(value, "No description available.")
                icon_class = icon_map.get(value, 'antd-info-circle')

                return html.Div([
                    fac.AntdIcon(
                                id='icon',
                                icon='antd-info-circle-two-tone',
                                style={'marginRight': '10px'}
                            ),

                    # html.I(className='antd-carry-out', style={'marginRight': '10px'}),
                    description
                ], style={'color': 'gray', 'fontSize': '15px', 'display': 'flex', 'alignItems': 'center', 'paddingBottom': '20px'})
            return html.Div()

        @app.callback(
            Output({'type': 'Query_input', 'index': MATCH}, "children"),  # This uses MATCH
            # Output("Query_display", "children", allow_duplicate=True),    # Regular output for Query_display
            # State("submit", "disabled"),           # Regular output for submit button
            Input({'type': 'radios', 'index': MATCH}, "value"),
            State({'type': 'radios', 'index': MATCH}, "id"),           # MATCH for the input
            prevent_initial_call=True
        )


        def update_output(value, id):
            print("in update_output", id)
            if value is not None:
                index = id['index']
                print("Index: ", index)
                pred = self.get_predicate_class(value)
                # self.reset()
                # self.selections['predicate'] = pred
                print("Predicate: ", value)
                arg_names = VelPredicate.get_predicate_args(pred)
                while len(self.predicate) <= index:
                    self.predicate.append(None)
                
                # while len(self.selections['predicate']) <= index:
                #     self.selections['predicate'].append(None)

                # self.selections['predicate'][index] = pred
                self.predicate[index] = value
                
                query_str = f"Query('{self.name}', {value}('', '')"


                if 'attribute_key' in arg_names and ('values' in arg_names):

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Attribute Key:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    # id='attribute_key_dropdown',
                                    id={'type': 'attribute_key_dropdown', 'index': index},
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                                dbc.Col(html.Div(
                                    # id='value_options_container'
                                    id={'type': 'value_options_container', 'index': index}
                                    ))
                    ]),True
                    # , html.Div([
                    #     html.Pre(query_str, style={
                    #         'whiteSpace': 'pre-wrap',
                    #         'wordBreak': 'break-word',
                    #         'backgroundColor': '#f8f9fa',
                    #         'padding': '10px',
                    #         'borderRadius': '5px',
                    #         'border': '1px solid #dee2e6'
                    #     })
                    # ])

                
                # elif 'attribute_key' in arg_names and ('value' in arg_names):
                    

                #     return html.Div([
                #         dbc.Row([
                #                     dbc.Col(fac.AntdText('Attribute Key:', type='primary'), width="auto", align="center"),
                #                     dbc.Col(fac.AntdSelect(
                #                         id='attribute_key_dropdown', 
                #                         options=[{'label': col, 'value': col} for col in self.df.columns],
                #                         style={'width': '100%'}
                #                     ), width=2)
                #                 ], className="mb-3"),
                #                     dbc.Col(fac.AntdText('Value:', type='primary'), width="auto", align="center"),
                #                     dbc.Col(fac.AntdInput(id='value_input', placeholder='Enter a value', size='medium', style={'width': '100%'}), width=2)

                #     ]), html.Div([
                #         html.Pre(query_str, style={
                #             'whiteSpace': 'pre-wrap',
                #             'wordBreak': 'break-word',
                #             'backgroundColor': '#f8f9fa',
                #             'padding': '10px',
                #             'borderRadius': '5px',
                #             'border': '1px solid #dee2e6'
                #         })
                #     ]), True
                
                # elif 'values' in arg_names and len(arg_names) == 1:
                #     print("in elif:", pred)
                #     self.attribute_key = None
                #     unique_values = self.df['Activity'].unique()
                #     print(f"unique_values: {unique_values}")

                #     return html.Div([
                #         dbc.Row([
                #                 dbc.Col(fac.AntdText('Values:', type='primary'), width="auto", align="center"),
                #                 dbc.Col(fac.AntdSelect(
                #                     id='values_dropdown', 
                #                     options=[{'label': value, 'value': value} for value in unique_values],
                #                     mode='tags',
                #                     style={'width': '100%'}
                #                 ), width=2)
                #             ], className="mb-3")
                #     ]), html.Div([
                #         html.Pre(query_str, style={
                #             'whiteSpace': 'pre-wrap',
                #             'wordBreak': 'break-word',
                #             'backgroundColor': '#f8f9fa',
                #             'padding': '10px',
                #             'borderRadius': '5px',
                #             'border': '1px solid #dee2e6'
                #         })
                #     ]), True

                # else:
                #     if 'group_by' in arg_names:
                #         return html.Div([
                #             dbc.Row([
                #                 dbc.Col(fac.AntdText('Aggregate Column:', type='primary'), width="auto", align="center"),
                #                 dbc.Col(fac.AntdSelect(
                #                     id='attribute_key_dropdown_groupby', 
                #                     options=[{'label': col, 'value': col} for col in self.log.columns],
                #                     style={'width': '100%'}
                #                 ), width=2)
                #             ], className="mb-3"),
                #             dbc.Col(html.Div(id='groupby_options_container'))
                #         ]), html.Div([
                #         html.Pre(query_str, style={
                #             'whiteSpace': 'pre-wrap',
                #             'wordBreak': 'break-word',
                #             'backgroundColor': '#f8f9fa',
                #             'padding': '10px',
                #             'borderRadius': '5px',
                #             'border': '1px solid #dee2e6'
                #         })
                #     ]), True

                #         # return html.Div([
                #         # html.Label('Aggregate Column:'),
                #         # dcc.Dropdown(id='attribute-key-dropdown-groupby', 
                #         #             options=[{'label': col, 'value': col} for col in self.log.columns]),
                #         # html.Div(id='groupby-options-container')
                #         # ])
                    
                #     elif value == 'DurationWithin':
                #         self.attribute_key = None

                #         return html.Div([
                #             dbc.Row([
                #                 dbc.Col(fac.AntdText('Min Duration:', type='primary'), width="auto", align="center"),
                #                 dbc.Col(fac.AntdTimePicker(id='min_duration', placeholder='Enter a value', showNow= False , style={'width': '100%'}), width=2),
                #                 dbc.Col(fac.AntdText('Max Duration:', type='primary'), width="auto", align="center"),    
                #                 dbc.Col(fac.AntdTimePicker(id='max_duration', placeholder='Enter a value', showNow= False ,style={'width': '100%'}), width=2)])
                #         ]), html.Div([
                #         html.Pre(query_str, style={
                #             'whiteSpace': 'pre-wrap',
                #             'wordBreak': 'break-word',
                #             'backgroundColor': '#f8f9fa',
                #             'padding': '10px',
                #             'borderRadius': '5px',
                #             'border': '1px solid #dee2e6'
                #         })
                #     ]), True



        # # @callback to run the predicate for DurationWithin
        # @app.callback(
        #     # Output('predicate_output', 'children', allow_duplicate=True),
        #     Output('Query_display', 'children', allow_duplicate=True),
        #     Output('submit', 'disabled', allow_duplicate=True),
        #     [Input('qname', 'value'),
        #     Input('min_duration', 'value'),
        #     Input('max_duration', 'value')],
        #     prevent_initial_call=True
        # )
        # def update_duration_output(qname, min_duration, max_duration):
        #     if min_duration is None or max_duration is None:
        #         return []
        #     self.selections['min_duration'] = min_duration
        #     self.selections['max_duration'] = max_duration
        #     # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
        #     # table = dash_table.DataTable(
        #     #     columns=[{"name": i, "id": i} for i in result.columns],
        #     #     data=result.to_dict('records'),
        #     #     editable=False,
        #     #     filter_action="native",
        #     #     sort_action="native",
        #     #     sort_mode="multi",
        #     #     column_selectable="multi",
        #     #     row_selectable="multi",
        #     #     row_deletable=True,
        #     #     selected_columns=[],
        #     #     selected_rows=[],
        #     #     page_action="native",
        #     #     page_current=0,
        #     #     page_size=10,
        #     #     )
        #     query_str = f"Query('{qname}', {self.predicate}('{min_duration}', '{max_duration}'))"
        #     return html.Div([
        #             html.Pre(query_str, style={
        #                 'whiteSpace': 'pre-wrap',
        #                 'wordBreak': 'break-word',
        #                 'backgroundColor': '#f8f9fa',
        #                 'padding': '10px',
        #                 'borderRadius': '5px',
        #                 'border': '1px solid #dee2e6'
        #             })
        #         ]), False
        

        # # @callback to return the groupby options
        # @app.callback(
        #     Output('groupby_options_container', 'children'),
        #     Output('Query_display', 'children', allow_duplicate=True),  
        #     Input('attribute_key_dropdown_groupby', 'value'),
        #     prevent_initial_call=True
        # )
        # def update_groupby_options(selected_key):
        #     if selected_key is None:
        #         return []
        #     self.selections['attribute_key'] = selected_key

        #     query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', ''))"

        #     return html.Div([
        #         html.Label('Group By Values:'),
        #         dcc.Dropdown(id='groupby_options',
        #                     multi=True,
        #                     options=[{'label': col, 'value': col} for col in self.log.columns])
                            
        #     ]), html.Div([
        #             html.Pre(query_str, style={
        #                 'whiteSpace': 'pre-wrap',
        #                 'wordBreak': 'break-word',
        #                 'backgroundColor': '#f8f9fa',
        #                 'padding': '10px',
        #                 'borderRadius': '5px',
        #                 'border': '1px solid #dee2e6'
        #             })
        #         ])
        
        # # @callback to run the predicate for groupby
        # @app.callback(
        #     # Output('predicate_output', 'children', allow_duplicate=True),
        #     Output('Query_display', 'children', allow_duplicate=True),
        #     Output('submit', 'disabled', allow_duplicate=True),
        #     [Input('qname', 'value'),
        #     Input('groupby_options', 'value')],
        #     prevent_initial_call=True
        # )
        # def update_groupby_output(qname, selected_value):
        #     if selected_value is None:
        #         return []
        #     self.selections['values'] = selected_value
        #     # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
        #     # table = dash_table.DataTable(
        #     #     columns=[{"name": i, "id": i} for i in result.columns],
        #     #     data=result.to_dict('records'),
        #     #     editable=False,
        #     #     filter_action="native",
        #     #     sort_action="native",
        #     #     sort_mode="multi",
        #     #     column_selectable="multi",
        #     #     row_selectable="multi",
        #     #     row_deletable=True,
        #     #     selected_columns=[],
        #     #     selected_rows=[],
        #     #     page_action="native",
        #     #     page_current=0,
        #     #     page_size=10,
        #     #     )
        #     query_str = f"Query('{qname}', {self.predicate}('{self.attribute_key}', '{selected_value}'))"
        #     return html.Div([
        #             html.Pre(query_str, style={
        #                 'whiteSpace': 'pre-wrap',
        #                 'wordBreak': 'break-word',
        #                 'backgroundColor': '#f8f9fa',
        #                 'padding': '10px',
        #                 'borderRadius': '5px',
        #                 'border': '1px solid #dee2e6'
        #             })
        #         ]), False
        

        # # @callback to run the predicate for values
        # @app.callback(
        #     # Output('predicate_output', 'children', allow_duplicate=True),
        #     Output('Query_display', 'children', allow_duplicate=True),
        #     Output('submit', 'disabled', allow_duplicate=True),
        #     Input('values_dropdown', 'value'),
        #     prevent_initial_call=True
        # )
        # def update_values(selected_value):
        #     if selected_value is None:
        #         return html.Div("Please select a value from the dropdown.")
        #     else:
        #         self.selections['values'] = selected_value
                
        #         # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
        #         # table = dash_table.DataTable(
        #         #     columns=[{"name": i, "id": i} for i in result.columns],
        #         #     data=result.to_dict('records'),
        #         #     editable=False,
        #         #     filter_action="native",
        #         #     sort_action="native",
        #         #     sort_mode="multi",
        #         #     column_selectable="multi",
        #         #     row_selectable="multi",
        #         #     row_deletable=True,
        #         #     selected_columns=[],
        #         #     selected_rows=[],
        #         #     page_action="native",
        #         #     page_current=0,
        #         #     page_size=10,
        #         #     )
                
        #         # return table

        #         query_str = f"Query('{self.name}', {self.predicate}('', '{selected_value}'))"
        #         return html.Div([
        #             html.Pre(query_str, style={
        #                 'whiteSpace': 'pre-wrap',
        #                 'wordBreak': 'break-word',
        #                 'backgroundColor': '#f8f9fa',
        #                 'padding': '10px',
        #                 'borderRadius': '5px',
        #                 'border': '1px solid #dee2e6'
        #             })
        #         ]), False
            
        # @app.callback(
        #     # Output('predicate_output', 'children', allow_duplicate=True),
        #     Output('Query_display', 'children', allow_duplicate=True),
        #     Output('submit', 'disabled', allow_duplicate=True),
        #     Input('attribute_key_dropdown', 'value'),
        #     Input('value_input', 'value'),
        #     prevent_initial_call=True
        # )
        # def update_values(selected_key, selected_value):
        #     # if selected_value is None:
        #     #     return html.Div("Please select a value from the dropdown.")
        #     # else:
        #     try:
        #         converted_value = float(selected_value)
        #     except ValueError:
        #         return html.Div("Invalid value. Please enter a numeric value.")
    
        #     self.selections['values'] = converted_value
        #     self.selections['attribute_key'] = selected_key
        #     # self.selections['values'] = float(selected_value)
            
        #     # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
        #     # table = dash_table.DataTable(
        #     #     columns=[{"name": i, "id": i} for i in result.columns],
        #     #     data=result.to_dict('records'),
        #     #     editable=False,
        #     #     filter_action="native",
        #     #     sort_action="native",
        #     #     sort_mode="multi",
        #     #     column_selectable="multi",
        #     #     row_selectable="multi",
        #     #     row_deletable=True,
        #     #     selected_columns=[],
        #     #     selected_rows=[],
        #     #     page_action="native",
        #     #     page_current=0,
        #     #     page_size=10,
        #     #     )

        #     query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', '{selected_value}'))"
        #     return html.Div([
        #         html.Pre(query_str, style={
        #             'whiteSpace': 'pre-wrap',
        #             'wordBreak': 'break-word',
        #             'backgroundColor': '#f8f9fa',
        #             'padding': '10px',
        #             'borderRadius': '5px',
        #             'border': '1px solid #dee2e6'
        #         })
        #     ]), False
        
        #     # query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', '{selected_value}'))"
        #     # return table, html.Div([
        #     #     html.Pre(query_str, style={
        #     #         'whiteSpace': 'pre-wrap',
        #     #         'wordBreak': 'break-word',
        #     #         'backgroundColor': '#f8f9fa',
        #     #         'padding': '10px',
        #     #         'borderRadius': '5px',
        #     #         'border': '1px solid #dee2e6'
        #     #     })
        #     # ])

        # @callback to update the value options based on the selected attribute key
        
        # , html.Div([
        #         html.Pre(query_str, style={
        #             'whiteSpace': 'pre-wrap',
        #             'wordBreak': 'break-word',
        #             'backgroundColor': '#f8f9fa',
        #             'padding': '10px',
        #             'borderRadius': '5px',
        #             'border': '1px solid #dee2e6'
        #         })
        #     ])

        @app.callback(
            # Output('value_options_container', 'children'),
            Output({'type': 'value_options_container', 'index': MATCH}, "children"),
            # Output({'type': 'Query_display', 'index': MATCH}, "children", allow_duplicate=True),  # Match structure with `MATCH`
            # Output('Query_display', 'children', allow_duplicate=True),

            # Input('attribute_key_dropdown', 'value'),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            State({'type': 'radios', 'index': MATCH}, "id"),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        
        def update_value_options(selected_key, id):
            print(f"selected_key: {selected_key}")
            if selected_key is None:
                return []
            index = id['index']
            # self.selections['attribute_key'] = selected_key
            unique_values = self.df[selected_key].unique()
            print(f"unique_values: {unique_values}")
            # self.attribute_key = selected_key
            while len(self.attribute_key) <= index:
                self.attribute_key.append(None)
                
            # while len(self.selections['attribute_key']) <= index:    
            #     self.selections['attribute_key'].append(None)

            self.attribute_key[index] = selected_key
            # self.selections['attribute_key'][index] = selected_key
            query_str = f"Query('{self.name}', {self.predicate}('{selected_key}', ''))"

            return html.Div([
                dbc.Row([
                            dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdSelect(
                                # id='value_options', 
                                id={'type': 'value_options', 'index': index},
                                # options=[{'label': value, 'value': value} for value in unique_values],
                                options = [{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
                                mode='tags',
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3")
            ])


        @app.callback(
            # Output('predicate_output', 'children'),
            # Output('Query_display', 'children', allow_duplicate=True),
            Output('submit', 'disabled', allow_duplicate=True),
            # [Input('value_options', 'value', ALL)],
            [Input({'type': 'value_options', 'index': ALL}, "value")],
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )

        def update_value_multi(selected_value):
            print("in options multi:", selected_value)
            if selected_value is None:
                return []
            # self.selections['values'] = selected_value
            query_str = f"Query('{self.name}', {self.predicate}('{self.attribute_key}', '{selected_value}'))"
            return False
            
            # return html.Div([
            #     html.Pre(query_str, style={
            #         'whiteSpace': 'pre-wrap',
            #         'wordBreak': 'break-word',
            #         'backgroundColor': '#f8f9fa',
            #         'padding': '10px',
            #         'borderRadius': '5px',
            #         'border': '1px solid #dee2e6'
            #     })
            # ]), False
            return False
            # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)

            # if result is None or result.empty:
            #     return html.Div("No data available for the selected predicate.")
            
            # Convert the result to a Dash table
            # table = dash_table.DataTable(
            #     columns=[{"name": i, "id": i} for i in result.columns],
            #     data=result.to_dict('records'),
            #     editable=False,
            #     filter_action="native",
            #     sort_action="native",
            #     sort_mode="multi",
            #     column_selectable="multi",
            #     row_selectable="multi",
            #     row_deletable=True,
            #     selected_columns=[],
            #     selected_rows=[],
            #     page_action="native",
            #     page_current=0,
            #     page_size=10,
            #     )
            
            # return table




        @app.callback(
            Output("predicate_output", "children"),
            [Input("submit", "nClicks")],
        )
        def on_button_click(n):
            if n >= 1:
                print("in on_button_click:", self.selections, self.attribute_key, self.predicate)
                for key in self.selections:
                    print(f"Key: {key}, Value: {self.selections[key]}")


                # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
                result = VelPredicate.run_predicate(self.log_view, self.log, self.selections)


                if result is None or result.empty:
                    return html.Div("No data available for the selected predicate.")

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


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # app = dash.Dash(__name__)
    


    def Query_Builder(self):


        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        min_duration, max_duration = self.get_min_max_duration()


        app.layout = html.Div([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Name:', type='secondary'), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(
                                            # id='qname',
                                            id = {'type': 'qname', 'index': self.index},
                                            placeholder='Enter a value', size='middle'), 
                                            width=3)
                    ], className="mb-3"),

                html.Div(id='condition-container' , children=[
                    
                    html.Div(id='condition-0', children=[

                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Query Condition{self.index + 1}:', type='secondary'), width="auto", align="center"),
                            dbc.Col(
                                fac.AntdSpace(
                                    [
                                        fac.AntdRadioGroup(
                                            options=[
                                                {'label': f'{c}', 'value': c}
                                                for c in self.getPredicates()
                                            ],
                                            # id=f'radios{self.index + 1}',
                                            id = {'type': 'radios', 'index': self.index},
                                            optionType='button'
                                        )
                                    ],
                                    direction='horizontal'
                                )
                            )
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(html.Div(
                                # id='predicate_info',
                                id = {'type': 'predicate-info', 'index': self.index},
                                
                                ), width=12)
                        ]),

                        dbc.Row([
                            dbc.Col(html.Div(
                                id = {'type': 'Query_input', 'index': self.index }                                
                                ))
                        ], className="mb-3"),

                        
                    ])
                ]),
                    dbc.Row([
                            dbc.Col(
                                fac.AntdButton(
                                    'Add Condition', 
                                    id='add-condition-button', 
                                    type='primary', 
                                    nClicks=0,
                                    icon=fac.AntdIcon(icon = 'antd-plus-square-two-tone')
                                ), 
                                width="auto", align="center"
                            ),
                            dbc.Col(
                                fac.AntdButton(
                                    'Remove Condition', 
                                    id='remove-condition-button', 
                                    type='primary', 
                                    nClicks=0,
                                    icon=fac.AntdIcon(icon = 'antd-close-circle-two-tone')
                                ),
                                width="auto", align="center"
                            )
                        ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_display'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(html.Div(id='Query_output_button'))
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton('Generate Output', id='submit', disabled=False, type='primary', nClicks=0), width="auto", align="center"
                        )
                    ], className="mb-3"),

                    dbc.Spinner(
                        dbc.Row([
                            dbc.Col(
                                html.Div(id='predicate_output', style={'overflowX': 'auto'})
                            )
                        ], className="mb-3"), color="primary"),
                ]), className="mb-4", style={'padding': '20px', 'margin': '20px', 'backgroundColor': 'white', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 'borderRadius': '5px'}),

                dcc.Store(id='qname_index', data=self.index)

        ], style={'padding': '20px', 'margin': '20px'}, id="Query_container")


        # @callback to add a new condition
        @app.callback(
        Output('condition-container', 'children'),
        Input('add-condition-button', 'nClicks'),
        State('condition-container', 'children')
        )
        def add_condition(nClicks, children):
            print("out add condition")
            if nClicks > 0:
                print("in add condition")
                if children is None:
                    children = []

                new_index = len(children)
                self.index = new_index
                new_condition = html.Div(id=f'condition-{new_index}', children=[
                    dbc.Row([
                        dbc.Col(fac.AntdText(f'Query Condition {new_index + 1}:', type='secondary'), width="auto", align="center"),
                        dbc.Col(
                            fac.AntdSpace(
                                [
                                    fac.AntdRadioGroup(
                                        options=[
                                            {'label': f'{c}', 'value': c}
                                            for c in self.getPredicates()
                                        ],
                                        optionType='button',
                                        id={'type': 'radios', 'index': new_index }

                                    )
                                ],
                                direction='horizontal'
                            )
                        )
                    ], className="mb-3"),

                    dbc.Row([
                            dbc.Col(html.Div(
                                id={'type': 'predicate-info', 'index': new_index },
                                ), width=12)
                        ]),

                    dbc.Row([
                        dbc.Col(html.Div(
                            id={'type': 'Query_input', 'index': new_index }
                            ))
                    ], className="mb-3"),

                    dcc.Store(id='cond_id', data=new_index)

                        


                    ])
                children.append(new_condition)

            return children
        
        # @app.callback(
        #     Output("Query_display", "children"),
        #     [   
        #         Input("qname", "value"),
        #         Input({'type': 'attribute_key_dropdown', 'index': ALL}, "value"),
        #         Input({'type': 'value_input', 'index': ALL}, "value"),
        #         Input({'type': 'value_options', 'index': ALL}, "value")
        #     ],
        #     prevent_initial_call=True
        # )
        # def update_query_display(qname, attribute_keys, value_input, value_options):
        #     query_str = ""
        #     self.reset()
        #     self.selections['query_name'] = qname
        #     print("in update_query_display", attribute_keys, value_input, value_options)

        #     for idx, (key, val_opts) in enumerate(zip(attribute_keys, value_input, value_options)):
        #         print("in update_query_display1:", key, val_opts)
        #         if key or val_opts:
        #             predicate = self.predicate[idx]
        #             value =  val_opts or value_input[idx]
        #             print("in update_query_display2:", predicate, value)
        #             pred_class = self.get_predicate_class(predicate)
        #             self.selections['predicate_class'].append(pred_class)
        #             self.selections['predicate'].append(predicate)
        #             self.selections['attribute_key'].append(key)
        #             self.selections['values'].append(value)
        #             print("In update Selections:", self.selections)
        #             if query_str:
        #                 query_str += f",({predicate}('{key}', '{value}'))"
        #             else:
        #                 query_str = f"Query('{qname}', {predicate}('{key}', '{value}'))"
        #     print("Query String:", query_str)
        #     return html.Pre(query_str, style={
        #         'whiteSpace': 'pre-wrap',
        #         'wordBreak': 'break-word',
        #         'backgroundColor': '#f8f9fa',
        #         'padding': '10px',
        #         'borderRadius': '5px',
        #         'border': '1px solid #dee2e6'
        #     })


        @app.callback(
            # Output("predicate_info", "children"),
            # Input("radios", "value")
            Output({'type': 'predicate-info', 'index': MATCH}, "children"),
            Input({'type': 'radios', 'index': MATCH}, "value")
        )
        def update_predicate_info(value):
            print("VALUE:", value)
            if value is not None:
                descriptions = {
                    'EqToConstant': "Keeps cases that contain at least an event with the given attribute equal to a constant value.",
                    'NotEqToConstant': "Keeps cases that do not contain any event with the given attribute equal to a constant value.",
                    'GreaterEqualToConstant': "Keeps cases that contain at least an event with the given attribute greater than or equal to a constant value.",
                    'LessEqualToConstant': "Keeps cases that contain at least an event with the given attribute lower than or equal to a constant value.",
                    'GreaterThanConstant': "Keeps cases that contain at least an event with the given attribute greater than a constant value.",
                    'LessThanConstant': "Keeps cases that contain at least an event with the given attribute lower than a constant value.",
                    'StartWith': "Keeps cases starting with the specified activities.",
                    'EndWith': "Keeps cases ending with a given activity.",
                    'DurationWithin': "Keeps cases with durations within a specified range in seconds.",
                    'SumAggregate': "Sums the values of the specified attribute for the specified group of columns.",
                    'MaxAggregate': "Finds the maximum value of the specified attribute for the specified group of columns.",
                    'MinAggregate': "Finds the minimum value of the specified attribute for the specified group of columns."
                }
                
                icon_map = {
                    'EqToConstant': 'antd-carry-out',
                    'NotEqToConstant': 'antd-not-equal',
                    'GreaterEqualToConstant': 'antd-greater-than-equal',
                    'LessEqualToConstant': 'antd-less-than-equal',
                    'GreaterThanConstant': 'antd-greater-than',
                    'LessThanConstant': 'antd-less-than',
                    'StartWith': 'antd-play',
                    'EndWith': 'antd-stop',
                    'DurationWithin': 'antd-clock',
                    'SumAggregate': 'antd-sum',
                    'MaxAggregate': 'antd-arrow-up',
                    'MinAggregate': 'antd-arrow-down'
                }

                description = descriptions.get(value, "No description available.")
                icon_class = icon_map.get(value, 'antd-info-circle')

                return html.Div([
                    fac.AntdIcon(
                                id='icon',
                                icon='antd-info-circle-two-tone',
                                style={'marginRight': '10px'}
                            ),

                    # html.I(className='antd-carry-out', style={'marginRight': '10px'}),
                    description
                ], style={'color': 'gray', 'fontSize': '15px', 'display': 'flex', 'alignItems': 'center', 'paddingBottom': '20px'})
            return html.Div()

        @app.callback(
            Output({'type': 'Query_input', 'index': MATCH}, "children"),  # This uses MATCH
            Input({'type': 'radios', 'index': MATCH}, "value"),
            State({'type': 'radios', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            # State({'type': 'qname', 'index': ALL}, "id"),
            prevent_initial_call=True
        )


        def update_output(value, condition_id, query_index):
            
            print("in update_output", condition_id, query_index)

            if value is not None:
                print("Q Index: ", query_index)

                self.initialize_query(query_index)
                cond_index = condition_id['index']
                print("C Index: ", cond_index)
                self.update_condition(query_index, cond_index, 'predicate' , value)
                self.update_condition(query_index, cond_index, 'attribute_key' , None)
                self.update_condition(query_index, cond_index, 'values' , None)


                pred = self.get_predicate_class(value)

                self.update_condition(query_index, cond_index, 'predicate_class' , pred)

                print("Predicate: ", self.conditions)

                arg_names = VelPredicate.get_predicate_args(pred)

                if 'attribute_key' in arg_names and 'values' in arg_names:

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Attribute Key:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    id={'type': 'attribute_key_dropdown', 'index': cond_index},
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                                dbc.Col(html.Div(
                                    id={'type': 'value_options_container', 'index': cond_index}
                                    ))
                    ])


                
                elif 'attribute_key' in arg_names and ('value' in arg_names):
                    

                    return html.Div([
                        dbc.Row([
                                    dbc.Col(fac.AntdText('Attribute Key:', type='secondary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdSelect(
                                        id={'type': 'attribute_key_dropdown', 'index': cond_index},                             
                                        options=[{'label': col, 'value': col} for col in self.df.columns],
                                        style={'width': '100%'}
                                    ), width=2)
                                ], className="mb-3"),
                        dbc.Row([
                                    dbc.Col(fac.AntdText('Value:', type='secondary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdInput(
                                                        id={'type': 'value_input', 'index': cond_index},
                                                        placeholder='Enter a value', size='middle', style={'width': '100%'}), width=2)
                                ], className="mb-3"),
                        dcc.Store(id={'type':'value1', 'index': cond_index})
                    ])

                elif 'values' in arg_names and len(arg_names) == 1:

                    self.attribute_key = None
                    unique_values = self.df['Activity'].unique()

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    # id='values_dropdown',
                                    id={'type':'values_dropdown', 'index': cond_index}, 
                                    options=[{'label': value, 'value': value} for value in unique_values],
                                    mode='tags',
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                        dcc.Store(id={'type':'value2', 'index': cond_index})
                    ])

                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                            dbc.Row([
                                dbc.Col(fac.AntdText('Aggregate Column:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    # id='attribute_key_dropdown_groupby',
                                    id={'type': 'attribute_key_dropdown_groupby', 'index': cond_index}, 
                                    options=[{'label': col, 'value': col} for col in self.log.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                            dbc.Col(html.Div(id={'type': 'groupby_options_container', 'index': cond_index})),
                            dcc.Store(id={'type':'value4', 'index': cond_index})
                            
                        ])
                    
                    elif value == 'DurationWithin':
                        self.attribute_key = None

                        time_units = [
                            {'label': 'Years', 'value': 'Years'},
                            {'label': 'Months', 'value': 'Months'},
                            {'label': 'Days', 'value': 'Days'},
                            {'label': 'Hours', 'value': 'Hours'},
                            {'label': 'Minutes', 'value': 'Minutes'},
                        ]

                    return html.Div([
                        dbc.Row([
                            dbc.Col(fac.AntdText('Time Unit:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdSelect(
                                id={'type': 'time_unit_dropdown', 'index': cond_index},
                                options=time_units,
                                defaultValue='Hours',
                                style={'width': '100%'}
                            ), width=2),
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(fac.AntdText('Min Duration:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'min_duration', 'index': cond_index},
                                placeholder='Enter min duration', 
                                style={'width': '100%'}
                            ), width=2),
                            dbc.Col(fac.AntdText('Max Duration:', type='secondary'), width="auto", align="center"),    
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'max_duration', 'index': cond_index},
                                placeholder='Enter max duration', 
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(fac.AntdSlider(
                                id={'type': 'duration_range_slider', 'index': cond_index},
                                range=True,  
                                min=0,  
                                max=86400,  
                                step=3600,  
                                marks={i: f'{i//86400}d' for i in range(0, 86400 + 1, 86400)},  # Every day mark
                                value=[0, 86400],  # Initial slider range
                            ), width=12)
                        ]),
                        dcc.Store(id={'type':'value3', 'index': cond_index})
                    ])

                        
                    # return html.Div([
                    #     dbc.Row([
                    #         dbc.Col(fac.AntdText('Time Unit:', type='secondary'), width="auto", align="center"),
                    #         dbc.Col(fac.AntdSelect(
                    #             id={'type': 'time_unit_dropdown', 'index': cond_index},
                    #             options=time_units,
                    #             defaultValue='Years',
                    #             style={'width': '100%'}
                    #         ), width=2),
                    #     ], className="mb-3"),

                    #     dbc.Row([
                    #         dbc.Col(fac.AntdText('Min Duration:', type='secondary'), width="auto", align="center"),
                    #         dbc.Col(fac.AntdInputNumber(
                    #             id={'type': 'min_duration', 'index': cond_index},
                    #             placeholder='Enter min duration', 
                    #             style={'width': '100%'}
                    #         ), width=2),
                    #         dbc.Col(fac.AntdText('Max Duration:', type='secondary'), width="auto", align="center"),    
                    #         dbc.Col(fac.AntdInputNumber(
                    #             id={'type': 'max_duration', 'index': cond_index},
                    #             placeholder='Enter max duration', 
                    #             style={'width': '100%'}
                    #         ), width=2)
                    #     ], className="mb-3"),

                    #     dbc.Row([
                    #             dbc.Col(fac.AntdSlider(
                    #                 id={'type': 'duration_range_slider', 'index': cond_index},
                    #                 range=True,  
                    #                 min=0,  
                    #                 max=86400,  
                    #                 step=3600,  
                    #                 marks={i: f'{i//86400}d' for i in range(0, 86400 + 1, 86400)},  # Every day mark
                    #                 value=[0, 86400],  # Initial slider range
                    #             ), width=12)
                    #         ]),
                    #     dcc.Store(id={'type':'value3', 'index': cond_index})
                    # ])


        @app.callback(
            [
                Output({'type': 'min_duration', 'index': MATCH}, 'value'),
                Output({'type': 'max_duration', 'index': MATCH}, 'value'),
                Output({'type': 'duration_range_slider', 'index': MATCH}, 'value'),
                Output({'type': 'duration_range_slider', 'index': MATCH}, 'min'),
                Output({'type': 'duration_range_slider', 'index': MATCH}, 'max'),
                Output({'type': 'duration_range_slider', 'index': MATCH}, 'marks')
            ],
            [
                Input({'type': 'min_duration', 'index': MATCH}, 'value'),
                Input({'type': 'max_duration', 'index': MATCH}, 'value'),
                Input({'type': 'duration_range_slider', 'index': MATCH}, 'value'),
                Input({'type': 'time_unit_dropdown', 'index': MATCH}, 'value')
            ],
            prevent_initial_call=True
        )
        def sync_duration_inputs(min_duration, max_duration, slider_range, time_unit):
            ctx = dash.callback_context

            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            
            if time_unit == 'Minutes':
                max_duration_seconds= 60*60  
                step = 60  
            elif time_unit == 'Hours':
                max_duration_seconds= 24*3600  
                step = 3600  
            elif time_unit == 'Days':
                max_duration_seconds= 30*86400
                step = 86400  
            else:
                max_duration_seconds= 24*3600  
                step = 3600

            if 'duration_range_slider' in ctx.triggered[0]['prop_id']:
                min_duration_converted = slider_range[0]
                max_duration_converted = slider_range[1]
                return min_duration_converted, max_duration_converted, slider_range, 0, max_duration_seconds, {i: f'{i//step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

            elif 'min_duration' in ctx.triggered[0]['prop_id']:
                if max_duration is None or min_duration > max_duration:
                    max_duration = min_duration
                return min_duration, max_duration, [min_duration, max_duration], 0, max_duration_seconds, {i: f'{i//step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

            elif 'max_duration' in ctx.triggered[0]['prop_id']:
                if min_duration is None or max_duration < min_duration:
                    min_duration = max_duration
                return min_duration, max_duration, [min_duration, max_duration], 0, max_duration_seconds, {i: f'{i//step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

            return 0, max_duration_seconds, [0, max_duration_seconds], 0, max_duration_seconds, {i: f'{i//step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}



        # @app.callback(
        #     [
        #         Output({'type': 'min_duration', 'index': MATCH}, 'value'),
        #         Output({'type': 'max_duration', 'index': MATCH}, 'value'),
        #         Output({'type': 'duration_range_slider', 'index': MATCH}, 'value'),
        #         Output({'type': 'duration_range_slider', 'index': MATCH}, 'min'),
        #         Output({'type': 'duration_range_slider', 'index': MATCH}, 'max'),
        #         Output({'type': 'duration_range_slider', 'index': MATCH}, 'marks')
        #     ],
        #     [
        #         Input({'type': 'min_duration', 'index': MATCH}, 'value'),
        #         Input({'type': 'max_duration', 'index': MATCH}, 'value'),
        #         Input({'type': 'duration_range_slider', 'index': MATCH}, 'value'),
        #         Input({'type': 'time_unit_dropdown', 'index': MATCH}, 'value')
        #     ],
        #     prevent_initial_call=True
        # )
        # def sync_duration_inputs(min_duration, max_duration, slider_range, time_unit):
        #     ctx = dash.callback_context

        #     # Check if the callback was triggered correctly
        #     print(f"Triggered by: {ctx.triggered}")

        #     if not ctx.triggered:
        #         raise dash.exceptions.PreventUpdate

        #     # Convert the time unit to the corresponding multiplier in seconds
        #     time_unit_multiplier = {
        #         'Years': 31536000,
        #         'Months': 2592000,
        #         'Days': 86400,
        #         'Hours': 3600,
        #         'Minutes': 60
        #     }[time_unit]

        #     # Retrieve the dataset-specific min and max durations
        #     min_duration_seconds, max_duration_seconds = self.get_min_max_duration()

        #     if 'duration_range_slider' in ctx.triggered[0]['prop_id']:
        #         min_duration_converted = slider_range[0] * time_unit_multiplier
        #         max_duration_converted = slider_range[1] * time_unit_multiplier
        #         print(f"Slider: Min Duration: {min_duration_converted}, Max Duration: {max_duration_converted}")
        #         return min_duration_converted, max_duration_converted, slider_range, min_duration_seconds, max_duration_seconds, {i: f'{i//time_unit_multiplier}{time_unit[0].lower()}' for i in range(int(min_duration_seconds), int(max_duration_seconds) + 1, time_unit_multiplier)}

        #     elif 'min_duration' in ctx.triggered[0]['prop_id']:
        #         if max_duration is None or min_duration > max_duration:
        #             max_duration = min_duration
        #         print(f"Min Duration changed: Min: {min_duration}, Max: {max_duration}")
        #         return min_duration, max_duration, [min_duration, max_duration], min_duration_seconds, max_duration_seconds, {i: f'{i//time_unit_multiplier}{time_unit[0].lower()}' for i in range(int(min_duration_seconds), int(max_duration_seconds) + 1, time_unit_multiplier)}

        #     elif 'max_duration' in ctx.triggered[0]['prop_id']:
        #         if min_duration is None or max_duration < min_duration:
        #             min_duration = max_duration
        #         print(f"Max Duration changed: Min: {min_duration}, Max: {max_duration}")
        #         return min_duration, max_duration, [min_duration, max_duration], min_duration_seconds, max_duration_seconds, {i: f'{i//time_unit_multiplier}{time_unit[0].lower()}' for i in range(int(min_duration_seconds), int(max_duration_seconds) + 1, time_unit_multiplier)}

        #     # If 'time_unit' was triggered
        #     print(f"Time Unit changed: Min Duration: {min_duration_seconds}, Max Duration: {max_duration_seconds}")
        #     return min_duration_seconds, max_duration_seconds, [min_duration_seconds, max_duration_seconds], min_duration_seconds, max_duration_seconds, {i: f'{i//time_unit_multiplier}{time_unit[0].lower()}' for i in range(int(min_duration_seconds), int(max_duration_seconds) + 1, time_unit_multiplier)}

        @app.callback(
            Output({'type': 'value3', 'index': MATCH}, "data"),
            [
                Input({'type': 'min_duration', 'index': MATCH}, "value"),
                Input({'type': 'max_duration', 'index': MATCH}, "value"),
                Input({'type': 'time_unit_dropdown', 'index': MATCH}, 'value'),
                Input({'type': 'min_duration', 'index': MATCH}, 'id'),
                Input("qname_index", 'data'),
            ]
        )
        def update_duration_output(min_duration, max_duration, unit, cond_id, query_index):
            print(f"Update Duration Output: Min Duration: {min_duration}, Max Duration: {max_duration}, Unit: {unit}")

            if min_duration is None or max_duration is None:
                print("One of the durations is None, returning empty.")
                return []

            # Convert selected duration to seconds based on the selected unit
            time_unit_multiplier = {
                'Years': 31536000,
                'Months': 2592000,
                'Days': 86400,
                'Hours': 3600,
                'Minutes': 60
            }[unit]

            min_duration_sec = min_duration * time_unit_multiplier
            max_duration_sec = max_duration * time_unit_multiplier

            print(f"Converted Min Duration: {min_duration_sec}, Max Duration: {max_duration_sec}")

            # Update the conditions with the converted values
            self.update_condition(query_index, cond_id['index'], 'min_duration_seconds', min_duration_sec)
            self.update_condition(query_index, cond_id['index'], 'max_duration_seconds', max_duration_sec)

            return cond_id['index']




        # @callback to return the groupby options
        @app.callback(
            Output({'type': 'groupby_options_container', 'index': MATCH}, "children"),
            Input({'type': 'attribute_key_dropdown_groupby', 'index': MATCH}, "value"),
            Input({'type':'attribute_key_dropdown_groupby', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),

            prevent_initial_call=True
        )
        def update_groupby_options(selected_key, cond_id, query_index):
            if selected_key is None:
                return []
            
            self.update_condition(query_index, cond_id['index'], 'attribute_key' , selected_key)

            return html.Div([
                dbc.Row([
                    dbc.Col(fac.AntdText('Group By Values:', type='secondary'), width="auto", align="center"),
                    dbc.Col(fac.AntdSelect(
                        id={'type': 'groupby_options', 'index': cond_id['index']},
                        options=[{'label': col, 'value': col} for col in self.log.columns],
                        defaultValue='case:concept:name',
                        mode='tags',
                    ), width=2),
                    dbc.Col(id={'type': 'warning_message', 'index': cond_id['index']}, width='auto')

                ], className="mb-3")
            ])

        
        # @callback to run the predicate for groupby
        # @app.callback(
        #     Output({'type': 'value4', 'index': MATCH}, "data"),
        #     Input({'type': 'groupby_options', 'index': MATCH}, "value"),
        #     Input({'type': 'groupby_options', 'index': MATCH}, "id"),
        #     Input("qname_index", 'data')
        # )
        # def update_groupby_output(selected_value, cond_index, query_index):
        #     if selected_value is None:
        #         return []
        #     self.update_condition(query_index, cond_index['index'], 'values' , selected_value)
        #     return selected_value


        @app.callback(
            [
                Output({'type': 'value4', 'index': MATCH}, "data"),
                Output({'type': 'warning_message', 'index': MATCH}, "children"),
            ],
            [
                Input({'type': 'groupby_options', 'index': MATCH}, "value"),
                Input({'type': 'groupby_options', 'index': MATCH}, "id"),
                Input("qname_index", 'data')
            ]
        )
        def update_groupby_output(selected_value, cond_id, query_index):
            warning_message = ''
            if selected_value is None or 'case:concept:name' not in selected_value:
                warning_message = html.Div([
                    fac.AntdIcon(id ='warning-icon', icon ='antd-warning', style={"color": "red", "marginRight": "8px"}),
                    "Required field missing: 'case:concept:name'"
                ], style={"display": "flex", "alignItems": "center"})

            self.update_condition(query_index, cond_id['index'], 'values', selected_value)

            return selected_value, warning_message
        

        # @callback to run the predicate for values
        @app.callback(
            Output({'type': 'value2', 'index': MATCH}, "data"),
            Input({'type':'values_dropdown', 'index': MATCH}, "value"),
            Input({'type':'values_dropdown', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_values(selected_value, cond_id, query_index):
            if selected_value is None:
                return []
            else:
                self.update_condition(query_index, cond_id['index'], 'attribute_key' , None)
                self.update_condition(query_index, cond_id['index'], 'values' , selected_value)

            return selected_value   

            
            
        @app.callback(
            Output({'type': 'value1', 'index': MATCH}, "data"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            Input({'type': 'value_input', 'index': MATCH}, "value"),
            State({'type': 'value_input', 'index': MATCH}, "id"),
            Input("qname_index", 'data')
        )
        def update_values(selected_key, selected_value, cond_id, query_index):

            if selected_key is None:
                return []
            
            try:
                converted_value = float(selected_value)
            except ValueError:
                return html.Div("Invalid value. Please enter a numeric value.")
    

            self.update_condition(query_index, cond_id['index'], 'attribute_key' , selected_key)
            self.update_condition(query_index, cond_id['index'], 'values' , converted_value)

            return converted_value


        @app.callback(

            Output({'type': 'value_options_container', 'index': MATCH}, "children"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            State({'type': 'radios', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        
        def update_value_options(selected_key, cond_id, query_index):

            print("QINDEX: {qname_id}")

            cond_index = cond_id['index']

            if selected_key is None:
                return []

            self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)
            self.update_condition(query_index, cond_index, 'values' , None)

  
            unique_values = self.df[selected_key].unique()

            print("after attri", self.conditions)


            return html.Div([
                dbc.Row([
                            dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdSelect(
                                id={'type': 'value_options', 'index': cond_index},
                                options = [{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
                                mode='tags',
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3")
                        ,
                dcc.Store(id={'type': 'value_data', 'index': cond_index})
            ])

        @app.callback(
            # Output('submit', 'disabled', allow_duplicate=True),
            Output({'type': 'value_data', 'index': MATCH}, "data"),
            Input({'type': 'value_options', 'index': MATCH}, "value"),
            Input("qname_index", 'data'), 
            Input({'type': 'radios', 'index': MATCH}, "id"),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        def update_value_multi(selected_value, query_index, cond_id):
            if selected_value is None:
                return []
            
            self.update_condition(query_index, cond_id['index'], 'values' , selected_value)

            print("in options multi:", self.conditions)

            return False


        @app.callback(
            Output("predicate_output", "children"),
            [Input("submit", "nClicks"),
             Input("qname_index", "data")],
        )
        def on_button_click(n, query_index):
            if n >= 1:
                print("in on_button_click:", self.selections, self.attribute_key, self.predicate)
                for key in self.selections:
                    print(f"Key: {key}, Value: {self.selections[key]}")


                # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
                result = VelPredicate.run_predicate(self.log_view, self.log, self.conditions, f'Query{query_index + 1}')


                if result is None or result.empty:
                    return html.Div("No data available for the selected predicate.")

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


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # app = dash.Dash(__name__)
    

