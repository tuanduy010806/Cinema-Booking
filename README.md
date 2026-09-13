## 📁 Project Structure

```text
cinema-booking/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── movie.py
│   │   ├── showtime.py
│   │   └── booking.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── movie_service.py
│   │   ├── showtime_service.py
│   │   └── booking_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── movie_repository.py
│   │   ├── showtime_repository.py
│   │   └── booking_repository.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── movie.py
│   │   ├── showtime.py
│   │   └── booking.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── movie.py
│   │   ├── showtime.py
│   │   └── booking.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   ├── auth_middleware.py
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   └── main.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_movie.py
│   ├── test_showtime.py
│   └── test_booking.py
│
├── load_test/
│   └── load_test.py
│
├── seed.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore

