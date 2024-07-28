from logview.interfaces import Predicate
import pandas as pd

class MinAggregate(Predicate):
    def __init__(self, attribute_key, group_by=None):
        self.min_column = attribute_key
        self.group_by = group_by or []

    def evaluate(self, log: pd.DataFrame) -> pd.DataFrame:
        if self.group_by:
            return log.groupby(self.group_by)[self.min_column].min().reset_index()
        else:
            min_value = log[self.min_column].min()
            return pd.DataFrame({self.min_column: [min_value]})

    def as_string(self) -> str:
        if self.group_by:
            group_by_str = ", ".join(self.group_by)
            return f'Min of {self.min_column} grouped by {group_by_str}'
        else:
            return f'Min of {self.min_column}'
