#!/usr/bin/env python3
import argparse
import csv
import datetime
import sqlalchemy as sql

import db


def get_lunch(session, event, year):
    if event == "easter":
        return session.query(
            db.Lunch).filter(db.Lunch.date >= "{}-03-01".format(year),
                             db.Lunch.date < "{}-09-01".format(year)).one()
    elif event == "christmas":
        return session.query(db.Lunch).filter(
            db.Lunch.date >= "{}-11-01".format(year),
            db.Lunch.date < "{}-03-01".format(year + 1)).one()
    else:
        raise RuntimeError("Unknown event type \"{}\"".format(event))


def get_or_create_guest(session, facebook_name):
    try:
        return session.query(
            db.Guest).filter(db.Guest.facebook_name == facebook_name).one()
    except sql.orm.exc.NoResultFound:
        split = facebook_name.split(" ")
        first_name = split[0]
        last_name = " ".join(split[1:])
        entry = db.Guest(
            first_name=first_name,
            last_name=last_name,
            facebook_name=facebook_name)
        session.add(entry)
        session.commit()
        return entry


def import_guest_list(session, event, year, path):
    lunch = get_lunch(session, event, year)
    attendees = []
    with open(path, "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for row in reader:
            guest = get_or_create_guest(session, row[0])
            entry = db.Attendance(guest_id=guest.id, lunch_id=lunch.id)
            attendees.append(entry)
        session.add_all(attendees)
    session.commit()


def list_guests(session, event, year):
    lunch = get_lunch(session, event, year)
    for a in lunch.attendances:
        print(a.guest)


def add_lunch(session, date):
    entry = db.Lunch(date=date)
    session.add(entry)
    session.commit()


# From https://gist.github.com/monkut/e60eea811ef085a6540f
def valid_date_type(arg_date_str):
    try:
        return datetime.datetime.strptime(arg_date_str, "%Y-%m-%d")
    except ValueError:
        msg = ("Given Date ({0}) not valid! "
               "Expected format, YYYY-MM-DD!".format(arg_date_str))
        raise argparse.ArgumentTypeError(msg)


if __name__ == "__main__":

    argParser = argparse.ArgumentParser()
    argParser.add_argument("database")

    subparsers = argParser.add_subparsers(dest="command")
    subparsers.required = True

    import_args = subparsers.add_parser("import_guest_list")
    import_args.add_argument(
        "event", type=str, choices=["easter", "christmas"])
    import_args.add_argument("year", type=int)
    import_args.add_argument("path", type=str)

    list_args = subparsers.add_parser("list_guests")
    list_args.add_argument("event", type=str, choices=["easter", "christmas"])
    list_args.add_argument("year", type=int)

    add_lunch_args = subparsers.add_parser("add_lunch")
    add_lunch_args.add_argument("date", type=valid_date_type)

    args = vars(argParser.parse_args())
    command = args["command"]

    session = db.connect(args["database"])

    if command == "list_guests":
        list_guests(session, args["event"], args["year"])
    elif command == "import_guest_list":
        import_guest_list(session, args["event"], args["year"], args["path"])
    elif command == "add_lunch":
        add_lunch(session, args["date"])
    else:
        raise NotImplementedError(
            "Command \"{}\" not implemented".format(command))
