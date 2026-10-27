"""Functions for looking up, searching, and displaying bus routes."""

from data import routes


def find_route(route_id):
    """Return a route dictionary by case-insensitive ID, or None if absent."""
    route_id = route_id.strip().upper()
    for route in routes:
        if route["route_id"] == route_id:
            return route
    # The for-else branch runs only when the loop did not return a match.
    else:
        return None


def ask_available_only():
    """Ask whether to hide routes that have no free seats; return a Boolean."""
    answer = input("Show available routes only? (y/n): ").strip().lower()
    return answer == "y"


def show_routes():
    """Display all routes or skip fully booked ones when the filter is enabled."""
    available_only = ask_available_only()
    print("\nAVAILABLE BUS ROUTES")
    print("No. Route Journey                         Depart     Fare       Seats")
    shown = 0
    for number, route in enumerate(routes, start=1):
        if available_only and route["available_seats"] == 0:
            continue  # Skip full routes only when the user requested the filter.
        shown += 1
        journey = route["departure_city"] + " -> " + route["destination_city"]
        seats = str(route["available_seats"]) + "/" + str(route["total_seats"])
        if route["available_seats"] == 0:
            seats += " Fully Booked"
        print(f"{number} {route['route_id']} {journey:<32} {route['departure_time']:<10} Rs.{route['ticket_price']} {seats}")
    if shown == 0:
        print("No routes match the selected filter.")


def print_route_result(route):
    """Print one route in the required search-result format."""
    print(f"{route['route_id']} | {route['departure_city']} -> {route['destination_city']} | Rs. {route['ticket_price']} | {route['available_seats']} seats available")


def search_routes():
    """Search by route ID or exact departure/destination city name."""
    query = input("Enter route ID or city: ").strip()
    if not query:
        print("Search cannot be empty.")
        return

    # Route IDs are case-insensitive; city searches use exact case-insensitive matches.
    if query.upper().startswith("R"):
        route = find_route(query)
        if route is None:
            print("No matching route found.")
        else:
            print_route_result(route)
        return

    city_query = query.lower()
    found = False
    for route in routes:
        if route["departure_city"].lower() == city_query or route["destination_city"].lower() == city_query:
            print_route_result(route)
            found = True
    if not found:
        print("No matching route found. Enter a route ID or a supported city name.")


def show_availability():
    """Display available/total seats and a status for each route."""
    available_only = ask_available_only()
    print("\nSEAT AVAILABILITY")
    shown = 0
    for route in routes:
        if available_only and route["available_seats"] == 0:
            continue
        available = route["available_seats"]
        total = route["total_seats"]
        if available == 0:
            status = "Fully Booked"
        elif available == total:
            status = "Available"
        else:
            status = "Partially Booked"
        print(f"{route['route_id']} | {route['departure_city']} -> {route['destination_city']} | {available}/{total} seats | {status}")
        shown += 1
    if shown == 0:
        print("No routes match the selected filter.")
