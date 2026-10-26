

def positions(repo, ids) -> list[tuple[str, int]]:
    """Заголовки и позиции элементов, отсортированные по позиции."""
    items = [repo.items[item_id] for item_id in ids]
    return [(item.title, item.position) for item in sorted(items, key=lambda item: item.position)]