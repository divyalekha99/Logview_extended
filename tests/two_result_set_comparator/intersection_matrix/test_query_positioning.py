# -*- coding: utf-8 -*-
# coding:=utf-8

import pytest
from log_view.two_result_set_comparator.intersection_matrix.infer_result_set_positioning import InferResultSetPositioning


def test_common_ancestor():
    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 0, 1, 1, 0)
    assert query_positioning == 'the query q is the complement of r and vice versa.'

    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 0, 1, 1, 1)
    assert query_positioning == 'the query q and r identify distinct result sets.'

    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 1, 0, 0, 1)
    assert query_positioning == 'the query q and r identify the same result set.'

    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 1, 1, 0, 1)
    assert query_positioning == 'the query r is included in query q.'

    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 1, 0, 1, 1)
    assert query_positioning == 'the query q is included in query r.'

    query_positioning = InferResultSetPositioning.get_positioning('q', 'r', 1, 2, 1, 1)
    assert query_positioning == 'q --> r with 33.333 % r --> q with 50.000 %'
