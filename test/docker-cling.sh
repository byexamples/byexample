#!/bin/bash
docker run --rm -it -v "$(pwd):/mnt" -w /mnt eldipa/cling cling "$@"
