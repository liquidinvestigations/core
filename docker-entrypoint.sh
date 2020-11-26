#!/bin/bash -ex

./manage.py initialize

chown -R $UID:$GID $DATA_DIR

exec gosu $USER_NAME ./manage.py initialize

exec gosu $USER_NAME "$@"
