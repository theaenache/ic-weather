# Imperial Valley Weather

Observed ASOS data for Imperial Airport (KIPL) and El Centro NAF (KNJK).

![Observed weather summary](weather-summary.svg)

- `observations.csv`: station observations in Pacific local time.
- `weather-summary.svg`: daily means and precipitation report counts.
- `fetch_observations.py`: refresh the CSV with `python3 fetch_observations.py`.

Blank values were not reported. Precipitation markers count positive or trace reports, not daily totals. WBGT is not reported by these stations. Super lightweight! Let me know if there are other stations or feeds to add.
