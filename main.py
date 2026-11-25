#!/usr/bin/env python3
"""The World in One Day -- Tuesday 24 November 2026. (Upgraded build.)

Draws a newspaper front page summing up the world news of
24 November 2026 as a 1024x1024 PNG. Pure standard library:
the PNG writer below uses only zlib and struct, and every glyph
comes from a small 5x7 bitmap font defined in this file.

Six stories, each checked against the wires (Reuters / BBC / AP /
CNN / Al Jazeera) on 25 November 2026:
  1. Nvidia's board reinstates Jensen Huang as CEO, reversing
     itself days after ruling out his return, under pressure
     from President Trump; shares jump 31%, the best day since
     2003, adding almost $1 trillion in value; Nasdaq +6.4%.
  2. NATO sends an AWACS early-warning jet to Poland after three
     Russian Kh-101 cruise missiles landed there on Friday
     20 November; SACEUR authorised the deployment.
  3. Ukraine says seven sea drones sank the Russian corvette
     Merkury in the Libyan port of Benghazi, and hit the cargo
     ship Angara; a Ka-27 helicopter aboard was destroyed.
  4. COP31, the longest climate summit in history, ends in
     Antalya with no deal: the first COP to collapse since
     Copenhagen in 2009.
  5. Israeli strikes kill three in Gaza, including UNRWA worker
     Adel al-Helo, hit near a water well in Jabalia camp;
     Oxfam says 99% of Gaza is contaminated.
  6. Iran vows to use all its tools against a US naval blockade;
     Washington sanctions 22 entities and eight people in its
     shadow banks, and Trump threatens to sink ships that test it.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into the output directory. Deterministic:
two runs produce byte-identical output (no time, no random).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 232)
INK = (26, 26, 26)
NAVY = (20, 53, 92)
RED = (179, 38, 30)
GREEN = (31, 122, 74)
GOLD = (198, 138, 28)
BLUE = (43, 106, 160)
TEAL = (0, 120, 113)
ORANGE = (214, 110, 26)
GREY = (110, 108, 96)
CREAM = (233, 227, 210)
WHITE = (255, 255, 255)
SKY = (178, 210, 232)
SEA = (36, 90, 140)
SMOKE = (190, 186, 172)
BLIP = (120, 255, 140)

# ---------------------------------------------------------------- 5x7 font
# Seven rows of five cells per glyph; '#' is ink, '.' is blank.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}


def glyph_width(text, scale):
    """Pixel width of text at scale (each glyph is 6 units wide)."""
    return len(text) * 6 * scale - scale


def wrap_words(text, max_width, scale):
    """Greedy word wrap; returns lines that fit max_width."""
    out, current = [], ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if glyph_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            out.append(current)
            current = word
    if current:
        out.append(current)
    return out


# ------------------------------------------------------------------- canvas
class Page:
    """An RGB pixel buffer with tiny drawing helpers."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def dot(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def box(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.dot(xx, yy, color)

    def border(self, x, y, w, h, color, t=2):
        self.box(x, y, w, t, color)
        self.box(x, y + h - t, w, t, color)
        self.box(x, y, t, h, color)
        self.box(x + w - t, y, t, h, color)

    def hbar(self, x, y, length, color, t=1):
        self.box(x, y, length, t, color)

    def vbar(self, x, y, length, color, t=1):
        self.box(x, y, t, length, color)

    def segment(self, x0, y0, x1, y1, color, t=1):
        """Bresenham segment with a square brush of thickness t."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        half = t // 2
        while True:
            for oy in range(-half, half + 1):
                for ox in range(-half, half + 1):
                    self.dot(x + ox, y + oy, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.dot(xx, yy, color)
                elif abs(d2 - r * r) <= r:
                    self.dot(xx, yy, color)

    def poly(self, points, color):
        """Filled polygon via the even-odd scanline rule."""
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        n = len(points)
        for y in range(top, bottom + 1):
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if ay == by:
                    continue
                lo, hi = (ay, by) if ay < by else (by, ay)
                if lo <= y < hi:
                    xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.dot(x, y, color)

    def glyph(self, x, y, ch, scale, color):
        rows = GLYPHS.get(ch, GLYPHS["?"])
        for r in range(7):
            for c in range(5):
                if rows[r][c] == "1":
                    self.box(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color, align="left"):
        """Draw text; align left/center/right around x. Returns width."""
        s = s.upper()
        w = glyph_width(s, scale)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color)
            cx += 6 * scale
        return w

    def para(self, x, y, text, max_width, scale, color):
        """Wrapped paragraph; returns the y just past the last line."""
        for line in wrap_words(text, max_width, scale):
            self.text(x, y, line, scale, color)
            y += 9 * scale
        return y


# ------------------------------------------------------------- illustrations
def draw_chip(pg, x, y, s, body, pin):
    """A processor: square body, four pins a side, gold die."""
    pg.box(x, y, s, s, body)
    pg.border(x, y, s, s, INK, 3)
    for i in range(4):
        off = 10 + i * (s - 20) // 3
        pg.box(x + off, y - 7, 5, 7, pin)
        pg.box(x + off, y + s, 5, 7, pin)
        pg.box(x - 7, y + off, 7, 5, pin)
        pg.box(x + s, y + off, 7, 5, pin)
    inner = s * 2 // 5
    ix = x + (s - inner) // 2
    iy = y + (s - inner) // 2
    pg.box(ix, iy, inner, inner, pin)
    pg.border(ix, iy, inner, inner, INK, 2)


def draw_chart(pg, x, y, w, h, color):
    """Axes, a rising line with an arrowhead, and a +31% tag."""
    pg.hbar(x, y + h, w, INK, 2)
    pg.vbar(x, y, h, INK, 2)
    pts = [(x + 8, y + h - 10), (x + w // 4, y + h - 24),
           (x + w // 2, y + h - 16), (x + 3 * w // 4, y + h - 46),
           (x + w - 16, y + 12)]
    for a, b in zip(pts, pts[1:]):
        pg.segment(a[0], a[1], b[0], b[1], color, 4)
    ex, ey = pts[-1]
    pg.poly([(ex, ey), (ex - 15, ey - 3), (ex - 3, ey + 12)], color)
    pg.text(x + w - 112, y + h - 28, "+31%", 3, color)


def draw_radar(pg, cx, cy, r):
    """Radar scope: rings, cross, sweep, blips, and a jet above."""
    pg.disc(cx, cy, r, NAVY, fill=True)
    for frac in (1.0, 0.66, 0.33):
        pg.disc(cx, cy, int(r * frac), GREEN, fill=False)
    pg.hbar(cx - r, cy, 2 * r, GREEN, 1)
    pg.vbar(cx, cy - r, 2 * r, GREEN, 1)
    pg.segment(cx, cy, cx + int(r * 0.7), cy - int(r * 0.7), GREEN, 2)
    for bx, by, br in ((18, -24, 4), (-28, 14, 4), (32, 20, 3)):
        pg.disc(cx + bx, cy + by, br, BLIP, fill=True)
    # jet silhouette flying over the scope
    px, py = cx, cy - r - 22
    pg.poly([(px - 28, py + 6), (px - 8, py - 2), (px - 8, py + 8)], INK)
    pg.poly([(px + 28, py + 6), (px + 8, py - 2), (px + 8, py + 8)], INK)
    pg.box(px - 15, py - 2, 30, 6, INK)
    pg.poly([(px + 15, py), (px + 25, py - 2), (px + 25, py + 2)], INK)
    pg.box(px - 2, py + 8, 4, 9, INK)


def draw_ship(pg, x, y, w, h):
    """A corvette on the waves, a drone overhead, blast at the stern."""
    hull_y = y + h - 34
    pg.box(x + 8, hull_y, w - 30, 16, INK)
    pg.poly([(x + w - 22, hull_y), (x + w - 22, hull_y + 16),
             (x + w - 56, hull_y + 16)], INK)
    pg.box(x + 22, hull_y - 22, 10, 22, INK)          # mast
    pg.box(x + 16, hull_y - 28, 22, 6, INK)           # mast top
    pg.box(x + 52, hull_y - 12, 32, 12, INK)          # deck house
    for i in range(3):
        pg.hbar(x, y + h - 8 - i * 6, w, BLUE, 2)
    # blast starburst at the stern
    ex, ey = x + w - 16, hull_y - 6
    for ang in range(0, 360, 30):
        dx = int(17 * math.cos(math.radians(ang)))
        dy = int(17 * math.sin(math.radians(ang)))
        pg.segment(ex, ey, ex + dx, ey + dy, ORANGE, 3)
    pg.disc(ex, ey, 7, GOLD, fill=True)
    # quadcopter drone above the bow
    dx, dy = x + 16, y + 12
    pg.box(dx, dy, 20, 5, INK)
    pg.disc(dx + 2, dy, 5, INK, fill=False)
    pg.disc(dx + 18, dy, 5, INK, fill=False)
    pg.vbar(dx + 10, dy + 5, 6, INK, 2)


def draw_globe(pg, cx, cy, r):
    """A globe split by a jagged crack, stamped NO DEAL."""
    pg.disc(cx, cy, r, SKY, fill=True)
    pg.disc(cx, cy, r, BLUE, fill=False)
    pg.hbar(cx - r, cy, 2 * r, BLUE, 2)
    pg.hbar(cx - int(r * 0.87), cy - r // 2, int(r * 1.74), BLUE, 2)
    pg.hbar(cx - int(r * 0.87), cy + r // 2, int(r * 1.74), BLUE, 2)
    pg.vbar(cx, cy - r, 2 * r, BLUE, 2)
    pts = [(cx - 5, cy - r), (cx + 7, cy - r // 2), (cx - 7, cy),
           (cx + 7, cy + r // 2), (cx - 3, cy + r)]
    for a, b in zip(pts, pts[1:]):
        pg.segment(a[0], a[1], b[0], b[1], RED, 4)
    pg.text(cx - 34, cy + r + 8, "NO DEAL", 2, RED)


def draw_skyline(pg, x, y, w, h):
    """City blocks with a column of smoke curling up."""
    base = y + h - 10
    pg.box(x, base - 44, 30, 44, GREY)
    pg.box(x + 38, base - 62, 26, 62, INK)
    pg.box(x + 72, base - 32, 34, 32, GREY)
    pg.box(x + 114, base - 52, 24, 52, INK)
    pg.vbar(x + 38 + 13, base - 78, 16, INK, 2)
    for sx, sy, sr in ((x + 42, y + 10, 9), (x + 54, y, 11), (x + 68, y - 10, 13)):
        pg.disc(sx, sy, sr, SMOKE, fill=True)
    pg.hbar(x, base, w, INK, 2)


def draw_tanker(pg, x, y, w, h):
    """An oil tanker halted behind a red-and-white blockade barrier."""
    hull_y = y + h - 30
    pg.box(x + 6, hull_y, w - 12, 14, RED)
    pg.box(x + w - 46, hull_y - 22, 30, 22, INK)
    pg.box(x + 14, hull_y - 16, 38, 16, INK)
    pg.disc(x + 30, hull_y + 7, 4, GOLD, fill=True)
    pg.disc(x + 46, hull_y + 7, 4, GOLD, fill=True)
    for i in range(3):
        pg.hbar(x, y + h - 8 - i * 6, w, SEA, 2)
    # blockade barrier across the top of the panel
    pg.box(x, y + 6, w, 12, RED)
    for i in range(0, w, 16):
        pg.box(x + i, y + 6, 8, 12, WHITE)
    pg.vbar(x + 8, y + 18, 10, INK, 3)
    pg.vbar(x + w - 8, y + 18, 10, INK, 3)


# -------------------------------------------------------------------- page
def draw_page():
    pg = Page(W, H, PAPER)

    # ---- masthead
    pg.box(0, 0, W, 128, NAVY)
    pg.text(W // 2, 22, "THE WORLD IN ONE DAY", 5, WHITE, align="center")
    pg.text(W // 2, 88, "TUESDAY, 24 NOVEMBER 2026", 2, GOLD, align="center")
    pg.text(W // 2, 110, "SIX STORIES FROM A DAY THAT SHOOK THE WORLD",
            1, GOLD, align="center")
    pg.hbar(0, 128, W, RED, 6)

    # ---- lead story: Nvidia / Huang
    lx, ly, lw, lh = 24, 148, 604, 320
    pg.border(lx, ly, lw, lh, INK, 3)
    pg.text(lx + 20, ly + 16, "BUSINESS  *  TECHNOLOGY", 1, RED)
    pg.text(lx + 20, ly + 44, "HUANG IS BACK", 6, INK)
    pg.text(lx + 20, ly + 96, "NVIDIA REINSTATES ITS CHIEF", 3, NAVY)
    pg.para(lx + 20, ly + 138,
            "Jensen Huang returns as chief executive after the board "
            "reverses itself under pressure from President Trump, days "
            "after ruling out his comeback. Nvidia shares jump 31% in "
            "a day, adding almost $1 trillion in value.",
            lw - 40, 2, INK)
    draw_chip(pg, lx + 36, ly + 240, 60, NAVY, GOLD)
    draw_chart(pg, lx + 180, ly + 236, 380, 64, GREEN)
    pg.text(lx + 180, ly + 306, "BEST DAY SINCE 2003 * NASDAQ +6.4%", 1, GREY)

    # ---- right column: NATO / Poland
    rx, ry, rw, rh = 652, 148, 324, 320
    pg.border(rx, ry, rw, rh, INK, 3)
    pg.text(rx + 16, ry + 16, "EUROPE  *  SECURITY", 1, RED)
    pg.text(rx + 16, ry + 44, "NATO WATCHES", 3, INK)
    pg.text(rx + 16, ry + 74, "THE EAST", 3, INK)
    draw_radar(pg, rx + rw // 2, ry + 176, 54)
    pg.text(rx + rw // 2, ry + 240, "3 X KH-101", 1, RED, align="center")
    pg.para(rx + 16, ry + 258,
            "The alliance sends an AWACS early-warning jet to "
            "Poland after three Russian Kh-101 cruise missiles "
            "landed there on Friday.",
            rw - 32, 1, INK)
    pg.hbar(rx + 16, ry + 294, rw - 32, GREY, 1)
    pg.text(rx + 16, ry + 302, "SACEUR AUTHORISED THE MOVE", 1, GREY)

    # ---- bottom grid: four stories
    panels = [
        (24, 492, "WAR AT SEA", "FAR FROM UKRAINE",
         "Ukraine says seven sea drones sank the Russian "
         "corvette Merkury off Benghazi, and hit the cargo "
         "ship Angara. A Ka-27 helicopter aboard was destroyed.",
         "ship", TEAL),
        (522, 492, "CLIMATE", "COP31 ENDS WITH NO DEAL",
         "The longest COP in history ends in Antalya with no "
         "deal on fossil fuels, the first climate summit to "
         "collapse since Copenhagen in 2009. The blame game begins.",
         "globe", ORANGE),
        (24, 736, "MIDDLE EAST", "THREE KILLED IN GAZA",
         "Israeli strikes kill three, including UNRWA worker "
         "Adel al-Helo, hit near a water well in Jabalia camp. "
         "Oxfam says 99% of Gaza is contaminated.",
         "skyline", RED),
        (522, 736, "ENERGY  *  IRAN", "TEHRAN DEFIES BLOCKADE",
         "Iran vows to use all its tools against a US naval "
         "blockade. Washington sanctions 22 entities and eight "
         "people in its shadow banks. Trump vows to sink ships "
         "that test it.",
         "tanker", NAVY),
    ]
    pw, ph = 478, 220
    for (px, py, kicker, headline, body, art, accent) in panels:
        pg.border(px, py, pw, ph, INK, 3)
        pg.box(px + 3, py + 3, pw - 6, 26, accent)
        pg.text(px + 14, py + 10, kicker, 1, WHITE)
        pg.text(px + 14, py + 42, headline, 2, INK)
        pg.para(px + 14, py + 78, body, 296, 2, INK)
        if art == "ship":
            pg.text(px + 330, py + 62, "7 SEA DRONES", 1, TEAL)
            draw_ship(pg, px + 330, py + 84, 132, 116)
        elif art == "globe":
            draw_globe(pg, px + 396, py + 108, 42)
        elif art == "skyline":
            draw_skyline(pg, px + 330, py + 84, 132, 116)
        else:
            draw_tanker(pg, px + 330, py + 84, 132, 116)

    # ---- footer
    pg.hbar(24, 972, 976, INK, 2)
    pg.text(W // 2, 984, "ALL STORIES AS REPORTED ON 24 NOVEMBER 2026  *  "
            "SOURCES: REUTERS, BBC, AP", 1, GREY, align="center")
    return pg


# ------------------------------------------------------------------ PNG out
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(pg):
    raw = bytearray()
    for y in range(pg.h):
        raw.append(0)  # filter: none
        raw += pg.px[y * pg.w * 3:(y + 1) * pg.w * 3]
    ihdr = struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def validate_png(data):
    """Fail loudly if the output is not a valid 1024x1024 PNG <= 1 MiB."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("invalid PNG signature")
    if len(data) > 1048576:
        raise SystemExit("entry.png exceeds 1 MiB")
    w, h = struct.unpack(">II", data[16:24])
    if (w, h) != (W, H):
        raise SystemExit("entry.png is %dx%d, expected 1024x1024" % (w, h))
    if data[-12:] != chunk(b"IEND", b""):
        raise SystemExit("PNG missing valid IEND chunk")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(draw_page())
    validate_png(data)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
