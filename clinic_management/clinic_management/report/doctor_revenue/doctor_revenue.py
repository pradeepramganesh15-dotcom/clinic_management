import frappe


def execute(filters=None):

    columns = [
        {
            "label": "Doctor",
            "fieldname": "doctor",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Consultation Revenue",
            "fieldname": "consultation_revenue",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": "Medicine Revenue",
            "fieldname": "medicine_revenue",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": "Total Revenue",
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 180
        }
    ]

    data = frappe.db.sql("""
        SELECT
            d.doctor_name AS doctor,
            SUM(i.consultation_fee) AS consultation_revenue,
            SUM(i.medicine_charges) AS medicine_revenue,
            SUM(i.total_amount) AS total_revenue

        FROM `tabInvoice` i

        LEFT JOIN `tabAppointment` a
            ON a.patient = i.patient

        LEFT JOIN `tabDoctor` d
            ON d.name = a.doctor

        GROUP BY d.doctor_name

        ORDER BY total_revenue DESC
    """, as_dict=True)

    return columns, data