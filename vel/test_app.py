# TO run the tests, run the following command in the terminal:
# pytest test_app.py
# The tests will run only if selenium is installed.

import pytest
from dash.testing.application_runners import import_app
from .VelPredicate import VelPredicate
from .Vel import Vel
from dash import Dash
import os

@pytest.fixture
def vel_instance():
    """
    Fixture to create an instance of the Vel class for testing.
    """
    vel = Vel(logName='Road_Traffic_Fine_Management_Process')
    return vel

@pytest.fixture
def dash_duo_app(vel_instance, dash_duo):
    """
    Fixture to create the Dash app from the Vel class.
    """
    app = vel_instance.Query_Builder_v5()
    dash_duo.start_server(app)

    yield dash_duo

def test_initialize_log_view(vel_instance):
    """
    Test that the log view is correctly initialized.
    """
    log_view = vel_instance.initLogView()
    assert log_view is not None, "Log view should be initialized"
    assert isinstance(log_view, object), "Log view should be a valid object"

def test_change_default_names(vel_instance):
    """
    Test that the default column names can be changed.
    """
    new_case_id_col = "New Case ID"
    new_activity_col = "New Activity"
    new_timestamp_col = "New Timestamp"

    vel_instance.changeDefaultNames(new_case_id_col, new_activity_col, new_timestamp_col)

    assert vel_instance.CASE_ID_COL == new_case_id_col, "Case ID column should be updated"
    assert vel_instance.ACTIVITY_COL == new_activity_col, "Activity column should be updated"
    assert vel_instance.TIMESTAMP_COL == new_timestamp_col, "Timestamp column should be updated"

# def test_set_log(dash_duo_app):
#     """
#     Test that the DataTable is rendered in the Set Log UI.
#     """
#     dash_duo_app.wait_for_element_by_id('datatable-interactivity', timeout=30)

#     table = dash_duo_app.find_element('#datatable-interactivity')
#     assert table is not None, "DataTable should be rendered"


def test_add_query_tab(dash_duo_app):
    """
    Test that a new query tab can be added.
    """
    dash_duo_app.wait_for_element_by_id('add-query-button', timeout=30)

    add_query_button = dash_duo_app.find_element('#add-query-button')
    add_query_button.click()

    tabs = dash_duo_app.find_elements('.ant-tabs-tab')
    assert len(tabs) > 1, "A new query tab should be added"


# def test_assign_roles_and_confirm(dash_duo_app):
#     """
#     Test the role assignment functionality.
#     """
#     dash_duo_app.wait_for_element_by_id('assign-roles-button', timeout=30)
    
#     assign_button = dash_duo_app.find_element('#assign-roles-button')
#     assign_button.click()

#     # Check that the role dropdowns appear in the modal
#     dash_duo_app.wait_for_element_by_id('role-assignment-container', timeout=5)
#     dropdowns = dash_duo_app.find_elements('.ant-select-selector')
    
#     assert len(dropdowns) > 0, "There should be dropdowns in the modal for assigning roles"
    
#     # Confirm role assignment and close modal
#     confirm_button = dash_duo_app.find_element('.ant-btn-primary')
#     confirm_button.click()

#     modal = dash_duo_app.find_element('#modal')
#     assert not modal.is_displayed(), "Modal should close after role assignment"

def test_summary_view(dash_duo_app):
    """
    Test if the Query Summary View can be opened.
    """
    dash_duo_app.wait_for_element_by_id('open-drawer-button', timeout=30)

    summary_button = dash_duo_app.find_element('#open-drawer-button')
    summary_button.click()

    dash_duo_app.wait_for_element_by_id('summary-content', timeout=5)
    summary_content = dash_duo_app.find_element('#summary-content')

    assert summary_content is not None, "Summary view should display executed queries"


