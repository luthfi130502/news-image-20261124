#!/usr/bin/env python3
"""news-image-20261124 -- "The World in One Day".

Pure-stdlib Python 3.13 program: draws a one-page editorial front page
summing up Tuesday 24 November 2026 and writes it to /output/entry.png.

No network, no third-party packages, no randomness, no clock: two runs
produce byte-identical PNGs. The rasteriser, the 5x7 bitmap font and the
PNG encoder are all written here from scratch.

Design: dark "night edition" front page. Masthead + date; one dominant
hero illustration (a green AI chip riding a steep gold market rally,
with the day's index gains); a two-line lead headline; an ALSO TODAY
strip of six short headlines across regions and beats.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ---------------------------------------------------------
NAVY = (13, 21, 38)
NAVY2 = (18, 30, 54)
NAVY3 = (30, 48, 80)
WHITE = (245, 247, 250)
MUTED = (148, 163, 184)
GOLD = (242, 193, 78)
GREEN = (34, 197, 94)
CHIP = (22, 163, 74)
CHIP_EDGE = (134, 239, 172)
DARK_GREEN = (20, 83, 45)
BLUE = (59, 130, 246)
RED = (220, 38, 38)
TEAL = (13, 148, 136)
ORANGE = (234, 88, 12)
PURPLE = (147, 51, 234)
DARK_GOLD = (202, 138, 4)

# ---- 5x7 bitmap font ('#' = on, '.' = off) ---------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}
BLANK = (".....", ".....", ".....", ".....", ".....", ".....", ".....")


class Canvas:
    """RGB pixel buffer with tiny vector primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, c, t=1):
        self.fill_rect(x0, y, x1 - x0, t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.fill_rect(x, y0, t, y1 - y0, c)

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, t // 2)
        for s in range(steps + 1):
            x = x0 + (x1 - x0) * s // steps
            y = y0 + (y1 - y0) * s // steps
            self.disc(x, y, r, c)

    def polyline(self, pts, c, t=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c, t)

    def tri(self, p0, p1, p2, c):
        pts = sorted((p0, p1, p2), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        def edge_x(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = edge_x(x0, y0, x1, y1, y)
                xb = edge_x(x0, y0, x2, y2, y)
            else:
                xa = edge_x(x1, y1, x2, y2, y)
                xb = edge_x(x0, y0, x2, y2, y)
            lo, hi = (xa, xb) if xa <= xb else (xb, xa)
            self.fill_rect(int(lo), y, int(hi) - int(lo) + 1, 1, c)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale if s else 0

    def text(self, x, y, s, color, scale=2, align="left"):
        if align == "center":
            x -= self.text_w(s, scale) // 2
        elif align == "right":
            x -= self.text_w(s, scale)
        cx = x
        for ch in s:
            g = FONT.get(ch, BLANK)
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "#":
                        self.fill_rect(cx + col * scale, y + r * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return self.text_w(s, scale)


def png_bytes(cv):
    """Encode the canvas as a deterministic PNG (fixed zlib level)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(typ, data):
        c = typ + data
        return (struct.pack(">I", len(data)) + c +
                struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


# ---- the picture -------------------------------------------------------
ROWS = [
    ("TECH", BLUE, "CROWDSTRIKE BUYS ZSCALER IN $44BN ALL-STOCK DEAL"),
    ("WAR", RED, "KYIV HIT BY FRESH RUSSIAN DRONE AND MISSILE STRIKES"),
    ("CLIMATE", TEAL, "COP31 TALKS DEADLOCKED OVER FOSSIL FUELS"),
    ("ASIA", ORANGE, "INDONESIA FACTORY FIRE: RESCUE UNDER WAY IN BANTEN"),
    ("MIDEAST", PURPLE, "IRAN WARNS U.S. OVER NAVAL BLOCKADE THREAT"),
    ("EUROPE", DARK_GOLD, "LISBON MARCHES AGAINST THE RISING COST OF LIVING"),
]


def draw():
    cv = Canvas(W, H, NAVY)

    # ---- masthead ------------------------------------------------------
    cv.text(512, 16, "THE WORLD IN ONE DAY", WHITE, scale=6, align="center")
    cv.text(512, 66, "TUESDAY 24 NOVEMBER 2026", GOLD, scale=3, align="center")
    cv.fill_rect(0, 100, W, 3, GOLD)

    # ---- hero: faint dot grid ------------------------------------------
    for gy in range(120, 556, 36):
        for gx in range(36, W, 36):
            cv.set(gx, gy, NAVY3)

    # ---- hero: gold rally arrow (drawn first, behind chip and stats) ---
    cv.polyline([(60, 540), (280, 470), (500, 380), (720, 260), (950, 150)],
                GOLD, t=12)
    cv.tri((988, 132), (952, 168), (937, 137), GOLD)

    # ---- hero: the chip -------------------------------------------------
    for px in range(140, 381, 32):
        cv.fill_rect(px, 191, 12, 14, DARK_GREEN)
        cv.fill_rect(px, 465, 12, 14, DARK_GREEN)
    for py in range(225, 466, 32):
        cv.fill_rect(106, py, 14, 12, DARK_GREEN)
        cv.fill_rect(380, py, 14, 12, DARK_GREEN)
    cv.fill_rect(120, 205, 260, 260, CHIP)
    cv.rect(120, 205, 260, 260, CHIP_EDGE, t=3)
    cv.fill_rect(168, 253, 164, 164, DARK_GREEN)
    cv.rect(168, 253, 164, 164, GREEN, t=2)
    cv.text(250, 300, "NVDA", WHITE, scale=5, align="center")
    cv.text(250, 352, "AI CHIP", GOLD, scale=2, align="center")
    cv.fill_rect(128, 170, 244, 24, GOLD)
    cv.text(250, 175, "BACK AFTER 11 DAYS", NAVY, scale=2, align="center")

    # ---- hero: index gains, 2x2 -----------------------------------------
    stats = [
        (560, 150, "NVDA", "+31.5%"),
        (772, 150, "NASDAQ", "+6.5%"),
        (560, 274, "S&P 500", "+4.7%"),
        (772, 274, "DOW", "+3.0%"),
    ]
    for x, y, label, value in stats:
        cv.fill_rect(x, y, 200, 112, NAVY2)
        cv.rect(x, y, 200, 112, NAVY3, t=2)
        cv.text(x + 14, y + 14, label, MUTED, scale=2)
        cv.text(x + 14, y + 46, value, GREEN, scale=5)

    # ---- hero: market context + rising candles --------------------------
    cv.text(560, 410, "BEST DAY SINCE APRIL 2025", GOLD, scale=2)
    cv.text(560, 436, "CHIP INDEX +14%", WHITE, scale=2)
    heights = [22, 30, 26, 40, 48, 44, 62, 74, 88, 104]
    for i, hgt in enumerate(heights):
        x = 580 + i * 40
        top = 535 - hgt
        col = RED if i == 2 else GREEN
        cv.vline(x + 10, top - 8, 535 + 8, col, t=2)
        cv.fill_rect(x, top, 22, hgt, col)
    cv.hline(560, 972, 542, NAVY3, t=2)

    # ---- lead headline band ----------------------------------------------
    cv.fill_rect(0, 556, W, 112, NAVY2)
    cv.fill_rect(0, 556, 10, 112, GOLD)
    cv.text(44, 574, "HUANG RETURNS TO NVIDIA", WHITE, scale=4)
    cv.text(44, 616, "MARKETS POST BEST DAY SINCE APRIL", GOLD, scale=4)

    # ---- ALSO TODAY strip -------------------------------------------------
    cv.text(44, 678, "ALSO TODAY", GOLD, scale=2)
    cv.hline(0, W, 700, NAVY3, t=1)
    for i, (tag, col, head) in enumerate(ROWS):
        y0 = 700 + i * 49
        if i:
            cv.hline(0, W, y0, NAVY3, t=1)
        cv.fill_rect(44, y0 + 8, 114, 33, col)
        cv.text(101, y0 + 17, tag, WHITE, scale=2, align="center")
        cv.text(174, y0 + 17, head, WHITE, scale=2)

    # ---- footer ------------------------------------------------------------
    cv.text(512, 1006,
            "REPORTED 24 NOV 2026 - SOURCES: REUTERS, BBC, WSJ, "
            "INVESTOR'S BUSINESS DAILY",
            MUTED, scale=1, align="center")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(draw())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
