console.log("🔥 Receptionist Realtime JS Loaded");


frappe.realtime.on("new_appointment", function(data) {

    console.log("🔥🔥🔥 NEW APPOINTMENT RECEIVED:", data);


    // ==========================================
    // POPUP
    // ==========================================

    frappe.show_alert({
        message: `🔥 New Appointment: ${data.patient}`,
        indicator: "green"
    }, 10);


    // ==========================================
    // NOTIFICATION MESSAGE
    // ==========================================

    frappe.show_notification({
        title: "New Appointment",
        message: `
            <b>Patient:</b> ${data.patient}<br>
            <b>Doctor:</b> ${data.doctor}<br>
            <b>Date:</b> ${data.date}<br>
            <b>Time:</b> ${data.time}
        `
    });


    // ==========================================
    // SOUND
    // ==========================================

    frappe.utils.play_sound("submit");

});