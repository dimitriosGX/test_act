#!/bin/bash

zip -r src.zip . -x "*.zip" > /dev/null 2>&1
if [ -f src.zip ]; then
    echo "Operation successful"
else
    echo "Error: Operation failed"
    exit 1
fi