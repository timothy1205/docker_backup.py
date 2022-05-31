#!/usr/bin/python3

import sys
import docker_backup

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Enter directory for backups")

    PATH = sys.argv[1]

    docker_backup.MySQLBackup(PATH).execute()
    docker_backup.JellyfinBackup(PATH).execute()
    docker_backup.RadarrBackup(PATH).execute()
    docker_backup.SonarrBackup(PATH).execute()
    docker_backup.GrocyBackup(PATH).execute()
    docker_backup.DuplicatiBackup(PATH).execute()
