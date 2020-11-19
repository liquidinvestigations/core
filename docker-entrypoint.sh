#!/bin/bash -ex

if [[ ! -d "$DATA_DIR" ]]; then
        exit 1
fi

./manage.py initialize

chown -R $UID:$GID $DATA_DIR

exec gosu $USER_NAME "$@"
