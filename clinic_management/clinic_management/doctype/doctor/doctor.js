frappe.ui.form.on("Appointment", {

    refresh(frm) {

        if (
            !frm.is_new() &&
            frm.doc.status === "Scheduled"
        ) {

            frm.add_custom_button("Confirm Appointment", () => {

                frappe.call({
                    method: "clinic_management.clinic_management.api.confirm_appointment",
                    args: {
                        appointment_name: frm.doc.name
                    },

                    callback: function(r) {

                        if (r.message) {

                            frappe.msgprint(
                                r.message.message
                            );

                            frm.reload_doc();
                        }
                    }
                });

            });
        }
    }

});