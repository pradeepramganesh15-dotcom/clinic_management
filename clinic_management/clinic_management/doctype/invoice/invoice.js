frappe.ui.form.on("Invoice", {

    refresh(frm) {
        frm.trigger("calculate_payment");
    },


    patient(frm) {

        if (!frm.doc.patient) {
            return;
        }

        // --------------------------------
        // Set Invoice Date
        // --------------------------------

        frm.set_value(
            "invoice_date",
            frappe.datetime.get_today()
        );


        // --------------------------------
        // Get Latest Appointment
        // --------------------------------

        frappe.db.get_list("Appointment", {

            filters: {
                patient: frm.doc.patient
            },

            fields: [
                "name",
                "doctor",
                "appointment_date",
                "appointment_time"
            ],

            order_by:
                "appointment_date desc, appointment_time desc",

            limit: 1

        }).then(appointments => {

            if (appointments.length > 0) {

                let appointment = appointments[0];


                // --------------------------------
                // Get Doctor Consultation Fee
                // --------------------------------

                if (appointment.doctor) {

                    frappe.db.get_value(
                        "Doctor",
                        appointment.doctor,
                        "consultation_fee"
                    ).then(r => {

                        let fee = 0;

                        if (
                            r.message &&
                            r.message.consultation_fee
                        ) {
                            fee =
                                flt(
                                    r.message.consultation_fee
                                );
                        }

                        frm.set_value(
                            "consultation_fee",
                            fee
                        );

                        frm.trigger(
                            "calculate_total"
                        );
                    });
                }
            }
        });


        // --------------------------------
        // Get Latest Submitted Prescription
        // --------------------------------

        frappe.db.get_list("Prescription", {

            filters: {
                patient: frm.doc.patient,
                docstatus: 1
            },

            fields: [
                "name",
                "total_amount",
                "prescription_date"
            ],

            order_by:
                "prescription_date desc, creation desc",

            limit: 1

        }).then(prescriptions => {

            let medicine_charge = 0;

            if (prescriptions.length > 0) {

                medicine_charge =
                    flt(
                        prescriptions[0].total_amount
                    );
            }

            frm.set_value(
                "medicine_charges",
                medicine_charge
            );

            frm.trigger(
                "calculate_total"
            );
        });
    },


    consultation_fee(frm) {

        frm.trigger(
            "calculate_total"
        );
    },


    medicine_charges(frm) {

        frm.trigger(
            "calculate_total"
        );
    },


    total_amount(frm) {

        frm.trigger(
            "calculate_payment"
        );
    },


    paid_amount(frm) {

        frm.trigger(
            "calculate_payment"
        );
    },


    calculate_total(frm) {

        let consultation_fee =
            flt(frm.doc.consultation_fee);

        let medicine_charges =
            flt(frm.doc.medicine_charges);

        let total =
            consultation_fee +
            medicine_charges;

        frm.set_value(
            "total_amount",
            total
        );

        frm.trigger(
            "calculate_payment"
        );
    },


    calculate_payment(frm) {

        let total =
            flt(frm.doc.total_amount);

        let paid =
            flt(frm.doc.paid_amount);


        // --------------------------------
        // Validate Paid Amount
        // --------------------------------

        if (paid < 0) {

            paid = 0;

            frm.set_value(
                "paid_amount",
                0
            );
        }


        // --------------------------------
        // Paid > Total
        // --------------------------------

        if (paid > total) {

            frappe.msgprint({
                title: __("Invalid Payment"),
                message:
                    __("Paid Amount cannot be greater than Total Amount."),
                indicator: "red"
            });

            paid = total;

            frm.set_value(
                "paid_amount",
                total
            );
        }


        // --------------------------------
        // Calculate Outstanding
        // --------------------------------

        let outstanding =
            Math.max(
                total - paid,
                0
            );


        frm.set_value(
            "outstanding_amount",
            outstanding
        );


        // --------------------------------
        // Payment Status
        // --------------------------------

        let status = "Unpaid";

        if (paid <= 0) {

            status = "Unpaid";

        }
        else if (outstanding > 0) {

            status = "Partially Paid";

        }
        else {

            status = "Fully Paid";
        }


        frm.set_value(
            "payment_status",
            status
        );
    }

});