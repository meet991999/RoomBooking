import unittest
from flask import json
from app import app, client


class RoomBookingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.token = self.get_token()

    def get_token(self):
        response = self.app.get('/?email=test@example.com')
        return response.headers.get('x-access-tokens')

    def tearDown(self):
        client.drop_database('testing_the_testcase')
        print("Dropped test database")

    def test_generate_token(self):
        response = self.app.get('/?email=test@example.com')
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        self.assertIn('x-access-tokens', response.headers, "Token is missing in the headers")

    def test_create_room_already_exists(self):
        response = self.app.post('/create-room',
                                 headers={'x-access-tokens': self.token},
                                 data=json.dumps({
                                     'room_name': 'Test Room',
                                     'tags': ['Conference', 'Meeting'],
                                     'seat_capacity': 10
                                 }),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertIn('_id', data, "Room ID is missing in the response")
        self.assertEqual(data['room_name'], 'Test Room', "Room name does not match")

        response = self.app.post('/create-room',
                                 headers={'x-access-tokens': self.token},
                                 data=json.dumps({
                                     'room_name': 'Test Room',
                                     'tags': ['Conference', 'Meeting'],
                                     'seat_capacity': 10
                                 }),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 400, f"Expected status code 400, but got {response.status_code}")

        data = json.loads(response.data)
        self.assertIn('error', data, "Error message is missing in the response")
        self.assertEqual(data['error'], 'Room already exists', "Error message does not match")

    def test_book_room(self):
        response = self.app.post('/create-room',
                                 headers={'x-access-tokens': self.token},
                                 data=json.dumps({
                                     'room_name': 'Test Room 1',
                                     'tags': ['Conference', 'Meeting'],
                                     'seat_capacity': 10
                                 }),
                                 content_type='application/json')
        data = json.loads(response.data)
        room_name = data['room_name']

        # Now, book the room
        response = self.app.post('/book-room',
                                 headers={'x-access-tokens': self.token},
                                 data=json.dumps({
                                     'room_name': room_name,
                                     'booking_date': '05-07-2024',
                                     'booking_time_slot': '12:00-12:30'
                                 }),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Room booked successfully', "Booking message does not match")

    def test_view_room_data(self):
        response = self.app.get('/view-room-data?room_id=1234567890abcdef12345678',
                                headers={'x-access-tokens': self.token})
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertIn('data', data, "Data is missing in the response")

    def test_get_reserved_records(self):
        response = self.app.get('/get-reserved-records',
                                headers={'x-access-tokens': self.token})
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertIn('Data', data, "Reserved records data is missing")

    def test_search(self):
        response = self.app.get('/search?booking_date_start=01-07-2024&booking_date_end=31-07-2024',
                                headers={'x-access-tokens': self.token})
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertIn('data', data, "Search data is missing in the response")

        response = self.app.get('/search?room_name=Test Room&booking_date_start=01-07-2024&booking_date_end=31-07-2024',
                                headers={'x-access-tokens': self.token})
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        data_1 = json.loads(response.data)
        print(data_1)
        self.assertIn('data', data, "Search data is missing in the response")

if __name__ == '__main__':
    unittest.main(verbosity=2)



