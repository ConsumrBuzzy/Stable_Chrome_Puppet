import config
import pytest

def test_zoom_contact_center_admin_url():
    """Test that ZOOM_CONTACT_CENTER_ADMIN_URL exists and is correctly formatted."""
    assert hasattr(config, 'ZOOM_CONTACT_CENTER_ADMIN_URL')
    assert config.ZOOM_CONTACT_CENTER_ADMIN_URL.startswith('https://zoom.us/cci/')
    assert 'admin' in config.ZOOM_CONTACT_CENTER_ADMIN_URL

def test_zoom_workplace_url():
    """Test that ZOOM_WORKPLACE_URL exists and is correctly formatted."""
    assert hasattr(config, 'ZOOM_WORKPLACE_URL')
    assert config.ZOOM_WORKPLACE_URL.startswith('https://zoom.us/pbx/')

def test_missing_config_attribute():
    """Test that accessing a non-existent config attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(config, 'NON_EXISTENT_CONFIG_KEY')

def test_invalid_url_format(monkeypatch):
    """Test that monkeypatching ZOOM_CONTACT_CENTER_ADMIN_URL to an invalid format is detected."""
    monkeypatch.setattr(config, 'ZOOM_CONTACT_CENTER_ADMIN_URL', 'ftp://invalid-url')
    assert not config.ZOOM_CONTACT_CENTER_ADMIN_URL.startswith('https://')
    assert config.ZOOM_CONTACT_CENTER_ADMIN_URL.startswith('ftp://')
