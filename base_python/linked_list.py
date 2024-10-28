from dataclasses import dataclass, field
from typing import Any, Optional


class InvalidObjectException(Exception):
    """Exception raised if incoming object is invalid."""

    def __init__(self, expected_type, actual_type):
        super().__init__(
            f"Expected an instance of {expected_type}, got {actual_type}."
        )


def _check_obj(obj: "ObjList") -> None:
    """Check if the object is an instance of ObjList."""
    if not isinstance(obj, ObjList):
        raise InvalidObjectException(ObjList, type(obj))


@dataclass(slots=True)
class ObjList:
    """ObjList class, that represents an object in a linked list."""

    __data: Any
    __next: Optional["ObjList"] = field(default=None)
    __prev: Optional["ObjList"] = field(default=None)

    @property
    def next(self) -> Optional["ObjList"]:
        """Get the next object in the list."""
        return self.__next

    @next.setter
    def next(self, obj: "ObjList") -> None:
        """Set the next object in the list."""
        _check_obj(obj)
        self.__next = obj

    @property
    def prev(self) -> Optional["ObjList"]:
        """Get the previous object in the list."""
        return self.__prev

    @prev.setter
    def prev(self, obj: "ObjList") -> None:
        """Set the previous object in the list."""
        _check_obj(obj)
        self.__prev = obj

    @property
    def data(self) -> Any:
        """Get object's data."""
        return self.__data

    @data.setter
    def data(self, data: Any) -> None:
        """Set the data of the object."""
        self.__data = data

    def __str__(self):
        return self.__data

    def __repr__(self):
        return (
            f"ObjList({self.__data}. Next: {self.__next},"
            f" Prev: {self.__prev})"
        )


class LinkedList:
    """Double-linked list implementation."""

    __slots__ = ("head", "tail")

    def __init__(self) -> None:
        self.head: Optional[ObjList] = None
        self.tail: Optional[ObjList] = None

    def add_obj(self, obj: ObjList) -> None:
        """Add an object to the end of the list."""
        _check_obj(obj)
        if not self.head:
            self.head = obj
            self.tail = obj
        else:
            if self.tail is not None:
                self.tail.next = obj
                obj.prev = self.tail
                self.tail = obj

    def remove_obj(self) -> None:
        """Remove an object from the end of the list."""
        if self.tail is None:
            return
        self.tail = self.tail.prev
        if self.tail is not None:
            self.tail.next = None
        else:
            self.head = None

    def get_data(self) -> list[Any]:
        """Get list's content."""
        data = []
        current: Optional[ObjList] = self.head
        while current is not None:
            data.append(current.data)
            current = current.next
        return data

    def __str__(self):
        return str(self.get_data())

    def __repr__(self):
        return (
            f"LinkedList({self.get_data()}."
            f" Head: {self.head}, Tail: {self.tail})"
        )


if __name__ == "__main__":
    lst = LinkedList()

    lst.add_obj(ObjList("Really secret data"))
    lst.add_obj(ObjList("Not so secret data"))
    lst.add_obj(ObjList("This data is totally not secret"))

    res = lst.get_data()
    print(res)
