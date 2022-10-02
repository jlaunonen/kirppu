import typing

import pytest

from .robots import RobotManager


@pytest.mark.usefixtures("robot_manager")
class RobotLiveTest:
    # Set by robot_manager fixture.
    manager: typing.ClassVar[RobotManager]
