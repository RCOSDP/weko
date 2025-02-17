FROM golang:1.16

ENV NOTIFY_LDN_INBOX_DB_PATH=/opt/data/ldn_inbox.sqlite
ENV NOTIFY_LDN_INBOX_HOST=127.0.0.1
ENV NOTIFY_LDN_INBOX_DEBUG=true
ENV NOTIFY_LDN_INBOX_PORT=8000

WORKDIR /go/src/app
RUN mkdir -p /opt/data

ADD inbox .
ADD go.mod .
ADD README.md .

RUN go get -d -v ./...
RUN go install -v ./...

ADD ./keys/server.crt /etc/inbox_sin/server.crt
ADD ./keys/server.key /etc/inbox_sin/server.key

#CMD ["sh", "-c", "notify_ldn_inbox -db=$NOTIFY_LDN_INBOX_DB_PATH -host=https://$NOTIFY_LDN_INBOX_HOST -port=$NOTIFY_LDN_INBOX_PORT -debug=$NOTIFY_LDN_INBOX_DEBUG"]
CMD ["sh", "-c", "notify_ldn_inbox"]