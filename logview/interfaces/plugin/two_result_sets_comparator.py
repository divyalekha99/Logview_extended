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

from abc import ABC, abstractmethod
from typing import Optional
from logview.interfaces.query_registry import QueryRegistry
import pandas as pd


class TwoResultSetsComparator(ABC):
    """
    The Two Result Sets Comparator aims to help analysts compare any two result sets recorded in the registry and
    infer dependencies between the queries that generated them.
    """
    @abstractmethod
    def get_properties(self, result_set_q: pd.DataFrame, result_set_r: pd.DataFrame, query_registry: QueryRegistry) -> Optional[dict]:
        """
        Return (optionally) a dictionary of properties highlighting the dependencies between the queries that
        generated the given result sets.
        :param result_set_q: A result set as a pandas DataFrame.
        :param result_set_r: A result set as a pandas DataFrame.
        :param query_registry A query registry.
        :return: dictionary.
        """
