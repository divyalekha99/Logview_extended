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

class Vel:
    def __init__(self, logName, fileType=".csv"):
        parent_dir = os.path.dirname(os.getcwd())
        # print(f"Parent Directory: {parent_dir}")
        self.logPath = os.path.join(parent_dir, "notebooks", "dataset", logName + fileType)
        self.CASE_ID_COL = 'Case ID'
        self.TIMESTAMP_COL = 'Complete Timestamp'
        self.ACTIVITY_COL = 'Activity'
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        self.initLogView()
        self.conditions = {}


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

    
    def changeDefaultNames(self, caseId, activity, timestamp):
        self.CASE_ID_COL = caseId
        self.ACTIVITY_COL = activity
        self.TIMESTAMP_COL = timestamp
    
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


    def setLog(self):
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        
        app.layout = html.Div([
            dash_table.DataTable(
                id='datatable-interactivity',
                columns=[
                    {"name": i, "id": i, "selectable": True} for i in self.log.columns
                ],
                data=self.log.head(100).to_dict('records'),
                page_size=10,  
                sort_action="native",  
                sort_mode="multi",  
                column_selectable="multi",  
                selected_columns=[],  
                style_table={'overflowX': 'auto'},  
            ),
            html.Button('Assign Roles to Selected Columns', id='assign-roles-button', n_clicks=0),
            dbc.Modal(
                [
                    dbc.ModalHeader("Assign Roles to Columns"),
                    dbc.ModalBody([
                        html.Div(id='role-assignment-container'),
                        html.Button('Confirm Assignment', id='confirm-assignment-button', n_clicks=0)
                    ]),
                    dbc.ModalFooter(
                        html.Button("Close", id="close", className="ml-auto")
                    ),
                ],
                id="modal",
                is_open=False,
            ),
            html.Div(id='update-status')
        ])

        
        @app.callback(
            Output("modal", "is_open"),
            Output("role-assignment-container", "children"),
            Input("assign-roles-button", "n_clicks"),
            State('datatable-interactivity', 'selected_columns'),
            State("modal", "is_open"),
        )
        def toggle_modal(n_clicks, selected_columns, is_open):
            if n_clicks > 0 and selected_columns:
                role_inputs = []
                role_labels = ["CASE_ID_COL", "ACTIVITY_COL", "TIMESTAMP_COL"]
                for i, col in enumerate(selected_columns[:3]):  
                    role_inputs.append(html.Div([
                        html.Label(f"Assign {role_labels[i]} to: {col}"),
                        dcc.Input(id=f'input-role-{i}', type='hidden', value=col),
                    ]))
                return not is_open, role_inputs
            return is_open, []

        # Callback to update column names based on confirmed assignment
        @app.callback(
            Output('update-status', 'children'),
            Input('confirm-assignment-button', 'n_clicks'),
            [State(f'input-role-{i}', 'value') for i in range(3)]
        )
        def update_column_names(n_clicks, case_id_col, activity_col, timestamp_col):
            if n_clicks > 0:
                self.changeDefaultNames(case_id_col, activity_col, timestamp_col)
                return f"Updated Columns: CASE_ID_COL: {case_id_col}, ACTIVITY_COL: {activity_col} , TIMESTAMP_COL: {timestamp_col}"
            return "No columns selected for update."

        return app


    
    def generate_query_tab(self, index):
        self.initialize_query(index)
        return fac.AntdTabPane(
        tab=f'Query {index + 1}',
        key=f'tab-{index}',
        children=[
            html.Div([
                # Query Name Input
                dbc.Row([
                    dbc.Col(fac.AntdText('Query Name:', className="font-weight-bold"), width="auto", align="center"),
                    dbc.Col(fac.AntdInput(
                        id = {'type': 'qname', 'index': index},
                        placeholder='Enter a value', size='middle'), 
                        width=2)
                    ], className="mb-3"),
                    
                # Query Conditions
                dbc.Row([
                    dbc.Col(fac.AntdText(f'Query Condition {index + 1}:', className="font-weight-bold"), width="auto", align="center"),
                    dbc.Col(
                        fac.AntdSpace(
                            [
                                fac.AntdRadioGroup(
                                    options=[
                                        {'label': f'{c}', 'value': c}
                                        for c in self.getPredicates()
                                    ],
                                    id = {'type': 'radios', 'index': index},
                                    optionType='button'
                                )
                            ],
                            direction='horizontal'
                        )
                    )
                ], className="mb-3"),
                
                # Predicate info
                dbc.Row([
                    dbc.Col(html.Div(
                        id = {'type': 'predicate-info', 'index': index},
                        
                        ), width=12)
                ]),
                # Additional Query Components (like Attribute Key, Values, etc.)
                dbc.Row([
                    dbc.Col(html.Div(id={'type': 'Query_input', 'index': index}))
                ], className="mb-3"),

                # Query Display Area
                dbc.Row([
                    dbc.Col(html.Div(id={'type': 'Query_display', 'index': index}))
                ], className="mb-3"),

                # Output Button
                dbc.Row([
                    dbc.Col(html.Div(id='Query_output_button'))
                ], className="mb-3"),
            ])
        ]
    )


    def Query_Builder_v4(self):

        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, './custom_styles.css', "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"])

        app.layout = html.Div(
                        style={
                            'fontFamily': "'Noto Sans', sans-serif",
                            'backgroundColor': '#bad2ea', 
                            # 'Plus Jakarta Sans', 
                            'color': '#081621',
                            'margin': '0',
                            'padding': '0',
                            'height': '100vh',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center'
                        },
                        children=[
                        dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                # Header
                                html.Header([
                                    dbc.Row([
                                        dbc.Col(
                                            dbc.Row([
                                                dbc.Col(
                                                    html.I(className="fa-solid fa-cubes", style={
                                                        'marginRight': '10px',
                                                        'fontSize': '26px',
                                                        'color': '#081621' 
                                                    }),
                                                ),
                                                dbc.Col(
                                                    html.H2("Query Builder", style={'fontWeight': 'bold', 'margin': '0', 'color': '#081621'}),
                                                    width="auto"
                                                )
                                            ], align="center"),
                                            width="auto"
                                        ),
                                        # dbc.Col(dbc.Button("Save Query", color="primary", className="ml-auto"), width="auto"),
                                    ], className="py-3 px-4", style={'borderBottom': '3px solid #dae9f6'}) # 'backgroundColor': '#f5f8fa'
                                ]),


                                # AntdTabs for Queries
                                fac.AntdTabs(
                                    id="tabs",
                                    children=[
                                        self.generate_query_tab(0)
                                    ],
                                    defaultActiveKey='tab-0',
                                    className="mb-4"
                                ),

                                # Buttons to Add/Remove Queries and Conditions
                                html.Div([
                                    dbc.Row([
                                        dbc.Col(dbc.Button("Add Query", id='add-query-button', n_clicks=0, color="primary"), width=2, align='center'),
                                    ], className="button-group justify-content-center my-3"),
                                ], className="px-4 py-3"),

                                dcc.Store(id='qname_index', data=0),
                            ], className="card-content")
                        ]), className="mb-4", style={'padding': '20px', 'margin': '20px', 'backgroundColor': 'white', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 'borderRadius': '30px', 'opacity': '0.9'})]
                    )
        self.initialize_query(0)
        
        @app.callback(
            Output('tabs', 'children'),
            Output('tabs', 'defaultActiveKey'),
            Input('add-query-button', 'n_clicks'),
            State('tabs', 'children'),
            prevent_initial_call=True
        )
        def add_query_tab(nClicks, current_tabs):
            new_index = len(current_tabs)

            new_tab = self.generate_query_tab(new_index)

            current_tabs.append(new_tab)

            return current_tabs, f'tab-{new_index}'

        @app.callback(
            Output('qname_index', 'data'),
            Input('tabs', 'activeKey'),
            prevent_initial_call=True
        )
        def update_query_index(active_tab_key):
            active_index = int(active_tab_key.split('-')[-1])
            print("Active Index: ", active_index)
            return active_index
        

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
                ], style={'color': 'gray', 'fontSize': '15px', 'display': 'flex', 'alignItems': 'center', 'paddingBottom': '20px'}, className="font-weight-bold")
            return html.Div()

        @app.callback(
            Output({'type': 'Query_input', 'index': MATCH}, "children"),  # This uses MATCH
            Input({'type': 'radios', 'index': MATCH}, "value"),
            State({'type': 'radios', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            prevent_initial_call=True
        )


        def update_output(value, condition_id, query_index):
            
            print("in update_output", condition_id, query_index)

            if value is not None:
                print("Q Index: ", query_index)

                # self.initialize_query(query_index)
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

        @app.callback(
            Output("Query_display", "children"),
            [
                Input({'type': 'qname', 'index': ALL}, "value"),
                Input({'type': 'attribute_key_dropdown', 'index': ALL}, "value"),
                Input({'type': 'value_input', 'index': ALL}, "value"),
                Input({'type': 'value_options', 'index': ALL}, "value"),
                Input("qname_index", "data"),  # Assuming you have a store or some method to track the current query index
            ],
            prevent_initial_call=True
        )
        def update_query_display(qnames, attribute_keys, value_inputs, value_options, query_index):
            
            query_str = ""

            self.initialize_query(query_index)

            qname = qnames[query_index] if qnames and len(qnames) > query_index else ""

            self.conditions[f'Query{query_index + 1}']['query_name'] = qname
            print(f"Query Name for Query{query_index + 1}: {qname}")
            print(f"attribute_keys: {attribute_keys}")
            print(f"value_inputs: {value_inputs}")
            print(f"value_options: {value_options}")

            for idx, (key, val_opts, val_input) in enumerate(zip(attribute_keys, value_options, value_inputs)):
                print(f"Processing condition {idx + 1} for Query{query_index + 1}")
                print(f"key: {key}, val_opts: {val_opts}, val_input: {val_input}")
                
                if key or val_opts or val_input:
                    condition = self.conditions[f'Query{query_index + 1}']['conditions'][idx]
                    predicate = condition['predicate']
                    pred_class = condition['predicate_class']
                    value = val_opts or val_input

                    print(f"Condition {idx + 1} for Query{query_index + 1}: Predicate: {predicate}, Key: {key}, Value: {value}")

                    if query_str:
                        query_str += f", ({predicate}('{key}', '{value}'))"
                    else:
                        query_str = f"Query('{qname}', {predicate}('{key}', '{value}'))"

            print("Final Query String:", query_str)

            return html.Pre(query_str, style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-word',
                'backgroundColor': '#f8f9fa',
                'padding': '10px',
                'borderRadius': '5px',
                'border': '1px solid #dee2e6'
            })


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


    def Query_Builder_v3(self):


        # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, './custom_styles.css'])

        # app.layout = html.Div([
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/Users/divyalekhas/Documents/Masters/Internship/logview/vel/custom_styles.css'])

        app.layout = html.Div(
                style={
                    'fontFamily': "'Plus Jakarta Sans', 'Noto Sans', sans-serif",
                    'backgroundColor': '#bad2ea',
                    'color': '#fbfcfd',
                    'margin': '70px',
                    'padding': '0',
                    'height': '100vh',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },

            children=[
                # Main Wrapper Div with background color and centering
                html.Div([
                    # Header
                    dbc.Row([
                        dbc.Col(html.H2("Query Builder", className="text-primary"), width="auto"),
                        dbc.Col(dbc.Button("Save Query", color="primary", className="ml-auto"), width="auto"),
                    ], className="py-3 border-bottom bg-light px-4"),

                    # Tabs for Queries
                    fac.AntdTabs([
                        fac.AntdTabPane(
                            tab='Query 1',
                            key='tab-0',
                            children=[
                                html.Div([
                                    # Query Name Input
                                    dbc.Row([
                                        dbc.Col(fac.AntdText('Query Name:', className="font-weight-bold"), width="auto", align="center"),
                                        dbc.Col(fac.AntdInput(
                                            id = {'type': 'qname', 'index': self.index},
                                            placeholder='Enter a value', size='middle'), 
                                            width=2)
                                        ], className="mb-3"),

                                    # Query Conditions
                                    dbc.Row([
                                        dbc.Col(fac.AntdText('Query Condition 1:', className="font-weight-bold"), width="auto", align="center"),
                                        dbc.Col(
                                            fac.AntdSpace(
                                                [
                                                    fac.AntdRadioGroup(
                                                        options=[
                                                            {'label': f'{c}', 'value': c}
                                                            for c in self.getPredicates()
                                                        ],
                                                        id = {'type': 'radios', 'index': 0},
                                                        optionType='button'
                                                    )
                                                ],
                                                direction='horizontal'
                                            )
                                        )
                                    ], className="mb-3"),
                                    
                                    # Predicate info
                                    dbc.Row([
                                        dbc.Col(html.Div(
                                            id = {'type': 'predicate-info', 'index': 0},
                                            
                                            ), width=12)
                                    ]),
                                    # Additional Query Components (like Attribute Key, Values, etc.)
                                    dbc.Row([
                                        dbc.Col(html.Div(id={'type': 'Query_input', 'index': 0}))
                                    ], className="mb-3"),

                                    # Query Display Area
                                    dbc.Row([
                                        dbc.Col(html.Div(id='Query_display'))
                                    ], className="mb-3"),

                                    # Output Button
                                    dbc.Row([
                                        dbc.Col(html.Div(id='Query_output_button'))
                                    ], className="mb-3"),

                                    # Spinner for Loading
                                    dbc.Spinner(
                                        dbc.Row([
                                            dbc.Col(html.Div(id='predicate_output', style={'overflowX': 'auto'}))
                                        ], className="mb-3"),
                                        color="primary"
                                    )
                                ], className="card")  # The card class for styling the background box
                            ]
                        )
                    ], defaultActiveKey='tab-0', className="mb-4"),


                    # Buttons to Add/Remove Queries and Conditions
                    html.Div([
                        dbc.Row([
                            dbc.Col(dbc.Button("Add Condition", id='add-condition-button', color="primary"), width=2, align='center'),
                            dbc.Col(dbc.Button("Remove Condition", id='remove-condition-button', color="secondary"), width=2, align='center'),
                            dbc.Col(dbc.Button("Add Query", id='add-query-button', color="primary", n_clicks=0), width=2, align='center'),
                        ], className="justify-content-center my-3"),

                        # Generate Output button
                        dbc.Row([
                            dbc.Col(dbc.Button("Generate Output", id='generate-output-button', color="primary"), width="auto", className="mx-auto"),
                        ], className="my-3 text-center"),
                    ], className="px-4 py-3"),

                    # Footer
                    html.Footer("2023 Query Builder Inc.", className="text-center py-4"),
                ], className="card-content")  # Centering and card-like background applied here
            ])


        @app.callback(
            [Output('tabs', 'children'),
            Output('tabs', 'value'),
            Output('query-store', 'data')],
            [Input('add-query-button', 'n_clicks')],
            [State('tabs', 'children'), State('query-store', 'data')]
        )
        def add_query(nClicks, tabs, data):
            if nClicks > 0:
                new_index = len(tabs)
                tab_value = f'tab-{new_index}'
                new_tab = dcc.Tab(label=f'Query {new_index + 1}', value=tab_value, children=[
                    html.Div(id=f'query-content-{new_index}')
                ])
                tabs.append(new_tab)
                data['queries'][tab_value] = {'conditions': []}
                return tabs, tab_value, data
            return tabs, 'tab-0', data


        # @app.callback(
        #     Output('confirm-dialog', 'displayed'),
        #     [Input({'type': 'tab-close-button', 'index': MATCH}, 'nClicks')]
        # )
        # def show_confirm_dialog(nClicks):
        #     if nClicks:
        #         return True
        #     return False

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
