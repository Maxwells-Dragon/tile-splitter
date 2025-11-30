# Tile Splitter

A desktop GUI application for splitting tileset images into individual labeled tiles, designed for curating ML training datasets for game tileset generation.

## Features

- **Drag-and-drop** tileset image loading
- **Configurable grid** overlay with tile size and separator settings
- **Click-to-select** tiles with individual naming
- **License management** - extracts from metadata, fetches from URLs, warns about restrictive licenses
- **Undo/Redo** support for naming operations
- **Batch export** with approval workflow
- **Persistent settings** across sessions

## Supported Formats

- PNG (recommended for pixel art)
- JPG/JPEG
- GIF
- BMP
- WEBP

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd tile_splitter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python -m src.main
```

1. Drag a tileset image onto the left panel
2. Configure the grid settings (tile size, separators)
3. Click tiles to select and name them
4. Set the output folder and tileset name
5. Add license information if not auto-detected
6. Click Export and approve the file list

## License Output

Each exported tileset folder contains:
- Individual tile images with license metadata embedded
- `LICENSE.json` tracking source files and their licenses

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT License
