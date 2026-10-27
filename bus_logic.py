"""Pure business rules for Smart Bus Reservation.

This module intentionally does not import Streamlit and never reads input or
prints output. The UI and the unit tests can call these functions directly.
"""
SUPPORTED_CITIES = ("Karachi", "Hyderabad", "Sukkur", "Mirpur Khas", "Lahore")


def create_starting_routes():
    """Return fresh copies of the five original routes for a new demo session."""
    return [
        {"route_id": "R101", "departure_city": "Karachi", "destination_city": "Hyderabad", "departure_time": "08:00 AM", "ticket_price": 1200, "total_seats": 40, "available_seats": 40},
        {"route_id": "R102", "departure_city": "Karachi", "destination_city": "Sukkur", "departure_time": "09:30 AM", "ticket_price": 2000, "total_seats": 36, "available_seats": 36},
        {"route_id": "R103", "departure_city": "Hyderabad", "destination_city": "Mirpur Khas", "departure_time": "11:00 AM", "ticket_price": 800, "total_seats": 32, "available_seats": 32},
        {"route_id": "R104", "departure_city": "Karachi", "destination_city": "Lahore", "departure_time": "07:00 PM", "ticket_price": 5000, "total_seats": 45, "available_seats": 45},
        {"route_id": "R105", "departure_city": "Sukkur", "destination_city": "Hyderabad", "departure_time": "02:00 PM", "ticket_price": 1500, "total_seats": 30, "available_seats": 30},
    ]


def find_route(routes, route_id):
    """Find a route by ID after trimming spaces and ignoring case; else None."""
    normalized_id = str(route_id).strip().upper()
    for route in routes:
        if route["route_id"] == normalized_id:
            return route
    return None


def search_routes(routes, query="", city_filter="All cities"):
    """Return route-ID or exact city matches, optionally narrowed by a city filter."""
    cleaned = str(query).strip()
    if cleaned.upper().startswith("R"):
        matches = []
        route = find_route(routes, cleaned)
        if route is not None:
            matches.append(route)
    elif cleaned:
        city = cleaned.lower()
        matches = [
            route for route in routes
            if route["departure_city"].lower() == city
            or route["destination_city"].lower() == city
        ]
    else:
        matches = list(routes)

    if city_filter and city_filter != "All cities":
        matches = [
            route for route in matches
            if route["departure_city"] == city_filter
            or route["destination_city"] == city_filter
        ]
    return matches


def validate_booking_inputs(routes, passenger_name, passenger_age, route_id, seats):
    """Validate all booking fields without mutating routes, bookings, or IDs.

    Returns {"valid": bool, "error": str, ...}. The first failed rule is returned.
    """
    if not isinstance(passenger_name, str) or not passenger_name.strip():
        return {"valid": False, "error": "Passenger name cannot be empty."}

    try:
        # Reject fractional values rather than silently converting them to integers.
        age = int(passenger_age)
        if isinstance(passenger_age, float) and not passenger_age.is_integer():
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "error": "Age must be a positive whole number."}
    if age <= 0:
        return {"valid": False, "error": "Age must be greater than zero."}

    route = find_route(routes, route_id)
    if route is None:
        return {"valid": False, "error": "Route ID does not exist."}

    try:
        seat_count = int(seats)
        if isinstance(seats, float) and not seats.is_integer():
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "error": "Number of seats must be a whole number greater than zero."}
    if seat_count <= 0:
        return {"valid": False, "error": "Number of seats must be greater than zero."}
    if seat_count > route["available_seats"]:
        return {"valid": False, "error": f"Only {route['available_seats']} seats are available on {route['route_id']}."}

    return {
        "valid": True,
        "error": "",
        "passenger_name": passenger_name.strip(),
        "passenger_age": age,
        "route": route,
        "route_id": route["route_id"],
        "seats": seat_count,
    }


def create_booking(routes, bookings, issued_ids, next_booking_counter,
                   passenger_name, passenger_age, route_id, seats):
    """Create a booking only after every input validates; return result and next ID counter."""
    validation = validate_booking_inputs(
        routes, passenger_name, passenger_age, route_id, seats
    )
    if not validation["valid"]:
        return {"success": False, "error": validation["error"], "booking": None,
                "next_booking_counter": next_booking_counter}

    # Find an unused ID before mutating any shared state.
    counter = int(next_booking_counter)
    while "B" + str(counter) in issued_ids:
        counter += 1
    booking_id = "B" + str(counter)
    route = validation["route"]
    seat_count = validation["seats"]
    booking = {
        "booking_id": booking_id,
        "passenger_name": validation["passenger_name"],
        "passenger_age": validation["passenger_age"],
        "route_id": route["route_id"],
        "seats": seat_count,
        "total_fare": route["ticket_price"] * seat_count,
        "status": "Confirmed",
    }

    # All validation and ID selection are complete. Apply the successful action once.
    route["available_seats"] -= seat_count
    bookings.append(booking)
    issued_ids.add(booking_id)
    return {"success": True, "error": "", "booking": booking,
            "next_booking_counter": counter + 1}


def cancel_booking(routes, bookings, booking_id):
    """Cancel a Confirmed booking and restore its seats once, keeping its record."""
    normalized_id = str(booking_id).strip().upper()
    booking = None
    for candidate in bookings:
        if candidate["booking_id"].upper() == normalized_id:
            booking = candidate
            break
    if booking is None:
        return {"success": False, "error": "Booking ID not found. No changes made.",
                "booking": None, "seats_restored": 0, "route": None}
    if booking["status"] == "Cancelled":
        return {"success": False,
                "error": f"Booking {normalized_id} has already been cancelled. No seats were restored.",
                "booking": booking, "seats_restored": 0, "route": find_route(routes, booking["route_id"])}
    route = find_route(routes, booking["route_id"])
    if route is None:
        return {"success": False,
                "error": "The booking's route could not be found; no changes made.",
                "booking": booking, "seats_restored": 0, "route": None}

    # Restore the booked quantity only on the original route and only on first cancellation.
    restored = booking["seats"]
    route["available_seats"] = min(route["total_seats"], route["available_seats"] + restored)
    booking["status"] = "Cancelled"
    return {"success": True, "error": "",
            "message": (f"Booking {normalized_id} has been cancelled. Seats restored: {restored}. "
                        f"Route {route['route_id']} available seats: {route['available_seats']}"),
            "booking": booking, "seats_restored": restored, "route": route}


def seat_status(route):
    """Return a readable status label for a route's current seat count."""
    if route["available_seats"] == 0:
        return "Fully Booked"
    if route["available_seats"] == route["total_seats"]:
        return "Available"
    return "Partially Booked"


def build_report(routes, bookings):
    """Build consistent summary totals and per-route confirmed booking statistics."""
    confirmed = [booking for booking in bookings if booking["status"] == "Confirmed"]
    cancelled = [booking for booking in bookings if booking["status"] == "Cancelled"]
    by_route = []
    # Required nested loop: every route is compared against every booking.
    for route in routes:
        route_bookings = 0
        route_seats = 0
        route_revenue = 0
        for booking in bookings:
            if booking["route_id"] == route["route_id"] and booking["status"] == "Confirmed":
                route_bookings += 1
                route_seats += booking["seats"]
                route_revenue += booking["total_fare"]
        by_route.append({
            "route_id": route["route_id"],
            "journey": f"{route['departure_city']} -> {route['destination_city']}",
            "confirmed_bookings": route_bookings,
            "confirmed_seats": route_seats,
            "confirmed_revenue": route_revenue,
        })
    return {
        "total_bookings": len(bookings),
        "confirmed_bookings": len(confirmed),
        "cancelled_bookings": len(cancelled),
        "reserved_seats": sum(booking["seats"] for booking in confirmed),
        "confirmed_revenue": sum(booking["total_fare"] for booking in confirmed),
        "fully_booked_routes": sum(1 for route in routes if route["available_seats"] == 0),
        "by_route": by_route,
    }


def build_schedule(routes, supported_cities=SUPPORTED_CITIES):
    """Return departures grouped in supported-city order, including empty cities."""
    schedule = []
    # Keep the same outer-city / inner-route ordering as the console report.
    for city in supported_cities:
        departures = []
        for route in routes:
            if route["departure_city"] == city:
                departures.append({
                    "route_id": route["route_id"],
                    "destination_city": route["destination_city"],
                    "departure_time": route["departure_time"],
                })
        schedule.append({"city": city, "departures": departures})
    return schedule
