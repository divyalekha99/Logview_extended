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

from logview.interfaces.predicate import Predicate
from logview.interfaces import ResultSetCharacterizer
import pandas as pd
from tabulate import tabulate


class PropertiesEvaluator(ResultSetCharacterizer):

    case_id_glue = 'case:concept:name'

    def __init__(self, properties: list[Predicate]):
        self.properties = properties

    def evaluate_property(self, log: pd.DataFrame) -> []:
        result = []
        initial_num_case_ids = len(log[PropertiesEvaluator.case_id_glue].unique())
        for property in self.properties:
            current_result = property.evaluate(log)
            num_case_ids = len(current_result[PropertiesEvaluator.case_id_glue].unique())
            result_item = (num_case_ids, round(num_case_ids / initial_num_case_ids, 3))
            result.append(result_item)
        return result

    def get_properties(self, result_set: pd.DataFrame, reference_log: pd.DataFrame):
        data = {result_set.name: self.evaluate_property(result_set),
                reference_log.name: self.evaluate_property(reference_log)}

        index_values = [property.as_string() for property in self.properties]
        df = pd.DataFrame(data, index=index_values)
        print(tabulate(df, headers='keys', tablefmt='psql'))
