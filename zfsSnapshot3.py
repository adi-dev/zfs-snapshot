#!/usr/bin/python3

from subprocess import check_output
from os import linesep
from datetime import datetime, date, time
from argparse import ArgumentParser
# Get command line args
par = ArgumentParser()
par.add_argument("-c", "--create", dest="create", action="store_true", help="Automatically create snapshots")
par.add_argument("-a", "--auto", dest="auto", action="store_true", help="Automatically create snapshots only when needed")
par.add_argument("-s", "--silent", dest="silent", action="store_true", help="Do not print anything")
par.add_argument("list", type=str, nargs='+', help="List of zfs volumes to snapshot")
args = par.parse_args()


def vprint(*text):
    """
    :param text: Text string to print if no -s set
    :type text: str
    """
    if not args.silent:
        print(*text)

# Declare some vars
timeStamp = datetime.now()  # Record timestamp used for snapshotting
zpoolName = "tank"          # Main zpool name
newest = 99                 # Used to estimate the age of last snapshot
maxAge = 7                  # Maximum age of snapshot
if not args.list:
    vprint("\nError:\n\tList of zfs snapshot not given")
    exit()
sets = dict.fromkeys(args.list, 0)

# Get list of current snapshots
zfsList = check_output(["zfs", "list", "-o", "name", "-t", "snapshot", "-H"]).decode().split(linesep)
# Clear screen and set cursors in 0,0
vprint("\033[2J\033[1;1H")
vprint("Current ZFS snapshots:")
# Create count of snapshots
for name in zfsList:
    if len(name) > 18:      # there may be a flaw as it may be a snapshot of fs not in 'sets'
        sets[name.strip(zpoolName)[1:][:-18]] += 1
        vprint("   ", sets[name.strip(zpoolName)[1:][:-18]], ":   ", name)
    else:
        zfsList.remove(name)
# Check snapshots time and if too old add to queue leaving at least one
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
    vprint("\n\033[34mSnapshot required, newest snapshot is", newest, "days old\033[37m")
else:
    vprint("\n\033[32mNo snapshot required\033[37m")
if args.create or args.silent or (args.auto and newest > 0):
    result = "y"
else:
    if args.auto:
        result = "n"
    else:
        result = input("\nCreate snapshots? ")
if result == "y":
    vprint("\033[34mSnapshotting")
    for names in sets:
        newname = "tank/" + names + "@" + timeStamp.strftime('%Y-%m-%d_%H%M%S')
        vprint("   ", newname)
        check_output(["zfs", "snapshot", newname])
# If there are any snapshots in the queue to destroy
if len(setToDestroy) > 0:
    vprint("\n\033[33mSnapshots to be destroyed:")
    for name in setToDestroy:
        vprint("   ", name, "...")
        check_output(["zfs", "destroy", name])
vprint("\033[0m")    # Set terminal back to normal
