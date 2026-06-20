#!/usr/bin/bash -x

echo "Check script content..."

# First, get the UUID of your NTFS partition
# sudo blkid /dev/sdb2

# Edit fstab
# sudo nano /etc/fstab

# Add this line (replace UUID with your actual UUID):
# UUID=your-uuid-here /mnt/shared ntfs-3g defaults,uid=1000,gid=1000,umask=022 0 0

# Test the fstab entry
# sudo mount -a
