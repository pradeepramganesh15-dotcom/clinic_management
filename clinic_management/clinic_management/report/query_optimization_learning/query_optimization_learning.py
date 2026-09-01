import frappe

def execute(filters=None):
    # 1. Report Headers/Columns Setup
    columns = [
        {"label": "Patient", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 150},
        {"label": "Doctor", "fieldname": "doctor", "fieldtype": "Link", "options": "Doctor", "width": 150},
        {"label": "Appointment Date", "fieldname": "appointment_date", "fieldtype": "Date", "width": 130},
        {"label": "Appointment Time", "fieldname": "appointment_time", "fieldtype": "Time", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Token", "fieldname": "token", "fieldtype": "Int", "width": 80}
    ]

    # 2. Database Fetch (Appointment Doctype Data)
    data = frappe.get_all(
        "Appointment",
        fields=[
            "patient",
            "patient_name",
            "doctor",
            "appointment_date",
            "appointment_time",
            "status",
            "token"
        ],
        order_by="appointment_date desc"
    )

    # 3. Return Columns and Data to Frontend
    return columns, data