from unittest.mock import Mock

import pytest

from src.streamwatch.menu_handler import MenuHandler


class TestMenuHandler:
    def test_init(self):
        mh = MenuHandler(command_invoker=Mock())
        assert mh.last_message == ""
