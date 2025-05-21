import os
import pytest
from utils.env_utils import load_credentials

def test_load_credentials_env(monkeypatch):
    """Test that load_credentials returns correct values when both env vars are present."""
    monkeypatch.setenv('ZOOM_EMAIL', 'test@example.com')
    monkeypatch.setenv('ZOOM_PASSWORD', 'secret')
    email, password = load_credentials()
    assert email == 'test@example.com'
    assert password == 'secret'

from unittest.mock import patch

def test_missing_email(monkeypatch, capsys):
    """Test that missing ZOOM_EMAIL triggers a SystemExit and prints the correct error message."""
    # Patch os.environ directly and mock load_dotenv to prevent .env loading
    with patch('utils.env_utils.load_dotenv', return_value=None):
        monkeypatch.delenv('ZOOM_EMAIL', raising=False)
        monkeypatch.setenv('ZOOM_PASSWORD', 'secret')
        with pytest.raises(SystemExit):
            load_credentials()
        captured = capsys.readouterr()
        assert 'Missing required environment variables' in captured.out
        assert 'ZOOM_EMAIL' in captured.out

def test_missing_password(monkeypatch, capsys):
    """Test that missing ZOOM_PASSWORD triggers a SystemExit and prints the correct error message."""
    with patch('utils.env_utils.load_dotenv', return_value=None):
        monkeypatch.setenv('ZOOM_EMAIL', 'test@example.com')
        monkeypatch.delenv('ZOOM_PASSWORD', raising=False)
        with pytest.raises(SystemExit):
            load_credentials()
        captured = capsys.readouterr()
        assert 'Missing required environment variables' in captured.out
        assert 'ZOOM_PASSWORD' in captured.out

def test_missing_both(monkeypatch, capsys):
    """Test that missing both ZOOM_EMAIL and ZOOM_PASSWORD triggers SystemExit and prints both in the error message."""
    with patch('utils.env_utils.load_dotenv', return_value=None):
        monkeypatch.delenv('ZOOM_EMAIL', raising=False)
        monkeypatch.delenv('ZOOM_PASSWORD', raising=False)
        with pytest.raises(SystemExit):
            load_credentials()
        captured = capsys.readouterr()
        assert 'Missing required environment variables' in captured.out
        assert 'ZOOM_EMAIL' in captured.out
        assert 'ZOOM_PASSWORD' in captured.out
