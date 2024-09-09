# -*- coding: utf-8 -*-
# coding:=utf-8

import pytest
from log_view.two_result_set_comparator.intersection_matrix.intersection_matrix import IntersectionMatrix
from log_view.query_registry import QueryRegistryImpl
from log_view.query_evaluator.query_evaluator_on_dataframe import QueryEvaluatorOnDataFrame
from log_view.predicate import Query, EqToConstant
from tests.test_cases.log_test_reader import LogTestReader
import copy
import pandas as pd


def evaluate_query(name, query_registry, log, query) -> (pd.DataFrame, pd.DataFrame):
    query_evaluator = QueryEvaluatorOnDataFrame()
    log_q, log_not_q = query_evaluator.evaluate(log, query)
    log_q.name = name
    evaluation = {'query': copy.copy(query), 'source_log': log, 'result_set': log_q, 'complement_result_set': log_not_q}
    query_registry.register_evaluation(id(log_q), evaluation)
    return log_q, log_not_q


def test_common_ancestor():
    initial_source_log = LogTestReader.read_log('intersection_matrix_test_case.csv')

    query_registry = QueryRegistryImpl()
    query_registry.set_initial_source_log(initial_source_log)

    query_q = Query("query_q", EqToConstant("Var1", [1, 2, 3]))
    result_set_q, _ = evaluate_query('result_set_q', query_registry, initial_source_log, query_q)

    query_r = Query("query_r", EqToConstant("Var1", [1, 4, 5]))
    result_set_r, _ = evaluate_query('result_set_r', query_registry, initial_source_log, query_r)

    intersection_matrix = IntersectionMatrix()
    result = intersection_matrix.get_properties(result_set_q, result_set_r, query_registry)

    intersection_matrix = result['intersection_matrix']
    assert intersection_matrix.at['q and r', 'Intersection Count'] == 1
    assert intersection_matrix.at['q and !r', 'Intersection Count'] == 2
    assert intersection_matrix.at['!q and r', 'Intersection Count'] == 2
    assert intersection_matrix.at['!q and !r', 'Intersection Count'] == 1

