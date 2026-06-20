"""Geometry primitives for the single-layer pane model.

The pane manager partitions the screen into non-overlapping rectangles. Keeping
this logic free of any curses dependency makes the layout engine unit-testable
in a headless environment (CI, tests) without a real terminal.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle in terminal cells.

    Coordinates follow curses conventions: ``y`` is the row (top is 0) and
    ``x`` is the column (left is 0). ``w``/``h`` are width/height in cells.
    """

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def area(self) -> int:
        return max(0, self.w) * max(0, self.h)

    def is_empty(self) -> bool:
        return self.w <= 0 or self.h <= 0

    def contains(self, y: int, x: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def inset(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> "Rect":
        """Shrink the rectangle by the given margins, clamped to non-negative size."""
        return Rect(
            x=self.x + left,
            y=self.y + top,
            w=max(0, self.w - left - right),
            h=max(0, self.h - top - bottom),
        )

    def split_h(self, weights: list[float], gap: int = 0) -> list["Rect"]:
        """Split horizontally (panes side by side) according to ``weights``.

        Any rounding remainder is added to the last cell so the children
        exactly tile the parent with no gaps or overlaps.
        """
        return self._split(weights, gap, horizontal=True)

    def split_v(self, weights: list[float], gap: int = 0) -> list["Rect"]:
        """Split vertically (panes stacked) according to ``weights``."""
        return self._split(weights, gap, horizontal=False)

    def _split(self, weights: list[float], gap: int, horizontal: bool) -> list["Rect"]:
        n = len(weights)
        if n == 0:
            return []
        total = float(sum(weights)) or 1.0
        extent = (self.w if horizontal else self.h) - gap * (n - 1)
        extent = max(0, extent)

        sizes: list[int] = []
        allocated = 0
        for i, weight in enumerate(weights):
            if i == n - 1:
                sizes.append(max(0, extent - allocated))
            else:
                size = int(extent * (weight / total))
                sizes.append(size)
                allocated += size

        rects: list[Rect] = []
        cursor = self.x if horizontal else self.y
        for size in sizes:
            if horizontal:
                rects.append(Rect(cursor, self.y, size, self.h))
            else:
                rects.append(Rect(self.x, cursor, self.w, size))
            cursor += size + gap
        return rects
