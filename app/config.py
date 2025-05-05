import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:sina@localhost:3306/room_reservation'
    SQLALCHEMY_TRACK_MODIFICATIONS = False