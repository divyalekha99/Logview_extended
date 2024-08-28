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
import time
import webbrowser
from threading import Timer
import constants
import json


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
        # self.path = 'http://127.0.0.1:8051'
        # print("Dash App Running on: ", self.path)


    def initialize_query(self, index):
        query_key = f'Query{index + 1}'
        if query_key not in self.conditions:
            self.conditions[query_key] = {
                'query_name': '',
                'label': [],
                'source_log': '',
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

    def get_predicate_groupings(self):
        return [
            {"label": "Attribute-Based Filters", "options": [
                {"label": "Equals to Constant", "value": "EqToConstant"},
                {"label": "Not Equals to Constant", "value": "NotEqToConstant"}
            ]},
            {"label": "Threshold-Based Filters", "options": [
                {"label": "Greater or Equal to Constant", "value": "GreaterEqualToConstant"},
                {"label": "Less or Equal to Constant", "value": "LessEqualToConstant"},
                {"label": "Greater Than Constant", "value": "GreaterThanConstant"},
                {"label": "Less Than Constant", "value": "LessThanConstant"}
            ]},
            {"label": "Aggregate-Based Filters", "options": [
                {"label": "Sum of Values", "value": "SumAggregate"},
                {"label": "Maximum of Values", "value": "MaxAggregate"},
                {"label": "Minimum of Values", "value": "MinAggregate"}
            ]},
            {"label": "Event-Based Filters", "options": [
                {"label": "Starts with Specific Event", "value": "StartWith"},
                {"label": "Ends with Specific Event", "value": "EndWith"}
            ]},
            {"label": "Time-Based Filters", "options": [
                {"label": "Duration Within Specified Range", "value": "DurationWithin"}
            ]}
        ]
    
    # def get_all_source_logs(self):
    #     """
    #     Retrieve all unique source logs used in the evaluations.
    #     """
    #     source_logs = set()

    #     # Access the query registry from the LogView instance
    #     query_registry = self.log_view.query_registry
    #     print("Query Registry: ", query_registry)

    #     # Iterate over all registered evaluations
    #     for result_set_id in query_registry.get_registered_result_set_ids():
    #         evaluation = query_registry.get_evaluation(result_set_id)
    #         source_log_name = evaluation['source_log'].name
    #         source_logs.add(source_log_name)

    #     return list(source_logs)

    def get_available_logs(self):
        """
        Retrieves all available logs (initial source log, result sets, complements).
        """
        # Gather initial source log
        # available_logs = [self.log_view.query_registry.get_initial_source_log().name]
        
        # Add all result sets and their complements
        available_logs = list(self.log_view.result_set_name_cache.keys())
        
        return available_logs



    def generate_query_tab(self, index):
        self.initialize_query(index)

        # Tab content
        tab_content = html.Div([
            # Query Name Input
            dbc.Row([
                dbc.Col(fac.AntdText('Query Name:', className="font-weight-bold"), width="auto", align="center"),
                dbc.Col(fac.AntdInput(
                    id={'type': 'query_name', 'index': index},
                    placeholder='Enter a value', size='middle'),
                    width=2),
                dbc.Col(
                    fac.AntdSpace(
                        [   
                            fac.AntdTooltip(
                            fac.AntdText('Labels:', className="font-weight-bold"),
                            id = "tooltip-label",
                            title="Allows the user to assign a descriptive tag to a result set. ",  # Tooltip content
                            color="#1890ff",  
                            placement="top",  
                            # arrowPointAtCenter=True, 
                            ),
                            # Existing Labels Container
                            html.Div(id={'type': 'label-container', 'index': index},
                                     children=[],
                                    style={'display': 'inline-flex', 'flex-wrap': 'wrap', 'gap': '5px'}),

                            # Add Label Button
                            fac.AntdButton(
                                'Add Label',
                                icon=fac.AntdIcon(icon='antd-plus'),
                                type='dashed',
                                size='small',
                                nClicks=0,
                                id={'type': 'add-label-button', 'index': index},
                                style={'display': 'inline-flex', 'marginLeft': '10px'}
                            ),

                            # Label Input Container
                            html.Div(id={'type': 'label-input-container', 'index': index}, style={'display': 'inline-flex', 'marginLeft': '10px'}),
                            dcc.Store(id={'type': 'closecount-store', 'index': index}, data=[])

                        ],
                        direction='horizontal',
                        style={'width': '100%', 'align-items': 'center'}
                    ),
                    width=8, align='center'
                ),
            ], className="mb-3"),

            html.Div(id={'type': 'condition-container', 'index': index},
                    children=[html.Div([
                        # Query Condition Inputs
                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Condition {0 + 1}:', className="font-weight-bold"), width="auto", align="center"),
                            dbc.Col(fac.AntdRadioGroup(
                                options=[{'label': f'{c}', 'value': c} for c in self.getPredicates()],
                                id={'type': 'radios', 'index': f'{index}-{0}'},
                                optionType='button'
                            ), width=10),
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'predicate-info', 'index': f'{index}-{0}'}))
                        ], className="mb-3"),

                        # Additional Inputs for Each Condition
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{0}'}))
                        ], className="mb-3"),
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
            ], className="mb-3"),

            # Label Management Section

            dbc.Row([
                # dbc.Col(
                #     fac.AntdSpace(
                #         [   
                #             fac.AntdText('Labels:', className="font-weight-bold"),

                #             # Existing Labels Container
                #             html.Div(id={'type': 'label-container', 'index': index},
                #                      children=[],
                #                     style={'display': 'inline-flex', 'flex-wrap': 'wrap', 'gap': '5px'}),

                #             # Add Label Button
                #             fac.AntdButton(
                #                 'Add Label',
                #                 icon=fac.AntdIcon(icon='antd-plus'),
                #                 type='dashed',
                #                 size='small',
                #                 nClicks=0,
                #                 id={'type': 'add-label-button', 'index': index},
                #                 style={'display': 'inline-flex', 'marginLeft': '10px'}
                #             ),

                #             # Label Input Container
                #             html.Div(id={'type': 'label-input-container', 'index': index}, style={'display': 'inline-flex', 'marginLeft': '10px'})
                #         ],
                #         direction='horizontal',
                #         style={'width': '100%', 'align-items': 'center'}
                #     ),
                #     width=12
                # ),
            ], className="mb-3"),



            # Query Display Area
            dbc.Row([
                dbc.Col(html.Div(id={'type': 'Query_display', 'index': index})),
                dbc.Col(fac.AntdSelect(id={'type':'log_selector', 'index': index}, options=[{'label': log, 'value': log} for log in self.get_available_logs()],
                        placeholder="Select a log", size='middle', style={'width':'100%', 'height':'40px'}), width=2),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-play-fill", style={"marginRight": "8px"}),  # Bootstrap icon
                            "Run Query"
                        ],
                        id={'type': 'submit', 'index': index},
                        type='primary',
                        n_clicks=0,
                        className="btn-primary"),
                    width="auto", align="start"  # , style={'paddingBottom': '40px'}
                )
            ], className="mb-3", style={'marginTop': '50px'}),

            fac.AntdSkeleton(
                dbc.Row([
                    dbc.Col(
                        html.Div(id={'type': 'predicate_output', 'index': index}, style={'overflowX': 'auto'}))
                ], className="mb-3"),
                active=True,
                paragraph={'rows': 7, 'width': '50%'},
            ),

            # Hidden Store for Tracking Conditions
            dcc.Store(id={'type': 'condition-store', 'index': index}, data=0),
            dcc.Store(id={'type': 'qname-store', 'index': index}),
            dcc.Store(id={'type': 'label-store', 'index': index}, data=[]),
            
        ])

        # Return the tab item dictionary for AntdTabs
        return {
            'key': f'tab-{index}',
            'label': f'Query {index + 1}',
            'children': tab_content,
            'closable': True
        }

    def Query_Builder_v5(self):

        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
                "https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css"])
        
        app.layout = html.Div(
            style={
            'backgroundColor': '#bad2ea',
            'color': '#081621',
            'padding': '20px'
            },

            children=[
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            # Header
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
                                    # Spacer column to push the "Show Summary" button to the right
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
                                ], className="py-3 px-4 justify-content-between", style={'borderBottom': '3px solid #dae9f6'})
                            ]),

                            # Drawer for Summary
                            fac.AntdDrawer(
                                title="Summary Information",
                                id="summary-drawer",
                                placement="right",
                                visible=False,
                                width=500,
                                children=[
                                    html.Div(id="summary-content")
                                ]
                            ),

                            # AntdTabs for Queries
                            # fac.AntdTabs(
                            #     id="tabs",
                            #     # type="editable-card",  # Allows dynamic add/remove
                            #     children=[
                            #         self.generate_query_tab(0)
                            #     ],
                            #     defaultActiveKey='tab-0',
                            #     className="mb-4"
                            # ),

                            fac.AntdTabs(
                            id="tabs",
                            type="editable-card",
                            items=[
                                self.generate_query_tab(0)
                            ],
                            tabBarRightExtraContent = fac.AntdButton(
                                        "Add Query", 
                                        id='add-query-button', 
                                        nClicks=0,
                                        type="dashed", 
                                        icon=fac.AntdIcon(icon="antd-plus")
                                    ), 
                            defaultActiveKey='tab-0',
                            className="mb-4"
                            ),

                            


                            # Button to Add Queries
                            # dbc.Row([
                            #     dbc.Col(
                            #         fac.AntdButton(
                            #             "Add Query", 
                            #             id='add-query-button', 
                            #             nClicks=0,
                            #             type="dashed", 
                            #             icon=fac.AntdIcon(icon="antd-plus")
                            #         ), 
                            #         width=2, align='center'
                            #     ),
                            # ], className="button-group justify-content-center my-3"),
                            
                            dcc.Store(id='qname_index', data=0),
                        ], className="card-content")
                    ]), 
                    className="mb-4", 
                    style={'padding': '20px', 'margin': '20px', 'backgroundColor': 'white', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 'borderRadius': '25px', 'opacity': '0.9'}
                )
            ]
        )
        self.initialize_query(0)

        @app.callback(
            # Output('log-dropdown', 'options'),
            Output({'type': 'log_selector', 'index': MATCH}, 'options'),
            # Input({'type':'submit', 'index': MATCH}, 'n_clicks')
            Input({'type': 'predicate_output', 'index': MATCH}, "children"),
        )
        def update_log_dropdown(children):
            if children is not None:
                logs = self.get_available_logs()
                print("Available Logs:", logs)
                return [{'label': log_name, 'value': log_name} for log_name in logs]
            return dash.no_update

        @app.callback(
            Output('tabs', 'items', allow_duplicate=True),
            Output('tabs', 'defaultActiveKey', allow_duplicate=True),
            Input('add-query-button', 'nClicks'),
            State('tabs', 'items'),
            prevent_initial_call=True
        )
        def add_query_tab(nClicks, current_tabs):
            ctx = dash.callback_context

            # Avoid unnecessary processing if no clicks happened
            if not ctx.triggered or nClicks is None:
                raise dash.exceptions.PreventUpdate

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
            return active_index
        
        @app.callback(
            Output('tabs', 'items', allow_duplicate=True),
            Output('tabs', 'defaultActiveKey', allow_duplicate=True),
            Input('tabs', 'latestDeletePane'),
            State('tabs', 'items'),
            State('tabs', 'activeKey'),
            prevent_initial_call=True
        )
        def delete_query_tab(latestDeletePane, current_tabs, activeKey):
            if latestDeletePane is None:
                raise dash.exceptions.PreventUpdate
            
            updated_tabs = [tab for tab in current_tabs if tab['key'] != latestDeletePane]

            if latestDeletePane == activeKey:
                new_active_key = updated_tabs[0]['key'] if updated_tabs else None
            else:
                new_active_key = dash.no_update

            return updated_tabs, new_active_key



        @app.callback(
            [Output({'type': 'label-input-container', 'index': MATCH}, 'children', allow_duplicate=True),
            Output({'type': 'add-label-button', 'index': MATCH}, 'style', allow_duplicate=True)],
            Input({'type': 'add-label-button', 'index': MATCH}, 'nClicks'),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def display_label_input(nClicks, index):
            if nClicks > 0:
                return fac.AntdInput(
                    id={'type': 'label-input', 'index': index},
                    size='small',
                    style={'width': '200px'}
                ), {'display': 'none'}
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
                        print(f"Deleting label: {child['props']['content']} with ID: {child['props']['id']}")
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

            summary_data = VelPredicate.get_summary(self.log_view)

            evaluations = summary_data['evaluations']
            queries = summary_data['queries']

             
            timeline_items = [
                {
                    'content': fac.AntdCard(
                        title=f"Query: {row['query']}",
                        children=[
                            html.P(f"Source Log: {row['source_log']}", style={'margin': '2px 0'}),
                            html.P(f"Result Set: {row['result_set']}", style={'margin': '2px 0'}),
                            html.P(f"Labels: {row['labels']}", style={'margin': '2px 0'}),
                            html.P(f"Predicates: {queries.loc[queries['query'] == row['query'], 'predicates'].values[0]}", style={'margin': '2px 0'}),
                        ],
                        bordered=True,
                        style={'marginBottom': '10px', 'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.15)', 'borderRadius': '8px'},
                        bodyStyle={'padding': '10px'},
                        hoverable=True,
                    ),
                    'color': 'blue',   
                    'label': html.Span(f"# {index + 1}", style={'fontSize': '14px', 'color': 'black'})  # Using step numbers instead of query names
                }
                for index, row in evaluations.iterrows()
            ]

            # Build the AntdTimeline component
            timeline_content = fac.AntdTimeline(
                items=timeline_items,
                mode='alternate',   
                style={'paddingLeft': '20px', 'width':'100%'},   
                pending="Processing.."
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

            triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]

            if 'add-condition-button' in triggered_id:
                condition_count += 1

            if existing_conditions is None:
                existing_conditions = []

            existing_conditions.append(
                html.Div(
                    [
                        # Divider
                        # html.Hr(style={'borderTop': '2px solid #dae9f6', 'marginBottom': '20px'}),

                        dbc.Row([
                                dbc.Col(
                                    fac.AntdSwitch(
                                        checked=True,
                                        readOnly=True,
                                        checkedChildren="AND",
                                        unCheckedChildren="OR",
                                        className="my-auto",
                                        style={'marginBottom': '10px'}
                                    ),
                                    width=2, align="center"
                                )
                            ], style={'marginBottom': '30px'}),

                        # Query Condition Inputs
                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Condition {condition_count + 1}:', className="font-weight-bold"), width="auto", align="center"),
                            dbc.Col(fac.AntdRadioGroup(
                                options=[{'label': f'{c}', 'value': c} for c in self.getPredicates()],
                                id={'type': 'radios', 'index': f'{index}-{condition_count}'},
                                optionType='button'
                            ), width=8),
                           dbc.Col(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-trash3-fill", style={"marginRight": "8px"}), 
                                    ],
                                    id={'type': 'remove-condition-button', 'index': f'{index}-{condition_count}'}, 
                                    color='secondary',
                                    n_clicks=0,
                                    className='custom-trash-button'
                                    ),
                                    width="auto", align="start"
                            )
                            ], className="mb-3"),
                        
                        # Additional Inputs for Each Condition
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{condition_count}'}))
                        ], className="mb-3"),
                    ]
                )
            )
            
            return existing_conditions, condition_count



        @app.callback(
            Output({'type': 'condition-container', 'index': ALL}, 'children', allow_duplicate=True),
            Output({'type': 'condition-store', 'index': ALL}, 'data', allow_duplicate=True),
            Input({'type': 'remove-condition-button', 'index': ALL}, 'n_clicks'),
            State({'type': 'condition-container', 'index': ALL}, 'children'),
            State({'type': 'condition-store', 'index': ALL}, 'data'),
            prevent_initial_call=True
        )
        def remove_condition(n_clicks, all_conditions, condition_count):

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
            condition_index_to_remove = int(full_index.split('-')[-1])

            if 'remove-condition-button' in triggered_id['type'] and condition_count[0] >= 1:
                condition_count[0] -= 1

            updated_conditions = []
            for i, conditions in enumerate(all_conditions):
                if i == int(full_index.split('-')[0]):
                    # This is the container to update
                    if 0 <= condition_index_to_remove < len(conditions):
                        conditions.pop(condition_index_to_remove)
                updated_conditions.append(conditions)

            return updated_conditions, condition_count


        # @app.callback(
        #     Output('tabs', 'children'),
        #     Output('tabs', 'defaultActiveKey'),
        #     Input('add-query-button', 'nClicks'),
        #     State('tabs', 'children'),
        #     prevent_initial_call=True
        # )
        # def add_query_tab(nClicks, current_tabs):
        #     ctx = dash.callback_context

        #     # Avoid unnecessary processing if no clicks happened
        #     if not ctx.triggered or nClicks is None:
        #         raise dash.exceptions.PreventUpdate
     
        #     new_index = len(current_tabs)

        #     new_tab = self.generate_query_tab(new_index)

        #     current_tabs.append(new_tab)

        #     return current_tabs, f'tab-{new_index}'

        # @app.callback(
        #     Output('qname_index', 'data'),
        #     Input('tabs', 'activeKey'),
        #     prevent_initial_call=True
        # )
        # def update_query_index(active_tab_key):
        #     active_index = int(active_tab_key.split('-')[-1])
        #     return active_index
        



        @app.callback(
            Output({'type': 'predicate-info', 'index': MATCH}, "children"),
            Input({'type': 'radios', 'index': MATCH}, "value")
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

                    description
                ], style={'color': 'gray', 'fontSize': '15px', 'display': 'flex', 'alignItems': 'center', 'paddingBottom': '20px'}, className="font-weight-bold")
            return html.Div()

        @app.callback(
            Output({'type': 'Query_input', 'index': MATCH}, "children"),  # This uses MATCH
            Input({'type': 'radios', 'index': MATCH}, "value"),
            Input({'type': 'radios', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )


        def update_output(value, condition_id, query_index):
            

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
                                dbc.Col(fac.AntdText('Attribute Key:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    id={'type': 'attribute_key_dropdown', 'index': f'{query_index}-{cond_index}'},
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                                dbc.Col(html.Div(
                                    id={'type': 'value_options_container', 'index': f'{query_index}-{cond_index}'}
                                    ))
                    ])


                
                elif 'attribute_key' in arg_names and ('value' in arg_names):
                    
                    return html.Div([
                        dbc.Row([
                                    dbc.Col(fac.AntdText('Attribute Key:', type='secondary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdSelect(
                                        id={'type': 'attribute_key_dropdown', 'index': f'{query_index}-{cond_index}'},                             
                                        options=[{'label': col, 'value': col} for col in self.df.columns],
                                        style={'width': '100%'}
                                    ), width=2)
                                ], className="mb-3"),
                        dbc.Row([
                                    dbc.Col(fac.AntdText('Value:', type='secondary'), width="auto", align="center"),
                                    dbc.Col(fac.AntdInput(
                                                        id={'type': 'value_input', 'index': f'{query_index}-{cond_index}'},
                                                        placeholder='Enter a value', size='middle', style={'width': '100%'}), width=2)
                                ], className="mb-3"),
                        dcc.Store(id={'type':'value1', 'index': f'{query_index}-{cond_index}'})
                    ])

                elif 'values' in arg_names and len(arg_names) == 1:

                    unique_values = self.df['Activity'].unique()

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    id={'type':'values_dropdown', 'index': f'{query_index}-{cond_index}'}, 
                                    options=[{'label': value, 'value': value} for value in unique_values],
                                    mode='tags',
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                        # dcc.Store(id={'type':'value2', 'index': f'{query_index}-{cond_index}'})
                    ])

                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                            dbc.Row([
                                dbc.Col(fac.AntdText('Aggregate Column:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    # id='attribute_key_dropdown_groupby',
                                    id={'type': 'attribute_key_dropdown_groupby', 'index': f'{query_index}-{cond_index}'}, 
                                    options=[{'label': col, 'value': col} for col in self.log.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
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
                            dbc.Col(fac.AntdText('Time Unit:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdSelect(
                                id={'type': 'time_unit_dropdown', 'index': f'{query_index}-{cond_index}'},
                                options=time_units,
                                defaultValue='Hours',
                                style={'width': '100%'}
                            ), width=2),
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(fac.AntdText('Min Duration(seconds):', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'min_duration', 'index': f'{query_index}-{cond_index}'},
                                placeholder='Enter min duration', 
                                style={'width': '100%'}
                            ), width=2),
                            dbc.Col(fac.AntdText('Max Duration(seconds):', type='secondary'), width="auto", align="center"),    
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'max_duration', 'index': f'{query_index}-{cond_index}'},
                                placeholder='Enter max duration', 
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col(fac.AntdSlider(
                                id={'type': 'duration_range_slider', 'index': f'{query_index}-{cond_index}'},
                                range=True,  
                                min=0,  
                                max=86400,  
                                step=3600,  
                                marks={i: f'{i//86400}d' for i in range(0, 86400 + 1, 86400)},  # Every day mark
                                value=[0, 86400],
                            ), width=12)
                        ]),
                        dcc.Store(id={'type':'value3', 'index': f'{query_index}-{cond_index}'})
                    ])

        @app.callback(
            Output({'type': 'qname-store', 'index': MATCH}, 'data'),
            Input({'type': 'query_name', 'index': MATCH}, 'value'),
            State({'type': 'query_name', 'index': MATCH}, "id"),
        )

        def store_qname(qname, query_index):

            query_index = query_index['index']

            self.conditions[f'Query{query_index + 1}']['query_name'] = qname

            return qname


        @app.callback(
            Output({'type': 'Query_display', 'index': ALL}, 'children'),
            [
                Input({'type': 'attribute_key_dropdown', 'index': ALL}, 'value'),
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
                State({'type': 'value_input', 'index': ALL}, 'id'),
                State({'type': 'values_dropdown', 'index': ALL}, 'id'),
                State({'type': 'radios', 'index': ALL}, 'id'),
                State({'type': 'time_unit_dropdown', 'index': ALL}, 'id'),
                State({'type': 'min_duration', 'index': ALL}, 'id'),
                State({'type': 'max_duration', 'index': ALL}, 'id'),
                State({'type': 'groupby_options', 'index': ALL}, 'id'),
                State({'type': 'value_equality', 'index': ALL}, 'id'),
                State("qname_index", "data")
            ]
        )
        def update_query_display(attr_keys, value_inputs, values_list, predicates, time_units, min_durations, max_durations, group_by_values, value_equalities,
                                attr_key_ids, value_input_ids, values_dropdown_ids, predicate_ids, time_unit_ids, min_duration_ids, max_duration_ids, group_by_ids, value_equality_ids,
                                query_index):

            def filter_relevant_inputs(inputs, ids):
                return [
                    (input_value, comp_id) for input_value, comp_id in zip(inputs, ids)
                    if comp_id['index'].split('-')[0] == str(query_index)
                ]

            relevant_attr_keys = filter_relevant_inputs(attr_keys, attr_key_ids)
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
                    attribute_key = next((val for val, val_id in relevant_attr_keys if val_id['index'].split('-')[1] == str(cond_index)), None)
                    group_by = next((val for val, val_id in relevant_group_by_values if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate}('{attribute_key}', group_by={group_by})")

                elif predicate in ['EqToConstant', 'NotEqToConstant']:
                    attribute_key = next((val for val, val_id in relevant_attr_keys if val_id['index'].split('-')[1] == str(cond_index)), None)
                    value = next((val for val, val_id in relevant_value_equalities if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate}('{attribute_key}', '{value}')")

                elif predicate in ['GreaterEqualToConstant', 'LessEqualToConstant', 'GreaterThanConstant', 'LessThanConstant']:
                    attribute_key = next((val for val, val_id in relevant_attr_keys if val_id['index'].split('-')[1] == str(cond_index)), None)
                    value = next((val for val, val_id in relevant_value_inputs if val_id['index'].split('-')[1] == str(cond_index)), None)
                    condition_strs.append(f"{predicate}('{attribute_key}', '{value}')")

            if len(condition_strs) == 1:
                query_str += condition_strs[0]
            else:
                query_str += "[" + ", ".join(condition_strs) + "]"
            query_str += ")"

            num_outputs = len(dash.callback_context.outputs_list)

            outputs = [
                html.Pre(query_str, style={
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
                }) if i == query_index else dash.no_update
                for i in range(num_outputs)
            ]

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
                State("qname_index", 'data'),
            ]
        )
        def update_duration_output(min_duration, max_duration, unit, cond_id, query_index):
        
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


            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            self.update_condition(query_index, cond_index, 'min_duration_seconds', min_duration_sec)
            self.update_condition(query_index, cond_index, 'max_duration_seconds', max_duration_sec)

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
            if selected_key is None:
                return dash.no_update
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])
            self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)

            return html.Div([
                dbc.Row([
                    dbc.Col(fac.AntdText('Group By Values:', type='secondary'), width="auto", align="center"),
                    dbc.Col(fac.AntdSelect(
                        id={'type': 'groupby_options', 'index': cond_id['index']},
                        options=[{'label': col, 'value': col} for col in self.log.columns],
                        defaultValue='case:concept:name',
                        mode='tags',
                        style={'width': '100%'}
                    ), width=2),
                    dbc.Col(id={'type': 'warning_message', 'index': cond_id['index']}, width=2)

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
                State("qname_index", 'data')
            ]
        )
        def update_groupby_output(selected_value, cond_id, query_index):
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
            print("In start with values:", selected_value)
            if selected_value is None:
                return []
            
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])
            self.update_condition(query_index, cond_index, 'attribute_key' , None)
            self.update_condition(query_index, cond_index, 'values' , selected_value)
            print("In start with values updated:", self.conditions)
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
            
            if selected_value is None:
                return []
            
            try:

                cond_index_parts = cond_id['index'].split('-')
                cond_index = int(cond_index_parts[-1])
                print("converting value:", selected_value)
                converted_value = float(selected_value)

            except ValueError:
                return html.Div("Invalid value. Please enter a numeric value.")
    

            self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)
            self.update_condition(query_index, cond_index, 'values' , converted_value)

            return converted_value

        # @callback to run the predicate for values ETC, NETC

        @app.callback(
            Output({'type': 'value_options_container', 'index': MATCH}, "children"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
            Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_value_options(selected_key, cond_id, query_index):
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            if selected_key is None:
                return dash.no_update

            self.update_condition(query_index, cond_index, 'attribute_key', selected_key)
        
            unique_values = self.df[selected_key].unique()

            return html.Div([
                dbc.Row([
                    dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                    dbc.Col(fac.AntdSelect(
                        id={'type': 'value_equality', 'index': f'{query_index}-{cond_index}'},
                        options=[{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
                        # value=unique_values[0] if len(unique_values) > 0 else None, 
                        mode='tags',
                        style={'width': '100%'}
                    ), width=2)
                ], className="mb-3"),
            ])

        
        @app.callback(
            Output({'type': 'value_equality', 'index': MATCH}, "value"),
            Input({'type': 'value_equality', 'index': MATCH}, "value"),
            Input({'type': 'value_equality', 'index': MATCH}, "id"),
            State("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_value_multi(selected_value, cond_id, query_index):
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
        )
        def update_log_selector(selected_log, query_index):
            print("Selected log:", selected_log)
            self.conditions[f'Query{query_index + 1}']['source_log'] = selected_log
            return selected_log

        @app.callback(
            Output({'type': 'label-store', 'index': MATCH}, 'data'),
            Input({"type": "label-container", "index": MATCH}, "children"),
            State("qname_index", "data"),
        )
        def update_label_container(labels, query_index):
            print("Labels:", labels)

            tag_values = [child['props']['content'] for child in labels]

            print("Tag values:", tag_values)
            self.conditions[f'Query{query_index + 1}']['label'] = tag_values

            return tag_values



        @app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children"),
            [
                Input({"type": "submit", "index": ALL}, "n_clicks"),
                # Input({"type": "label-container", "index": ALL}, "children"),
                # Input({"type": "log_selector", "index": ALL}, "value"),
            ],
            State("qname_index", "data"),
            #  State({'type': 'query_name', 'index': ALL}, "value")],
            prevent_initial_call=True
        )
        def on_button_click(n_clicks, query_index):

            if n_clicks[0] is None:
                raise dash.exceptions.PreventUpdate

            
            # Initial loading state with the skeleton
            skeleton = fac.AntdSkeleton(
                loading=True,
                active=True,
                title=True,
                paragraph={'rows': 20}
            )

            # Show the skeleton while processing
            if n_clicks[0] > 0:
               
                # result = VelPredicate.run_predicate(self.log_view, self.log, self.conditions, f'Query{query_index + 1}')
                # VelPredicate.apply_label_to_result(self.log_view, result, label)
                result = VelPredicate.run_predicate(self.log_view, self.conditions, f'Query{query_index + 1}')

                # Once processing is done, hide the skeleton and show the table
                if result is None or result.empty:
                    return html.Div("No data available for the selected predicate.")
                
                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in result.columns],
                    data=result.to_dict('records'),
                    page_action="native",
                    page_current=0,
                    page_size=10,
                )

                return fac.AntdSkeleton(
                    loading=False,  # Hide skeleton, show table
                    active=True,
                    paragraph={'rows': 20},
                    children=[table]
                )

            return skeleton


        # @app.callback(
        #     # Output({'type': 'shadow-loading', 'index': MATCH}, 'style'),
        #     Output({'type': 'predicate_output', 'index': MATCH}, "children"),
        #     [
        #         Input({"type": "submit", "index": ALL}, "nClicks"),
        #         State("qname_index", "data")
        #     ],
        #     prevent_initial_call=True
        # )
        # def on_button_click(n, query_index):
        #     if n[0] >= 1:
        #         # Show shadow loading
        #         loading_style = {"display": "block"}
                
        #         # Simulate data processing
        #         time.sleep(3)  # Replace this with the actual `run_predicate` logic
                
        #         # Hide shadow loading and show results
        #         loading_style = {"display": "none"}
                
        #         # Real DataTable rendering
        #         result = VelPredicate.run_predicate(self.log_view, self.log, self.conditions, f'Query{query_index + 1}')
                
        #         if result is None or result.empty:
        #             return loading_style, html.Div("No data available for the selected predicate.")

        #         table = dash_table.DataTable(
        #             columns=[{"name": i, "id": i} for i in result.columns],
        #             data=result.to_dict('records'),
        #             page_action="native",
        #             page_current=0,
        #             page_size=10,
        #         )
                
        #         return loading_style, table

        #     return dash.no_update,
        #     # dash.no_update

        
        

        return app

    def open_browser(self, PORT):
        webbrowser.open("http://127.0.0.1:{}".format(PORT))

    def run_Query_Builder(self):
        print("Running Query Builder")
        app = self.Query_Builder_v5()
        if app is None:
            raise ValueError("App is None, there is an issue with the Query_Builder_v5 method.")
        print(f"App is ready to run at : http://127.0.0.1:{constants.QUERYPORT}")
        app.run_server(port=constants.QUERYPORT, open_browser=True, debug=True)

        
