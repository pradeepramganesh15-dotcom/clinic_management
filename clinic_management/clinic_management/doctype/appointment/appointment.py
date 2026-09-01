import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Appointment(Document):

    def validate(self):
        self.validate_doctor_available()
        self.validate_past_date()
        self.validate_double_booking()

    def validate_doctor_available(self):
        """
        Allow appointments only for doctors
        whose status is Available.
        """

        if not self.doctor:
            return

        doctor_status = frappe.db.get_value(
            "Doctor",
            self.doctor,
            "status"
        )

        if doctor_status != "Available":
            frappe.throw(
                f"Doctor {self.doctor} is currently unavailable. "
                f"Please select an available doctor."
            )

    def validate_past_date(self):
        """
        Automatically cancel appointment
        when appointment date is in the past.
        """

        if not self.appointment_date:
            return

        appointment_date = getdate(self.appointment_date)
        today = getdate(nowdate())

        if appointment_date < today:
            self.status = "Cancelled"

            frappe.msgprint(
                "Appointment date is in the past. "
                "The appointment has been cancelled."
            )

    def validate_double_booking(self):
        """
        Prevent double booking for the same doctor,
        appointment date and slot/time.
        """

        if not self.doctor or not self.appointment_date:
            return

        filters = {
            "doctor": self.doctor,
            "appointment_date": self.appointment_date,
            "name": ["!=", self.name],
            "status": ["!=", "Cancelled"],
        }

        if self.slot:
            filters["slot"] = self.slot

        elif self.appointment_time:
            filters["appointment_time"] = self.appointment_time

        else:
            return

        existing_appointment = frappe.db.exists(
            "Appointment",
            filters
        )

        if existing_appointment:
            frappe.throw(
                f"Doctor {self.doctor} is already booked "
                f"for this date and slot/time."
            )


# ==========================================================
# SEND APPOINTMENT REMINDER
# ==========================================================

@frappe.whitelist()
def send_appointment_reminder(appointment):

    # Get Appointment
    doc = frappe.get_doc(
        "Appointment",
        appointment
    )

    # ------------------------------------------------------
    # Check Patient
    # ------------------------------------------------------

    if not doc.patient:
        frappe.throw(
            "Patient is required."
        )

    # ------------------------------------------------------
    # Check Patient Email
    # ------------------------------------------------------

    if not doc.patient_email:
        frappe.throw(
            "Patient email address is not available."
        )

    # ------------------------------------------------------
    # Get Patient Name
    # ------------------------------------------------------

    patient_name = frappe.db.get_value(
        "Patient",
        doc.patient,
        "patient_name"
    )

    if not patient_name:
        patient_name = doc.patient

    # ------------------------------------------------------
    # Appointment Details
    # ------------------------------------------------------

    doctor_name = doc.doctor or "Doctor"

    appointment_date = (
        str(doc.appointment_date)
        if doc.appointment_date
        else ""
    )

    appointment_time = (
        str(doc.appointment_time)
        if doc.appointment_time
        else ""
    )

    slot = doc.slot or "Not specified"

    # ------------------------------------------------------
    # Email Subject
    # ------------------------------------------------------

    subject = "Appointment Reminder - Clinic Management"

    # ------------------------------------------------------
    # Email Body
    # ------------------------------------------------------

    message = f"""
    <div style="font-family: Arial, sans-serif;">

        <h2>Appointment Reminder</h2>

        <p>
            Dear <b>{patient_name}</b>,
        </p>

        <p>
            This is a reminder for your upcoming
            appointment at our clinic.
        </p>

        <h3>Appointment Details</h3>

        <table
            border="1"
            cellpadding="8"
            cellspacing="0"
            style="border-collapse: collapse;"
        >

            <tr>
                <td><b>Patient</b></td>
                <td>{patient_name}</td>
            </tr>

            <tr>
                <td><b>Doctor</b></td>
                <td>{doctor_name}</td>
            </tr>

            <tr>
                <td><b>Date</b></td>
                <td>{appointment_date}</td>
            </tr>

            <tr>
                <td><b>Time</b></td>
                <td>{appointment_time}</td>
            </tr>

            <tr>
                <td><b>Slot</b></td>
                <td>{slot}</td>
            </tr>

        </table>

        <br>

        <p>
            Please arrive a few minutes before
            your scheduled appointment time.
        </p>

        <p>
            Thank you,<br>
            <b>Clinic Management</b>
        </p>

    </div>
    """

    # ------------------------------------------------------
    # SEND EMAIL IMMEDIATELY
    # ------------------------------------------------------

    frappe.sendmail(
        recipients=[doc.patient_email],
        subject=subject,
        message=message,
        now=True
    )

    # ------------------------------------------------------
    # Success Message
    # ------------------------------------------------------

    frappe.msgprint(
        f"Appointment reminder sent successfully "
        f"to {doc.patient_email}."
    )

    return {
        "status": "success",
        "message": (
            f"Appointment reminder sent successfully "
            f"to {doc.patient_email}."
        )
    }


# ==========================================================
# RECEPTIONIST NOTIFICATION
# ==========================================================

def notify_receptionist(doc, method=None):

    frappe.msgprint(
        f"Appointment created successfully "
        f"for patient {doc.patient}."
    )