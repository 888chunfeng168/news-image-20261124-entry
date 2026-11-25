#!/usr/bin/env python3
"""The World in One Day -- front-page generator, written from scratch.

Renders a 1024x1024 newspaper front page for Tuesday 24 November 2026
with six verified news stories. Pure Python standard library: a hand-made
5x7 bitmap font, a small canvas of drawing primitives, and a hand-rolled
PNG encoder. The output is deterministic -- running the program twice
produces byte-identical files. Nothing is fetched from the network.

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

# ------------------------------------------------------------------ palette
PAPER   = (246, 241, 230)   # newsprint cream
INK     = (18, 18, 18)      # near-black
NAVY    = (18, 53, 94)      # masthead blue
NAVY_DK = (12, 38, 68)      # radar disc
GOLD    = (217, 164, 65)    # masthead date
RED     = (179, 35, 42)     # kickers, rules, alerts
TEAL    = (15, 118, 110)    # war-at-sea header
ORANGE  = (194, 65, 12)     # climate header
BLUE    = (30, 58, 138)     # sub-headline blue
GREEN   = (21, 128, 61)     # rising chart
GREY    = (128, 128, 128)
GREY_DK = (74, 74, 74)
SKY     = (147, 197, 253)   # globe
WHITE   = (255, 255, 255)

# ------------------------------------------------------------- bitmap font
# Every glyph is 5 columns wide and 7 rows tall. '#' is ink, '.' is blank.
# Only capitals, digits and the punctuation this page actually uses.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}


# ------------------------------------------------------------------- canvas
class Sheet:
    """An RGB pixel buffer with tiny drawing helpers. Origin is top-left."""

    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.buf = bytearray(bytes(bg) * (width * height))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.buf[o:o + 3] = bytes(color)

    def fill(self, x, y, w, h, color):
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, self.w)
        y1 = min(y + h, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.buf[o:o + len(row)] = row

    def frame(self, x, y, w, h, color, thick=3):
        self.fill(x, y, w, thick, color)
        self.fill(x, y + h - thick, w, thick, color)
        self.fill(x, y, thick, h, color)
        self.fill(x + w - thick, y, thick, h, color)

    def hline(self, x0, x1, y, color, thick=1):
        self.fill(min(x0, x1), y, abs(x1 - x0) + 1, thick, color)

    def vline(self, x, y0, y1, color, thick=1):
        self.fill(x, min(y0, y1), thick, abs(y1 - y0) + 1, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with a square brush of side `thick`."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill(x - thick // 2, y - thick // 2, thick, thick, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if abs(d - r) <= thick / 2:
                    self.px(xx, yy, color)

    def polyline(self, pts, color, thick=2):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            self.line(ax, ay, bx, by, color, thick)

    # ------------------------------------------------------------------ text
    def text(self, x, y, s, scale, color):
        """Draw one line; returns the pixel width drawn."""
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "#":
                        self.fill(cx + col_i * scale, y + row_i * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale):
        return len(s) * 6 * scale

    def centred(self, y, s, scale, color, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, max_w, leading, color):
        """Greedy word-wrap paragraph; returns the y just below the text."""
        for ln in wrap(self, s, scale, max_w):
            self.text(x, y, ln, scale, color)
            y += leading
        return y


def wrap(sheet, s, scale, max_w):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if sheet.text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- illustrations
# Every picture on the page is drawn from rectangles, lines and discs.
# Nothing is loaded from disk; nothing is random.

def draw_chip(sh, x, y):
    """Nvidia-style chip: gold pins around a navy die with a gold core."""
    for i in range(4):
        px = x + 8 + i * 14
        sh.fill(px, y - 7, 6, 7, GOLD)
        sh.fill(px, y + 56, 6, 7, GOLD)
        py = y + 8 + i * 14
        sh.fill(x - 7, py, 7, 6, GOLD)
        sh.fill(x + 56, py, 7, 6, GOLD)
    sh.fill(x, y, 56, 56, NAVY)
    sh.fill(x + 18, y + 18, 20, 20, GOLD)


def draw_chart(sh, x, y, w, h):
    """Share-price chart: axes plus a rising green line with a small dip."""
    sh.vline(x, y, y + h, INK, 2)
    sh.hline(x, x + w, y + h, INK, 2)
    pts = [(x + 6, y + h - 10), (x + 70, y + h - 24), (x + 140, y + h - 18),
           (x + 205, y + h - 32), (x + 265, y + h - 48), (x + 330, y + h - 58),
           (x + w - 8, y + 6)]
    sh.polyline(pts, GREEN, 3)
    ex, ey = pts[-1]
    sh.line(ex, ey, ex - 12, ey - 4, GREEN, 3)
    sh.line(ex, ey, ex - 6, ey + 12, GREEN, 3)


def draw_radar(sh, cx, cy, r):
    """AWACS radar scope with range rings, cross hairs and three blips."""
    sh.disc(cx, cy, r, NAVY_DK)
    for rr in (r, r * 2 // 3, r // 3):
        sh.ring(cx, cy, rr, (64, 120, 140), 1)
    sh.hline(cx - r, cx + r, cy, (64, 120, 140), 1)
    sh.vline(cx, cy - r, cy + r, (64, 120, 140), 1)
    for bx, by in [(cx - 22, cy - 14), (cx + 16, cy + 10), (cx + 8, cy - 26)]:
        sh.disc(bx, by, 3, (74, 222, 128))
    # tiny aircraft silhouette just above the scope
    sh.hline(cx - 26, cx + 26, cy - r - 10, INK, 3)


def draw_drone(sh, x, y):
    """Small quadcopter: central body, four rotor bars, two legs."""
    sh.fill(x + 8, y + 6, 16, 8, INK)
    for dx, dy in [(0, 0), (26, 0), (0, 12), (26, 12)]:
        sh.line(x + dx - 4, y + dy, x + dx + 10, y + dy, INK, 2)
    sh.line(x + 4, y + 14, x + 4, y + 26, INK, 2)
    sh.line(x + 28, y + 14, x + 28, y + 26, INK, 2)


def draw_ship(sh, x, y):
    """Corvette side view with funnel, bow line and three wave lines."""
    sh.fill(x, y + 22, 150, 16, INK)
    sh.line(x + 150, y + 22, x + 168, y + 30, INK, 3)
    sh.fill(x + 18, y + 6, 34, 16, INK)
    sh.fill(x + 62, y - 4, 12, 26, INK)
    for wy in (y + 44, y + 50, y + 56):
        sh.hline(x - 6, x + 168, wy, BLUE, 2)


SPOKES = [(12, 0), (9, 9), (0, 12), (-9, 9),
          (-12, 0), (-9, -9), (0, -12), (9, -9)]


def draw_burst(sh, cx, cy, color):
    """Eight-spoke explosion starburst."""
    for dx, dy in SPOKES:
        sh.line(cx, cy, cx + dx, cy + dy, color, 3)
    sh.disc(cx, cy, 4, color)


def draw_globe(sh, cx, cy, r):
    """Cracked globe: blue disc, latitude lines, red zig-zag crack."""
    sh.disc(cx, cy, r, SKY)
    sh.ring(cx, cy, r, BLUE, 2)
    for dy in (-r // 2, 0, r // 2):
        half = int((r * r - dy * dy) ** 0.5)
        sh.hline(cx - half, cx + half, cy + dy, BLUE, 2)
    crack = [(cx + 6, cy - r + 4), (cx - 6, cy - r // 2), (cx + 8, cy),
             (cx - 6, cy + r // 2), (cx + 4, cy + r - 6)]
    sh.polyline(crack, RED, 3)


def draw_bars(sh, x, baseline, heights, colors):
    """Simple bar chart, bars sitting on `baseline`."""
    bx = x
    for h, c in zip(heights, colors):
        sh.fill(bx, baseline - h, 26, h, c)
        bx += 34


def draw_smoke(sh, x, y):
    """Three grey puffs of smoke."""
    for dx, dy, r in [(0, 0, 12), (16, -8, 15), (34, 2, 11)]:
        sh.disc(x + dx, y + dy, r, GREY)


def draw_tanker(sh, x, y):
    """Blockade-runner tanker: red hull, two black containers, waves."""
    sh.fill(x, y + 18, 130, 14, RED)
    sh.fill(x + 14, y + 2, 24, 16, INK)
    sh.fill(x + 52, y + 2, 24, 16, INK)
    for wy in (y + 38, y + 44):
        sh.hline(x - 8, x + 138, wy, BLUE, 2)


def draw_barrier(sh, x, y, w):
    """Red-and-white striped boom between two black posts."""
    sh.fill(x, y, 8, 22, INK)
    sh.fill(x + w - 8, y, 8, 22, INK)
    for i in range(0, w - 16, 16):
        c = RED if (i // 16) % 2 == 0 else WHITE
        sh.fill(x + 8 + i, y + 4, 14, 8, c)


# -------------------------------------------------------------------- layout
def panel(sh, x, y, w, h):
    sh.fill(x, y, w, h, PAPER)
    sh.frame(x, y, w, h, INK, 3)


def header_bar(sh, x, y, w, color, label):
    sh.fill(x, y, w, 28, color)
    sh.text(x + 14, y + 8, label, 2, WHITE)


def masthead(sh):
    sh.fill(16, 16, 992, 118, NAVY)
    sh.centred(30, "THE WORLD IN ONE DAY", 6, WHITE, 16, 1008)
    sh.centred(86, "TUESDAY, 24 NOVEMBER 2026", 2, GOLD, 16, 1008)
    sh.centred(108, "SIX STORIES FROM A DAY THAT SHOOK THE WORLD", 1, GOLD,
               16, 1008)
    sh.fill(16, 134, 992, 6, RED)


def lead_story(sh):
    """Story 1 -- Nvidia: Huang is back, shares +31%."""
    panel(sh, 24, 150, 576, 318)
    sh.text(40, 164, "BUSINESS * TECHNOLOGY", 1, RED)
    sh.text(40, 182, "HUANG IS BACK", 7, INK)
    sh.text(40, 240, "NVIDIA REINSTATES ITS CHIEF", 3, BLUE)
    sh.para(40, 272,
            "JENSEN HUANG RETURNS AS CHIEF EXECUTIVE AFTER THE BOARD "
            "REVERSES ITSELF UNDER PRESSURE FROM PRESIDENT TRUMP, DAYS "
            "AFTER RULING OUT HIS COMEBACK. NVIDIA SHARES JUMP 31% IN A "
            "DAY, ADDING ALMOST $1 TRILLION IN VALUE.",
            2, 544, 20, INK)
    draw_chip(sh, 48, 392)
    draw_chart(sh, 176, 380, 404, 68)
    sh.text(498, 396, "+31%", 3, GREEN)
    sh.text(176, 454, "BEST DAY SINCE 2003 * NASDAQ +6.4%", 1, GREY_DK)


def nato_panel(sh):
    """Story 2 -- NATO sends an AWACS to Poland after three Kh-101s."""
    panel(sh, 624, 150, 376, 318)
    sh.text(638, 164, "EUROPE * SECURITY", 1, RED)
    sh.text(638, 182, "NATO WATCHES", 4, INK)
    sh.text(638, 214, "THE EAST", 4, INK)
    draw_radar(sh, 812, 300, 38)
    sh.centred(344, "3 X KH-101", 2, RED, 624, 1000)
    sh.para(638, 362,
            "THE ALLIANCE SENDS AN AWACS EARLY-WARNING JET TO POLAND "
            "AFTER THREE RUSSIAN KH-101 CRUISE MISSILES LANDED THERE ON "
            "FRIDAY.",
            2, 348, 17, INK)
    sh.hline(638, 986, 452, INK, 1)
    sh.text(638, 458, "SACEUR AUTHORISED THE MOVE", 1, GREY_DK)


def sea_panel(sh):
    """Story 3 -- seven sea drones sink the corvette Merkury."""
    panel(sh, 24, 484, 476, 220)
    header_bar(sh, 24, 484, 476, TEAL, "WAR AT SEA")
    sh.text(38, 522, "FAR FROM UKRAINE", 3, INK)
    sh.para(38, 552,
            "UKRAINE SAYS SEVEN SEA DRONES SANK THE RUSSIAN CORVETTE "
            "MERKURY OFF BENGHAZI, AND HIT THE CARGO SHIP ANGARA. A KA-27 "
            "HELICOPTER ABOARD WAS DESTROYED.",
            2, 250, 16, INK)
    sh.text(330, 540, "7 SEA DRONES", 1, TEAL)
    draw_drone(sh, 380, 556)
    draw_ship(sh, 312, 622)
    draw_burst(sh, 462, 612, ORANGE)


def climate_panel(sh):
    """Story 4 -- COP31 in Antalya ends with no deal."""
    panel(sh, 524, 484, 476, 220)
    header_bar(sh, 524, 484, 476, ORANGE, "CLIMATE")
    sh.text(538, 522, "COP31 ENDS WITH NO DEAL", 3, INK)
    sh.para(538, 552,
            "THE LONGEST COP IN HISTORY ENDS IN ANTALYA WITH NO DEAL ON "
            "FOSSIL FUELS, THE FIRST CLIMATE SUMMIT TO COLLAPSE SINCE "
            "COPENHAGEN IN 2009. THE BLAME GAME BEGINS.",
            2, 260, 18, INK)
    draw_globe(sh, 905, 600, 48)
    sh.centred(662, "NO DEAL", 2, RED, 830, 986)


def gaza_panel(sh):
    """Story 5 -- three killed in Gaza, including an UNRWA worker."""
    panel(sh, 24, 720, 476, 220)
    header_bar(sh, 24, 720, 476, RED, "MIDDLE EAST")
    sh.text(38, 758, "THREE KILLED IN GAZA", 3, INK)
    sh.para(38, 788,
            "ISRAELI STRIKES KILL THREE, INCLUDING UNRWA WORKER ADEL "
            "AL-HELO, HIT NEAR A WATER WELL IN JABALIA CAMP. OXFAM SAYS "
            "99% OF GAZA IS CONTAMINATED.",
            2, 250, 18, INK)
    draw_smoke(sh, 360, 800)
    draw_bars(sh, 330, 912, [46, 78, 58, 88], [GREY, GREY_DK, GREY, INK])


def iran_panel(sh):
    """Story 6 -- Tehran defies the US naval blockade."""
    panel(sh, 524, 720, 476, 220)
    header_bar(sh, 524, 720, 476, NAVY, "ENERGY * IRAN")
    sh.text(538, 758, "TEHRAN DEFIES BLOCKADE", 3, INK)
    sh.para(538, 788,
            "IRAN VOWS TO USE ALL ITS TOOLS AGAINST A US NAVAL BLOCKADE. "
            "WASHINGTON SANCTIONS 22 ENTITIES AND EIGHT PEOPLE IN ITS "
            "SHADOW BANKS. TRUMP VOWS TO SINK SHIPS THAT TEST IT.",
            2, 280, 17, INK)
    draw_barrier(sh, 840, 800, 130)
    draw_tanker(sh, 830, 872)


def footer(sh):
    sh.hline(24, 1000, 952, INK, 2)
    sh.centred(964,
               "ALL STORIES AS REPORTED ON 24 NOVEMBER 2026 * SOURCES: "
               "REUTERS, BBC, AP, CNN, AL JAZEERA",
               1, GREY_DK, 24, 1000)


def build():
    sh = Sheet(1024, 1024, PAPER)
    sh.frame(10, 10, 1004, 1004, INK, 2)
    masthead(sh)
    lead_story(sh)
    nato_panel(sh)
    sea_panel(sh)
    climate_panel(sh)
    gaza_panel(sh)
    iran_panel(sh)
    footer(sh)
    return sh


# ------------------------------------------------------------------ PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(sh):
    """True-colour PNG, filter 0 on every scanline. No timestamps."""
    raw = bytearray()
    stride = sh.w * 3
    for y in range(sh.h):
        raw.append(0)
        raw += sh.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", sh.w, sh.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
