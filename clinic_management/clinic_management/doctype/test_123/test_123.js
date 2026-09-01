// Copyright (c) 2026, pradeep@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Test_123", {onload(frm) {frappe.msgprint("Form loaded")},validate(frm){if (frm.doc.age < 18){frappe.throw("You need to cross the minimum age")}}});
