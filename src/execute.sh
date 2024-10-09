#!/bin/bash

$ACTION_PATH/src/compress.sh
echo $1
echo $2
echo $3
python3 $ACTION_PATH/src/bot_api.py --bot_address $1 --bot_port $2 --token $3