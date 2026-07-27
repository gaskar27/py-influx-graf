FROM alpine:latest

RUN apk update && apk add --no-cache python3 py3-pip

WORKDIR /app

COPY app/ .
COPY tools/ /usr/local/bin/tools/

RUN pip install --no-cache-dir --break-system-packages -r requirements.txt
RUN chmod -R +x /usr/local/bin/tools/
RUN ln -s /usr/local/bin/tools/entrypoint.sh /usr/local/bin/entrypoint

ENTRYPOINT ["entrypoint"]

CMD ["tail", "-f", "/var/log/logger.log"]
