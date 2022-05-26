"""
Provides backup solutions for various types of containers
"""

import docker
import gzip
import os
import datetime

def merge_keywords(keywords, custom_keywords):
    if custom_keywords is None:
        return keywords
    if keywords is None:
        return custom_keywords

    print(keywords, custom_keywords)
    return keywords + custom_keywords

def parse_env(container):
    unparsed_env = container.exec_run("env") \
        .output.decode("utf-8") \
        .split("\n")

    parsed = {}
    for pair in unparsed_env:
        pair_s = pair.split("=")

        if len(pair_s) != 2:
            continue

        parsed[pair_s[0]] = pair_s[1]

    return parsed

def format_file_path(backup_dir: str, name: str, extension: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(backup_dir, f'{name}_{now}.{extension}')

def write_compressed_file(path, data):
    compressed_data = gzip.compress(data)

    with open(path, 'wb') as file:
        file.write(compressed_data)

    print(f'Wrote file: {path}')


class BackupStrategy: # pylint: disable=too-few-public-methods
    """
    Abstract backup strategy
    """
    def __init__(self, backup_dir: str, keywords=None):
        self.containers = docker.from_env().containers.list()
        self.backup_dir = backup_dir

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        self.__filter_containers(keywords)



    def __filter_containers(self, keywords):
        def __helper(container):
            for k in keywords:
                if k in container.name:
                    return True
            return False

        self.containers = list(filter(__helper, self.containers))

    def execute(self):
        """
        Execute backup solution
        """
        raise NotImplementedError()

class MySQLBackup(BackupStrategy): # pylint: disable=too-few-public-methods
    """
    MySQL/MariaDB backups
    """
    keywords = ["mysql", "mariadb"]

    def __init__(self, backup_dir: str,keywords=None):
        super().__init__(
            backup_dir, merge_keywords(self.keywords, keywords)
        )


    def execute(self):
        for container in self.containers:
            env = parse_env(container)
            output = container.exec_run(
                f'/usr/bin/mysqldump ' \
                f'{env.get("MYSQL_DATABASE")} -u root -p{env.get("MYSQL_ROOT_PASSWORD")}'
            ).output

            path = format_file_path(self.backup_dir,
                                    f'{container.name}_{env.get("MYSQL_DATABASE")}',
                                    'sql.gz')
            write_compressed_file(path, output)
