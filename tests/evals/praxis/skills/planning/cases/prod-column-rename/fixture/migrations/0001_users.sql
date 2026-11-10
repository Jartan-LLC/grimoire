CREATE TABLE users (
    id bigserial PRIMARY KEY,
    email text NOT NULL,
    name text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX users_email_key ON users (email);
