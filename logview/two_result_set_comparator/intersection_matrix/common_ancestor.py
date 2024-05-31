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

from logview.interfaces.query_registry import QueryRegistry
import pandas as pd


class CommonAncestor:

    @staticmethod
    def _get_source_log_id(result_set_id: int, query_registry: QueryRegistry) -> int:
        evaluation = query_registry.get_evaluation(result_set_id)
        source_log = evaluation['source_log']
        return id(source_log)

    @staticmethod
    def _get_number_of_queries_to_result_set(result_set_id: int, query_registry: QueryRegistry):
        initial_source_log_id = query_registry.get_initial_source_log_id()
        depth = 0
        while result_set_id != initial_source_log_id:
            result_set_id = CommonAncestor._get_source_log_id(result_set_id, query_registry)
            depth = depth + 1
        return depth

    @staticmethod
    def _bring_result_set_up_by(result_set_id: int, query_registry: QueryRegistry, steps: int) -> int:
        initial_source_log_id = query_registry.get_initial_source_log_id()
        while steps > 0 and result_set_id != initial_source_log_id:
            result_set_id = CommonAncestor._get_source_log_id(result_set_id, query_registry)
            steps = steps - 1
        return result_set_id

    @staticmethod
    def get_common_ancestor(result_set_q: pd.DataFrame, result_set_r: pd.DataFrame, query_registry: QueryRegistry):
        result_set_q_id = id(result_set_q)
        result_set_r_id = id(result_set_r)

        delta = (CommonAncestor._get_number_of_queries_to_result_set(result_set_q_id, query_registry) -
                 CommonAncestor._get_number_of_queries_to_result_set(result_set_r_id, query_registry))

        shallower_result_set_id = result_set_r_id if delta > 0 else result_set_q_id
        deeper_result_set_id = result_set_q_id if delta > 0 else result_set_r_id
        deeper_result_set_id = CommonAncestor._bring_result_set_up_by(deeper_result_set_id, query_registry,
                                                                      abs(delta))

        initial_source_log_id = query_registry.get_initial_source_log_id()
        while shallower_result_set_id != deeper_result_set_id and \
                shallower_result_set_id != initial_source_log_id and \
                deeper_result_set_id != initial_source_log_id:
            shallower_result_set_id = CommonAncestor._get_source_log_id(shallower_result_set_id, query_registry)
            deeper_result_set_id = CommonAncestor._get_source_log_id(deeper_result_set_id, query_registry)

        if deeper_result_set_id == initial_source_log_id or shallower_result_set_id == initial_source_log_id:
            return query_registry.get_initial_source_log()

        evaluation = query_registry.get_evaluation(shallower_result_set_id)
        return evaluation['result_set']


