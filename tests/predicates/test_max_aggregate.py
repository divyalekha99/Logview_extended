# -*- coding: utf-8 -*-
# coding:=utf-8

from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, MaxAggregate
from tests.test_cases.log_test_reader import LogTestReader


def run_max_aggregate_evaluation(log, variable_name, groupby_var, expected_max):
    query_evaluator = QueryEvaluatorOnDataFrame()
    filter = Query('query', MaxAggregate(variable_name, groupby_var))
    result_set, _ = query_evaluator.evaluate(log, filter)
    assert result_set['Max'].max() == expected_max


def check_max_as_string(variable_name, groupby_var, reference: str):
    filter = Query('query', MaxAggregate(variable_name, groupby_var))
    assert filter.as_string() == reference


def test_max_aggregate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')

    run_max_aggregate_evaluation(initial_source_log, 'Var1', 'Group1', 10)
    check_max_as_string('Var1', 'Group1', "Max('Var1', group_by=Group1)")
