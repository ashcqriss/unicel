"""Image Viewer / inline image renderer.

When Pillow is available the image is downscaled and drawn with an ASCII
brightness ramp — which works on every profile including grayscale E-Ink and
needs no truecolour support. Without Pillow it shows file metadata and how to
enable inline previews. Pillow is an *optional* dependency, in keeping with the
zero-required-dependency core.
"""

from __future__ import annotations

import curses
from pathlib import Path
from typing import Any

from ..widgets import truncate
from .base import AppPane

# Dark -> light ramp; index by scaled brightness.
_RAMP = " .:-=+*#%@"

try:  # optional dependency
    from PIL import Image  # type: ignore
    _HAS_PIL = True
except Exception:  # noqa: BLE001
    Image = None  # type: ignore
    _HAS_PIL = False


class ImageApp(AppPane):
    app_name = "image"
    app_label = "Image Viewer"

    def __init__(self, pane_id: int = 0, context: Any = None, path: str | None = None):
        super().__init__(pane_id, context)
        self.path = Path(path).expanduser() if path else None
        self.error = ""

    def header_title(self, focused: bool) -> str:
        name = self.path.name if self.path else "no image"
        return f"Image — {truncate(name, 40)}"

    def status_hint(self) -> str:
        return "open via: image <path>"

    def _render_ascii(self, surface, focused: bool) -> bool:
        if not (_HAS_PIL and self.path and self.path.exists()):
            return False
        try:
            img = Image.open(self.path).convert("L")
        except Exception as exc:  # noqa: BLE001
            self.error = f"cannot open image: {exc}"
            return False
        # Cells are ~2x taller than wide; compress vertical accordingly.
        target_w = max(1, surface.width)
        target_h = max(1, surface.height - 1)
        ratio = img.height / img.width if img.width else 1
        draw_w = target_w
        draw_h = max(1, min(target_h, int(target_w * ratio * 0.5)))
        img = img.resize((draw_w, draw_h))
        pixels = img.load()
        surface.text(0, 0, f"{self.path.name}  {img.width}x{img.height} (ascii)", role="dim")
        for y in range(draw_h):
            if 1 + y >= surface.height:
                break
            row_chars = []
            for x in range(draw_w):
                value = pixels[x, y]
                row_chars.append(_RAMP[min(len(_RAMP) - 1, value * len(_RAMP) // 256)])
            surface.text(1 + y, 0, "".join(row_chars), role="text")
        return True

    def render_body(self, surface, focused: bool) -> None:
        if self.path is None:
            surface.text(0, 0, "No image loaded.", role="dim")
            surface.text(1, 0, "Open one with:  image <path>", role="dim")
            return
        if not self.path.exists():
            surface.text(0, 0, f"not found: {self.path}", role="error")
            return
        if self._render_ascii(surface, focused):
            return
        # Metadata fallback
        try:
            size = self.path.stat().st_size
        except OSError:
            size = 0
        surface.text(0, 0, truncate(str(self.path), surface.width), role="accent")
        surface.text(2, 0, f"size: {size} bytes", role="text")
        surface.text(3, 0, f"type: {self.path.suffix.lstrip('.').upper() or 'unknown'}", role="text")
        if self.error:
            surface.text(5, 0, truncate(self.error, surface.width), role="error")
        if not _HAS_PIL:
            surface.text(surface.height - 2, 0,
                         "Inline preview needs Pillow:  pip install pillow", role="dim")
