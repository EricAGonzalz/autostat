    game_eff_df = build_game_efficiency(games, game_drive_counts, fbs_teams)
    adj_df = solve_adjusted_efficiency(game_eff_df)               # Adjust efficiency for opponent strength.

    ratings_df = ratings_df.merge(adj_df, on="Team", how="left")
    ratings_df["AdjEM Rank"] = ratings_df["AdjEM"].rank(ascending=False, method="min").astype("Int64")

    # Strength of schedule = average quality of the opponents actually played.
    #
    #     SOS_i = mean(AdjRtg of each completed FBS opponent)
    #
    # This intentionally contains no win-percentage bonus, conference bonus,
    # preseason prior, or subjective schedule weighting. Because each opponent's
    # AdjRtg is itself recursively opponent-adjusted, an opponent that has proven
    # itself against other strong teams contributes more schedule strength than
    # one that has produced the same raw efficiency against weak competition.
    #
    # Positive SOS = above-average schedule
    # Negative SOS = below-average schedule
    # SOS rank 1 = strongest average schedule played so far.
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

    # Sort the final table by raw Net Rating rank.
    #
    # Rk = 1 corresponds to the highest:
    #
    #     Net Rating = Ortg - DRtg
    #
    # The adjusted ranking is still preserved separately in AdjRk.
    ratings_df = ratings_df.sort_values("Rk", ascending=True).reset_index(drop=True)

    # Keep calculated decimal fields at exactly three decimal places.
    decimal_columns = [
        "NetRtg", "AdjRtg", "Win %", "PyW %",
        "Luck", "Luck Z", "Ortg", "DRtg", "SOS",
    ]
    decimal_columns = [c for c in decimal_columns if c in ratings_df.columns]
    ratings_df[decimal_columns] = ratings_df[decimal_columns].round(3)

    # In GitHub Actions, GITHUB_WORKSPACE is the repository root. Locally,
    # fall back to the directory containing this script.
    repo_root = os.environ.get(
        "GITHUB_WORKSPACE",
        os.path.dirname(os.path.abspath(__file__))
    )
    data_dir = os.path.join(repo_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    # This filename matches the URLs already used by index.html/matchup.html:
    # data/2026 Master.csv, data/2027 Master.csv, etc.
    outfile = os.path.join(data_dir, f"{YEAR} Master.csv")

    # float_format preserves trailing zeroes (for example 1.000 and 140.000).
    ratings_df.to_csv(outfile, index=False, float_format="%.3f")

    print("Saved rankings to:", outfile)
    print(ratings_df.head(15))


if __name__ == "__main__":
    main()
