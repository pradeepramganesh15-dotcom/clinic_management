import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestAppointment(FrappeTestCase):

    def setUp(self):
        # Unique test execution identifier to avoid naming collision
        self.patient_name = "Test Patient " + frappe.generate_hash(length=5)
        self.doctor_name = "Test Doctor " + frappe.generate_hash(length=5)
        self.test_date = add_days(nowdate(), 2)

        # 1. Setup Patient
        self.patient = frappe.get_doc({
            "doctype": "Patient",
            "patient_name": self.patient_name,
            "phone_number": "+919000000001",
        }).insert(ignore_permissions=True)

        # 2. Setup Doctor
        self.doctor = frappe.get_doc({
            "doctype": "Doctor",
            "doctor_name": self.doctor_name,
            "consultation_fee": 500,
            "status": "Available",
        }).insert(ignore_permissions=True)

    # TEST 1: Double-Booking Validation
    def test_double_booking_validation(self):
        # Create first valid appointment
        appointment_1 = frappe.get_doc({
            "doctype": "Appointment",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "appointment_date": self.test_date,
            "appointment_time": "10:00:00",
            "token": 1,
            "status": "Scheduled",
        })
        appointment_1.insert(ignore_permissions=True)

        self.assertTrue(appointment_1.name)

        # Create duplicate appointment (Same doctor, date & time slot)
        appointment_2 = frappe.get_doc({
            "doctype": "Appointment",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "appointment_date": self.test_date,
            "appointment_time": "10:00:00",
            "token": 2,
            "status": "Scheduled",
        })

        # Expect Frappe ValidationError on duplicate slot
        with self.assertRaises(frappe.ValidationError):
            appointment_2.insert(ignore_permissions=True)

    # TEST 2: Invoice Submit Flow
    def test_invoice_submit_flow(self):
        invoice = frappe.get_doc({
            "doctype": "Invoice",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "invoice_date": self.test_date,
            "consultation_fee": 500,
            "medicine_charges": 0,
            "total_amount": 500,
            "paid_amount": 0,
            "outstanding_amount": 500,
            "payment_status": "Unpaid",
        })

        invoice.insert(ignore_permissions=True)
        
        # Check draft status (docstatus == 0)
        self.assertEqual(invoice.docstatus, 0)

        # Submit Invoice
        invoice.submit()

        # Check submitted status (docstatus == 1) & fields consistency
        self.assertEqual(invoice.docstatus, 1)
        self.assertEqual(invoice.total_amount, 500)
        self.assertEqual(invoice.outstanding_amount, 500)
        self.assertEqual(invoice.payment_status, "Unpaid")