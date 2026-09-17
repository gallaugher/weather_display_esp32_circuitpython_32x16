# 32x16 NeoPixel weather display  (two 32x8 panels, lower one rotated 180)
# Board: YD-ESP32-S3 N16R8, CircuitPython 10.x
# Wiring: panel DIN -> GPIO15, panel GND -> ESP32 GND, panel power from a 5V 4A brick
# Files:  code.py, weather_gfx.py, settings.toml (Wi-Fi, LOCATION, UNITS)
# Libs:   adafruit_requests, adafruit_connection_manager, adafruit_ntp  (in /lib)
# Data:   Open-Meteo (free, no API key); time from NTP
#
# Pages cycle:  WEATHER (today) -> CLOCK -> TOMORROW -> TICKER (scrolling summary)

import time, os, json, rtc
import board, neopixel, wifi, socketpool, ssl
import adafruit_requests, adafruit_ntp
import weather_gfx as gfx

# ---------------- settings (location and units come from settings.toml) ----------------
#   LOCATION = "02467"            a postal code or a place name, e.g. "Newton, MA", "Lisbon, Portugal"
#   UNITS    = "F"                "F" or "C"
#   LAT / LON                     optional: skip the lookup and use these coordinates
LOCATION = os.getenv("LOCATION") or "Boston College"
UNITS    = (os.getenv("UNITS") or "F").upper()
LAT, LON = os.getenv("LAT"), os.getenv("LON")
gfx.UNITS = UNITS

REFRESH_SEC   = 600                    # weather refresh
NTP_SEC       = 3600                   # clock resync
BRIGHT_DAY    = 0.12                   # 512 px on a 4 A brick: keep <= 0.12 for all colors
BRIGHT_NIGHT  = 0.05
PAGE_SEC      = {"weather": 10, "clock": 6, "tomorrow": 6}
ICON_FRAME    = 0.4                    # icon animation step
SCROLL_STEP   = 0.06                   # ticker: seconds per pixel
PAGES         = ["weather", "clock", "tomorrow", "ticker"]

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&name="

def weather_url(lat, lon):
    unit = "celsius" if UNITS == "C" else "fahrenheit"
    return ("https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code,is_day"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
            f"&temperature_unit={unit}&timezone=auto&forecast_days=2")

pixels = neopixel.NeoPixel(board.GPIO15, 512, brightness=BRIGHT_DAY, auto_write=False)

def show(buf):
    pixels.fill((0, 0, 0))
    for (x, y), color in buf.items():
        pixels[gfx.xy(x, y)] = color
    pixels.show()

def show_text(msg, color=(80, 80, 80)):
    buf = {}
    gfx.draw_text_centered(buf, msg, 5, color)
    show(buf)

# ---------------- Wi-Fi ----------------
show_text("WIFI", (60, 60, 200))
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
pwd  = os.getenv("CIRCUITPY_WIFI_PASSWORD") or ""
print("Connecting to", ssid)
while True:
    try:
        wifi.radio.connect(ssid, pwd)
        break
    except Exception as e:
        print("Wi-Fi failed:", e, "- retrying")
        show_text("WIFI", (200, 40, 40))
        time.sleep(5)
print("Connected, IP", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
utc_offset = 0                          # seconds; comes from Open-Meteo (handles DST)

def url_quote(s):
    return "".join(ch if ch.isalpha() or ch.isdigit() else "%%%02X" % ord(ch) for ch in s)

def scroll_message(msg, color=(200, 200, 200)):
    width = gfx.text_width(msg)
    for x in range(gfx.W, -width - 1, -1):
        show(gfx.render_message(msg, x, color))
        time.sleep(0.04)

def geocode(place):
    """place name or postal code -> (lat, lon, label). Raises on no match."""
    r = requests.get(GEO_URL + url_quote(place), timeout=15)
    data = r.json()
    r.close()
    hit = data["results"][0]
    label = hit["name"]
    if hit.get("admin1") and hit.get("country_code") == "US":
        label += " " + hit["admin1"]
    elif hit.get("country"):
        label += " " + hit["country"]
    return hit["latitude"], hit["longitude"], label

if LAT and LON:
    LAT, LON, place_label = float(LAT), float(LON), f"{LAT} {LON}"
else:
    while True:
        try:
            LAT, LON, place_label = geocode(LOCATION)
            break
        except Exception as e:
            print(f"Could not find location '{LOCATION}':", e)
            show_text("LOC?", (200, 40, 40))
            time.sleep(15)
print(f"Location: {place_label}  ({LAT}, {LON})  units {UNITS}")
scroll_message(place_label.upper())
URL = weather_url(LAT, LON)

def fetch_weather(first=False):
    global utc_offset
    r = requests.get(URL, timeout=15)
    data = r.json()
    r.close()
    if first:
        print(json.dumps(data))
    utc_offset = int(data.get("utc_offset_seconds", 0))
    cur, day = data["current"], data["daily"]
    return {
        "temp":        cur["temperature_2m"],
        "code":        int(cur["weather_code"]),
        "is_day":      bool(cur.get("is_day", 1)),
        "hi":          day["temperature_2m_max"][0],
        "lo":          day["temperature_2m_min"][0],
        "precip_prob": (day.get("precipitation_probability_max") or [0])[0] or 0,
        "tmrw_hi":     day["temperature_2m_max"][1],
        "tmrw_lo":     day["temperature_2m_min"][1],
        "tmrw_code":   int(day["weather_code"][1]),
        "tmrw_precip": (day.get("precipitation_probability_max") or [0, 0])[1] or 0,
    }

def sync_clock():
    ntp = adafruit_ntp.NTP(pool, tz_offset=utc_offset / 3600, cache_seconds=NTP_SEC)
    rtc.RTC().datetime = ntp.datetime
    t = time.localtime()
    print(f"Clock set: {t.tm_hour:02d}:{t.tm_min:02d}  {t.tm_mon}/{t.tm_mday}")

# ---------------- main loop ----------------
wx = None
last_fetch = -REFRESH_SEC
last_ntp = -NTP_SEC
clock_ok = False
first = True

page_i = 0
page_start = time.monotonic()
frame = 0
last_frame = 0.0
ticker_msg = ""
ticker_x = gfx.W
last_scroll = 0.0
current_buf = {}

def render_page(name):
    if name == "weather":
        return gfx.render_weather(wx, frame)
    if name == "tomorrow":
        return gfx.render_tomorrow(wx, frame)
    if name == "clock":
        return gfx.render_clock(time.localtime(), frame)
    return gfx.render_ticker(wx, frame, ticker_msg, ticker_x)

def next_page():
    """advance with a slide transition; skip clock if NTP never succeeded"""
    global page_i, page_start, ticker_x, ticker_msg, current_buf
    old = current_buf
    while True:
        page_i = (page_i + 1) % len(PAGES)
        if PAGES[page_i] != "clock" or clock_ok:
            break
    if PAGES[page_i] == "ticker":
        ticker_msg = gfx.message_for(wx)
        ticker_x = gfx.W
    new = render_page(PAGES[page_i])
    for step in range(1, 17):
        show(gfx.slide(old, new, step))
        time.sleep(0.025)
    page_start = time.monotonic()

while True:
    now = time.monotonic()

    # ---- data refresh ----
    if now - last_fetch >= REFRESH_SEC:
        try:
            wx = fetch_weather(first)
            first = False
            last_fetch = now
            print(f"temp {wx['temp']} hi {wx['hi']} lo {wx['lo']} code {wx['code']} "
                  f"day {wx['is_day']} precip {wx['precip_prob']}% | "
                  f"tmrw {wx['tmrw_hi']}/{wx['tmrw_lo']} code {wx['tmrw_code']}")
            pixels.brightness = BRIGHT_DAY if wx["is_day"] else BRIGHT_NIGHT
        except Exception as e:
            print("fetch failed:", e)
            if wx is None:
                show_text("ERR", (200, 40, 40))
            last_fetch = now - REFRESH_SEC + 30      # retry in 30 s
    if wx and now - last_ntp >= NTP_SEC:
        try:
            sync_clock()
            clock_ok = True
            last_ntp = now
        except Exception as e:
            print("NTP failed:", e)
            last_ntp = now - NTP_SEC + 60
    if not wx:
        time.sleep(0.5)
        continue

    # ---- page timing ----
    page = PAGES[page_i]
    if page == "ticker":
        if now - last_scroll >= SCROLL_STEP:
            last_scroll = now
            ticker_x -= 1
            if ticker_x < -gfx.text_width(ticker_msg):
                next_page()
                continue
    elif now - page_start >= PAGE_SEC[page]:
        next_page()
        continue

    # ---- animation frame ----
    if now - last_frame >= ICON_FRAME or page == "ticker":
        if now - last_frame >= ICON_FRAME:
            last_frame = now
            frame += 1
        current_buf = render_page(page)
        show(current_buf)

    time.sleep(0.01)
