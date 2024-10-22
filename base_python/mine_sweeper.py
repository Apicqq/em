import random

INVALID_CELL_COORDINATES = "Invalid coordinates. Please try again."


class GameOverException(Exception):
    """Exception raises upon stepping on a mine."""


class CellAlreadyRevealedException(Exception):
    """Exception raises if desired cell is already revealed."""


class Cell:
    """Class which represents a cell in a Minesweeper field."""

    __slots__ = ("_mine", "_around_mines", "_is_open")

    def __init__(self, around_mines: int, mine: bool) -> None:
        self._mine = mine
        self._around_mines = around_mines
        self._is_open = False

    def __repr__(self) -> str:
        return (
            f"Cell(is_mine:"
            f" {self.mine},"
            f" around_mines: {self.around_mines},"
            f" is_open: {self.is_open})"
        )

    @property
    def mine(self) -> bool:
        """Property indicating whether the cell is a mine."""
        return self._mine

    @mine.setter
    def mine(self, value: bool) -> None:
        """Set whether the cell is a mine."""
        if not isinstance(value, bool):
            raise TypeError("mine must be a boolean value")
        self._mine = value

    @property
    def around_mines(self) -> int:
        """Read-only property indicating number of mines around the cell."""
        return self._around_mines

    @around_mines.setter
    def around_mines(self, value: int) -> None:
        """Set number of mines around the cell."""
        if not isinstance(value, int):
            raise TypeError("around_mines must be an integer value")
        self._around_mines = value

    @property
    def is_open(self) -> bool:
        """Read-only property indicating whether the cell is open."""
        return self._is_open


class GamePole:
    """Class which represents Minesweeper game."""

    __slots__ = ("_pole", "size", "mines_count")

    def __init__(self, size: int, mines_count: int) -> None:
        self.size = size
        self.mines_count = mines_count
        self._pole = self.generate_empty_field()
        self.generate_mines()

    def show(self) -> None:
        """Reveal the game field."""
        print("  ", end="")
        for i in range(len(self._pole[0])):
            print(i, end=" ")
        print()
        # to print cell position horizontally
        for i, row in enumerate(self._pole):
            print(i, end=" ")
            for cell in row:
                if cell.is_open:
                    if cell.mine:
                        print("*", end=" ")
                    else:
                        print(cell.around_mines, end=" ")
                else:
                    print("#", end=" ")
            print()

    @property
    def pole(self) -> list[list[Cell]]:
        """Read-only property representing the game field."""
        return self._pole

    def generate_empty_field(self) -> list[list[Cell]]:
        """Generate an empty game field."""
        return [
            [Cell(0, False) for _ in range(self.size)]
            for _ in range(self.size)
        ]

    def generate_mines(self) -> None:
        """Generate the game field with mines."""
        mines = random.sample(range(self.size**2), self.mines_count)
        for mine in mines:
            x_mine_pos, y_mine_pos = mine // self.size, mine % self.size
            self._pole[x_mine_pos][y_mine_pos].mine = True
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (
                        0 <= x_mine_pos + i < self.size
                        and 0 <= y_mine_pos + j < self.size
                    ):
                        self._pole[x_mine_pos + i][
                            y_mine_pos + j
                        ].around_mines += 1

    def reveal_cell(self, x_pos: int, y_pos: int) -> None:
        """Reveal the cell."""
        if 0 < x_pos >= self.size or 0 < y_pos >= self.size:
            raise ValueError(INVALID_CELL_COORDINATES)
        cell_to_be_revealed = self._pole[x_pos][y_pos]
        if (x_pos < 0 or x_pos >= self.size) or (
            y_pos < 0 or y_pos >= self.size
        ):
            raise ValueError(INVALID_CELL_COORDINATES)
        if cell_to_be_revealed.is_open:
            raise CellAlreadyRevealedException(
                "Cell is already revealed! Please try again."
            )
        cell_to_be_revealed._is_open = True
        if cell_to_be_revealed.mine:
            raise GameOverException("You stepped on a mine!")

    def play_game(self):
        """
        Play the game.

        Initially reveal fully covered field, then wait for an input
        and reveal the cell.
        If a cell is already revealed, raise an exception.
        If a mine is revealed, raise an exception and end the game.
        """
        self.show()
        while True:
            try:
                x, y = map(int, input("Enter coordinates: ").split())
            except ValueError:
                print(INVALID_CELL_COORDINATES)
                continue
            try:
                self.reveal_cell(x, y)
            except (ValueError, CellAlreadyRevealedException) as exception:
                print(exception.args[0])
            except GameOverException as exception:
                print("Game over!", exception.args[0])
                break
            self.show()


if __name__ == "__main__":
    pole = GamePole(10, 12)
    pole.play_game()
