#!/usr/bin/env python3
"""news-image-20261119: sum up 19 November 2026 in one image.

Draws a newspaper front page with PIL (DejaVu fonts) when Pillow is
available, and with a pure-stdlib pixel renderer otherwise -- the
grader runs python:3.13-slim, standard library only, so a PIL-only
program would fail there. Both paths draw the same page, the same
stories, at the same size, with no network and no randomness, so two
runs in the same environment write byte-identical PNGs.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Test the stdlib path locally: MAKEFUN_FORCE_STDLIB=1 MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (17, 17, 17)
GREY = (90, 88, 82)
RED = (163, 18, 26)
BLUE = (26, 58, 92)
LIGHT = (232, 228, 216)
SKY1 = (255, 183, 77)
SKY2 = (255, 120, 70)
SKY3 = (90, 40, 90)
SEA = (40, 60, 110)

STORIES = [
    # (kicker, headline, body, colour)
    ("CRIMEAN BRIDGE", "CRIMEAN BRIDGE HIT AGAIN",
     "Struck overnight, the third attack in a week; traffic halted.", RED),
    ("US - IRAN / THE GULF", "US AND IRAN EXCHANGE FIRE AGAIN",
     "Iran widens attacks on Gulf states, targeting Bahrain and Kuwait.", RED),
    ("EUROPE / UKRAINE", "EU PROPOSES EUR 45BN UKRAINE LOAN",
     "To be repaid after Russia pays reparations.", BLUE),
    ("SPACE", "VOYAGER 1 REACHES ONE LIGHT-DAY",
     "Fifty years after launch, NASA's probe is one light-day from Earth.", BLUE),
]

LEAD_HEADLINE = "GTA VI ROLLS OUT WORLDWIDE"
LEAD_BODY = "Gamers enter Vice City as the UK release arrives after a 13-year wait."


# ---------------------------------------------------------------- font (stdlib path)
# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows
# of 5 bits, written as strings of '#' (on) and '.' (off).
FONT_5X7 = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '\u2022': ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def wrap_text(text, max_width, measure):
    """Wrap text to lines fitting max_width (measure: text -> pixels)."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if measure(trial) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- backends
class PilBackend:
    """Draw with Pillow + DejaVu. Used locally, where Pillow is installed."""

    def __init__(self):
        from PIL import Image, ImageDraw, ImageFont
        self._Image = Image
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def font(self, size, bold=False, serif=False):
        key = (size, bold, serif)
        if key not in self._fonts:
            from PIL import ImageFont
            if serif:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
            elif bold:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            else:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            self._fonts[key] = ImageFont.truetype(path, size)
        return self._fonts[key]

    def measure(self, text, size, bold=False, serif=False):
        return self.font(size, bold, serif).getlength(text)

    def rect(self, x, y, w, h, fill):
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill)

    def ellipse(self, x, y, w, h, fill):
        self.d.ellipse([x, y, x + w - 1, y + h - 1], fill=fill)

    def text(self, x, y, s, size, fill, bold=False, serif=False, centre=False):
        f = self.font(size, bold, serif)
        if centre:
            x = x - int(f.getlength(s) // 2)
        self.d.text((x, y), s, font=f, fill=fill)

    def save(self, path):
        self.img.save(path, format="PNG", compress_level=9)


class PixelBackend:
    """Draw into a plain RGB bytearray and encode PNG with zlib only."""

    def __init__(self):
        self.pix = bytearray(PAPER * (W * H))

    def _scale(self, size):
        return max(1, int(round(size / 7.0)))

    def measure(self, text, size, bold=False, serif=False):
        return len(text) * 6 * self._scale(size)

    def rect(self, x, y, w, h, fill):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        for yy in range(y0, y1):
            base = yy * W * 3
            for xx in range(x0, x1):
                o = base + xx * 3
                self.pix[o:o + 3] = bytes(fill)

    def ellipse(self, x, y, w, h, fill):
        cx, cy, rx, ry = x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0
        for yy in range(max(0, y), min(H, y + h)):
            dy = (yy + 0.5 - cy) / ry
            if abs(dy) > 1:
                continue
            dx = rx * (1 - dy * dy) ** 0.5
            self.rect(int(cx - dx), yy, int(2 * dx), 1, fill)

    def text(self, x, y, s, size, fill, bold=False, serif=False, centre=False):
        sc = self._scale(size)
        if centre:
            x = x - self.measure(s, size) // 2
        s = s.upper()
        for ci, ch in enumerate(s):
            glyph = FONT_5X7.get(ch, FONT_5X7[' '])
            gx = x + ci * 6 * sc
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '1':
                        self.rect(gx + col * sc, y + row * sc, sc, sc, fill)
                        if bold:
                            self.rect(gx + col * sc + 1, y + row * sc, sc, sc, fill)

    def save(self, path):
        raw = b"".join(b"\x00" + bytes(self.pix[yy * W * 3:(yy + 1) * W * 3])
                       for yy in range(H))
        def chunk(kind, data):
            c = struct.pack(">I", len(data)) + kind + data
            return c + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
               + chunk(b"IDAT", zlib.compress(raw, 9))
               + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(png)


# ---------------------------------------------------------------- layout
def draw_text_block(b, x, y, max_w, lines, size, fill, bold=False, serif=False):
    for i, line in enumerate(lines):
        b.text(x, y + i * (size + 6), line, size, fill, bold=bold, serif=serif)
    return y + len(lines) * (size + 6)


def draw_story(b, x, y, w, h, kicker, headline, body, colour):
    b.rect(x, y, w, h, LIGHT)
    b.rect(x, y, w, 5, colour)
    b.text(x + 16, y + 16, kicker, 17, colour, bold=True)
    # Shrink until headline and body each fit in two lines. The stdlib
    # bitmap font is wider per character than DejaVu, so it needs the
    # smaller sizes; the PIL path takes the first pair, as before.
    chosen = None
    for hsize, bsize in [(25, 19), (25, 16), (25, 14), (22, 14)]:
        hl = wrap_text(headline, w - 32, lambda t, s=hsize: b.measure(t, s, serif=True))
        bl = wrap_text(body, w - 32, lambda t, s=bsize: b.measure(t, s))
        chosen = (hsize, bsize, hl, bl)
        if len(hl) <= 2 and len(bl) <= 2:
            break
    hsize, bsize, hl, bl = chosen
    draw_text_block(b, x + 16, y + 44, w - 32, hl[:2], hsize, INK, serif=True)
    by = y + 44 + min(len(hl), 2) * (hsize + 6)
    draw_text_block(b, x + 16, by + 4, w - 32, bl[:2], bsize, GREY)


def draw_sunset(b, x, y, w, h):
    """Vice City sunset: banded sky, sun, skyline, sea."""
    bands = [(SKY1, 0.00), (SKY2, 0.35), (SKY3, 0.70)]
    for i in range(h):
        f = i / h
        if f < 0.35:
            col = SKY1
        elif f < 0.70:
            col = SKY2
        else:
            col = SKY3
        b.rect(x, y + i, w, 1, col)
    b.ellipse(x + w // 2 - 42, y + 28, 84, 84, (255, 220, 130))
    # skyline silhouettes
    heights = [90, 130, 70, 150, 100, 120, 80]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bx = x + i * bw
        b.rect(bx + 4, y + h - 46 - bh, bw - 8, bh + 46, (30, 20, 50))
        for wy in range(y + h - 40 - bh, y + h - 50, 22):
            b.rect(bx + bw // 2 - 3, wy, 6, 8, (255, 200, 90))
    b.rect(x, y + h - 46, w, 46, SEA)
    b.rect(x, y + h - 30, w, 3, (255, 200, 90))


def draw_page(b):
    # masthead
    b.text(W // 2, 26, "THE DAILY WORLD", 62, INK, bold=True, serif=True, centre=True)
    b.rect(36, 108, W - 72, 3, INK)
    b.text(W // 2, 124, "THURSDAY  \u2022  19 NOVEMBER 2026", 26, RED, bold=True, centre=True)
    b.rect(36, 162, W - 72, 2, GREY)

    # lead story
    b.rect(36, 178, W - 72, 296, (255, 255, 255))
    b.rect(36, 178, W - 72, 5, RED)
    b.text(56, 196, "LEAD  \u2022  GAMING  \u2022  BBC", 18, RED, bold=True)
    hl = wrap_text(LEAD_HEADLINE, 600, lambda t: b.measure(t, 44, serif=True))
    draw_text_block(b, 56, 226, 600, hl, 44, INK, serif=True)
    bl = wrap_text(LEAD_BODY, 600, lambda t: b.measure(t, 21))
    draw_text_block(b, 56, 226 + len(hl) * 50 + 10, 600, bl, 21, GREY)
    draw_sunset(b, 700, 196, 268, 260)

    # four stories in a 2x2 grid
    gx, gy = 36, 494
    cw, ch, gap = 466, 158, 20
    for i, (kicker, headline, body, colour) in enumerate(STORIES):
        draw_story(b, gx + (i % 2) * (cw + gap), gy + (i // 2) * (ch + gap),
                   cw, ch, kicker, headline, body, colour)

    # fifth story, full width
    b.rect(36, 830, W - 72, 108, LIGHT)
    b.rect(36, 830, W - 72, 5, RED)
    b.text(56, 844, "BUSINESS  \u2022  AL JAZEERA", 17, RED, bold=True)
    b.text(56, 870, "ANTHROPIC RAISES $81.3BN IN RECORD IPO", 27, INK, serif=True)
    b.text(56, 906, "The biggest initial public offering of all time.", 19, GREY)

    # footer
    b.rect(36, 956, W - 72, 2, GREY)
    b.text(W // 2, 970, "19 NOVEMBER 2026  \u2022  SIX STORIES", 18, GREY, centre=True)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    use_stdlib = os.environ.get("MAKEFUN_FORCE_STDLIB") == "1"
    backend = None
    if not use_stdlib:
        try:
            backend = PilBackend()
        except Exception:
            backend = None
    if backend is None:
        backend = PixelBackend()
    draw_page(backend)
    backend.save(out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
