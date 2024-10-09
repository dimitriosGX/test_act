#!/bin/bash

./compress.sh
python3 bot_api.py --bot_address $1 --bot_port $2 --token $3