frappe.query_reports["Doctor Revenue + Medicine Stock"] = {

    // ========================================================
    // FILTERS
    // ========================================================

    filters: [

        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },

        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },

        {
            fieldname: "doctor",
            label: __("Doctor"),
            fieldtype: "Link",
            options: "Doctor"
        }

    ],

    // ========================================================
    // ONLOAD
    // ========================================================

    onload: function(report) {

        report.page.add_inner_button(
            __("Refresh Report"),
            function() {

                report.refresh();

            }
        );

    },

    // ========================================================
    // FORMATTER
    // ========================================================

    formatter: function(
        value,
        row,
        column,
        data
    ) {

        if (!data) {
            return value;
        }

        // ----------------------------------------------------
        // SECTION
        // ----------------------------------------------------

        if (
            column.fieldname === "section"
        ) {

            if (
                value === "Doctor Revenue"
            ) {

                return `
                    <span style="
                        color: #2490EF;
                        font-weight: 600;
                    ">
                        ${value}
                    </span>
                `;

            }

            if (
                value === "Medicine Stock"
            ) {

                return `
                    <span style="
                        color: #8E44AD;
                        font-weight: 600;
                    ">
                        ${value}
                    </span>
                `;

            }

        }

        // ----------------------------------------------------
        // STATUS
        // ----------------------------------------------------

        if (
            column.fieldname === "status"
        ) {

            if (
                value === "Low Stock"
            ) {

                return `
                    <span style="
                        color: #E74C3C;
                        font-weight: 600;
                    ">
                        ⚠ ${value}
                    </span>
                `;

            }

            if (
                value === "Available"
            ) {

                return `
                    <span style="
                        color: #27AE60;
                        font-weight: 600;
                    ">
                        ✓ ${value}
                    </span>
                `;

            }

            if (
                value === "Revenue"
            ) {

                return `
                    <span style="
                        color: #2490EF;
                        font-weight: 600;
                    ">
                        ${value}
                    </span>
                `;

            }

        }

        return value;

    }

};