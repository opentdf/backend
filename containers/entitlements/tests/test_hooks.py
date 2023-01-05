import json
import pytest
import logging
import sys

from python_base import hook_into

from ..hooks import HttpMethod

from .. import hooks

logger = logging.getLogger(__package__)

async def hi_name(name):
    return "hello "+ name

async def hi_error(name):
    raise Exception("TESTING hi_error EXCEPTION")

@pytest.mark.asyncio
async def test_function_name(caplog):

    def mock_run_pre_command_hooks_func_name(
            http_method, function_name, *args, **kwargs):
        logger.info("pre_command: "+function_name)

    caplog.set_level(logging.INFO)
    result = await hook_into(HttpMethod.GET,
     pre=mock_run_pre_command_hooks_func_name)(hi_name)("Alice")
    messages = [r.msg for r in caplog.records]
    assert result == "hello Alice"
    assert "pre_command: hi_name" in messages

@pytest.mark.asyncio
async def test_sys_exec_info(caplog):

    def mock_run_err_hooks_sys_exec(
            http_method, function_name, *args, **kwargs):
        err = sys.exc_info()[1]
        logger.info(repr(err))

    caplog.set_level(logging.INFO)
    with pytest.raises(Exception) as e_info:
        result = await hook_into(HttpMethod.GET,
         err=mock_run_err_hooks_sys_exec)(hi_error)("Bob")
    messages = [r.msg for r in caplog.records]
    assert e_info.value.args[0] == 'TESTING hi_error EXCEPTION'
    assert "Exception('TESTING hi_error EXCEPTION')" in messages
