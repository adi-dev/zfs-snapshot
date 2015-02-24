#!/usr/bin/python3

from subprocess import check_output
from os import linesep
from datetime import datetime, date, time
# Declare some vars
timeStamp = datetime.now()  # Record timestamp used for snapshotting
zpoolName = "tank"          # Main zpool name
newest = 99                 # Used to estimate the age of last snapshot
maxAge = 7                  # Maximum age of snapshot
sets = {"adam": 0,"anna": 0,"mysql": 0,"owncloud": 0,"www": 0}  # List of filesystems to process
# Get list of current snapshots
zfsList = check_output(["zfs", "list", "-o", "name", "-t", "snapshot", "-H"]).decode().split(linesep)
# Clear screen and set cursos in 0,0
print("\033[2J\033[1;1H")
print("Current ZFS snapshots:")
# Create count of snapshots
for name in zfsList:
    if len(name) > 18:      # there may be a flaw as it may be a snapshot of fs not in 'sets'
        sets[name.strip(zpoolName)[1:][:-18]] += 1
        print("   ", sets[name.strip(zpoolName)[1:][:-18]], ":   ", name)
    else:
        zfsList.remove(name)
# Check snapshots time and if too old add to queque leaving at least one
setToDestroy = []
for zfsFileSystems in zfsList:
    snapshotTime = datetime.strptime(zfsFileSystems[-17:], '%Y-%m-%d_%H%M%S')
    name = zfsFileSystems.strip(zpoolName)[1:][:-18]
    timeLeap = int((timeStamp - snapshotTime).days)
    if sets[name] > 1:
        if timeLeap > maxAge:
            sets[name] -= 1
            setToDestroy.append(zfsFileSystems)
    newest = min(newest, timeLeap)
# If last snapshot date is older than one day make a new snapshots
if newest > 0:
    print("\n\033[34mSnapshot required, newest snapshot is",newest,"days old\033[37m")
else:
    print("\n\033[32mNo snapshot required\033[37m")
result = input("\nCreate snapshots? ")
if result == "y":
    print("\033[34m   Snapshotting")
    for names in sets:
        newname = "tank/" + names + "@" + timeStamp.strftime('%Y-%m-%d_%H%M%S')
        print("      ", newname)
        check_output(["zfs", "snapshot", newname])
# If there are any snapshots in the queue to destroy
if len(setToDestroy) > 0:
    print("\n\033[33mSnapshots to be destroyed:")
    for name in setToDestroy:
        print("  ", name, "...")
        check_output(["zfs", "destroy", name])
print("\033[0m") # Set terminal back to normal