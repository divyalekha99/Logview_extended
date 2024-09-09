# -*- coding: utf-8 -*-
# coding:=utf-8

from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, SumAggregate
from tests.test_cases.log_test_reader import LogTestReader


def run_sum_aggregate_evaluation(log, variable_name, groupby_var, expected_sum):
    query_evaluator = QueryEvaluatorOnDataFrame()
    filter = Query('query', SumAggregate(variable_name, groupby_var))
    result_set, _ = query_evaluator.evaluate(log, filter)
    assert result_set['Sum'].sum() == expected_sum


def check_sum_as_string(variable_name, groupby_var, reference: str):
    filter = Query('query', SumAggregate(variable_name, groupby_var))
    assert filter.as_string() == reference


def test_sum_aggregate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')

    run_sum_aggregate_evaluation(initial_source_log, 'Var1', 'Group1', 10)
    check_sum_as_string('Var1', 'Group1', "Sum('Var1', group_by=Group1)")
