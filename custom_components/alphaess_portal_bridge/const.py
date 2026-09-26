"""Constants for the AlphaESS Portal Bridge."""

from datetime import timedelta

DOMAIN = "alphaess_portal_bridge"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SYSTEM_SERIAL = "system_serial"
CONF_WALLBOX_SERIAL = "wallbox_serial"
PLATFORM_URL = "https://platform.alphaess.com"
API_URL = f"{PLATFORM_URL}/api"
SESSION_URL = f"{API_URL}/users-center/sessions"
SESSION_REFRESH_URL = f"{SESSION_URL}/refresh"
UPDATE_INTERVAL = timedelta(minutes=5)
