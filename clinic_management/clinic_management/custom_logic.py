import frappe


def custom_logic(doc, method):
    frappe.msgprint("Hook executed!")
