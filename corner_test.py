# Verifies the panel mapping in weather_gfx.xy(): four colored corners, the
# seam between the panels, then a gray border around the whole 32x16 display.
import board, neopixel, time
import weather_gfx as gfx

panel = neopixel.NeoPixel(board.GPIO15, 512, brightness=0.1, auto_write=False)

tests = [
    ("top-left     RED",      0,  0, (255, 0, 0)),
    ("top-right    GREEN",   31,  0, (0, 255, 0)),
    ("bottom-left  BLUE",     0, 15, (0, 0, 255)),
    ("bottom-right WHITE",   31, 15, (255, 255, 255)),
    ("seam left, upper  YELLOW",  0, 7, (255, 255, 0)),
    ("seam left, lower  CYAN",    0, 8, (0, 255, 255)),
    ("seam right, upper MAGENTA", 31, 7, (255, 0, 255)),
    ("seam right, lower ORANGE",  31, 8, (255, 80, 0)),
]
panel.fill((0, 0, 0))
for name, x, y, color in tests:
    i = gfx.xy(x, y)
    panel[i] = color
    print(f"{name:28s} x={x:2d} y={y:2d} -> index {i}")
panel.show()
time.sleep(5)

panel.fill((0, 0, 0))
for x in range(32):
    panel[gfx.xy(x, 0)] = (40, 40, 40); panel[gfx.xy(x, 15)] = (40, 40, 40)
for y in range(16):
    panel[gfx.xy(0, y)] = (40, 40, 40); panel[gfx.xy(31, y)] = (40, 40, 40)
panel.show()
while True:
    time.sleep(1)
