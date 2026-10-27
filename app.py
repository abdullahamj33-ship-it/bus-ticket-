"""Streamlit UI for Smart Bus Reservation. Business rules live in bus_logic.py."""
import html
import pandas as pd
import streamlit as st

from bus_logic import (
    SUPPORTED_CITIES, build_report, build_schedule, cancel_booking,
    create_booking, create_starting_routes, find_route, search_routes, seat_status,
)

st.set_page_config(page_title="Smart Bus Reservation", page_icon="🚌", layout="wide")

# Short, readable CSS for a calm transport-brand look.
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.route-card, .ticket-card {border: 1px solid #d9e4e7; border-radius: 14px;
  padding: 1rem 1.1rem; margin: .45rem 0; background: #ffffff;
  box-shadow: 0 3px 12px rgba(16, 54, 63, .07);}
.ticket-card {border-top: 5px solid #e7a83e; background: #fffdf8;}
.status {display:inline-block; padding:.18rem .6rem; border-radius:999px;
  font-size:.82rem; font-weight:650; border:1px solid transparent;}
.status-available, .status-confirmed {color:#17633b;background:#e5f5eb;border-color:#b8e4c8;}
.status-partial {color:#855600;background:#fff2d4;border-color:#f0d28d;}
.status-full, .status-cancelled {color:#9d2b2b;background:#fde9e7;border-color:#f2b8b3;}
.small-note {color:#52666b;font-size:.86rem;}
</style>
""", unsafe_allow_html=True)


def money(amount):
    """Format integer rupees with thousands separators."""
    return f"Rs. {int(amount):,}"


def badge(status):
    """Render a text status and its matching CSS class; text always carries meaning."""
    classes = {
        "Available": "status-available",
        "Confirmed": "status-confirmed",
        "Partially Booked": "status-partial",
        "Fully Booked": "status-full",
        "Cancelled": "status-cancelled",
    }
    st.markdown(
        f'<span class="status {classes.get(status, "status-partial")}">{status}</span>',
        unsafe_allow_html=True,
    )


def initialise_state():
    """Create demo data once per Streamlit session, never on every rerun."""
    if "routes" not in st.session_state:
        st.session_state.routes = create_starting_routes()
        st.session_state.bookings = []
        st.session_state.issued_ids = set()
        st.session_state.next_booking_counter = 1001
        st.session_state.last_booking = None
        st.session_state.last_action = None
    # Support a partially initialized session defensively.
    defaults = {
        "bookings": [], "issued_ids": set(), "next_booking_counter": 1001,
        "last_booking": None, "last_action": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_demo_data():
    """Restore starter routes and clear all booking/session action records."""
    if not st.session_state.get("reset_confirm", False):
        st.session_state.reset_warning = True
        return
    st.session_state.routes = create_starting_routes()
    st.session_state.bookings = []
    st.session_state.issued_ids = set()
    st.session_state.next_booking_counter = 1001
    st.session_state.last_booking = None
    st.session_state.last_action = None
    st.session_state.reset_confirm = False
    st.session_state.page_nav = "Dashboard"
    st.session_state.reset_notice = True


def go_to_page(page_name):
    """Switch the sidebar radio to a page after a dashboard quick action."""
    st.session_state.page_nav = page_name


def route_card(route, sequence=None):
    """Display a styled route card with a text label and a visual occupancy bar."""
    taken = route["total_seats"] - route["available_seats"]
    progress = taken / route["total_seats"] if route["total_seats"] else 0
    label = seat_status(route)
    css_class = {
        "Available": "status-available", "Partially Booked": "status-partial",
        "Fully Booked": "status-full",
    }[label]
    number = sequence if sequence is not None else route["route_id"]
    # Render the card as one HTML block so its border wraps the full contents.
    st.markdown(
        f'''<div class="route-card">
        <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap">
          <strong>{html.escape(str(number))}. {html.escape(route['route_id'])} · {html.escape(route['departure_city'])} → {html.escape(route['destination_city'])}</strong>
          <strong>{money(route['ticket_price'])}</strong>
        </div>
        <p>Departure {html.escape(route['departure_time'])} · Seats {route['available_seats']}/{route['total_seats']}</p>
        <div style="height:8px;background:#e8f0f1;border-radius:99px;overflow:hidden">
          <div style="height:8px;width:{progress * 100:.1f}%;background:#0f5965"></div>
        </div>
        <p><span class="status {css_class}">{label}</span> <span class="small-note">{taken} of {route['total_seats']} seats booked</span></p>
        </div>''',
        unsafe_allow_html=True,
    )


def ticket_text(booking, route):
    """Build a downloadable plain-text ticket without writing any file."""
    return (
        "SMART BUS RESERVATION — TICKET\n"
        "================================\n"
        f"Booking ID: {booking['booking_id']}\n"
        f"Passenger: {booking['passenger_name']}\n"
        f"Age: {booking['passenger_age']}\n"
        f"Route: {route['route_id']} ({route['departure_city']} -> {route['destination_city']})\n"
        f"Departure time: {route['departure_time']}\n"
        f"Seats booked: {booking['seats']}\n"
        f"Fare per seat: {money(route['ticket_price'])}\n"
        f"Total fare: {money(booking['total_fare'])}\n"
        f"Status: {booking['status']}\n"
    )


def page_dashboard():
    """Show headline totals, next departures, and shortcuts."""
    st.title("Your journey starts here")
    st.caption("A simple way to explore routes, reserve seats and manage tickets.")
    report = build_report(st.session_state.routes, st.session_state.bookings)
    metrics = st.columns(4)
    metrics[0].metric("Total routes", len(st.session_state.routes))
    metrics[1].metric("Seats available", sum(route["available_seats"] for route in st.session_state.routes))
    metrics[2].metric("Confirmed bookings", report["confirmed_bookings"])
    metrics[3].metric("Confirmed revenue", money(report["confirmed_revenue"]))
    st.subheader("Next departures")
    cols = st.columns(len(st.session_state.routes))
    for col, route in zip(cols, st.session_state.routes):
        with col:
            status = seat_status(route)
            status_class = {
                "Available": "status-available", "Partially Booked": "status-partial",
                "Fully Booked": "status-full",
            }[status]
            st.markdown(
                f'''<div class="route-card">
                <strong>{html.escape(route['route_id'])}</strong>
                <p>{html.escape(route['departure_city'])} → {html.escape(route['destination_city'])}</p>
                <p>{html.escape(route['departure_time'])}</p>
                <strong>{money(route['ticket_price'])}</strong>
                <p>{route['available_seats']} seats left</p>
                <span class="status {status_class}">{status}</span>
                </div>''',
                unsafe_allow_html=True,
            )
    if not st.session_state.bookings:
        st.info("No bookings yet. Book a ticket to see your activity here.")
    st.subheader("Quick actions")
    first, second = st.columns(2)
    with first:
        st.button("🎟️ Book a Ticket", on_click=go_to_page, args=("Book a Ticket",), use_container_width=True)
    with second:
        st.button("🔎 Search routes", on_click=go_to_page, args=("Search",), use_container_width=True)


def page_routes():
    """List every route and optionally hide routes with no free seats."""
    st.title("View Routes")
    available_only = st.toggle("Show only routes with seats available", value=False)
    routes = st.session_state.routes
    shown = [route for route in routes if not available_only or route["available_seats"] > 0]
    if not shown:
        st.info("No routes match the selected filter.")
    for route in shown:
        route_card(route, routes.index(route) + 1)


def page_search():
    """Search by route ID or exact city, with a supported-city quick filter."""
    st.title("Search routes")
    left, right = st.columns([2, 1])
    with left:
        query = st.text_input("Route ID or city", placeholder="Try R101 or hyderabad", key="search_query")
    with right:
        city_filter = st.selectbox("Quick city filter", ["All cities", *SUPPORTED_CITIES], key="search_city_filter")
    matches = search_routes(st.session_state.routes, query, city_filter)
    if query.strip() or city_filter != "All cities":
        if matches:
            for route in matches:
                st.markdown(
                    f"**{route['route_id']} | {route['departure_city']} -> {route['destination_city']} | "
                    f"{money(route['ticket_price'])} | {route['available_seats']} seats available**"
                )
                badge(seat_status(route))
                st.divider()
        else:
            st.info("No matching route found. Try a route ID or a supported city name.")
    else:
        st.caption("Enter a route ID or city, or choose a city filter to see matching routes.")


def page_booking():
    """Collect booking inputs in a form, validate centrally, and show a ticket."""
    st.title("Book a Ticket")
    st.caption("Your fare is calculated from the selected route and number of seats.")
    routes = st.session_state.routes
    # Keep stable route IDs as widget values; labels may change when seat counts change.
    routes_by_id = {route["route_id"]: route for route in routes}
    route_ids = list(routes_by_id)
    def route_label(route_id):
        route = routes_by_id[route_id]
        return (f"{route['route_id']} - {route['departure_city']} -> {route['destination_city']} "
                f"({route['available_seats']} left)")

    with st.form("booking_form", clear_on_submit=True):
        name_col, age_col = st.columns([2, 1])
        passenger_name = name_col.text_input("Passenger name", key="booking_name")
        passenger_age = age_col.number_input("Age", min_value=1, step=1, value=18, key="booking_age")
        selected_route_id = st.selectbox("Route", route_ids, format_func=route_label, key="booking_route")
        seats_col, preview_col = st.columns([1, 2])
        seats = seats_col.number_input("Seats", min_value=1, step=1, value=1, key="booking_seats")
        selected_route = routes_by_id[selected_route_id]
        preview_col.metric("Live fare preview", money(selected_route["ticket_price"] * int(seats)))
        submitted = st.form_submit_button("Confirm booking", use_container_width=True)

    if submitted:
        result = create_booking(
            st.session_state.routes, st.session_state.bookings, st.session_state.issued_ids,
            st.session_state.next_booking_counter, passenger_name, passenger_age,
            selected_route["route_id"], seats,
        )
        if not result["success"]:
            st.error(result["error"])
        else:
            # The form submit event is one-shot; save the result for later reruns.
            st.session_state.next_booking_counter = result["next_booking_counter"]
            st.session_state.last_booking = result["booking"]
            st.session_state.last_action = ("booking", result["booking"]["booking_id"])
            st.success(f"Booking confirmed! Your booking ID is {result['booking']['booking_id']}.")
            st.toast("Ticket booked successfully!", icon="🎟️")
            st.balloons()

    booking = st.session_state.last_booking
    if booking:
        route = find_route(st.session_state.routes, booking["route_id"])
        if route:
            st.subheader("Your ticket")
            # Escape passenger text before placing it into the ticket's HTML card.
            st.markdown(
                f'''<div class="ticket-card">
                <h3>Booking {html.escape(booking['booking_id'])}</h3>
                <p><strong>Passenger:</strong> {html.escape(booking['passenger_name'])}</p>
                <p><strong>Route:</strong> {html.escape(route['departure_city'])} → {html.escape(route['destination_city'])} ({html.escape(route['route_id'])})</p>
                <p><strong>Departure time:</strong> {html.escape(route['departure_time'])}</p>
                <p><strong>Seats booked:</strong> {booking['seats']}</p>
                <p><strong>Fare per seat:</strong> {money(route['ticket_price'])}</p>
                <p><strong>Total fare:</strong> {money(booking['total_fare'])}</p>
                <p><span class="status status-confirmed">Confirmed</span></p>
                </div>''',
                unsafe_allow_html=True,
            )
            st.download_button(
                "Download ticket (.txt)", data=ticket_text(booking, route),
                file_name=f"{booking['booking_id']}_ticket.txt", mime="text/plain",
            )


def page_bookings():
    """Display all booking records, with status and ID filters."""
    st.title("My Bookings")
    status_filter = st.radio("Show", ["All", "Confirmed", "Cancelled"], horizontal=True, key="bookings_filter")
    search_id = st.text_input("Search booking ID (optional)", placeholder="B1001", key="bookings_search").strip().upper()
    rows = []
    for number, booking in enumerate(st.session_state.bookings, start=1):
        if status_filter != "All" and booking["status"] != status_filter:
            continue
        if search_id and search_id not in booking["booking_id"].upper():
            continue
        rows.append({
            "No.": number, "Booking ID": booking["booking_id"],
            "Passenger": booking["passenger_name"], "Route": booking["route_id"],
            "Seats": booking["seats"], "Fare": money(booking["total_fare"]),
            "Status": booking["status"],
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No bookings found.")


def page_cancel():
    """Summarize a selected booking and require confirmation before cancellation."""
    st.title("Cancel a Booking")
    confirmed = [booking for booking in st.session_state.bookings if booking["status"] == "Confirmed"]
    shortcut_options = ["Choose a confirmed booking"] + [
        f"{booking['booking_id']} — {booking['passenger_name']} ({booking['route_id']})"
        for booking in confirmed
    ]
    shortcut = st.selectbox("Confirmed bookings", shortcut_options, key="cancel_shortcut")
    typed_id = st.text_input("Booking ID", placeholder="B1001", key="cancel_booking_id")
    chosen_id = typed_id.strip().upper()
    if shortcut != shortcut_options[0]:
        chosen_id = shortcut.split(" — ", 1)[0].strip().upper()
    target = next((booking for booking in st.session_state.bookings
                   if booking["booking_id"].upper() == chosen_id), None)
    if chosen_id and target:
        route = find_route(st.session_state.routes, target["route_id"])
        st.markdown(f"**{target['booking_id']} · {target['passenger_name']} · Route {target['route_id']} · "
                    f"{target['seats']} seat(s) · {money(target['total_fare'])}**")
        badge(target["status"])
        if target["status"] == "Cancelled":
            st.info(f"Booking {target['booking_id']} has already been cancelled. No seats were restored.")
    elif chosen_id:
        st.caption("The booking ID will be checked when you press Cancel booking.")
    confirm = st.checkbox("I understand this booking will be cancelled.", key="cancel_confirm")
    if st.button("Cancel booking", type="primary", disabled=not confirm, use_container_width=True):
        if not chosen_id:
            st.error("Enter a booking ID or choose a confirmed booking.")
        else:
            result = cancel_booking(st.session_state.routes, st.session_state.bookings, chosen_id)
            if not result["success"]:
                st.error(result["error"])
            else:
                st.success(result["message"])
                st.toast("Booking cancelled.", icon="↩️")
                st.session_state.last_action = ("cancel", chosen_id)


def page_availability():
    """Show seat counts, status badges, progress bars, and a simple bar chart."""
    st.title("Seat Availability")
    available_only = st.toggle("Show only routes with seats available", value=False, key="availability_only")
    routes = st.session_state.routes
    shown = [route for route in routes if not available_only or route["available_seats"] > 0]
    for route in shown:
        st.markdown(f"**{route['route_id']} · {route['departure_city']} → {route['destination_city']}**")
        st.caption(f"{route['available_seats']} / {route['total_seats']} seats available")
        taken = route["total_seats"] - route["available_seats"]
        st.progress(taken / route["total_seats"], text=f"{taken} seat(s) booked")
        badge(seat_status(route))
        st.divider()
    if not shown:
        st.info("No routes match the selected filter.")
    if routes:
        st.subheader("Available seats by route")
        chart_data = pd.DataFrame(
            {"Available seats": [route["available_seats"] for route in routes]},
            index=[route["route_id"] for route in routes],
        )
        st.bar_chart(chart_data)


def page_reports():
    """Display report metrics, route-level aggregates, and departure schedule."""
    st.title("Reports")
    routes = st.session_state.routes
    bookings = st.session_state.bookings
    report = build_report(routes, bookings)
    metric_rows = st.columns(3)
    metric_rows[0].metric("Total bookings created", report["total_bookings"])
    metric_rows[1].metric("Confirmed", report["confirmed_bookings"])
    metric_rows[2].metric("Cancelled", report["cancelled_bookings"])
    metric_rows2 = st.columns(3)
    metric_rows2[0].metric("Seats currently reserved", report["reserved_seats"])
    metric_rows2[1].metric("Confirmed revenue", money(report["confirmed_revenue"]))
    metric_rows2[2].metric("Fully booked routes", report["fully_booked_routes"])
    st.subheader("Confirmed bookings by route")
    display_rows = []
    for item in report["by_route"]:
        display_rows.append({
            "Route": item["route_id"], "Journey": item["journey"],
            "Confirmed bookings": item["confirmed_bookings"],
            "Confirmed seats": item["confirmed_seats"],
            "Confirmed revenue": money(item["confirmed_revenue"]),
        })
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    chart_data = pd.DataFrame(
        {"Confirmed bookings": [item["confirmed_bookings"] for item in report["by_route"]],
         "Confirmed seats": [item["confirmed_seats"] for item in report["by_route"]]},
        index=[item["route_id"] for item in report["by_route"]],
    )
    st.bar_chart(chart_data)
    with st.expander("Route Schedule"):
        for group in build_schedule(routes):
            st.markdown(f"**{group['city']}**")
            if not group["departures"]:
                st.caption("No scheduled departures.")
            else:
                for departure in group["departures"]:
                    st.write(f"{departure['route_id']} → {departure['destination_city']} | {departure['departure_time']}")


# Initialise shared session data before rendering any page.
initialise_state()

with st.sidebar:
    st.markdown("## 🚌 Smart Bus")
    st.caption("Reservation & route management")
    pages = [
        "Dashboard", "View Routes", "Search", "Book a Ticket",
        "My Bookings", "Cancel a Booking", "Seat Availability", "Reports",
    ]
    if "page_nav" not in st.session_state:
        st.session_state.page_nav = "Dashboard"
    st.radio("Navigate", pages, key="page_nav")
    st.divider()
    st.markdown("**Demo data**")
    st.caption("Routes and bookings live only in this browser session. They are not saved to a database or file.")
    st.checkbox("Confirm reset of demo data", key="reset_confirm")
    if st.button("Reset demo data", use_container_width=True, on_click=reset_demo_data):
        # The callback runs before this script rerenders, so widget state can be reset safely.
        pass
    if st.session_state.get("reset_notice", False):
        st.success("Demo data has been reset.")
        st.session_state.reset_notice = False
    elif not st.session_state.reset_confirm:
        # The warning appears only after the user attempts an unconfirmed reset.
        if st.session_state.get("reset_warning", False):
            st.warning("Tick the confirmation checkbox before resetting.")
            st.session_state.reset_warning = False

page_functions = {
    "Dashboard": page_dashboard,
    "View Routes": page_routes,
    "Search": page_search,
    "Book a Ticket": page_booking,
    "My Bookings": page_bookings,
    "Cancel a Booking": page_cancel,
    "Seat Availability": page_availability,
    "Reports": page_reports,
}
page_functions[st.session_state.page_nav]()
