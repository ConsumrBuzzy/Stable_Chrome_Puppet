import unittest
from unittest.mock import patch
from utils import logging_utils

class TestLoggingUtils(unittest.TestCase):
    """
    Unit tests for the logging_utils module.
    Ensures all logging functions delegate to the correct logger methods and file handlers.
    Follows PEP8, DRY, KISS, SOLID principles.
    """

    def test_log_info_calls_logger(self):
        """Test that log_info calls logger.info with the correct message."""
        with patch.object(logging_utils.logger, 'info') as mock_info:
            logging_utils.log_info('test info')
            mock_info.assert_called_once_with('test info')

    def test_log_warning_calls_logger(self):
        """Test that log_warning calls logger.warning with the correct message."""
        with patch.object(logging_utils.logger, 'warning') as mock_warning:
            logging_utils.log_warning('test warning')
            mock_warning.assert_called_once_with('test warning')

    def test_log_error_calls_logger(self):
        """Test that log_error calls logger.error with the correct message."""
        with patch.object(logging_utils.logger, 'error') as mock_error:
            logging_utils.log_error('test error')
            mock_error.assert_called_once_with('test error')

    def test_log_debug_calls_logger(self):
        """Test that log_debug calls logger.debug with the correct message."""
        with patch.object(logging_utils.logger, 'debug') as mock_debug:
            logging_utils.log_debug('test debug')
            mock_debug.assert_called_once_with('test debug')

    def test_log_error_exception(self):
        """Test that log_error logs exception messages correctly."""
        with patch.object(logging_utils.logger, 'error') as mock_error:
            try:
                raise ValueError('Test exception')
            except Exception as e:
                logging_utils.log_error(f'Exception occurred: {e}')
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert 'Exception occurred: Test exception' in args[0]

    def test_log_info_file_handler(self):
        """Test that log_info writes to at least one file handler with INFO level."""
        with patch('logging.FileHandler.emit') as mock_emit:
            logging_utils.log_info('file handler info test')
            assert mock_emit.called
            found = False
            for call in mock_emit.call_args_list:
                record = call[0][0]
                if 'file handler info test' in record.getMessage() and record.levelname == 'INFO':
                    found = True
            assert found

    def test_logger_singleton(self):
        """Test that get_logger always returns the same logger instance (singleton)."""
        logger1 = logging_utils.get_logger()
        logger2 = logging_utils.get_logger()
        self.assertIs(logger1, logger2)

if __name__ == '__main__':
    unittest.main()
