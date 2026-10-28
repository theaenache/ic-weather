#!/usr/bin/env python3
"""Download west-side station observations for Calipatria and Westmorland."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START_DATE = date(2026, 6, 16)
TIMEZONE = "America/Los_Angeles"
STATIONS = {
    "CIMS": ("CIMS", "CIMS station"),
    "CAR": ("CAR", "CAR station"),
    "BRAWLEY": ("BWL", "BRW", "BRAWLEY", "BLY"),
}
OBSERVATION_FIELDS = ("tmpf", "relh", "drct", "sknt", "p01i")
OUTPUT_FIELDS = (
    "station_id",
    "station_name",
    "observation_time_local",
    "temperature_f",
    "humidity_pct",
    "wind_direction_deg",
    "wind_speed_kt",
    "precipitation_in",
    "wbgt_f",
)
OUTPUT_PATH = Path(__file__).with_name("observations.csv")


def fetch_station_rows(station_codes, start: date, end: date, now: datetime):
    """Yield rows for the first station code that returns valid data."""
    for station_code in station_codes:
        params = {
            "station": station_code,
            "data": ",".join(OBSERVATION_FIELDS),
            "year1": start.year,
            "month1": start.month,
            "day1": start.day,
            "year2": (end + timedelta(days=1)).year,
            "month2": (end + timedelta(days=1)).month,
            "day2": (end + timedelta(days=1)).day,
            "tz": TIMEZONE,
            "format": "comma",
            "missing": "empty",
            "trace": "T",
            "report_type": "1,2",
        }
        url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?" + urlencode(params)
        request = Request(url, headers={"User-Agent": "ic-weather west-side data downloader"})
        try:
            with urlopen(request, timeout=120) as response:
                content = (line.decode("utf-8") for line in response if not line.startswith(b"#"))
                reader = csv.DictReader(content)
                if not reader.fieldnames or "valid" not in reader.fieldnames:
                    continue
                for row in reader:
                    if not row.get("valid"):
                        continue
                    observed_at = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M")
                    if observed_at > now:
                        continue
                    values = tuple(row.get(field, "").strip() for field in OBSERVATION_FIELDS)
                    if any(values):
                        yield station_code, observed_at, values
                return
        except Exception:
            continue


def main():
    now = datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    end_date = now.date()

    rows = []
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open("r", newline="", encoding="utf-8") as output:
            reader = csv.DictReader(output)
            rows = list(reader)

    existing_keys = {(row["station_id"], row["observation_time_local"]) for row in rows}
    for station_key, station_codes in STATIONS.items():
        for station_code, observed_at, values in fetch_station_rows(station_codes, START_DATE, end_date, now):
            record_key = (station_key, observed_at.strftime("%Y-%m-%d %H:%M"))
            if record_key in existing_keys:
                continue
            rows.append(
                {
                    "station_id": station_key,
                    "station_name": station_key,
                    "observation_time_local": observed_at.strftime("%Y-%m-%d %H:%M"),
                    "temperature_f": values[0],
                    "humidity_pct": values[1],
                    "wind_direction_deg": values[2],
                    "wind_speed_kt": values[3],
                    "precipitation_in": values[4],
                    "wbgt_f": "",
                }
            )
            existing_keys.add(record_key)

    rows.sort(key=lambda row: (row["observation_time_local"], row["station_id"]))
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} west-side station records to {OUTPUT_PATH}")
    if not rows:
        print("No west-side station data was returned for CIMS, CAR, or Brawley in the selected date range.")


if __name__ == "__main__":
    main()
