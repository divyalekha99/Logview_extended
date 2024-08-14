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
        self.predicate= ""
        self.attribute_key = ""
        self.selections = {
                    'predicate': None,
                    'attribute_key': None,
                    'values': None,
                    'min_duration': None,
                    'max_duration': None,
                }
        self.initLogView()
        self.index = 0
        self.query = ''
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
    
    

    def create_query_section(self, query_index):
        # result = html.Div([])
        result = html.Div(
            id={'type': 'query-section', 'index': query_index},
            style={'border': '1px solid black', 'padding': '10px', 'marginTop': '10px'},
            children=[
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'},
                    children=[
                        html.Div([
                            html.Label('Value'),
                            dcc.Dropdown(
                                id='value-dropdown',
                                options=[{'label': 'Option 1', 'value': 'Option 1'},
                                        {'label': 'Option 2', 'value': 'Option 2'}],
                                placeholder="Select or enter a value",
                                style={'marginBottom': '10px'}
                            ),
                            dcc.Input(id='value-input', type='text', placeholder='Or enter a custom value')
                        ], id='drag-3', className='drag-item', style={'background-color': 'lightcoral', 'padding': '10px'}),

                        dcc.Input(
                            id={'type': 'query-name', 'index': query_index},
                            type='text',
                            placeholder='Query name',
                            style={'flex': '1'}
                        ),
                        dcc.Dropdown(
                            self.getPredicates(),
                            id={'type': 'predicate-dropdown', 'index': query_index},
                            style={'flex': '1'}
                        )
                         
                    ]
                ),
                dcc.Loading(
                            id={'type': 'loading-predicate-input', 'index': query_index},
                            type="default",
                            children=[
                                html.Div(
                                    id={'type': 'predicate-input', 'index': query_index},
                                    style={'flex': '1'}
                                    # style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}
                                )
                            ]
                        ),
                dcc.Loading(
                    id={'type': 'loading-predicate-output', 'index': query_index},
                    type="default",
                    children=[
                        html.Div(
                            id={'type': 'predicate-output', 'index': query_index},
                            style={'width': '100%', 'height': '400px', 'overflowY': 'auto'}
                        )
                    ]
                )
            ]
        )

        
    
        # @callback(
        #     Output('query-sections', 'children'),
        #     Input('add-query-button', 'n_clicks'),
        #     # Input({'type': 'query-name', 'index': ALL}, 'value'),
        #     # Input({'type': 'predicate-dropdown', 'index': ALL}, 'value'),
        #     # Input({'type': 'predicate-input', 'index': ALL}, 'children')
        # )
        # def add_query_section(n_clicks):
        #     sections = []
        #     for i in range(n_clicks + 1):
        #         section = self.create_query_section(i)
        #         print(f"Section {i} structure: {section}") 
        #         if i < len(predicates):
        #             try:
        #                 section.children[0].children[1].value = predicates[i]
        #             except AttributeError as e:
        #                 print(f"AttributeError: {e} in section {i}")
        #         sections.append(section)
        #     return sections
        
        @callback(
            Output({'type': 'predicate-input', 'index': MATCH}, 'children'),
            Input({'type': 'predicate-dropdown', 'index': MATCH}, 'value'),
            State({'type': 'predicate-dropdown', 'index': MATCH}, 'id')
        )
        def update_output(value, id):
            index = id['index']
            print(f"update_output called with value: {value}, index: {index}")
            if value is not None:
                pred = self.get_predicate_class(value)
                self.selections['predicate'+ str(index)] = pred
                arg_names = VelPredicate.get_predicate_args(pred)
    
                if 'attribute_key' in arg_names and ('value' in arg_names or 'values' in arg_names):
                    print("in if")
                    return html.Div([
                        html.Label('Attribute Key:'),
                        dcc.Dropdown(id={'type': 'attribute-key-dropdown', 'index': index},
                                        options=[{'label': col, 'value': col} for col in self.df.columns]),
                        html.Div(id={'type': 'value-options-container', 'index': index})
                    ])
    
                elif 'values' in arg_names and len(arg_names) == 1:
                    unique_values = self.df['Activity'].unique()
                    return html.Div([
                        html.Label('Values:'),
                        dcc.Dropdown(id={'type': 'values-dropdown', 'index': index},
                                    multi='values' in arg_names,
                                    options=[{'label': value, 'value': value} for value in unique_values])
                    ])
                else:
                    if 'group_by' in arg_names:
                        return html.Div([
                            html.Label('Aggregate Column:'),
                            dcc.Dropdown(id={'type': 'attribute-key-dropdown-groupby', 'index': index},
                                        options=[{'label': col, 'value': col} for col in self.log.columns]),
                            html.Div(id={'type': 'groupby-options-container', 'index': index})
                        ])
    
                    elif value == 'DurationWithin':
                        return html.Div([
                            html.Label('Min Duration:'),
                            dcc.Input(id={'type': 'min-duration', 'index': index}, type='number'),
                            html.Label('Max Duration:'),
                            dcc.Input(id={'type': 'max-duration', 'index': index}, type='number')
                        ])
    
        @callback(
            Output({'type': 'value-options-container', 'index': MATCH}, 'children'),
            Input({'type': 'attribute-key-dropdown', 'index': MATCH}, 'value'),
        )
        def update_value_options(selected_key):
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            unique_values = self.df[selected_key].unique()
            return html.Div([
                html.Label('Values:'),
                dcc.Dropdown(id={'type': 'value-options'},
                            options=[{'label': value, 'value': value} for value in unique_values])
            ])
        @callback(
            Output({'type': 'predicate-output', 'index': MATCH}, 'children', allow_duplicate=True),
            [Input({'type': 'min-duration', 'index': MATCH}, 'value'),
            Input({'type': 'max-duration', 'index': MATCH}, 'value')],
            prevent_initial_call=True
        )
        def update_duration_output(min_duration, max_duration, index):
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
    
        @callback(
            Output({'type': 'groupby-options-container', 'index': MATCH}, 'children'),
            Input({'type': 'attribute-key-dropdown-groupby', 'index': MATCH}, 'value')
        )
        def update_groupby_options(selected_key, index):
            if selected_key is None:
                    return []
            self.selections['attribute_key'] = selected_key
            return html.Div([
                html.Label('Group By Values:'),
                dcc.Dropdown(id={'type': 'groupby-options', 'index': index},
                            multi=True,
                            options=[{'label': col, 'value': col} for col in self.log.columns])
            ])
    
        @callback(
            Output({'type': 'predicate-output', 'index': MATCH}, 'children', allow_duplicate=True),
            [Input({'type': 'groupby-options', 'index': MATCH}, 'value')],
            prevent_initial_call=True
        )
        def update_groupby_output(selected_value, index):
            if selected_value is None:
                return []
            self.selections['values'] = selected_value
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
    
        @callback(
            Output({'type': 'predicate-output', 'index': MATCH}, 'children', allow_duplicate=True),
            Input({'type': 'values-dropdown', 'index': MATCH}, 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_value, index):
            if selected_value is None:
                return html.Div("Please select a value from the dropdown.")
            else:
                self.selections['values'] = selected_value
                result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)

        return result

    


    def queryBuilder(self):
        app = Dash(__name__)

        app.layout = html.Div(
            style={'border': '1px solid black', 'padding': '20px', 'width': '800px', 'margin': 'auto'},
            children=[
                html.H3('Query Builder'),
                html.Div(id='query-sections', children=[
                    self.create_query_section(0)
                ]),
                html.Button('Add Query', id='add-query-button', n_clicks=0)
            ]
        )

        return app



    def queryBuilder1(self):
        
        app = Dash(__name__)

        app.layout = html.Div(
        style={'border': '1px solid black', 'padding': '20px', 'width': '800px', 'margin': 'auto'},
        children=[
            html.H3('Query Builder'),
            html.Div(
                style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'},
                children=[
                    html.Div(
                        style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'},
                        children=[
                            dcc.Input(
                                id='query-name',
                                type='text',
                                placeholder='Query name',
                                style={'flex': '1'}
                            ),
                            dcc.Dropdown(
                                self.getPredicates(),
                                id='pandas-dropdown-2',
                                style={'flex': '1'}
                            ),
                            html.Button(
                                'Add',
                                id='add-query',
                                style={'flex': 'none'}
                            )
                        ]
                    ),
                    dcc.Loading(
                        id="loading-predicate-input1",
                        type="default",
                        children=[
                            html.Div(
                                id='predicate-input1',
                                style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}
                            )
                        ]
                    ),
                    dcc.Loading(
                        id="loading-predicate-output",
                        type="default",
                        children=[
                            html.Div(
                                id='predicate-output',
                                style={'width': '100%', 'height': '400px', 'overflowY': 'auto'}
                            )
                        ]
                    ),
                    html.Div(id='queries-container')
                ]
            )
        ]
    )
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
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
                        html.Div(id='value-options-container',
                                 style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'})
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
    
    def layoutTest(self):


        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        app.layout = html.Div([
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Name:', type='primary'), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(id='qname', placeholder='Enter a value', size='medium'), width=2)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Condition:', type='primary'), width="auto", align="center"),
                        dbc.Col(       
                                
                        fac.AntdSpace(
                            [
                                fac.AntdRadioGroup(
                                    options=[
                                        {
                                            'label': f'{c}',
                                            'value': c
                                        }
                                        for c in self.getPredicates()
                                    ],
                                    id='radios',
                                    # defaultValue='a',
                                    optionType='button'
                                )
                            ],
                            direction='horizontal'
                        )
                        )
                    ],className="mb-3"),


                    dbc.Row([
                        dbc.Col(
                            html.Div(id='Query_input')
                        )
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col(
                            html.Div(id='Query_display')
                        )
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(
                            html.Div(id='Query_output_button')
                        )
                    ], className="mb-3"),

                    # dbc.Button("Generate Output", id="submit", color="primary", className="mr-1", disabled=True),

                    dbc.Spinner(
                        dbc.Row([
                            dbc.Col(
                                html.Div(id='predicate_output')
                            )
                        ], className="mb-3"), color="primary"),

                ], style={'padding': '20px', 'margin': '20px'}),


        


        @app.callback(
            Output("Query_input", "children"),
            Input("radios", "value")
        )

        def update_output(value):

            if value is not None:
                
                pred = self.get_predicate_class(value)
                self.selections = {}
                self.selections['predicate'] = pred
                print("Predicate: ", value)
                arg_names = VelPredicate.get_predicate_args(pred)
                
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
                    ])
                
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

                    ])


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
                    ])

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
                        ])

                        # return html.Div([
                        # html.Label('Aggregate Column:'),
                        # dcc.Dropdown(id='attribute-key-dropdown-groupby', 
                        #             options=[{'label': col, 'value': col} for col in self.log.columns]),
                        # html.Div(id='groupby-options-container')
                        # ])
                    
                    elif value == 'DurationWithin':

                        return html.Div([
                               dbc.Row([
                                   dbc.Col(fac.AntdText('Min Duration:', type='primary'), width="auto", align="center"),
                                   dbc.Col(fac.AntdTimePicker(id='min_duration', placeholder='Enter a value', showNow= False , style={'width': '100%'}), width=2),
                                   dbc.Col(fac.AntdText('Max Duration:', type='primary'), width="auto", align="center"),    
                                   dbc.Col(fac.AntdTimePicker(id='max_duration', placeholder='Enter a value', showNow= False ,style={'width': '100%'}), width=2)])
                        ])

                        # return html.Div([
                        #     html.Label('Min Duration:'),
                        #     dcc.Input(id='min-duration', type='time'),
                        #     html.Label('Max Duration:'),
                        #     dcc.Input(id='max-duration', type='time')
                        # ])

        

        # @callback to run the predicate for DurationWithin
        @app.callback(
            Output('predicate_output', 'children', allow_duplicate=True),
            [Input('min_duration', 'value'),
            Input('max_duration', 'value')],
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
        

        # @callback to return the groupby options
        @app.callback(
            Output('groupby_options_container', 'children'),
            Input('attribute_key_dropdown_groupby', 'value')
        )
        def update_groupby_options(selected_key):
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            return html.Div([
                html.Label('Group By Values:'),
                dcc.Dropdown(id='groupby_options',
                             multi=True,
                             options=[{'label': col, 'value': col} for col in self.log.columns])
                            
            ]), 
        
        # @callback to run the predicate for groupby
        @app.callback(
            Output('predicate_output', 'children', allow_duplicate=True),
            [Input('groupby_options', 'value')],
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
        

        # @callback to run the predicate for values
        @app.callback(
            Output('predicate_output', 'children', allow_duplicate=True),
            Input('values_dropdown', 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_value):
            if selected_value is None:
                return html.Div("Please select a value from the dropdown.")
            else:
                self.selections['values'] = selected_value
                
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
            Output('predicate_output', 'children', allow_duplicate=True),
            Input('attribute_key_dropdown', 'value'),
            Input('value_input', 'value'),
            prevent_initial_call=True
        )
        def update_values(selected_key, selected_value):
            if selected_value is None:
                return html.Div("Please select a value from the dropdown.")
            else:
                try:
                    converted_value = float(selected_value)
                except ValueError:
                    return html.Div("Invalid value. Please enter a numeric value.")
        
                self.selections['values'] = converted_value
                self.selections['attribute_key'] = selected_key
                # self.selections['values'] = float(selected_value)
                
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

        # @callback to update the value options based on the selected attribute key
        @app.callback(
            Output('value_options_container', 'children'),
            Input('attribute_key_dropdown', 'value')
        )
        
        def update_value_options(selected_key):
            print(f"selected_key: {selected_key}")
            if selected_key is None:
                return []
            self.selections['attribute_key'] = selected_key
            unique_values = self.df[selected_key].unique()
            print(f"unique_values: {unique_values}")
            

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
            ])

           

        @app.callback(
            Output('predicate_output', 'children'),
            [Input('value_options', 'value')]
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

        # @callback to display the query
        @app.callback(
            Output("Query_display", "children", allow_duplicate=True),
            Input("qname", "value"),
            Input("radios", "value"),
            Input("attribute_key_dropdown", "value"),
            Input("values_dropdown", "value"),
            prevent_initial_call=True
        )
        def update_query_display(qname, radios, attribute_key_dropdown, values_dropdown):
            
            query_str = f"Query('{qname}', {radios}('{attribute_key_dropdown}', '{values_dropdown}'))"
     

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
            Output("Query_display", "children", allow_duplicate=True),
            Input("qname", "value"),
            Input("radios", "value"),
            Input("attribute_key_dropdown", "value"),
            Input("value_input", "value"),
            prevent_initial_call=True
        )
        def update_query_display_(qname, radios, attribute_key_dropdown, value_input):
            if not qname or not radios:
                return html.Div("Please complete all fields for the query to be displayed", style={'color': 'red'})

            query_str = f"Query('{qname}', {radios}('{attribute_key_dropdown}','{value_input}'"
        
            
            query_str += "))"

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
            Output("Query_display", "children", allow_duplicate=True),
            Input("qname", "value"),
            Input("radios", "value"),
            Input("attribute_key_dropdown", "value"),
            Input("min_duration", "value"),
            Input("max_duration", "value"),
            prevent_initial_call=True
        )
        def update_query_display_(qname, radios, attribute_key_dropdown, min_duration, max_duration):
            if not qname or not radios:
                return html.Div("Please complete all fields for the query to be displayed", style={'color': 'red'})

            query_str = f"Query('{qname}', {radios}('{attribute_key_dropdown}','{min_duration}', '{max_duration}'"
        
            
            query_str += "))"

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
        






        # @app.callback(
        #     Output("Query_display", "children"),
        #     [Input("qname", "value"),
        #      Input("radios", "value"),
        #      State("attribute_key_dropdown", "value"),
        #      State("value_input", "value"),
        #      State("values_dropdown", "value")],
        #     prevent_initial_call=True
        # )
        # def update_query_display(qname, radios, attribute_key_dropdown, value_input, values_dropdown):
        #     if not qname or not radios:
        #         return html.Div("Please complete all fields for the query to be displayed", style={'color': 'red'})

        #     query_str = f"Query('{qname}', {radios}("
            
        #     if attribute_key_dropdown:
        #         query_str += f"'{attribute_key_dropdown}', "
            
        #     if value_input:
        #         query_str += f"'{value_input}'"
        #     elif values_dropdown:
        #         query_str += f"'{values_dropdown}'"
            
        #     query_str += "))"

        #     return html.Div([
        #         html.Pre(query_str, style={
        #             'whiteSpace': 'pre-wrap',
        #             'wordBreak': 'break-word',
        #             'backgroundColor': '#f8f9fa',
        #             'padding': '10px',
        #             'borderRadius': '5px',
        #             'border': '1px solid #dee2e6'
        #         })
        #     ])

        # @app.callback(
        #     Output("submit", "disabled"),
        #     Input("qname", "value"),
        #     Input("radios", "value"),
        #     Input("Query_input", "children"),  # Check children instead of value
        #     Input("value_input", "value"),
        #     Input("values_dropdown", "value")
        # )
        # def enable_button(qname, radios, query_input1_children, value_input, values_dropdown):
        #     # Check if all inputs are provided
        #     print("insie enable")
        #     if qname and radios and query_input1_children and (value_input or values_dropdown):
        #         return False  # Enable the button
        #     return True  # Disable the button


        return app









        return app
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # app = dash.Dash(__name__)
    #     app.layout = html.Div([
    #     html.H1('Draggable AntdSelect Example'),
        
    #     # AntdSelect within a draggable div
    #     html.Div(
    #         [
    #             fac.AntdSelect(
    #                 id='antd-select',
    #                 options=[
    #                     {'label': 'Option 1', 'value': 'Option 1'},
    #                     {'label': 'Option 2', 'value': 'Option 2'},
    #                     {'label': 'Option 3', 'value': 'Option 3'}
    #                 ],
    #                 mode='tags',
    #                 placeholder='Select or enter a value',
    #                 style={'width': '100%'}
    #             ),
    #         ],
    #         id='draggable-div',
    #         style={
    #             'width': '50%',
    #             'padding': '10px',
    #             'border': '1px solid black',
    #             'background-color': 'white',
    #             'cursor': 'move'
    #         },
    #         draggable=True
    #     ),
    #     html.Br(),
    #     fac.AntdButton('Submit', id='submit-button', type='primary'),
    #     html.Br(),
    #     html.Div(id='output')
    # ])

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
                        dbc.Col(fac.AntdText('Query Name:', type='primary'), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(id='qname', placeholder='Enter a value', size='medium'), width=3)
                    ], className="mb-3"),

                html.Div(id='condition-container' , children=[
                    
                    html.Div(id='condition-0', children=[

                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Query Condition:{self.index + 1}', type='primary'), width="auto", align="center"),
                            dbc.Col(
                                fac.AntdSpace(
                                    [
                                        fac.AntdRadioGroup(
                                            options=[
                                                {'label': f'{c}', 'value': c}
                                                for c in self.getPredicates()
                                            ],
                                            # id=f'radios{self.index + 1}',
                                            id = {'type': 'radios', 'index': self.index + 1},
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
                                id = {'type': 'predicate-info', 'index': self.index + 1},
                                
                                ), width=12)
                        ]),

                        dbc.Row([
                            dbc.Col(html.Div(
                                # id='Query_input'
                                id = {'type': 'Query_input', 'index': self.index + 1}                                
                                ))
                        ], className="mb-3"),

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
                    ])
                ]),

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
                        dbc.Col(fac.AntdText(f'Query Condition {new_index + 1}:', type='primary'), width="auto", align="center"),
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
                                        id={'type': 'radios', 'index': new_index + 1}
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
                                id={'type': 'predicate-info', 'index': new_index + 1},
                                ), width=12)
                        ]),

                        dbc.Row([
                            dbc.Col(html.Div(
                                # id='Query_input'
                                id={'type': 'Query_input', 'index': new_index + 1}
                                ))
                        ], className="mb-3"),

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
                    ])
                children.append(new_condition)

            return children

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
            # Output("Query_input", "children"),
            Output({'type': 'Query_input', 'index': MATCH}, "children"),
            Output("Query_display", "children", allow_duplicate=True),
            Output("submit", "disabled", allow_duplicate=True),
            # Input("radios", "value"),
            Input({'type': 'radios', 'index': MATCH}, "value"),
            prevent_initial_call=True
        )

        def update_output(value, id):

            if value is not None:
                index = id['index']
                print("Index: ", index)
                pred = self.get_predicate_class(value)
                self.selections = {}
                self.selections['predicate'] = pred
                print("Predicate: ", value)
                arg_names = VelPredicate.get_predicate_args(pred)
                self.predicate[index] = value
                
                query_str = f"Query('{self.name}', {value}('', '')"


                if 'attribute_key' in arg_names and ('values' in arg_names):

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Attribute Key:', type='primary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    id=f'attribute_key_dropdown_{index}', 
                                    options=[{'label': col, 'value': col} for col in self.df.columns],
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                                dbc.Col(html.Div(id=f'value_options_container_{index}'))
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
    


