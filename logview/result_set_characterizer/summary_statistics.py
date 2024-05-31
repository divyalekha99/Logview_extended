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

from logview.interfaces import ResultSetCharacterizer
import pandas as pd
from tabulate import tabulate

class SummaryStatistics(ResultSetCharacterizer):

    case_id_glue = 'case:concept:name'

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.statistics = ['mean', 'std', 'min', 'max']

    def _compute_summary_statistics(self, result_set: pd.DataFrame):
        numeric_summary_reference = result_set.describe()
        numeric_summary_reference = numeric_summary_reference.loc[self.statistics]
        numeric_summary_reference = numeric_summary_reference.loc[:,~numeric_summary_reference.columns.str.contains('index')]
        return numeric_summary_reference

    def _print_properties(self, name: str, numeric_summary_reference: pd.DataFrame):
        print(f'Summary statistics of {name}')
        print(tabulate(numeric_summary_reference, headers='keys', tablefmt='psql'))

    def get_properties(self, result_set: pd.DataFrame, reference_log: pd.DataFrame):
        result_set_statistics = self._compute_summary_statistics(result_set)
        reference_log_statistics = self._compute_summary_statistics(reference_log)
        if self.verbose:
            self._print_properties(result_set.name, result_set_statistics)
            self._print_properties(reference_log.name, reference_log_statistics)

        return {result_set.name: result_set_statistics, reference_log.name: reference_log_statistics}
