import frappe
from frappe.utils import add_days, getdate, nowdate


def enqueue_appointment_reminders():
    """
    Scheduler runs this nightly.
    It pushes the actual email work to a background queue.
    """

    frappe.enqueue(
        send_tomorrow_appointment_reminders,
        queue="short",
        job_name="nightly_appointment_reminders"
    )


def send_tomorrow_appointment_reminders():
    """
    Find tomorrow's scheduled appointments
    and send reminder emails to patients.
    """

    tomorrow = add_days(getdate(nowdate()), 1)

    appointments = frappe.get_all(
        "Appointment",
        filters={
            "appointment_date": tomorrow,
            "status": "Scheduled"
        },
        fields=[
            "name",
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time"
        ]
    )

    for appointment in appointments:

        if not appointment.patient:
            continue

        patient = frappe.db.get_value(
            "Patient",
            appointment.patient,
            [
                "patient_name",
                "email"
            ],
            as_dict=True
        )

        if not patient or not patient.email:
            continue

        doctor_name = "-"

        if appointment.doctor:
            doctor_name = frappe.db.get_value(
                "Doctor",
                appointment.doctor,
                "doctor_name"
            ) or "-"

        frappe.sendmail(
            recipients=[patient.email],
            subject="Appointment Reminder - Tomorrow",
            message=f"""
                <p>Dear {patient.patient_name},</p>

                <p>
                    This is a reminder that you have an appointment
                    scheduled for tomorrow.
                </p>

                <p>
                    <b>Doctor:</b> {doctor_name}<br>
                    <b>Date:</b> {appointment.appointment_date}<br>
                    <b>Time:</b> {appointment.appointment_time}
                </p>

                <p>
                    Please arrive on time for your appointment.
                </p>

                <p>
                    Regards,<br>
                    Clinic Management
                </p>
            """
        )