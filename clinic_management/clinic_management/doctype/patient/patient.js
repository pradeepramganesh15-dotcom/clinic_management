frappe.ui.form.on("Patient", {

    refresh: function(frm) {
        calculate_patient_age(frm);
    },

    date_of_birth: function(frm) {
        calculate_patient_age(frm);
    }

});


function calculate_patient_age(frm) {

    if (!frm.doc.date_of_birth) {
        frm.set_value("patient_age", null);
        return;
    }

    const dob = new Date(frm.doc.date_of_birth);
    const today = new Date();

    let age = today.getFullYear() - dob.getFullYear();

    const month_difference = today.getMonth() - dob.getMonth();

    if (
        month_difference < 0 ||
        (
            month_difference === 0 &&
            today.getDate() < dob.getDate()
        )
    ) {
        age--;
    }

    frm.set_value("patient_age", age);
}