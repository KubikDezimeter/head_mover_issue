from unittest.mock import MagicMock

import pytest
from humanoid_league_team_communication.converter.robocup_protocol_converter import RobocupProtocolConverter


def test_setup_of_mappings(snapshot):
    converter = RobocupProtocolConverter()
    assert converter.team_mapping == snapshot
    assert converter.role_mapping == snapshot
    assert converter.action_mapping == snapshot
    assert converter.side_mapping == snapshot


def test_setup_of_to_message_converter(snapshot, to_message_mock):
    RobocupProtocolConverter()

    to_message_mock.assert_called_once()
    args = to_message_mock.mock_calls[0].kwargs
    assert args == snapshot


def test_setup_of_from_message_converter(snapshot, from_message_mock):
    RobocupProtocolConverter()

    from_message_mock.assert_called_once()
    args = from_message_mock.mock_calls[0].kwargs
    assert args == snapshot


def test_maps_convert_functions(to_message_mock, from_message_mock):
    to_message_mock.return_value.convert.return_value = 'message'
    from_message_mock.return_value.convert.return_value = 'team_data'

    converter = RobocupProtocolConverter()

    assert converter.convert_to_message() == 'message'
    assert converter.convert_from_message() == 'team_data'


@pytest.fixture
def to_message_mock(mocker) -> MagicMock:
    return mocker.patch(
        "humanoid_league_team_communication.converter.robocup_protocol_converter.StateToMessageConverter")


@pytest.fixture
def from_message_mock(mocker) -> MagicMock:
    return mocker.patch(
        "humanoid_league_team_communication.converter.robocup_protocol_converter.MessageToTeamDataConverter")
