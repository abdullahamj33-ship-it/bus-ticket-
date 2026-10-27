# Project Index — Recommended Reading Order

1. `README.md` — overall project guide and run commands.
2. `main.py` — console entry point.
3. `data.py` — shared console data.
4. `route_functions.py` — route features.
5. `booking_functions.py` — booking and cancellation features.
6. `report_functions.py` — reports and schedule.
7. `app.py` — optional Streamlit interface.
8. `bus_logic.py` — UI business rules called by `app.py`.
9. `requirements.txt` and `.streamlit/config.toml` — web dependency and theme.
10. `test_ui.py` — automated tests.
11. `test_cases.txt` and `*_transcript.txt` — test reference and example output.
12. `UI_README.md` — detailed Streamlit page and function guide.

## Entry points

- Console: `python main.py`
- Web: `python -m pip install -r requirements.txt` followed by `python -m streamlit run app.py`

The console application and Streamlit interface are separate entry points. The console uses the modular console files; the web interface uses `app.py` and `bus_logic.py`. Both are included in this bundle.
