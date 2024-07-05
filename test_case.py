import threading
import unittest
import json
from app import app, client

class FlaskAppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        # Get tokens for two different users
        self.token_user1 = self.get_token('user1@example.com')
        self.token_user2 = self.get_token('user2@example.com')
        # Create a room
        self.room_name = self.create_room()

    def get_token(self, email):
        response = self.client.get(f'/?email={email}')
        return response.headers.get('x-access-tokens')

    def create_room(self):
        response = self.client.post('/create-room',
                                    headers={'x-access-tokens': self.token_user1},
                                    data=json.dumps({
                                        'room_name': 'Test Room 2',
                                        'tags': ['Conference', 'Meeting'],
                                        'seat_capacity': 10
                                    }),
                                    content_type='application/json')
        data = json.loads(response.data)
        return data['room_name']

    def book_room(self, token, room_name, booking_date, booking_time_slot):
        response = self.client.post('/book-room',
                                    headers={'x-access-tokens': token},
                                    data=json.dumps({
                                        'room_name': room_name,
                                        'booking_date': booking_date,
                                        'booking_time_slot': booking_time_slot
                                    }),
                                    content_type='application/json')
        return response

    def test_simultaneous_booking_requests(self):
        booking_date = '05-07-2024'
        booking_time_slot = '12:00-12:30'

        def book_room_and_store_response(token, responses, index):
            response = self.book_room(token, self.room_name, booking_date, booking_time_slot)
            responses[index] = response

        responses = [None, None]

        thread_user1 = threading.Thread(target=book_room_and_store_response, args=(self.token_user1, responses, 0))
        thread_user2 = threading.Thread(target=book_room_and_store_response, args=(self.token_user2, responses, 1))

        thread_user1.start()
        thread_user2.start()

        thread_user1.join()
        thread_user2.join()

        for response in responses:
            print(response)
            data = json.loads(response.data)
            if response.status_code == 201:
                self.assertEqual(data['message'], 'Room booked successfully', "Booking message does not match")
            else:
                self.assertEqual(response.status_code, 409, f"Expected status code 409, but got {response.status_code}")
                self.assertIn('error', data, "Error message is missing in the response")
                self.assertEqual(data['error'], 'Booking already exists for this time slot', "Error message does not match")

        response = self.book_room(self.token_user1, self.room_name, booking_date, '13:00-13:30')
        self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Room booked successfully', "Booking message does not match")

        response = self.book_room(self.token_user2, self.room_name, booking_date, '13:00-13:30')
        self.assertEqual(response.status_code, 409, f"Expected status code 409, but got {response.status_code}")
        data = json.loads(response.data)
        self.assertIn('error', data, "Error message is missing in the response")
        self.assertEqual(data['error'], 'Booking already exists for this time slot', "Error message does not match")

if __name__ == '__main__':
    unittest.main(verbosity=2)
