"""Tileset view widget with grid overlay."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QImage, QPainter, QPen, QColor, QBrush,
    QDragEnterEvent, QDropEvent, QMouseEvent, QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QWidget,
)

from ..models import Tileset, GridSettings
from ..utils import SUPPORTED_FORMATS


class TilesetView(QGraphicsView):
    """Widget for displaying and interacting with a tileset image."""

    # Signals
    tile_selected = Signal(int)  # Emits tile index when clicked
    file_dropped = Signal(str)  # Emits file path when dropped

    # Grid colors
    GRID_COLOR = QColor(255, 0, 255, 180)  # Magenta
    SELECTION_COLOR = QColor(0, 255, 255, 200)  # Cyan
    SELECTION_FILL = QColor(0, 255, 255, 50)
    DUPLICATE_COLOR = QColor(255, 200, 0, 180)  # Orange for duplicates
    DUPLICATE_FILL = QColor(255, 200, 0, 30)
    LABELED_OVERLAY = QColor(0, 0, 0, 150)  # Semi-transparent black for labeled tiles

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Setup scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Image item
        self._image_item: Optional[QGraphicsPixmapItem] = None

        # Grid overlay items
        self._grid_lines: list = []
        self._selection_rects: list[QGraphicsRectItem] = []  # Multiple for duplicates
        self._labeled_overlays: list[QGraphicsRectItem] = []  # Overlays for labeled tiles

        # State
        self._tileset: Optional[Tileset] = None
        self._show_grid = True
        self._hide_labeled = False  # Toggle to grey out labeled tiles

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Show placeholder text
        self._update_placeholder()

    @property
    def tileset(self) -> Optional[Tileset]:
        """Get the current tileset."""
        return self._tileset

    @tileset.setter
    def tileset(self, value: Optional[Tileset]) -> None:
        """Set the tileset and update display."""
        self._tileset = value
        self._update_display()

    @property
    def show_grid(self) -> bool:
        """Get whether grid is visible."""
        return self._show_grid

    @show_grid.setter
    def show_grid(self, value: bool) -> None:
        """Set grid visibility."""
        self._show_grid = value
        self._update_grid_visibility()

    @property
    def hide_labeled(self) -> bool:
        """Get whether labeled tiles are hidden (greyed out)."""
        return self._hide_labeled

    @hide_labeled.setter
    def hide_labeled(self, value: bool) -> None:
        """Set whether to hide (grey out) labeled tiles."""
        self._hide_labeled = value
        self._update_labeled_overlays()

    def set_image(self, image: QImage) -> None:
        """Set the tileset image directly."""
        if self._tileset is None:
            return
        self._tileset.image = image
        self._update_display()

    def update_grid(self) -> None:
        """Update the grid overlay after settings change."""
        if self._tileset:
            self._tileset.regenerate_tiles()
        self._draw_grid()
        self._update_selection()
        self._update_labeled_overlays()

    def refresh_overlays(self) -> None:
        """Refresh the labeled overlays (call after tile naming changes)."""
        self._update_labeled_overlays()

    def _update_display(self) -> None:
        """Update the entire display."""
        self._scene.clear()
        self._image_item = None
        self._grid_lines = []
        self._selection_rects = []
        self._labeled_overlays = []

        if self._tileset is None or self._tileset.image is None:
            self._update_placeholder()
            return

        # Add image
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap.fromImage(self._tileset.image)
        self._image_item = self._scene.addPixmap(pixmap)
        self._image_item.setZValue(0)

        # Set scene rect
        self._scene.setSceneRect(self._image_item.boundingRect())

        # Draw grid
        self._draw_grid()

        # Draw labeled overlays
        self._update_labeled_overlays()

        # Fit in view
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _update_placeholder(self) -> None:
        """Show placeholder text when no image is loaded."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont

        text = self._scene.addText("Drop a tileset image here")
        text.setDefaultTextColor(QColor(150, 150, 150))
        font = QFont()
        font.setPointSize(14)
        text.setFont(font)

        # Center the text
        rect = text.boundingRect()
        text.setPos(-rect.width() / 2, -rect.height() / 2)

    def _draw_grid(self) -> None:
        """Draw the grid overlay."""
        # Remove old grid lines
        for item in self._grid_lines:
            self._scene.removeItem(item)
        self._grid_lines = []

        if self._tileset is None or self._tileset.image is None:
            return

        if not self._show_grid:
            return

        gs = self._tileset.grid_settings
        img = self._tileset.image

        pen = QPen(self.GRID_COLOR)
        pen.setWidth(1)
        pen.setCosmetic(True)  # Always 1 pixel regardless of zoom

        # Draw vertical lines
        x = gs.offset_x
        while x <= img.width():
            line = self._scene.addLine(x, 0, x, img.height(), pen)
            line.setZValue(1)
            self._grid_lines.append(line)

            # Move to next tile boundary
            x += gs.tile_width
            if x <= img.width():
                # Add separator line if there's a gap
                if gs.separator_x > 0:
                    sep_line = self._scene.addLine(x, 0, x, img.height(), pen)
                    sep_line.setZValue(1)
                    self._grid_lines.append(sep_line)
                x += gs.separator_x

        # Draw horizontal lines
        y = gs.offset_y
        while y <= img.height():
            line = self._scene.addLine(0, y, img.width(), y, pen)
            line.setZValue(1)
            self._grid_lines.append(line)

            y += gs.tile_height
            if y <= img.height():
                if gs.separator_y > 0:
                    sep_line = self._scene.addLine(0, y, img.width(), y, pen)
                    sep_line.setZValue(1)
                    self._grid_lines.append(sep_line)
                y += gs.separator_y

    def _update_grid_visibility(self) -> None:
        """Update visibility of grid lines."""
        for item in self._grid_lines:
            item.setVisible(self._show_grid)

    def _update_labeled_overlays(self) -> None:
        """Update overlays that grey out labeled tiles."""
        # Remove old overlays
        for item in self._labeled_overlays:
            self._scene.removeItem(item)
        self._labeled_overlays = []

        if self._tileset is None or not self._hide_labeled:
            return

        # Create overlay for each labeled tile
        brush = QBrush(self.LABELED_OVERLAY)
        pen = QPen(Qt.PenStyle.NoPen)

        for tile in self._tileset.tiles:
            if tile.is_labeled:
                overlay = self._scene.addRect(
                    tile.pixel_x, tile.pixel_y,
                    tile.width, tile.height,
                    pen, brush
                )
                overlay.setZValue(1.5)  # Above image, below selection
                self._labeled_overlays.append(overlay)

    def _update_selection(self) -> None:
        """Update the selection highlight (including duplicates)."""
        # Remove old selection rects
        for item in self._selection_rects:
            self._scene.removeItem(item)
        self._selection_rects = []

        if self._tileset is None:
            return

        tile = self._tileset.selected_tile
        if tile is None:
            return

        # Get all selected indices (including duplicates)
        selected_indices = self._tileset.selected_tile_indices
        primary_index = self._tileset.selected_tile_index

        for idx in selected_indices:
            t = self._tileset.tiles[idx]

            # Use different colors for primary vs duplicate selections
            if idx == primary_index:
                pen = QPen(self.SELECTION_COLOR)
                brush = QBrush(self.SELECTION_FILL)
            else:
                pen = QPen(self.DUPLICATE_COLOR)
                brush = QBrush(self.DUPLICATE_FILL)

            pen.setWidth(2)
            pen.setCosmetic(True)

            rect = self._scene.addRect(
                t.pixel_x, t.pixel_y,
                t.width, t.height,
                pen, brush
            )
            rect.setZValue(2)
            self._selection_rects.append(rect)

    def select_tile(self, index: int) -> None:
        """Select a tile by index."""
        if self._tileset is None:
            return

        if 0 <= index < len(self._tileset.tiles):
            self._tileset.selected_tile_index = index
            self._update_selection()

    # Event handlers

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click for tile selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we should select a tile
            if self._tileset and self._tileset.image:
                # Map to scene coordinates
                scene_pos = self.mapToScene(event.pos())

                # Check if within image bounds (use boundingRect, not contains,
                # so transparent pixels are still clickable)
                if self._image_item and self._image_item.boundingRect().contains(scene_pos):
                    # Try to select tile
                    index = self._tileset.select_tile_at_position(
                        int(scene_pos.x()),
                        int(scene_pos.y())
                    )
                    if index is not None:
                        self._update_selection()
                        self.tile_selected.emit(index)
                        return

        # Fall through to default behavior (panning)
        super().mousePressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter for file drops."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                ext = Path(path).suffix.lower().lstrip(".")
                if ext in SUPPORTED_FORMATS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move."""
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drop."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                self.file_dropped.emit(path)
                event.acceptProposedAction()
                return
        event.ignore()

    def reset_zoom(self) -> None:
        """Reset zoom to fit the image in view."""
        if self._tileset and self._tileset.image:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_to_actual(self) -> None:
        """Zoom to 100% (1:1 pixel)."""
        self.resetTransform()
