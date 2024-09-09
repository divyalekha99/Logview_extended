# -*- coding: utf-8 -*-
# coding:=utf-8

import pytest
from log_view.two_result_set_comparator.intersection_matrix.common_ancestor import CommonAncestor
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
    initial_source_log = LogTestReader.read_log('common_ancestor_test_case.csv')

    query_registry = QueryRegistryImpl()
    query_registry.set_initial_source_log(initial_source_log)

    initial_filter = Query('query', EqToConstant("Var3", [1]))
    source_log, _ = evaluate_query('source_log', query_registry, initial_source_log, initial_filter)
    assert len(source_log) == 2

    common_ancestor = CommonAncestor.get_common_ancestor(initial_source_log, source_log, query_registry)
    #query_to_common_ancestor = query_registry.get_query_from_source_log_to_result_set(initial_source_log, common_ancestor)
    assert id(common_ancestor) == id(initial_source_log)
    #assert query_to_common_ancestor.as_string() == ''

    # first analysis
    query_a = Query('query', EqToConstant("Var1", [1]))
    result_set_a, _ = evaluate_query('result_set_a', query_registry, source_log, query_a)
    common_ancestor = CommonAncestor.get_common_ancestor(result_set_a, source_log, query_registry)
    #query_to_common_ancestor = query_registry.get_query_from_source_log_to_result_set(initial_source_log, common_ancestor)
    assert id(common_ancestor) == id(source_log)
    #assert query_to_common_ancestor.as_string() == '(Var3 in { 1 })'

    # second analysis
    # refinement of query a
    query_b = Query('query', EqToConstant("Var2", [2]))
    result_set_b, _ = evaluate_query('result_set_b', query_registry, result_set_a, query_b)

    query_c = Query('query', EqToConstant("Var2", [2]))
    query_d = Query('query', EqToConstant("Var1", [1]))
    result_set_c, _ = evaluate_query('result_set_c', query_registry, source_log, query_c)
    result_set_d, _ = evaluate_query('result_set_d', query_registry, result_set_c, query_d)

    common_ancestor = CommonAncestor.get_common_ancestor(result_set_b, result_set_d, query_registry)
    #query_to_common_ancestor = query_registry.get_query_from_source_log_to_result_set(initial_source_log, common_ancestor)

    #query_to_result_set_b = query_registry.get_query_from_source_log_to_result_set(common_ancestor, result_set_b)
    #query_to_result_set_d = query_registry.get_query_from_source_log_to_result_set(common_ancestor, result_set_d)

    assert id(source_log) == id(common_ancestor)
    #assert query_to_common_ancestor.as_string() == '(Var3 in { 1 })'
    #assert query_to_result_set_b.as_string() == '(Var1 in { 1 }) and (Var2 in { 2 })'
    #assert query_to_result_set_d.as_string() == '(Var1 in { 1 }) and (Var2 in { 2 })'
