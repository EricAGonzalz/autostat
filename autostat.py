import os
import argparse
import time
import json
from datetime import datetime, timezone
from collections import Counter

import numpy as np
import pandas as pd
import requests

# Conferences and historical conference labels treated as FBS.
# A game is included in the ratings only when both teams belong to one of these
# conferences. This keeps the data set limited to FBS-vs-FBS competition.
FBS_CONFERENCES = {
    "ACC", "Big Ten", "Big 12", "SEC", "Pac-12",
    "American Athletic", "Mountain West", "Mid-American",
    "Sun Belt", "Conference USA", "C-USA",
    "FBS Independents", "Big East", "Pac-10", # "Western Athletic"
}

# Global settings used by the data-collection and rating calculations.
# YEAR selects the season to analyze. API_KEY authenticates requests to the
# CollegeFootballData API. TIMEOUT controls how long an API request may wait
# before being treated as failed.
# GitHub Actions can override the season with the CFB_YEAR environment variable.
# If no override is provided, determine the college-football season automatically.
# January bowl/CFP games still belong to the previous calendar year's season.
def get_current_cfb_season() -> int:
    now = datetime.now(timezone.utc)
    return now.year - 1 if now.month == 1 else now.year


YEAR = int(os.environ.get("CFB_YEAR", str(get_current_cfb_season())))

# Never store the CollegeFootballData API key in source control.
# In GitHub, create an Actions secret named CFBD_API_KEY.
API_KEY = os.environ.get("CFBD_API_KEY")
if not API_KEY:
    raise SystemExit(
        "Missing CFBD_API_KEY. Set it as an environment variable locally or "
        "as a GitHub Actions repository secret."
    )

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",  # prevents brotli crash
    "Connection": "keep-alive",
}

TIMEOUT = 30  # Maximum number of seconds allowed for a single API request before a timeout is raised.
PYTHAG_EXP = 2.5  # Exponent x used in Pythagorean expectation: Off^x / (Off^x + Def^x).

# Early-season stabilization constant for schedule-adjusted ratings.
#
# The adjusted model uses only current-season FBS-vs-FBS results. To keep a
# very small sample from producing extreme schedule-adjusted values, each team's
# opponent adjustment is weighted by:
#
#     sample_weight = Games / (Games + ADJ_STABILIZATION_GAMES)
#
# With ADJ_STABILIZATION_GAMES = 3:
#     1 game  -> 25% observed adjustment
#     3 games -> 50% observed adjustment
#     6 games -> 67% observed adjustment
#    10 games -> 77% observed adjustment
#
# The remaining weight is centered on the CURRENT-SEASON FBS average, not a
# preseason rating, poll, recruiting ranking, betting line, or historical prior.
ADJ_STABILIZATION_GAMES = 3.0

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# Request JSON data from the API with automatic retries.
#
# If a network, timeout, decoding, or HTTP error occurs, the request is retried
# up to `tries` times. The waiting period grows after each failure:
#
#     delay = backoff * (attempt_number + 1)
#
# This creates a simple linear backoff so temporary API problems do not
# immediately terminate the program.
def get_json(url: str, *, tries: int = 4, backoff: float = 0.6):
    last_err = None
    for i in range(tries):
        try:
            resp = SESSION.get(url, timeout=TIMEOUT)
            if not resp.ok:
                msg = (resp.text or "")[:500]
                raise requests.HTTPError(f"{resp.status_code} for {url}\n{msg}", response=resp)
            return resp.json()
        except (requests.exceptions.ContentDecodingError,
