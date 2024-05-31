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

from logview.log_view import LogView
from logview.result_set_characterizer import SetCardinality, SummaryStatistics, RandomExampleRetriever
from logview.two_result_set_comparator.intersection_matrix import IntersectionMatrix
from logview.query_evaluator import QueryEvaluatorOnDataFrame
from logview.query_registry import QueryRegistryImpl
from logview.multi_result_set_comparator import UpSetPlotComparator
import pandas as pd


class LogViewBuilder:

    @staticmethod
    def build_log_view(initial_source_log: pd.DataFrame) -> LogView:
        logview = LogView(QueryEvaluatorOnDataFrame(), QueryRegistryImpl(), initial_source_log)
        logview.attach_result_set_characterizer('set-cardinality', SetCardinality())
        logview.attach_result_set_characterizer('summary-statistics', SummaryStatistics())
        logview.attach_result_set_characterizer('random-example-retriever', RandomExampleRetriever())
        logview.attach_two_result_sets_comparator('intersection-matrix', IntersectionMatrix())
        logview.attach_multiquery_comparator('upsetplot', UpSetPlotComparator())
        return logview
