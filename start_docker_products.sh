#!/usr/bin/bash
make dbrm
make db
docker run --rm -it --network=host products:1.0
