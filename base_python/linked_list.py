from typing import Any


class ObjList:

    def __init__(self, data: Any) -> None:
        self.__prev = None
        self.__next = None
        self.__data = data

    def set_next(self, obj) -> None:
        self.__next = obj

    def set_prev(self, obj):
        self.__prev = obj

    def get_next(self):
        return self.__next

    def get_prev(self):
        return self.__prev

    def set_data(self, data):
        self.__data = data

    def get_data(self):
        return self.__data

    def __str__(self):
        return self.__data


class LinkedList:
    __slots__ = ("head", "tail")

    def __init__(self):
        self.head = None
        self.tail = None

    def add_obj(self, obj: ObjList):
        if not self.head:
            self.head, self.tail = obj, obj
        else:
            self.tail.set_next(obj)
            obj.set_prev(self.tail)
            self.tail = obj

    def remove_obj(self) -> None:
        if self.tail is None:
            return

        self.tail = self.tail.get_prev()
        if self.tail is not None:
            self.tail.set_next(None)
        else:
            self.head = None

    def get_data(self):
        data = []
        current: ObjList = self.head
        while current is not None:
            data.append(current.get_data())
            current = current.get_next()
        return data

    def is_empty(self):
        return not bool(self.head)

    def __str__(self):
        return str(self.get_data())


lst = LinkedList()

obj_1 = ObjList("Данные 1")
obj_1.set_data("Данные УДАЛЕНО")
lst.add_obj(obj_1)
lst.add_obj(ObjList("Данные 2"))
lst.add_obj(ObjList("Данные 3"))
# print(obj_1.get_next())
# print(lst)
# print(lst.head)
# print(lst.tail)
# lst.remove_obj()
# print(f"list head: {lst.head}, list tail: {lst.tail}")

print(obj_1.get_next().get_next().get_next())