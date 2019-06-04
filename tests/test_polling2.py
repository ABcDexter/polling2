import logging
import time
import unittest

from mock import patch
import pytest

import polling2


class TestPoll(object):

    def test_import(self):
        """Test that you can import via correct usage"""
        import polling2
        from polling2 import poll

        assert poll
        assert polling2

    def test_arg_no_arg(self):
        """Tests various permutations of calling with invalid args"""
        with pytest.raises(TypeError):
            polling2.poll()

    def test_arg_no_step(self):
        with pytest.raises(TypeError):
            polling2.poll(lambda: True)

    def test_no_poll_forever_or_maxtries(self):
        """No error raised without specifying poll_forever or a timeout/max_tries"""
        with pytest.raises(AssertionError):
            polling2.poll(lambda: True, step=1)

    def test_poll_forever_with_timeout_max_tries(self):
        with pytest.raises(AssertionError):
            polling2.poll(lambda: True, step=1, timeout=1, max_tries=1, poll_forever=True)

    def test_type_error_when_misspelt_argnames(self):
        with pytest.raises(TypeError):
            polling2.poll(target=lambda: None, step=2, timeout=10, check_sucess=lambda rv: rv is None)

    def test_valid_arg_options(self):
        # Valid options
        polling2.poll(lambda: True, step=1, poll_forever=True)
        polling2.poll(lambda: True, step=1, timeout=1)
        polling2.poll(lambda: True, step=1, max_tries=1)
        polling2.poll(lambda: True, step=1, timeout=1, max_tries=1)

    @patch('time.sleep', return_value=None)
    @patch('time.time', return_value=0)
    def test_timeout_exception(self, patch_sleep, patch_time):

        # Since the timeout is < 0, the first iteration of polling should raise the error if max timeout < 0
        try:
            polling2.poll(lambda: False, step=10, timeout=-1)
        except polling2.TimeoutException as e:
            assert e.values.qsize() == 1, 'There should have been 1 value pushed to the queue of values'
            assert e.last is False, 'The last value was incorrect'
        else:
            assert False, 'No timeout exception raised'

        # Test happy path timeout
        val = polling2.poll(lambda: True, step=0, timeout=0)
        assert val is True, 'Val was: {} != {}'.format(val, True)

    def test_max_call_exception(self):
        """
        Test that a MaxCallException will be raised 
        """
        tries = 100
        try:
            polling2.poll(lambda: False, step=0, max_tries=tries)
        except polling2.MaxCallException as e:
            assert e.values.qsize() == tries, 'Poll function called the incorrect number of times'
            assert e.last is False, 'The last value was incorrect'
        else:
            assert False, 'No MaxCallException raised'

    def test_max_call_no_sleep(self):
        """
        Test that a MaxCallException is raised without sleeping after the last call
        """
        tries = 2
        sleep = 0.1
        start_time = time.time()

        with pytest.raises(polling2.MaxCallException):
            polling2.poll(lambda: False, step=sleep, max_tries=tries)
        assert time.time() - start_time < tries * sleep, 'Poll function slept before MaxCallException'

    def test_logs_response_at_debug(self, caplog):
        """
        Test that the log_value decorator will log values returned to a check_success function.
        """
        with caplog.at_level(logging.DEBUG):
            polling2.poll(target=lambda: True, step=0.1, max_tries=1, log=logging.DEBUG)
            assert len(caplog.records) == 1, "Should only be one log record."
            record = caplog.records[0]
            assert record.levelname == 'DEBUG'
            assert record.message == "poll() calls check_success(True)"

    def test_logs_response_change_level(self, caplog):
        """
        Test that the log parameter controls the logging level in poll function
        """
        with caplog.at_level(logging.DEBUG):
            polling2.poll(target=lambda: True, step=0.1, max_tries=1, log=logging.INFO)
            assert len(caplog.records) == 1, "Should only be one log record."
            record = caplog.records[0]
            assert record.levelname == 'INFO'
            assert record.message == "poll() calls check_success(True)"

    def test_default_is_not_log(self, caplog):
        """
        Shouldn't log anything unless explicitly asked to do so.
        """
        with caplog.at_level(logging.DEBUG):
            polling2.poll(target=lambda: True, step=0.1, max_tries=1)
            assert len(caplog.records) == 0, "Should not be any log records"
