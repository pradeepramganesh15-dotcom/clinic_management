import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    # ---------------------------------------------------------
    # DATE FILTERS
    # ---------------------------------------------------------

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    doctor = filters.get("doctor")

    if not from_date:
        from_date = frappe.utils.get_first_day(
            frappe.utils.getdate()
        )

    if not to_date:
        to_date = frappe.utils.getdate()

    # ---------------------------------------------------------
    # COLUMNS
    # ---------------------------------------------------------

    columns = [
        {
            "fieldname": "section",
            "label": _("Section"),
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "doctor_medicine",
            "label": _("Doctor / Medicine"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "fieldname": "revenue",
            "label": _("Revenue"),
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "fieldname": "stock_qty",
            "label": _("Stock Qty"),
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "price_per_piece",
            "label": _("Price / Piece"),
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "fieldname": "stock_value",
            "label": _("Stock Value"),
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 120,
        },
    ]

    # ---------------------------------------------------------
    # DOCTOR REVENUE
    # Payment Entry -> Invoice -> Doctor
    # ---------------------------------------------------------

    doctor_conditions = """
        pe.status = 'Paid'
        AND pe.payment_date BETWEEN %(from_date)s AND %(to_date)s
        AND IFNULL(inv.docstatus, 0) < 2
        AND IFNULL(inv.doctor, '') != ''
    """

    if doctor:
        doctor_conditions += """
            AND inv.doctor = %(doctor)s
        """

    doctor_revenue = frappe.db.sql(
        f"""
        SELECT
            inv.doctor AS doctor,
            d.department AS department,
            SUM(pe.amount) AS revenue

        FROM `tabPayment Entry` pe

        INNER JOIN `tabInvoice` inv
            ON inv.name = pe.invoice

        LEFT JOIN `tabDoctor` d
            ON d.name = inv.doctor

        WHERE
            {doctor_conditions}

        GROUP BY
            inv.doctor,
            d.department

        ORDER BY
            revenue DESC
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "doctor": doctor,
        },
        as_dict=True,
    )

    # ---------------------------------------------------------
    # MEDICINE STOCK
    # ---------------------------------------------------------

    medicine_stock = frappe.db.sql(
        """
        SELECT
            name,
            medicine_name,
            stock_qty,
            price_per_piece,
            status

        FROM `tabMedicine`

        ORDER BY
            stock_qty ASC,
            medicine_name ASC
        """,
        as_dict=True,
    )

    # ---------------------------------------------------------
    # SUMMARY CALCULATIONS
    # ---------------------------------------------------------

    total_revenue = sum(
        frappe.utils.flt(row.revenue)
        for row in doctor_revenue
    )

    # Total doctors in master
    total_doctors = frappe.db.count("Doctor")

    # Total medicines
    total_medicines = len(medicine_stock)

    # Low stock count
    low_stock_medicines = sum(
        1
        for row in medicine_stock
        if row.status == "Low Stock"
    )

    # Available stock count
    available_medicines = sum(
        1
        for row in medicine_stock
        if row.status == "Available"
    )

    # Total stock value
    total_stock_value = sum(
        frappe.utils.flt(row.stock_qty)
        * frappe.utils.flt(row.price_per_piece)
        for row in medicine_stock
    )

    # ---------------------------------------------------------
    # REPORT DATA
    # ---------------------------------------------------------

    data = []

    # ---------------------------------------------------------
    # DOCTOR REVENUE DATA
    # ---------------------------------------------------------

    for row in doctor_revenue:

        data.append(
            {
                "section": "Doctor Revenue",
                "doctor_medicine": row.doctor,
                "department": row.department or "-",
                "revenue": frappe.utils.flt(row.revenue),
                "stock_qty": None,
                "price_per_piece": None,
                "stock_value": None,
                "status": "Revenue",
            }
        )

    # ---------------------------------------------------------
    # MEDICINE STOCK DATA
    # ---------------------------------------------------------

    for row in medicine_stock:

        stock_value = (
            frappe.utils.flt(row.stock_qty)
            * frappe.utils.flt(row.price_per_piece)
        )

        data.append(
            {
                "section": "Medicine Stock",
                "doctor_medicine": row.medicine_name,
                "department": "-",
                "revenue": None,
                "stock_qty": row.stock_qty,
                "price_per_piece": row.price_per_piece,
                "stock_value": stock_value,
                "status": row.status,
            }
        )

    # ---------------------------------------------------------
    # SUMMARY CARDS
    # ---------------------------------------------------------

    report_summary = [
        {
            "value": total_revenue,
            "indicator": "Green",
            "label": _("Total Revenue"),
            "datatype": "Currency",
            "currency": "INR",
        },
        {
            "value": total_doctors,
            "indicator": "Blue",
            "label": _("Total Doctors"),
            "datatype": "Int",
        },
        {
            "value": total_medicines,
            "indicator": "Blue",
            "label": _("Total Medicines"),
            "datatype": "Int",
        },
        {
            "value": low_stock_medicines,
            "indicator": "Red"
            if low_stock_medicines
            else "Green",
            "label": _("Low Stock Medicines"),
            "datatype": "Int",
        },
        {
            "value": total_stock_value,
            "indicator": "Purple",
            "label": _("Total Stock Value"),
            "datatype": "Currency",
            "currency": "INR",
        },
    ]

    # ---------------------------------------------------------
    # BAR CHART
    # DOCTOR REVENUE
    # ---------------------------------------------------------

    chart_labels = [
        row.doctor
        for row in doctor_revenue
    ]

    chart_values = [
        frappe.utils.flt(row.revenue)
        for row in doctor_revenue
    ]

    chart = {
        "data": {
            "labels": chart_labels,
            "datasets": [
                {
                    "name": _("Doctor Revenue"),
                    "values": chart_values,
                }
            ],
        },
        "type": "bar",
        "height": 300,
        "colors": ["#2490EF"],
    }

    # ---------------------------------------------------------
    # MEDICINE PIE CHART DATA
    # ---------------------------------------------------------

    pie_total = (
        available_medicines
        + low_stock_medicines
    )

    if pie_total:

        available_percent = round(
            (
                available_medicines
                / pie_total
            ) * 100,
            1,
        )

        low_stock_percent = round(
            (
                low_stock_medicines
                / pie_total
            ) * 100,
            1,
        )

    else:

        available_percent = 0
        low_stock_percent = 0

    # ---------------------------------------------------------
    # MEDICINE STOCK VISUAL
    # ---------------------------------------------------------

    pie_html = f"""
        <div style="
            margin-top: 20px;
            padding: 20px;
            border: 1px solid #d1d8dd;
            border-radius: 8px;
            background: #ffffff;
        ">

            <h4 style="
                margin: 0 0 20px 0;
                font-weight: 600;
            ">
                Medicine Stock Status
            </h4>

            <div style="
                display: flex;
                align-items: center;
                gap: 30px;
                flex-wrap: wrap;
            ">

                <div style="
                    width: 170px;
                    height: 170px;
                    border-radius: 50%;
                    background:
                        conic-gradient(
                            #2490EF 0%
                            {available_percent}%,

                            #F39C12
                            {available_percent}%
                            100%
                        );

                    position: relative;
                ">

                    <div style="
                        position: absolute;
                        width: 90px;
                        height: 90px;
                        background: white;
                        border-radius: 50%;
                        top: 40px;
                        left: 40px;
                    ">
                    </div>

                </div>

                <div style="
                    font-size: 14px;
                    line-height: 2;
                ">

                    <div>

                        <span style="
                            display: inline-block;
                            width: 12px;
                            height: 12px;
                            background: #2490EF;
                            border-radius: 3px;
                            margin-right: 8px;
                        ">
                        </span>

                        <strong>
                            Available
                        </strong>

                        &nbsp;

                        {available_medicines}

                        &nbsp;

                        ({available_percent}%)

                    </div>

                    <div>

                        <span style="
                            display: inline-block;
                            width: 12px;
                            height: 12px;
                            background: #F39C12;
                            border-radius: 3px;
                            margin-right: 8px;
                        ">
                        </span>

                        <strong>
                            Low Stock
                        </strong>

                        &nbsp;

                        {low_stock_medicines}

                        &nbsp;

                        ({low_stock_percent}%)

                    </div>

                </div>

            </div>

        </div>
    """

    # ---------------------------------------------------------
    # REPORT MESSAGE
    # ---------------------------------------------------------

    message = f"""
        <div style="
            padding: 12px 0;
            color: #6c757d;
        ">

            <strong>
                Report Period:
            </strong>

            {frappe.utils.formatdate(from_date)}

            &nbsp; → &nbsp;

            {frappe.utils.formatdate(to_date)}

        </div>

        {pie_html}
    """

    # ---------------------------------------------------------
    # IMPORTANT
    # Frappe v16 expects EXACTLY 6 values
    # ---------------------------------------------------------

    return (
        columns,
        data,
        message,
        chart,
        report_summary,
        False,
    )