from typing import Protocol, TypeVar

from app.domain.exceptions import InvalidPositionError


class Positioned(Protocol):
    position: int


T = TypeVar("T", bound=Positioned)


def make_room(siblings: list[T], position: int) -> list[T]:
    """Освобождает место под новый элемент: всех на position и дальше сдвигает на +1."""
    changed = [item for item in siblings if item.position >= position]
    for item in changed:
        item.position += 1
    return changed


def close_gap(siblings: list[T], position: int) -> list[T]:
    """Закрывает дырку после удаления: всех после position сдвигает на -1."""
    changed = [item for item in siblings if item.position > position]
    for item in changed:
        item.position -= 1
    return changed


def check_insert_position(siblings: list[T], position: int) -> None:
    """Новый элемент можно поставить на 1..N+1, где N — сколько элементов уже есть."""
    max_position = len(siblings) + 1
    if position > max_position:
        raise InvalidPositionError(f'Position must be between 1 and {max_position}.')


def move_position(siblings: list[T], old_position: int, new_position: int) -> list[T]:
    """Перемещает элемент со старой позиции на новую. siblings — соседи БЕЗ самого элемента."""
    before = {id(item): item.position for item in siblings}
    close_gap(siblings, old_position)
    make_room(siblings, new_position)
    return [item for item in siblings if item.position != before[id(item)]]




