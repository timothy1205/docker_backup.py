"""
Provides backup solutions for various types of containers
"""
import abc
import gzip
import os
import datetime
import docker
from docker.models.containers import Container

def merge_keywords(keywords: list[str] | None, custom_keywords: list[str] | None):
    """
    Merge keywords lists or return other if one is None
    """
    if custom_keywords is None:
        return keywords
    if keywords is None:
        return custom_keywords

    return keywords + custom_keywords

def parse_env(container: Container):
    """
    Return dict of parsed envars for container
    """
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
    """
    Append ISO8601 timestamp to given name/extension at backup_dir
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(backup_dir, f'{name}_{now}.{extension}')

def write_compressed_file(path: str, data: bytes):
    """
    Compress and write data to path
    """
    compressed_data = gzip.compress(data)

    with open(path, 'wb') as file:
        file.write(compressed_data)

    print(f'Wrote file: {path}')


class BackupStrategy(metaclass=abc.ABCMeta): # pylint: disable=too-few-public-methods
    """
    Abstract backup strategy
    """
    def __init__(self, backup_dir: str, keywords=None):
        self.containers = docker.from_env().containers.list()
        self.backup_dir = backup_dir

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        self.__filter_containers(keywords)

    def __filter_containers(self, keywords: list[str]):
        def __helper(container: Container):
            for k in keywords:
                if k in container.name:
                    return True
            return False

        self.containers = list(filter(__helper, self.containers))

    @abc.abstractmethod
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
            print()


class SQLiteGeneric(BackupStrategy, metaclass=abc.ABCMeta): # pylint: disable=too-few-public-methods
    """
    Generic SQLite backup to provide method for individual database files
    """
    def backup_database(self, container: Container, path: str):
        """
        Backup sqlite db file at path of container
        """
        output = container.exec_run(
            f'/usr/bin/sqlite3 {path} .dump'
        ).output

        file_name = os.path.basename(path)
        if "." in file_name:
            file_name = file_name.split(".")[0]

        backup_path = format_file_path(self.backup_dir,
                                f'{container.name}_{file_name}',
                                'sql.gz')
        write_compressed_file(backup_path, output)


class JellyfinBackup(SQLiteGeneric):
    """
    Jellyfin (official) container backup
    """
    keywords = ["jellyfin"]
    db_path = "/config/data"
    db_ext = "db"

    def __init__(self, backup_dir: str,keywords=None):
        super().__init__(
            backup_dir, merge_keywords(self.keywords, keywords)
        )

    def execute(self):
        ls_path = os.path.join(self.db_path, f"*.{self.db_ext}")
        for container in self.containers:
            ls_result = container.exec_run(f'bash -c "ls {ls_path}"')
            ls_output = ls_result.output.decode("utf-8").strip()
            if ls_result.exit_code != 0:
                print(f"ls failed with exit code {ls_result.exit_code}: {ls_output}")
                return

            for path in ls_output.split("\n"):
                self.backup_database(container, path)
