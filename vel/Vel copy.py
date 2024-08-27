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


        # self.predicates = []

    # def readLog(self):
    #     self.df = pd.read_csv(self.logPath)
    #     self.df = self.df.sort_values([self.CASE_ID_COL, self.TIMESTAMP_COL], ignore_index=True)
    #     return self.log

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
    
    def layoutTestold(self):


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



    def layoutTestnew_(self):


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
    



    def Query_Builder_new(self):


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

    def Query_Builder_v2(self):


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

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # app = dash.Dash(__name__)
    

    def generate_query_tab_v1(self, index):
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
                    dbc.Col(
                        fac.AntdButton('Generate Output', id='submit', disabled=False, type='primary', nClicks=0), width="auto", align="center"
                    )
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

                dbc.Spinner(
                    dbc.Row([
                        dbc.Col(
                            html.Div(id='predicate_output', style={'overflowX': 'auto'})
                        )
                    ], className="mb-3"), color="primary"),
            
            ])
        ]
    )

    def generate_query_tab_v2(self, index):
        self.initialize_query(index)
        print("Generating Query Tab for Index: ", index)
        return fac.AntdTabPane(
            tab=f'Query {index + 1}',
            key=f'tab-{index}',
            children=[
                html.Div([
                    # Query Name Input
                    dbc.Row([
                        dbc.Col(fac.AntdText('Query Name:', className="font-weight-bold"), width="auto", align="center"),
                        dbc.Col(fac.AntdInput(
                            id={'type': 'qname', 'index': index},
                            placeholder='Enter a value', size='middle'),
                            width=2)
                    ], className="mb-3"),
                    
                    # Conditions Placeholder (This will be populated by callback)
                    html.Div(id={'type': 'condition-container', 'index': index}),
                    
                    # Add/Remove Condition Buttons
                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton(
                                'Add Condition', 
                                id={'type': 'add-condition-button', 'index': index}, 
                                type='primary', 
                                nClicks=0,
                                icon=fac.AntdIcon(icon='antd-plus-square-two-tone')
                            ), 
                            width="auto", align="center"
                        ),
                        dbc.Col(
                            fac.AntdButton(
                                'Remove Condition', 
                                id={'type': 'remove-condition-button', 'index': index}, 
                                type='danger', 
                                nClicks=0,
                                icon=fac.AntdIcon(icon='antd-close-circle-two-tone')
                            ),
                            width="auto", align="center"
                        )
                    ], className="mb-3"),
                    
                    # Generate Output Button
                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton('Generate Output', id={'type': 'submit', 'index': index}, type='primary', nClicks=0),
                            width="auto", align="center"
                        )
                    ], className="mb-3"),

                    # Query Display Area
                    dbc.Row([
                        dbc.Col(html.Div(id={'type': 'Query_display', 'index': index}))
                    ], className="mb-3"),

                    # Spinner for Output
                    dbc.Spinner(
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'predicate_output', 'index': index}, style={'overflowX': 'auto'}))
                        ], className="mb-3"), color="primary"
                    ),

                    # Hidden Store for Tracking Conditions
                    dcc.Store(id={'type': 'condition-store', 'index': index}, data=1)
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
            Output({'type': 'condition-container', 'index': MATCH}, 'children'),
            Input({'type': 'add-condition-button', 'index': MATCH}, 'nClicks'),
            Input({'type': 'remove-condition-button', 'index': MATCH}, 'nClicks'),
            State({'type': 'condition-store', 'index': MATCH}, 'data'),
            State({'type': 'condition-container', 'index': MATCH}, 'children'),
            Input('qname_index', 'data'),
            prevent_initial_call=True
        )
        def manage_conditions(add_clicks, remove_clicks, condition_count, existing_conditions, index):
            # Determine if add or remove was triggered
            triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
            print("add Triggered ID: ", triggered_id)
            if 'add-condition-button' in triggered_id:
                condition_count += 1
            elif 'remove-condition-button' in triggered_id and condition_count > 1:
                condition_count -= 1

            if existing_conditions is None:
                existing_conditions = []

            existing_conditions.append(
                html.Div(
                    [
                        # Query Condition Inputs
                        dbc.Row([
                            dbc.Col(fac.AntdText(f'Condition {condition_count}:', className="font-weight-bold"), width="auto", align="center"),
                            dbc.Col(fac.AntdRadioGroup(
                                options=[{'label': f'{c}', 'value': c} for c in self.getPredicates()],
                                id={'type': 'radios', 'index': f'{index}-{condition_count}'},
                                optionType='button'
                            ), width=8)
                        ], className="mb-3"),
                        
                        # Additional Inputs for Each Condition
                        dbc.Row([
                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{condition_count}'}))
                        ], className="mb-3"),
                    ]
                )
            )
            
            return existing_conditions


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

                cond_index_parts = condition_id['index'].split('-')
                cond_index = int(cond_index_parts[-1])  # Assuming you want the last part as the index

                print("C Index: ", cond_index)

                # self.initialize_query(query_index)
                # cond_index = condition_id['index']
                # print("C Index: ", cond_index)
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
                        dcc.Store(id={'type':'value1', 'index': cond_index})
                    ])

                elif 'values' in arg_names and len(arg_names) == 1:

                    unique_values = self.df['Activity'].unique()

                    return html.Div([
                        dbc.Row([
                                dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
                                dbc.Col(fac.AntdSelect(
                                    # id='values_dropdown',
                                    id={'type':'values_dropdown', 'index': f'{query_index}-{cond_index}'}, 
                                    options=[{'label': value, 'value': value} for value in unique_values],
                                    mode='tags',
                                    style={'width': '100%'}
                                ), width=2)
                            ], className="mb-3"),
                        dcc.Store(id={'type':'value2', 'index': f'{query_index}-{cond_index}'})
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
                            dbc.Col(fac.AntdText('Min Duration:', type='secondary'), width="auto", align="center"),
                            dbc.Col(fac.AntdInputNumber(
                                id={'type': 'min_duration', 'index': f'{query_index}-{cond_index}'},
                                placeholder='Enter min duration', 
                                style={'width': '100%'}
                            ), width=2),
                            dbc.Col(fac.AntdText('Max Duration:', type='secondary'), width="auto", align="center"),    
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
                                value=[0, 86400],  # Initial slider range
                            ), width=12)
                        ]),
                        dcc.Store(id={'type':'value3', 'index': f'{query_index}-{cond_index}'})
                    ])

        # @app.callback(
        #     Output("Query_display", "children"),
        #     [
        #         Input({'type': 'qname', 'index': ALL}, "value"),
        #         Input({'type': 'attribute_key_dropdown', 'index': ALL}, "value"),
        #         Input({'type': 'value_input', 'index': ALL}, "value"),
        #         Input({'type': 'value_options', 'index': ALL}, "value"),
        #         Input("qname_index", "data"),  # Assuming you have a store or some method to track the current query index
        #     ],
        #     prevent_initial_call=True
        # )
        # def update_query_display(qnames, attribute_keys, value_inputs, value_options, query_index):
            
        #     query_str = ""

        #     self.initialize_query(query_index)

        #     qname = qnames[query_index] if qnames and len(qnames) > query_index else ""

        #     self.conditions[f'Query{query_index + 1}']['query_name'] = qname
        #     print(f"Query Name for Query{query_index + 1}: {qname}")
        #     print(f"attribute_keys: {attribute_keys}")
        #     print(f"value_inputs: {value_inputs}")
        #     print(f"value_options: {value_options}")

        #     for idx, (key, val_opts, val_input) in enumerate(zip(attribute_keys, value_options, value_inputs)):
        #         print(f"Processing condition {idx + 1} for Query{query_index + 1}")
        #         print(f"key: {key}, val_opts: {val_opts}, val_input: {val_input}")
                
        #         if key or val_opts or val_input:
        #             condition = self.conditions[f'Query{query_index + 1}']['conditions'][idx]
        #             predicate = condition['predicate']
        #             pred_class = condition['predicate_class']
        #             value = val_opts or val_input

        #             print(f"Condition {idx + 1} for Query{query_index + 1}: Predicate: {predicate}, Key: {key}, Value: {value}")

        #             if query_str:
        #                 query_str += f", ({predicate}('{key}', '{value}'))"
        #             else:
        #                 query_str = f"Query('{qname}', {predicate}('{key}', '{value}'))"

        #     print("Final Query String:", query_str)

        #     return html.Pre(query_str, style={
        #         'whiteSpace': 'pre-wrap',
        #         'wordBreak': 'break-word',
        #         'backgroundColor': '#f8f9fa',
        #         'padding': '10px',
        #         'borderRadius': '5px',
        #         'border': '1px solid #dee2e6'
        #     })


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
            prevent_initial_call= True
        )
        def update_values(selected_value, cond_id, query_index):
            if selected_value is None:
                return []
            else:
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
            Input("qname_index", 'data'),
            prevent_initial_call=True
        )
        def update_values(selected_key, selected_value, cond_id, query_index):
            
            print("in GEC options:")
            if selected_key is None:
                return []
            
            try:
                print(f"QIND: {query_index}")
                cond_index_parts = cond_id['index'].split('-')
                cond_index = int(cond_index_parts[-1])

                # cond_index = cond_id['index']
                print("C : ", cond_index)
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
            # State({'type': 'radios', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        
        def update_value_options(selected_key, cond_id, query_index):

            print(f"QINDEX: {query_index}")
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            # cond_index = cond_id['index']
            print("C Index: ", cond_index)

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
                                id={'type': 'value_equality', 'index': f'{query_index}-{cond_index}'},
                                options = [{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
                                mode='tags',
                                style={'width': '100%'}
                            ), width=2)
                        ], className="mb-3"),
                dcc.Store(id={'type': 'value_data', 'index': cond_index})
            ])

        @app.callback(
            # Output('submit', 'disabled', allow_duplicate=True),
            Output({'type': 'value_data', 'index': MATCH}, "data"),
            Input({'type': 'value_equality', 'index': MATCH}, "value"),
            Input({'type': 'value_equality', 'index': MATCH}, "id"),
            Input("qname_index", 'data'),
            prevent_initial_call=True
            # suppress_callback_exceptions=True,

        )
        def update_value_multi(selected_value, cond_id, query_index):
            print("in options multi0:", self.conditions)
            if selected_value is None:
                return []
            cond_index_parts = cond_id['index'].split('-')
            cond_index = int(cond_index_parts[-1])

            self.update_condition(query_index, cond_index, 'values' , selected_value)

            print("in options multi:", self.conditions)

            return cond_index


        @app.callback(
            # Output("predicate_output", "children"),
            Output({'type': 'predicate_output', 'index': MATCH}, "children"),
            [
             Input({"type": "submit", "index": ALL}, "nClicks"),
             Input({"type": "submit", "index": ALL}, "id"),
             Input("qname_index", "data")
             ]
        )
        def on_button_click(n, cond_id, query_index):
            print("in on_button_click:", n)
            if n[0] >= 1:
                print("in on_button_click:", self.conditions)
                
                for key in self.conditions:
                    print(f"Key: {key}, Value: {self.conditions[key]}")
                result = VelPredicate.run_predicate(self.log_view, self.log, self.conditions, f'Query{query_index + 1}')

                # # result = VelPredicate.run_predicate(self.selections['predicate'], self.log_view, self.log, self.selections)
                


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
            return html.Div()

        return app
    def manage_conditions(add_clicks, remove_clicks, condition_count, existing_conditions, index):
            # Determine if add or remove was triggered
            triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
            print("add Triggered ID: ", triggered_id)
            if 'add-condition-button' in triggered_id:
                condition_count += 1
            elif 'remove-condition-button' in triggered_id and condition_count > 1:
                condition_count -= 1

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
                                    id={'type': 'remove-condition-button', 'index': index}, 
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
    
    # @app.callback(
        #     Output({'type': 'Query_display', 'index': ALL}, 'children'),
        #     [
        #         Input({'type': 'attribute_key_dropdown', 'index': ALL}, 'value'),
        #         Input({'type': 'value_input', 'index': ALL}, 'value'),
        #         Input({'type': 'values_dropdown', 'index': ALL}, 'value'),
        #         Input({'type': 'radios', 'index': ALL}, 'value'),
        #         Input({'type': 'time_unit_dropdown', 'index': ALL}, 'value'),
        #         Input({'type': 'min_duration', 'index': ALL}, 'value'),
        #         Input({'type': 'max_duration', 'index': ALL}, 'value'),
        #         Input({'type': 'groupby_options', 'index': ALL}, 'value'),
        #         Input({'type': 'value_equality', 'index': ALL}, 'value'),
        #     ],
        #     [
        #         State({'type': 'attribute_key_dropdown', 'index': ALL}, 'id'),
        #         State({'type': 'value_input', 'index': ALL}, 'id'),
        #         State({'type': 'values_dropdown', 'index': ALL}, 'id'),
        #         State({'type': 'radios', 'index': ALL}, 'id'),
        #         State({'type': 'time_unit_dropdown', 'index': ALL}, 'id'),
        #         State({'type': 'min_duration', 'index': ALL}, 'id'),
        #         State({'type': 'max_duration', 'index': ALL}, 'id'),
        #         State({'type': 'groupby_options', 'index': ALL}, 'id'),
        #         State({'type': 'value_equality', 'index': ALL}, 'id'),
        #         State("qname_index", "data")
        #     ]
        # )
        # def update_query_display(attr_keys, value_inputs, values_list, predicates, time_units, min_durations, max_durations, group_by_values, value_equalities,
        #                         attr_key_ids, value_input_ids, values_dropdown_ids, predicate_ids, time_unit_ids, min_duration_ids, max_duration_ids, group_by_ids, value_equality_ids,
        #                         query_index):

        #     def filter_relevant_inputs(inputs, ids):
        #         return [input_value for input_value, comp_id in zip(inputs, ids) if comp_id['index'].split('-')[0] == str(query_index)]

        #     # Filter inputs relevant to the current query tab using the query_index
        #     relevant_attr_keys = filter_relevant_inputs(attr_keys, attr_key_ids)
        #     relevant_value_inputs = filter_relevant_inputs(value_inputs, value_input_ids)
        #     relevant_values_list = filter_relevant_inputs(values_list, values_dropdown_ids)
        #     relevant_predicates = filter_relevant_inputs(predicates, predicate_ids)
        #     relevant_time_units = filter_relevant_inputs(time_units, time_unit_ids)
        #     relevant_min_durations = filter_relevant_inputs(min_durations, min_duration_ids)
        #     relevant_max_durations = filter_relevant_inputs(max_durations, max_duration_ids)
        #     relevant_group_by_values = filter_relevant_inputs(group_by_values, group_by_ids)
        #     relevant_value_equalities = filter_relevant_inputs(value_equalities, value_equality_ids)

        #     print("Query display val list: ", relevant_values_list)
        #     # Retrieve the query name from self.conditions
        #     query_key = f'Query{query_index + 1}'
        #     query_data = self.conditions.get(query_key, {})
        #     query_name = query_data.get('query_name', '')

        #     # Initialize the query string
        #     query_str = f"Query('{query_name}', "

        #     # Build the query conditions based on the relevant inputs
        #     condition_strs = []
        #     for i, predicate in enumerate(relevant_predicates):
        #         if predicate in ['StartWith', 'EndWith']:
        #             values = relevant_values_list[i] if len(relevant_values_list) >= i else None
        #             print("Query display Values: ", values)
        #             condition_strs.append(f"{predicate}({values})")

        #         elif predicate == 'DurationWithin':
        #             min_duration = relevant_min_durations[i] if len(relevant_min_durations) >= i else None
        #             max_duration = relevant_max_durations[i] if len(relevant_max_durations) >= i else None
        #             condition_strs.append(f"DurationWithin({min_duration}, {max_duration})")

        #         elif predicate in ['SumAggregate', 'MaxAggregate', 'MinAggregate']:
        #             attribute_key = relevant_attr_keys[i] if len(relevant_attr_keys) > i else None
        #             group_by = relevant_group_by_values[i] if len(relevant_group_by_values) > i else None
        #             condition_strs.append(f"{predicate}('{attribute_key}', group_by={group_by})")

        #         elif predicate in ['EqToConstant', 'NotEqToConstant']:
        #             attribute_key = relevant_attr_keys[i] if len(relevant_attr_keys) > i else None
        #             value = relevant_value_equalities[i] if len(relevant_value_equalities) > i else None
        #             condition_strs.append(f"{predicate}('{attribute_key}', '{value}')")

        #         elif predicate in ['GreaterEqualToConstant', 'LessEqualToConstant', 'GreaterThanConstant', 'LessThanConstant']:
        #             attribute_key = relevant_attr_keys[i] if len(relevant_attr_keys) > i else None
        #             value = relevant_value_inputs[i] if len(relevant_value_inputs) > i else None
        #             condition_strs.append(f"{predicate}('{attribute_key}', '{value}')")

        #     if len(condition_strs) == 1:
        #         query_str += condition_strs[0]
        #     else:
        #         query_str += "[" + ", ".join(condition_strs) + "]"
        #     query_str += ")"

        #     num_outputs = len(dash.callback_context.outputs_list)

        #     outputs = [
        #         html.Pre(query_str, style={
        #             'whiteSpace': 'pre-wrap',
        #             'wordBreak': 'break-word',
        #             'backgroundColor': '#f8f9fa',
        #             # 'padding': '10px',
        #             'borderRadius': '5px',
        #             'border': '1px solid #dee2e6',
        #             'fontSize': '14px',
        #             'justifyContent': 'center',
        #             'alignItems': 'center',
        #             'height': '40px',
        #             'textAlign': 'center',
        #             'alignContent': 'center',

        #         }) if i == query_index else dash.no_update
        #         for i in range(num_outputs)
        #     ]

        #     return outputs
        # @app.callback(

        #     Output({'type': 'value_options_container', 'index': MATCH}, "children"),
        #     Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "value"),
        #     Input({'type': 'attribute_key_dropdown', 'index': MATCH}, "id"),
        #     State("qname_index", 'data'),

        # )
        
        # def update_value_options(selected_key, cond_id, query_index):
        #     #print what is triggreing the callback
        #     ctx = dash.callback_context
        #     print("ctx",ctx)
        #     print("value options triggered", ctx.triggered)

        #     cond_index_parts = cond_id['index'].split('-')
        #     cond_index = int(cond_index_parts[-1])

        #     if selected_key is None:
        #         return []

        #     self.update_condition(query_index, cond_index, 'attribute_key' , selected_key)
  
        #     unique_values = self.df[selected_key].unique()

        #     return html.Div([
        #         dbc.Row([
        #                     dbc.Col(fac.AntdText('Values:', type='secondary'), width="auto", align="center"),
        #                     dbc.Col(fac.AntdSelect(
        #                         id={'type': 'value_equality', 'index': f'{query_index}-{cond_index}'},
        #                         options = [{'label': value, 'value': value} for value in unique_values if not pd.isna(value)],
        #                         defaultValue= unique_values[0],
        #                         mode='tags',
        #                         style={'width': '100%'}
        #                     ), width=2)
        #                 ], className="mb-3"),
        #         # dcc.Store(id={'type': 'value_data', 'index': f'{query_index}-{cond_index}'})
        #     ])

        # @app.callback(

        #     Output({'type': 'value_equality', 'index': MATCH}, "value"),
        #     Input({'type': 'value_equality', 'index': MATCH}, "value"),
        #     Input({'type': 'value_equality', 'index': MATCH}, "id"),
        #     State("qname_index", 'data'),
        #     prevent_initial_call=True
        # )

        # def update_value_multi(selected_value, cond_id, query_index):

        #     ctx = dash.callback_context
        #     print("ctx",ctx.triggered_id)
            
        #     print("value equality triggered",selected_value)
        #     print("value equality triggered by",dash.callback_context.triggered)
        #     if selected_value is None:
        #         return []
        #     cond_index_parts = cond_id['index'].split('-')
        #     cond_index = int(cond_index_parts[-1])

        #     self.update_condition(query_index, cond_index, 'values' , selected_value)

        #     return selected_value

    html.Div(id={'type': 'condition-container', 'index': index},
                                children=[html.Div(
                                [
                                    # Query Condition Inputs
                                    dbc.Row([
                                        dbc.Col(fac.AntdText(f'Condition {0+1}:', className="font-weight-bold"), width="auto", align="center"),
                                        dbc.Col(fac.AntdRadioGroup(
                                            options=[{'label': f'{c}', 'value': c} for c in self.getPredicates()],
                                            id={'type': 'radios', 'index': f'{index}-{0}'},
                                            optionType='button'
                                        ), width=8),
                                    ], className="mb-3"),

                                    dbc.Row([
                                        dbc.Col(html.Div(id={'type': 'predicate-info', 'index': f'{index}-{0}'}))
                                    ], className="mb-3"),
                                    
                                    # Additional Inputs for Each Condition
                                    dbc.Row([
                                        dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{0}'}))
                                    ], className="mb-3"),
                                ]
                            )]),
                    
    html.Div(id={'type': 'condition-container', 'index': index},
                        children=[
                            html.Div(
                                [
                                    # Query Condition Header
                                    dbc.Row([
                                        dbc.Col(fac.AntdText(f'Condition {0+1}:', className="font-weight-bold"), width="auto", align="center")
                                    ], className="mb-3"),

                                    # First Row: Attribute-Based Predicates and Threshold-Based Predicates
                                    dbc.Row([
                                        dbc.Col(
                                            html.Div([
                                                html.H6("Attribute-Based Predicates", style={'fontWeight': 'bold'}),
                                                fac.AntdRadioGroup(
                                                    options=[
                                                        {'label': 'Equals to Constant', 'value': 'EqToConstant'},
                                                        {'label': 'Not Equals to Constant', 'value': 'NotEqToConstant'}
                                                    ],
                                                    id={'type': 'radios', 'index': f'{index}-{0}'},
                                                    optionType='button',
                                                    buttonStyle="solid",
                                                    size="middle"
                                                ),
                                            ]),
                                            width=6
                                        ),
                                        dbc.Col(
                                            html.Div([
                                                html.H6("Threshold-Based Predicates", style={'fontWeight': 'bold'}),
                                                fac.AntdRadioGroup(
                                                    options=[
                                                        {'label': 'Greater Than', 'value': 'GreaterThanConstant'},
                                                        {'label': 'Less Than', 'value': 'LessThanConstant'},
                                                        {'label': 'Greater or Equal', 'value': 'GreaterEqualToConstant'},
                                                        {'label': 'Less or Equal', 'value': 'LessEqualToConstant'}
                                                    ],
                                                    id={'type': 'radios', 'index': f'{index}-{0}'},
                                                    optionType='button',
                                                    buttonStyle="solid",
                                                    size="middle"
                                                ),
                                            ]),
                                            width=6
                                        )
                                    ], className="mb-3"),

                                    # Second Row: Aggregate Functions and Activity-Based Predicates
                                        dbc.Row([
                                            dbc.Col(
                                                html.Div([
                                                    html.H6("Aggregate Functions", style={'fontWeight': 'bold'}),
                                                    fac.AntdRadioGroup(
                                                        options=[
                                                            {'label': 'Sum', 'value': 'SumAggregate'},
                                                            {'label': 'Max', 'value': 'MaxAggregate'},
                                                            {'label': 'Min', 'value': 'MinAggregate'}
                                                        ],
                                                        id={'type': 'radios', 'index': f'{index}-{0}'},
                                                        optionType='button',
                                                        buttonStyle="solid",
                                                        size="middle"
                                                    ),
                                                ]),
                                                width=6
                                            ),
                                            dbc.Col(
                                                html.Div([
                                                    html.H6("Activity-Based Predicates", style={'fontWeight': 'bold'}),
                                                    fac.AntdRadioGroup(
                                                        options=[
                                                            {'label': 'Starts With', 'value': 'StartWith'},
                                                            {'label': 'Ends With', 'value': 'EndWith'}
                                                        ],
                                                        id={'type': 'radios', 'index': f'{index}-{0}'},
                                                        optionType='button',
                                                        buttonStyle="solid",
                                                        size="middle"
                                                    ),
                                                ]),
                                                width=6
                                            )
                                        ], className="mb-3"),

                                        # Third Row: Time-Based Predicates
                                        dbc.Row([
                                            dbc.Col(
                                                html.Div([
                                                    html.H6("Time-Based Predicates", style={'fontWeight': 'bold'}),
                                                    fac.AntdRadioGroup(
                                                        options=[
                                                            {'label': 'Duration Within', 'value': 'DurationWithin'}
                                                        ],
                                                        id={'type': 'radios', 'index': f'{index}-{0}'},
                                                        optionType='button',
                                                        buttonStyle="solid",
                                                        size="middle"
                                                    ),
                                                ]),
                                                width=6
                                            )
                                        ], className="mb-3"),

                                        # Predicate Info and Additional Inputs
                                        dbc.Row([
                                            dbc.Col(html.Div(id={'type': 'predicate-info', 'index': f'{index}-{0}'}), width=12)
                                        ], className="mb-3"),
                                        
                                        dbc.Row([
                                            dbc.Col(html.Div(id={'type': 'Query_input', 'index': f'{index}-{0}'}), width=12)
                                        ], className="mb-3"),
                                    ]
                                )
                            ]),
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
                            id={'type': 'query_name', 'index': index},
                            placeholder='Enter a value', size='middle'),
                            width=2)
                    ], className="mb-3"),


                    html.Div(id={'type': 'condition-container', 'index': index},
                                children=[html.Div(
                                [
                                    # Query Condition Inputs
                                    dbc.Row([
                                        dbc.Col(fac.AntdText(f'Condition {0+1}:', className="font-weight-bold"), width="auto", align="center"),
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
                                ]
                            )]),
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
                        dbc.Col(
                            fac.AntdSpace(
                                id={'type': 'label-container', 'index': index},
                                children=[],
                                direction='horizontal',
                                style={'width': '100%', 'flex-wrap': 'wrap', 'gap': '5px'}
                            ),
                            width=12
                        ),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col(
                            fac.AntdButton(
                                'Add Label',
                                icon=fac.AntdIcon(icon='antd-plus'),
                                type='dashed',
                                size='small',
                                nClicks=0,
                                id={'type': 'add-label-button', 'index': index},
                            ),
                            width="auto", align="end"
                        ),
                        dbc.Col(html.Div(id={'type': 'label-input-container', 'index': index}))
                    ], className="mb-3"),

                    
                    # Query Display Area
                    dbc.Row([
                        dbc.Col(html.Div(id={'type': 'Query_display', 'index': index})),
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
                            width="auto", align="start" #, style={'paddingBottom': '40px'}
                        )
                    ], className="mb-3", style={'marginTop': '50px'}),

                    

                    # dbc.Progress(id={'type': 'progress-bar', 'index': index}, style={'marginTop': '10px'}, animated=True, striped=True),
                    # html.Div(id="loading-placeholder", className="shadow-loading", style={"height": "200px", "marginTop": "20px"}),

                    # Spinner for Output
                    # dbc.Spinner(
                    
                    # ,color="primary", type="border"),
                    fac.AntdSkeleton(
                        dbc.Row([
                        dbc.Col(
                            html.Div(id={'type': 'predicate_output', 'index': index}, style={'overflowX': 'auto'}))
                        ], className="mb-3"),
                        active=True,
                        # avatar={'size': 'large', 'shape': 'square'},
                        paragraph={'rows': 7, 'width': '50%'},
                        # title={'width': '8rem'}
                    ),


                    # Hidden Store for Tracking Conditions
                    dcc.Store(id={'type': 'condition-store', 'index': index}, data=0),
                    dcc.Store(id={'type': 'qname-store', 'index': index}),


                ])
            ]
        )
    
