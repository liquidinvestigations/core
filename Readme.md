# Liquid Investigations Core App

## Users
The `liquid-core` app serves as the central user database in the bundle.

It's a Django app with the `django-oauth-toolkit` plugin installed,
which acts as an OAuth2 provider. The users are stored as plain Django
users, and they can be managed via Django's admin pages.

## Configuration
The app is configured by setting environment variables.

* `DEBUG`: set to `true` to enable debugging.
* `SECRET_KEY`: a random secret string.
* `LIQUID_PROTO`: `http` (default) or `https`.
* `LIQUID_DOMAIN`: the domain name, e.g. `liquid.example.com`.
* `SERVICE_ADDRESS`: name or address of the internal service, as it's
  registered in the cluster
