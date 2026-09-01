import frappe
from frappe.tests.utils import FrappeTestCase


class TestBook(FrappeTestCase):
    # Test 1: Single Book creation test
    def test_book_creation(self):
        book = frappe.get_doc({
            "doctype": "Book",
            "book_name": "Test Book",
            "author": "Test Author",
            "price": 500,
            "available_qty": 10
        })

        book.insert()

        self.assertEqual(book.book_name, "Test Book")
        self.assertEqual(book.price, 500)
        self.assertEqual(book.available_qty, 10)

    # Test 2: Multiple Mock Data generation & verification test
    def test_create_mock_books(self):
        
        for i in range(1, 6):
            book = frappe.get_doc({
                "doctype": "Book",
                "book_name": f"Mock Book {i}",
                "author": f"Mock Author {i}",
                "price": i * 100,
                "available_qty": i * 5
            })
            book.insert()

        \
        mock_books_count = frappe.db.count("Book", filters={"book_name": ["like", "Mock Book%"]})
        self.assertEqual(mock_books_count, 5)