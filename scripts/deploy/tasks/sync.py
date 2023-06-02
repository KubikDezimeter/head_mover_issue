from typing import List

import os
import subprocess
import sys

import yaml
from fabric import Connection, Result

from tasks.abstract_task import AbstractTask
from misc import *


class Sync(AbstractTask):
    def __init__(self, local_meta: str, package: str = '', pre_clean: bool = False) -> None:
        """
        Sync task that synchronizes (copies) the local source directory to the remote server.

        :param file_path: Path to the local Bit-Bots meta directory
        :param package: Limit to file from this package, if empty, all files are included
        :param pre_clean: Whether to clean the source directory before syncing
        """
        super().__init__()
        self._local_meta = local_meta
        self._package = package
        self._pre_clean = pre_clean

        self._includes = self._get_includes_from_file(
            os.path.join(self._local_meta, f"sync_includes_wolfgang_nuc.yaml"),
            self._package
        )


    def _get_includes_from_file(self, file_path: str, package: str = '') -> List[str]:
        """
        Retrieve a list of file to sync from and includes-file

        :param file_path: Path of the includes-file
        :param package: Limit to file from this package, if empty, all files are included
        :returns: List of files to sync
        """
        includes = list()
        with open(file_path) as file:
            data = yaml.safe_load(file)
            # Exclude files
            for entry in data['exclude']:
                includes.append(f'--include=- {entry}')
            # Include files
            for entry in data['include']:
                if isinstance(entry, dict):
                    for folder, subfolders in entry.items():
                        if package == '':
                            includes.append(f'--include=+ {folder}')
                            for subfolder in subfolders:
                                includes.append(f'--include=+ {folder}/{subfolder}')
                                includes.append(f'--include=+ {folder}/{subfolder}/**')
                        elif package in subfolders:
                            includes.append(f'--include=+ {folder}')
                            includes.append(f'--include=+ {folder}/{package}')
                            includes.append(f'--include=+ {folder}/{package}/**')
                elif isinstance(entry, str):
                    if package == '' or package == entry:
                        includes.append(f'--include=+ {entry}')
                        includes.append(f'--include=+ {entry}/**')
        includes.append('--include=- *')
        return includes


    def run(self, connection: Connection, target: Target) -> Result:
        """
        Synchronize (copy) the local source directory to the given Target using the rsync tool.

        :param connection: The connection to the remote server.
        :param target: The Target to synchronize the source directory to.
        :return: The result of the task.
        """
        if self._pre_clean and self._package:
            print_warn("Cleaning selected packages is not supported. Will clean all packages instead.")

        if self._pre_clean:
            print_debug("Cleaning source directory")
            clean_result = connection.run(f"rm -rf {target.workspace}/src && mkdir -p {target.workspace}/src")
            if not clean_result.ok:
                print_warn(f"Cleaning of source directory failed. Continuing anyways")

        cmd = [
            "rsync",
            "--checksum",
            "--archive",
            "--delete",
        ]

        if not should_run_quietly():
            cmd.append("--verbose")

        cmd.extend(self._includes)
        cmd.extend([os.path.join(self._local_meta, "/"),  f"bitbots@{target}:{target.workspace}/src/"])

        print_debug(f"Calling {' '.join(cmd)}")
        sync_result = subprocess.run(cmd)
        if sync_result.returncode != 0:
            print_err(f"Synchronizing task failed with error code {sync_result.returncode}")
            sys.exit(sync_result.returncode)
