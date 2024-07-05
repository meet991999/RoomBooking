
# Room Booking Service API

This document provides an overview of the APIs available in the Room Booking Service. It includes details about the endpoints, required parameters, and expected responses.

## API Endpoints

### 1. Generate Token
- **Endpoint**: `/`
- **Method**: `GET`
- **Description**: Generates a token for authentication and provides basic room information.
- **Query Parameters**:
  - `email`: The email of the user (required)
  - `page`: The page number for pagination (optional, default is 0)
- **Response**: Returns a token and room data.

### 2. View Room Data
- **Endpoint**: `/view-room-data`
- **Method**: `GET`
- **Description**: Fetches booking details for a specific room for the current month.
- **Query Parameters**:
  - `room_id`: The ID of the room (required)
- **Response**: Room booking details within the current month.

### 3. Create Room
- **Endpoint**: `/create-room`
- **Method**: `POST`
- **Description**: Creates a new room.
- **Request Body**:
  - `room_name`: Name of the room (required)
  - `seat_capacity`: Capacity of the room (required)
  - `tags`: A list of tags associated with the room (optional)
- **Response**: Returns the ID and name of the created room.

### 4. Book Room
- **Endpoint**: `/book-room`
- **Method**: `POST`
- **Description**: Books a room for a specified date and time.
- **Request Body**:
  - `room_name`: Name of the room (required)
  - `booking_date`: Date for booking (required)
  - `booking_time_slot`: Time slot for booking (required)
- **Response**: Confirmation of the booking.

### 5. Get Reserved Records
- **Endpoint**: `/get-reserved-records`
- **Method**: `GET`
- **Description**: Fetches all booking details of a specific person.
- **Response**: Booking data of the user.

### 6. Search
- **Endpoint**: `/search`
- **Method**: `GET`
- **Description**: Searches for rooms based on name or date.
- **Query Parameters**:
  - `room_name`: The name of the room to filter by (optional)
  - `booking_date_start`: Start date of the booking (required if filtering by date)
  - `booking_date_end`: End date of the booking (required if filtering by date)
  - `page`: The page number for pagination (optional, default is 0)
- **Response**: List of rooms matching the criteria.

## Authentication
Most endpoints require a valid token to be included in the `x-access-tokens` header.

## Errors
Responses will include an appropriate HTTP status code and a JSON body containing error details when applicable.

