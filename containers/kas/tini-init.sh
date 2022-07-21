#!/usr/bin/env bash
set -e

gunicorn --statsd-host "${STATSD_HOST}:${STATSD_PORT}" --limit-request-field_size 65535 --statsd-prefix "service.kas" \
    --config "gunicorn.conf.py" --bind ":8000" wsgi:app &
/opentdf/bin/access-pdp-grpc-server &
wait -n
