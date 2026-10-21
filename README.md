# FreE-Bike Map

A minimal, phone-friendly Streamlit map of bike-share stations that have e-bikes and an exact number of classic bikes (0 = e-bikes only).

Uses Lyft's public GBFS feeds, refreshed every 60 seconds. Set `CITY` at the top of `app.py` to `nyc`, `sf`, `chi`, or `dc`.

```
pip install -r requirements.txt
streamlit run app.py
```
