#!/usr/bin/env bash
lsof -i :6767 | tail --lines=+2 | cut -d' ' -f3-3 | uniq | xargs kill -9
