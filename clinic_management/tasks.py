import frappe


def hourly_student_reminder():
    student = frappe.get_all("Student",fields=["student_name"],limit=1)

    if student:
        frappe.publish_realtime("student_reminder",
            {
                "message": f"Student: {student[0].student_name}"
            }
        )