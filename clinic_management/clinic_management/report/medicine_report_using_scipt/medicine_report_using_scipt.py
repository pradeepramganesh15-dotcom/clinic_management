import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "medicine_name",
			"label": "Medicine Name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "stock_qty",
			"label": "Stock Qty",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "price_per_piece",
			"label": "Price Per Piece",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"width": 120
		}
	]

def get_data(filters):
	conditions = {}

	# Filter apply pannirundha add panna:
	if filters and filters.get("status"):
		conditions["status"] = filters.get("status")

	# ORM Query:
	data = frappe.db.get_all(
		"Medicine",
		filters=conditions,
		fields=["medicine_name", "stock_qty", "price_per_piece", "status"]
	)

	return data