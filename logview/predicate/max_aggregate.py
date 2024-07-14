from logview.interfaces import Predicate
import pandas as pd


class MaxAggregate(Predicate):
    def __init__(self, max_column, group_by=None):
        self.max_column = max_column
        self.group_by = group_by or []

    def evaluate(self, log: pd.DataFrame) -> pd.DataFrame:
        if self.group_by:
            return log.groupby(self.group_by)[self.max_column].max().reset_index()
        else:
            max_value = log[self.max_column].max()
            return pd.DataFrame({self.max_column: [max_value]})

    def as_string(self) -> str:
        if self.group_by:
            group_by_str = ", ".join(self.group_by)
            return f'Max of {self.max_column} grouped by {group_by_str}'
        else:
            return f'Max of {self.max_column}'