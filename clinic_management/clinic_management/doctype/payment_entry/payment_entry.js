frappe.ui.form.on("Payment Entry", {

    // =====================================================
    // ONLOAD
    // =====================================================

    onload: function(frm) {

        if (frm.is_new() && !frm.doc.payment_date) {

            frm.set_value(
                "payment_date",
                frappe.datetime.get_today()
            );
        }
    },


    // =====================================================
    // INVOICE
    // =====================================================

    invoice: function(frm) {

        if (!frm.doc.invoice) {

            frm.set_value(
                "patient",
                ""
            );

            frm.set_value(
                "amount",
                0
            );

            return;
        }


        frappe.db.get_doc(
            "Invoice",
            frm.doc.invoice
        ).then(invoice => {


            // --------------------------------
            // Fetch Patient
            // --------------------------------

            if (invoice.patient) {

                frm.set_value(
                    "patient",
                    invoice.patient
                );
            }


            // --------------------------------
            // Calculate Current Outstanding
            // --------------------------------

            let total_amount =
                flt(
                    invoice.total_amount || 0
                );

            let already_paid =
                flt(
                    invoice.paid_amount || 0
                );

            let outstanding =
                total_amount -
                already_paid;


            if (outstanding < 0) {

                outstanding = 0;
            }


            // --------------------------------
            // Set Payment Amount
            // --------------------------------

            frm.set_value(
                "amount",
                outstanding
            );


            // --------------------------------
            // Payment Date
            // --------------------------------

            frm.set_value(
                "payment_date",
                frappe.datetime.get_today()
            );


            // --------------------------------
            // Already Fully Paid
            // --------------------------------

            if (outstanding <= 0) {

                frappe.msgprint({
                    title: __("Invoice Already Paid"),
                    message: __(
                        "This Invoice has no outstanding amount."
                    ),
                    indicator: "orange"
                });


                frm.set_value(
                    "amount",
                    0
                );

                return;
            }


            // --------------------------------
            // Show Outstanding Amount
            // --------------------------------

            frappe.show_alert({
                message: __(
                    "Invoice outstanding amount: ₹{0}"
                ).replace(
                    "{0}",
                    outstanding.toFixed(2)
                ),
                indicator: "green"
            });

        });
    },


    // =====================================================
    // AMOUNT
    // =====================================================

    amount: function(frm) {

        if (
            !frm.doc.invoice ||
            !frm.doc.amount
        ) {

            return;
        }


        frappe.db.get_doc(
            "Invoice",
            frm.doc.invoice
        ).then(invoice => {


            let outstanding =
                flt(
                    invoice.total_amount || 0
                ) -
                flt(
                    invoice.paid_amount || 0
                );


            if (outstanding < 0) {

                outstanding = 0;
            }


            // --------------------------------
            // Validate Amount
            // --------------------------------

            if (
                flt(frm.doc.amount) >
                outstanding
            ) {

                frappe.msgprint({
                    title: __("Invalid Amount"),
                    message: __(
                        "Payment cannot be greater than outstanding amount ₹{0}."
                    ).replace(
                        "{0}",
                        outstanding.toFixed(2)
                    ),
                    indicator: "red"
                });


                frm.set_value(
                    "amount",
                    outstanding
                );
            }

        });
    },


    // =====================================================
    // PAYMENT MODE
    // =====================================================

    payment_mode: function(frm) {


        // --------------------------------
        // Only UPI
        // --------------------------------

        if (
            frm.doc.payment_mode !== "UPI"
        ) {

            return;
        }


        // --------------------------------
        // Invoice Required
        // --------------------------------

        if (!frm.doc.invoice) {

            frappe.msgprint({
                title: __("Invoice Required"),
                message: __(
                    "Please select an Invoice first."
                ),
                indicator: "orange"
            });


            frm.set_value(
                "payment_mode",
                ""
            );


            return;
        }


        // --------------------------------
        // Amount Required
        // --------------------------------

        if (
            !frm.doc.amount ||
            flt(frm.doc.amount) <= 0
        ) {

            frappe.msgprint({
                title: __("Invalid Amount"),
                message: __(
                    "Outstanding amount is not available."
                ),
                indicator: "red"
            });


            frm.set_value(
                "payment_mode",
                ""
            );


            return;
        }


        // =================================================
        // UPI DETAILS
        // =================================================

        let upi_id =
            "8072427580@upi";

        let payee_name =
            "J Pradeep Ram Ganesh BE,ME.";


        let amount =
            flt(frm.doc.amount);


        // =================================================
        // CREATE UPI PAYMENT URL
        // =================================================

        let upi_url =
            "upi://pay" +
            "?pa=" +
            encodeURIComponent(
                upi_id
            ) +
            "&pn=" +
            encodeURIComponent(
                payee_name
            ) +
            "&am=" +
            encodeURIComponent(
                amount.toFixed(2)
            ) +
            "&cu=INR";


        // =================================================
        // CREATE QR URL
        // =================================================

        let qr_url =
            "https://api.qrserver.com/v1/create-qr-code/" +
            "?size=220x220" +
            "&data=" +
            encodeURIComponent(
                upi_url
            );


        // =================================================
        // CREATE POPUP DIALOG
        // =================================================

        let dialog =
            new frappe.ui.Dialog({

                title: __("UPI Payment"),

                fields: [

                    {
                        fieldname: "qr_html",
                        fieldtype: "HTML"
                    }

                ],

                primary_action_label:
                    __("Close"),

                primary_action() {

                    dialog.hide();

                }

            });


        // =================================================
        // POPUP QR CONTENT
        // =================================================

        dialog.fields_dict.qr_html.$wrapper.html(`

            <div style="
                text-align: center;
                padding: 10px 5px 15px;
            ">

                <div style="
                    font-size: 17px;
                    font-weight: 600;
                    margin-bottom: 12px;
                ">
                    Scan to Pay
                </div>


                <img
                    src="${qr_url}"
                    style="
                        width: 220px;
                        height: 220px;
                        display: block;
                        margin: 0 auto;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                    "
                >


                <div style="
                    margin-top: 12px;
                    font-size: 13px;
                    color: #666;
                ">
                    UPI ID
                </div>


                <div style="
                    margin-top: 3px;
                    font-size: 15px;
                    font-weight: 600;
                ">
                    ${frappe.utils.escape_html(
                        upi_id
                    )}
                </div>


                <div style="
                    margin-top: 10px;
                    font-size: 22px;
                    font-weight: bold;
                ">
                    ₹ ${amount.toFixed(2)}
                </div>


                <div style="
                    margin-top: 10px;
                    font-size: 12px;
                    color: #888;
                ">
                    QR will close automatically
                    in 100 seconds
                </div>

            </div>

        `);


        // =================================================
        // SHOW POPUP
        // =================================================

        dialog.show();


        // =================================================
        // AUTO CLOSE AFTER 10 SECONDS
        // =================================================

        setTimeout(
            function() {

                if (
                    dialog &&
                    dialog.display
                ) {

                    dialog.hide();
                }

            },
            1000000
        );

    }

});