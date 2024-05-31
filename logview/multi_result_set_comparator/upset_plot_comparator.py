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

import pandas as pd
import warnings

from logview.interfaces import MultiResultSetsComparator
from logview.predicate.query import Query
from upsetplot import UpSet
from upsetplot import from_contents
from tabulate import tabulate


class UpSetPlotComparator(MultiResultSetsComparator):

    case_id_glue = 'case:concept:name'

    @staticmethod
    def _print_queries(result_sets: [(Query, pd.DataFrame)]):
        data = {'query name': [], 'predicates': []}
        for result_set in result_sets:
            data['query name'].append(result_set[0].get_name())
            data['predicates'].append(result_set[0].as_string())
        print(tabulate( pd.DataFrame(data), headers='keys', tablefmt='psql'))

    def get_properties(self, result_sets: [(Query, pd.DataFrame)]):
        if len(result_sets) <= 1:
            warnings.warn(message="At least two result sets must be provided to UpSetPlot")
            return

        contents = {}
        for result in result_sets:
            query_str = result[0].get_name()
            case_ids = result[1][UpSetPlotComparator.case_id_glue].unique()
            contents[query_str] = list(case_ids)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.filterwarnings("ignore", category=FutureWarning)
            test_up = from_contents(contents)
            upset_obj = UpSet(test_up, subset_size='count', show_counts=True)
            upset_obj.plot()

        UpSetPlotComparator._print_queries(result_sets)

