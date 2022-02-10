## COAR Notify Test Inbox

This utility allows developers to post Linked Data Notifications and inspect the payload as received. Notifications are stored temporarily - you should have plenty of time to inspect the payload but no long-term persistence should be assumed.

### Posting LDNs to the inbox
JSON-LD payloads should be posted to the LDN inbox here (https://ldninbox.antleaf.com/inbox). The following example uses Curl as the HTTP client and a local JSON-LD file containing the payload to be posted:

```bash
curl -s -o /dev/null -D - -X POST -H "Content-Type: application/ld+json" -d @<JSON-FILE-NAME> https://ldninbox.antleaf.com/inbox
```

### Viewing the inbox and inspecting payloads and their metadata

#### Browser view
You can inspect the results of the posted payload by pointing your web browser at the same URL:

[https://ldninbox.antleaf.com/inbox](https://ldninbox.antleaf.com/inbox)

Here you will find links to inspect metadata and payloads in JSON-LD, N-Quads and Turtle formats

#### Machine-readable view
You can retrieve the inbox in JSON-LD format as follows:
```bash
curl -H "Accept: application/ld+json" https://ldninbox.antleaf.com/inbox
```

### Getting Notifications directly
The URL for a given notification uses a generated UUID, in the form:

https://ldninbox.antleaf.com/inbox/<NOTIFICATION_UUID>

With a browser, this URL will give you a comprehensive view of the notification, its metadata and its payload in various formats.

To retrieve this notification's payload in machine-readable form, just issue a GET with the appropriate `Accept` header. Supported formats *(MIME Types) are:

* application/ld+json
* application/json
* text/turtle
* application/n-quads

For example:
```bash
curl -H "Accept: application/ld+json" <NOTIFICATION_URL>
```

### About this system
This system has been successfully tested (as an *LDN Receiver*) with the W3C-supplied test suite for LDN:

[https://linkedresearch.org/ldn/tests/](https://linkedresearch.org/ldn/tests/)

[Source code for this system is available](https://github.com/antleaf/coar_notify_inbox).