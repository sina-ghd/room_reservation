from datetime import datetime
from app.models import db, Availability, SessionToken, Role
from flask import request, jsonify
from datetime import datetime, timedelta, time
from app.models import (
    User,
    Student,
    Role,
    AuthCode,
    SessionToken,
    Availability,
    Reservation,
)
from app import db
import random
import secrets


def init_routes(app):
    @app.route("/student", methods=["POST"])
    def create_student():
        data = request.get_json()
        phone = data.get("phone_number")
        student_id = data.get("student_identifier")
        first = data.get("first_name")
        last = data.get("last_name")
        email = data.get("email")

        if not all([phone, student_id, first, last, email]):
            return jsonify({"error": "Missing fields"}), 400

        try:
            student_role = Role.query.filter_by(role_name="student").first()
            if not student_role:
                return jsonify({"error": "Role 'student' not found"}), 400

            user = User(
                phone_number=phone,
                role_id=student_role.role_id,
                created_at=datetime.utcnow(),
            )
            db.session.add(user)
            db.session.flush()

            student = Student(
                user_id=user.user_id,
                student_identifier=student_id,
                first_name=first,
                last_name=last,
                email=email,
            )
            db.session.add(student)
            db.session.commit()

            return (
                jsonify(
                    {"message": "Student created", "student_id": student.student_id}
                ),
                201,
            )

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # لیست دانشجوها (مخصوص ادمین)
    @app.route("/admin/students", methods=["GET"])
    def admin_get_students():
        token = request.args.get("token")
        if not token:
            return jsonify({"error": "Token is required"}), 400

        # بررسی توکن و نقش ادمین
        session = SessionToken.query.filter_by(token=token).first()
        if not session:
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.get(session.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # بررسی اینکه نقش کاربر به درستی بارگذاری شده باشد
        role = Role.query.get(user.role_id)
        if not role:
            return jsonify({"error": "User does not have a role"}), 400

        if role.role_name != "admin":
            return jsonify({"error": "Forbidden: admin only"}), 403

        # اگر توکن معتبر بود، لیست دانشجویان و رزروهای آن‌ها را برمی‌گرداند
        students = Student.query.all()
        return (
            jsonify(
                [
                    {
                        "id": s.student_id,
                        "first_name": s.first_name,
                        "last_name": s.last_name,
                        "phone": s.user.phone_number,
                        # افزودن رزروها
                        "reservations": [
                            reservation.to_dict() for reservation in s.reservations
                        ],
                    }
                    for s in students
                ]
            ),
            200,
        )

    # درخواست کد OTP
    @app.route("/auth/request-code", methods=["POST"])
    def request_otp():
        data = request.get_json()
        phone = data.get("phone_number")

        if not phone:
            return jsonify({"error": "Phone number is required"}), 400

        user = User.query.filter_by(phone_number=phone).first()
        if not user:
            user = User(phone_number=phone, created_at=datetime.utcnow())
            db.session.add(user)
            db.session.flush()

        code = str(random.randint(100000, 999999))
        expires = datetime.utcnow() + timedelta(minutes=2)

        otp = AuthCode(user_id=user.user_id, code=code, expires_at=expires)
        db.session.add(otp)
        db.session.commit()

        print(f"🔐 OTP for {phone} = {code}")
        with open("otp_codes.txt", "a") as file:
            file.write(f"{phone} : {code}\n")
        return jsonify({"message": "OTP sent (check console)"}), 200

    # تأیید کد OTP و ساخت session_token
    @app.route("/auth/verify-code", methods=["POST"])
    def verify_otp():
        data = request.get_json()
        phone = data.get("phone_number")
        code = data.get("code")

        if not all([phone, code]):
            return jsonify({"error": "Phone and code are required"}), 400

        user = User.query.filter_by(phone_number=phone).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        otp = AuthCode.query.filter_by(
            user_id=user.user_id, code=code, is_used=False
        ).first()
        if not otp:
            return jsonify({"error": "Invalid code"}), 400
        if otp.expires_at < datetime.utcnow():
            return jsonify({"error": "Code expired"}), 400

        otp.is_used = True

        # ساخت session token
        session_token = secrets.token_hex(32)
        token = SessionToken(user_id=user.user_id, token=session_token)
        db.session.add(token)
        db.session.commit()

        return (
            jsonify({"message": "✅ Auth successful!", "session_token": session_token}),
            200,
        )

    # گرفتن session_token برای کاربر (فقط آخرین مورد)
    @app.route("/auth/session-token", methods=["GET"])
    def get_session_token():
        phone = request.args.get("phone_number")
        user = User.query.filter_by(phone_number=phone).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        latest_token = (
            SessionToken.query.filter_by(user_id=user.user_id)
            .order_by(SessionToken.created_at.desc())
            .first()
        )
        if not latest_token:
            return jsonify({"error": "No token found"}), 404

        return jsonify({"session_token": latest_token.token}), 200

    # تنظیم زمان‌های معتبر برای ادمین
    @app.route("/admin/set-availability", methods=["POST"])
    def set_availability():
        data = request.get_json()

        token = data.get("token")
        day_of_week = data.get("day_of_week")
        date_str = data.get("date")  # ← اضافه شده
        start_time_str = data.get("start_time")
        end_time_str = data.get("end_time")

        if not all([token, day_of_week, date_str, start_time_str, end_time_str]):
            return jsonify({"error": "Missing fields"}), 400

            # بررسی اعتبار توکن
        session = SessionToken.query.filter_by(token=token).first()
        if not session:
            return jsonify({"error": "Invalid token"}), 401

        user = session.user
        role = Role.query.get(user.role_id)
        if not role or role.role_name != "admin":
            return jsonify({"error": "Forbidden: only admin can set availability"}), 403

            # تبدیل زمان و تاریخ
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            return jsonify({"error": "Invalid date or time format"}), 400

        if start_time >= end_time:
            return jsonify({"error": "Start time must be before end time"}), 400

            # بررسی تداخل بازه زمانی
        overlap = Availability.query.filter(
            Availability.date == date_obj,
            db.or_(
                db.and_(
                    Availability.start_time <= start_time,
                    Availability.end_time > start_time,
                ),
                db.and_(
                    Availability.start_time < end_time,
                    Availability.end_time >= end_time,
                ),
                db.and_(
                    Availability.start_time >= start_time,
                    Availability.end_time <= end_time,
                ),
            ),
        ).first()

        if overlap:
            return (
                jsonify(
                    {"error": "This time range overlaps with existing availability"}
                ),
                409,
            )

            # ذخیره‌سازی در دیتابیس
        availability = Availability(
            day_of_week=day_of_week,
            date=date_obj,
            start_time=start_time,
            end_time=end_time,
        )
        db.session.add(availability)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "✅ Availability set successfully",
                    "day_of_week": day_of_week,
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "start_time": start_time.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                }
            ),
            201,
        )

    # ثبت رزرو دانشجو

    @app.route("/student/make-reservation", methods=["POST"])
    def make_reservation():
        data = request.get_json()

        student_id = data.get("student_id")
        reservation_time = data.get("reservation_time")
        day_of_week = data.get("day_of_week")

        if not all([student_id, reservation_time, day_of_week]):
            return jsonify({"error": "Missing fields"}), 400

        availability = Availability.query.filter_by(day_of_week=day_of_week).first()
        if not availability:
            return jsonify({"error": "No availability for this day"}), 400

        reservation_time_obj = datetime.strptime(reservation_time, "%H:%M").time()
        if not (
            availability.start_time <= reservation_time_obj <= availability.end_time
        ):
            return (
                jsonify({"error": "Selected time is outside of valid availability"}),
                400,
            )

        reservation = Reservation(
            student_id=student_id,
            reserved_at=reservation_time_obj,
            duration_minutes=60,
            request_type="online",
            priority=1,
        )
        db.session.add(reservation)
        db.session.commit()

        return jsonify({"message": "Reservation successful"}), 200

    @app.route("/available-slots", methods=["GET"])
    def get_available_slots():
        day_of_week = request.args.get("day_of_week")
        date_str = request.args.get("date")  # مثال: "2025-05-01"
        if not all([day_of_week, date_str]):
            return jsonify({"error": "Missing date or day_of_week"}), 400

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        availabilities = Availability.query.filter_by(
            day_of_week=day_of_week, date=date_obj
        ).all()

        available_slots = []

        for avail in availabilities:
            current = datetime.combine(date_obj, avail.start_time)
            end = datetime.combine(date_obj, avail.end_time)

            while current + timedelta(minutes=15) <= end:
                slot_start = current
                slot_end = current + timedelta(minutes=15)

                # بررسی اینکه آیا این اسلات رزرو شده یا نه
                overlap = Reservation.query.filter(
                    db.func.date(Reservation.reserved_at) == date_obj,
                    Reservation.reserved_at >= slot_start,
                    Reservation.reserved_at < slot_end,
                ).first()

                if not overlap:
                    available_slots.append(
                        {
                            "start": slot_start.strftime("%Y-%m-%d %H:%M"),
                            "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                        }
                    )

                current = slot_end

        return jsonify({"available_slots": available_slots})

    @app.route("/student/book-slot", methods=["POST"])
    def book_slot():
        data = request.get_json()
        student_id = data.get("student_id")
        reserved_at_str = data.get("reserved_at")  # مثال: 2025-05-01 12:15

        if not all([student_id, reserved_at_str]):
            return jsonify({"error": "Missing student_id or reserved_at"}), 400

        # بررسی فرمت و اعتبار زمان ورودی
        try:
            reserved_at = datetime.strptime(reserved_at_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return (
                jsonify({"error": "Invalid datetime format, use YYYY-MM-DD HH:MM"}),
                400,
            )

        # بررسی اینکه دقیقه و ثانیه باید دقیقاً روی اسلات ۱۵ دقیقه‌ای باشد
        if reserved_at.minute % 15 != 0 or reserved_at.second != 0:
            return (
                jsonify(
                    {
                        "error": "Time must align to 15-minute slots exactly (e.g., 12:00, 12:15...)"
                    }
                ),
                400,
            )

        date_obj = reserved_at.date()
        time_obj = reserved_at.time()
        slot_end = (reserved_at + timedelta(minutes=15)).time()

        # بررسی وجود اسلات در availability
        matching_slot = Availability.query.filter(
            Availability.date == date_obj,
            Availability.start_time <= time_obj,
            Availability.end_time >= slot_end,
        ).first()

        if not matching_slot:
            return (
                jsonify({"error": "Selected time does not match any available slot"}),
                400,
            )

        # بررسی رزرو نبودن تایم
        existing_reservation = Reservation.query.filter(
            db.func.date(Reservation.reserved_at) == date_obj,
            Reservation.reserved_at == reserved_at,
        ).first()

        if existing_reservation:
            return jsonify({"error": "This slot is already reserved"}), 409

        # ایجاد رزرو
        reservation = Reservation(
            student_id=student_id,
            reserved_at=reserved_at,
            duration_minutes=15,
            request_type="online",
            priority=1,
        )
        db.session.add(reservation)
        db.session.commit()

        return jsonify({"message": "✅ Slot reserved successfully"}), 201
