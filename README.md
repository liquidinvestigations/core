# Liquid Investigations: Central User Database

The `liquid-core` app serves as the central user database in the bundle.

It's a Django app with the `django-oauth-toolkit` plugin installed,
which acts as an OAuth2 provider. The users are stored as plain Django
users, and they can be managed via Django's admin pages.
