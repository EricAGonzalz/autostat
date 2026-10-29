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
        "off_rating": "ORtg",
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
        "ORtg", "DRtg", "AdjO", "AdjD", "PF", "PA",
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
    #     Net Rating = ORtg - DRtg
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
        "ORtg",
        "DRtg",
        "AdjO",
        "AdjD",
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

    # A diagnostic CSV preserving the REAL game scores alongside offensive
    # attribution. Write only after validation and complete calculation.
    audit_file = os.path.join(data_dir, f"{YEAR} Scoring Audit.csv")
    pd.DataFrame(scoring_audit).to_csv(audit_file, index=False)
    print("Saved scoring audit to:", audit_file)

    ratings_df.to_csv(
        outfile,
        index=False,
        na_rep=""
    )

    # Build/update the current-season schedule file used by team pages.
    build_schedule_csv(games, ratings_df, data_dir)


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
    parser = argparse.ArgumentParser(
        description="Calculate CFB efficiency rankings or update the active weekly history snapshot."
    )
    parser.add_argument(
        "--archive-week",
        action="store_true",
        help="Update weekly history from the current Master.csv using the active FBS week."
    )
    args = parser.parse_args()

    if args.archive_week:
        archive_weekly_snapshot()
    else:
        main()
