import pytest
from django.contrib.staticfiles.testing import LiveServerTestCase
from playwright.sync_api import Page

from .live.robots import RobotManager


@pytest.fixture()
def robot_manager(request, page: Page):
    if not issubclass(request.cls, LiveServerTestCase):
        raise RuntimeError("This fixture may only be used on LiveServerTestCase; was on " + repr(request.cls))

    page.set_default_timeout(10000)

    manager = RobotManager(page, server_url=request.cls.live_server_url)
    request.cls.manager = manager
