from typing import Any, Iterable, Optional

import ipaddress
import os
import subprocess

import yaml

from fabric import Connection, GroupResult, ThreadingGroup
from rich.console import Console
from rich.panel import Panel
from rich import box

CONSOLE = Console()


def print_err(msg: Any) -> None:
    """Prints an error message in a red box to the console."""
    if LOGLEVEL.CURRENT >= LOGLEVEL.ERR_SUCCESS:
        CONSOLE.print(Panel(msg, title="Error", style="bold red", box=box.HEAVY))


def print_warn(msg: Any) -> None:
    """Prints a warning message in a yellow box to the console."""
    if LOGLEVEL.CURRENT >= LOGLEVEL.WARN:
        CONSOLE.print(Panel(msg, title="Warning", style="yellow", box=box.SQUARE))


def print_success(msg: Any) -> None:
    """Prints a success message in a green box to the console."""
    if LOGLEVEL.CURRENT >= LOGLEVEL.ERR_SUCCESS:
        CONSOLE.print(Panel(msg, title="Success", style="green", box=box.SQUARE))


def print_info(msg: Any) -> None:
    """Prints an info message to the console."""
    if LOGLEVEL.CURRENT >= LOGLEVEL.INFO:
        CONSOLE.log(msg, style="")


def print_debug(msg: Any) -> None:
    """Prints a debug message to the console."""
    if LOGLEVEL.CURRENT >= LOGLEVEL.DEBUG:
        CONSOLE.log(msg, style="dim")


def print_bit_bot() -> None:
    """Prints the Bit-Bots logo to the console using cat."""
    path = os.path.join(os.path.dirname(__file__), "bitbot.ans")
    subprocess.run(["cat", path])


class LOGLEVEL:
    ERR_SUCCESS = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    CURRENT = 2

def be_quiet() -> bool:
    """
    Returns whether to be quiet or not.

    :return: True if the current loglevel is below INFO, False otherwise.
    """
    return LOGLEVEL.CURRENT <= LOGLEVEL.INFO


# Read the known targets
_known_targets_path: str = os.path.join(os.path.dirname(__file__), "known_targets.yaml")
try:
    with open(_known_targets_path, "r") as f:
        KNOWN_TARGETS: dict[str, dict[str, str]] = yaml.safe_load(f)
except FileNotFoundError:
    print_err(f"Could not find known_targets.yaml in {_known_targets_path}")
    exit(1)


class Target:
    hostname: str
    ip: Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]

    def __init__(self, identifier: str) -> None:
        """
        Target represents a robot to deploy to.
        It can be initialized with a hostname, IP address or a robot name.
        """
        self.hostname, self.ip = self._identify_target(identifier)

    def _identify_target(self, identifier: str) -> tuple[str, Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]]:
        """
        Identifies a target from an identifier.
        The identifier can be a hostname, IP address or a robot name.

        :param identifier: The identifier to identify the target from.
        :return: A tuple containing the hostname and the IP address of the target.
        """
        print_debug(f"Identifying target from identifier: {identifier}")

        identified_target: Optional[str] = None  # The hostname of the identified target

        # Iterate over the known targets
        for hostname, values in KNOWN_TARGETS.items():
            print_debug(f"Checking if {identifier} is {hostname}")

            # Is the identifier a known hostname?
            print_debug(f"Comparing {identifier} with {hostname}")
            if hostname == identifier:
                identified_target = hostname
                break

            # Is the identifier a known robot name?
            print_debug(f"Comparing {identifier} with {values['robot_name']}") if "robot_name" in values else None
            if values.get("robot_name") == identifier:
                identified_target = hostname
                break

            # Is the identifier a known IP address?
            identifier_ip = None
            try:
                identifier_ip = ipaddress.ip_address(identifier)
            except ValueError:
                print_debug(f"Checking if {identifier} is a IP address")

            if "ip" in values:
                try:
                    known_target_ip = ipaddress.ip_address(values["ip"])
                except ValueError:
                    print_warn(f"Invalid IP address ('{values['ip']}') defined for known target: {hostname}")
                    exit(1)

                if identifier_ip is not None and identifier_ip == known_target_ip:
                    identified_target = hostname
                    break

        # If no target was identified, exit
        if identified_target is None:
            print_err(f"Could not find a known target for the given identifier: {identifier}")
            exit(1)

        print_debug(f"Found {identified_target} as known target")

        identified_ip = None
        if "ip" in KNOWN_TARGETS[identified_target]:
            try:
                identified_ip = ipaddress.ip_address(KNOWN_TARGETS[identified_target]["ip"])
            except ValueError:
                print_err(f"Invalid IP address defined for known target: {identified_target}")
                exit(1)

        return (identified_target, identified_ip)


    def __str__(self) -> str:
        """Returns the target's hostname if available or IP-address."""
        return self.hostname if self.hostname is not None else str(self.ip)

def _get_connections(
    hosts: list[str],
    user: str,
    connection_timeout: Optional[int] = 10
    ) -> ThreadingGroup:
    """
    Helper function for getting connections from hosts using the given username.
    Checks the new connections for success and returns them.

    :param hosts: The hosts to connect to
    :param user: The username to connect with
    :param connection_timeout: Timeout for establishing the connection
    """
    try:
        connections = ThreadingGroup(
            hosts,
            user=user,
            connect_timeout=connection_timeout
        )
        for connection in connections:
            connection.open()
    except Exception as e:
        print_err(f"Could not establish all required connections: {e}")
        exit(1)
    return connections

def get_connections_from_targets(
    targets: list[Target],
    user: str,
    connection_timeout: Optional[int] = 10
) -> ThreadingGroup:
    """
    Get connections to the given Targets using the 'bitbots' username.

    :param targets: The Targets to connect to
    :param user: The username to connect with
    :param connection_timeout: Timeout for establishing the connection
    :return: The connections
    """
    return _get_connections(
        [str(target) for target in targets],
        user,
        connection_timeout
    )


class ThreadingGroupFromSucceeded(ThreadingGroup):
    """
    ThreadingGroupFromSucceeded is a Group that only contains the succeeded hosts from a GroupResult.
    """
    def __init__(self, results: GroupResult) -> None:
        """
        Creates a new GroupFromSucceeded from the given GroupResult.

        :param results: The GroupResult to get the succeeded hosts from
        """
        succeeded_connection: Iterable[Connection] = results.succeeded.keys()
        return ThreadingGroup.from_connections(succeeded_connection)
