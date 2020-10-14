ssh-eygen rsa 

openssl pkcs8 -topk8 -in mykey.pem -nocrypt | sed ':a;N;$!ba;s/\n/\\r\\n/g'
openssl pkcs8 -topk8 -in mykey.pem -nocrypt | openssl pkey -pubout | sed ':a;N;$!ba;s/\n/\\r\\n/g'

