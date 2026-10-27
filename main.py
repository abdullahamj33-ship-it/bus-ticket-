"""Entry point for the Smart Bus Ticket Booking & Reservation System."""

from booking_functions import book_ticket, cancel_booking, show_bookings
from report_functions import generate_report
from route_functions import search_routes, show_availability, show_routes


def print_menu():
    """Display the required main menu."""
    print("\nSMART BUS RESERVATION SYSTEM")
    print("1. View Available Routes")
    print("2. Search for a Route")
    print("3. Book a Ticket")
    print("4. View My Bookings")
    print("5. Cancel a Booking")
    print("6. View Seat Availability")
    print("7. Generate Booking Report")
    print("8. Exit")
    print("================================")


def main():
    """Run the menu loop and safely handle invalid choices."""
    print("Welcome to the Smart Bus Ticket Booking & Reservation System.")
    while True:
        print_menu()
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid choice. Please enter a number from 1 to 8.")
            continue

        if choice == 1:
            show_routes()
        elif choice == 2:
            search_routes()
        elif choice == 3:
            book_ticket()
        elif choice == 4:
            show_bookings()
        elif choice == 5:
            cancel_booking()
        elif choice == 6:
            show_availability()
        elif choice == 7:
            generate_report()
        elif choice == 8:
            print("Thank you for using the Smart Bus Reservation System. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 8.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. Exiting the Smart Bus Reservation System safely.")
