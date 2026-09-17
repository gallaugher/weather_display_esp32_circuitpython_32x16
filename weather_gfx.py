# Graphics for the 32x16 NeoPixel weather display.
# Pure Python (no board imports) so it can be rendered on a desktop for preview.

W, H = 32, 16

def xy(x, y):
    """Physical (x 0-31 left->right, y 0-15 top->bottom) -> pixel index.
    Two 32x8 vertical-serpentine panels; the lower panel is rotated 180."""
    if y < 8:
        col, row = x, y
        return col * 8 + (row if col % 2 == 0 else 7 - row)
    col, row = 31 - x, 15 - y
    return 256 + col * 8 + (row if col % 2 == 0 else 7 - row)

# ---------------------------------------------------------------- 3x5 font
FONT = {
    "0": ["111","101","101","101","111"], "1": ["010","110","010","010","111"],
    "2": ["111","001","111","100","111"], "3": ["111","001","111","001","111"],
    "4": ["101","101","111","001","001"], "5": ["111","100","111","001","111"],
    "6": ["111","100","111","101","111"], "7": ["111","001","001","010","010"],
    "8": ["111","101","111","101","111"], "9": ["111","101","111","001","111"],
    "A": ["010","101","111","101","101"], "B": ["110","101","110","101","110"],
    "C": ["111","100","100","100","111"], "D": ["110","101","101","101","110"],
    "E": ["111","100","110","100","111"], "F": ["111","100","110","100","100"],
    "G": ["111","100","101","101","111"], "H": ["101","101","111","101","101"],
    "I": ["111","010","010","010","111"], "J": ["001","001","001","101","111"],
    "K": ["101","101","110","101","101"], "L": ["100","100","100","100","111"],
    "M": ["101","111","111","101","101"], "N": ["110","101","101","101","101"],
    "O": ["111","101","101","101","111"], "P": ["111","101","111","100","100"],
    "Q": ["111","101","101","111","001"], "R": ["110","101","110","101","101"],
    "S": ["111","100","111","001","111"], "T": ["111","010","010","010","010"],
    "U": ["101","101","101","101","111"], "V": ["101","101","101","101","010"],
    "W": ["101","101","111","111","101"], "X": ["101","101","010","101","101"],
    "Y": ["101","101","010","010","010"], "Z": ["111","001","010","100","111"],
    "-": ["000","000","111","000","000"], "°": ["11","11","00","00","00"],
    "/": ["001","001","010","100","100"], ":": ["0","1","0","1","0"],
    ".": ["0","0","0","0","1"],           "%": ["101","001","010","100","101"],
    "!": ["1","1","1","0","1"],           "?": ["111","001","011","000","010"],
    " ": ["00","00","00","00","00"],
}

def text_width(s):
    return sum(len(FONT.get(ch, FONT["?"])[0]) + 1 for ch in s) - 1

def draw_text(buf, s, x, y, color):
    """Draw 3x5 text into buf (dict of (x,y)->color). Returns end x (+1 gap)."""
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "1" and 0 <= x + c < W and 0 <= y + r < H:
                    buf[(x + c, y + r)] = color
        x += len(glyph[0]) + 1
    return x

def draw_text_centered(buf, s, y, color):
    return draw_text(buf, s, max(0, (W - text_width(s)) // 2), y, color)

# ---------------------------------------------------------------- colors
SUN   = (255, 170, 0);  RAY  = (255, 110, 0);  MOON = (200, 200, 255)
STAR  = (255, 255, 220); CLOUD = (110, 110, 120); DARK = (60, 60, 75)
RAIN  = (30, 90, 255);  SNOW = (230, 230, 255); BOLT = (255, 230, 0)
FOG   = (90, 90, 90)
HOT   = (255, 60, 0);   WARM = (255, 150, 0);   MILD = (60, 220, 60)
COOL  = (40, 140, 255); COLD = (150, 200, 255)
HI_C  = (255, 90, 40);  LO_C = (60, 120, 255);  DIM  = (70, 70, 70)
CLOCK = (255, 200, 120); DATE = (120, 160, 255); TICK = (200, 200, 200)

UNITS = "F"            # set by code.py from settings.toml; thresholds below are in F

def temp_color(t):
    if UNITS == "C":
        t = t * 9 / 5 + 32
    if t >= 85: return HOT
    if t >= 70: return WARM
    if t >= 55: return MILD
    if t >= 40: return COOL
    return COLD

# ---------------------------------------------------------------- 8x8 icons
# Legend: . off  y sun  r ray  m moon  * star  c cloud  d dark cloud
#         b rain  s snow  l bolt  f fog
SUN_FRAMES = [
    ["r..rr..r", ".r.yy.r.", "..yyyy..", "ryyyyyyr",
     "ryyyyyyr", "..yyyy..", ".r.yy.r.", "r..rr..r"],
    ["...rr...", "r..yy..r", ".ryyyyr.", ".yyyyyy.",
     ".yyyyyy.", ".ryyyyr.", "r..yy..r", "...rr..."],
]
# moon with twinkling stars (three frames, different stars lit)
MOON_FRAMES = [
    ["...mmm.*", "..mm....", ".mm...*.", ".mm.....",
     ".mm.....", ".mm....*", "..mm....", "*..mmm.."],
    ["...mmm..", "..mm...*", ".mm.....", ".mm....*",
     ".mm.....", ".mm.....", "*.mm....", "...mmm.*"],
    ["...mmm..", "..mm....", ".mm...*.", ".mm.....",
     ".mm....*", ".mm.....", "..mm....", "*..mmm.."],
]
PARTLY_FRAMES = [
    ["r.rr.r..", ".yyyy...", "ryyyyr..", ".yyyy...",
     "r.rcccc.", "..cccccc", ".ccccccc", "..cccccc"],
    ["..rr....", "ryyyyr..", ".yyyy...", ".yyyy...",
     "r.rcccc.", "..cccccc", ".ccccccc", "..cccccc"],
]
PARTLY_NIGHT_FRAMES = [
    ["..mmm..*", ".mm.....", ".mm.....", "..mm....",
     "...cccc.", "..cccccc", ".ccccccc", "..cccccc"],
    ["..mmm...", ".mm....*", ".mm.....", "..mm....",
     "...cccc.", "..cccccc", ".ccccccc", "..cccccc"],
]
CLOUD_FRAMES = [
    ["........", "...cc...", "..cccc..", ".cccccc.",
     "cccccccc", "cccccccc", ".cccccc.", "........"],
]

def _precip_frames(kind):
    cloud = ["...cc...", ".cccccc.", "cccccccc", ".cccccc."]
    frames = []
    for f in range(4):
        rows = list(cloud)
        for r in range(4):
            line = ""
            for c in range(8):
                on = ((c + r + f) % 4 == 0) if c % 2 == (r % 2) else False
                line += kind if on else "."
            rows.append(line)
        frames.append(rows)
    return frames

RAIN_FRAMES = _precip_frames("b")
SNOW_FRAMES = _precip_frames("s")
STORM_FRAMES = [
    ["...dd...", ".dddddd.", "dddddddd", ".dddddd.", "...ll...", "..ll....", "...l....", "..l....."],
    ["...dd...", ".dddddd.", "dddddddd", ".dddddd.", "..b.b.b.", ".b.b.b..", "..b.b.b.", "........"],
    ["...dd...", ".dddddd.", "dddddddd", ".dddddd.", "...ll...", "..ll....", "...l....", "..l....."],
    ["...dd...", ".dddddd.", "dddddddd", ".dddddd.", ".b.b.b..", "..b.b.b.", ".b.b.b..", "........"],
]
FOG_FRAMES = [
    ["........", "ffffff..", "........", "..ffffff", "........", "ffffff..", "........", "..ffffff"],
    ["........", "..ffffff", "........", "ffffff..", "........", "..ffffff", "........", "ffffff.."],
]

PALETTE = {"y": SUN, "r": RAY, "m": MOON, "*": STAR, "c": CLOUD, "d": DARK,
           "b": RAIN, "s": SNOW, "l": BOLT, "f": FOG, ".": None}

def icon_for(code, is_day=True):
    """WMO weather code -> (frames, precip_kind, description)"""
    if code == 0:
        return (SUN_FRAMES if is_day else MOON_FRAMES), None, "CLEAR"
    if code in (1, 2):
        return (PARTLY_FRAMES if is_day else PARTLY_NIGHT_FRAMES), None, "PARTLY CLOUDY"
    if code == 3:
        return CLOUD_FRAMES, None, "CLOUDY"
    if code in (45, 48):
        return FOG_FRAMES, None, "FOG"
    if code in (71, 73, 75, 77, 85, 86):
        return SNOW_FRAMES, "snow", "SNOW"
    if code in (95, 96, 99):
        return STORM_FRAMES, "rain", "STORMS"
    if code in (51, 53, 55, 56, 57):
        return RAIN_FRAMES, "rain", "DRIZZLE"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return RAIN_FRAMES, "rain", "RAIN"
    return CLOUD_FRAMES, None, "CLOUDY"

def draw_icon(buf, frames, frame_no, x0=0, y0=0):
    for r, row in enumerate(frames[frame_no % len(frames)]):
        for c, ch in enumerate(row):
            col = PALETTE.get(ch)
            if col:
                buf[(x0 + c, y0 + r)] = col

# ---------------------------------------------------------------- pages
def render_weather(wx, frame_no):
    """Page 1: icon, current temp, today's hi/lo, precip-chance bar."""
    buf = {}
    frames, precip, _ = icon_for(wx["code"], wx["is_day"])
    draw_icon(buf, frames, frame_no, 0, 0)

    t = int(round(wx["temp"]))
    x = draw_text(buf, str(t), 10, 1, temp_color(t))
    draw_text(buf, "°", x, 1, temp_color(t))

    hi_s, lo_s = str(int(round(wx["hi"]))), str(int(round(wx["lo"])))
    hi_end = draw_text(buf, hi_s, 10, 10, HI_C)
    lo_x = W - text_width(lo_s)
    draw_text(buf, lo_s, lo_x, 10, LO_C)
    if lo_x - hi_end >= 5:
        draw_text(buf, "/", hi_end + (lo_x - hi_end - 3) // 2, 10, DIM)

    prob = wx.get("precip_prob", 0) or 0
    dots = min(8, (prob + 12) // 13)
    color = SNOW if precip == "snow" else RAIN
    for i in range(8):
        buf[(i, 15)] = color if i < dots else (8, 8, 12)
    if dots and frame_no % 2:
        buf[(dots - 1, 15)] = (255, 255, 255) if precip == "snow" else (120, 180, 255)
    return buf

def render_tomorrow(wx, frame_no):
    """Page 2: tomorrow's icon + hi/lo, labeled TMRW."""
    buf = {}
    frames, precip, _ = icon_for(wx["tmrw_code"], True)
    draw_icon(buf, frames, frame_no, 0, 0)
    draw_text(buf, "TMRW", 10, 1, (200, 200, 200))
    hi_s, lo_s = str(int(round(wx["tmrw_hi"]))), str(int(round(wx["tmrw_lo"])))
    hi_end = draw_text(buf, hi_s, 10, 10, HI_C)
    lo_x = W - text_width(lo_s)
    draw_text(buf, lo_s, lo_x, 10, LO_C)
    if lo_x - hi_end >= 5:
        draw_text(buf, "/", hi_end + (lo_x - hi_end - 3) // 2, 10, DIM)
    prob = wx.get("tmrw_precip", 0) or 0
    dots = min(8, (prob + 12) // 13)
    color = SNOW if precip == "snow" else RAIN
    for i in range(8):
        buf[(i, 15)] = color if i < dots else (8, 8, 12)
    return buf

MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
DAYS   = ["MON","TUE","WED","THU","FRI","SAT","SUN"]

def render_clock(t, frame_no):
    """Page 3: time (12h) on top, weekday + date below. t = time.struct_time."""
    buf = {}
    h, m = t.tm_hour, t.tm_min
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    x = 2 if h12 >= 10 else 4
    x = draw_text(buf, str(h12), x, 1, CLOCK)      # hour, then a 1-px colon slot
    if frame_no % 2 == 0:                           # blink the dots only; slot never moves
        buf[(x, 2)] = CLOCK
        buf[(x, 4)] = CLOCK
    x += 2                                          # past the colon slot + gap
    x = draw_text(buf, f"{m:02d}", x, 1, CLOCK)
    draw_text(buf, ampm, x + 1, 1, (120, 90, 60))
    draw_text(buf, DAYS[t.tm_wday], 0, 10, DATE)
    date = f"{t.tm_mon}/{t.tm_mday}"
    draw_text(buf, date, W - text_width(date), 10, DATE)
    return buf

def render_ticker(wx, frame_no, message, offset):
    """Page 4: current icon + temp on top, message scrolling across the bottom.
    offset = pixel column where the message starts (decreasing each frame)."""
    buf = {}
    frames, _, _ = icon_for(wx["code"], wx["is_day"])
    draw_icon(buf, frames, frame_no, 0, 0)
    t = int(round(wx["temp"]))
    x = draw_text(buf, str(t), 10, 1, temp_color(t))
    draw_text(buf, "°", x, 1, temp_color(t))
    draw_text(buf, message, offset, 10, TICK)
    return buf

def render_message(message, offset, color=TICK):
    """A bare scrolling message, vertically centered (used at startup)."""
    buf = {}
    draw_text(buf, message, offset, 5, color)
    return buf

def message_for(wx):
    """Build the ticker sentence from the forecast."""
    _, precip, desc = icon_for(wx["code"], wx["is_day"])
    parts = [desc]
    prob = wx.get("precip_prob", 0) or 0
    if prob >= 30:
        kind = "SNOW" if precip == "snow" else "RAIN"
        parts.append(f"{kind} {int(prob)}%")
    _, _, tdesc = icon_for(wx["tmrw_code"], True)
    parts.append(f"TOMORROW {tdesc} {int(round(wx['tmrw_hi']))}/{int(round(wx['tmrw_lo']))}")
    return "   ".join(parts)

def slide(old, new, step, steps=16):
    """Vertical slide transition: old moves up, new enters from below."""
    buf = {}
    for (x, y), c in old.items():
        if y - step >= 0:
            buf[(x, y - step)] = c
    for (x, y), c in new.items():
        if y + (steps - step) < H:
            buf[(x, y + (steps - step))] = c
    return buf
