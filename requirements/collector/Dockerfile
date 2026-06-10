FROM alpine:latest

RUN apk update && apk add --no-cache python3 py3-pip bash

WORKDIR /app

COPY app/ .
COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["tail", "-f", "/var/log/cron.log"]
