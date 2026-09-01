frappe.ui.form.on("Appointment", {

    // ==========================================================
    // REFRESH
    // ==========================================================

    refresh(frm) {

        // Set default status for new appointment
        if (frm.is_new() && !frm.doc.status) {
            frm.set_value("status", "Scheduled");
        }


        // ------------------------------------------------------
        // DOCTOR - CONFIRM APPOINTMENT BUTTON
        // ------------------------------------------------------

        if (
            !frm.is_new() &&
            frm.doc.status === "Scheduled" &&
            frappe.user.has_role("Doctor")
        ) {
            frm.add_custom_button(
                "Confirm Appointment",
                function () {
                    frappe.confirm(
                        "Are you sure you want to confirm this appointment?",
                        function () {
                            frappe.call({
                                method: "clinic_management.clinic_management.api.confirm_appointment",
                                args: {
                                    appointment_name: frm.doc.name
                                },
                                freeze: true,
                                freeze_message: "Confirming appointment...",
                                callback: function (r) {
                                    if (
                                        r.message &&
                                        r.message.status === "success"
                                    ) {
                                        frappe.show_alert({
                                            message: "Appointment Confirmed",
                                            indicator: "green"
                                        });

                                        // Refresh current form
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }
            );
        }


        // ------------------------------------------------------
        // SEND REMINDER BUTTON (PATIENT EMAIL NOTIFICATION)
        // ------------------------------------------------------

        if (!frm.is_new() && frm.doc.patient_email) {
            frm.add_custom_button(
                "Send Reminder",
                function () {
                    frappe.call({
                        method: "clinic_management.clinic_management.api.send_appointment_reminder",
                        args: {
                            appointment_name: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: "Sending Reminder Email...",
                        callback: function (r) {
                            if (
                                r.message &&
                                r.message.status === "success"
                            ) {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: "green"
                                });
                            }
                        }
                    });
                }
            );
        }


        // ------------------------------------------------------
        // QUICK WALK-IN BUTTON (ONLY FOR NEW FORMS)
        // ------------------------------------------------------

        if (frm.is_new()) {
            frm.add_custom_button(
                "Quick Walk-In",
                function () {
                    if (!frm.doc.patient) {
                        frappe.msgprint({
                            title: "Patient Required",
                            message: "Please select a patient first.",
                            indicator: "red"
                        });
                        return;
                    }

                    frm.set_value(
                        "appointment_date",
                        frappe.datetime.get_today()
                    );

                    frm.set_value(
                        "appointment_time",
                        frappe.datetime.now_time()
                    );

                    frm.set_value(
                        "status",
                        "Scheduled"
                    );

                    frappe.show_alert({
                        message: "Walk-in appointment details prepared.",
                        indicator: "green"
                    });
                }
            );
        }
    },


    // ==========================================================
    // PATIENT
    // ==========================================================

    patient(frm) {
        if (!frm.doc.patient) {
            frm.set_value("patient_email", "");
            return;
        }

        // Fetch Patient Details
        frappe.db.get_doc("Patient", frm.doc.patient).then(patient => {
            // Email
            if (patient.email) {
                frm.set_value("patient_email", patient.email);
            }

            // Phone
            if (frm.fields_dict.patient_phone && patient.phone) {
                frm.set_value("patient_phone", patient.phone);
            }
        });
    },


    // ==========================================================
    // DOCTOR
    // ==========================================================

    doctor(frm) {
        if (!frm.doc.doctor) {
            return;
        }

        // Clear old token
        frm.set_value("token", "");

        // Check slot
        frm.trigger("check_appointment_slot");
    },


    // ==========================================================
    // APPOINTMENT DATE
    // ==========================================================

    appointment_date(frm) {
        // Clear old token
        frm.set_value("token", "");

        // Check slot
        frm.trigger("check_appointment_slot");
    },


    // ==========================================================
    // APPOINTMENT TIME
    // ==========================================================

    appointment_time(frm) {
        // Clear old token
        frm.set_value("token", "");

        // Check slot
        frm.trigger("check_appointment_slot");
    },


    // ==========================================================
    // CHECK APPOINTMENT SLOT
    // ==========================================================

    check_appointment_slot(frm) {
        // Required fields
        if (!frm.doc.doctor || !frm.doc.appointment_date || !frm.doc.appointment_time) {
            return;
        }

        // Prevent checking while loading existing document
        if (frm.is_new() && !frm.doc.__islocal) {
            return;
        }

        // Show checking message
        frappe.show_alert({
            message: "Checking appointment slot...",
            indicator: "blue"
        });

        // CALL PYTHON API
        frappe.call({
            method: "clinic_management.clinic_management.api.check_slot_availability",
            args: {
                doctor: frm.doc.doctor,
                appointment_date: frm.doc.appointment_date,
                appointment_time: frm.doc.appointment_time
            },
            freeze: true,
            freeze_message: "Checking appointment slot...",
            callback: function (r) {
                // No response
                if (!r.message) {
                    frappe.msgprint({
                        title: "Slot Check Failed",
                        message: "Unable to verify appointment slot.",
                        indicator: "red"
                    });
                    return;
                }

                // SLOT NOT AVAILABLE
                if (!r.message.available) {
                    frm.set_value("token", "");

                    frappe.msgprint({
                        title: "Slot Not Available",
                        message: r.message.message || "This appointment slot is already booked.",
                        indicator: "red"
                    });
                    return;
                }

                // SLOT AVAILABLE
                frm.trigger("generate_token");

                frappe.show_alert({
                    message: r.message.message,
                    indicator: "green"
                });
            },
            error: function (r) {
                console.error("Appointment Slot API Error:", r);
                frappe.msgprint({
                    title: "Slot Check Failed",
                    message: "Unable to verify appointment slot. Please try again.",
                    indicator: "red"
                });
            }
        });
    },


    // ==========================================================
    // GENERATE TOKEN
    // ==========================================================

    generate_token(frm) {
        if (!frm.doc.doctor || !frm.doc.appointment_date || !frm.doc.appointment_time) {
            return;
        }

        // Find existing tokens
        frappe.db.get_list("Appointment", {
            filters: {
                doctor: frm.doc.doctor,
                appointment_date: frm.doc.appointment_date,
                docstatus: ["!=", 2]
            },
            fields: ["token"],
            limit_page_length: 0,
            order_by: "token desc"
        }).then(appointments => {
            let highest_token = 0;

            appointments.forEach(function (appointment) {
                let token = parseInt(appointment.token) || 0;
                if (token > highest_token) {
                    highest_token = token;
                }
            });

            let next_token = highest_token + 1;
            frm.set_value("token", next_token);

            frappe.show_alert({
                message: `Appointment slot is available. Token: ${next_token}`,
                indicator: "green"
            });
        });
    },


    // ==========================================================
    // BEFORE SAVE
    // ==========================================================

    before_save(frm) {
        if (!frm.doc.doctor) {
            frappe.throw("Please select a Doctor.");
        }

        if (!frm.doc.appointment_date) {
            frappe.throw("Please select Appointment Date.");
        }

        if (!frm.doc.appointment_time) {
            frappe.throw("Please select Appointment Time.");
        }

        if (!frm.doc.status) {
            frm.set_value("status", "Scheduled");
        }
    },


    // ==========================================================
    // VALIDATE
    // ==========================================================

    validate(frm) {
        if (frm.doc.appointment_date && frm.doc.appointment_time) {
            let appointment_datetime = frappe.datetime.str_to_obj(
                `${frm.doc.appointment_date} ${frm.doc.appointment_time}`
            );
            let now = new Date();

            if (frm.is_new() && appointment_datetime < now) {
                frappe.throw({
                    title: "Invalid Appointment Time",
                    message: "Appointment date and time cannot be in the past.",
                    indicator: "red"
                });
            }
        }

        if (frm.doc.status === "Scheduled" && !frm.doc.token) {
            frappe.throw({
                title: "Token Required",
                message: "Appointment token could not be generated. Please check the slot again.",
                indicator: "red"
            });
        }
    }
});


// ==========================================================
// REAL-TIME EVENT LISTENER
// ==========================================================

frappe.realtime.on("appointment_confirmed", function (data) {
    if (!frappe.user.has_role("Receptionist")) {
        return;
    }

    frappe.show_alert({
        message: `🔔 Appointment Confirmed\nPatient: ${data.patient}\nDoctor: ${data.doctor}`,
        indicator: "green"
    }, 10);

    frappe.msgprint({
        title: "🔔 Appointment Confirmed",
        message: `
            <b>Appointment:</b> ${data.appointment}<br><br>
            <b>Patient:</b> ${data.patient}<br><br>
            <b>Doctor:</b> ${data.doctor}
        `,
        indicator: "green"
    });
});