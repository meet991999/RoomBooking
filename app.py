from datetime import timedelta, datetime
import jwt
import secrets
from functools import wraps
from flask import Flask, request, jsonify, g, make_response
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv
load_dotenv()
from helper import *

app = Flask(__name__)

MONGO_URI = os.environ['CONNECTION_STRING']
secret_key = 'xtsXryhxiSjMBdJ9ZL1F5SphVIa00yVRIEII9C_H32g'
app.config['SECRET_KEY'] = secret_key

client = MongoClient(MONGO_URI)

db = client['test_1']

try:
    index_fields = [('booking_date_time', 1), ('room_id', 1)]
    db.room_booking_details.create_index(index_fields, unique=True)
except Exception as e:
    print(e)

try:
    db.session.create_index([('email', ASCENDING)], unique=True)
except Exception as e:
    print(e)

try:
    db.rooms.create_index([('room_name', ASCENDING)], unique=True)
except Exception as e:
    print(e)


def token_required(f):
    """
    decorate route to require token
    :param f:
    :return: return functoin on verification of the token otherwise error
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            g.current_user = data['email']
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/')
def generate_token():
    """
    index function to generate token and give basic room information
    :return: access token in header and basic room data in json format
    """
    email = request.args.get('email')
    page = int(request.args.get('page', 0))
    if not email:
        return jsonify({'error': 'Email parameter is missing'}), 400

    doc = db.session.find_one({"email": email})
    if doc:
        access_token = doc['access_token']
    else:
        access_token = jwt.encode({
            'email': email,
        }, app.config['SECRET_KEY'], algorithm='HS256')
        data = {'access_token': access_token, "email": email, "created_at": datetime.utcnow()}
        db.session.insert_one(data)
    pipeline = [
        {
            "$lookup": {
                "from": "room_booking_details",
                "localField": "_id",
                "foreignField": "room_id",
                "as": "booking_details"
            }
        },
        {
            "$unwind": {
                "path": "$booking_details",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "room_name": {"$first": "$room_name"},
                "tags": {"$first": "$tags"},
                "seat_capacity": {"$first": "$seat_capacity"},
                "createdAt": {"$first": "$createdAt"},
                "booking_date_times": {"$push": "$booking_details.booking_date_time"}
            }
        },
        {
            "$unwind": {
                "path": "$booking_date_times",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$sort": {
                "booking_date_times": 1
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "room_name": {"$first": "$room_name"},
                "tags": {"$first": "$tags"},
                "seat_capacity": {"$first": "$seat_capacity"},
                "createdAt": {"$first": "$createdAt"},
                "sorted_booking_dates": {"$push": "$booking_date_times"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "room_name": 1,
                "tags": 1,
                "seat_capacity": 1,
                "createdAt": 1,
                "booking_date_times": "$sorted_booking_dates"
            }
        },
        {
         "$limit": 5
        },
        {
            "$skip": page  # Add the $skip stage here to skip the first 5 documents
        },
    ]

    room_list = list(db.rooms.aggregate(pipeline))
    for i in room_list:
        for key, value in i.items():
            date_dict = {}
            if key == "createdAt":
                ist, formated = coonvert_to_ist(i['createdAt'])
                i['createdAt'] = ist
            if key == "booking_date_times":
                sorted_list = sorted(value)
                for j in range(len(sorted_list)):
                    raw_date = value[j].strftime("%d-%m-%YT%H:%M")
                    print(raw_date,"ksdfj")
                    raw_date_list = raw_date.split('T')
                    if raw_date_list[0] in date_dict.keys():
                        date_dict[raw_date_list[0]].append(raw_date_list[1] + " - "+add_minutes_to_time(raw_date_list[1], 30))
                    else:
                        date_dict[raw_date_list[0]] = [raw_date_list[1] + " - " + add_minutes_to_time(raw_date_list[1], 30)]

            if key == "_id":
                i[key] = str(i[key])
        print(i['booking_date_times'],"thuis siisisis")
        i['room_availability'] = check_availability(date_dict)
        del i["booking_date_times"]
    response = make_response(jsonify({'data': room_list}))
    response.headers['x-access-tokens'] = access_token
    return response





@app.route('/view-room-data', methods=['GET'])
@token_required
def view_room_data():
    """
    get room booking details of one month
    :return: room data in json format
    """
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({'error': 'Room ID is missing'}), 400
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    end_of_month = datetime(now.year, now.month + 1, 1) - timedelta(days=1) if now.month < 12 else datetime(
        now.year + 1, 1, 1) - timedelta(days=1)

    # Define the query
    query = {
        "room_id": ObjectId(room_id),
        "booking_date_time": {"$gte": start_of_month, "$lte": end_of_month}
    }
    booking_data = list(db.room_booking_details.find(query, {'_id': 0, 'booking_date_time': 1}))
    date_dict = {}
    if booking_data:
        for i in booking_data:
            raw_date = i['booking_date_time'].strftime("%d-%m-%YT%H:%M")
            raw_date_list = raw_date.split('T')
            if raw_date_list[0] in date_dict.keys():
                date_dict[raw_date_list[0]].append(raw_date_list[1] + " - " + add_minutes_to_time(raw_date_list[1], 30))
            else:
                date_dict[raw_date_list[0]] = [raw_date_list[1] + " - " + add_minutes_to_time(raw_date_list[1], 30)]

    return jsonify({'data': date_dict}), 200



@app.route('/create-room', methods=['POST'])
@token_required
def create_room():
    """
    function to create a new room
    :return: return room id
    """
    data = request.json
    if "room_name" not in data.keys() or "seat_capacity" not in data.keys():
        return jsonify({'error': 'room_name or seat_capacity missing'}), 400
    try:
        tags = data['tags']
        if not isinstance(tags, list):
            return jsonify({'error': 'tags must be a list'}), 400
        if tags:
            ids = [upsert_document('tags', tag,db) for tag in tags]
            data['tags'] = ids
        else:
            del data['tags']
        data['createdAt'] = datetime.utcnow()
        result = db.rooms.insert_one(data)
        return jsonify({"_id": str(result.inserted_id),'room_name':data['room_name']}), 201
    except DuplicateKeyError:
        return jsonify({"error": "Room already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/book-room', methods=['POST'])
@token_required
def book_room():
    """
    function to store room booking details,
    this function will require room_name, booking_Date, booking_time_slot
    :return: success of failure of room booking
    """
    data = request.json
    try:
        if 'room_name' not in data or 'booking_date' not in data or 'booking_time_slot' not in data:
            return jsonify({'error': 'Missing required fields'}), 401

        room_name = data['room_name']
        try:
            date_time_slot = parse_date_time(data['booking_date'], data['booking_time_slot'])
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        room_doc = db.rooms.find_one({"room_name": room_name})
        if not room_doc:
            return jsonify({'error': 'Room not found'}), 404
        room_id = room_doc['_id']

        access_token = request.headers.get('x-access-tokens')
        session_doc = db.session.find_one({"access_token": access_token})
        if not session_doc:
            return jsonify({'error': 'Session not found'}), 404
        session_id = session_doc['_id']

        booking_data = {
            'room_id': room_id,
            'session_id': session_id,
            'booking_date_time': date_time_slot,
            'created_at': datetime.utcnow()
        }

        db.room_booking_details.insert_one(booking_data)
        return jsonify({'message': 'Room booked successfully'}), 201

    except DuplicateKeyError:
        return jsonify({'error': 'Booking already exists for this time slot'}), 409
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500



@app.route('/get-reserved-records', methods=['GET'])
@token_required
def get_reserved_records():
    """
    get all booking details of specific person
    :return: booking data in json format
    """
    access_token = request.headers.get('x-access-tokens')
    session_doc = db.session.find_one({"access_token": access_token})
    if not session_doc:
        return jsonify({'Data': 'No records Found'}), 200
    session_id = session_doc['_id']
    print(session_id)
    pipeline = [
        {
            "$match": {
                "session_id": session_id
            }
        },
        {
            "$lookup": {
                "from": "rooms",
                "localField": "room_id",
                "foreignField": "_id",
                "as": "room_details"
            }
        },
        {
            "$unwind": "$room_details"
        },
        {
            "$group": {
                "_id": "$room_details.room_name",
                "bookings": {
                    "$push": {
                        "booking_date_time": "$booking_date_time",
                        "created_at": "$created_at"
                    }
                }
            }
        },
        {
            "$sort": {"_id": 1}
        },
        {
            "$project": {
                "_id": 0,
                "room_name": "$_id",
                "bookings": 1
            }
        }
    ]
    result = list(db.room_booking_details.aggregate(pipeline))
    for i in result:
        for key,value in i.items():
            if key=='bookings':
                for j in value:
                    for k,v in j.items():
                        if k=='booking_date_time':
                            j['booking_date_time'] = v.strftime("%d-%m-%Y %H:%M")


    return jsonify({'Data': result}), 200


@app.route('/search', methods=['GET'])
@token_required
def search():
    """
    function to dearch all rooms based on room name or date
    :return: basic room data in json
    """
    room_name = request.args.get('room_name')
    print(room_name,"this is trhe room")
    booking_date_start = request.args.get('booking_date_start')
    booking_date_end = request.args.get('booking_date_end')
    page = int(request.args.get('page',0))
    if not booking_date_end or not booking_date_start:
        return jsonify({'error': 'Missing required fields'}), 400
    filters = {
    }
    if room_name:
        filters['room_name'] = room_name
    if booking_date_start:
        filters['date_start'] = booking_date_start
        filters['date_end'] = booking_date_end

    date_conditions = {}
    if "date_start" in filters and "date_end" in filters:
        end_date = datetime.strptime(filters["date_end"], "%d-%m-%Y") + timedelta(days=1, microseconds=-1)
        date_conditions = {
            "booking_details.booking_date_time": {
                "$gte": datetime.strptime(filters["date_start"], "%d-%m-%Y"),
                "$lte": end_date
            }
        }

    room_name_condition = {}
    if "room_name" in filters:
        room_name_condition = {"room_name": filters["room_name"]}

    pipeline = [
        {
            "$lookup": {
                "from": "room_booking_details",
                "localField": "_id",
                "foreignField": "room_id",
                "as": "booking_details"
            }
        },
        {
            "$unwind": {
                "path": "$booking_details",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$match": {
                "$and": [
                    {"$or": [
                        {"booking_details.booking_date_time": {"$exists": False}},
                        date_conditions if date_conditions else {"booking_details.booking_date_time": {"$exists": True}}
                    ]},
                    room_name_condition if room_name_condition else {}
                ]
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "room_name": {"$first": "$room_name"},
                "tags": {"$first": "$tags"},
                "seat_capacity": {"$first": "$seat_capacity"},
                "createdAt": {"$first": "$createdAt"},
                "booking_date_times": {"$push": "$booking_details.booking_date_time"}
            }
        },
        {
            "$unwind": {
                "path": "$booking_date_times",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$sort": {
                "booking_date_times": 1
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "room_name": {"$first": "$room_name"},
                "tags": {"$first": "$tags"},
                "seat_capacity": {"$first": "$seat_capacity"},
                "createdAt": {"$first": "$createdAt"},
                "sorted_booking_dates": {"$push": "$booking_date_times"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "room_name": 1,
                "tags": 1,
                "seat_capacity": 1,
                "createdAt": 1,
                "booking_date_times": "$sorted_booking_dates"
            }
        },
        {
            "$skip": page
        },
        {
            "$limit": 5
        }
    ]

    results = list(db.rooms.aggregate(pipeline))
    for i in results:
        for key, value in i.items():
            date_dict = {}
            if key == "createdAt":
                ist, formated = coonvert_to_ist(i['createdAt'])
                i['createdAt'] = ist
            if key == "booking_date_times":
                sorted_list = sorted(value)
                for j in range(len(sorted_list)):
                    raw_date = value[j].strftime("%d-%m-%YT%H:%M")
                    print(raw_date,"ksdfj")
                    raw_date_list = raw_date.split('T')
                    if raw_date_list[0] in date_dict.keys():
                        date_dict[raw_date_list[0]].append(raw_date_list[1] + " - "+add_minutes_to_time(raw_date_list[1], 30))
                    else:
                        date_dict[raw_date_list[0]] = [raw_date_list[1] + " - " + add_minutes_to_time(raw_date_list[1], 30)]

            if key == "_id":
                i[key] = str(i[key])
        print(i['booking_date_times'],"suldfhsfgw8uhfguwrgjhd")
        i['room_availability'] = check_availability(date_dict)
        del i["booking_date_times"]
    return jsonify({'data':results}), 200

if __name__ == '__main__':
    app.run(debug=True)