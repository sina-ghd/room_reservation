from flask import Blueprint, jsonify
from .models import Student
from . import db

api = Blueprint('api', __name__)

@api.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([student.to_dict() for student in students])

def init_routes(app):
    from .routes import api
    app.register_blueprint(api)