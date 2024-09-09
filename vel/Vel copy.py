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
                            dbc.Row([
                                dbc.Col("Source Log: ", style={'fontWeight': 'bold', 'display': 'inline'}, width='auto'),
                                dbc.Col(row['source_log'], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px'}),
                            dbc.Row([
                                dbc.Col("Result Set: ", style={'fontWeight': 'bold', 'display': 'inline'}, width='auto'),
                                dbc.Col(row['result_set'], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px'}),
                            dbc.Row([
                                dbc.Col("Labels: ", style={'fontWeight': 'bold', 'display': 'inline'}, width='auto'),
                                dbc.Col(row['labels'], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px'}),
                            dbc.Row([
                                dbc.Col("Predicates: ", style={'fontWeight': 'bold', 'display': 'inline'}, width='auto'),
                                dbc.Col(queries.loc[queries['query'] == row['query'], 'predicates'].values[0], style={'display': 'inline'}, width='auto')
                            ], style={'marginBottom': '6px'}),
                        ],
                        bordered=True,
                        style={
                            'marginBottom': '10px',
                            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.15)',
                            'borderRadius': '8px',
                            'backgroundColor': '#fafafa'  # Slightly different background color for the card body
                        },
                        bodyStyle={'padding': '10px'},
                        hoverable=True,
                        headStyle={'backgroundColor': '#f0f2f5'}  # Slightly different color for the card header
                    ),
                    'color': 'blue',
                }
                for index, row in evaluations.iterrows()
            ]


            # Build the AntdTimeline component
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


@app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
            Input({"type": "submit", "index": MATCH}, "n_clicks"),
            # Input({'type':'warning-popup', 'index': MATCH}, 'visible'),
            # State({'type': 'warning-state', 'index': MATCH}, 'data'),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        # def on_button_click(n_clicks, warning_visible, warning_state, query_index):
        def on_button_click(n_clicks, query_index):

            if n_clicks is None:
                raise dash.exceptions.PreventUpdate
            
            # print("warning_state", warning_state, warning_visible, n_clicks)

            if n_clicks > 0 :
                start_time = time.time()
                
                # Log start
                print("Running predicate...")

                result, self.num_cases, self.num_events  = VelPredicate.run_predicate(self.log_view, self.conditions, f'Query{query_index + 1}', 10)

                if result is None or result.empty:
                    return html.Div("No data available for the selected filters, try different filters.")

                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in result.columns],
                    data= result.head(10).to_dict('records'),  
                    page_size=10,
                    page_action='none',  
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'}
                )

                # self.num_cases = len(result['case:concept:name'].unique())
                # self.num_events = len(result)

                shape_info = html.Div([
                    html.Span(f"Number of Cases: {self.num_cases}", style={'fontWeight': 'bold', 'marginRight': '20px'}),
                    html.Span(f"Number of Events: {self.num_events}", style={'fontWeight': 'bold'})
                ], style={'marginBottom': '10px'})

                load_more_options = html.Div([
                    dbc.Button("Load Next 10 Rows", id={'type': 'load-next-rows-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                    dbc.Button("Load Full Table", id={'type': 'load-full-table-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                ], style={'marginTop': '10px'})

                print(f"Total execution time: {time.time() - start_time:.2f} seconds")

                return html.Div([shape_info, table, load_more_options])

            return html.Div()
        
        @app.callback(
        [
            Output({'type': 'query-result', 'index': MATCH}, "data")],
            Input({"type": "submit", "index": ALL}, "n_clicks"),
            # Input({'type':'warning-popup', 'index': MATCH}, 'visible'),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        def on_button_click_background(n_clicks , query_index):
            if n_clicks[0] is None:
                raise dash.exceptions.PreventUpdate

            if n_clicks[0] > 0 :
                start_time = time.time()
                
                # Log start
                print("Running predicate background entire...")

                result, _, _  = VelPredicate.run_predicate(self.log_view, self.conditions, f'Query{query_index + 1}', 0)

                if result is None or result.empty:
                    return [result.to_dict('records')]

                print(f"Total execution time: {time.time() - start_time:.2f} seconds")

                return [result.to_dict('records')]

            return dash.no_update
        # Callback for handling the "Load Next 10 Rows" functionality
        @app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
            Output({'type': 'row-number-store', 'index': MATCH}, 'data'),
            Input({'type': 'load-next-rows-button', 'index': MATCH}, 'n_clicks'),
            State({'type': 'predicate_output', 'index': MATCH}, 'children'),
            State({'type': 'query-result', 'index': MATCH}, 'data'),
            State({'type': 'row-number-store', 'index': MATCH}, 'data'),
            State("qname_index", "data"),
            prevent_initial_call=True
        )
        def load_next_10_rows(n_clicks, current_output, stored_data, current_rows, query_index):
            if n_clicks > 0:
                
                new_row_number = current_rows + 10

                # Create the updated DataTable
                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in stored_data[0].keys()],
                    data=stored_data[:new_row_number], 
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
                    dbc.Button("Load Next 10 Rows", id={'type': 'load-next-rows-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                    dbc.Button("Load Full Table", id={'type': 'load-full-table-button', 'index': query_index}, n_clicks=0, style={'marginRight': '10px'}),
                ], style={'marginTop': '10px'})

                return html.Div([shape_info, table, load_more_options]), new_row_number

            return dash.no_update



        # Callback for handling the "Load Full Table" functionality
        @app.callback(
            Output({'type': 'predicate_output', 'index': MATCH}, "children", allow_duplicate=True),
            Input({'type': 'load-full-table-button', 'index': MATCH}, 'n_clicks'),
            State({'type': 'query-result', 'index': MATCH}, 'data'),
            prevent_initial_call=True
        )
        def load_full_table(n_clicks, stored_data):
            if n_clicks > 0:

                table = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in stored_data[0].keys()],
                    data=stored_data,
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


            # Helper function to filter relevant inputs by query index
        # def filter_relevant_inputs(inputs, query_index):
        #     return [input_value for input_value, comp_id in inputs if comp_id['index'].split('-')[0] == str(query_index)]

        # # Helper function to check if a required field is missing
        # def check_required_field(field, field_name, required_fields):
        #     if not field:
        #         required_fields.append(field_name)
        #         return True
        #     return False

        # # Helper function to check attribute keys and values
        # def validate_predicates(predicates, attr_keys, value_inputs, values_dropdowns, value_equalities, query_index, required_fields):
        #     warning_state = False
        #     for pred, _ in predicates:
        #         if pred in ['EqToConstant', 'NotEqToConstant', 'GreaterEqualToConstant', 'LessEqualToConstant', 'GreaterThanConstant', 'LessThanConstant']:
        #             if check_required_field(attr_keys, f"Missing Attribute Key for '{pred}' Predicate", required_fields):
        #                 warning_state = True
        #             if pred in ['EqToConstant', 'NotEqToConstant']:
        #                 if check_required_field(value_equalities, f"Missing Value for '{pred}' Predicate", required_fields):
        #                     warning_state = True
        #             else:
        #                 if check_required_field(value_inputs, f"Missing Input Value for '{pred}' Predicate", required_fields):
        #                     warning_state = True
        #         elif pred in ['StartWith', 'EndWith']:
        #             if check_required_field(values_dropdowns, f"Missing Values for '{pred}' Predicate", required_fields):
        #                 warning_state = True
        #         elif pred == 'DurationWithin':
        #             # Add additional checks for 'DurationWithin' if needed
        #             pass
        #         elif pred in ['SumAggregate', 'MaxAggregate', 'MinAggregate']:
        #             # Add checks for aggregate predicates
        #             pass
        #     return warning_state

        # # Optimized Callback
        # @app.callback(
        #     [
        #         Output({'type': 'warning-popup', 'index': MATCH}, 'visible'),
        #         Output({'type': 'warning-message', 'index': MATCH}, 'children'),
        #         Output({'type': 'warning-state', 'index': MATCH}, 'data')
        #     ],
        #     [
        #         Input({'type': 'submit', 'index': MATCH}, 'n_clicks')
        #     ],
        #     [
        #         State({'type': 'query_name', 'index': MATCH}, 'value'),
        #         State({'type': 'log_selector', 'index': MATCH}, 'value'),
        #         State({'type': 'radios', 'index': ALL}, 'value'),
        #         State({'type': 'attribute_key_dropdown', 'index': ALL}, 'value'),
        #         State({'type': 'value_input', 'index': ALL}, 'value'),
        #         State({'type': 'values_dropdown', 'index': ALL}, 'value'),
        #         State({'type': 'value_equality', 'index': ALL}, 'value'),
        #         State("qname_index", "data")
        #     ]
        # )
        # def handle_run_query_click(n_clicks, query_name, log_selector, predicates, attr_keys, value_inputs, values_dropdowns, value_equalities, query_index):
        #     if n_clicks is None or n_clicks == 0:
        #         return False, "", False

        #     required_fields = []
        #     warning_state = False

        #     # Filter relevant inputs for the current query
        #     relevant_predicates = filter_relevant_inputs(list(zip(predicates, [{'index': f"{query_index}-{i}"} for i in range(len(predicates))])), query_index)
        #     relevant_attr_keys = filter_relevant_inputs(attr_keys, query_index)
        #     relevant_value_inputs = filter_relevant_inputs(value_inputs, query_index)
        #     relevant_values_dropdowns = filter_relevant_inputs(values_dropdowns, query_index)
        #     relevant_value_equalities = filter_relevant_inputs(value_equalities, query_index)


        #     if check_required_field(query_name, "Query Name", required_fields):
        #         warning_state = True

        #     if check_required_field(log_selector, "Log", required_fields):
        #         warning_state = True

        #     warning_state = validate_predicates(relevant_predicates, relevant_attr_keys, relevant_value_inputs, relevant_values_dropdowns, relevant_value_equalities, query_index, required_fields)

        #     if required_fields:
        #         warning_message = f"Missing required fields: {', '.join(required_fields)}"
        #         return True, warning_message, warning_state

        #     return False, "", False


        # # Callback to handle validation and display warnings only when Run Query is clicked
        # @app.callback(
        #     [
        #         Output({'type': 'warning-popup', 'index': MATCH}, 'visible'),  # Control the visibility of the popup
        #         Output({'type': 'warning-message', 'index': MATCH}, 'children'),  # Set the warning message
        #         # Output({'type': 'submit', 'index': MATCH}, 'n_clicks'),
        #         Output({'type': 'warning-state', 'index': MATCH}, 'data')  # Reset the click counter after handling
        #     ],
        #     [
        #         Input({'type': 'submit', 'index': MATCH}, 'n_clicks')  # Trigger the popup on Run Query button click
        #     ],
        #     [
        #         State({'type': 'query_name', 'index': MATCH}, 'value'),
        #         State({'type': 'log_selector', 'index': MATCH}, 'value'),
        #         State({'type': 'radios', 'index': ALL}, 'value'),
        #         State({'type': 'attribute_key_dropdown', 'index': ALL}, 'value'),
        #         State({'type': 'attribute_key_dropdown_groupby', 'index': ALL}, 'value'),
        #         State({'type': 'value_input', 'index': ALL}, 'value'),
        #         State({'type': 'values_dropdown', 'index': ALL}, 'value'),
        #         State({'type': 'time_unit_dropdown', 'index': ALL}, 'value'),
        #         State({'type': 'min_duration', 'index': ALL}, 'value'),
        #         State({'type': 'max_duration', 'index': ALL}, 'value'),
        #         State({'type': 'groupby_options', 'index': ALL}, 'value'),
        #         State({'type': 'value_equality', 'index': ALL}, 'value'),
        #         State("qname_index", "data"),  # Active query index
        #         State({'type': 'warning-state', 'index': MATCH}, 'data')
        #     ]
        # )
        # def handle_run_query_click(n_clicks, query_name, log_selector, predicates, attr_keys, groupby_attr_keys, value_inputs, values_dropdowns, time_units, min_durations, max_durations, groupby_options, value_equalities, query_index, warning_state):
        #     if n_clicks is None or n_clicks == 0:
        #         return False, "", False

        #     required_fields = []

        #     # This function filters inputs by query_index
        #     def filter_relevant_inputs(inputs, ids):
        #         # Ensure 'index' field is always string to split correctly
        #         return [
        #             (input_value, comp_id) for input_value, comp_id in zip(inputs, ids)
        #             if isinstance(comp_id['index'], str) and comp_id['index'].split('-')[0] == str(query_index)
        #         ]

        #     # Applying the filtering for each input type
        #     relevant_predicates = filter_relevant_inputs(predicates, [{'index': f"{query_index}-{i}"} for i in range(len(predicates))])
        #     relevant_attr_keys = filter_relevant_inputs(attr_keys, [{'index': f"{query_index}-{i}"} for i in range(len(attr_keys))])
        #     relevant_groupby_attr_keys = filter_relevant_inputs(groupby_attr_keys, [{'index': f"{query_index}-{i}"} for i in range(len(groupby_attr_keys))])
        #     relevant_value_inputs = filter_relevant_inputs(value_inputs, [{'index': f"{query_index}-{i}"} for i in range(len(value_inputs))])
        #     relevant_values_dropdowns = filter_relevant_inputs(values_dropdowns, [{'index': f"{query_index}-{i}"} for i in range(len(values_dropdowns))])
        #     relevant_time_units = filter_relevant_inputs(time_units, [{'index': f"{query_index}-{i}"} for i in range(len(time_units))])
        #     relevant_min_durations = filter_relevant_inputs(min_durations, [{'index': f"{query_index}-{i}"} for i in range(len(min_durations))])
        #     relevant_max_durations = filter_relevant_inputs(max_durations, [{'index': f"{query_index}-{i}"} for i in range(len(max_durations))])
        #     relevant_groupby_options = filter_relevant_inputs(groupby_options, [{'index': f"{query_index}-{i}"} for i in range(len(groupby_options))])
        #     relevant_value_equalities = filter_relevant_inputs(value_equalities, [{'index': f"{query_index}-{i}"} for i in range(len(value_equalities))])


        #     # Debugging filtered inputs
        #     print(f"Filtered Predicates for Query {query_index}: {relevant_predicates}")
        #     print(f"Filtered Values for Query {query_index}: {relevant_values_dropdowns}")
        #     print(f"Filtered Attr Keys for Query {query_index}: {relevant_attr_keys}")
        #     print(f"Filtered Value Inputs for Query {query_index}: {relevant_value_inputs}")
        #     print(f"Filtered Value Equalities for Query {query_index}: {relevant_value_equalities}")

        #     # Check if the query name is entered
        #     if not query_name:
        #         required_fields.append("Query Name")
        #         warning_state = True

        #     # Check if the log is selected
        #     if not log_selector:
        #         required_fields.append("Log")
        #         warning_state = True

        #     # Check if at least one predicate is selected
        #     if not any([pred for pred, _ in relevant_predicates]):
        #         required_fields.append("At least one Predicate")
        #         warning_state = True

        #     # Optimized check for missing fields based on predicates
        #     for pred, _ in relevant_predicates:
        #         # Common checks for attribute keys and values
        #         if pred in ['EqToConstant', 'NotEqToConstant', 'GreaterEqualToConstant', 'LessEqualToConstant', 'GreaterThanConstant', 'LessThanConstant']:
        #             if not relevant_attr_keys or any(attr_key is None for attr_key, _ in relevant_attr_keys):
        #                 warning_state = True
        #                 required_fields.append(f"Missing Attribute Key for '{pred}' Predicate")
        #             if pred in ['EqToConstant', 'NotEqToConstant']:
        #                 if not relevant_value_equalities or any(value_eq is None for value_eq, _ in relevant_value_equalities):
        #                     warning_state = True
        #                     required_fields.append(f"Missing Value for '{pred}' Predicate")
        #             else:
        #                 if not relevant_value_inputs or any(value_input is None for value_input, _ in relevant_value_inputs):
        #                     warning_state = True
        #                     required_fields.append(f"Missing Input Value for '{pred}' Predicate")

        #         # Check for StartWith or EndWith
        #         elif pred in ['StartWith', 'EndWith']:
        #             actual_values = [val for val, _ in relevant_values_dropdowns if val is not None]
        #             if not actual_values:
        #                 required_fields.append(f"Missing Values for '{pred}' Predicate")
        #                 warning_state = True

        #         # Check for DurationWithin
        #         elif pred == 'DurationWithin':
        #             if not relevant_min_durations or any(min_dur is None for min_dur, _ in relevant_min_durations):
        #                 required_fields.append("Missing Minimum Duration for 'DurationWithin' Predicate")
        #                 warning_state = True
        #             if not relevant_max_durations or any(max_dur is None for max_dur, _ in relevant_max_durations):
        #                 required_fields.append("Missing Maximum Duration for 'DurationWithin' Predicate")
        #                 warning_state = True
        #             if not relevant_time_units or any(time_unit is None for time_unit, _ in relevant_time_units):
        #                 required_fields.append("Missing Time Unit for 'DurationWithin' Predicate")
        #                 warning_state = True

        #         # Check for SumAggregate, MaxAggregate, MinAggregate
        #         elif pred in ['SumAggregate', 'MaxAggregate', 'MinAggregate']:
        #             if not relevant_groupby_attr_keys or any(group_attr is None for group_attr, _ in relevant_groupby_attr_keys):
        #                 required_fields.append(f"Missing Group By Attribute Key for '{pred}' Predicate")
        #                 warning_state = True
        #             if not relevant_groupby_options or any(group_opt is None for group_opt, _ in relevant_groupby_options):
        #                 required_fields.append(f"Missing Group By Option for '{pred}' Predicate")
        #                 warning_state = True

        #     # If required fields are missing, show a warning
        #     if required_fields:
        #         warning_message = f"Missing required fields: {', '.join(required_fields)}"
        #         return True, warning_message, warning_state

        #     # No warning is needed, return the defaults
        #     return False, "", False  # Hide the popup and reset the button click counter



        # # Background process for storing the query result
        # @app.callback(
        #     Output({'type': 'query-result', 'index': MATCH}, "data"),
        #     Input({"type": "submit", "index": ALL}, "n_clicks"),
        #     State("qname_index", "data"),
        #     prevent_initial_call=True
        # )
        # def on_button_click_background(n_clicks, query_index):
        #     if n_clicks[0] is None:
        #         raise dash.exceptions.PreventUpdate

        #     if n_clicks[0] > 0:
        #         query_key = f'Query{query_index + 1}'
                
        #         # Check Redis cache first
        #         result = get_cached_result(query_key)
        #         if result is not None:
        #             print(f"Loaded cached result from Redis for {query_key}")
        #         else:
        #             # Run predicate and cache result in Redis
        #             result, _, _ = VelPredicate.run_predicate(self.log_view, self.conditions, query_key, 0)
        #             if result is None or result.empty:
        #                 return [result.to_dict('records')]
        #             cache_query_result(query_key, result)  # Cache result in Redis
        #             print(f"Cached result in Redis for {query_key}")

        #         return [result.to_dict('records')]

        #     return dash.no_update

def setLogv1(self):
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        app.layout = html.Div([
            dash_table.DataTable(
                id='datatable-interactivity',
                columns=[
                    {"name": i, "id": i, "selectable": True} for i in self.log.columns
                ],
                data=self.log.head(50).to_dict('records'),
                page_size=20,  
                sort_action="native",  
                sort_mode="multi",  
                column_selectable="multi",  
                selected_columns=[],  
                style_table={'overflowX': 'auto', 'color': '#081621'},  
                # style_data={'color': '#081621'},
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
                style={'color': '#081621'}
            ),
            html.Div(id='update-status'),
            dcc.Store(id='stored-columns')  # Store the column mapping
        ])

        @app.callback(
            Output("modal", "is_open"),
            Output("role-assignment-container", "children"),
            Output('stored-columns', 'data'),
            Input("assign-roles-button", "n_clicks"),
            State('datatable-interactivity', 'selected_columns'),
            State("modal", "is_open"),
        )
        def toggle_modal(n_clicks, selected_columns, is_open):
            
            if n_clicks > 0 and selected_columns:
                role_inputs = []
                role_labels = ["CASE_ID_COL", "ACTIVITY_COL", "TIMESTAMP_COL"]
                column_map = {}

                for i, col in enumerate(selected_columns[:3]):
                    column_map[role_labels[i]] = col
                    role_inputs.append(html.Label(f"Assign {role_labels[i]} to: {col}"))

                return not is_open, role_inputs, column_map

            return is_open, [], {}

        @app.callback(
            Output('update-status', 'children'),
            Input('confirm-assignment-button', 'n_clicks'),
            State('stored-columns', 'data')
        )
        def update_column_names(n_clicks, column_map):
            '''
            This function updates the default column names based on the selected roles.
            '''
            if n_clicks > 0:
                case_id_col = column_map.get("CASE_ID_COL")
                activity_col = column_map.get("ACTIVITY_COL")
                timestamp_col = column_map.get("TIMESTAMP_COL")

                self.changeDefaultNames(case_id_col, activity_col, timestamp_col)

                return f"Updated Columns: CASE_ID_COL: {case_id_col}, ACTIVITY_COL: {activity_col}, TIMESTAMP_COL: {timestamp_col}"
            return "No columns selected for update."

        return app
        
        def get_min_max_duration(self):
        '''
        This function returns the minimum and maximum case durations.
        '''
        durations = self.calculate_case_durations()
        min_duration = durations.min()
        max_duration = durations.max()

        min_duration_adjusted = max(0, min_duration)  
        max_duration_adjusted = min(max_duration, max_duration)  

        return min_duration_adjusted, max_duration_adjusted

    def calculate_case_durations(self):def calculate_case_durations(self):
        duration_df = self.df.groupby(self.CASE_ID_COL)[self.TIMESTAMP_COL].agg(['min', 'max'])
        duration_df['duration'] = (duration_df['max'] - duration_df['min']).dt.total_seconds()
        return duration_df['duration']
        
        def getPredicates(self):
        '''
        This function retrieves all available predicates.
        '''
        self.predicates = [pred for pred in logview.predicate.__all__ if pred not in ['Query', 'Union', 'CountAggregate']]
        return self.predicates
        
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
                ], style={'color': 'black', 'fontSize': '15px', 'display': 'flex', 'alignItems': 'center', 'paddingBottom': '20px','fontWeight':'500'}, className="font-weight-bold")
            return html.Div()



        # @app.callback(
        #     Output('tabs', 'items', allow_duplicate=True),
        #     Output('tabs', 'defaultActiveKey', allow_duplicate=True),
        #     Input('tabs', 'latestDeletePane'),
        #     State('tabs', 'items'),
        #     State('tabs', 'activeKey'),
        #     prevent_initial_call=True
        # )
        # def delete_query_tab(latestDeletePane, current_tabs, activeKey):
        #     if latestDeletePane is None:
        #         raise dash.exceptions.PreventUpdate
            
        #     updated_tabs = [tab for tab in current_tabs if tab['key'] != latestDeletePane]

        #     if latestDeletePane == activeKey:
        #         new_active_key = updated_tabs[0]['key'] if updated_tabs else None
        #     else:
        #         new_active_key = dash.no_update

        #     return updated_tabs, new_active_key
                # @app.callback(
        #     Output('tabs', 'items', allow_duplicate=True),
        #     Output('tabs', 'defaultActiveKey', allow_duplicate=True),
        #     Input('add-query-button', 'nClicks'),
        #     State('tabs', 'items'),
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

