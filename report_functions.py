"""Functions for the booking report and route schedule."""

from data import bookings, routes, supported_cities


def show_schedule():
    """Print departure routes grouped in the fixed supported-city order."""
    print("\nROUTE SCHEDULE BY DEPARTURE CITY")
    for city in supported_cities:  # Outer loop chooses the city order.
        print(city)
        has_departure = False
        for route in routes:  # Inner loop finds routes leaving that city.
            if route["departure_city"] == city:
                print(f"{route['route_id']} -> {route['destination_city']} | {route['departure_time']}")
                has_departure = True
        if not has_departure:
            print("No scheduled departures.")


def generate_report():
    """Print booking totals and confirmed bookings grouped by route."""
    confirmed_count = 0
    cancelled_count = 0
    reserved_seats = 0
    confirmed_revenue = 0
    for booking in bookings:
        if booking["status"] == "Confirmed":
            confirmed_count += 1
            reserved_seats += booking["seats"]
            confirmed_revenue += booking["total_fare"]
        elif booking["status"] == "Cancelled":
            cancelled_count += 1

    fully_booked_count = 0
    for route in routes:
        if route["available_seats"] == 0:
            fully_booked_count += 1

    print("\nBOOKING REPORT")
    print(f"Total bookings created: {len(bookings)}")
    print(f"Confirmed bookings: {confirmed_count}")
    print(f"Cancelled bookings: {cancelled_count}")
    print(f"Seats currently reserved: {reserved_seats}")
    print(f"Confirmed revenue: Rs. {confirmed_revenue:,}")
    print(f"Fully booked routes: {fully_booked_count}")
    print("Confirmed bookings by route:")

    # Nested loops compare every route with every booking, as required.
    for route in routes:
        route_count = 0
        route_seats = 0
        route_revenue = 0
        for booking in bookings:
            if booking["route_id"] == route["route_id"] and booking["status"] == "Confirmed":
                route_count += 1
                route_seats += booking["seats"]
                route_revenue += booking["total_fare"]
        print(f"{route['route_id']}: {route_count} confirmed booking(s), {route_seats} seat(s), Rs. {route_revenue:,}")

    # The menu has no schedule option, so display it immediately after the report.
    show_schedule()
