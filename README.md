# zfs-snapshot

Python 3 script to create a new zfs snapshot and delete old ones.

Arguments

- pool - zfs pool name
- --create (-c) - Create new snapshot on execution
- --auto (-a) - Only create new snapshot if most fresh is too old
- --silent (-s) - Silent operation (for cron jobs)
- --maxage - define maximum age of snapshot, default = 7
