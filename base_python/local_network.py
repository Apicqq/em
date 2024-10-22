from abc import ABC, abstractmethod
from dataclasses import dataclass
from random import randint
from typing import Any, Optional

IP_GENERATION_MAX_RETRIES = 10
CANNOT_SET_ATTRIBUTE_MANUALLY = "Cannot set attribute {} manually."


class IpAddressGenerationError(Exception):
    """Exception raised if IP-address could not be generated."""

    def __init__(self):
        super().__init__("Could not generate an IP-address. Please try again.")


class InvalidDataException(Exception):
    """Exception raised if incoming data type is invalid."""

    def __init__(self, expected_type, actual_type):
        super().__init__(
            f"Expected an instance of {expected_type}, got {actual_type}."
        )


def _validate_server(server: "Server") -> None:
    """
    Validate if incoming object is an instance of Server.

    :param server: Server to validate.
    :raises InvalidDataException: If the given
     server is not an instance of Server.
    """
    if not isinstance(server, Server):
        raise InvalidDataException("Server", type(server))


class Device(ABC):
    """
    Abstract base class which represents a device in a network.

    This class provides a basic implementation of a device,
    including data sending capabilities.
    """

    __slots__ = ("_buffer",)

    def __init__(self):
        self._buffer = []

    @property
    def buffer(self) -> list:
        """Get the buffer of currently holding packages."""
        return self._buffer

    @buffer.setter
    def buffer(self, data: list) -> None:
        """Manual setting of the buffer is prohibited."""
        raise RuntimeError(CANNOT_SET_ATTRIBUTE_MANUALLY.format("buffer"))

    @abstractmethod
    def send_data(self, **kwargs) -> None:
        """Abstract method that sends data to destination."""
        raise NotImplementedError(
            "You must implement that method in child class."
        )

    def __repr__(self) -> str:
        if type(self) == Router:
            return (
                f"{type(self).__name__} with {len(self.linked_servers)}"
                f" linked servers and "
                f"{len(self.buffer)} packages in buffer."
            )
        return (
            f"{type(self).__name__} with IP: {self.ip}. Currently"
            f" holding {len(self.buffer)} packages in buffer."
        )


class Server(Device):
    """Class that represents a Server, that can exchange data with Router."""

    __assigned_ips = set()

    __slots__ = ("_connected_to", "_ip")

    def __init__(self):
        super().__init__()
        self._connected_to: Optional[Router] = None
        self._ip = self.generate_ip()

    def generate_ip(self) -> int:
        """
        Generate a unique IP address.

        This is done for the device by randomly selecting a number
        between 1 and 255 until a unique address is found.

        :raises IpAddressGenerationError: if IP-address could not be generated.
        :returns: unique IP-address.
        """
        tries = 0
        while tries < IP_GENERATION_MAX_RETRIES:
            res = randint(1, 255)
            if res not in self.__assigned_ips:
                self.__assigned_ips.add(res)
                return res
            tries += 1
        raise IpAddressGenerationError()

    @property
    def ip(self) -> int:
        """Get device's IP-address."""
        return self._ip

    @ip.setter
    def ip(self, ip: int) -> None:
        """Manual setting of the IP-address is prohibited."""
        raise RuntimeError(CANNOT_SET_ATTRIBUTE_MANUALLY.format("ip"))

    @property
    def connected_to(self) -> "Router":
        """Get device's connected router."""
        return self._connected_to

    @connected_to.setter
    def connected_to(self, router: "Router") -> None:
        """Manual setting of the connected router is prohibited."""
        raise RuntimeError(
            CANNOT_SET_ATTRIBUTE_MANUALLY.format("connected_to")
        )

    def send_data(self, data: "Data") -> None:
        """
        Send the given data to the connected router.

        :param data: Data to send.
        :raises InvalidDataException: If the given
         data is not an instance of Data.
        """
        if not isinstance(data, Data):
            raise InvalidDataException("Data", type(data))
        self._connected_to.buffer.append(data)

    def get_data(self) -> list:
        """Return list of accepted Data packages and clears the buffer."""
        buffer = self.buffer.copy()
        self.buffer.clear()
        return buffer


class Router(Device):
    """Class that represents a Router, that can exchange data with Servers."""

    __slots__ = ("_linked_servers",)

    def __init__(self):
        super().__init__()
        self._linked_servers = set()

    @property
    def linked_servers(self) -> set:
        """Get set of currently linked servers to router."""
        return self._linked_servers

    @linked_servers.setter
    def linked_servers(self, servers: set) -> None:
        """Manual setting of the linked servers is prohibited."""
        raise RuntimeError(
            CANNOT_SET_ATTRIBUTE_MANUALLY.format("linked_servers")
        )

    def link(self, server: Server) -> None:
        """
        Link a Server to current router.

        :param server: Server to link to.
        :raises RuntimeError: If server is already linked to another router.
        :raises InvalidDataException: If the given
         server is not an instance of Server.
        """
        _validate_server(server)
        if server.connected_to is not None:
            raise RuntimeError("Server is already linked to another router.")
        self.linked_servers.add(server)
        server._connected_to = self

    def unlink(self, server: Server) -> None:
        """
        Remove link to a Server from current router.

        :param server: Server to unlink.
        :raises InvalidDataException: If the given
         server is not an instance of Server.
        :raises RuntimeError: If server is not linked to any router.
        """
        _validate_server(server)
        if not server.connected_to:
            raise RuntimeError("Server is not linked to router.")
        self.linked_servers.discard(server)
        server._connected_to = None

    def send_data(self) -> None:
        """
        Send all packages from buffer to dedicated servers.

        Clears buffer after all packages were sent.
        """
        for package in self.buffer:
            for server in self._linked_servers:
                if server.ip == package.ip:
                    server.buffer.append(package)
        self._buffer.clear()


@dataclass(slots=True)
class Data:
    """Class that represents data that can be sent to another device."""

    data: Any
    ip: int

    def __repr__(self):
        return f"Data(data: {self.data}, ip_to: {self.ip})"


if __name__ == "__main__":
    _router = Router()
    sv_from = Server()
    sv_to = Server()
    sv_from2 = Server()
    _router.link(sv_from)
    _router.link(sv_from2)
    _router.link(sv_to)
    sv_from.send_data(Data("Hello", sv_to.ip))
    sv_from2.send_data(Data("World", sv_to.ip))
    sv_to.send_data(Data("Hi!", sv_from.ip))
    _router.send_data()
    sv_3 = Server()
    print(sv_to.get_data())
    print(sv_to)
