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
from tabulate import tabulate
import pandas as pd
import random


class RandomExampleRetriever(ResultSetCharacterizer):

    case_id_glue = 'case:concept:name'

    def __init__(self, samples: int = 1, verbose: bool = True):
        self.samples = samples
        self.verbose = verbose

    def _retrieve_samples_from_log(self, log: pd.DataFrame, valid_items):
        if len(valid_items) == 0:
            return None
        if len(valid_items) <= self.samples:
            return log[log[RandomExampleRetriever.case_id_glue].isin(valid_items)]
        else:
            random_samples = random.sample([*valid_items], self.samples)
            return log[log[RandomExampleRetriever.case_id_glue].isin(random_samples)]

    @staticmethod
    def _print_properties(header: str, df: pd.DataFrame):
        if df is not None:
            print(header)
            case_ids = set(df[RandomExampleRetriever.case_id_glue].unique())
            for case_id in case_ids:
                example = df[df[RandomExampleRetriever.case_id_glue] == case_id]
                print(tabulate(example, headers='keys', tablefmt='psql'))

    def get_properties(self, result_set: pd.DataFrame, reference_log: pd.DataFrame):
        result_set_items = set(result_set[RandomExampleRetriever.case_id_glue].unique())
        reference_log_items = set(reference_log[RandomExampleRetriever.case_id_glue].unique())
        items_in_common = result_set_items.intersection(reference_log_items)

        only_result_set_items = result_set_items.difference(items_in_common)
        t1 = self._retrieve_samples_from_log(result_set, only_result_set_items)
        only_reference_log_items = reference_log_items.difference(items_in_common)
        t2 = self._retrieve_samples_from_log(reference_log, only_reference_log_items)
        t3 = self._retrieve_samples_from_log(reference_log, items_in_common)

        RandomExampleRetriever._print_properties(f'Sample from {result_set.name}', t1)
        RandomExampleRetriever._print_properties(f'Sample from {reference_log.name}', t2)
        RandomExampleRetriever._print_properties(f'Sample in {result_set.name} and {reference_log.name}', t3)
