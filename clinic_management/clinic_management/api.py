import frappe
from frappe import _
import jwt
import requests
from datetime import datetime, timedelta, timezone
from frappe.auth import LoginManager
from frappe.query_builder import DocType

# ==========================================================
# 1. CLINIC APPOINTMENT APIS
# ==========================================================

@frappe.whitelist(allow_guest=True)
def check_slot_availability(doctor, appointment_date, appointment_time):
    if not doctor or not appointment_date or not appointment_time:
        return {
            "available": False,
            "message": "Doctor, Date, and Time are required."
        }

    # Check existing booked appointments
    existing_appointment = frappe.db.exists(
        "Appointment",
        {
            "doctor": doctor,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "status": ["!=", "Cancelled"]
        }
    )

    if existing_appointment:
        return {
            "available": False,
            "message": f"Doctor {doctor} is already booked for this slot/time."
        }

    return {
        "available": True,
        "message": "Appointment slot is available."
    }


@frappe.whitelist()
def confirm_appointment(appointment_name):
    if not appointment_name:
        frappe.throw("Appointment name is required.")

    doc = frappe.get_doc("Appointment", appointment_name)
    doc.status = "Confirmed"
    doc.save()

    # Trigger Realtime Event for Receptionist
    frappe.publish_realtime(
        "appointment_confirmed",
        {
            "appointment": doc.name,
            "patient": doc.patient,
            "doctor": doc.doctor
        }
    )

    return {
        "status": "success",
        "message": "Appointment confirmed successfully."
    }


@frappe.whitelist(methods=["GET"])
def get_cached_doctors():
    cache_key = "cached_doctors"
    cached_doctors = frappe.cache.get_value(cache_key)

    if cached_doctors:
        return {
            "status": "success",
            "source": "cache",
            "data": cached_doctors
        }

    doctors = frappe.get_all(
        "Doctor",
        fields=["name", "doctor_name", "department"]
    )

    frappe.cache.set_value(cache_key, doctors, expires_in_sec=300)

    return {
        "status": "success",
        "source": "database",
        "data": doctors
    }


@frappe.whitelist(methods=["GET"])
def get_orthopedic_doctors():
    doctors = frappe.get_all(
        "Doctor",
        filters={"department": "Orthopedics"},
        fields=["name", "doctor_name", "department"],
        limit_page_length=10
    )

    return {
        "status": "success",
        "data": doctors
    }


# ==========================================================
# 2. BOOK STORE & UTILS APIS
# ==========================================================

@frappe.whitelist(methods=["POST"])
def check_book_availability(book_name):
    if not frappe.db.exists("Book", {"book_name": book_name}):
        return {
            "status": "not_found",
            "message": f"Bro, '{book_name}' book is not available from us!"
        }

    book = frappe.get_doc("Book", {"book_name": book_name})

    if book.available_qty > 0:
        return {
            "status": "available",
            "price": book.price,
            "stock": book.available_qty,
            "message": (
                f"Yes da! '{book.book_name}' available. "
                f"Price: ₹{book.price}, Stock: {book.available_qty}"
            )
        }
    else:
        return {
            "status": "out_of_stock",
            "message": f"Sorry da, '{book.book_name}' currently Out of Stock!"
        }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_book(book_name, price, available_qty):
    book = frappe.get_doc({
        "doctype": "Book",
        "book_name": book_name,
        "price": price,
        "available_qty": available_qty
    })
    book.insert()
    return {"status": "success", "book": book.name}


@frappe.whitelist(methods=["GET"])
def get_book(name):
    book = frappe.get_doc("Book", name)
    return {
        "status": "success",
        "book": {
            "name": book.name,
            "book_name": book.book_name,
            "price": book.price,
            "available_qty": book.available_qty
        }
    }


@frappe.whitelist(methods=["POST"])
def bulk_create_books(books_list):
    if isinstance(books_list, str):
        books_list = frappe.parse_json(books_list)

    if not isinstance(books_list, list) or len(books_list) == 0:
        frappe.throw("Bro, atleast send one book in the array!")

    created_books = []

    for item in books_list:
        doc = frappe.get_doc({
            "doctype": "Book",
            "book_name": item.get("book_name"),
            "price": item.get("price", 0),
            "available_qty": item.get("available_qty", 1),
            "status": "Available"
        })

        doc.insert()
        created_books.append(doc.name)

    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Successfully created {len(created_books)} books!",
        "created_ids": created_books
    }


@frappe.whitelist(methods=["GET", "POST"])
def get_books_paginated(page=1, page_length=5, search_text=None, min_price=None):
    page = int(page)
    page_length = int(page_length)
    start = (page - 1) * page_length

    filters = {}

    if search_text:
        filters["book_name"] = ["like", f"%{search_text}%"]

    if min_price:
        filters["price"] = [">=", float(min_price)]

    books = frappe.get_all(
        "Book",
        filters=filters,
        fields=["name", "book_name", "price", "available_qty", "status"],
        start=start,
        page_length=page_length,
        order_by="creation desc"
    )

    total_count = frappe.db.count("Book", filters=filters)

    return {
        "status": "success",
        "page": page,
        "page_length": page_length,
        "total_records": total_count,
        "total_pages": (total_count + page_length - 1) // page_length if page_length > 0 else 1,
        "data": books
    }


@frappe.whitelist(methods=["POST"])
def upload_book_cover(book_id):
    if "file" not in frappe.request.files:
        frappe.throw("Bro, no file in the request!")

    file_data = frappe.request.files["file"]

    saved_file = frappe.get_doc({
        "doctype": "File",
        "file_name": file_data.filename,
        "attached_to_doctype": "Book",
        "attached_to_name": book_id,
        "content": file_data.read(),
        "is_private": 0
    })

    saved_file.save()

    return {
        "status": "success",
        "message": "File Uploaded & Attached Successfully!",
        "file_url": saved_file.file_url,
        "attached_to": book_id
    }


@frappe.whitelist(methods=["POST"])
def create_book_status(book_name, price):
    try:
        price = float(price)
        if not book_name or price <= 0:
            frappe.local.response["http_status_code"] = 400
            return {"status": "error", "message": "Invalid book details"}

        frappe.local.response["http_status_code"] = 201
        return {
            "status": "success",
            "message": "Book created successfully",
            "book_name": book_name,
            "price": price
        }
    except (ValueError, TypeError):
        frappe.local.response["http_status_code"] = 400
        return {"status": "error", "message": "Price must be a valid number"}


# ==========================================================
# 3. AUTHENTICATION & SECURITY
# ==========================================================

@frappe.whitelist(methods=["POST"])
def test_role_security(book_name, price):
    current_user = frappe.session.user

    if current_user == "Guest":
        frappe.throw(
            "Bro, No permission for guest user! Send your token.",
            frappe.PermissionError
        )

    user_roles = frappe.get_roles(current_user)
    required_roles = ["System Manager", "Doctor"]

    has_access = any(role in user_roles for role in required_roles)

    if not has_access:
        frappe.throw(
            f"Bro '{current_user}', You don't have access! Required Roles: {required_roles}",
            frappe.PermissionError
        )

    return {
        "status": "success",
        "authenticated_user": current_user,
        "roles_found": user_roles,
        "message": f"Security Cleared! Book '{book_name}' with price ₹{price} verified by {current_user}."
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def jwt_login(usr, pwd):
    try:
        login_manager = LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)

        secret = frappe.conf.get("jwt_secret")
        if not secret:
            frappe.throw("JWT secret is not configured in site_config.json!")

        payload = {
            "sub": usr,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        token = jwt.encode(payload, secret, algorithm="HS256")

        return {
            "status": "success",
            "message": "Login successful",
            "token": token,
            "expires_in": "1 hour"
        }
    except Exception:
        frappe.throw("Invalid username or password")


def verify_jwt_token():
    token = frappe.get_request_header("X-JWT-Token")

    if not token:
        return None

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    secret = frappe.conf.get("jwt_secret")
    if not secret:
        return None

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user = payload.get("sub")
        if user and frappe.db.exists("User", user):
            frappe.set_user(user)
            return user
    except Exception:
        pass

    return None


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_protected_books():
    user = verify_jwt_token()

    if not user or user == "Guest" or frappe.session.user == "Guest":
        frappe.throw(
            "Authentication required! Please provide a valid token in X-JWT-Token header.",
            frappe.AuthenticationError
        )

    books = frappe.get_all(
        "Book",
        fields=["name", "book_name", "price", "available_qty", "status"]
    )

    return {
        "status": "success",
        "authenticated_user": frappe.session.user,
        "data": books
    }


# ==========================================================
# 4. EXTERNAL APIS, WEBHOOKS & REALTIME
# ==========================================================

@frappe.whitelist()
def test_external_api():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            return {"status": "success", "external_data": response.json()}
        return {"status": "failed", "error": response.text}
    except Exception as e:
        frappe.log_error(title="API Request Error", message=str(e))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def consume_external_data():
    try:
        response = requests.get("https://catfact.ninja/fact")
        if response.status_code == 200:
            external_json = response.json()
            return {
                "status": "success",
                "message": "Successfully consumed 3rd-party API data!",
                "cat_fact": external_json["fact"],
                "full_external_response": external_json
            }
        return {"status": "failed", "error": "Could not fetch data"}
    except Exception as e:
        frappe.log_error(title="Consume API Error", message=str(e))
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle_webhook():
    data = frappe.request.get_json()
    frappe.log_error(title="Webhook Received", message=str(data))
    return {
        "status": "success",
        "message": "Webhook received successfully da mapla!",
        "received_data": data
    }


@frappe.whitelist(methods=["POST"])
def create_payment_order(amount, currency="INR"):
    try:
        order_data = {
            "amount": float(amount),
            "currency": currency,
            "receipt": "receipt_order_123",
            "status": "created"
        }
        return {
            "status": "success",
            "message": "Payment order created successfully da mapla!",
            "gateway_order_id": "order_mock_987654",
            "order_details": order_data
        }
    except Exception as e:
        frappe.log_error(title="Payment Order Error", message=str(e))
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def payment_gateway_webhook():
    try:
        webhook_data = frappe.request.get_json()
        event = webhook_data.get("event")
        payload = webhook_data.get("payload", {})

        if event == "payment.success":
            order_id = payload.get("order_id")
            amount_paid = payload.get("amount")
            frappe.log_error(
                title="Payment Success Log",
                message=f"Order {order_id} paid successfully for amount {amount_paid}"
            )
            return {
                "status": "success",
                "message": f"Webhook received! Order {order_id} marked as Paid."
            }

        return {"status": "ignored", "message": "Event not handled"}
    except Exception as e:
        frappe.log_error(title="Payment Webhook Error", message=str(e))
        return {"status": "error", "message": str(e)}


@frappe.whitelist(methods=["POST"])
def test_realtime(message):
    user = frappe.session.user
    cache_key = f"realtime_rate_limit:{user}"

    request_count = frappe.cache.get_value(cache_key) or 0

    if request_count >= 3:
        frappe.throw(
            "Too many requests. Please try again after 30 seconds.",
            frappe.TooManyRequestsError
        )

    request_count += 1

    frappe.cache.set_value(cache_key, request_count, expires_in_sec=30)

    frappe.publish_realtime(
        "simple_test_event",
        {"message": message}
    )

    return {
        "status": "success",
        "message": "Real-time event sent",
        "requests_used": request_count,
        "limit": 3,
        "window_seconds": 30
    }


@frappe.whitelist(methods=["GET"])
def rate_limit_test():
    user = frappe.session.user
    cache_key = f"rate_limit:{user}"

    request_count = frappe.cache.get_value(cache_key) or 0

    if request_count >= 5:
        frappe.throw(
            _("Too many requests. Please try again later."),
            frappe.TooManyRequestsError
        )

    request_count += 1

    frappe.cache.set_value(cache_key, request_count, expires_in_sec=60)

    return {
        "status": "success",
        "message": "Request accepted",
        "requests_used": request_count,
        "limit": 5
    }
# ==========================================================
# HOOK: ON APPOINTMENT UPDATE / SAVE
# ==========================================================

def appointment_updated(doc, method):
    """
    This function is automatically triggered via hooks.py 
    when an Appointment document is saved or updated.
    """
    frappe.logger().info(f"Appointment {doc.name} updated for Patient {doc.patient}")
    
    # Custom logic (Realtime notification send panna):
    frappe.publish_realtime(
        "appointment_updated",
        {
            "appointment": doc.name,
            "patient": doc.patient,
            "doctor": doc.doctor,
            "status": doc.status
        }
    )

@frappe.whitelist()
def send_appointment_reminder(appointment_name):
    """Sends an email reminder to the patient."""
    if not appointment_name:
        frappe.throw(_("Appointment Name is required."))

    doc = frappe.get_doc("Appointment", appointment_name)

    if not doc.patient_email:
        frappe.throw(_("Patient Email is missing in this appointment."))

    patient_display = doc.patient_name or doc.patient

    subject = f"Reminder: Appointment with Dr. {doc.doctor}"
    message = f"""
        <p>Dear <b>{patient_display}</b>,</p>
        <p>This is a gentle reminder for your upcoming appointment.</p>
        <ul>
            <li><b>Doctor:</b> {doc.doctor}</li>
            <li><b>Date:</b> {doc.appointment_date}</li>
            <li><b>Time:</b> {doc.appointment_time}</li>
            <li><b>Token Number:</b> {doc.token or 'N/A'}</li>
            <li><b>Status:</b> {doc.status}</li>
        </ul>
        <p>Thank you,<br>Clinic Management Team</p>
    """

    frappe.sendmail(
        recipients=[doc.patient_email],
        subject=subject,
        message=message,
        reference_doctype="Appointment",
        reference_name=doc.name,
        now=True,
    )

    return {
        "status": "success",
        "message": _("Reminder email sent successfully!"),
    } 



def custom_logic(doc, method):
    frappe.msgprint("Hook executed!")



@frappe.whitelist()
def student_course_api():

    Student = DocType("Student")
    Course = DocType("Course")

    result = (
        frappe.qb.from_(Student)
        .join(Course)
        .on(Student.name == Course.student)
        .select(
            Student.name,
            Student.student_name,
            Student.age,
            Course.course_name
        )
        .limit(10)
        .run(as_dict=True)
    )

    if result:
        student = frappe.get_doc("Student", result[0]["name"])
        student.age = student.age + 1
        student.save()

    for row in result:
        frappe.db.set_value(
            "Student",
            row["name"],
            "status",
            "Active"
        )

    return result

@frappe.whitelist()
def todo_api():

    todos = frappe.get_list("ToDo",fields=["name", "description", "owner"],order_by="creation desc",limit=5)

    for todo in todos:
        todo["email"] = frappe.db.get_value(
            "User",
            todo["owner"],
            "email"
        )

    return {
        "timestamp": frappe.utils.now(),
        "records": todos
    }

@frappe.whitelist()
def create_task(task_subject):

    task = frappe.new_doc("Task")
    task.task_subject = task_subject
    task.save()

    return task.name

































