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


def add_lunch(session, date, facebook_event):
    lunch = db.Lunch(date=date, facebook_event=facebook_event)
    session.add(lunch)
    session.commit()
    print("Successfully added:\n{}".format(lunch))


def get_or_create_guest(session, facebook_name):
    """Identifies guests based on their facebook names, and adds them if they
    are not already present in the database."""
    try:
        return session.query(
            db.Guest).filter(db.Guest.facebook_name == facebook_name).one()
    except sql.orm.exc.NoResultFound:
        split = facebook_name.split(" ")
        first_name = split[0]
        last_name = " ".join(split[1:])
        print("Creating new guest: {} {}".format(first_name, last_name))
        entry = db.Guest(
            first_name=first_name,
            last_name=last_name,
            facebook_name=facebook_name)
        session.add(entry)
        session.commit()
        return entry


def import_guest_list(session, event, year, path):
    """Import a facebook guest list in .csv format by adding attendance
    entries, and creating guests not already present in the database."""
    lunch = get_lunch(session, event, year)
    attendees = []
    with open(path, "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for row in reader:
            guest = get_or_create_guest(session, row[0])
            if row[1] == "Going":
                print("Adding {}...".format(guest))
                entry = db.Attendance(guest_id=guest.id, lunch_id=lunch.id)
                attendees.append(entry)
            else:
                print("Guest {} did not mark attendance on Facebook.".format(
                    row[0]))
        session.add_all(attendees)
    session.commit()


def list_guests(session, event, year):
    lunch = get_lunch(session, event, year)
    print("Listing guests for:\n{}\nA total of {} guests attended:".format(
        lunch, len(lunch.attendances)))
    for a in lunch.attendances:
        print(a.guest)


def list_guests_by_attendance(session):
    res = session.query(
        db.Guest,
        sql.func.count(
            db.Attendance.lunch_id).label("attendances")).select_from(
                db.Attendance).join(db.Guest).group_by(
                    db.Guest.last_name).order_by(
                        "attendances DESC, first_name, last_name").all()
    print("Listing guests by attendance in descending order:")
    for r in res:
        print("{}: {}".format(r[0], r[1]))


def list_lunches(session):
    print("Listing all registered lunches in chronological order...")
    for lunch in session.query(db.Lunch).order_by(db.Lunch.date).all():
        print(lunch)


def delete_attendances(session, event, year):
    lunch = get_lunch(session, event, year)
    count = 0
    for a in lunch.attendances:
        session.delete(a)
        count += 1
    answer = input(
        "Are you sure you want to remove {} attendances? [y/N] ".format(count))
    if answer.strip() == "y":
        session.commit()
        print("Successfully removed attendances.")
    else:
        print("Action cancelled.")


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
    argParser.add_argument("--database", default="sqlite:///lunch.sqlite")

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

    list_lunches_args = subparsers.add_parser("list_lunches")

    list_guests_by_attendance_args = subparsers.add_parser(
        "list_guests_by_attendance")

    add_lunch_args = subparsers.add_parser("add_lunch")
    add_lunch_args.add_argument("date", type=valid_date_type)
    add_lunch_args.add_argument("facebook_event", type=str)

    delete_attendances_args = subparsers.add_parser("delete_attendances")
    delete_attendances_args.add_argument(
        "event", type=str, choices=["easter", "christmas"])
    delete_attendances_args.add_argument("year", type=int)

    args = vars(argParser.parse_args())
    command = args["command"]

    session = db.connect(args["database"])

    if command == "list_guests":
        list_guests(session, args["event"], args["year"])
    elif command == "list_lunches":
        list_lunches(session)
    elif command == "import_guest_list":
        import_guest_list(session, args["event"], args["year"], args["path"])
    elif command == "add_lunch":
        add_lunch(session, args["date"], args["facebook_event"])
    elif command == "delete_attendances":
        delete_attendances(session, args["event"], args["year"])
    elif command == "list_guests_by_attendance":
        list_guests_by_attendance(session)
    else:
        raise NotImplementedError(
            "Command \"{}\" not implemented".format(command))
