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

class InferResultSetPositioning:

    """
    Expected intersection matrix:
     m00, m01
     m10, m11

    where:
     m00 is |query_q and query_r|
     m01 is |!query_q and query_r|
     m10 is |query_q and !query_r|
     m11 is |!query_q and !query_r|
    """

    @staticmethod
    def get_positioning(query_q, query_r, m00, m01, m10, m11):
        if m00 == 0 and m11 == 0 and m01 > 0 and m10 > 0:
            return f'the query {query_q} is the complement of {query_r} and vice versa.'

        if m01 == 0 and m10 == 0 and m00 > 0 and m11 > 0:
            return f'the query {query_q} and {query_r} identify the same result set.'

        if m01 == 0 and m10 > 0 and m00 > 0 and m11 > 0:
            return f'the query {query_q} is included in query {query_r}.'

        if m10 == 0 and m01 > 0 and m00 > 0 and m11 > 0:
            return f'the query {query_r} is included in query {query_q}.'

        if m00 == 0 and m01 > 0 and m10 > 0 and m11 > 0:
            return f'the query {query_q} and {query_r} identify distinct result sets.'

        prop_q_impl_r = m00 / (m00 + m01) * 100
        prop_r_impl_q = m00 / (m00 + m10) * 100
        return (f'{query_q} --> {query_r} with {prop_q_impl_r:.3f} % '
                f'{query_r} --> {query_q} with {prop_r_impl_q:.3f} %')
