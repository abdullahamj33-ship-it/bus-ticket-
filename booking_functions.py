"""Functions for creating, listing, and cancelling ticket bookings."""

import data
from data import bookings, issued_booking_ids
from route_functions import find_route


def book_ticket():
    """Validate every field before creating a booking or changing seat counts."""
    passenger_name = input("Enter passenger name: ")
    if not passenger_name.strip():
        print("Error: passenger name cannot be empty.")
        return

    try:
        passenger_age = int(input("Enter passenger age: "))
    except ValueError:
        print("Error: age must be a positive whole number.")
        return
    if passenger_age <= 0:
        print("Error: age must be greater than zero.")
        return

    route_id = input("Enter route ID: ").strip().upper()
    route = find_route(route_id)
    if route is None:
        print("Error: route ID does not exist.")
        return

    try:
        seats = int(input("Enter number of seats: "))
    except ValueError:
        print("Error: seats must be a whole number greater than zero.")
        return
    if seats <= 0:
        print("Error: number of seats must be greater than zero.")
        return
    if seats > route["available_seats"]:
        print(f"Error: only {route['available_seats']} seats are available on {route['route_id']}.")
        return

    # All validation passed. Only now may shared state be changed.
    while "B" + str(data.next_booking_number) in issued_booking_ids:
        data.next_booking_number += 1
    booking_id = "B" + str(data.next_booking_number)
    data.next_booking_number += 1
    total_fare = route["ticket_price"] * seats
    booking = {
        "booking_id": booking_id,
        "passenger_name": passenger_name.strip(),
        "passenger_age": passenger_age,
        "route_id": route["route_id"],
        "seats": seats,
        "total_fare": total_fare,
        "status": "Confirmed",
    }
    bookings.append(booking)
    issued_booking_ids.add(booking_id)
    route["available_seats"] -= seats  # Decrement seats exactly once.

    print("Booking confirmed!")
    print(f"Booking ID: {booking_id}")
    print(f"Passenger: {booking['passenger_name']}")
    print(f"Route: {route['route_id']} ({route['departure_city']} -> {route['destination_city']})")
    print(f"Seats booked: {seats}")
    print(f"Fare per seat: Rs. {route['ticket_price']}")
    print(f"Total fare: Rs. {total_fare}")
    print(f"Status: {booking['status']}")


def show_bookings():
    """List every booking, including records that have been cancelled."""
    if not bookings:
        print("No bookings found.")
        return
    print("\nMY BOOKINGS")
    for number, booking in enumerate(bookings, start=1):
        print(f"{number}. {booking['booking_id']} | {booking['passenger_name']} | Route {booking['route_id']} | Seats: {booking['seats']} | Fare: Rs. {booking['total_fare']} | Status: {booking['status']}")


def cancel_booking():
    """Cancel a confirmed booking and restore its seats once only."""
    booking_id = input("Enter booking ID to cancel: ").strip().upper()
    for booking in bookings:
        if booking["booking_id"] == booking_id:
            if booking["status"] == "Cancelled":
                print(f"Booking {booking_id} has already been cancelled. No seats were restored.")
                return
            route = find_route(booking["route_id"])
            if route is None:
                print("Error: the booking's route could not be found; no changes made.")
                return
            booking["status"] = "Cancelled"
            route["available_seats"] += booking["seats"]
            # Keep the capacity invariant even if the data was manually edited.
            if route["available_seats"] > route["total_seats"]:
                route["available_seats"] = route["total_seats"]
            print(f"Booking {booking_id} has been cancelled. Seats restored: {booking['seats']} Route {route['route_id']} available seats: {route['available_seats']}")
            return
    else:
        print("Booking ID not found. No changes made.")
