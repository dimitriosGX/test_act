#!/bin/bash

$ACTION_PATH/src/compress.sh
pip3 run python $ACTION_PATH/src/bot_api.py --bot_address $1 --bot_port $2 --token $3