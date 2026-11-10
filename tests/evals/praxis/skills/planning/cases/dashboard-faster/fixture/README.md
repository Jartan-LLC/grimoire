# sales-dashboard

Internal dashboard for the sales team (about 60 people). A Flask app on one server, with
Postgres behind it. `flask --app dash run` starts it locally against `DATABASE_URL`.

Pages: Overview (`/`), Orders (`/orders`), Reports (`/reports`), Settings (`/settings`).
