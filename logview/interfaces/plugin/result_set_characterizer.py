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
import pandas as pd


class ResultSetCharacterizer(ABC):
    """
    The goal of a ResultSet Characterize component is to characterize a result set L by comparing it to a reference log.
    """
    @abstractmethod
    def get_properties(self, result_set: pd.DataFrame, reference_log: pd.DataFrame) -> Optional[dict]:
        """
        Return (optionally) a dictionary of properties characterizing the given result set.
        :param result_set: A result set as a pandas DataFrame.
        :param reference_log A reference log as a pandas DataFrame.
        :return: dictionary.
        """
