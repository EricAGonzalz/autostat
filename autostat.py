import os
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
# Locally, this defaults to 2026 if CFB_YEAR is not set.
YEAR = int(os.environ.get("CFB_YEAR", "2026"))

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

# Maximum scoring margin allowed to influence a single game's efficiency.
#
# If the actual score difference is larger than CAP_MARGIN, the winning team's
# score is reduced so that:
#
#     capped_margin = min(actual_margin, CAP_MARGIN)
#
# Example:
#     Actual score = 56-7, margin = 49
#     CAP_MARGIN = 28
#     Rating score becomes 35-7, margin = 28
#
# This prevents late-game scoring in extreme blowouts from dominating the
# adjusted-efficiency model.
CAP_MARGIN = 28

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
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.HTTPError) as e:
            last_err = e
            time.sleep(backoff * (i + 1))
    raise SystemExit(f"Failed after {tries} tries: {last_err}")


# Calculate season scoring totals for each FBS team.
#
# For every FBS-vs-FBS game:
#     points_for     += points scored by the team
#     points_against += points scored by the opponent
#
# These totals later become the numerators of the offensive and defensive
# efficiency formulas. Games against non-FBS teams are excluded so large
# mismatches do not artificially inflate a team's raw rating.


def add_missing_live_teams(ratings_df: pd.DataFrame,
                           live_metadata: list) -> pd.DataFrame:
    """
    Add only currently-live FBS teams that still do not have a calculated row.

    Normally, canonicalizing the live names and drives causes these teams to be
    calculated normally. This is only a fallback for the opening moments of a
    game before enough completed drives exist to calculate efficiency.
    """
    if not live_metadata:
        return ratings_df

    existing = {
        str(team).strip().lower()
        for team in ratings_df["Team"].dropna()
    }

    rows = []

    for game in live_metadata:
        for team_name, conference in (
            (game.get("homeTeam"), game.get("homeConference")),
            (game.get("awayTeam"), game.get("awayConference")),
        ):
            if not team_name:
                continue

            key = str(team_name).strip().lower()
            if key in existing:
                continue

            # np.nan keeps numeric columns numeric, allowing float_format="%.3f"
            # to work correctly when the CSV is written.
            row = {column: np.nan for column in ratings_df.columns}
            row["Team"] = team_name
            row["Conference"] = conference or ""
            row["W"] = 0
            row["L"] = 0

            rows.append(row)
            existing.add(key)

    if not rows:
        return ratings_df

    live_only_df = pd.DataFrame(rows, columns=ratings_df.columns)

    print(
        f"Added {len(live_only_df)} temporary live team row(s) because "
        "insufficient completed-drive data existed for a calculated rating."
    )

    return pd.concat([ratings_df, live_only_df], ignore_index=True)




def get_fbs_team_id_map(year: int) -> dict:
    """
    Build a CFBD team-ID -> canonical school-name/conference map.

    This is used ONLY to normalize live scoreboard/play-by-play names. It does
    not cause every FBS team to be added to the rankings.
    """
    teams = get_json(
        f"https://api.collegefootballdata.com/teams/fbs?year={year}"
    )

    mapping = {}
    for team in teams:
        team_id = team.get("id")
        school = team.get("school")
        conference = team.get("conference")

        if team_id is None or not school:
            continue

        mapping[str(team_id)] = {
            "school": school,
            "conference": conference or "",
        }

    return mapping


def get_json_optional(url: str):
    """
    Request JSON without terminating the rankings job if an optional live-data
    endpoint is unavailable. The completed-game rankings can still publish.
    """
    try:
        resp = SESSION.get(url, timeout=TIMEOUT)
        if not resp.ok:
            print(f"Live-data request skipped: HTTP {resp.status_code} for {url}")
            return None
        return resp.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        print(f"Live-data request skipped for {url}: {exc}")
        return None


def get_live_scoreboard() -> list:
    """
    Return only FBS games currently in progress.

    The scoreboard endpoint is used only for live state. If the user's CFBD
    access tier does not include live data, this returns an empty list and the
    script continues using completed games.
    """
    data = get_json_optional(
        "https://api.collegefootballdata.com/scoreboard?classification=fbs"
    )
    if not isinstance(data, list):
        return []

    live_games = []
    for game in data:
        if str(game.get("status", "")).lower() != "in_progress":
            continue

        home = game.get("homeTeam") or {}
        away = game.get("awayTeam") or {}

        if str(home.get("classification", "")).lower() != "fbs":
            continue
        if str(away.get("classification", "")).lower() != "fbs":
            continue

        live_games.append(game)

    return live_games


def _extract_team_name(value):
    """Return a team name whether CFBD gives us a string or a nested object."""
    if isinstance(value, dict):
        return value.get("name") or value.get("team") or value.get("school")
    return value


def _extract_team_points(value):
    """Return current points whether the scoreboard uses a team object or flat fields."""
    if isinstance(value, dict):
        return value.get("points")
    return None


def _extract_team_name(value):
    """Return a team name whether CFBD gives us a string or a nested object."""
    if isinstance(value, dict):
        return value.get("name") or value.get("team") or value.get("school")
    return value


def _extract_team_points(value):
    """Return current points whether the scoreboard uses nested or flat fields."""
    if isinstance(value, dict):
        return value.get("points")
    return None


def merge_live_games(games: list,
                     drives_raw: list,
                     live_scoreboard: list,
                     team_id_map: dict):
    """
    Overlay live FBS-vs-FBS data on top of completed season data.

    Final/completed games remain untouched. A live game contributes its current
    score and completed drives to the same season totals used for finished games.

    Example:
        completed season = 10 drives, 30 points
        live game        =  4 drives, 14 points
        current totals   = 14 drives, 44 points

    W/L is still based only on completed games.
    """
    if not live_scoreboard:
        return games, drives_raw, []

    games_by_id = {
        str(g.get("id")): g
        for g in games
        if g.get("id") is not None
    }

    live_ids = {
        str(g.get("id"))
        for g in live_scoreboard
        if g.get("id") is not None
    }

    def drive_game_id(d):
        for field in ("gameId", "game_id", "gameID"):
            value = d.get(field)
            if value is not None:
                return str(value)
        return None

    # Keep every completed-game drive; remove only records for games that are
    # currently live so the live endpoint cannot double-count them.
    updated_drives = [
        d for d in drives_raw
        if drive_game_id(d) not in live_ids
    ]

    live_metadata = []

    for board_game in live_scoreboard:
        game_id = board_game.get("id")
        if game_id is None:
            continue

        gid = str(game_id)
        home_obj = board_game.get("homeTeam") or {}
        away_obj = board_game.get("awayTeam") or {}

        home_id = (
            home_obj.get("id") if isinstance(home_obj, dict)
            else board_game.get("homeId")
        )
        away_id = (
            away_obj.get("id") if isinstance(away_obj, dict)
            else board_game.get("awayId")
        )

        game_record = games_by_id.get(gid)

        # Canonical names: /games first, then the team-ID directory, then
        # scoreboard display name as a last resort.
        home_team = game_record.get("homeTeam") if game_record else None
        away_team = game_record.get("awayTeam") if game_record else None

        if not home_team and home_id is not None:
            home_team = team_id_map.get(str(home_id), {}).get("school")
        if not away_team and away_id is not None:
            away_team = team_id_map.get(str(away_id), {}).get("school")

        home_team = home_team or _extract_team_name(home_obj)
        away_team = away_team or _extract_team_name(away_obj)

        home_conf = game_record.get("homeConference") if game_record else None
        away_conf = game_record.get("awayConference") if game_record else None

        if not home_conf and home_id is not None:
            home_conf = team_id_map.get(str(home_id), {}).get("conference")
        if not away_conf and away_id is not None:
            away_conf = team_id_map.get(str(away_id), {}).get("conference")

        if not home_conf and isinstance(home_obj, dict):
            home_conf = home_obj.get("conference")
        if not away_conf and isinstance(away_obj, dict):
            away_conf = away_obj.get("conference")

        home_points = _extract_team_points(home_obj)
        away_points = _extract_team_points(away_obj)

        if home_points is None:
            home_points = board_game.get("homePoints")
        if away_points is None:
            away_points = board_game.get("awayPoints")

        if not home_team or not away_team:
            print(f"Skipping live game {gid}: missing canonical team names")
            continue

        if home_points is None or away_points is None:
            print(f"Skipping live game {gid}: live score unavailable")
            continue

        # Add the live game to the season game list if /games does not already
        # contain it. This is what lets a team with no previous FBS game appear
        # and receive live PF/PA.
        if game_record is None:
            game_record = {
                "id": game_id,
                "homeTeam": home_team,
                "awayTeam": away_team,
                "homeConference": home_conf,
                "awayConference": away_conf,
            }
            games.append(game_record)
            games_by_id[gid] = game_record

        game_record["homeTeam"] = home_team
        game_record["awayTeam"] = away_team
        game_record["homeConference"] = home_conf
        game_record["awayConference"] = away_conf
        game_record["homePoints"] = float(home_points)
        game_record["awayPoints"] = float(away_points)
        game_record["completed"] = False

        # ID map for live drive attribution.
        live_team_names = {}
        if home_id is not None:
            live_team_names[str(home_id)] = home_team
        if away_id is not None:
            live_team_names[str(away_id)] = away_team

        live_game = get_json_optional(
            f"https://api.collegefootballdata.com/live/plays?gameId={game_id}"
        )

        completed_drives = 0
        team_live_drives = Counter()

        if isinstance(live_game, dict):
            for drive in (live_game.get("drives") or []):
                offense_id = drive.get("offenseId")
                defense_id = drive.get("defenseId")

                offense = (
                    live_team_names.get(str(offense_id))
                    if offense_id is not None else None
                )
                defense = (
                    live_team_names.get(str(defense_id))
                    if defense_id is not None else None
                )

                # If drive IDs are present but not on the scoreboard object,
                # fall back to the FBS team directory.
                if not offense and offense_id is not None:
                    offense = team_id_map.get(str(offense_id), {}).get("school")
                if not defense and defense_id is not None:
                    defense = team_id_map.get(str(defense_id), {}).get("school")

                offense = offense or _extract_team_name(drive.get("offense"))
                defense = defense or _extract_team_name(drive.get("defense"))

                result = drive.get("result")

                # Only completed drives affect efficiency.
                if not offense or not defense or not result:
                    continue

                updated_drives.append({
                    "gameId": game_id,
                    "offense": offense,
                    "defense": defense,
                })

                team_live_drives[offense] += 1
                completed_drives += 1

        print(
            f"LIVE INCLUDED: {away_team} {away_points} - "
            f"{home_team} {home_points} | "
            f"{away_team} drives={team_live_drives[away_team]}, "
            f"{home_team} drives={team_live_drives[home_team]}"
        )

        live_metadata.append({
            "id": game_id,
            "status": "in_progress",
            "homeTeam": home_team,
            "awayTeam": away_team,
            "homeConference": home_conf,
            "awayConference": away_conf,
            "homePoints": float(home_points),
            "awayPoints": float(away_points),
            "period": board_game.get("period"),
            "clock": board_game.get("clock"),
            "completedDrives": completed_drives,
            "homeOffensiveDrives": team_live_drives[home_team],
            "awayOffensiveDrives": team_live_drives[away_team],
        })

    return games, updated_drives, live_metadata



def get_points(games: list) -> pd.DataFrame:
    """Return each FBS team's total points scored and allowed in games against other FBS teams."""
    team_totals = {}
    for g in games:
        home = g.get("homeTeam")
        away = g.get("awayTeam")
        home_conf = g.get("homeConference")
        away_conf = g.get("awayConference")

        if home_conf not in FBS_CONFERENCES or away_conf not in FBS_CONFERENCES:
            continue

        home_pts = g.get("homePoints")
        away_pts = g.get("awayPoints")

        # Ignore future/scheduled games that do not yet have a score.
        if home_pts is None or away_pts is None:
            continue

        if home:
            if home not in team_totals:
                team_totals[home] = {
                    "team": home, "conference": home_conf,
                    "points_for": 0.0, "points_against": 0.0,
                }
            team_totals[home]["points_for"] += float(home_pts)
            team_totals[home]["points_against"] += float(away_pts)

        if away:
            if away not in team_totals:
                team_totals[away] = {
                    "team": away, "conference": away_conf,
                    "points_for": 0.0, "points_against": 0.0,
                }
            team_totals[away]["points_for"] += float(away_pts)
            team_totals[away]["points_against"] += float(home_pts)

    df = pd.DataFrame(team_totals.values())
    print("points_df shape (ALL):", df.shape)
    df = df[df["conference"].isin(FBS_CONFERENCES)].reset_index(drop=True)
    print("points_df shape (FBS ONLY):", df.shape)
    return df


# Retrieve and organize drive data.
#
# Drives are used as the possession unit for the efficiency model. Instead of
# measuring scoring per game, the model measures scoring per 100 drives, which
# better accounts for differences in pace and number of possessions.
def get_drives_raw(year: int) -> list:
    url = f"https://api.collegefootballdata.com/drives?year={year}&seasonType=both"
    return get_json(url)


def aggregate_season_drives(drives_raw: list, fbs_teams: set) -> pd.DataFrame:
    """
    Count each team's offensive and defensive drives across FBS-vs-FBS games.

    For each drive:
        off_drives[offense] += 1
        def_drives[defense] += 1

    These season totals are later used in:

        Offensive Rating = 100 * Points For / Offensive Drives
        Defensive Rating = 100 * Points Against / Defensive Drives

    Multiplying by 100 expresses both values as points per 100 drives.
    """
    off_counts = Counter()
    def_counts = Counter()

    for d in drives_raw:
        off = d.get("offense")
        deff = d.get("defense")
        if off not in fbs_teams or deff not in fbs_teams:
            continue
        if off:
            off_counts[off] += 1
        if deff:
            def_counts[deff] += 1

    rows = []
    all_teams = set(off_counts) | set(def_counts)
    for team in all_teams:
        rows.append({"team": team, "off_drives": off_counts[team], "def_drives": def_counts[team]})

    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit(
            "aggregate_season_drives: no drives matched the FBS team-name filter. "
            "Check that team names from /drives match team names from /games."
        )
    print("season drives_df shape:", df.shape)
    return df


def aggregate_game_drives(drives_raw: list, fbs_teams: set) -> dict:
    """
    Count offensive and defensive drives for every team in every individual game.

    The dictionary key is:

        (game_id, team)

    and the stored value is:

        {"off": offensive_drives, "def": defensive_drives}

    Per-game drive counts are required because the adjusted model calculates
    game-level efficiencies before adjusting them for opponent strength.

    The API's game-ID field may use different names, so the function checks
    several possible field names and stops with an error if none are present.
    """
    candidates = ["gameId", "game_id", "gameID"]
    game_id_field = None
    for c in candidates:
        if drives_raw and c in drives_raw[0]:
            game_id_field = c
            break
    if game_id_field is None:
        sample_keys = sorted(drives_raw[0].keys()) if drives_raw else []
        raise SystemExit(
            "aggregate_game_drives: couldn't find a game-id field on /drives records "
            f"(tried {candidates}). Fields actually present on a sample record: {sample_keys}. "
            "Add the correct field name to `candidates` in aggregate_game_drives() and rerun."
        )
    print(f"aggregate_game_drives: using '{game_id_field}' as the game-id field")

    counts = {}
    for d in drives_raw:
        off = d.get("offense")
        deff = d.get("defense")
        gid = d.get(game_id_field)
        if gid is None:
            continue
        gid = str(gid)
        if off in fbs_teams:
            key = (gid, off)
            counts.setdefault(key, {"off": 0, "def": 0})
            counts[key]["off"] += 1
        if deff in fbs_teams:
            key = (gid, deff)
            counts.setdefault(key, {"off": 0, "def": 0})
            counts[key]["def"] += 1
    return counts


# Calculate raw offensive, defensive, and net efficiency.
#
# Offensive Rating:
#
#     Ortg = 100 * Points For / Offensive Drives
#
# This is the number of points a team scores per 100 offensive drives.
#
# Defensive Rating:
#
#     DRtg = 100 * Points Against / Defensive Drives
#
# This is the number of points a team allows per 100 defensive drives.
# Lower defensive ratings are better.
#
# Net Rating:
#
#     Net Rating = Ortg - DRtg
#
# A positive value means the team scores more points per 100 drives than it
# allows. A larger positive value therefore represents stronger performance.
def compute_ratings(points_df: pd.DataFrame, drives_df: pd.DataFrame) -> pd.DataFrame:
    merged = points_df.merge(drives_df, on="team", how="inner")
    merged = merged[(merged["off_drives"] > 0) & (merged["def_drives"] > 0)].copy()
    print("merged shape (FBS only):", merged.shape)

    merged["off_rating"] = 100 * merged["points_for"] / merged["off_drives"]
    merged["def_rating"] = 100 * merged["points_against"] / merged["def_drives"]
    merged["net_rating"] = merged["off_rating"] - merged["def_rating"]

    merged = merged[[
        "team", "conference", "net_rating", "off_rating", "def_rating",
        "points_for", "points_against", "off_drives", "def_drives"
    ]]
    return merged.sort_values("net_rating", ascending=False).reset_index(drop=True)


# Calculate each team's FBS record and raw Net Rating rank.
#
# Winning percentage is:
#
#     Win % = Wins / Games Played
#
# Ties are not added to either the win or loss counters in this implementation.
# Net Rank is then calculated by sorting Net Rating from highest to lowest,
# because a larger offensive-minus-defensive efficiency margin is better.
def add_record(ratings_df: pd.DataFrame, games: list) -> pd.DataFrame:
    wins = Counter()
    losses = Counter()
    games_played = Counter()

    for g in games:
        home = g.get("homeTeam")
        away = g.get("awayTeam")
        home_conf = g.get("homeConference")
        away_conf = g.get("awayConference")
        if not home or not away:
            continue
        if home_conf not in FBS_CONFERENCES or away_conf not in FBS_CONFERENCES:
            continue
        home_pts = g.get("homePoints")
        away_pts = g.get("awayPoints")
        if home_pts is None or away_pts is None:
            continue

        # Live games can affect efficiency, but the record does not change until
        # CFBD marks the game completed.
        if g.get("completed") is False:
            continue

        games_played[home] += 1
        games_played[away] += 1
        if home_pts > away_pts:
            wins[home] += 1
            losses[away] += 1
        elif away_pts > home_pts:
            wins[away] += 1
            losses[home] += 1

    win_pct_map = {t: (wins[t] / gp if gp > 0 else 0.0) for t, gp in games_played.items()}
    record_df = pd.DataFrame([
        {"team": t, "wins": wins.get(t, 0), "losses": losses.get(t, 0), "win_pct": win_pct_map.get(t, 0.0)}
        for t in ratings_df["team"]
    ])

    out = ratings_df.merge(record_df, on="team", how="left")
    out["Net Rank"] = out["net_rating"].rank(ascending=False, method="min").astype("Int64")
    out = out.rename(columns={
        "team": "Team", "conference": "Conference", "net_rating": "Net Rating",
        "wins": "Wins", "losses": "Losses",
    })
    return out


# Convert each game into offensive and defensive efficiency observations.
#
# For the home team:
#
#     Game Offensive Rating = 100 * Capped Home Points / Home Offensive Drives
#     Game Defensive Rating = 100 * Capped Away Points / Home Defensive Drives
#
# The same calculation is then performed from the away team's perspective.
#
# These game-level observations become the inputs to the schedule-adjusted
# rating system rather than relying only on season totals.
def apply_cap(home_pts: float, away_pts: float, cap: float):
    """
    Reduce scoring margins larger than `cap` while preserving the winner.

    Let:

        diff = home_points - away_points

    If diff > cap:
        adjusted_home = away_points + cap

    If diff < -cap:
        adjusted_away = home_points + cap

    Otherwise the score is unchanged.

    Only the margin used by the efficiency calculation changes; the actual game
    result and win/loss record are not modified.
    """
    diff = home_pts - away_pts
    if diff > cap:
        return away_pts + cap, away_pts
    if diff < -cap:
        return home_pts, home_pts + cap
    return home_pts, away_pts


def build_game_efficiency(games: list, game_drive_counts: dict, fbs_teams: set, cap_margin: float) -> pd.DataFrame:
    rows = []
    skipped_missing_drives = 0

    for g in games:
        home = g.get("homeTeam")
        away = g.get("awayTeam")
        home_conf = g.get("homeConference")
        away_conf = g.get("awayConference")
        if home not in fbs_teams or away not in fbs_teams:
            continue
        if home_conf not in FBS_CONFERENCES or away_conf not in FBS_CONFERENCES:
            continue

        home_pts = g.get("homePoints")
        away_pts = g.get("awayPoints")
        if home_pts is None or away_pts is None:
            continue

        game_id = g.get("id")
        if game_id is None:
            continue
        gid = str(game_id)

        home_off = game_drive_counts.get((gid, home), {}).get("off", 0)
        home_def = game_drive_counts.get((gid, home), {}).get("def", 0)
        away_off = game_drive_counts.get((gid, away), {}).get("off", 0)
        away_def = game_drive_counts.get((gid, away), {}).get("def", 0)

        if not (home_off and home_def and away_off and away_def):
            skipped_missing_drives += 1
            continue

        capped_home_pts, capped_away_pts = apply_cap(home_pts, away_pts, cap_margin)

        rows.append({
            "team": home, "opponent": away,
            "off_rating": 100 * capped_home_pts / home_off,
            "def_rating": 100 * capped_away_pts / home_def,
        })
        rows.append({
            "team": away, "opponent": home,
            "off_rating": 100 * capped_away_pts / away_off,
            "def_rating": 100 * capped_home_pts / away_def,
        })

    df = pd.DataFrame(rows)
    print(f"game_efficiency rows: {len(df)} (skipped {skipped_missing_drives} games missing per-game drive data)")
    if df.empty:
        raise SystemExit(
            "build_game_efficiency: no game-level rows produced. Check the game-id "
            "matching between /games and /drives in aggregate_game_drives()."
        )
    return df


# Solve schedule-adjusted offensive and defensive efficiencies.
#
# Raw efficiency does not account for opponent quality. A team scoring well
# against elite defenses should receive more credit than a team scoring the
# same amount against weak defenses. The adjusted model corrects for this by
# linking every team's rating to the ratings of its opponents.
def solve_adjusted_efficiency(game_eff_df: pd.DataFrame) -> pd.DataFrame:
    """
    Solve the mutually dependent adjusted offensive and defensive ratings.

    For team i:

        AdjO_i = AvgRawOff_i - AvgOpponentAdjD_i + LeagueAvg

        AdjD_i = AvgRawDef_i - AvgOpponentAdjO_i + LeagueAvg

    Interpretation:

    - AdjO asks how efficiently the team scored after accounting for the
      defensive quality of the opponents it faced.
    - AdjD asks how efficiently the team defended after accounting for the
      offensive quality of the opponents it faced.

    Because AdjO depends on opponents' AdjD values and AdjD depends on opponents'
    AdjO values, every team's rating depends on every connected opponent. The
    equations therefore form one simultaneous linear system:

        Mx = b

    where:
        M = coefficient matrix containing team/opponent relationships
        x = unknown AdjO and AdjD values
        b = observed raw efficiencies shifted by league average

    The program first attempts an exact solution with np.linalg.solve(). If the
    matrix is singular or nearly dependent, least-squares is used instead.

    After solving, AdjO and AdjD are recentered so their league means equal the
    league-average raw efficiency.

    Adjusted Efficiency Margin is:

        AdjEM = AdjO - AdjD

    A positive AdjEM means the team performs above an average FBS team after
    opponent strength is taken into account.
    """
    if game_eff_df.empty:
        raise SystemExit("solve_adjusted_efficiency: no game-level efficiency rows to solve with.")

    teams = sorted(game_eff_df["team"].unique())
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}

    k = game_eff_df.groupby("team").size()
    avg_off = game_eff_df.groupby("team")["off_rating"].mean()
    avg_def = game_eff_df.groupby("team")["def_rating"].mean()
    league_avg = pd.concat([game_eff_df["off_rating"], game_eff_df["def_rating"]]).mean()

    M = np.zeros((2 * n, 2 * n))
    b = np.zeros(2 * n)

    for i, team in enumerate(teams):
        M[i, i] = 1.0
        b[i] = avg_off.get(team, league_avg) + league_avg
        M[n + i, n + i] = 1.0
        b[n + i] = avg_def.get(team, league_avg) + league_avg

    for team, group in game_eff_df.groupby("team"):
        i = idx[team]
        ki = k[team]
        for opp in group["opponent"]:
            j = idx[opp]
            M[i, n + j] += 1.0 / ki       # Add 1/G of this opponent's AdjD to the team's AdjO equation.
            M[n + i, j] += 1.0 / ki       # Add 1/G of this opponent's AdjO to the team's AdjD equation.

    try:
        x = np.linalg.solve(M, b)
    except np.linalg.LinAlgError:
        x, *_ = np.linalg.lstsq(M, b, rcond=None)

    adj_o = x[:n]
    adj_d = x[n:2 * n]

    # Recenter the solved ratings.
    #
    # The shifts are:
    #
    #     AdjO_new = AdjO + (LeagueAvg - mean(AdjO))
    #     AdjD_new = AdjD + (LeagueAvg - mean(AdjD))
    #
    # This preserves the differences between teams while forcing the average
    # adjusted offense and defense to sit on the same scale as raw efficiency.
    adj_o = adj_o + (league_avg - adj_o.mean())
    adj_d = adj_d + (league_avg - adj_d.mean())

    out = pd.DataFrame({
        "Team": teams,
        "AdjO": adj_o,
        "AdjD": adj_d,
    })
    out["AdjEM"] = out["AdjO"] - out["AdjD"]
    out["Games Used (AdjEM)"] = [k[t] for t in teams]
    return out


# Estimate expected winning percentage and measure "luck."
#
# The model uses a Pythagorean expectation based on offensive and defensive
# efficiency:
#
#                     Off^x
#     Pyth Win % = ---------------
#                  Off^x + Def^x
#
# where x = PYTHAG_EXP.
#
# A larger offensive rating increases expected winning percentage, while a
# larger defensive rating lowers it because allowing more points is worse.
#
# Luck is then:
#
#     Luck = Actual Win % - Pyth Win %
#
# Positive Luck means the team won more often than its efficiency would predict.
# Negative Luck means it won less often than expected.
#
# Luck Z standardizes Luck across all teams:
#
#     Luck Z = (Luck - Mean Luck) / Standard Deviation of Luck
#
# A Luck Z near 0 is typical, while larger positive or negative values indicate
# more unusual results relative to the rest of the FBS.
def add_luck(df: pd.DataFrame) -> pd.DataFrame:
    if {"AdjO", "AdjD", "win_pct"}.issubset(df.columns):
        off_col, def_col = "AdjO", "AdjD"
    elif {"off_rating", "def_rating", "win_pct"}.issubset(df.columns):
        off_col, def_col = "off_rating", "def_rating"
    else:
        print("Luck: required columns missing, skipping luck calculation.")
        return df

    df = df.copy()
    off = df[off_col].clip(lower=1e-6)
    deff = df[def_col].clip(lower=1e-6)

    num = off ** PYTHAG_EXP
    den = num + (deff ** PYTHAG_EXP)
    pyth_win_pct = (num / den.replace(0, float("nan"))).fillna(0.5)

    df["Pyth Win Pct"] = pyth_win_pct
    df["Luck"] = df["win_pct"] - df["Pyth Win Pct"]

    luck_mean = df["Luck"].mean()
    luck_std = df["Luck"].std(ddof=0)
    df["Luck Z"] = 0.0 if luck_std == 0 else (df["Luck"] - luck_mean) / luck_std
    return df


# Run the complete ranking pipeline.
#
# The processing order is:
#   1. Download season games.
#   2. Calculate FBS scoring totals.
#   3. Download and count drives.
#   4. Calculate raw efficiency ratings.
#   5. Add win/loss records.
#   6. Build per-game efficiency observations.
#   7. Solve schedule-adjusted ratings.
#   8. Calculate strength of schedule and luck.
#   9. Rename, order, sort, and export the final columns.
def main():
    # Used only to normalize team names/IDs in live data.
    team_id_map = get_fbs_team_id_map(YEAR)

    games_url = f"https://api.collegefootballdata.com/games?year={YEAR}&seasonType=both"
    games = get_json(games_url)

    drives_raw = get_json(
        f"https://api.collegefootballdata.com/drives?year={YEAR}&seasonType=both"
    )

    # Live games are intentionally layered on top of the normal season data.
    # Current scores + completed live drives affect efficiency, but W/L stays
    # unchanged until the game becomes final.
    live_scoreboard = get_live_scoreboard()
    games, drives_raw, live_metadata = merge_live_games(
        games, drives_raw, live_scoreboard, team_id_map
    )

    print(f"Live scoreboard games detected: {len(live_scoreboard)}")
    print(f"Live games merged into ratings: {len(live_metadata)}")

    points_df = get_points(games)
    fbs_teams = set(points_df["team"])

    season_drives_df = aggregate_season_drives(drives_raw, fbs_teams)
    ratings_df = compute_ratings(points_df, season_drives_df)   # Calculate unadjusted efficiency ratings.
    ratings_df = add_record(ratings_df, games)                    # Add each team's FBS record and raw ranking.

    game_drive_counts = aggregate_game_drives(drives_raw, fbs_teams)
    game_eff_df = build_game_efficiency(games, game_drive_counts, fbs_teams, CAP_MARGIN)
    adj_df = solve_adjusted_efficiency(game_eff_df)               # Adjust efficiency for opponent strength.

    ratings_df = ratings_df.merge(adj_df, on="Team", how="left")
    ratings_df["AdjEM Rank"] = ratings_df["AdjEM"].rank(ascending=False, method="min").astype("Int64")

    # Calculate opponent strength of schedule.
    #
    # For each team:
    #
    #     OppSOS = Sum(Opponent AdjEM) / Number of Games
    #
    # Because AdjEM measures opponent quality relative to the FBS average,
    # a positive OppSOS means the team faced above-average opponents on average.
    # A negative OppSOS means its opponents were below average.
    #
    # SOSRk ranks OppSOS from highest to lowest, so rank 1 represents the
    # strongest average schedule.
    adj_em_map = dict(zip(adj_df["Team"], adj_df["AdjEM"]))
    opp_strength = (
        game_eff_df.assign(opp_adj_em=game_eff_df["opponent"].map(adj_em_map))
        .groupby("team")["opp_adj_em"].mean()
        .rename("opp_strength")
        .reset_index()
        .rename(columns={"team": "Team"})
    )
    ratings_df = ratings_df.merge(opp_strength, on="Team", how="left")
    ratings_df["SOSRk"] = ratings_df["opp_strength"].rank(ascending=False, method="min").astype("Int64")

    ratings_df = add_luck(ratings_df)

    # Rename internal variables to compact output-column names.
    #
    # Key fields:
    #   Rk      = rank by raw Net Rating
    #   AdjRtg  = adjusted efficiency margin, AdjO - AdjD
    #   AdjRk   = rank by adjusted efficiency margin
    #   Ortg    = points scored per 100 offensive drives
    #   DRtg    = points allowed per 100 defensive drives
    #   OppSOS  = average AdjEM of opponents
    #   SOSRk   = rank by OppSOS
    #   Luck    = actual Win % minus expected Pythagorean Win %
    #   LuckZ   = standardized Luck score
    # Rename columns to the exact schema consumed by index.html and matchup.html.
    ratings_df = ratings_df.rename(columns={
        "Net Rank": "Rk",
        "Wins": "W",
        "Losses": "L",
        "Net Rating": "NetRtg",
        "AdjEM": "AdjRtg",
        "AdjEM Rank": "AdjRk",
        "win_pct": "Win %",
        "Pyth Win Pct": "PyW %",
        "Luck Z": "Luck Z",
        "off_rating": "Ortg",
        "def_rating": "DRtg",
        "points_for": "PF",
        "points_against": "PA",
        "off_drives": "ODrives",
        "def_drives": "DDrives",
        "opp_strength": "SOS",
        "SOSRk": "SOS rank",
    })

    # Keep this order stable because the public pages expect this schema.
    cols = [
        "Rk", "Team", "Conference", "W", "L",
        "NetRtg", "AdjRtg", "AdjRk",
        "Win %", "PyW %", "Luck", "Luck Z",
        "Ortg", "DRtg", "PF", "PA",
        "ODrives", "DDrives", "SOS", "SOS rank",
    ]
    cols = [c for c in cols if c in ratings_df.columns]
    ratings_df = ratings_df[cols].copy()

    # Only add teams currently playing an FBS-vs-FBS live game if they do
    # not yet have a calculated rankings row.
    ratings_df = add_missing_live_teams(ratings_df, live_metadata)

    # Sort the final table by raw Net Rating rank.
    #
    # Rk = 1 corresponds to the highest:
    #
    #     Net Rating = Ortg - DRtg
    #
    # The adjusted ranking is still preserved separately in AdjRk.
    ratings_df = ratings_df.sort_values("Rk", ascending=True).reset_index(drop=True)


    # Format calculated statistics as EXACTLY three decimal places in the CSV.
    # They remain parseable by JavaScript/parseFloat on the public pages.
    decimal_columns = [
        "NetRtg",
        "AdjRtg",
        "Win %",
        "PyW %",
        "Luck",
        "Luck Z",
        "Ortg",
        "DRtg",
        "SOS",
    ]

    for column in decimal_columns:
        if column in ratings_df.columns:
            numeric = pd.to_numeric(ratings_df[column], errors="coerce")
            ratings_df[column] = numeric.map(
                lambda value: "" if pd.isna(value) else f"{value:.3f}"
            )

    integer_columns = [
        "Rk",
        "W",
        "L",
        "AdjRk",
        "PF",
        "PA",
        "ODrives",
        "DDrives",
        "SOS rank",
    ]

    for column in integer_columns:
        if column in ratings_df.columns:
            numeric = pd.to_numeric(ratings_df[column], errors="coerce")
            ratings_df[column] = numeric.map(
                lambda value: "" if pd.isna(value) else str(int(round(value)))
            )

    ratings_df.to_csv(
        outfile,
        index=False,
        na_rep=""
    )

    # Publish a small companion JSON file used by index.html for the LIVE lights
    # and "Last updated" timestamp.
    live_file = os.path.join(data_dir, f"{YEAR} Live.json")
    live_payload = {
        "season": YEAR,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "liveGames": live_metadata,
        "liveTeams": sorted({
            team
            for game in live_metadata
            for team in (game.get("homeTeam"), game.get("awayTeam"))
            if team
        }),
    }

    with open(live_file, "w", encoding="utf-8") as f:
        json.dump(live_payload, f, indent=2, ensure_ascii=False)

    print("Saved rankings to:", outfile)
    print("Saved live metadata to:", live_file)
    print(f"Live FBS games included: {len(live_metadata)}")
    print(ratings_df.head(15))


if __name__ == "__main__":
    main()
