#!/usr/bin/bash -x

sudo mkdir -p /mnt/shared
sudo mount -t ntfs-3g /dev/sdb2 /mnt/shared
sudo chown "${USER}:${USER}" /mnt/shared
ln -s /mnt/shared
