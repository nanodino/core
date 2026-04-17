"""Constants for the transitapp integration."""

from datetime import timedelta

DOMAIN = "transitapp"

API_URL = "https://external.transitapp.com/v3"
API_KEY_HEADER = "apiKey"

# Lightweight endpoint hit during config flow to verify the API key works.
PROBE_PATH = "/public/available_networks"

CONF_RADIUS = "radius"

DEFAULT_RADIUS_METERS = 500
MIN_RADIUS_METERS = 100
MAX_RADIUS_METERS = 1500

UPDATE_INTERVAL = timedelta(minutes=45)
