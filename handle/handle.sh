#!/bin/sh

HANDLE_BIN="/opt/handle/bin"
HANDLE_SVR="/var/handle/svr"

# Build and configure the server
python3 /home/handle/build.py $HANDLE_BIN $HANDLE_SVR

exec "$HANDLE_BIN/hdl-genericbatch" "$HANDLE_SVR/addadmin.batch"

# Start the handle server
exec "$HANDLE_BIN/hdl-server" $HANDLE_SVR 2>&1

