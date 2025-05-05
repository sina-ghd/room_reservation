from . import db
from datetime import datetime


class Role(db.Model):
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"))
    created_at = db.Column(db.DateTime)

    role = db.relationship("Role", backref="users")


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    student_identifier = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=True)  # ← اضافه شد

    user = db.relationship("User", backref="student")
    reservations = db.relationship("Reservation", backref="student", lazy=True)

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "user_id": self.user_id,
            "student_identifier": self.student_identifier,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "reservations": [r.to_dict() for r in self.reservations],
        }


class Admin(db.Model):
    __tablename__ = "admins"
    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    user = db.relationship("User", backref="admin")


class Reservation(db.Model):
    __tablename__ = "reservations"

    reservation_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    reserved_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    request_type = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ارتباط یک به چند با مدل Student

    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "student_id": self.student_id,
            "reserved_at": self.reserved_at.strftime("%Y-%m-%d %H:%M"),
            "duration_minutes": self.duration_minutes,
            "request_type": self.request_type,
            "priority": self.priority,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None
            ),
        }


class AuthCode(db.Model):
    __tablename__ = "auth_codes"
    code_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="auth_codes")


class SessionToken(db.Model):
    __tablename__ = "session_tokens"
    session_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="session_tokens")


class Availability(db.Model):
    __tablename__ = "availability"

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(9), nullable=False)  # Saturday, Monday, ...
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Availability {self.date} ({self.day_of_week}) {self.start_time}-{self.end_time}>"
