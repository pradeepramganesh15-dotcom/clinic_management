import frappe


def get_context(context):
    context.title = "Our Team"
    context.no_cache = True

    context.users = frappe.get_all(
        "User",
        filters={"enabled": 1},
        fields=["full_name", "email"],
        order_by="full_name asc",
    )