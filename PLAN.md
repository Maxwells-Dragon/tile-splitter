# Tile Splitter - Implementation Plan

## Overview
A PySide6 desktop GUI application for breaking tileset images into individual labeled tiles for ML training dataset curation.

## Core Features

### 1. Main Window Layout
- **Left Panel**: Tileset preview with toggleable grid overlay
- **Right Panel**: Selected tile preview + name editor
- **Top Toolbar**: Grid settings, output folder, set name
- **Status Bar**: License info with warning icons

### 2. Tileset Display (Left Panel)
- Drag-and-drop image loading
- Supports: PNG, JPG, GIF, BMP, WEBP
- Toggleable grid overlay
- Configurable:
  - Tile width (pixels)
  - Tile height (pixels)
  - Horizontal separator (pixels)
  - Vertical separator (pixels)
  - X offset (pixels)
  - Y offset (pixels)
- Click any grid cell to select that tile
- Visual highlight on selected tile
- Zoom and pan support (QGraphicsView built-in)

### 3. Tile Editor (Right Panel)
- Shows selected tile at larger scale
- Editable text field for tile name
- Default name: `{x}_{y}` (zero-indexed)
- Live preview of final filename

### 4. Naming & Organization
- Set name field (folder name for this tileset)
- Default: `tileset_{i}` where i is next available in output folder
- Output parent folder selector (persists across sessions)
- Name collision handling: append `_1`, `_2`, etc.

### 5. Undo/Redo System
- QUndoStack for all naming operations
- Ctrl+Z / Ctrl+Y bindings
- Tracks:
  - Individual tile renames
  - Set name changes

### 6. Licensing System
- Attempt to read from source image metadata (EXIF, PNG text chunks, XMP)
- Manual URL input to fetch license from web page
- Manual text input as fallback
- Display current license in status bar
- Warning icons for problematic licenses:
  - NC (Non-Commercial) - yellow warning
  - ND (No Derivatives) - red warning
  - Other restrictions detected
- Tooltip explains the problem

### 7. Export
- Preview list of all tiles with names before export
- User approval required before any files created
- Export format: same as source (default) or user-selected
- For each tile:
  - Save image file with license embedded in metadata
  - Track for LICENSE.json
- Create LICENSE.json in set folder:
```json
{
  "sources": [
    {
      "source_file": "original_tileset.png",
      "license": "CC BY 4.0",
      "license_url": "https://...",
      "author": "...",
      "tiles": ["0_0.png", "1_0.png", "..."]
    }
  ]
}
```

### 8. Session Persistence (QSettings)
- Output parent folder
- Window size/position
- Last used grid settings
- Recent files list
- Last used export format

## File Structure
```
tile_splitter/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── app.py                  # QApplication setup
│   ├── main_window.py          # Main window widget
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── tileset_view.py     # Left panel - QGraphicsView for tileset
│   │   ├── tile_editor.py      # Right panel - selected tile + name
│   │   ├── grid_settings.py    # Grid configuration controls
│   │   ├── license_display.py  # License status bar widget
│   │   └── export_dialog.py    # Export preview/approval dialog
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tileset.py          # Tileset data model
│   │   ├── tile.py             # Individual tile data
│   │   └── license_info.py     # License data model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_loader.py     # Load images, extract metadata
│   │   ├── license_extractor.py # Extract/fetch license info
│   │   ├── tile_exporter.py    # Export tiles with metadata
│   │   └── settings_manager.py # QSettings wrapper
│   ├── commands/
│   │   ├── __init__.py
│   │   └── rename_commands.py  # QUndoCommand subclasses
│   └── utils/
│       ├── __init__.py
│       ├── image_formats.py    # Supported formats, metadata handling
│       └── name_collision.py   # Collision resolution logic
├── tests/
│   └── __init__.py
├── requirements.txt
├── README.md
├── .gitignore
└── pyproject.toml
```

## Supported Image Formats
- PNG (preferred for pixel art)
- JPG/JPEG
- GIF
- BMP
- WEBP

## Dependencies
- PySide6 (GUI framework)
- Pillow (image metadata extraction/writing)
- requests (fetching license from URLs)

## TODO (Future - Not Implemented)
- [ ] Partial tile handling at edges
- [ ] Batch tile selection/naming
- [ ] Auto-detect grid from image analysis
- [ ] Auto-suggested names (ML-based)
- [ ] Flask/React web interface
- [ ] Cloud storage integration (Google Drive, etc.)
- [ ] Authentication system

## Implementation Order
1. Project scaffolding + dependencies
2. Basic main window layout
3. Image loading with drag-and-drop
4. Grid overlay rendering
5. Tile selection + preview
6. Naming system with defaults
7. Undo/redo stack
8. Settings persistence
9. License extraction from metadata
10. License URL fetching
11. License warnings
12. Export dialog with preview
13. Export with metadata embedding
14. LICENSE.json generation
15. Name collision handling
16. Polish and testing
