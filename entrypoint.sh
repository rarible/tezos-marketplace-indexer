#!/bin/sh
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <ENV> <TYPE> <CONFIG_HASURA>" >&2
  exit 1
fi

if [ -z "$1" ]
  then
    echo "No ENV supplied"
fi

if [ -z "$2" ]
  then
    echo "No TYPE supplied"
fi

if [ "$3" = "true" ]
  then
    dipdup hasura configure --force
fi

dipdup -c dipdup.yml -c dipdup."$1"."$2".yml run
