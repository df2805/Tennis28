from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


START_YEAR = 2017
END_YEAR = datetime.now(timezone.utc).year
DATA_DIR = Path("data")


SOURCES = [
    (
        "ATP",
        "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv",
    ),
    (
        "CHALL",
        "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_qual_chall_{year}.csv",
    ),
    (
        "WTA",
        "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv",
    ),
    (
        "WTA_ITF",
        "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_qual_itf_{year}.csv",
    ),
]


def load_matches() -> pd.DataFrame:
    all_dfs = []

    for year in range(START_YEAR, END_YEAR + 1):
        for source, url_template in SOURCES:
            url = url_template.format(year=year)
            try:
                print(f"Loading {source} {year}...")
                df = pd.read_csv(url, low_memory=False)
                df["data_source"] = source
                all_dfs.append(df)
            except Exception as exc:
                print(f"Failed {source} {year}: {exc}")

    if not all_dfs:
        raise RuntimeError("No tennis match data could be downloaded.")

    return pd.concat(all_dfs, ignore_index=True)


def normalize_name(value: object) -> str:
    return str(value).strip().lower()


def build_player_stats(df: pd.DataFrame) -> dict[str, object]:
    rows = []

    for _, match in df.iterrows():
        surface = str(match.get("surface", "")).strip().lower()
        tour = str(match.get("data_source", "ATP")).strip()
        score = str(match.get("score", "")).strip()

        for side, opponent_side, won in (("winner", "loser", True), ("loser", "winner", False)):
            name = match.get(f"{side}_name")
            if pd.isna(name) or not str(name).strip():
                continue

            rank = match.get(f"{side}_rank")
            opponent_rank = match.get(f"{opponent_side}_rank")
            aces = match.get(f"{side}_ace", 0)
            double_faults = match.get(f"{side}_df", 0)
            serve_points = match.get(f"{side}_svpt", 0)
            first_in = match.get(f"{side}_1stIn", 0)
            first_won = match.get(f"{side}_1stWon", 0)
            second_won = match.get(f"{side}_2ndWon", 0)
            opponent_serve_points = match.get(f"{opponent_side}_svpt", 0)

            rows.append(
                {
                    "name": str(name).strip(),
                    "key": normalize_name(name).split()[-1],
                    "tour": "WTA" if tour.startswith("WTA") else "ATP",
                    "surface": surface,
                    "won": won,
                    "rank": pd.to_numeric(rank, errors="coerce"),
                    "opponent_rank": pd.to_numeric(opponent_rank, errors="coerce"),
                    "aces": pd.to_numeric(aces, errors="coerce"),
                    "double_faults": pd.to_numeric(double_faults, errors="coerce"),
                    "serve_points": pd.to_numeric(serve_points, errors="coerce"),
                    "first_in": pd.to_numeric(first_in, errors="coerce"),
                    "first_won": pd.to_numeric(first_won, errors="coerce"),
                    "second_won": pd.to_numeric(second_won, errors="coerce"),
                    "opponent_serve_points": pd.to_numeric(opponent_serve_points, errors="coerce"),
                    "is_slam": str(match.get("tourney_level", "")).strip() == "G",
                    "score": score,
                }
            )

    player_df = pd.DataFrame(rows)
    output: dict[str, object] = {}

    for key, group in player_df.groupby("key"):
        recent = group.tail(80)
        serve_points = recent["serve_points"].fillna(0).sum()
        opponent_serve_points = recent["opponent_serve_points"].fillna(0).sum()
        rank_values = recent["rank"].dropna()
        wins = recent["won"].sum()
        matches = len(recent)

        if matches < 5:
            continue

        surface_stats = {}
        for surface in ("hard", "clay", "grass"):
            surface_group = recent[recent["surface"] == surface]
            if len(surface_group) < 3:
                surface_stats[surface] = round(float(wins / matches), 3)
            else:
                surface_stats[surface] = round(float(surface_group["won"].mean()), 3)

        serve_rate = (
            (recent["first_won"].fillna(0).sum() + recent["second_won"].fillna(0).sum()) / serve_points
            if serve_points
            else 0.62
        )
        return_rate = (
            1 - (
                (recent["first_won"].fillna(0).sum() + recent["second_won"].fillna(0).sum())
                / opponent_serve_points
            )
            if opponent_serve_points
            else 0.40
        )

        best_name = recent["name"].mode().iat[0]
        rank = int(rank_values.median()) if not rank_values.empty else 50
        elo_proxy = 1500 + (wins / matches) * 430 + max(0, 100 - rank) * 2

        output[key] = {
            "name": best_name,
            "tour": recent["tour"].mode().iat[0],
            "matches": int(matches),
            "rank": rank,
            "elo": round(float(elo_proxy)),
            "serve": round(float(max(0.48, min(0.78, serve_rate))), 3),
            "return": round(float(max(0.28, min(0.55, return_rate))), 3),
            **surface_stats,
        }

    return output


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df = load_matches()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_path = DATA_DIR / f"merged_output_{timestamp}.csv"
    latest_path = DATA_DIR / "merged_latest.csv"
    stats_path = DATA_DIR / "player_stats.json"
    metadata_path = DATA_DIR / "metadata.json"

    df.to_csv(snapshot_path, index=False)
    df.to_csv(latest_path, index=False)

    player_stats = build_player_stats(df)
    stats_path.write_text(json.dumps(player_stats, indent=2, sort_keys=True), encoding="utf-8")

    metadata = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "start_year": START_YEAR,
        "end_year": END_YEAR,
        "rows": int(len(df)),
        "sources": df["data_source"].value_counts().to_dict(),
        "snapshot": snapshot_path.name,
        "player_count": len(player_stats),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nTotal rows: {len(df):,}")
    print(f"Sources   : {metadata['sources']}")
    print(f"Players   : {len(player_stats):,}")
    print(f"Saved to  : {latest_path}")


if __name__ == "__main__":
    main()
