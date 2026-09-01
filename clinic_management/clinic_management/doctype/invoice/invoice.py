import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Invoice(Document):

    def validate(self):
        self.calculate_payment_details()

    def calculate_payment_details(self):
        """
        Calculate outstanding amount and payment status.
        """

        total_amount = flt(self.total_amount)
        paid_amount = flt(self.paid_amount)

        # Prevent negative paid amount
        if paid_amount < 0:
            paid_amount = 0
            self.paid_amount = 0

        # Paid amount cannot exceed total amount
        if paid_amount > total_amount:
            frappe.throw(
                "Paid Amount cannot be greater than Total Amount."
            )

        outstanding_amount = total_amount - paid_amount

        if outstanding_amount < 0:
            outstanding_amount = 0

        self.outstanding_amount = outstanding_amount

        # Payment status
        if paid_amount <= 0:
            self.payment_status = "Unpaid"

        elif outstanding_amount == 0:
            self.payment_status = "Fully Paid"

        else:
            self.payment_status = "Partially Paid"

    def on_submit(self):
        """
        Add this Invoice's outstanding amount
        to the Patient's overall outstanding balance.
        """

        self.update_patient_outstanding_balance()

    def on_cancel(self):
        """
        Recalculate Patient's outstanding balance
        after this Invoice is cancelled.
        """

        self.update_patient_outstanding_balance()

    def update_patient_outstanding_balance(self):
        """
        Calculate total outstanding amount from all
        submitted invoices belonging to this patient.
        """

        if not self.patient:
            return

        outstanding_balance = frappe.db.sql(
            """
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabInvoice`
            WHERE patient = %s
            AND docstatus = 1
            """,
            self.patient
        )[0][0]

        outstanding_balance = flt(outstanding_balance)

        frappe.db.set_value(
            "Patient",
            self.patient,
            "outstanding_balance",
            outstanding_balance
        )