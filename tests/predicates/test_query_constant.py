# -*- coding: utf-8 -*-
# coding:=utf-8

from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, EqToConstant
from tests.test_cases.log_test_reader import LogTestReader


def test_eq_predicate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')
    query_evaluator = QueryEvaluatorOnDataFrame()

    filter = Query('query', [EqToConstant('Var1', {2, 1}), EqToConstant('Var2', 1.2)])
    result_set, complement_result_set = query_evaluator.evaluate(initial_source_log, filter)

    assert len(result_set) == 3
    assert len(complement_result_set) == 4
    assert filter.as_string() == '(Var1 in { 1, 2 }) and (Var2 in { 1.2 })'
