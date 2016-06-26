#!/usr/bin/python3

from subprocess import check_output
from os import linesep
from datetime import datetime, date, time
from argparse import ArgumentParser
import fcntl, sys
# Get command line args
par = ArgumentParser()
par.add_argument("pool", help="Name of the pool to run on")
par.add_argument("-c", "--create", dest="create", action="store_true", help="Automatically create snapshots")
par.add_argument("-a", "--auto", dest="auto", action="store_true", help="Automatically create snapshots only when needed")
par.add_argument("-s", "--silent", dest="silent", action="store_true", help="Do not print anything")
par.add_argument("--maxage", dest="maxage", default=7, help="Maximum snapshot age in days, destroy older than this")
par.add_argument("list", type=str, nargs='+', help="List of zfs datasets to snapshot")
args = par.parse_args()
file_handle = None
lockfile_path = '/var/lock/zfssnapshot3.py'

def filelock(file_path):
    global file_handle
    file_handle = open(file_path, 'w')
    try:
        fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        return True


def vprint(*text):
    """
    :param text: Text string to print if no -s set
    :type text: str
    """
    if not args.silent:
        print(*text)

# Declare some vars
timeStamp = datetime.now()  # Record timestamp used for snapshotting
zpoolName = args.pool       # Main zpool name
newest = 99                 # Used to estimate the age of last snapshot
maxAge = args.maxage        # Maximum age of snapshot
sets = dict.fromkeys(args.list, 0)

if filelock(lockfile_path):
    print("Another instance is already running")
    sys.exit(-1)

# Get list of current snapshots
zfsList = check_output(["/sbin/zfs", "list", "-o", "name", "-t", "snapshot", "-H"]).decode().split(linesep)
# Clear screen and set cursors in 0,0
vprint("\033[2J\033[1;1H")
vprint("Current ZFS snapshots:")
# Create count of snapshots
for name in zfsList:
    if len(name) > 18:      # there may be a flaw as it may be a snapshot of fs not in 'sets'
        if name.strip(zpoolName)[1:][:-18] in sets:
            sets[name.strip(zpoolName)[1:][:-18]] += 1
            vprint("   ", sets[name.strip(zpoolName)[1:][:-18]], ":   ", name)
        else:
            print("Error, dataset: ", name, " doesn't match", zpoolName)
            sys.exit(1)
    else:
        zfsList.remove(name)
# Check snapshots time and if too old add to queue leaving at least one
setToDestroy = []
for zfsFileSystems in zfsList:
    snapshotTime = datetime.strptime(zfsFileSystems[-17:], '%Y-%m-%d_%H%M%S')
    name = zfsFileSystems.strip(zpoolName)[1:][:-18]
    timeLeap = int((timeStamp - snapshotTime).days)
    if name in sets:
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
        check_output(["/sbin/zfs", "snapshot", newname])
# If there are any snapshots in the queue to destroy
if len(setToDestroy) > 0:
    vprint("\n\033[33mSnapshots to be destroyed:")
    for name in setToDestroy:
        vprint("   ", name, "...")
        check_output(["/sbin/zfs", "destroy", name])
vprint("\033[0m")    # Set terminal back to normal
