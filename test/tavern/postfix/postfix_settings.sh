#!/bin/bash

cp -f ./main.cf /etc/postfix/
cp -f ./recipient_access /etc/postfix/

postmap /etc/postfix/recipient_access

systemctl restart postfix

cat ./recipient_access | while read line
do
    if [[ "$line" == *"@example.org"* ]]; then
        ARR=(${line//@/ })
        id ${ARR[0]}
        if [ $? -ne 0 ]; then
            useradd ${ARR[0]} -s /sbin/nologin
        fi
    fi
done