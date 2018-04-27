#!/usr/bin/env bash

keys=$(echo $1THISISTHEEND | sed 's/+/Shift+/g')
keys=$(echo $keys | sed 's/\^/Control+/g')
keys=$(echo $keys | sed 's/#/Super_L+/g')
keys=$(echo $keys | sed 's/!/Alt_L+/g')
keys=$(echo $keys | sed 's/+THISISTHEEND//g')
keys=$(echo $keys | sed 's/THISISTHEEND//g')
echo "$keys"

