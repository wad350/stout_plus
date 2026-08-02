"""Constants for the Stout Plus integration."""

from datetime import timedelta

DOMAIN = "stout_plus"
PLATFORMS = ["binary_sensor", "climate", "number", "sensor", "select", "switch", "time"]

DEFAULT_NAME = "Stout Plus"
REQUEST_TIMEOUT = 10
UPDATE_INTERVAL = timedelta(seconds=10)
