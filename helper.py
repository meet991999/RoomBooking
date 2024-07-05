from datetime import datetime, timedelta

def coonvert_to_ist(date):
    """
    conver the date to ist from utc
    :param date:
    :return: ist date
    """
    time_difference = timedelta(hours=5, minutes=30)
    ist_datetime_object = date + time_difference
    formatted_date = ist_datetime_object.strftime("%d-%m-%YT%H:%M")
    return ist_datetime_object, formatted_date

def parse_date_time(date_str, time_slot):
    """
    parse the date and time
    :param date_str:
    :param time_slot:
    :return:
    """

    date = datetime.strptime(date_str, "%d-%m-%Y")
    start_time_str, end_time_str = time_slot.split('-')
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    start_datetime = datetime.combine(date, start_time)
    return start_datetime


def add_minutes_to_time(time_str, minutes_to_add):
    """
    add specifiec to time
    :param time_str:
    :param minutes_to_add:
    :return: return the new time string
    """

    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time_obj = time_obj + timedelta(minutes=minutes_to_add)
    new_time_str = new_time_obj.strftime("%H:%M")

    return new_time_str



def check_availability(room_list):
    """
    calculate the availability of each room
    :param room_list:
    :return: availability status
    """
    current_time_ist = datetime.now()
    current_date = current_time_ist.strftime("%d-%m-%Y")
    current_time_str = current_time_ist.strftime("%H:%M")
    is_within_working_hours = (10 <= int(current_time_str[:2])) and (int(current_time_str[:2]) < 19)
    print(is_within_working_hours)
    if is_within_working_hours:
        print(room_list)
        if current_date in list(room_list.keys()):
            check_time_obj = datetime.strptime(current_time_str, "%H:%M")
            for time_range in room_list[current_date]:
                start_time, end_time = time_range.split(" - ")
                start_time_obj = datetime.strptime(start_time, "%H:%M")
                end_time_obj = datetime.strptime(end_time, "%H:%M")
                if start_time_obj < check_time_obj < end_time_obj:
                    return "availabile today"

            else:
                return "available right now"
        else:
            return "available right now"
    else:
        return "available tomorrow"


def upsert_document(collection, name, db):
    """
    insert document to collection
    :param collection:
    :param name:
    :return: object id as string
    """
    doc = db[collection].find_one({"name": name})
    if doc:
        return str(doc["_id"])
    else:
        result = db[collection].insert_one({"name": name})
        return str(result.inserted_id)

