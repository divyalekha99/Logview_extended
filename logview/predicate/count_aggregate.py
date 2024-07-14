from logview.interfaces import Predicate
import pandas as pd

class CountAggregate(Predicate):
    def __init__(self, count_column, group_by=None):
        """
        Initializes the CountAggregate object.
        :param count_column: The column to count occurrences in.
        :param group_by: Optional list of columns to group by before counting.
        """
        self.count_column = count_column
        self.group_by = group_by or []

    def evaluate(self, log: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluates the count of occurrences, optionally grouped by specified columns.
        :param log: The DataFrame to perform the aggregation on.
        :return: A DataFrame with the count of occurrences.
        """
        if self.group_by:
            # Group by specified columns and count
            return log.groupby(self.group_by).size().reset_index(name=f'Count of {self.count_column}')
        else:
            # Return a DataFrame with total count if no group_by columns are specified
            total_count = log[self.count_column].count()
            # Create a DataFrame with the count as its only row
            return pd.DataFrame({f'Count of {self.count_column}': [total_count]})

    def as_string(self) -> str:
        """
        Returns a string representation of the CountAggregate object.
        """
        if self.group_by:
            group_by_str = ", ".join(self.group_by)
            return f'Count of {self.count_column} grouped by {group_by_str}'
        else:
            return f'Count of {self.count_column}'