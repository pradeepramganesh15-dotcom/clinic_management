frappe.ui.form.on("Book", {

    // 🔄 Form Refresh
    refresh(frm) {

        // ⭐ Existing Rating code
        const render_stars = () => {

            let rating = frm.doc.rating || 0;
            let stars_html = "";

            for (let i = 1; i <= 5; i++) {

                let star = i <= rating ? "★" : "☆";

                stars_html += `
                    <span
                        class="star-btn"
                        data-val="${i}"
                        style="
                            font-size: 30px;
                            cursor: pointer;
                            margin-right: 8px;
                        "
                    >
                        ${star}
                    </span>
                `;
            }

            frm.set_df_property(
                "rating",
                "description",
                `<div id="rating-box">${stars_html}</div>`
            );
        };

        render_stars();


        // ⭐ Rating click
        $(frm.wrapper)
            .off("click", ".star-btn")
            .on("click", ".star-btn", function() {

                let selected_val = $(this).data("val");

                frm.set_value("rating", selected_val).then(() => {
                    render_stars();
                });

            });


        // 📦 Existing Stock Button
        frm.add_custom_button("Check Stock Status", () => {

            frappe.call({

                method:
                    "clinic_management.clinic_management.api.check_book_availability",

                args: {
                    book_name: frm.doc.book_name
                },

                callback: function(response) {

                    if (response.message) {

                        frappe.msgprint(
                            response.message.message
                        );

                    }

                }

            });

        });


        // 🔥 Existing Send Realtime Button
        frm.add_custom_button("Send Realtime", () => {

            frappe.call({

                method:
                    "clinic_management.clinic_management.api.test_realtime",

                type: "POST",

                args: {
                    message: "Book " + frm.doc.book_name + " updated!"
                },

                callback: function(response) {

                    if (response.message) {

                        frappe.msgprint(
                            "da na thaan da API vanthu irrukan"
                        );

                    }

                }

            });

        });


        // 📡 Realtime Event Listener
        frappe.realtime.on(
            "simple_test_event",
            function(data) {

                frappe.msgprint(
                    "🔔 Real-time Message: " + data.message
                );

            }
        );


        // 👁️ Conditional Field Display
        toggle_available_qty(frm);

    },


    // 🔄 Status field change event
    status(frm) {

        toggle_available_qty(frm);

    }

});


// 👁️ Show / Hide Available Qty
function toggle_available_qty(frm) {

    if (frm.doc.status === "Low Stock") {

        frm.toggle_display("available_qty", true);

    } else {

        frm.toggle_display("available_qty", false);

    }

}