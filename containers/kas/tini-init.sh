#!/usr/bin/env bash
set -e

/opentdf/bin/access-pdp-grpc-server &
gunicorn --statsd-host "${STATSD_HOST}:${STATSD_PORT}" --limit-request-field_size 65535 --statsd-prefix "service.kas" \
    --config "gunicorn.conf.py" --bind ":8000" --logger-class=kas_logger.KasLogger -k uvicorn.workers.UvicornWorker \
    run:app &
wait -n
