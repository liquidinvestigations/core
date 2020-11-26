#!/bin/bash -ex

./manage.py initialize

chown -R $UID:$GID $DATA_DIR

exec gosu $USER_NAME ./manage.py migrate .

exec gosu $USER_NAME "$@"
