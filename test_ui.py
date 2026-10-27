"""Automated tests for pure bus logic and the Streamlit UI.

Run with: python -m unittest -v test_ui.py
The business-rule tests need only the Python standard library. AppTest tests
are skipped if the optional Streamlit dependency is not installed.
"""
import unittest

from bus_logic import (
    SUPPORTED_CITIES, build_report, build_schedule, cancel_booking,
    create_booking, create_starting_routes, find_route, search_routes,
    seat_status, validate_booking_inputs,
)


class BusLogicTests(unittest.TestCase):
    def setUp(self):
        self.routes = create_starting_routes()
        self.bookings = []
        self.issued_ids = set()
        self.counter = 1001

    def book(self, name="Ahmed", age=25, route_id="R101", seats=2):
        result = create_booking(
            self.routes, self.bookings, self.issued_ids, self.counter,
            name, age, route_id, seats,
        )
        if result["success"]:
            self.counter = result["next_booking_counter"]
        return result

    def test_starting_routes_and_supported_cities(self):
        self.assertEqual([r["route_id"] for r in self.routes],
                         ["R101", "R102", "R103", "R104", "R105"])
        self.assertEqual(SUPPORTED_CITIES,
                         ("Karachi", "Hyderabad", "Sukkur", "Mirpur Khas", "Lahore"))

    def test_find_route_normalizes_id(self):
        self.assertEqual(find_route(self.routes, " r101 ")["route_id"], "R101")
        self.assertIsNone(find_route(self.routes, "R999"))

    def test_search_route_id_and_all_city_matches(self):
        self.assertEqual([r["route_id"] for r in search_routes(self.routes, " r101 ")], ["R101"])
        self.assertEqual([r["route_id"] for r in search_routes(self.routes, " hyderabad ")],
                         ["R101", "R103", "R105"])
        self.assertEqual([r["route_id"] for r in search_routes(self.routes, "", "Karachi")],
                         ["R101", "R102", "R104"])

    def assert_invalid_without_changes(self, name, age, route_id, seats, expected):
        route_snapshot = [dict(route) for route in self.routes]
        result = self.book(name, age, route_id, seats)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], expected)
        self.assertEqual(self.routes, route_snapshot)
        self.assertEqual(self.bookings, [])
        self.assertEqual(self.issued_ids, set())
        self.assertEqual(result["next_booking_counter"], 1001)

    def test_blank_name(self):
        self.assert_invalid_without_changes("   ", 20, "R101", 1,
                                            "Passenger name cannot be empty.")

    def test_non_numeric_age(self):
        self.assert_invalid_without_changes("A", "abc", "R101", 1,
                                            "Age must be a positive whole number.")

    def test_zero_age(self):
        self.assert_invalid_without_changes("A", 0, "R101", 1,
                                            "Age must be greater than zero.")

    def test_negative_age(self):
        self.assert_invalid_without_changes("A", -4, "R101", 1,
                                            "Age must be greater than zero.")

    def test_unknown_route(self):
        self.assert_invalid_without_changes("A", 20, "R999", 1,
                                            "Route ID does not exist.")

    def test_zero_seats(self):
        self.assert_invalid_without_changes("A", 20, "R101", 0,
                                            "Number of seats must be greater than zero.")

    def test_non_numeric_seats(self):
        self.assert_invalid_without_changes("A", 20, "R101", "x",
                                            "Number of seats must be a whole number greater than zero.")

    def test_more_than_available(self):
        self.assert_invalid_without_changes("A", 20, "R101", 41,
                                            "Only 40 seats are available on R101.")

    def test_exactly_all_remaining_seats_succeeds(self):
        result = self.book("A", 20, "R101", 40)
        self.assertTrue(result["success"])
        self.assertEqual(self.routes[0]["available_seats"], 0)
        self.assertEqual(result["booking"]["total_fare"], 48000)
        self.assertEqual(seat_status(self.routes[0]), "Fully Booked")

    def test_fare_equals_price_times_seats(self):
        result = self.book(seats=3)
        self.assertTrue(result["success"])
        self.assertEqual(result["booking"]["total_fare"],
                         self.routes[0]["ticket_price"] * 3)
        self.assertEqual(self.routes[0]["available_seats"], 37)

    def test_unique_booking_ids_skip_issued_ids(self):
        self.issued_ids.add("B1001")
        result = self.book()
        self.assertEqual(result["booking"]["booking_id"], "B1002")
        second = create_booking(self.routes, self.bookings, self.issued_ids,
                                result["next_booking_counter"], "Sara", 22, "R102", 1)
        self.assertEqual(second["booking"]["booking_id"], "B1003")
        self.assertEqual(len(self.issued_ids), 3)

    def test_cancel_confirmed_booking_restores_original_route(self):
        result = self.book(seats=2)
        cancelled = cancel_booking(self.routes, self.bookings, "b1001")
        self.assertTrue(cancelled["success"])
        self.assertEqual(self.routes[0]["available_seats"], 40)
        self.assertEqual(self.bookings[0]["status"], "Cancelled")
        self.assertEqual(cancelled["seats_restored"], 2)
        self.assertIn("Route R101 available seats: 40", cancelled["message"])

    def test_cancel_same_booking_twice_restores_once(self):
        self.book(seats=2)
        self.assertTrue(cancel_booking(self.routes, self.bookings, "B1001")["success"])
        before = self.routes[0]["available_seats"]
        second = cancel_booking(self.routes, self.bookings, "B1001")
        self.assertFalse(second["success"])
        self.assertEqual(second["seats_restored"], 0)
        self.assertEqual(self.routes[0]["available_seats"], before)
        self.assertEqual(len(self.bookings), 1)

    def test_unknown_booking_id_does_not_change_state(self):
        self.book(seats=2)
        before_routes = [dict(route) for route in self.routes]
        before_bookings = [dict(booking) for booking in self.bookings]
        result = cancel_booking(self.routes, self.bookings, "B9999")
        self.assertFalse(result["success"])
        self.assertEqual(self.routes, before_routes)
        self.assertEqual(self.bookings, before_bookings)

    def test_cancelled_records_are_kept(self):
        self.book()
        cancel_booking(self.routes, self.bookings, "B1001")
        self.assertEqual(len(self.bookings), 1)
        self.assertEqual(self.bookings[0]["status"], "Cancelled")

    def test_seat_invariant_after_book_and_cancel(self):
        self.book(seats=5)
        cancel_booking(self.routes, self.bookings, "B1001")
        for route in self.routes:
            self.assertGreaterEqual(route["available_seats"], 0)
            self.assertLessEqual(route["available_seats"], route["total_seats"])

    def test_report_totals_reconcile_confirmed_records_only(self):
        self.book(seats=2)
        create_booking(self.routes, self.bookings, self.issued_ids,
                       self.counter, "Sara", 30, "R102", 3)
        cancel_booking(self.routes, self.bookings, "B1001")
        report = build_report(self.routes, self.bookings)
        confirmed = [b for b in self.bookings if b["status"] == "Confirmed"]
        self.assertEqual(report["total_bookings"], 2)
        self.assertEqual(report["confirmed_bookings"], len(confirmed))
        self.assertEqual(report["cancelled_bookings"], 1)
        self.assertEqual(report["reserved_seats"], sum(b["seats"] for b in confirmed))
        self.assertEqual(report["confirmed_revenue"], sum(b["total_fare"] for b in confirmed))
        self.assertEqual(sum(item["confirmed_bookings"] for item in report["by_route"]), 1)

    def test_empty_report(self):
        report = build_report(self.routes, self.bookings)
        self.assertEqual(report["total_bookings"], 0)
        self.assertEqual(report["confirmed_bookings"], 0)
        self.assertEqual(report["cancelled_bookings"], 0)
        self.assertEqual(report["reserved_seats"], 0)
        self.assertEqual(report["confirmed_revenue"], 0)
        self.assertEqual(report["fully_booked_routes"], 0)
        self.assertTrue(all(item["confirmed_bookings"] == 0 for item in report["by_route"]))

    def test_schedule_includes_cities_without_departures(self):
        schedule = build_schedule(self.routes)
        self.assertEqual([item["city"] for item in schedule], list(SUPPORTED_CITIES))
        empty_cities = [item["city"] for item in schedule if not item["departures"]]
        self.assertEqual(empty_cities, ["Mirpur Khas", "Lahore"])
        self.assertEqual([d["route_id"] for d in schedule[0]["departures"]],
                         ["R101", "R102", "R104"])


try:
    from streamlit.testing.v1 import AppTest
    STREAMLIT_AVAILABLE = True
except ImportError:
    AppTest = None
    STREAMLIT_AVAILABLE = False


@unittest.skipUnless(STREAMLIT_AVAILABLE, "Optional Streamlit package is not installed.")
class StreamlitAppTests(unittest.TestCase):
    """Integration tests using Streamlit's own in-process AppTest harness."""

    def run_page(self, page):
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        app.radio(key="page_nav").set_value(page).run()
        self.assertEqual(len(app.exception), 0, f"{page} raised: {app.exception}")
        return app

    def click_labeled_button(self, app, label):
        # Streamlit versions may expose form-submit buttons in a dedicated list.
        candidates = []
        for collection_name in ("button", "form_submit_button"):
            collection = getattr(app, collection_name, [])
            candidates.extend(
                element for element in collection
                if label in getattr(element, "label", "")
            )
        self.assertTrue(candidates, f"Button not found: {label}")
        candidates[0].click().run()

    def test_every_page_loads(self):
        for page in ["Dashboard", "View Routes", "Search", "Book a Ticket",
                     "My Bookings", "Cancel a Booking", "Seat Availability", "Reports"]:
            with self.subTest(page=page):
                self.run_page(page)

    def test_booking_flow_and_fare(self):
        app = self.run_page("Book a Ticket")
        app.text_input(key="booking_name").set_value("Ahmed")
        app.number_input(key="booking_age").set_value(25)
        app.number_input(key="booking_seats").set_value(2)
        # Submit the only form button, then check the generated ticket and route seat count.
        self.click_labeled_button(app, "Confirm booking")
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("B1001" in element.value for element in app.markdown))
        self.assertEqual(app.session_state["routes"][0]["available_seats"], 38)
        self.assertEqual(app.session_state["bookings"][0]["total_fare"], 2400)

    def test_invalid_booking_changes_nothing(self):
        app = self.run_page("Book a Ticket")
        app.text_input(key="booking_name").set_value("   ")
        self.click_labeled_button(app, "Confirm booking")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["routes"][0]["available_seats"], 40)
        self.assertEqual(app.session_state["bookings"], [])
        self.assertTrue(any("Passenger name cannot be empty" in element.value for element in app.error))

    def test_cancel_flow(self):
        app = self.run_page("Book a Ticket")
        app.text_input(key="booking_name").set_value("Ahmed")
        app.number_input(key="booking_age").set_value(25)
        app.number_input(key="booking_seats").set_value(2)
        self.click_labeled_button(app, "Confirm booking")
        app.radio(key="page_nav").set_value("Cancel a Booking").run()
        app.text_input(key="cancel_booking_id").set_value("B1001")
        app.checkbox(key="cancel_confirm").check().run()
        self.click_labeled_button(app, "Cancel booking")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["routes"][0]["available_seats"], 40)
        self.assertEqual(app.session_state["bookings"][0]["status"], "Cancelled")

    def test_reset_button_requires_confirmation_and_resets(self):
        app = self.run_page("Book a Ticket")
        app.text_input(key="booking_name").set_value("Ahmed")
        self.click_labeled_button(app, "Confirm booking")
        app.checkbox(key="reset_confirm").check().run()
        self.click_labeled_button(app, "Reset demo data")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["bookings"], [])
        self.assertEqual(app.session_state["routes"][0]["available_seats"], 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
