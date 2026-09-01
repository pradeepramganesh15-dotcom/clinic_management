import frappe
from frappe.model.document import Document


class Prescription(Document):

    def validate(self):
        self.calculate_total_amount()

    def calculate_total_amount(self):
        total = 0

        for item in self.medicines:

            if not item.medicine:
                continue

            medicine = frappe.get_doc("Medicine", item.medicine)

            price = medicine.price_per_piece or 0
            qty = item.qty or 0

            total += price * qty

        self.total_amount = total

    # --------------------------------------------------
    # SUBMIT → REDUCE STOCK
    # --------------------------------------------------

    def on_submit(self):
        self.deduct_medicine_stock()

    def deduct_medicine_stock(self):

        # First validate ALL stock before changing anything
        for item in self.medicines:

            if not item.medicine:
                continue

            medicine = frappe.get_doc("Medicine", item.medicine)

            qty = item.qty or 0

            if qty <= 0:
                frappe.throw(
                    f"Quantity must be greater than 0 for "
                    f"{medicine.medicine_name}"
                )

            available_stock = medicine.stock_qty or 0

            if available_stock < qty:
                frappe.throw(
                    f"Insufficient stock for {medicine.medicine_name}. "
                    f"Available stock: {available_stock}, "
                    f"Required: {qty}"
                )

        # All stock validations passed → now reduce stock
        for item in self.medicines:

            if not item.medicine:
                continue

            medicine = frappe.get_doc("Medicine", item.medicine)

            qty = item.qty or 0

            medicine.stock_qty = (medicine.stock_qty or 0) - qty

            self.update_medicine_status(medicine)

            medicine.save(ignore_permissions=True)

    # --------------------------------------------------
    # CANCEL → RESTORE STOCK
    # --------------------------------------------------

    def on_cancel(self):
        self.restore_medicine_stock()

    def restore_medicine_stock(self):

        for item in self.medicines:

            if not item.medicine:
                continue

            medicine = frappe.get_doc("Medicine", item.medicine)

            qty = item.qty or 0

            medicine.stock_qty = (medicine.stock_qty or 0) + qty

            self.update_medicine_status(medicine)

            medicine.save(ignore_permissions=True)

    # --------------------------------------------------
    # UPDATE MEDICINE STATUS
    # --------------------------------------------------

    def update_medicine_status(self, medicine):

        if (medicine.stock_qty or 0) <= 10:
            medicine.status = "Low Stock"
        else:
            medicine.status = "Available"