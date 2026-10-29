# Imperial Valley Weather

Observed ASOS data for Imperial Airport (KIPL) and El Centro NAF (KNJK), plus the west-side Calipatria/Westmorland feeds when available.

![Observed weather summary](weather-summary.svg)

- `observations.csv`: station observations in Pacific local time.
- `weather-summary.svg`: daily means and precipitation report counts.
- `fetch_observations.py`: refresh the original east-side CSV with `python3 fetch_observations.py`.
- `fetch_obersvations_CAR.py`: refresh the CAR station feed with `python3 fetch_obersvations_CAR.py`.

Blank values were not reported. Precipitation markers count positive or trace reports, not daily totals. WBGT is not reported by these stations. The CAR scraper adds CAR observations to the shared CSV; CIMS and Brawley require separate feed integrations.
