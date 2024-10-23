from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from random import randint
from typing import Any, Optional, Union

IP_GENERATION_MAX_RETRIES = 10


class DeviceType(Enum):
    """Enum class for device types."""

    SERVER = auto()
    ROUTER = auto()


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


class Device(ABC):
    """
    Abstract base class which represents a device in a network.

    This class provides a basic implementation of a device,
    including data sending capabilities.
    """

    __slots__ = ("_buffer",)

    def __init__(self):
        self._buffer = []

    @classmethod
    def _validate_device(
        cls, device_type: DeviceType, device: Union["Device", "Router"]
    ) -> None:
        """
        Validate if incoming device is of correct type.

        :param device: device to validate.
        :param device_type: against which class device is being validated.
        :raises InvalidDataException: If the given
         device is not an instance of appropriate class.
        """
        match device_type:
            case DeviceType.SERVER:
                if not isinstance(device, Server):
                    raise InvalidDataException(Server, type(device))
            case DeviceType.ROUTER:
                if not isinstance(device, Router):
                    raise InvalidDataException(Router, type(device))
            case _:
                raise ValueError(f"Invalid caller: {device_type}.")

    @property
    def buffer(self) -> list:
        """Read-only method to get the buffer of currently holding packages."""
        return self._buffer

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
        self._ip = self._generate_ip()

    def _generate_ip(self) -> int:
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
        """Read-only method to get device's IP-address."""
        return self._ip

    @property
    def connected_to(self) -> "Router":
        """Method to get device's connected router."""
        return self._connected_to

    @connected_to.setter
    def connected_to(self, router: "Router") -> None:
        """Set device's connected router."""
        self._validate_device(DeviceType.ROUTER, router)
        self._connected_to = router

    def send_data(self, data: "Data") -> None:
        """
        Send the given data to the connected router.

        :param data: Data to send.
        :raises InvalidDataException: If the given
         data is not an instance of Data.
        """
        if not isinstance(data, Data):
            raise InvalidDataException("Data", type(data))
        self.connected_to.buffer.append(data)

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
        """Read-only method to get set of linked servers to router."""
        return self._linked_servers

    def link(self, server: Server) -> None:
        """
        Link a Server to current router.

        :param server: Server to link to.
        :raises RuntimeError: If server is already linked to another router.
        :raises InvalidDataException: If the given
         server is not an instance of Server.
        """
        self._validate_device(DeviceType.SERVER, server)
        if server.connected_to is not None:
            raise RuntimeError("Server is already linked to another router.")
        self.linked_servers.add(server)
        server.connected_to = self

    def unlink(self, server: Server) -> None:
        """
        Remove link to a Server from current router.

        :param server: Server to unlink.
        :raises InvalidDataException: If the given
         server is not an instance of Server.
        :raises RuntimeError: If server is not linked to any router.
        """
        self._validate_device(DeviceType.SERVER, server)
        if not server.connected_to:
            raise RuntimeError("Server is not linked to router.")
        self.linked_servers.discard(server)
        server.connected_to = None

    def send_data(self) -> None:
        """
        Send all packages from buffer to dedicated servers.

        Clears buffer after all packages were sent.
        """
        for package in self.buffer:
            for server in self.linked_servers:
                if server.ip == package.ip:
                    server.buffer.append(package)
        self.buffer.clear()


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
