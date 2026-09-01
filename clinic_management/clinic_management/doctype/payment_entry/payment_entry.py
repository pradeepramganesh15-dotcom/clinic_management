import frappe
from frappe.model.document import Document
from frappe.utils import today, flt


class PaymentEntry(Document):

    def validate(self):
        self.set_payment_date()
        self.fetch_patient()
        self.set_payment_amount()
        self.validate_payment_amount()

    def set_payment_date(self):
        """Set today's date automatically."""
        if not self.payment_date:
            self.payment_date = today()

    def fetch_patient(self):
        """Fetch patient from selected Invoice."""

        if not self.invoice:
            return

        patient = frappe.db.get_value(
            "Invoice",
            self.invoice,
            "patient"
        )

        if patient:
            self.patient = patient

    def set_payment_amount(self):
        """Automatically set amount to Invoice outstanding amount."""

        if not self.invoice:
            return

        invoice = frappe.get_doc(
            "Invoice",
            self.invoice
        )

        total_amount = flt(invoice.total_amount)
        paid_amount = flt(invoice.paid_amount)

        outstanding_amount = total_amount - paid_amount

        if outstanding_amount < 0:
            outstanding_amount = 0

        # Auto-fill only when amount is empty
        if not self.amount and outstanding_amount > 0:
            self.amount = outstanding_amount

    def validate_payment_amount(self):
        """Validate payment against current Invoice outstanding."""

        if not self.invoice:
            frappe.throw(
                "Please select an Invoice."
            )

        if not self.amount or flt(self.amount) <= 0:
            frappe.throw(
                "Payment amount must be greater than 0."
            )

        invoice = frappe.get_doc(
            "Invoice",
            self.invoice
        )

        total_amount = flt(invoice.total_amount)
        paid_amount = flt(invoice.paid_amount)

        outstanding_amount = total_amount - paid_amount

        if outstanding_amount <= 0:
            frappe.throw(
                f"Invoice {invoice.name} is already fully paid."
            )

        if flt(self.amount) > outstanding_amount:
            frappe.throw(
                f"Payment amount cannot be greater than "
                f"outstanding amount {outstanding_amount:.2f}."
            )

    def on_submit(self):
        """Update Invoice when Payment Entry is submitted."""

        self.process_payment()

    def process_payment(self):
        """Add payment amount to Invoice."""

        invoice = frappe.get_doc(
            "Invoice",
            self.invoice
        )

        total_amount = flt(invoice.total_amount)
        current_paid = flt(invoice.paid_amount)
        payment_amount = flt(self.amount)

        new_paid_amount = current_paid + payment_amount

        new_outstanding_amount = (
            total_amount - new_paid_amount
        )

        if new_outstanding_amount < 0:
            new_outstanding_amount = 0

        # Determine payment status
        if new_paid_amount <= 0:
            payment_status = "Unpaid"

        elif new_outstanding_amount == 0:
            payment_status = "Fully Paid"

        else:
            payment_status = "Partially Paid"

        # Update Invoice
        frappe.db.set_value(
            "Invoice",
            invoice.name,
            {
                "paid_amount": new_paid_amount,
                "outstanding_amount": new_outstanding_amount,
                "payment_status": payment_status
            }
        )

        # Update Payment Entry status
        frappe.db.set_value(
            "Payment Entry",
            self.name,
            "status",
            "Paid"
        )

        frappe.msgprint(
            f"Payment of ₹{payment_amount:.2f} recorded successfully.<br>"
            f"Invoice: {invoice.name}<br>"
            f"Paid Amount: ₹{new_paid_amount:.2f}<br>"
            f"Outstanding Amount: ₹{new_outstanding_amount:.2f}<br>"
            f"Payment Status: {payment_status}"
        )

    def on_cancel(self):
        """Reverse payment when Payment Entry is cancelled."""

        self.reverse_payment()

    def reverse_payment(self):
        """Subtract cancelled payment from Invoice."""

        invoice = frappe.get_doc(
            "Invoice",
            self.invoice
        )

        total_amount = flt(invoice.total_amount)
        current_paid = flt(invoice.paid_amount)
        payment_amount = flt(self.amount)

        new_paid_amount = current_paid - payment_amount

        if new_paid_amount < 0:
            new_paid_amount = 0

        new_outstanding_amount = (
            total_amount - new_paid_amount
        )

        if new_outstanding_amount < 0:
            new_outstanding_amount = 0

        # Determine payment status
        if new_paid_amount <= 0:
            payment_status = "Unpaid"

        elif new_outstanding_amount == 0:
            payment_status = "Fully Paid"

        else:
            payment_status = "Partially Paid"

        # Update Invoice
        frappe.db.set_value(
            "Invoice",
            invoice.name,
            {
                "paid_amount": new_paid_amount,
                "outstanding_amount": new_outstanding_amount,
                "payment_status": payment_status
            }
        )

        # Reset Payment Entry status
        frappe.db.set_value(
            "Payment Entry",
            self.name,
            "status",
            "Pending"
        )

        frappe.msgprint(
            f"Payment of ₹{payment_amount:.2f} reversed successfully.<br>"
            f"Invoice: {invoice.name}<br>"
            f"Paid Amount: ₹{new_paid_amount:.2f}<br>"
            f"Outstanding Amount: ₹{new_outstanding_amount:.2f}<br>"
            f"Payment Status: {payment_status}"
        )