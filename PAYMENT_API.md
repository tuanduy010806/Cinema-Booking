# Seat hold and demo payment API

All hold and payment endpoints require `Authorization: Bearer <access_token>`.
The server holds seats for five minutes. The client does not submit the hold
duration, user ID, amount, or payment result.

For local/Docker configuration, copy `.env.example` to `.env`. Configure
`SEAT_HOLD_TTL_SECONDS` (default `300`) and `DEMO_PAYMENT_AMOUNT_VND` (default
`100000`); Docker Compose passes both values to the API container. This demo
does not connect to an external payment provider.

## Create a hold

`POST /api/v1/holds`

```json
{"showtime_id":1,"seat_numbers":["3","4"]}
```

The request must contain 1–5 distinct positive numeric seat labels. The whole
group is accepted or rejected together. Seats that are actively booked or held
cannot be held. A successful response contains the hold `id`, seat list,
`status`, `created_at`, and `expires_at` (UTC). The five-minute expiry is set by
the server; `SEAT_HOLD_TTL_SECONDS` defaults to `300`.

`GET /api/v1/holds/{hold_id}` returns the caller's hold. Its status is reported
as `expired` after the deadline even if no request has persisted that state yet.
`DELETE /api/v1/holds/{hold_id}` releases an active hold early. A paid hold
cannot be released.

`GET /api/v1/showtimes/{showtime_id}/seats` reports seats in active, unexpired
holds as unavailable. Expired holds stop blocking seats without a background
worker.

## Pay for a hold

`POST /api/v1/payments`

```json
{"hold_id":123456}
```

The hold must exist, belong to the caller, still be active, and be unexpired.
The demo succeeds immediately and charges
`DEMO_PAYMENT_AMOUNT_VND` per seat (default `100000` VND). The response
contains the payment and every booking created for the held seats. Payment,
booking creation, and the hold's transition to `paid` share one database
transaction. Repeating payment for an already paid hold returns the same
payment and bookings (`200`); a new payment returns `201`.

`GET /api/v1/payments/me` returns the caller's payment history. The existing
single-seat `POST /api/v1/bookings/` API remains available; it rejects seats
held by an active hold.

## Database setup

`scripts/init_db.py` creates missing tables, including hold and payment tables,
for a new database. It does not alter existing tables or replace a schema
migration tool. The application uses straightforward checks in each request;
it does not serialize simultaneous requests that claim the same seat.
