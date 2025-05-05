from flask import Blueprint, request, jsonify
from app.models import db, Student, Reservation, SessionToken, User
from datetime import datetime

reservation_bp = Blueprint('reservation', __name__)

# ▶️ ایجاد رزرو
@reservation_bp.route('/reserve', methods=['POST'])
def create_reservation():
    student_identifier = request.json.get('student_identifier')
    reserved_at = request.json.get('reserved_at')  # مثال: "2025-04-25 14:15:00"
    request_type = request.json.get('request_type')
    priority = request.json.get('priority')

    student = Student.query.filter_by(student_identifier=student_identifier).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    # تبدیل به datetime
    try:
        reserved_datetime = datetime.strptime(reserved_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    # رزرو جدید
    reservation = Reservation(
        student_id=student.student_id,
        reserved_at=reserved_datetime,
        duration_minutes=15,
        request_type=request_type,
        priority=priority
    )

    db.session.add(reservation)
    db.session.commit()

    return jsonify({"message": "Reservation created successfully!"}), 201


# ▶️ نمایش اطلاعات دانشجو بر اساس توکن
@reservation_bp.route('/me', methods=['GET'])
def get_user_with_reservations():
    token = request.args.get('token')  # توکن از query string دریافت می‌شود

    if not token:
        return jsonify({"error": "Token is required"}), 400

    session = SessionToken.query.filter_by(token=token).first()
    if not session:
        return jsonify({"error": "Invalid token"}), 401

    user = session.user
    student = Student.query.filter_by(user_id=user.user_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    # گرفتن رزروها
    reservations = Reservation.query.filter_by(student_id=student.student_id).all()

    return jsonify({
        "student": {
            "first_name": student.first_name,
            "last_name": student.last_name,
            "student_identifier": student.student_identifier
        },
        "reservations": [
            {
                "reserved_at": r.reserved_at.strftime("%Y-%m-%d %H:%M:%S"),
                "request_type": r.request_type,
                "priority": r.priority
            } for r in reservations
        ]
    }), 200
