#!/bin/bash

$ACTION_PATH/src/compress.sh
python3 $ACTION_PATH/src/bot_api.py --bot_address $1 --bot_port $2 --token $3