# -*- coding: utf-8 -*-
# coding:=utf-8

"""
from log_view.result_set_characterizer.properties_evaluator import PropertiesEvaluator
from log_view.predicate import EqToConstant
from tests.test_cases.log_test_reader import LogTestReader


def run_evaluation(log, variable_values, len_result_set, len_complement_result_set):
    query_evaluator = QueryEvaluatorOnDataFrame()
    filter = Query(StartWith(variable_values))
    result_set, complement_result_set = query_evaluator.evaluate(log, filter)
    assert len(result_set) == len_result_set
    assert len(complement_result_set) == len_complement_result_set


def check_as_string(variable_values, reference: str):
    filter = Query('query', StartWith(variable_values))
    assert filter.as_string() == reference


def test_eq_predicate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')

    run_evaluation(initial_source_log, 'activity_a', 4, 3)
    check_as_string("activity_a", "(StartWith { 'activity_a' })")
    run_evaluation(initial_source_log, ['activity_a', 'activity_b'], 7, 0)
    check_as_string(['activity_a', 'activity_b'], "(StartWith { 'activity_a', 'activity_b' })")
"""