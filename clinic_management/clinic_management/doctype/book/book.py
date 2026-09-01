import logging
import os
import frappe
from frappe.model.document import Document


class Book(Document):

	@property
	def logger(self):
		logger = logging.getLogger("book_custom_logger")
		if not logger.handlers:
			logger.setLevel(logging.INFO)
			log_dir = os.path.join(frappe.get_site_path(), "logs")
			os.makedirs(log_dir, exist_ok=True)
			log_file = os.path.join(log_dir, "book.log")

			handler = logging.FileHandler(log_file)
			handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
			logger.addHandler(handler)
		return logger

	def before_validate(self):
		if self.book_name:
			self.book_name = self.book_name.strip()
		if self.author:
			self.author = self.author.strip()

	def validate(self):
		# Price or Qty empty-a (None) irundha 0-nu assign pannum
		price = self.price or 0
		qty = self.available_qty or 0

		if price <= 0:
			self.logger.error(f"Validation Failed: Invalid price {self.price} for {self.book_name}")
			frappe.throw("Price must be greater than 0")

		if qty < 0:
			self.logger.error(f"Validation Failed: Negative quantity {self.available_qty} for {self.book_name}")
			frappe.throw("Quantity cannot be negative")

		if qty == 0 and price > 0:
			self.logger.warning(f"Validation Failed: Price exists with zero quantity for {self.book_name}")
			frappe.throw("Price cannot be set when quantity is 0")

		if frappe.db.exists("Book", {"book_name": self.book_name, "name": ["!=", self.name]}):
			frappe.throw("Book Name already exists")

	def before_insert(self):
		self.update_status()

	def before_save(self):
		self.update_status()

	def after_insert(self):
		frappe.msgprint("Book created successfully")
		self.logger.info(f"Book Created: {self.name} - {self.book_name}")

	def on_update(self):
		frappe.msgprint("Book updated successfully")
		self.logger.info(f"Book Updated: {self.name}")

	def before_submit(self):
		qty = self.available_qty or 0
		if qty <= 0:
			self.logger.warning(f"Submit Blocked: Zero Qty for {self.name}")
			frappe.throw("Cannot submit book with 0 quantity")

	def on_submit(self):
		frappe.msgprint("Book submitted successfully")
		self.logger.info(f"Book Submitted: {self.name}")

	def before_cancel(self):
		frappe.msgprint("Book is being cancelled")

	def on_cancel(self):
		frappe.msgprint("Book cancelled successfully")
		self.logger.info(f"Book Cancelled: {self.name}")

	def on_trash(self):
		frappe.msgprint("Book is being deleted")
		self.logger.info(f"Book Deleting: {self.name}")

	def after_delete(self):
		frappe.msgprint("Book deleted successfully")
		self.logger.info(f"Book Deleted: {self.name}")

	def update_status(self):
		qty = self.available_qty or 0
		if qty == 0:
			self.status = "Out of Stock"
		elif qty <= 5:
			self.status = "Low Stock"
		else:
			self.status = "Available"