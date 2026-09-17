# Renders the display pages to preview.png on a computer (pip install pillow).
# Run:  python3 preview.py
from PIL import Image, ImageDraw
import time
import weather_gfx as g

wx = dict(temp=61, hi=68, lo=52, code=0, is_day=False, precip_prob=10,
          tmrw_hi=74, tmrw_lo=58, tmrw_code=61, tmrw_precip=80)
t = time.struct_time((2026, 9, 17, 10, 42, 0, 3, 260, -1))
msg = g.message_for(wx)
shots = [
    ("Today (three frames)", [g.render_weather(wx, f) for f in range(3)]),
    ("Clock", [g.render_clock(t, f) for f in range(2)]),
    ("Tomorrow", [g.render_tomorrow(wx, f) for f in range(2)]),
    ("Ticker", [g.render_ticker(wx, 0, msg, x) for x in (10, -20, -60)]),
    ("Slide transition", [g.slide(g.render_weather(wx, 0), g.render_clock(t, 0), s) for s in (4, 8, 12)]),
]
S, gap = 12, 4
img = Image.new("RGB", ((32 * S + gap) * 3 + 8, (16 * S + 20 + gap) * len(shots) + 6), (20, 20, 20))
d = ImageDraw.Draw(img)
y0 = 4
for title, bufs in shots:
    d.text((6, y0), title, fill=(200, 200, 200))
    for i, buf in enumerate(bufs):
        x0 = 6 + i * (32 * S + gap)
        for y in range(16):
            for x in range(32):
                c = buf.get((x, y), (16, 16, 16))
                d.ellipse([x0 + x * S + 2, y0 + 18 + y * S + 2, x0 + x * S + S - 3, y0 + 18 + y * S + S - 3], fill=c)
    y0 += 16 * S + 20 + gap
img.save("preview.png")
print("wrote preview.png", img.size)
