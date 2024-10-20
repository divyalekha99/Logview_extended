from dash import jupyter_dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback, State, clientside_callback, no_update
import pandas as pd 
import pm4py
from logview.utils import LogViewBuilder
from logview.predicate import *
from vel.VelPredicate import VelPredicate
from vel import constants
from dash.exceptions import PreventUpdate
from dash.dependencies import MATCH, ALL
import dash_bootstrap_components as dbc
import os
import dash
import feffery_antd_components as fac
import time
import webbrowser
from threading import Timer
from functools import lru_cache
from flask import Flask
from redis import Redis
from io import StringIO
import warnings
from contextlib import redirect_stdout
import io


class Vel:


    def __init__(self, logName, fileType=".csv"):
        parent_dir = os.path.dirname(os.getcwd())
        self.logPath = os.path.join(parent_dir, "notebooks", "dataset", logName + fileType)
        self.CASE_ID_COL = 'Case ID'
        self.TIMESTAMP_COL = 'Complete Timestamp'
        self.ACTIVITY_COL = 'Activity'
        self.df = pd.read_csv(self.logPath)
        self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
        self.initLogView()
        self.conditions = {}
        self.num_cases = 0
        self.num_events = 0
        self.predicate_categories = {
                "Activity-Based": ["StartWith", "EndWith"],
                "Attribute-Based": ["EqToConstant =", "NotEqToConstant ≠"],
                "Time-Based": ["DurationWithin"],
                "Numerical-Based": ["LessThanConstant <", "GreaterThanConstant >", "LessEqualToConstant ≤", "GreaterEqualToConstant ≥"],
                "Aggregate-Based": ["MinAggregate", "MaxAggregate", "SumAggregate",  ],
            }
        self.query_tab_cache = {}
        self.tab_content_cache = {}
        self.condition_index_map = {}  



    def initialize_query(self, index):
        ''' 
        This function initializes the query based on the index.
        '''
        
        query_key = f'Query{index + 1}'
         
        if query_key not in self.conditions:
            self.conditions[query_key] = {
                'query_name': '',
                'label': [],
                'source_log': '',
                'conditions': []
            }
         

    def update_condition(self, index, condition_id, field, value):
        query_key = f'Query{index + 1}'
        if query_key in self.conditions:
            conditions = self.conditions[query_key]['conditions']
            if not any(cond['index'] == condition_id for cond in conditions):
                conditions.append({
                    'index': condition_id,
                    'predicate': None,
                    'predicate_class': None,
                    'attribute_key': None,
                    'values': None,
                    'min_duration_seconds': None,
                    'max_duration_seconds': None
                })
            for condition in conditions:
                if condition['index'] == condition_id:
                    condition[field] = value
                    break
        else:
            print(f"Query {index + 1} not found in conditions.")

             

    
    def changeDefaultNames(self, caseId, activity, timestamp):
        '''
        This function changes the default column names.
        '''

        self.CASE_ID_COL = caseId
        self.ACTIVITY_COL = activity
        self.TIMESTAMP_COL = timestamp
    
    def initLogView(self):
        '''
        This function initializes the log view.
        '''

        self.log = pm4py.format_dataframe(self.df, case_id=self.CASE_ID_COL, activity_key=self.ACTIVITY_COL, timestamp_key=self.TIMESTAMP_COL)
        self.log_view = LogViewBuilder.build_log_view(self.log)
        return self.log_view

   
    def get_predicate_class(self, predicate_name):
        '''
        This function returns the predicate class based on the predicate name.
        '''

        predicate_class_mapping = {
                "StartWith": StartWith,
                "EndWith": EndWith,
                "EqToConstant =": EqToConstant,
                "NotEqToConstant ≠": NotEqToConstant,
                "GreaterEqualToConstant ≥": GreaterEqualToConstant,
                "GreaterThanConstant >": GreaterThanConstant,
                "LessThanConstant <": LessThanConstant,
                "LessEqualToConstant ≤": LessEqualToConstant,
                "DurationWithin": DurationWithin,
                "SumAggregate": SumAggregate,
                "MaxAggregate": MaxAggregate,
                "MinAggregate": MinAggregate
            }
        if predicate_name in predicate_class_mapping:
            return predicate_class_mapping[predicate_name]
        else:
            raise ValueError(f"No class found for value: {predicate_name}")
          
    def run_set_log(self):
        '''
        This method runs the Set Log method.
        '''

         
        app = self.setLog()
        if app is None:
            raise ValueError("App is None, there is an issue with the setLog method.")
        

        app.run_server(mode='inline', port=constants.SETLOGPORT, debug=False)


    def setLog(self):
        '''
        This function sets up the log view UI.
        '''

        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        app.layout = html.Div([
            dash_table.DataTable(
                id='datatable-interactivity',
                columns=[
                    {"name": i, "id": i, "selectable": True} for i in self.log.columns
                ],
                data=self.log.head(50).to_dict('records'),
                page_size=15,  
                sort_action="native",  
                sort_mode="multi",  
                column_selectable="multi",  
                selected_columns=[],  
                style_table={'overflowX': 'auto', 'color': '#081621', 'fontSize': '14px'},  
            ),
            fac.AntdButton('Assign Roles to Selected Columns', id='assign-roles-button', nClicks=0),
            fac.AntdModal(
                id="modal",
                title="Assign Roles to Columns",
                renderFooter=True,
                okText="Confirm",
                cancelText="Cancel",
                okButtonProps={'type': 'primary'},
                children=[
                    html.Div(id='role-assignment-container'),
                ],
                locale='en-us',
            ),
            html.Div(id='update-status', style={'color': '#081621', 'fontFamily': 'Noto Sans, sans-serif'}, className="mt-3"),
            dcc.Store(id='stored-columns')  
        ])

        @callback(
            Output('datatable-interactivity', 'style_data_conditional'),
            Input('datatable-interactivity', 'selected_columns')
        )
        def update_styles(selected_columns):
            return [{
                'if': { 'column_id': i },
                'background_color': '#e6eaed'
            } for i in selected_columns]



        @app.callback(
            Output("modal", "visible", allow_duplicate=True),
            Output("role-assignment-container", "children"),
            Output('stored-columns', 'data'),
            Input("assign-roles-button", "nClicks"),
            State('datatable-interactivity', 'selected_columns'),
            State("modal", "visible"),
            prevent_initial_call=True
        )
        def toggle_modal(n_clicks, selected_columns, is_open):
            '''
            This function toggles the modal and displays the role assignment dropdowns.
            '''
            if n_clicks > 0 and selected_columns:
                role_inputs = []
                role_labels = ["CASE_ID_COL", "ACTIVITY_COL", "TIMESTAMP_COL"]

                for col in selected_columns:
                    dropdown = fac.AntdSelect(
                        options=[{"label": label, "value": label} for label in role_labels],
                        placeholder=f"Assign a role to {col}",
                        id={'type': 'role-dropdown', 'column': col},
                        style={'width': '100%'}
                    )
                    role_inputs.append(html.Div([html.Label(col), dropdown]))

                return not is_open, role_inputs, {}

            return is_open, [], {}

        @app.callback(
            Output('update-status', 'children'),
            Output("modal", "visible", allow_duplicate=True),
            Input('modal', 'okCounts'),
            State({'type': 'role-dropdown', 'column': ALL}, 'value'),
            State({'type': 'role-dropdown', 'column': ALL}, 'id'),
            prevent_initial_call=True
        )
        def update_column_names(okCounts, selected_roles, selected_columns):
            '''
            This function updates the default column names based on the selected roles.
            '''

            if okCounts > 0 and selected_roles:
                # Create a mapping of roles to their assigned columns
                column_map = {
                    "CASE_ID_COL": None,
                    "ACTIVITY_COL": None,
                    "TIMESTAMP_COL": None
                }

                for role, col in zip(selected_roles, selected_columns):
                    if role is not None:
                        column_map[role] = col['column']

                case_id_col = column_map["CASE_ID_COL"]
                activity_col = column_map["ACTIVITY_COL"]
                timestamp_col = column_map["TIMESTAMP_COL"]
                
                self.changeDefaultNames(case_id_col, activity_col, timestamp_col)
                
                # Return the updated columns in the status message
                return f"Updated Columns: CASE_ID_COL: {case_id_col}, ACTIVITY_COL: {activity_col}, TIMESTAMP_COL: {timestamp_col}", False
            
            return "No columns selected for update.", False

        @app.callback(
            Output("modal", "visible"),
            Input('modal', 'cancelCounts'),
            prevent_initial_call=True
        )
        def close_modal_on_cancel(cancelCounts):
            '''
            This function closes the modal when the cancel button is clicked.
            '''
            return False

        return app
    
    def get_available_logs(self):
        '''
        Retrieves all available logs (initial source log, result sets, complements).
        '''

        available_logs = list(self.log_view.result_set_name_cache.keys())
        
        return available_logs

    def generate_grouped_radio_options(self, predicate_categories):
        '''
        Generates grouped radio options for the predicate categories.
        '''

        predicate_descriptions = {
            'EqToConstant': "Keeps cases that contain at least an event with the given attribute equal to a constant value.",
            'NotEqToConstant': "Keeps cases that do not contain any event with the given attribute equal to a constant value.",
            'GreaterEqualToConstant ≥': "Keeps cases that contain at least an event with the given attribute greater than or equal to a constant value.",
            'GreaterThanConstant >': "Keeps cases that contain at least an event with the given attribute greater than a constant value.",
            'LessEqualToConstant ≤': "Keeps cases that contain at least an event with the given attribute lower than or equal to a constant value.",
            'LessThanConstant <': "Keeps cases that contain at least an event with the given attribute lower than a constant value.",
            'StartWith': "Keeps cases starting with the specified activities.",
            'EndWith': "Keeps cases ending with a given activity.",
            'DurationWithin': "Keeps cases with durations within a specified range in seconds.",
            'SumAggregate': "Sums the values of the specified attribute, grouping by the specified columns.",
            'MaxAggregate': "Finds the maximum value of the specified attribute, grouping by the specified columns.",
            'MinAggregate': "Finds the minimum value of the specified attribute, grouping by the specified columns."
        }

        options = []
        for category, predicates in predicate_categories.items():

            options.append({
                'label': fac.AntdText(category, strong=True),
                'value': f'{category}-header',
                'disabled': True,

            })

            for predicate in predicates:
                options.append({
                    'label': fac.AntdTooltip(
                        title=predicate_descriptions.get(predicate, "No description available."),
                        overlayStyle={
                            'padding': '2px',  
                            'fontSize': '15px',  
                            'color': '#2c3e50',  
                            'borderRadius': '10px',  
                            'boxShadow': '0px 6px 10px rgba(0, 0, 0, 0.12)',  
                            'textShadow': '0.5px 0.5px 2px rgba(0, 0, 0, 0.05)'  
                        },
                        children=fac.AntdText(predicate, style={'color': '#081621'})  
                    ),
                    'value': predicate
                })

        return options



    @lru_cache(maxsize=128)
    def generate_query_tab(self, index):
        '''
        This function generates a query tab for the AntdTabs component.
        '''

        self.initialize_query(index)

        radio_options = self.generate_grouped_radio_options(self.predicate_categories)

        # Tab content
        tab_content = html.Div([
            # Query Name Input
            dbc.Row([
                dbc.Col(fac.AntdText('Query Name:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                dbc.Col(fac.AntdInput(
                    id={'type': 'query_name', 'index': index},
                    placeholder='Enter a value', size='middle'),
                    width= 1, align='start', style={'paddingLeft': '0vw', 'width': '11vw'}),
                dbc.Col(
                    fac.AntdSpace(
                        [   
                            fac.AntdText('Labels:', className="font-weight-bold"),

                            # Existing Labels Container
                            html.Div(id={'type': 'label-container', 'index': index},
                                     children=[],
                                    style={'display': 'inline-flex', 'flex-wrap': 'wrap', 'gap': '5px', 'paddingRight': '2vw'}),

                            # Add Label Button
                            fac.AntdTooltip(
                            fac.AntdButton(
                                'Add Label',
                                icon=fac.AntdIcon(icon='antd-plus'),
                                type='dashed',
                                size='small',
                                nClicks=0,
                                id={'type': 'add-label-button', 'index': index},
                                style={'display': 'inline-flex', 'marginLeft': '10px'}
                            ),
                            id = "tooltip-label",
                            title="Assigns a descriptive tag to the result set. Different result sets can be tagged with the same label ",
                                placement="top",  
                                trigger="hover",
                                overlayStyle={
                                    'padding': '2px',  
                                    'fontSize': '15px',  
                                    'color': '#2c3e50',  
                                    'borderRadius': '10px',  
                                    'boxShadow': '0px 6px 10px rgba(0, 0, 0, 0.12)',   
                                    'textShadow': '0.5px 0.5px 2px rgba(0, 0, 0, 0.05)'  
                                },
                            ),
                            

                            # Label Input Container
                            html.Div(id={'type': 'label-input-container', 'index': index}, style={'display': 'inline-flex', 'marginLeft': '10px'}),
                            dcc.Store(id={'type': 'closecount-store', 'index': index}, data=[])

                        ],
                        direction='horizontal',
                        style={'width': '100%', 'align-items': 'center'}
                    ),
                    width=7, align='center',style={'paddingLeft': '7vw'},
                )
            ], className="mb-4 mt-4", align='center'),

            html.Div(id={'type': 'condition-container', 'index': index},
                    className="condition-container",
                    children=[html.Div([
                        # Query Condition Inputs
                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Condition {0 + 1}:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                            dbc.Col(
                                fac.AntdRadioGroup(
                                    options=radio_options,
                                    id={'type': 'radios', 'index': f'{index}-{0}'},
                                    optionType='button',
                                    buttonStyle='outline',
                                    className="equal-width-buttons custom-disabled-radio",
                                ),className='radio-group-container',
                                width=10, align='start' ,style={'paddingLeft': '0vw', 'width': '55vw'}
                            ),
                        
                        ], className="mb-4 mt-4"),

                        # Additional Inputs for Each Condition
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{0}'}))
                        ], className="mb-4 mt-4"),
                        dcc.Store(id='scroll-trigger'),
                    ])]),

            # Add/Remove Condition Buttons
            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-plus-square-fill", style={"marginRight": "8px"}),
                            'Add Condition',
                        ],
                        id={'type': 'add-condition-button', 'index': index},
                        color='primary',
                        n_clicks=0,
                    ),
                    width="auto", align="center"
                ),
            ], className="mb-4 mt-4"),


            # Query Display Area
            dbc.Row([
                dbc.Col(html.Div(id={'type': 'Query_display', 'index': index})),
                dbc.Col(fac.AntdSelect(id={'type':'log_selector', 'index': index},
                        autoSpin=True,
                        options=[{'label': log_name, 'value': log_name} for log_name in self.get_available_logs()],
                        placeholder="Select a log", size='middle', style={'width':'100%', 'height':'40px'}), width=2),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-play-fill", style={"marginRight": "8px"}),  
                            "Run Query"
                        ],
                        id={'type': 'submit', 'index': index},
                        type='primary',
                        n_clicks=0,
                        # disabled=True,
                        className="btn-primary"),
                    width="auto", align="start"  
                )
            ], className="mb-4 mt-4", style={'marginTop': '50px'}),

            fac.AntdSkeleton(
                    dbc.Row([
                        dbc.Col(
                                id={'type': 'predicate_output', 'index': index}, 
                                style={
                                    'overflowX': 'auto',
                                    'border': '2px dotted #d3d3d3', 
                                    'padding': '10px',
                                    'borderRadius': '5px',
                                    'minHeight': '15vh'
                                }
                        )
                    ], className="mb-4 mt-4"),
                    active=True,
                    paragraph={'rows': 7, 'width': '50%'},
            ),

            # Popup for Warnings with Icon
            fac.AntdPopupCard(
                id={'type': 'warning-popup', 'index': index},
                title=html.Span([
                    fac.AntdIcon(icon="antd-warning", style={'marginRight': '5px', 'marginLeft': '2px'}),  # Small icon
                    'Warning'
                ]),
                visible=False,
                children=[
                    fac.AntdParagraph(id={'type': 'warning-message', 'index': index})
                ]
            ),

            fac.AntdPopupCard(
                id={'type': 'warning-popup-ui', 'index': index},
                title=html.Span([
                    fac.AntdIcon(icon="antd-warning", style={'marginRight': '5px', 'marginLeft': '2px'}),  # Small icon
                    'Warning'
                ]),
                visible=False,
                children=[
                    fac.AntdParagraph(id={'type': 'warning-message-ui', 'index': index})
                ]
            ),

            
            # Hidden Store
            dcc.Store(id={'type': 'condition-store', 'index': index}, data=0),
            dcc.Store(id={'type': 'qname-store', 'index': index}),
            dcc.Store(id={'type': 'label-store', 'index': index}, data=[]),
            dcc.Store(id={'type': 'row-number-store', 'index': index}, data=10),
            dcc.Store(id={'type': 'query-result', 'index': index}),
            dcc.Store(id={'type': 'warning-state', 'index': index}, data=True),
            dcc.Store(id={'type': 'required-flag', 'index': index}, data=False),
            dcc.Store(id={'type': 'condition-id-counter', 'index': index}, data=0),

             

            
        ], style={'padding-inline': '7vw', 'maxHeight': '60vh'})

        # Return the tab item dictionary for AntdTabs
        return {
            'key': f'tab-{index}',
            'label': f'Query {index + 1}',
            'children': tab_content,
            'closable': True
        }

    def Query_Builder_v5(self):
        '''
        This function generates the Query Builder UI.
        '''

        server = Flask(__name__)
        redis_cache = Redis(host='localhost', port=6379, db=0)  


        app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP,"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
                "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css"])

        app.title = "Query Builder"

        app.layout= html.Div(
            className="app-container mb-4",
            style={
            },
            children=[
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            # Sticky Header
                            html.Header([
                                dbc.Row([
                                    # Left side content (Icon and Title)
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
                                            ),
                                        ], align="center"),
                                        width="auto"
                                    ),
                                    
                                    dbc.Col(),
                                    # Right side content (Show Summary button)
                                    dbc.Col(
                                        dbc.Button(
                                            [
                                            html.I(className="bi bi-clock-history", style={'marginRight': '5px'}),
                                            "Show Summary",
                                            ],
                                            id="open-drawer-button",
                                            color="primary",
                                            n_clicks=0,
                                            style={'marginLeft': 'auto'}
                                        ),
                                        width="auto", align="end"
                                    ),
                                ], className="py-3 px-4 justify-content-between", 
                                style={
                                    'borderBottom': '3px solid #dae9f6',
                                    'position': 'sticky',
                                    'top': '0',
                                    'zIndex': '1000',  
                                    'backgroundColor': 'white'
                                })
                            ]),

                            # Drawer for Summary
                            fac.AntdDrawer(
                                title="Query Summary",
                                id="summary-drawer",
                                placement="right",
                                visible=False,
                                width=500,
                                children=[
                                    html.Div(id="summary-content")
                                ]
                            ),
                            # AntdTabs for Queries
                            fac.AntdTabs(
                                id="tabs",
                                type="editable-card",
                                style={'paddingInline': '40px'},
                                items=[
                                    self.generate_query_tab(0)
                                ],
                                tabBarRightExtraContent=fac.AntdTooltip(
                                    title="Add Query",
                                    placement="top",
                                    trigger="hover",
                                    overlayStyle={
                                        'padding': '2px',
                                        'fontSize': '15px',
                                        'color': '#2c3e50',
                                        'borderRadius': '10px',
                                        'boxShadow': '0px 6px 10px rgba(0, 0, 0, 0.12)',
                                        'textShadow': '0.5px 0.5px 2px rgba(0, 0, 0, 0.05)'
                                    },
                                    children=fac.AntdIcon(
                                        id='add-query-button',
                                        icon='antd-plus-circle-two-tone',
                                        style={'fontSize': 20, 'cursor': 'pointer'},
                                    )
                                ),


                            defaultActiveKey='tab-0',
                            className="mb-4"
                            ),
                            

                           
                            dcc.Store(id='qname_index', data=0),
                            dcc.Store(id='reset', data=0),
                            dcc.Location(id='url', refresh=False),

                        ], className="card-content", style={})  
                    ]), 
                    className="mb-4 card-container", 
                    style={
                        
                    }
                )
            ]
        )
        
        # Callback for handling scroll to the last added condition
        @app.callback(
            Output('scroll-trigger', 'data'),
            Input({'type': 'add-condition-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
            prevent_initial_call=True
        )
        def trigger_scroll(n_clicks):
            '''
            This function triggers a scroll to the last added condition.
            '''

            if any(n_clicks) and sum(n_clicks) > 0:
                return "scroll"
            return dash.no_update


        @app.callback(
            Output({'type': 'log_selector', 'index': ALL}, 'options'),
            Input({'type': 'predicate_output', 'index': ALL}, 'children'),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_log_dropdown_on_interaction(query_result, qname_index):
            '''
            This function updates the log dropdown options based on the query result.
            '''

            logs = self.get_available_logs()
            options = [{'label': log_name, 'value': log_name} for log_name in logs]
            return [options for _ in query_result]


        @app.callback(
            [
                Output('tabs', 'items', allow_duplicate=True),
                Output('tabs', 'defaultActiveKey', allow_duplicate=True),
            ],
            Input('add-query-button', 'nClicks'),
            State('tabs', 'items'),
            prevent_initial_call=True
        )
        def add_query_tab(nClicks, current_tabs):
            '''
            This function adds a new query tab with a unique index after checking 
            for the maximum tab index to avoid duplication of indices.
            '''

            if nClicks is None:
                raise dash.exceptions.PreventUpdate

            if current_tabs:
                tab_indices = [int(tab['key'].split('-')[-1]) for tab in current_tabs]
                max_index = max(tab_indices)
            else:
                max_index = 0  

            new_index = max_index + 1

            new_tab = self.generate_query_tab(new_index)

            current_tabs.append(new_tab)

            return current_tabs, f'tab-{new_index}'

        
        @app.callback(
            Output('qname_index', 'data'),
            Input('tabs', 'activeKey'),
            prevent_initial_call=True
        )
        def update_query_index(active_tab_key):
            '''
            This function updates the query index based on the active tab.
            '''

            active_index = int(active_tab_key.split('-')[-1])
            
            cached_tab = self.query_tab_cache.get(active_index)
            if cached_tab:
                return active_index
            
            return active_index


        @app.callback(
            [Output('tabs', 'items', allow_duplicate=True),
            Output('tabs', 'activeKey', allow_duplicate=True)],
            [Input('tabs', 'latestDeletePane')],
            [State('tabs', 'items'), State('tabs', 'activeKey')],
            prevent_initial_call=True
        )
        def delete_query_tab(latestDeletePane, current_tabs, active_key):
            if latestDeletePane is None:
                raise dash.exceptions.PreventUpdate

            updated_tabs = [tab for tab in current_tabs if tab['key'] != latestDeletePane]

            new_active_key = updated_tabs[0]['key'] if active_key == latestDeletePane else dash.no_update

            query_key = f"Query{int(latestDeletePane.split('-')[1])+1}"  
             
            if query_key in self.conditions:
                del self.conditions[query_key]
                 

            return updated_tabs, new_active_key



        @app.callback(
            [Output({'type': 'label-input-container', 'index': MATCH}, 'children', allow_duplicate=True),
            Output({'type': 'add-label-button', 'index': MATCH}, 'style', allow_duplicate=True)],
            Input({'type': 'add-label-button', 'index': MATCH}, 'nClicks'),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def display_label_input(nClicks, index):
            '''
            This function displays the label input field when the 'Add Label' button is clicked.
            '''

            if nClicks > 0:
                return fac.AntdTooltip(
                        fac.AntdInput(
                        id={'type': 'label-input', 'index': index},
                        size='small',
                        style={'width': '200px'}
                        ),
                        id = "tooltip-label",
                        title="Press ENTER to add the label",
                        placement="top",  
                        trigger="hover",
                        overlayStyle={
                        'padding': '2px',  
                        'fontSize': '15px',  
                        'color': '#2c3e50',  
                        'borderRadius': '10px',  
                        'boxShadow': '0px 6px 10px rgba(0, 0, 0, 0.12)',  
                        'textShadow': '0.5px 0.5px 2px rgba(0, 0, 0, 0.05)'  
                        },
                        ),{'display': 'none'}

            return dash.no_update, dash.no_update


        @app.callback(
            [Output({'type': 'label-container', 'index': MATCH}, 'children', allow_duplicate=True),
            Output({'type': 'label-input-container', 'index': MATCH}, 'children', allow_duplicate=True),
            Output({'type': 'add-label-button', 'index': MATCH}, 'style', allow_duplicate=True)],
            Input({'type': 'label-input', 'index': MATCH}, 'nSubmit'),
            [State({'type': 'label-input', 'index': MATCH}, 'value'),
            State({'type': 'label-container', 'index': MATCH}, 'children')],
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def add_label(nSubmit, label_value, existing_labels, query_index):
            '''
            This function adds a label to the query.
            '''

            if label_value:
                label_id = len(existing_labels)  
                dcc.Store(id={'type': 'closecount-store', 'index': f"{query_index}-{label_id}"}, data=[]),
                new_label = fac.AntdTag(
                    content=label_value,
                    closeIcon=True,
                    color='blue',
                    id={'type': 'label', 'index': f"{query_index}-{label_id}"},
                    style={'font-size': '14px', 'display': 'flex', 'align-items': 'center'}
                )
                existing_labels.append(new_label)

                return existing_labels, [], {}
            
            return dash.no_update, dash.no_update, dash.no_update
        
        

        @app.callback(
            Output({'type': 'label-container', 'index': ALL}, 'children', allow_duplicate=True),
            Input({'type': 'label', 'index': ALL}, 'closeCounts'),
            State({'type': 'label-container', 'index': ALL}, 'children'),
            prevent_initial_call=True
        )
        def delete_label(closeCounts, existing_labels):
            '''
            This function deletes a label from the query.
            '''
           
            ctx = dash.callback_context
            triggered_id = ctx.triggered_id

            if not triggered_id:
                return dash.no_update
            
            triggered_close_counts = ctx.triggered[0]['value']

            
            if triggered_close_counts is None or triggered_close_counts <= 0:
                return dash.no_update  

            updated_label_lists = []


            for container_children in existing_labels:
                for i, child in enumerate(container_children):
                    
                    if 'id' in child['props'] and child['props']['id'] == triggered_id:
                         
                        container_children.pop(i)  
                        break  

                updated_label_lists.append(container_children)

            return updated_label_lists


        @app.callback(
            Output("summary-drawer", "visible"),
            Output("summary-content", "children"),
            Input("open-drawer-button", "n_clicks"),
            prevent_initial_call=True
        )
        def display_summary(nClicks):
            '''
            This function displays the query summary information.
            '''

            summary_data = VelPredicate.get_summary(self.log_view)

            evaluations = summary_data['evaluations']
            queries = summary_data['queries']
             
             

            timeline_items = []

            for index, row in evaluations.iterrows():
                query_value = row['query']

                  
                if index < len(queries):
                    predicate_value = queries.loc[index, 'predicates']
                else:
                    predicate_value = "No predicates found for this index."

                  
                timeline_item = {
                    'content': fac.AntdCard(
                        title=f"Query: {query_value if query_value else 'Unnamed Query'}",
                        children=[
                            dbc.Row([
                                dbc.Col("Source Log: ", style={'fontWeight': 'bold', 'display': 'inline'}, width=4, align='start'),
                                dbc.Col(row['source_log'], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px', 'width': '100%'}),
                            dbc.Row([
                                dbc.Col("Result Set: ", style={'fontWeight': 'bold', 'display': 'inline'}, width=4, align='start'),
                                dbc.Col(row['result_set'], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px', 'width': '100%'}),
                            dbc.Row([
                                dbc.Col("Labels: ", style={'fontWeight': 'bold', 'display': 'inline'}, width=4, align='start'),
                                dbc.Col(", ".join([lbl for sublist in row['labels'] for lbl in sublist]), style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px', 'width': '100%'}),
                            dbc.Row([
                                dbc.Col("Predicates: ", style={'fontWeight': 'bold', 'width': 'fit-content'}, width=3, align='start'),
                                dbc.Col(predicate_value, style={'padding':'0px', 'width':'14vw'}, width=9, align='start')
                            ], style={'marginBottom': '6px', 'width': '100%'})
                        ],
                        bordered=True,
                        style={
                            'marginBottom': '10px',
                            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.15)',
                            'borderRadius': '8px',
                            'backgroundColor': '#fafafa'
                        },
                        bodyStyle={'padding': '10px'},
                        hoverable=True,
                        headStyle={'backgroundColor': '#f0f2f5'}
                    ),
                    'color': 'blue',
                }

                timeline_items.append(timeline_item)

              
            timeline_content = fac.AntdSpace(
                [
                    fac.AntdTimeline(
                        items=timeline_items,
                        style={'paddingLeft': '20px', 'width': '100%'},
                        pending="Processing.."
                    )
                ],
                direction='vertical',
                align='start',
                style={'width': '100%'}
            )

            return True, timeline_content


        
        @app.callback(
            Output({'type': 'condition-container', 'index': MATCH}, 'children', allow_duplicate=True),
            Output({'type': 'condition-store', 'index': MATCH}, 'data', allow_duplicate=True),
            Input({'type': 'add-condition-button', 'index': MATCH}, 'n_clicks'),
            State({'type': 'condition-store', 'index': MATCH}, 'data'),
            State({'type': 'condition-container', 'index': MATCH}, 'children'),
            State('qname_index', 'data'),
            prevent_initial_call=True
        )
        def add_condition(add_clicks, condition_count, existing_conditions, index):
            '''
            This function adds a condition to the query.
            '''

            triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]


            if 'add-condition-button' in triggered_id:
                condition_count += 1
            else:
                raise dash.exceptions.PreventUpdate

            if existing_conditions is None:
                existing_conditions = []

            radio_options = self.generate_grouped_radio_options(self.predicate_categories)

            existing_conditions.append(
                html.Div(
                    [
                        dbc.Row([
                                dbc.Col(
                                    fac.AntdDivider(
                                        fac.AntdSpace(
                                            [
                                                fac.AntdTag(
                                                    content='AND',
                                                    bordered=True,
                                                    color='blue',
                                                )
                                                ],
                                                wrap=True,
                                            ), innerTextOrientation='center'),

                                        width=12, align="center"
                                )
                            ], 
                            ),

                        # Query Condition Inputs
                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Condition {condition_count + 1}:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                            dbc.Col(
                                fac.AntdRadioGroup(
                                    options=radio_options,
                                    id={'type': 'radios', 'index': f'{index}-{condition_count}'},
                                    optionType='button',
                                    buttonStyle='outline',
                                    className="equal-width-buttons custom-disabled-radio",
                                ),className='radio-group-container',
                                width=10, align='start' ,style={'paddingLeft': '0vw', 'width': '55vw'}
                            ),
                        dbc.Col(
                            fac.AntdTooltip(
                                fac.AntdIcon(
                                    id={'type': 'remove-condition-button', 'index': f'{index}-{condition_count}'},
                                    nClicks=0,
                                    icon='antd-delete-two-tone',
                                    style={'fontSize': 20, 'cursor': 'pointer'},
                                ),
                                id = "tooltip-label",
                                title="Delete Condition",
                                    placement="top",  
                                    trigger="hover",
                                    overlayStyle={
                                        'padding': '2px',  
                                        'fontSize': '15px',  
                                        'color': '#2c3e50',  
                                        'borderRadius': '10px',  
                                        'boxShadow': '0px 6px 10px rgba(0, 0, 0, 0.12)',  
                                        'textShadow': '0.5px 0.5px 2px rgba(0, 0, 0, 0.05)'  
                                    },
                            ),width="auto", align="start")

                            ], className="mb-4 mt-4"),
                        
                        # Additional Inputs for Each Condition
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{condition_count}'}))
                        ], className="mb-4 mt-4"),
                    ]
                )
            )

            query_key = f'Query{index + 1}'

            self.conditions[query_key]['conditions'].append({
                    'index': condition_count,
                    'predicate': None,
                    'predicate_class': None,
                    'attribute_key': None,
                    'values': None,
                    'min_duration_seconds': None,
                    'max_duration_seconds': None
                })

            self.condition_index_map[condition_count] = condition_count
            return existing_conditions, condition_count




        @app.callback(
            Output({'type': 'condition-container', 'index': ALL}, 'children', allow_duplicate=True),
            Output({'type': 'condition-store', 'index': ALL}, 'data', allow_duplicate=True),
            Input({'type': 'remove-condition-button', 'index': ALL}, 'nClicks'),
            State({'type': 'condition-container', 'index': ALL}, 'children'),
            State({'type': 'condition-store', 'index': ALL}, 'data'),
            prevent_initial_call=True
        )
        def remove_condition(n_clicks, all_conditions, condition_count):
            '''
            This function removes a condition from the query in both the UI and self.conditions.
            '''
            ctx = dash.callback_context
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            
            for i, clicks in enumerate(n_clicks):
                if clicks > 0:
                    triggered_index = i
                    break
            else:
                raise dash.exceptions.PreventUpdate

            triggered_prop_id = ctx.triggered[0]['prop_id']
            triggered_id = eval(triggered_prop_id.split('.')[0])


            full_index = triggered_id['index']
            query_index = int(full_index.split('-')[0])   
            condition_index_to_remove = int(full_index.split('-')[-1])   

             
            array_index = self.condition_index_map.get(condition_index_to_remove)

             
            if array_index is None:
                raise dash.exceptions.PreventUpdate

             
            if 'remove-condition-button' in triggered_id['type'] and condition_count[query_index] >= 1:
                condition_count[query_index] -= 1
            else:
                raise dash.exceptions.PreventUpdate

            updated_conditions = []
            for i, conditions in enumerate(all_conditions):
                if i == query_index:
                     
                    if array_index is not None and 0 <= array_index < len(conditions):
                        conditions.pop(array_index)
                        
                         
                        del self.condition_index_map[condition_index_to_remove]

                         
                        for old_condition_index in list(self.condition_index_map.keys()):
                            if self.condition_index_map[old_condition_index] > array_index:
                                self.condition_index_map[old_condition_index] -= 1   

                updated_conditions.append(conditions)

            query_key = f"Query{query_index + 1}"

            if query_key in self.conditions:
                 
                if array_index is not None and 0 <= array_index < len(self.conditions[query_key]['conditions']):
                    self.conditions[query_key]['conditions'].pop(array_index)

            return updated_conditions, condition_count


        @app.callback(
            Output({'type': 'Query_input', 'index': MATCH}, "children"),  
            Input({'type': 'radios', 'index': MATCH}, "value"),
            Input({'type': 'radios', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_output(value, condition_id, query_index):
            '''
            This function updates the input fields based on the selected predicate.
            '''

            if value is not None:

                cond_index_parts = condition_id['index'].split('-')
                cond_index = int(cond_index_parts[-1])  

                self.update_condition(query_index, cond_index, 'predicate' , value)
                self.update_condition(query_index, cond_index, 'attribute_key' , None)
                self.update_condition(query_index, cond_index, 'values' , None)


                pred = self.get_predicate_class(value)

                self.update_condition(query_index, cond_index, 'predicate_class' , pred)

                arg_names = VelPredicate.get_predicate_args(pred)


                if 'attribute_key' in arg_names and 'values' in arg_names:

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Attribute Key:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                                dbc.Col(fac.AntdSelect(
                                    id={'type': 'attribute_key_dropdown', 'index': f'{query_index}-{cond_index}'},
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'width': '11vw', 'paddingLeft': '0vw'}
                                ), width=1),
                                dbc.Col(width=1,style={'width': '10vw'}),
                                dbc.Col(
                                    id={'type': 'value_options_container1', 'index': f'{query_index}-{cond_index}'}, width=1, align="center"),
                                dbc.Col(
                                    id={'type': 'value_options_container2', 'index': f'{query_index}-{cond_index}'}, width=1)           
                            ], className="mb-1 mt-4", align="center"),
                    ])


                
                elif 'attribute_key' in arg_names and ('value' in arg_names):
                    
                    return html.Div([
                        dbc.Row([
                                    dbc.Col(fac.AntdText('Attribute Key:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                                    dbc.Col(fac.AntdSelect(
                                        id={'type': 'attribute_key_dropdown', 'index': f'{query_index}-{cond_index}'},                             
                                        options=[{'label': col, 'value': col} for col in self.df.columns],
                                        style={'width': '11vw', 'paddingLeft': '0vw'}
                                    ), width=1),
                                    dbc.Col(width=1,style={'width': '10vw'}),
                                    dbc.Col(fac.AntdText('Value:', className="font-weight-bold"), width=1, align="center", style={'width': '9vw'}),
                                    dbc.Col(fac.AntdInput(
                                                        id={'type': 'value_input', 'index': f'{query_index}-{cond_index}'},
                                                        placeholder='Enter a value', size='middle', style={'width': '11vw'}), width=1)
                                ], className="mb-1 mt-4"),
                        dcc.Store(id={'type':'value1', 'index': f'{query_index}-{cond_index}'})
                    ])

                elif 'values' in arg_names and len(arg_names) == 1:

                    unique_values = self.df['Activity'].unique()

                    tooltip_text = "Selecting multiple values will apply a logical OR operation. Any of the selected values will satisfy the condition."

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Values:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                                dbc.Col(
                                        fac.AntdTooltip(
                                            title=tooltip_text,
                                            placement="right",
                                            children=fac.AntdSelect(
                                                id={'type':'values_dropdown', 'index': f'{query_index}-{cond_index}'},
                                                options=[{'label': value, 'value': value} for value in unique_values],
                                                mode='tags',
                                                style={'width': '11vw', 'paddingLeft': '0vw'}
                                            )
                                        ),
                                        width=1
                                    ),
                            ], className="mb-1 mt-4"),
                    ])

                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                            dbc.Row([
                                dbc.Col(fac.AntdText('Aggregate Column:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                                dbc.Col(fac.AntdSelect(
                                    id={'type': 'attribute_key_dropdown_groupby', 'index': f'{query_index}-{cond_index}'}, 
                                    options=[{'label': col, 'value': col} for col in self.log.columns],
                                    style={'width': '11vw', 'paddingLeft': '0vw'}
                                ), width=1)
                            ], className="mb-4 mt-4"),
                            dbc.Col(width=1,style={'width': '10vw'}),
                            dbc.Col(html.Div(id={'type': 'groupby_options_container', 'index': f'{query_index}-{cond_index}'})),
                            dcc.Store(id={'type':'value4', 'index': f'{query_index}-{cond_index}'})
                            
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
                            dbc.Col(fac.AntdText('Time Unit:', className="font-weight-bold"), width=1, align="center"),
                            dbc.Col(fac.AntdSelect(
                                id={'type': 'time_unit_dropdown', 'index': f'{query_index}-{cond_index}'},
                                options=time_units,
                                defaultValue='Hours',
                                style={'width': '11vw', 'paddingLeft': '0vw'}
                            ), width=1),
                            dbc.Col(width=1,style={'width': '10vw'}),
                            dbc.Col(fac.AntdText('Min Duration(seconds):', className="font-weight-bold"), width="auto", align="center"),
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'min_duration', 'index': f'{query_index}-{cond_index}'},
                                placeholder='Enter min duration', 
                                style={'width': '11vw', 'paddingLeft': '0vw'}
                            ), width=1),
                            dbc.Col(width=1,style={'width': '10vw'}),
                            dbc.Col(fac.AntdText('Max Duration(seconds):', className="font-weight-bold"), width="auto", align="center"),    
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'max_duration', 'index': f'{query_index}-{cond_index}'},
                                placeholder='Enter max duration', 
                                style={'width': '11vw', 'paddingLeft': '0vw'}
                            ), width=1)
                        ], className="mb-4 mt-4"),


                        dbc.Row([
                            dbc.Col(fac.AntdSlider(
                                id={'type': 'duration_range_slider', 'index': f'{query_index}-{cond_index}'},
                                range=True,  
                                min=0,  
                                max=86400,  
                                step=3600,  
                                marks={i: f'{i//86400}d' for i in range(0, 86400 + 1, 86400)},  # Every day mark
                                value=[0, 86400],
                            ), width=12, align="center", style={'paddingLeft': '1vw', 'paddingRight': '1vw'})
                        ]),
                        dcc.Store(id={'type':'value3', 'index': f'{query_index}-{cond_index}'})
                    ])


        @app.callback(
            Output({'type': 'qname-store', 'index': MATCH}, 'data'),
            Input({'type': 'query_name', 'index': MATCH}, 'value'),
            State({'type': 'query_name', 'index': MATCH}, "id"),
            prevent_initial_call=True
        )

        def store_qname(qname, query_index):
            '''
            This function is responsible for storing the query name.
            '''

            query_index = query_index['index']
            if self.conditions.get(f'Query{query_index + 1}'):
                self.conditions[f'Query{query_index + 1}']['query_name'] = qname
            else:
                self.initialize_query(query_index)
                self.conditions[f'Query{query_index + 1}']['query_name'] = qname


            return qname


        @app.callback(
            Output({'type': 'Query_display', 'index': ALL}, 'children'),
            [
                Input({'type': 'attribute_key_dropdown', 'index': ALL}, 'value'),
                Input({'type': 'attribute_key_dropdown_groupby', 'index': ALL}, 'value'),
                Input({'type': 'value_input', 'index': ALL}, 'value'),
                Input({'type': 'values_dropdown', 'index': ALL}, 'value'),
                Input({'type': 'radios', 'index': ALL}, 'value'),
                Input({'type': 'time_unit_dropdown', 'index': ALL}, 'value'),
                Input({'type': 'min_duration', 'index': ALL}, 'value'),
                Input({'type': 'max_duration', 'index': ALL}, 'value'),
                Input({'type': 'groupby_options', 'index': ALL}, 'value'),
                Input({'type': 'value_equality', 'index': ALL}, 'value'),
            ],
            [   
                State({'type': 'attribute_key_dropdown', 'index': ALL}, 'id'),
                Input({'type': 'attribute_key_dropdown_groupby', 'index': ALL}, 'id'),
                State({'type': 'value_input', 'index': ALL}, 'id'),
                State({'type': 'values_dropdown', 'index': ALL}, 'id'),
                State({'type': 'radios', 'index': ALL}, 'id'),
                State({'type': 'time_unit_dropdown', 'index': ALL}, 'id'),
                State({'type': 'min_duration', 'index': ALL}, 'id'),
                State({'type': 'max_duration', 'index': ALL}, 'id'),
                State({'type': 'groupby_options', 'index': ALL}, 'id'),
                State({'type': 'value_equality', 'index': ALL}, 'id'),
                State("qname_index", "data")
            ],
            prevent_initial_call=True
        )
        def update_query_display(attr_keys, attr_keys_groupby , value_inputs, values_list, predicates, time_units, min_durations, max_durations, group_by_values, value_equalities,
                                attr_key_ids, attr_keys_groupby_ids, value_input_ids, values_dropdown_ids, predicate_ids, time_unit_ids, min_duration_ids, max_duration_ids, group_by_ids, value_equality_ids,
                                query_index):
            '''
            This function is responsible for updating the query display based on the user's input.
            '''

            def filter_relevant_inputs(inputs, ids):
                return [
                    (input_value, comp_id) for input_value, comp_id in zip(inputs, ids)
                    if comp_id['index'].split('-')[0] == str(query_index)
                ]

            # Ensure you are filtering based on the updated query_index after the tab deletion
            relevant_attr_keys = filter_relevant_inputs(attr_keys, attr_key_ids)
            relevant_attr_keys_groupby = filter_relevant_inputs(attr_keys_groupby, attr_keys_groupby_ids)
            relevant_value_inputs = filter_relevant_inputs(value_inputs, value_input_ids)
            relevant_values_list = filter_relevant_inputs(values_list, values_dropdown_ids)
            relevant_predicates = filter_relevant_inputs(predicates, predicate_ids)
            relevant_time_units = filter_relevant_inputs(time_units, time_unit_ids)
            relevant_min_durations = filter_relevant_inputs(min_durations, min_duration_ids)
            relevant_max_durations = filter_relevant_inputs(max_durations, max_duration_ids)
            relevant_group_by_values = filter_relevant_inputs(group_by_values, group_by_ids)
            relevant_value_equalities = filter_relevant_inputs(value_equalities, value_equality_ids)

            query_key = f'Query{query_index + 1}'
            query_data = self.conditions.get(query_key, {})
            query_name = query_data.get('query_name', '')

            query_str = f"Query('{query_name}', "
             
             

            condition_strs = []
            for i, (predicate, predicate_id) in enumerate(relevant_predicates):
                cond_index = int(predicate_id['index'].split('-')[1])  

                if predicate in ['StartWith', 'EndWith']:
                    values = next((val for val, val_id in relevant_values_list if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate}({values})")

                elif predicate == 'DurationWithin':
                    min_duration = next((val for val, val_id in relevant_min_durations if val_id['index'].split('-')[1] == str(cond_index)), None)
                    max_duration = next((val for val, val_id in relevant_max_durations if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"DurationWithin({min_duration}, {max_duration})")

                elif predicate in ['SumAggregate', 'MaxAggregate', 'MinAggregate']:
                    attribute_key = next((val for val, val_id in relevant_attr_keys_groupby if val_id['index'].split('-')[1] == str(cond_index)), None)
                    group_by = next((val for val, val_id in relevant_group_by_values if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate}('{attribute_key}', group_by={group_by})")

                elif predicate in ['EqToConstant =', 'NotEqToConstant ≠']:
                    attribute_key = next((val for val, val_id in relevant_attr_keys if val_id['index'].split('-')[1] == str(cond_index)), None)
                    value = next((val for val, val_id in relevant_value_equalities if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate.split()[0]}('{attribute_key}', '{value}')")
                     

                elif predicate in ['GreaterEqualToConstant ≥', 'LessEqualToConstant ≤', 'GreaterThanConstant >', 'LessThanConstant <']:
                    attribute_key = next((val for val, val_id in relevant_attr_keys if val_id['index'].split('-')[1] == str(cond_index)), None)
                    value = next((val for val, val_id in relevant_value_inputs if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate.split()[0]}('{attribute_key}', '{value}')")

            if len(condition_strs) == 1:
                query_str += condition_strs[0]
            else:
                query_str += "[" + ", ".join(condition_strs) + "]"
            query_str += ")"

            num_outputs = len(dash.callback_context.outputs_list)

            output_indices = [output['id']['index'] for output in dash.callback_context.outputs_list]
    
            outputs = []
            for i, output_index in enumerate(output_indices):
                if output_index == query_index:
                    output = html.Pre(query_str, style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-word',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '5px',
                        'border': '1px solid #dee2e6',
                        'fontSize': '14px',
                        'justifyContent': 'center',
                        'alignItems': 'center',
                        'height': '40px',
                        'textAlign': 'center',
                        'alignContent': 'center',
                    })
                    outputs.append(output)
                else:
                    outputs.append(dash.no_update)

            return outputs




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
            '''
            This callback synchronizes the duration inputs and the slider range.
            '''

            ctx = dash.callback_context

            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            # Conversion based on time units
            if time_unit == 'Minutes':
                max_duration_seconds = 60 * 60  # 1 hour max
                step = 60  # 1 minute
            elif time_unit == 'Hours':
                max_duration_seconds = 24 * 3600  
                step = 3600  
            elif time_unit == 'Days':
                max_duration_seconds = 30 * 86400  
                step = 86400  
            elif time_unit == 'Months':
                max_duration_seconds = 12 * 2592000  
                step = 2592000  
            elif time_unit == 'Years':
                max_duration_seconds = 24 * 31536000  
                step = 31536000  
            else:
                max_duration_seconds = 24 * 3600  
                step = 3600

            # Update the slider range based on the context
            if 'duration_range_slider' in ctx.triggered[0]['prop_id']:
                min_duration_converted = slider_range[0]
                max_duration_converted = slider_range[1]
                 

                return min_duration_converted, max_duration_converted, slider_range, 0, max_duration_seconds, {i: f'{i // step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

            elif 'min_duration' in ctx.triggered[0]['prop_id']:
                if max_duration is None or min_duration > max_duration:
                    max_duration = min_duration
                return min_duration, max_duration, [min_duration, max_duration], 0, max_duration_seconds, {i: f'{i // step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

            elif 'max_duration' in ctx.triggered[0]['prop_id']:
                if min_duration is None or max_duration < min_duration:
                    min_duration = max_duration
                return min_duration, max_duration, [min_duration, max_duration], 0, max_duration_seconds, {i: f'{i // step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}

             

            return 0, max_duration_seconds, [0, max_duration_seconds], 0, max_duration_seconds, {i: f'{i // step}{time_unit[0].lower()}' for i in range(0, max_duration_seconds + 1, step)}


        @app.callback(
            Output({'type': 'value3', 'index': MATCH}, "data"),
            [
                Input({'type': 'min_duration', 'index': MATCH}, "value"),
                Input({'type': 'max_duration', 'index': MATCH}, "value"),
                Input({'type': 'time_unit_dropdown', 'index': MATCH}, 'value'),
                Input({'type': 'min_duration', 'index': MATCH}, 'id'),
                State("qname_index", 'data'),
            ],
            prevent_initial_call=True
        )
        def update_duration_output(min_duration, max_duration, unit, cond_id, query_index):
            '''
            This callback updates the min and max duration values for the DurationWithin Predicate.
            '''
        
            if min_duration is None or max_duration is None:
                 
                return []


            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            self.update_condition(query_index, cond_index, 'min_duration_seconds', min_duration)
            self.update_condition(query_index, cond_index, 'max_duration_seconds', max_duration)

            return cond_index


        # @callback to return the groupby options
        @app.callback(
            Output({'type': 'groupby_options_container', 'index': MATCH}, "children"),
            Input({'type': 'attribute_key_dropdown_groupby', 'index': MATCH}, "value"),
            Input({'type':'attribute_key_dropdown_groupby', 'index': MATCH}, "id"),
            State("qname_index", 'data'),

            prevent_initial_call=True
        )
        def update_groupby_options(selected_key, cond_id, query_index):
            '''
            This callback updates the group by options for the selected attribute key for SumAggregate, MaxAggregate, MinAggregate Predicates.
            '''

            if selected_key is None:
                return dash.no_update
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])
            self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)

            return html.Div([
                dbc.Row([
                    dbc.Col(fac.AntdText('Group By Values:', className="font-weight-bold"), width=2, align="center", style={'width': '9vw'}),
                    dbc.Col(fac.AntdSelect(
                        id={'type': 'groupby_options', 'index': cond_id['index']},
                        options=[{'label': col, 'value': col} for col in self.log.columns],
                        defaultValue='case:concept:name',
                        mode='tags',
                        style={'width': '11vw', 'paddingLeft': '0vw'}
                    ), width=2),
                    dbc.Col(id={'type': 'warning_message', 'index': cond_id['index']}, width=3, align="center")

                ], className="mb-1 mt-4")
            ])

        @app.callback(
            [
                Output({'type': 'value4', 'index': MATCH}, "data"),
                Output({'type': 'warning_message', 'index': MATCH}, "children"),
            ],
            [
                Input({'type': 'groupby_options', 'index': MATCH}, "value"),
                Input({'type': 'groupby_options', 'index': MATCH}, "id"),
                State("qname_index", 'data')
            ],
            prevent_initial_call=True
        )
        def update_groupby_output(selected_value, cond_id, query_index):
            '''
            This callback updates the group by values for the selected attribute key for SumAggregate, MaxAggregate, MinAggregate Predicates.
            '''
            warning_message = ''
            if selected_value is None or 'case:concept:name' not in selected_value:
                warning_message = html.Div([
                    fac.AntdIcon(id ='warning-icon', icon ='antd-warning', style={"color": "red", "marginRight": "8px"}),
                    "Required field missing: 'case:concept:name'"
                ], style={"display": "flex", "alignItems": "center"})

            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])
            
            self.update_condition(query_index, cond_index, 'values', selected_value)

            return selected_value, warning_message
        

        # @callback to run the predicate for values
        @app.callback(
            Output({'type': 'values_dropdown', 'index': MATCH}, "value"),
            Input({'type':'values_dropdown', 'index': MATCH}, "value"),
            Input({'type':'values_dropdown', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call= True
        )
        def update_values(selected_value, cond_id, query_index):
            '''
            This callback updates the value for the selected values StartWith and EndWith Predicates.
            '''
            if selected_value is None:
                return []
            
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])
            self.update_condition(query_index, cond_index, 'attribute_key' , None)
            self.update_condition(query_index, cond_index, 'values' , selected_value)
            return selected_value   

            
        # @callback to run the predicate for values GTC, LTC, GTEC, LTEC    
        @app.callback(
            Output({'type': 'value1', 'index': MATCH}, "data"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            Input({'type': 'value_input', 'index': MATCH}, "value"),
            Input({'type': 'value_input', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_values(selected_key, selected_value, cond_id, query_index):
            '''
            This callback updates the value for the selected attribute key for GTC, LTC, GTEC, LTEC Predicates.
            '''

            if selected_value is None:
                return []
            
            try:

                cond_index_parts = cond_id['index'].split('-')
                cond_index = int(cond_index_parts[-1])
                converted_value = float(selected_value)

            except ValueError:
                return html.Div("Invalid value. Please enter a numeric value.")
    

            self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)
            self.update_condition(query_index, cond_index, 'values' , converted_value)

            return converted_value
        

        # @callback to run the predicate for values ETC, NETC
        @app.callback(
            Output({'type': 'value_options_container1', 'index': MATCH}, "children"),
            Output({'type': 'value_options_container2', 'index': MATCH}, "children"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_value_options(selected_key, cond_id, query_index):
            '''
            This callback updates the value options of the value field for the selected attribute key for EQ and NotEQ Predicates.
            '''

            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            if selected_key is None:
                return dash.no_update

            self.update_condition(query_index, cond_index, 'attribute_key', selected_key)
        
            unique_values = self.df[selected_key].unique()

            tooltip_text = (
                "Selecting multiple values will apply a logical OR operation. "
                "This means any of the selected values will satisfy the condition."
            )


            return fac.AntdText('Values:', className="font-weight-bold", style={'width':'9vw'}),fac.AntdTooltip(
                        title=tooltip_text,
                        placement="right",
                        children=fac.AntdSelect(
                            id={'type': 'value_equality', 'index': f'{query_index}-{cond_index}'},
                            options=[{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
                            mode='tags',
                            style={'width': '11vw', 'paddingLeft': '0vw'}
                        )
                )

        
        @app.callback(
            Output({'type': 'value_equality', 'index': MATCH}, "value"),
            Input({'type': 'value_equality', 'index': MATCH}, "value"),
            Input({'type': 'value_equality', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_value_multi(selected_value, cond_id, query_index):
            '''
            This callback updates the value for the selected values for EQ and NotEQ Predicates.
            '''
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            if selected_value is None:
                return dash.no_update  

            self.update_condition(query_index, cond_index, 'values', selected_value)

            return selected_value

        @app.callback(
            Output({'type':'log_selector', 'index': MATCH}, 'value'),
            Input({'type':'log_selector', 'index': MATCH}, 'value'),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        def update_log_selector(selected_log, query_index):
            '''
            This callback updates the log selector with the selected log.
            '''

            self.conditions[f'Query{query_index + 1}']['source_log'] = selected_log
            return selected_log

        @app.callback(
            Output({'type': 'label-store', 'index': MATCH}, 'data'),
            Input({"type": "label-container", "index": MATCH}, "children"),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        def update_label_container(labels, query_index):
            '''
            This callback updates the label container with the selected labels.
            '''

            tag_values = [child['props']['content'] for child in labels]

            self.conditions[f'Query{query_index + 1}']['label'] = tag_values

            return tag_values

        # Function to cache the full query result in Redis (done in the background)
        def cache_query_result(key, result):
            '''
            This function caches the query result in Redis.
            '''
            try:
                result_json = result.to_json(orient="split")
                redis_cache.set(key, result_json)
 
            except Exception as e:
                print(f"Error caching result: {e}")


        # Function to retrieve the cached result from Redis
        def get_cached_result(key):
            '''
            This function retrieves the cached result from Redis.
            '''

            try:
                cached_data = redis_cache.get(key)
                if cached_data:

                    cached_data = cached_data.decode('utf-8')
                    
                    result = pd.read_json(StringIO(cached_data), orient="split")
                    return result
                return None
            except Exception as e:
                print(f"Error retrieving cached result: {e}")
                return None

        # Function to capture both UserWarnings and runtime errors
        def capture_warnings_and_errors():
            '''
            This function captures both UserWarnings and runtime errors during query execution.
            '''

            warning_stream = io.StringIO()

            def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
                warning_stream.write(f"{category.__name__}: {message}\n")

            warnings.showwarning = custom_warning_handler
            return warning_stream


        # Callback for running the query with UserWarnings and runtime errors captured and displayed
        @app.callback(
            [
                Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
                Output({'type': 'warning-popup', 'index': MATCH}, "visible"),
                Output({'type': 'warning-message', 'index': MATCH}, "children"),
                Output({'type': 'warning-popup-ui', 'index': MATCH}, "visible"),
                Output({'type': 'warning-message-ui', 'index': MATCH}, "children"),
            ],
            Input({"type": "submit", "index": MATCH}, "n_clicks"),
            State("qname_index", "data"),
            State({'type': 'query_name', 'index': MATCH}, 'value'),
            State({'type': 'log_selector', 'index': MATCH}, 'value'),

            prevent_initial_call=True
        )
        def on_button_click(n_clicks, query_index, query_name, log_selector):
            '''
            This callback runs the query when the "Run Query" button is clicked.
            '''

            if n_clicks is None:
                raise dash.exceptions.PreventUpdate

            warning_message_ui = ''
            trigger = False

            # Validation: Check if required fields are missing
            query_name_missing = query_name is None or query_name.strip() == ""
            log_selector_missing = log_selector is None

            if query_name_missing and log_selector_missing:
                return no_update, True, "Query Name and Log Selector are required!", False, "",
            elif query_name_missing:
                return no_update, True, "Query Name is required!", False, "",
            elif log_selector_missing:
                return no_update, True, "Log Selector is required!", False, ""


            if n_clicks > 0:

                start_time = time.time()
                query_key = f'Query{query_index + 1}'

                # Capture UserWarnings and runtime errors during query execution
                warning_stream = capture_warnings_and_errors()

                try:

                    key = query_key+query_name


                    result, self.num_cases, self.num_events = VelPredicate.run_predicate(self.log_view, self.conditions, query_key, 10)
                    if result is None or result.empty:
                        return html.Div("No data available for the selected filters."), False, "", False, "",

                       
                    cache_query_result(key, result)

                    table = dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in result.columns],
                        data=result.head(10).to_dict('records'),
                        page_size=10,
                        page_action='none',
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'}
                    )

                    shape_info = html.Div([
                        html.Span(f"Number of Cases: {self.num_cases}", style={'fontWeight': 'bold', 'marginRight': '20px'}),
                        html.Span(f"Number of Events: {self.num_events}", style={'fontWeight': 'bold'})
                    ], style={'marginBottom': '10px'})

                    load_more_options = html.Div([
                        dbc.Button("Load Next 10 Rows", id={'type': 'load-next-rows-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                        dbc.Button("Load Full Table", id={'type': 'load-full-table-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                    ], style={'marginTop': '10px', 'display': 'flex', 'justifyContent': 'flex-end'})


                except Exception as e:
                    # Capture any runtime errors and display them in the warning message
                    warning_message_ui = f"Error: {str(e)}"
                    trigger = True
                    return html.Div(), True, warning_message_ui, True, warning_message_ui

                # Process captured warnings
                warning_message_ui = warning_stream.getvalue().strip()
                if warning_message_ui:
                    trigger, warn = True, warning_message_ui
                else:
                    trigger, warn = False, ""

                return html.Div([shape_info, table, load_more_options]), False, "", trigger, warn

            return html.Div(), False, "", False, ""


        # Callback for "Load Next 10 Rows" functionality
        @app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
            Input({'type': 'load-next-rows-button', 'index': MATCH}, 'n_clicks'),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        def load_next_10_rows(nClicks, query_index):
            '''
            This callback loads the next 10 rows when the "Load Next 10 Rows" button is clicked.
            '''

            if nClicks > 0:
                query_key = f'Query{query_index + 1}'

                # Calculate the number of rows to display based on click count
                new_row_number = max(10, 10 * (nClicks + 1))
                 

                result, self.num_cases, self.num_events = VelPredicate.run_predicate(self.log_view, self.conditions, query_key, new_row_number)

                if result is None or result.empty:
                    return html.Div[("No data available for the selected filters.")]

                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in result.columns],
                    data=result[:new_row_number].to_dict('records'),
                    page_size=10,
                    page_action='native',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'}
                )

                shape_info = html.Div([
                    html.Span(f"Number of Cases: {self.num_cases}", style={'fontWeight': 'bold', 'marginRight': '20px'}),
                    html.Span(f"Number of Events: {self.num_events}", style={'fontWeight': 'bold'})
                ], style={'marginBottom': '10px'})

                load_more_options = html.Div([
                    dbc.Button("Load Next 10 Rows", id={'type': 'load-next-rows-button', 'index': query_index}, n_clicks= nClicks, style={'marginRight': '10px'}),
                    dbc.Button("Load Full Table", id={'type': 'load-full-table-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                ], style={'marginTop': '10px','display': 'flex', 'justifyContent': 'flex-end'})

                return html.Div([shape_info, table, load_more_options])

            return dash.no_update
        
        # Load full table
        @app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
            Input({'type': 'load-full-table-button', 'index': MATCH}, 'n_clicks'),
            State("qname_index", "data"),
            State({'type': 'query_name', 'index': MATCH}, 'value'),
            prevent_initial_call=True
        )
        def load_full_table(n_clicks, query_index, query_name):
            '''
            This callback loads the full table when the "Load Full Table" button is clicked.
            '''

            if n_clicks > 0:

                query_key = f'Query{query_index + 1}'
                key = query_key+query_name

                result, self.num_cases, self.num_events = VelPredicate.run_predicate(self.log_view, self.conditions, query_key, 0)

                if result is None or result.empty:
                    return html.Div[("No data available for the selected filters.")]

                cache_query_result(key, result)

                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in result.columns],
                    data= result.to_dict('records'),
                    page_size=10,  
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    page_action='native'  
                )

                shape_info = html.Div([
                    html.Span(f"Number of Cases: {self.num_cases}", style={'fontWeight': 'bold', 'marginRight': '20px'}),
                    html.Span(f"Number of Events: {self.num_events}", style={'fontWeight': 'bold'})
                ], style={'marginBottom': '10px'})

                return html.Div([shape_info, table])

            return dash.no_update

                
    
        return app

    def open_browser(self, PORT):
        '''
        This method opens the default web browser to the Query Builder application.
        '''

        webbrowser.open_new("http://127.0.0.1:{}".format(PORT))

    def flush_redis_on_start(self):
        '''
        This method flushes the Redis cache on startup.
        '''

        try:
            r = Redis(host='localhost', port=6379, db=0)
            r.flushall()  
            print("Redis cache cleared on startup.")
        except Exception as e:
            print(f"Error flushing Redis cache: {e}")

    def run_Query_Builder(self):
        '''
        This method runs the Query Builder application.
        '''

        print("Running Query Builder")
        self.flush_redis_on_start()
        
        self.conditions = {}
        self.initialize_query(0)
         
        app = self.Query_Builder_v5()
        if app is None:
            raise ValueError("App is None, there is an issue with the Query_Builder method.")
        
        PORT = constants.QUERYPORT
        print(f"App is ready to run at: http://127.0.0.1:{PORT}")

        Timer(1, self.open_browser, args=[PORT]).start()

        # Run the Dash app
        app.run_server(port=PORT, debug=False)
