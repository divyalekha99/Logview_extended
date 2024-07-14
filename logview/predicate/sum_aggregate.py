from logview.interfaces import Predicate
from typing import Union, Set
import pm4py
import pandas as pd

class SumAggregate(Predicate):
    # def __init__(self, attribute_key: str):
    #     self.attribute_key = attribute_key

    # def evaluate(self, log: pd.DataFrame) -> pd.DataFrame:
    #     grouped_sum = log.groupby(['Case ID','case:concept:name', 'concept:name', 'Activity'])[self.attribute_key].sum().reset_index()
    #     return grouped_sum
    

    # def as_string(self) -> str:
    #     return f'Sum({self.attribute_key})'
# class SumAggregate:
    def __init__(self, sum_column, group_by=None):
        self.sum_column = sum_column
        self.group_by = group_by or []

    def evaluate(self, log: pd.DataFrame) -> pd.DataFrame:
        if self.group_by:
            # Group by specified columns and sum
            return log.groupby(self.group_by)[self.sum_column].sum().reset_index()
        else:
            # Return a DataFrame with total sum if no group_by columns are specified
            total_sum = log[self.sum_column].sum()
            # Create a DataFrame with the sum as its only row
            return pd.DataFrame({self.sum_column: [total_sum]})

    def as_string(self) -> str:
        if self.group_by:
            group_by_str = ", ".join(self.group_by)
            return f'Sum of {self.sum_column} grouped by {group_by_str}'
        else:
            return f'Sum of {self.sum_column}'