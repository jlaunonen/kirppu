# -*- coding: utf-8 -*-
from __future__ import annotations

import re

# note: typing.Self is not available before Python 3.11, so don't import it directly for now.
import typing

from playwright.sync_api import Locator, Page, expect

from kirppu.models import Event

from . import RobotDsl


def click_menu_item(page: Page, name: str):
    with page.expect_request_finished():
        (
            page
            .get_by_role("navigation")
            .get_by_role("listitem")
            .filter(has=page.get_by_text(name))
            .click()
        )


class HomeRobot(RobotDsl):
    address = "/"
    expect_title = "Kirppu"

    def nav_login(self) -> LoginRobot:
        click_menu_item(self.raw, "Log in")
        return self.new_robot(LoginRobot, reset_context=True)

    def do_login(self, username, password) -> typing.Self:
        with self.nav_login() as login:
            login.enter(username, password)
            login.click_login()
            login.pop_self()
        return self

    def assert_login_name(self, first_name: str) -> typing.Self:
        expect(
            self.raw.get_by_role("listitem").filter(has=self.raw.get_by_test_id("user_actions"))
        ).to_have_text(re.compile(re.escape(first_name) + ".*"))
        return self

    def do_logout(self) -> typing.Self:
        menu = self.raw.get_by_role("listitem").filter(has=self.raw.get_by_test_id("user_actions"))
        menu.get_by_test_id("user_actions").click()
        with self.raw.expect_request_finished():
            menu.get_by_text("Log out").click()
        return self

    def nav_event(self, event: Event) -> EventRobot:
        with self.raw.expect_request_finished():
            self.raw.locator("//a[@data-currentevent][text()=%s]" % repr(event.name)).click()
        return self.new_robot(EventRobot, reset_context=True, event=event)


class LoginRobot(RobotDsl):
    address = "/accounts/login/"
    expect_title = "Login – Kirppu"

    def enter(self, username: str, password: str) -> typing.Self:
        self.enter_username(username)
        self.enter_password(password)
        return self

    def enter_username(self, username: str) -> typing.Self:
        input_field = self.raw.get_by_placeholder("Username")
        input_field.fill(username)
        return self

    def enter_password(self, password: str) -> typing.Self:
        input_field = self.raw.get_by_placeholder("Password")
        input_field.fill(password)
        return self

    def click_login(self) -> None:
        with self.raw.expect_request_finished():
            self.raw.get_by_role("button", name="Login").click()


class EventRobot(RobotDsl):
    address = "/kirppu/{event.slug}"
    expect_title = "{event.name} – Kirppu"

    def nav_items(self) -> ItemListRobot:
        """
        Go to item list. Note, must be logged in. Otherwise, the returned robot doesn't match actual view.
        """
        click_menu_item(self.raw, "Item list")
        return self.new_robot(ItemListRobot)

    def nav_items_with_login(self) -> typing.Tuple[LoginRobot, ItemListRobot]:
        click_menu_item(self.raw, "Item list")

        return (
            self.new_robot(LoginRobot),
            self.new_robot(ItemListRobot),
        )

    def nav_boxes(self) -> BoxListRobot:
        click_menu_item(self.raw, "Box list")
        return self.new_robot(BoxListRobot)

    def nav_mobile(self, as_anonymous: bool) -> MobileRobot:
        click_menu_item(self.raw, "Mobile")
        return self.new_robot(MobileRobot)

    def nav_mobile_anonymous(self) -> MobileLoginRobot:
        click_menu_item(self.raw, "Mobile")
        return self.new_robot(MobileLoginRobot)


class _ItemRobot(RobotDsl):
    def accept_terms(self) -> typing.Self:
        # checkbox
        self.raw.get_by_label("I accept").click()
        # button
        btn = self.raw.get_by_role("button", name="Accept")
        assert btn.is_visible()
        with self.raw.expect_request_finished():
            btn.click()
        assert not btn.is_visible()
        return self


class ItemListRobot(_ItemRobot):
    expect_title = "Item list – {event.name} – Kirppu"

    @property
    def form(self) -> Locator:
        return self.raw.locator("form#item-add-form")

    def check_form_empty(self) -> typing.Self:
        # Lazy check: we don't actually check whole form.
        expect(self.form.get_by_placeholder("Ranma")).to_have_value("")
        return self

    def check_has_tag(self, name: str) -> Locator:
        return self.raw.get_by_test_id("itemContainer").locator(".item_container").filter(
            has=self.raw.locator(".item_name", has_text=name)
        )

    def check_tag_count(self, count: int) -> typing.Self:
        expect(self.raw.get_by_test_id("itemContainer").locator(".item_container")).to_have_count(count)
        return self

    def enter_name(self, value: str) -> typing.Self:
        self.form.get_by_placeholder("Ranma").fill(value)
        return self

    def enter_suffix(self, value: str) -> typing.Self:
        self.form.get_by_placeholder("1 3-5").fill(value)
        return self

    def enter_price(self, value: str) -> typing.Self:
        self.form.get_by_placeholder("5", exact=True).fill(value)
        return self

    def set_small_size(self, small: bool) -> typing.Self:
        find_label = "6 cm" if small else "9 cm"
        self.form.get_by_label(find_label).get_by_role("checkbox").set_checked(True)
        return self

    def set_type(self, type_name: str) -> typing.Self:
        types = self.form.locator("//select")
        types.select_option(type_name)
        return self

    def set_adult(self, adult: bool) -> typing.Self:
        find_label = "Yes" if adult else "No"
        self.form.get_by_label(find_label).get_by_role("checkbox").set_checked(True)
        return self

    def submit(self) -> typing.Self:
        with self.raw.expect_request_finished():
            self.form.get_by_role("button", name="Add item").click()
        return self

    def clear(self) -> typing.Self:
        self.form.get_by_role("button", name="Empty").click()
        return self


class BoxListRobot(_ItemRobot):
    expect_title = "Box list – {event.name} – Kirppu"

    @property
    def form(self) -> Locator:
        return self.raw.locator("form#box-add-form")

    def check_form_empty(self) -> typing.Self:
        # Lazy check: we don't actually check whole form.
        expect(self.form.get_by_placeholder("Box full")).to_have_value("")
        return self

    def check_has_box(self, name: str) -> Locator:
        return self.raw.locator(".box_container").filter(
            has=self.raw.locator(".box_description", has_text=name)
        )

    def check_box_count(self, count: int) -> typing.Self:
        expect(self.raw.locator(".box_container")).to_have_count(count)
        return self

    def enter_description(self, value: str) -> typing.Self:
        self.form.get_by_placeholder("Box full").fill(value)
        return self

    def enter_pricing(self, price: str, per_units: int = 1) -> typing.Self:
        self.form.get_by_placeholder("5").fill(price)
        self.form.get_by_placeholder("1", exact=True).fill(str(per_units))
        return self

    def enter_item_count(self, count: int) -> typing.Self:
        self.form.get_by_placeholder("10").fill(str(count))
        return self

    def set_type(self, type_name: str) -> typing.Self:
        types = self.form.locator("//select")
        types.select_option(type_name)
        return self

    def set_adult(self, adult: bool) -> typing.Self:
        find_label = "Yes" if adult else "No"
        self.form.get_by_label(find_label).get_by_role("checkbox").set_checked(True)
        return self

    def submit(self) -> typing.Self:
        with self.raw.expect_request_finished():
            self.form.get_by_role("button", name="Add box").click()
        return self

    def clear(self) -> typing.Self:
        self.form.get_by_role("button", name="Empty").click()
        return self


class MobileRobot(RobotDsl):
    expect_title_pattern = "Item status – {event.name} – Kirppu"

    def nav_home(self) -> HomeRobot:
        click_menu_item(self.raw, "Home")
        return self.new_robot(HomeRobot)

    def do_logout(self) -> HomeRobot:
        click_menu_item(self.raw, "Log out")
        return self.new_robot(HomeRobot)


class MobileLoginRobot(RobotDsl):
    expect_title_pattern = "Login – {event.name} – Kirppu"

    def enter_code(self, code: str) -> typing.Self:
        input_field = self.raw.get_by_placeholder("1234")
        input_field.fill(code)
        return self

    def click_login(self) -> MobileRobot:
        with self.raw.expect_request_finished():
            self.raw.get_by_role("button", name="Log in").click()
        return self.new_robot(MobileRobot)
