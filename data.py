"""Shared in-memory data for the Smart Bus Reservation System."""

# A list of dictionaries stores the starter routes and their current seat counts.
routes = [
    {"route_id": "R101", "departure_city": "Karachi", "destination_city": "Hyderabad", "departure_time": "08:00 AM", "ticket_price": 1200, "total_seats": 40, "available_seats": 40},
    {"route_id": "R102", "departure_city": "Karachi", "destination_city": "Sukkur", "departure_time": "09:30 AM", "ticket_price": 2000, "total_seats": 36, "available_seats": 36},
    {"route_id": "R103", "departure_city": "Hyderabad", "destination_city": "Mirpur Khas", "departure_time": "11:00 AM", "ticket_price": 800, "total_seats": 32, "available_seats": 32},
    {"route_id": "R104", "departure_city": "Karachi", "destination_city": "Lahore", "departure_time": "07:00 PM", "ticket_price": 5000, "total_seats": 45, "available_seats": 45},
    {"route_id": "R105", "departure_city": "Sukkur", "destination_city": "Hyderabad", "departure_time": "02:00 PM", "ticket_price": 1500, "total_seats": 30, "available_seats": 30},
]

# A tuple represents the fixed order of supported cities.
supported_cities = ("Karachi", "Hyderabad", "Sukkur", "Mirpur Khas", "Lahore")
# A set makes it easy to check whether a booking ID has already been issued.
issued_booking_ids = set()
# Booking records stay in this list, even after cancellation.
bookings = []
next_booking_number = 1001
