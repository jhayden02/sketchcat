# sketchcat
A kitty terminal sketchpad kitten.

## Prerequisites

- [Kitty terminal emulator](https://sw.kovidgoyal.net/kitty/)
- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Pillow (PIL) library (installed automatically by uv)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BlinkDynamo/sketchcat.git
cd sketchcat
```

2. Install dependencies and symlink the kitten:
```bash
make install
```

This will use uv to sync dependencies and create a symlink
in your kitty config directory.

## Uninstallation

```bash
make uninstall
```

## Usage

If your installation was successful, you may now use
sketchcat in any kitty terminal.
```bash
kitty +kitten sketchcat.py
```

If typing this out everytime feels clunky to you, you
can map a keybind in your `kitty.conf` to launch sketchcat.
```
map ctrl+shift+d kitten sketchcat.py
```

With this added, pressing `Ctrl+Shift+D` in any kitty terminal
will launch sketchcat.

## Controls
Sketchcat is very simple by design.

- **Left mouse button + drag**: Draw on the canvas
- **q**: Quit and return to terminal

## Configuration

Edit the `config` class in `sketchcat.py` to customize:

- `canvas_height`: Canvas height in pixels (default: 600)
- `brush_size`: Brush radius in pixels (default: 5)
- `brush_color`: RGBA brush color (default: white)
- `border_color`: RGBA border color (default: white)

Canvas width automatically adjusts to terminal width.

## License

GNU General Public License v3.0
