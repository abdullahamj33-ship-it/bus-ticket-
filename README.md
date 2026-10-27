# Smart Bus Ticket Booking & Reservation System

A complete project bundle containing the original Python console application, its modular business functions, an optional Streamlit web UI, test cases, and example terminal transcripts. The console and web interfaces are separate entry points and can be run independently.

## 1. Choose how to run the project

### Option A — Console application (no installation required)

Requires Python 3.10+ and uses only Python's standard library.

```bash
python main.py
```

### Option B — Streamlit web interface

Requires Python 3.10+ and the one additional package listed in `requirements.txt` (`streamlit`).

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The web UI is optional; the console program still runs without Streamlit.

## 2. Project files in logical order

### Application entry points

- `main.py` — console application's menu and feature dispatch.
- `app.py` — Streamlit web interface with dashboard, route search, booking, cancellation, seat availability, and reports.

### Shared data and business logic

- `data.py` — shared in-memory data for the console application.
- `route_functions.py` — console route listing, route search, and seat availability.
- `booking_functions.py` — console booking, viewing, validation, and cancellation.
- `report_functions.py` — console booking reports and route schedule.
- `bus_logic.py` — UI-independent business rules used by the Streamlit interface. Its functions are independently testable.

### Configuration and dependencies

- `requirements.txt` — contains only `streamlit`, needed for the web UI.
- `.streamlit/config.toml` — theme and UI configuration.

### Tests and reference material

- `test_ui.py` — unit tests for web business logic plus Streamlit AppTest checks (the UI tests require Streamlit installed).
- `test_cases.txt` — original project test cases and sample results.
- `UI_README.md` — web UI page guide, data assumptions, and function-by-function explanation.
- `route_listing_transcript.txt` — example console route listing.
- `successful_booking_transcript.txt` — example successful booking.
- `cancellation_transcript.txt` — example cancellation.
- `report_transcript.txt` — example report output.

## 3. Main features

1. View available bus routes.
2. Search routes by route ID or city.
3. Book one or more seats and calculate fares.
4. View bookings.
5. Cancel a confirmed booking and restore seats once.
6. Check seat availability.
7. Generate booking reports and route schedules.
8. Use a web dashboard with metrics, route cards, filters, charts, ticket summary, and downloadable ticket text.

## 4. Important data behavior

- **No permanent storage:** all route changes, bookings, issued IDs, and counters are held in memory. Console data resets when the program exits. Web data lives in `st.session_state` and is lost when that session ends. The downloadable ticket is generated in memory and is not saved by the app to its own storage.
- There is no database, login, payment processing, API integration, or third-party service.
- Fare values are integer Pakistani rupees.
- Only confirmed bookings can be cancelled. A cancelled record remains visible, and its seats are restored only once.
- Route and booking IDs are handled case-insensitively where applicable; city searches use exact case-insensitive city matches.

## 5. Tests and verification

Run the available automated tests:

```bash
python -m unittest -v test_ui.py
```

The business-logic tests run without Streamlit. Streamlit AppTest checks are skipped if Streamlit is not installed. To run the full suite, first install `requirements.txt`.

To compile-check the Python modules:

```bash
python -m py_compile main.py data.py route_functions.py booking_functions.py report_functions.py bus_logic.py app.py test_ui.py
```

See `UI_README.md` for the detailed page guide and function reference.
