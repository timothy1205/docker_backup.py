#!/usr/bin/python3
# pylint: disable=missing-module-docstring

import sys
import docker_backup

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Missing arguments!")
        print("Usage: main.py <backup_dir> <max_days>")
        sys.exit(1)

    PATH = sys.argv[1]
    MAX_DAYS = int(sys.argv[2])

    if MAX_DAYS < 1:
        print("<max_days> must be a positive non-zero integer!")
        sys.exit(1)

    docker_backup.MySQLBackup(PATH).execute()
    docker_backup.JellyfinBackup(PATH).execute()
    docker_backup.RadarrBackup(PATH).execute()
    docker_backup.SonarrBackup(PATH).execute()
    docker_backup.GrocyBackup(PATH).execute()
    docker_backup.DuplicatiBackup(PATH).execute()

    docker_backup.delete_old_backups(PATH, MAX_DAYS)
