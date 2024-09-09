# -*- coding: utf-8 -*-
# coding:=utf-8

from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, DurationWithin
from tests.test_cases.log_test_reader import LogTestReader


def run_evaluation(log, min_duration, max_duration, len_result_set, len_complement_result_set):
    query_evaluator = QueryEvaluatorOnDataFrame()
    filter = Query('query', DurationWithin(min_duration, max_duration))
    result_set, complement_result_set = query_evaluator.evaluate(log, filter)
    assert len(result_set) == len_result_set
    assert len(complement_result_set) == len_complement_result_set


def check_as_string(min_duration, max_duration, reference: str):
    filter = Query('query', DurationWithin(min_duration, max_duration))
    assert filter.as_string() == reference


def test_eq_predicate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')

    hour_in_sec = 60  * 60
    run_evaluation(initial_source_log, 1 * hour_in_sec, 2 * hour_in_sec, 5, 2)
    check_as_string(1 * hour_in_sec, 2 * hour_in_sec, "(DurationWithin [3600, 7200])")
    run_evaluation(initial_source_log, 0 * hour_in_sec, 1 * hour_in_sec, 4, 3)
    check_as_string(0 * hour_in_sec, 1 * hour_in_sec, "(DurationWithin [0, 3600])")
