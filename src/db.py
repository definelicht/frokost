#!/usr/bin/env python3
import sqlalchemy as sql
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists
import argparse

###############################################################################

Base = declarative_base()

###############################################################################
# Schema definition
###############################################################################


class Lunch(Base):
    __tablename__ = "lunch"

    id = sql.Column(sql.Integer, primary_key=True)
    date = sql.Column(sql.Date, unique=True)
    facebook_event = sql.Column(sql.Text)


class Guest(Base):
    __tablename__ = "guest"

    id = sql.Column(sql.Integer, primary_key=True)
    first_name = sql.Column(sql.String(length=127))
    last_name = sql.Column(sql.String(length=127))
    nationality = sql.Column(sql.String(length=127))


class Attendance(Base):
    __tablename__ = "attendance"

    guest_id = sql.Column(
        sql.Integer, sql.ForeignKey(Guest.id), primary_key=True)
    lunch_id = sql.Column(
        sql.Integer, sql.ForeignKey(Lunch.id), primary_key=True)

    guest = orm.relationship("Guest", back_populates="attendances")
    lunch = orm.relationship("Lunch", back_populates="attendances")


Lunch.attendances = orm.relationship(
    "Attendance", order_by=Attendance.guest_id, back_populates="lunch")
Guest.attendances = orm.relationship(
    "Attendance", order_by=Attendance.lunch_id, back_populates="guest")

###############################################################################
# Executable
###############################################################################

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("database", type=str)
    arg_parser.add_argument("--create", action="store_true")
    arg_parser.add_argument("--verbose", action="store_true")

    args = vars(arg_parser.parse_args())
    database_path = args["database"]
    should_create = args["create"]
    verbose = args["verbose"]

    if not should_create:
        if not database_exists(database_path):
            raise RuntimeError(
                "Database \"{}\" does not exist. "
                "Use --create to create it at the specified location.".format(
                    database_path))
        engine = sql.create_engine(database_path, echo=verbose)
        engine.connect()
        print("Database \"{}\" is valid.".format(database_path))
    else:
        if database_exists(database_path):
            raise RuntimeError(
                "Database \"{}\" already exists.".format(database_path))
        engine = sql.create_engine(database_path, echo=verbose)
        Base.metadata.create_all(engine)
