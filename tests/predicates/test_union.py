# -*- coding: utf-8 -*-
# coding:=utf-8

from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, EqToConstant, Union
from tests.test_cases.log_test_reader import LogTestReader


def test_union_predicate():
    initial_source_log = LogTestReader.read_log('predicates_test_case.csv')
    query_evaluator = QueryEvaluatorOnDataFrame()

    var1_eq_to = EqToConstant('Var1', {2, 1})
    var2_eq_to = EqToConstant('Var2', 1.3)

    filter = Query('query', Union([var1_eq_to, var2_eq_to]))
    result_set, complement_result_set = query_evaluator.evaluate(initial_source_log, filter)

    assert len(result_set) == 6
    assert len(complement_result_set) == 1
    assert filter.as_string() == '(Var1 in { 1, 2 }) or (Var2 in { 1.3 })'


