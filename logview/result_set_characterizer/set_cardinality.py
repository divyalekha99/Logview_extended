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


class SetCardinality(ResultSetCharacterizer):

    case_id_glue = 'case:concept:name'

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    @staticmethod
    def _print_properties( result_set: pd.DataFrame, reference_log: pd.DataFrame, result: dict):
        print(f"Number of case_id in {result_set.name}: {result[result_set.name]}")
        print(f"Number of case_id in {reference_log.name}: {result[reference_log.name]}")

    def get_properties(self, result_set: pd.DataFrame, reference_log: pd.DataFrame) -> dict:
        result = {result_set.name: len(result_set[SetCardinality.case_id_glue].unique()),
                  reference_log.name: len(reference_log[SetCardinality.case_id_glue].unique())}
        if self.verbose:
            SetCardinality._print_properties(result_set, reference_log, result)
        return result
