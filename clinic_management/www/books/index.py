import frappe

def get_context(context):
    # Set web page meta title
    context.title = "Book Library"
    
    # Fetch all books with matching doctype fields
    context.books = frappe.get_all(
        "Book",
        fields=[
            "name",
            "book_name",
            "author",
            "price",
            "available_qty",
            "rating",
            "status"
        ],
        order_by="creation desc"
    )

    context.total_books = frappe.db.count("Book")
    return context