# Smart Bus Reservation — Streamlit UI

## Run it

Use Python 3.10 or newer (the project was developed with Python 3.13.5). In a terminal, from this folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit is the only extra package listed in `requirements.txt`. The console program continues to use only Python's standard library and can still be started with `python main.py`.

## Pages

- **Dashboard:** route count, available seats, confirmed bookings, confirmed revenue, next departures and quick links.
- **View Routes:** all routes, seat occupancy progress, fare and availability status; optional available-only filter.
- **Search:** case-insensitive route ID or exact city search, plus a supported-city quick filter.
- **Book a Ticket:** booking form, fare preview, central business-rule validation, ticket summary and in-memory text download.
- **My Bookings:** every booking including cancelled records, with status and ID filters.
- **Cancel a Booking:** select or enter an ID, review its summary, confirm, then cancel. Seats are restored once only.
- **Seat Availability:** route-by-route seat progress and available-seat bar chart.
- **Reports:** booking totals, confirmed revenue and seats, route aggregates and schedule grouped by supported city.

## Business rules and assumptions

- Five starter routes and their fares/capacities are defined in `bus_logic.py`.
- Route IDs are matched case-insensitively; city searches are exact, case-insensitive matches.
- Passenger name cannot be blank; age and seat count must be positive whole numbers; the route must exist and have enough seats.
- All inputs are validated before a booking mutates route seats, bookings, or issued IDs.
- Booking IDs start at `B1001`, skip IDs already in the issued-ID set, and are not reused within a session.
- Only confirmed bookings can be cancelled. A cancelled booking remains in the list; cancelled bookings do not count toward reserved seats or confirmed revenue.
- A cancellation restores seats to the booking's original route and does not restore them again on a second cancellation.
- Fare amounts are integer rupees; the UI formats them with thousands separators.
- No database, file persistence, payment processing, login, third-party API, or external service is used.

## Data lifetime

**All routes, bookings, issued IDs, and counters are stored in `st.session_state` only.** They are lost when the browser session or server session ends; the reset control also restores the starter demo state. The downloadable ticket is generated in memory and is not written to disk.

## Optional enhancement layer

The Streamlit interface is an optional UI layer. `main.py` and the original console modules are not imported or modified by the web UI and remain runnable with Python's standard library alone. Install the optional dependency only when you want to use `app.py`.

## Tests

Run the business-logic and Streamlit AppTest suite with:

```bash
python -m unittest -v test_ui.py
```

The AppTest portion requires Streamlit to be installed from `requirements.txt`.


## Function guide (for explaining the code)

### `bus_logic.py`

All functions in this module are independent of Streamlit. The route and booking lists are passed in by the caller so the same rules can be tested without launching a web page.

| Function | Inputs | What it does / returns | Common failure case |
|---|---|---|---|
| `create_starting_routes()` | None | Returns a fresh list of five route dictionaries. It does not mutate existing state. | None expected; the starter route definitions are fixed. |
| `find_route(routes, route_id)` | Route list, ID text | Returns the matching route dictionary or `None`; IDs are trimmed and uppercased. | Unknown ID returns `None`. |
| `search_routes(routes, query, city_filter)` | Route list, text query, optional city filter | Returns every exact city match or the unique route-ID match, narrowed by the optional filter. | No matches returns an empty list. |
| `validate_booking_inputs(routes, name, age, route_id, seats)` | All booking fields | Returns a validation dictionary. It returns the first specific error and does not change any state. | Blank name, non-integer/non-positive age, unknown route, non-integer/non-positive seats, or too many seats. |
| `create_booking(routes, bookings, issued_ids, next_booking_counter, name, age, route_id, seats)` | Shared state plus form fields | Calls validation first. On success it creates a booking dict, subtracts seats once, appends the record, adds the ID to the set, and returns the booking plus the next counter. On failure it returns an error and leaves all state unchanged. | Returns `success=False` for any invalid field. |
| `cancel_booking(routes, bookings, booking_id)` | Shared route/booking lists and ID | Returns a result dictionary. A confirmed booking changes to Cancelled and its seats are restored to the original route once; its record remains in the list. | Unknown ID, already-cancelled booking, or missing original route returns an error without restoring seats. |
| `seat_status(route)` | One route dictionary | Returns `Available`, `Partially Booked`, or `Fully Booked`. | Assumes the route has valid integer capacity fields. |
| `build_report(routes, bookings)` | Current routes and all bookings | Returns overall totals and per-route aggregates. The per-route calculation uses an outer route loop and an inner booking loop; only Confirmed records count toward revenue and reserved seats. | Empty bookings are valid and produce zero booking/revenue totals. |
| `build_schedule(routes, supported_cities)` | Routes and optional fixed city tuple | Returns one schedule group per city, including cities with no departures. | Cities without departures return an empty `departures` list. |

### `app.py` helpers and page functions

| Function | What it does / connects to |
|---|---|
| `money(amount)` | Formats integer rupees as `Rs. 1,200`; used anywhere a fare is shown. |
| `badge(status)` | Renders a text status label with its CSS class. Status words remain visible, so color is not the only signal. |
| `initialise_state()` | Creates `routes`, `bookings`, `issued_ids`, `next_booking_counter`, `last_booking`, and action state only when missing in `st.session_state`. This prevents route seats resetting on every rerun. |
| `reset_demo_data()` | If the sidebar confirmation is checked, restores starter routes and clears bookings and issued IDs; otherwise sets a warning flag and changes no business data. |
| `go_to_page(page_name)` | Changes the sidebar navigation selection for dashboard quick-action buttons. |
| `route_card(route, sequence)` | Displays one route's journey, fare, seat ratio, progress bar, and status using `seat_status()` and `money()`. |
| `ticket_text(booking, route)` | Creates the downloadable ticket text in memory; it does not write a file. |
| `page_dashboard()` | Calls `build_report()` for the four headline metrics, shows all five next departures, empty state, and quick navigation buttons. |
| `page_routes()` | Filters `st.session_state.routes` if requested and displays each route with `route_card()`. |
| `page_search()` | Reads query and city filter widgets, calls `search_routes()`, and displays matching route summaries or a helpful no-match message. |
| `page_booking()` | Builds the form and fare preview, calls `create_booking()` on submit, stores the returned counter and last ticket, and offers an in-memory text download. Business validation is never duplicated as UI-only logic. |
| `page_bookings()` | Filters the full booking list by status and ID, then displays a dataframe. Cancelled records are not removed. |
| `page_cancel()` | Looks up the typed/selected ID for a summary, requires a checkbox, calls `cancel_booking()`, and displays success/error feedback. |
| `page_availability()` | Shows each route's available/total seats, progress, textual status, optional available-only filter, and a built-in bar chart. |
| `page_reports()` | Calls `build_report()` and `build_schedule()` to render summary metrics, per-route confirmed aggregates, charts, and city-grouped departures. |

The bottom of `app.py` maps the selected sidebar label to one page function. On every rerun, `initialise_state()` preserves the current session data and then only the selected page is rendered. Invalid booking input is rejected by `bus_logic.py` before any route seats, booking records, ID set, or counter are changed.
