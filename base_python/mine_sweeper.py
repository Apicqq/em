import random

INVALID_CELL_COORDINATES = "Invalid coordinates. Please try again."


class GameOverException(Exception):
    """Exception raises upon stepping on a mine."""


class CellAlreadyRevealedException(Exception):
    """Exception raises if desired cell is already revealed."""


class Cell:
    """Class which represents a cell in a Minesweeper field."""

    def __init__(self, around_mines: int, mine: bool) -> None:
        self.mine = mine
        self.around_mines = around_mines
        self.is_open = False

    def __str__(self):
        return (
            f"Cell(is_mine:"
            f" {self.mine},"
            f" around_mines: {self.around_mines},"
            f" is_open: {self.is_open})"
        )


class GamePole:
    """Class which represents Minesweeper game."""

    def __init__(self, size: int, mines_count: int) -> None:
        self.size = size
        self.mines_count = mines_count
        self.pole = self.generate_empty_field()
        self.generate_mines()

    def show(self) -> None:
        """Reveal the game field."""
        for row in self.pole:
            for cell in row:
                if cell.is_open:
                    if cell.mine:
                        print("*", end=" ")
                    else:
                        print(cell.around_mines, end=" ")
                else:
                    print("#", end=" ")
            print()

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
            self.pole[x_mine_pos][y_mine_pos].mine = True
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (
                        0 <= x_mine_pos + i < self.size
                        and 0 <= y_mine_pos + j < self.size
                    ):
                        self.pole[x_mine_pos + i][
                            y_mine_pos + j
                        ].around_mines += 1

    def reveal_cell(self, x_axis: int, y_axis: int):
        """Reveal the cell."""
        if 0 < x_axis >= self.size or 0 < y_axis >= self.size:
            raise ValueError(INVALID_CELL_COORDINATES)
        cell_to_be_revealed = self.pole[x_axis][y_axis]
        if (x_axis < 0 or x_axis >= self.size) or (
            y_axis < 0 or y_axis >= self.size
        ):
            raise ValueError(INVALID_CELL_COORDINATES)
        if cell_to_be_revealed.is_open:
            raise CellAlreadyRevealedException(
                "Cell is already revealed! Please try again."
            )
        cell_to_be_revealed.is_open = True
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
