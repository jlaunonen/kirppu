# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time
import typing
from functools import wraps

from playwright.sync_api import Page, expect

__all__ = [
    "RobotDsl",
    "RobotManager",
]


class RobotMeta(type):
    STEP_DELAY: float = float(os.environ.get("TEST_STEP_DELAY", "0.0"))

    def __new__(mcs, name, bases, namespace, **kwargs):
        if not bases:
            # RobotDsl base class. We don't patch its functions.
            return type.__new__(mcs, name, bases, namespace)

        overrides = dict()
        for ns_name, ns_item in namespace.items():
            if not ns_name.startswith("_") and callable(ns_item):
                # Wrap every public function with function that ensures correct robot is in use
                # when the function is called.
                new_func = mcs._check_wrapper(ns_item)
                overrides[ns_name] = new_func

        ns = dict(namespace)
        ns.update(overrides)
        return type.__new__(mcs, name, bases, ns)

    @staticmethod
    def _check_wrapper(fn):
        @wraps(fn)
        def wrapped_dsl_fn(self: RobotDsl, *args, **kwargs):
            self._manager.check(self)
            if RobotMeta.STEP_DELAY > 0.0:
                time.sleep(RobotMeta.STEP_DELAY)
            return fn(self, *args, **kwargs)
        return wrapped_dsl_fn


class RobotDsl(metaclass=RobotMeta):
    address: typing.Optional[str] = None
    "Host-relative URL to navigate when this robot is used as entrypoint."

    expect_title_pattern: typing.Optional[str] = None
    """
    Expected title pattern when entering this robot.
    Placeholders in pattern must be in `str.format` format, using data from `context` supplied to this robot.
    """

    PUSH_TITLE_TIMEOUT_SECONDS: float = 3.0
    "Time to wait for the page title to be correct."

    def __init__(self, manager: RobotManager, **context):
        self._manager = manager
        self.context = context

    @property
    def raw(self) -> Page:
        """
        "Raw" access to the `Page` object provided by framework.
        """
        if not self._manager.is_started():
            self.start_testing()
        return self._manager.page

    def __enter__(self) -> typing.Self:
        """
        Context manager for visual separation of view actions.
        For example::

            with myRobot.nav_login() as login_view:
                login_view.enter(...)
                login_view.click_login()
                login_view.pop_self()
            myRobot.continue_testing(...)
        """
        self._manager.push(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Should we always pop self? We don't know if back (->pop) has been called as last;
        #  If back doesn't automatically pop, it's use gets more difficult.
        return False

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "{}(0x{:x})".format(self.__class__.__name__, id(self))

    def start_testing(self):
        self._manager.start(self.page_address)
        self._manager.push(self)

    def new_robot(self, dsl: typing.Type[T], reset_context: bool = False, **extra_context) -> T:
        if reset_context:
            new_context = {}
        else:
            new_context = self.context.copy()
        if extra_context:
            new_context.update(extra_context)
        return dsl(self._manager, **new_context)

    @property
    def expected_title(self) -> typing.Optional[str]:
        if self.expect_title_pattern:
            return self.expect_title_pattern.format_map(self.context)

    def expect_is_current(self) -> None:
        expect_title = self.expected_title
        if expect_title:
            expect(self.raw).to_have_title(expect_title, self.PUSH_TITLE_TIMEOUT_SECONDS)
            current_title = self.raw.title()

            if expect_title != current_title:
                raise AssertionError(
                    "Pushing {} failed: Expected title {} was not found. Currently {}. New stack: {}"
                    .format(
                        self.__class__.__name__,
                        repr(expect_title),
                        repr(current_title),
                        self._manager.get_stack(),
                    )
                )

    @property
    def page_address(self) -> typing.Optional[str]:
        if self.address:
            return self.address.format_map(self.context)

    def add_to_stack(self) -> typing.Self:
        self._manager.push(self)
        return self

    def pop_self(self) -> None:
        """
        Pop self away from robot stack.
        The `with` context this is called in should end after this.

        :raises :exc:`AttributeError` when the robot stack does not contain this class topmost.
        """
        self._manager.pop(self)

    def back(self) -> None:
        """
        Pop self away and press browser back button.
        The `with` context this is called in should end after this.

        :raises :exc:`AttributeError` when the robot stack does not contain this class topmost.
        """
        self.pop_self()
        self.raw.go_back()


T = typing.TypeVar("T", bound=RobotDsl)


class RobotManager:
    def __init__(self, framework: Page, server_url: str):
        self._stack: typing.List[RobotDsl] = []
        self.page: Page = framework
        self._started = False
        self._server_url = server_url

    def start(self, page_address: str) -> Page:
        assert not self._started
        self._started = True
        self.page.goto(self._server_url + page_address)
        return self.page

    def is_started(self) -> bool:
        return self._started

    def push(self, dsl: RobotDsl) -> None:
        """
        Push a robot on top of the stack.
        Must be paired with a later call to :py:func:`.pop(check)`.

        :param dsl: Robot instance to push on the stack.
        """
        self._stack.append(dsl)
        dsl.expect_is_current()

    def pop(self, check: typing.Optional[RobotDsl]) -> None:
        """
        Pop given robot away from top of robot stack.
        If `check` is `None`, pop skips checking correct value.

        :raises :exc:`AttributeError` when the robot stack does not contain this class topmost.
        """
        if check is not None and self._stack[-1] != check:
            raise AttributeError(
                "Encountered wrong context on pop, {}, expected {}. Old stack: {}"
                .format(self._stack[-1], check, self.get_stack())
            )
        self._stack.pop()

    def check(self, dsl: RobotDsl) -> None:
        """
        Ensure that given robot is the topmost on robot stack.

        :param dsl: Robot instance.
        :raises AttributeError when the topmost isn't the one given as argument.
        """
        # check() is called just before start() happens, so ignore that.
        if self._started and self._stack[-1] != dsl:
            raise AttributeError(
                "Encountered wrong context on call, {}, expected {}. Stack: {}"
                .format(dsl, self._stack[-1], self.get_stack())
            )

    def get_stack(self) -> str:
        return ", ".join(repr(item) for item in self._stack)
