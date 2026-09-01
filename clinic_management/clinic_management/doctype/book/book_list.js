frappe.listview_settings["Book"] = {
    formatters: {
        rating(value) {

            let rating = parseInt(value) || 0;

            if (rating < 0) {
                rating = 0;
            }

            if (rating > 5) {
                rating = 5;
            }

            let stars = "★".repeat(rating);
            let empty_stars = "☆".repeat(5 - rating);

            return `${stars}${empty_stars}`;
        }
    }
};