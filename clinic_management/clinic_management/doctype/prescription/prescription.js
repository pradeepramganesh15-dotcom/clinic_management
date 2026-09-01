frappe.ui.form.on("Prescription", {

    appointment: function(frm) {

        if (!frm.doc.appointment) {
            frm.set_value("patient", "");
            frm.set_value("doctor", "");
            return;
        }

        frappe.db.get_doc("Appointment", frm.doc.appointment)
            .then(appointment => {

                // Fetch Patient
                if (appointment.patient) {
                    frm.set_value("patient", appointment.patient);
                }

                // Fetch Doctor
                if (appointment.doctor) {
                    frm.set_value("doctor", appointment.doctor);
                }

                // Fetch Appointment Date
                if (appointment.appointment_date) {
                    frm.set_value(
                        "prescription_date",
                        appointment.appointment_date
                    );
                }
            });
    },

    refresh: function(frm) {
        calculate_total(frm);
    },

    validate: function(frm) {
        calculate_total(frm);
    }
});


// Medicine field changed
frappe.ui.form.on("Prescription Medicine", {

    medicine: function(frm, cdt, cdn) {
        calculate_total(frm);
    },

    qty: function(frm, cdt, cdn) {
        calculate_total(frm);
    },

    days: function(frm, cdt, cdn) {
        calculate_total(frm);
    },

    medicines_remove: function(frm) {
        calculate_total(frm);
    }
});


async function calculate_total(frm) {

    let total = 0;

    for (const row of frm.doc.medicines || []) {

        if (!row.medicine || !row.qty) {
            continue;
        }

        try {

            const response = await frappe.db.get_value(
                "Medicine",
                row.medicine,
                "price_per_piece"
            );

            const price = response.message
                ? response.message.price_per_piece || 0
                : 0;

            total += price * row.qty;

        } catch (error) {

            console.error(
                "Error fetching medicine price:",
                error
            );
        }
    }

    frm.set_value("total_amount", total);
}