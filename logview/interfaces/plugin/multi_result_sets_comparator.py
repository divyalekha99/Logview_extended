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
from logview.interfaces import Predicate
import pandas as pd


class MultiResultSetsComparator(ABC):

    @abstractmethod
    def get_properties(self, result_sets: [(Predicate, pd.DataFrame)]) -> Optional[dict]:
        """
        A component comparing the given queries and result sets with the final intent of extracting some interesting
        properties.
        :param result_sets: A list of tuples where the first item is a Predicate and the second a result set.
        :return: a dictionary (optional)
        """
