#!/bin/sh -e

curl -XDELETE localhost:9200/_template/* && curl -XDELETE localhost:9200/*
flask queues delete
