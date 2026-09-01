frappe.query_reports["Medicine Report using scipt"] = {
	"filters": [
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nAvailable\nLow Stock",
			"default": ""
		}
	]
};