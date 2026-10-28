#!/usr/bin/env python3
"""Download CAR station observations to observations.csv."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START_DATE = date(2026, 6, 16)
TIMEZONE = "America/Los_Angeles"
STATION_ID = "CAR"
STATION_NAME = "CAR station"
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


def fetch_station_rows(start: date, end: date, now: datetime):
    params = {
        "station": STATION_ID,
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
    request = Request(url, headers={"User-Agent": "ic-weather CAR data downloader"})
    with urlopen(request, timeout=120) as response:
        content = (line.decode("utf-8") for line in response if not line.startswith(b"#"))
        reader = csv.DictReader(content)
        if not reader.fieldnames or "valid" not in reader.fieldnames:
            raise RuntimeError(f"Unexpected CSV response for station {STATION_ID}")
        for row in reader:
            if not row.get("valid"):
                continue
            observed_at = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M")
            if observed_at > now:
                continue
            values = tuple(row.get(field, "").strip() for field in OBSERVATION_FIELDS)
            if any(values):
                yield observed_at, values


def main():
    now = datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    end_date = now.date()

    rows = []
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open("r", newline="", encoding="utf-8") as output:
            reader = csv.DictReader(output)
            rows = list(reader)

    existing_keys = {(row["station_id"], row["observation_time_local"]) for row in rows}
    station_rows = list(fetch_station_rows(START_DATE, end_date, now))
    if not station_rows:
        raise RuntimeError(f"No observations returned for station {STATION_ID}")
    for observed_at, values in station_rows:
        record_key = (STATION_ID, observed_at.strftime("%Y-%m-%d %H:%M"))
        if record_key in existing_keys:
            continue
        rows.append(
            {
                "station_id": STATION_ID,
                "station_name": STATION_NAME,
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

    print(f"Wrote {len(rows)} observations including station {STATION_ID} to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
