#!/bin/sh


DISK_NUM=10
DISK_SIZE=$((32*1024)) #KB

DISKS_BASE=./disks

mkdir -p $DISKS_BASE
for i in `seq 0 $((DISK_NUM-1))`
do
    DISK_NAME="disk_$i"
    if [ ! -f $DISK_NAME ]; then
        echo create disk : $DISK_NAME
        dd if=/dev/zero of=$DISKS_BASE/$DISK_NAME bs=1024 count=$DISK_SIZE
        #dd if=/dev/zero bs=1024 count=$DISK_SIZE | tr '\000' '\377' > $DISK_NAME
    else
       echo disk $DISK_NAME exists
    fi
done
