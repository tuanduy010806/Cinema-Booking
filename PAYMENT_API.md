# Standalone demo payment API

This payment module is intentionally isolated from the booking and seat-hold flows. It stores `hold_id` as a unique integer reference, but there is no hold table in the current application, so the API cannot verify that reference or create bookings.

The backend charges a fixed demo amount configured with `DEMO_PAYMENT_AMOUNT_VND` (default `100000`); clients cannot submit an amount or payment status. A successful demo request records the payment as `succeeded` immediately.

## Create a demo payment

`POST /api/v1/payments` (authenticated)

```json
{"hold_id": 12}
```

The response contains `id`, `hold_id`, `amount`, `currency`, `status`, `created_at`, and `paid_at`. A new payment returns `201`; repeating the request as the same user returns the existing payment with `200`. A reference already owned by another user returns `409`.

## Payment history

`GET /api/v1/payments/me` returns the authenticated user's payment records.

For a fresh database, `py scripts/init_db.py` creates the `payments` table. Existing booking tables and business flows are not changed by this module.
