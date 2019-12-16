#!/bin/sh -e

# clean elasticsearch
curl -XDELETE localhost:9200/_template/* && curl -XDELETE localhost:9200/*

flask index init
flask queues declare

flask fixtures events
curl -XGET localhost:9200/*/_flush
flask fixtures aggregations
curl -XGET localhost:9200/*/_flush
