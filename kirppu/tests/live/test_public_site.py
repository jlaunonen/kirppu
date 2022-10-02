# -*- coding: utf-8 -*-
import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from kirppu.models import Event

from ..factories import EventFactory, ItemTypeFactory, UserFactory
from . import RobotLiveTest
from .robots.public import BoxListRobot, HomeRobot, ItemListRobot


@pytest.mark.web
class HomeTests(RobotLiveTest, StaticLiveServerTestCase):
    page: HomeRobot

    def setUp(self) -> None:
        super().setUp()
        self.page = HomeRobot(self.manager)
        self.u = UserFactory()

    def test_home_login_logout(self):
        """
        Login and logout in home view without any events.
        """
        self.page.do_login(self.u.username, UserFactory.DEFAULT_PASSWORD)
        self.page.assert_login_name(first_name=self.u.first_name)
        self.page.do_logout()

    def test_home_event_login(self):
        """
        Navigate to item list in an event.
        :return:
        """
        event_mdl: Event = EventFactory()
        with self.page.nav_event(event_mdl) as event_view:
            login_view, items_view = event_view.nav_items_with_login()
            with login_view:
                login_view.enter(self.u.username, UserFactory.DEFAULT_PASSWORD)
                login_view.click_login()
                login_view.pop_self()

            with items_view:
                items_view.accept_terms()
                items_view.back()


@pytest.mark.web
class ItemRegistration(RobotLiveTest, StaticLiveServerTestCase):
    page: ItemListRobot

    def setUp(self) -> None:
        super().setUp()
        self.u = UserFactory()
        self.event = EventFactory()
        self.types = [
            ItemTypeFactory(event=self.event),
            ItemTypeFactory(event=self.event),
        ]

        self.page = (
            HomeRobot(self.manager)
            .do_login(self.u.username, UserFactory.DEFAULT_PASSWORD)
            .nav_event(self.event)
            .add_to_stack()
            .nav_items()
            .add_to_stack()
        )

    def test_add_single(self):
        (
            self.page
            .accept_terms()
            .enter_name("Test item")
            .enter_price("2.50")
            .set_type(self.types[0].title)
            .submit()
            .check_tag_count(1)
            .check_has_tag("Test item")
        )

    def test_add_suffix(self):
        (
            self.page
            .accept_terms()
            .enter_name("Test item")
            .enter_suffix("1-10")
            .enter_price("1.50")
            .set_type(self.types[0].title)
            .submit()
            .check_tag_count(10)
        )


@pytest.mark.web
class BoxRegistration(RobotLiveTest, StaticLiveServerTestCase):
    page: BoxListRobot

    def setUp(self):
        super().setUp()
        self.u = UserFactory()
        self.event = EventFactory()
        self.types = [
            ItemTypeFactory(event=self.event),
            ItemTypeFactory(event=self.event),
        ]

        self.page = (
            HomeRobot(self.manager)
            .do_login(self.u.username, UserFactory.DEFAULT_PASSWORD)
            .nav_event(self.event)
            .add_to_stack()
            .nav_boxes()
            .add_to_stack()
        )

    def test_add_single(self):
        (
            self.page
            .accept_terms()
            .enter_description("Test box")
            .enter_pricing("2.50")
            .enter_item_count(5)
            .set_type(self.types[0].title)
            .submit()
            .check_box_count(1)
            .check_has_box("Test box")
        )

    def test_add_bundle(self):
        (
            self.page
            .accept_terms()
            .enter_description("Bundle box")
            .enter_pricing("4.00", 3)
            .enter_item_count(5)
            .set_type(self.types[0].title)
            .submit()
            .check_box_count(1)
            .check_has_box("Bundle box")
        )
