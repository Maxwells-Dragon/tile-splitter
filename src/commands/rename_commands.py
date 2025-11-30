"""Undo/Redo commands for rename operations."""

from PySide6.QtGui import QUndoCommand

from ..models import Tile, Tileset


class RenameDuplicatesCommand(QUndoCommand):
    """Command to rename a tile and all its duplicates."""

    def __init__(
        self,
        tileset: Tileset,
        tile: Tile,
        new_name: str,
        parent=None,
    ):
        super().__init__(parent)
        self._tileset = tileset
        self._tile = tile
        self._new_name = new_name

        # Store old names for all duplicates
        self._duplicates = tileset.get_duplicate_tiles(tile)
        self._old_names = [t.custom_name for t in self._duplicates]

        self.setText(f"Rename tile to '{new_name}'")

    def redo(self) -> None:
        """Apply the rename to all duplicates."""
        for t in self._duplicates:
            t.name = self._new_name

    def undo(self) -> None:
        """Revert the rename for all duplicates."""
        for t, old_name in zip(self._duplicates, self._old_names):
            t.custom_name = old_name

    def id(self) -> int:
        return 1001

    def mergeWith(self, other) -> bool:
        if not isinstance(other, RenameDuplicatesCommand):
            return False
        if other._tile is not self._tile:
            return False
        self._new_name = other._new_name
        self.setText(f"Rename tile to '{self._new_name}'")
        return True


class RenameSetCommand(QUndoCommand):
    """Command to rename the tileset folder."""

    def __init__(
        self,
        tileset: Tileset,
        new_name: str,
        parent: QUndoCommand = None,
    ):
        super().__init__(parent)
        self._tileset = tileset
        self._new_name = new_name
        self._old_name = tileset.set_name

        self.setText(f"Rename set '{self._old_name}' to '{self._new_name}'")

    def redo(self) -> None:
        """Apply the rename."""
        self._tileset.set_name = self._new_name

    def undo(self) -> None:
        """Revert the rename."""
        self._tileset.set_name = self._old_name

    def id(self) -> int:
        """Return command ID for merging."""
        return 1002

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive renames of the same tileset."""
        if not isinstance(other, RenameSetCommand):
            return False

        if other._tileset is not self._tileset:
            return False

        self._new_name = other._new_name
        self.setText(f"Rename set to '{self._new_name}'")
        return True
