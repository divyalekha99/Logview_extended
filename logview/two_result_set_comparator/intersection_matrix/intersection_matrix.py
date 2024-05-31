"""
    This file is part of LogView.

    LogView is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    LogView is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with LogView. If not, see <https://www.gnu.org/licenses/>.
"""

from tabulate import tabulate
from logview.interfaces import TwoResultSetsComparator
from logview.interfaces.query_registry import QueryRegistry
from logview.predicate import Query
from logview.two_result_set_comparator.intersection_matrix.common_ancestor import CommonAncestor
from logview.two_result_set_comparator.intersection_matrix.infer_result_set_positioning import InferResultSetPositioning
import pandas as pd
import copy


class IntersectionMatrix(TwoResultSetsComparator):

    case_id_glue = 'case:concept:name'

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    @staticmethod
    def _get_predicates_from_source_log_to_result_set(source_log: pd.DataFrame, result_set: pd.DataFrame,
                                                      query_registry: QueryRegistry):
        source_log_id = id(source_log)
        result_set_id = id(result_set)

        predicates = []
        while result_set_id != source_log_id:
            evaluation = query_registry.get_evaluation(result_set_id)
            predicates.insert(0, copy.copy(evaluation['query']))
            result_set_id = id(evaluation['source_log'])
        return predicates

    @staticmethod
    def _create_domain_conditions(common_ancestor: pd.DataFrame, result_set_q: pd.DataFrame,
                                  result_set_r: pd.DataFrame, query_registry: QueryRegistry):

        initial_source_log = query_registry.get_initial_source_log()
        predicates_to_common_ancestor = IntersectionMatrix._get_predicates_from_source_log_to_result_set(initial_source_log, common_ancestor, query_registry)
        query_to_common_ancestor = Query('query_common_ancestor', predicates_to_common_ancestor)
        predicates_to_result_set_q = IntersectionMatrix._get_predicates_from_source_log_to_result_set(common_ancestor, result_set_q, query_registry)
        query_to_result_set_q = Query('query_q', predicates_to_result_set_q)
        predicates_to_result_set_r = IntersectionMatrix._get_predicates_from_source_log_to_result_set(common_ancestor, result_set_r, query_registry)
        query_to_result_set_r = Query('query_r', predicates_to_result_set_r)

        return {query_to_common_ancestor.name: query_to_common_ancestor,
                'query_q': query_to_result_set_q,
                'query_r': query_to_result_set_r}

    @staticmethod
    def _compute_intersection_matrix(common_ancestor: pd.DataFrame, result_set_q: pd.DataFrame, result_set_r: pd.DataFrame):
        items_in_common_ancestor = set(common_ancestor[IntersectionMatrix.case_id_glue].unique())
        log_q_items = set(result_set_q[IntersectionMatrix.case_id_glue].unique())
        log_r_items = set(result_set_r[IntersectionMatrix.case_id_glue].unique())
        log_not_q_items = items_in_common_ancestor.difference(log_q_items)
        log_not_r_items = items_in_common_ancestor.difference(log_r_items)

        q_and_r = log_q_items.intersection(log_r_items)
        q_and_not_r = log_q_items.difference(log_r_items)
        r_and_not_q = log_r_items.difference(log_q_items)
        not_q_and_not_r = log_not_q_items.intersection(log_not_r_items)

        intersection_matrix = {'q and r': len(q_and_r),
                               'q and !r': len(q_and_not_r),
                               '!q and r': len(r_and_not_q),
                               '!q and !r': len(not_q_and_not_r)}
        return intersection_matrix

    @staticmethod
    def _infer_query_positioning(domain_conditions: dict, intersection_matrix: dict):
        query_q_str = domain_conditions['query_q'].get_name()
        query_r_str = domain_conditions['query_r'].get_name()
        m00 = intersection_matrix['q and r']
        m01 = intersection_matrix['q and !r']
        m10 = intersection_matrix['!q and r']
        m11 = intersection_matrix['!q and !r']
        return InferResultSetPositioning.get_positioning(query_q_str, query_r_str, m00, m01, m10, m11)

    @staticmethod
    def _print_properties(common_ancestor: pd.DataFrame, result_set_q: pd.DataFrame,
                          result_set_r: pd.DataFrame, result: dict):
        print(f"Result set comparison between q: '{result_set_q.name}' and r: '{result_set_r.name}'")

        print("\nIntersection Matrix:")
        print(tabulate(result['intersection_matrix'], headers='keys', tablefmt='psql'))

        print("\nAnalysis Context:")
        domain_conditions = result['analysis_context']
        print(f"\tQuery from initial log to common ancestor '{common_ancestor.name}': {domain_conditions['query_common_ancestor'].as_string()} ")
        print(f"\tQueries from common ancestor to '{result_set_q.name}': {domain_conditions['query_q'].as_string()} ")
        print(f"\tQueries from common ancestor to '{result_set_r.name}': {domain_conditions['query_r'].as_string()} ")

        print(f"\nQuery Dependency Probability:\n {result['result_set_positioning']}")

    def get_properties(self, result_set_q: pd.DataFrame, result_set_r: pd.DataFrame, query_registry: QueryRegistry) -> dict:
        common_ancestor = CommonAncestor.get_common_ancestor(result_set_q, result_set_r, query_registry)
        domain_conditions = IntersectionMatrix._create_domain_conditions(common_ancestor, result_set_q, result_set_r, query_registry)

        intersection_matrix = IntersectionMatrix._compute_intersection_matrix(common_ancestor, result_set_q, result_set_r)
        query_positioning = IntersectionMatrix._infer_query_positioning(domain_conditions, intersection_matrix)
        intersection_matrix_as_df = pd.DataFrame.from_dict(intersection_matrix, orient='index', columns=['Intersection Count'])

        result = {'analysis_context': domain_conditions,
                  'intersection_matrix': intersection_matrix_as_df,
                  'result_set_positioning': query_positioning}

        if self.verbose:
            IntersectionMatrix._print_properties(common_ancestor, result_set_q, result_set_r, result)

        return result
