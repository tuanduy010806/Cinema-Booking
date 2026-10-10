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


## Run authentication smoke tests

Install the packages in `requirements.txt`, configure `TEST_DATABASE_URL` in
`.env.test` using `.env.test.example`, and make sure the PostgreSQL test
database is available. Run the HTTP smoke tests and database-free auth service
tests with:

```sh
pytest tests/test_auth.py
pytest tests/unit/test_auth.py
```

The HTTP tests cover registration, login, a JWT-protected request, anonymous
access rejection, and USER/ADMIN authorization. The unit tests cover password
hashing, token claims, and invalid-password rejection.

## Provision an ADMIN account

Public registration always creates a `USER`. The registration endpoint does
not accept a role change. To grant administrator access, an operator must
first register the account normally, then update that user's role directly in
the development or deployment PostgreSQL database.

For the local database started by `docker-compose.yml`, open a PostgreSQL
prompt with:

```sh
docker compose exec db psql -U cinema -d cinema_booking
```

Then run the following statement with the registered account's exact email:

```sql
UPDATE users
SET role = 'ADMIN'
WHERE email = 'admin@example.com';
```

Confirm PostgreSQL reports exactly one updated row, then verify the account:

```sql
SELECT email, role FROM users WHERE email = 'admin@example.com';
```

Use a trusted operator connection for this database change. Do not expose an
ADMIN registration endpoint or accept `role` from a public request body. The
administrator signs in through the normal `/api/v1/auth/login` endpoint after
the role change.
