#!/usr/bin/env python3
"""Генерация ассетов для игры: аватар Меллстроя, фон-улица, иконка, музыка."""
import math, random, struct, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

random.seed(7)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------------- АВАТАР: голова Меллстроя в круге ----------------
src = Image.open("image-search/mellstroy-1.jpg").convert("RGB")
head = src.crop((262, 22, 408, 168)).resize((256, 256), Image.LANCZOS)

mask = Image.new("L", (256, 256), 0)
md = ImageDraw.Draw(mask)
md.ellipse((6, 6, 250, 250), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(0.6))

avatar = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
avatar.paste(head, (0, 0), mask)
# белая обводка
ring = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring)
rd.ellipse((3, 3, 253, 253), outline=(255, 255, 255, 255), width=8)
avatar = Image.alpha_composite(avatar, ring)
avatar.save("out/img/mell_avatar.png")
avatar.resize((48, 48), Image.LANCZOS).save("out/img/mell_avatar_small.png")

# ---------------- ФОН: ночная улица с силуэтами ----------------
W, H = 720, 1280
bg = Image.new("RGB", (W, H))
px = bg.load()
# градиент ночного неба
for y in range(H):
    t = y / H
    r = int(12 + 40 * t)
    g = int(8 + 14 * t)
    b = int(42 + 66 * t)
    for x in range(W):
        px[x, y] = (r, g, b)

d = ImageDraw.Draw(bg, "RGBA")
# звёзды
for _ in range(140):
    x, y = random.randint(0, W), random.randint(0, int(H * 0.45))
    s = random.choice([1, 1, 1, 2])
    a = random.randint(60, 200)
    d.ellipse((x, y, x + s, y + s), fill=(255, 255, 255, a))
# луна
d.ellipse((520, 90, 640, 210), fill=(255, 246, 210, 235))
d.ellipse((545, 78, 690, 200), fill=(14, 10, 48, 255))
# дальние дома
def skyline(base_y, color, bw_min, bw_max, h_min, h_max):
    x = -20
    while x < W + 20:
        bw = random.randint(bw_min, bw_max)
        bh = random.randint(h_min, h_max)
        d.rectangle((x, base_y - bh, x + bw, base_y), fill=color)
        # окна
        for wy in range(base_y - bh + 14, base_y - 10, 26):
            for wx in range(x + 8, x + bw - 10, 20):
                if random.random() < 0.42:
                    c = random.choice([(255, 220, 120, 210), (255, 190, 90, 190),
                                       (160, 220, 255, 180), (255, 120, 220, 160)])
                    d.rectangle((wx, wy, wx + 7, wy + 11), fill=c)
        x += bw + random.randint(4, 16)

skyline(760, (18, 16, 52, 255), 60, 110, 120, 320)   # дальний ряд
skyline(840, (10, 9, 32, 255), 80, 140, 80, 260)     # ближний ряд
# земля
d.rectangle((0, 830, W, 900), fill=(24, 20, 40, 255))
d.rectangle((0, 830, W, 836), fill=(90, 80, 140, 255))
# разметка дороги (перспектива)
for i in range(-6, 14):
    x1 = W // 2 + i * 90
    d.polygon([(x1, 900), (x1 + 40, 900), (W // 2 + i * 220 - 8, H),
               (W // 2 + i * 220 + 8, H)], fill=(70, 62, 110, 120))
# нижняя заливка под трубы остаётся тёмной
d.rectangle((0, 900, W, H), fill=(12, 10, 26, 255))
for i in range(-6, 14):
    x1 = W // 2 + i * 90
    d.polygon([(x1, 900), (x1 + 40, 900), (W // 2 + i * 220 - 8, H),
               (W // 2 + i * 220 + 8, H)], fill=(70, 62, 110, 140))
bg.save("out/img/bg_street.png")

# ---------------- ИКОНКА 512 ----------------
icon = Image.new("RGB", (512, 512), (18, 14, 48))
d = ImageDraw.Draw(icon, "RGBA")
for y in range(512):
    t = y / 512
    d.line((0, y, 512, y), fill=(int(14 + 50 * t), int(10 + 20 * t), int(50 + 90 * t)))
for _ in range(60):
    x, y = random.randint(0, 512), random.randint(0, 300)
    d.ellipse((x, y, x + 2, y + 2), fill=(255, 255, 255, random.randint(80, 220)))
# трубы
for i, cx in enumerate((150, 256, 362)):
    d.rounded_rectangle((cx - 42, 170 + i * 30, cx + 42, 470), radius=16,
                        fill=(34, 200, 100, 255), outline=(180, 255, 200, 255), width=6)
    d.rounded_rectangle((cx - 42, 170 + i * 30, cx + 42, 196 + i * 30), radius=12, fill=(200, 255, 215, 255))
av = Image.open("out/img/mell_avatar.png").resize((190, 190), Image.LANCZOS)
icon.paste(av, (256 - 95, 60), av)
icon.save("out/img/icon_512.png")
for s in (192, 144, 96, 72, 48):
    icon.resize((s, s), Image.LANCZOS).save(f"out/img/icon_{s}.png")

# ---------------- ИГРОК-СПРАЙТ (маленький, для полосы) ----------------
av_small = Image.open("out/img/mell_avatar.png").resize((96, 96), Image.LANCZOS)
av_small.save("out/img/mell_small.png")

# ---------------- МУЗЫКА: 4-сек луп (чиптюн-бит) ----------------
SR = 22050
dur = 4.0
n = int(SR * dur)
buf = [0.0] * n
BPM = 120
beat = 60.0 / BPM


def add_tone(start, length, freq, vol, wave_type="square", decay=True):
    s0 = int(start * SR)
    ln = int(length * SR)
    for i in range(ln):
        idx = s0 + i
        if idx >= n:
            break
        t = i / SR
        env = (1 - i / ln) ** (2.0 if decay else 0.2)
        ph = (t * freq) % 1.0
        if wave_type == "square":
            v = 1.0 if ph < 0.5 else -1.0
        elif wave_type == "saw":
            v = 2 * ph - 1
        else:
            v = math.sin(2 * math.pi * ph)
        buf[idx] += v * vol * env


def add_kick(start, vol=0.55):
    s0 = int(start * SR)
    ln = int(0.16 * SR)
    for i in range(ln):
        idx = s0 + i
        if idx >= n:
            break
        t = i / SR
        f = 120 * math.exp(-t * 24) + 38
        env = math.exp(-t * 16)
        buf[idx] += math.sin(2 * math.pi * f * t) * vol * env


def add_hat(start, vol=0.12):
    s0 = int(start * SR)
    ln = int(0.05 * SR)
    for i in range(ln):
        idx = s0 + i
        if idx >= n:
            break
        env = math.exp(-i / ln * 5)
        buf[idx] += (random.random() * 2 - 1) * vol * env


# басовая линия: A minor riff
bass = [110, 110, 131, 131, 98, 98, 110, 110]
for b in range(8):
    add_tone(b * beat * 0.5, beat * 0.48, bass[b], 0.16, "square")
# мелодия
mel = [(0.0, 440), (0.5, 523), (1.0, 659), (1.5, 523), (2.0, 440), (2.5, 392),
       (3.0, 440), (3.5, 523)]
for t0, f in mel:
    add_tone(t0, beat * 0.42, f, 0.10, "saw")
# барабаны
for b in range(8):
    add_kick(b * beat * 0.5)
for i in range(16):
    add_hat(i * beat * 0.25)

peak = max(abs(v) for v in buf) or 1
with wave.open("out/raw/flap_beat.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * 0.85)) * 32767)) for v in buf))
print("assets ok")
