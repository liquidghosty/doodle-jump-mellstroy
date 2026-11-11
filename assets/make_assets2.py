#!/usr/bin/env python3
"""Генерация фонов, кнопок и иконок для Doodle Jump: Меллстрой."""
import math, random, os
from PIL import Image, ImageDraw, ImageFilter

OUT = "out/assets2"
os.makedirs(OUT, exist_ok=True)
random.seed(42)

W, H = 720, 1440

# ---------------------------------------------------------------- helpers
def tile_star(img, x, y, r, col=(255, 255, 255, 220)):
    """Рисует звезду с вертикальной закольцовкой (бесшовная плитка)."""
    d = ImageDraw.Draw(img, "RGBA")
    for yy in (y, y - H, y + H):
        if -8 < yy < H + 8:
            d.ellipse((x - r, yy - r, x + r, yy + r), fill=col)


def soft_blob(img, cx, cy, rx, ry, col):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for yy in (cy, cy - H, cy + H):
        d.ellipse((cx - rx, yy - ry, cx + rx, yy + ry), fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(38))
    img.alpha_composite(layer)


# ---------------------------------------------------------------- ЗВЁЗДНОЕ НЕБО (город)
sky = Image.new("RGBA", (W, H), (0, 0, 0, 255))
d = ImageDraw.Draw(sky, "RGBA")
for y in range(H):
    t = y / H
    d.line((0, y, W, y), fill=(int(16 + 20 * t), int(12 + 14 * t), int(52 + 40 * t), 255))
for _ in range(260):
    tile_star(sky, random.randint(0, W), random.randint(0, H),
               random.choice([1, 1, 1, 1.6, 2.2]), (255, 255, 255, random.randint(90, 230)))
# млечный путь
soft_blob(sky, 520, 300, 240, 120, (120, 110, 255, 26))
soft_blob(sky, 180, 900, 260, 140, (90, 140, 255, 20))
sky.convert("RGB").save(f"{OUT}/bg_stars.png", optimize=True)

# ---------------------------------------------------------------- КОСМОС
sp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
d = ImageDraw.Draw(sp, "RGBA")
for y in range(H):
    t = y / H
    d.line((0, y, W, y), fill=(int(10 + 16 * t), int(6 + 8 * t), int(30 + 26 * t), 255))
soft_blob(sp, 540, 240, 260, 170, (168, 90, 255, 46))
soft_blob(sp, 150, 720, 220, 160, (60, 170, 255, 40))
soft_blob(sp, 420, 1180, 260, 150, (255, 90, 190, 34))
for _ in range(320):
    tile_star(sp, random.randint(0, W), random.randint(0, H),
              random.choice([1, 1, 1.5, 2]), (255, 255, 255, random.randint(80, 240)))
# планета
d.ellipse((470, 540, 700, 770), fill=(255, 170, 120, 235))
d.ellipse((470, 540, 700, 770), outline=(255, 225, 190, 160), width=6)
d.ellipse((520, 580, 590, 640), fill=(240, 140, 100, 190))
d.ellipse((610, 660, 660, 700), fill=(240, 140, 100, 160))
# кольцо
for i, a in enumerate((70, 50, 30)):
    d.ellipse((430 + i * 8, 600 + i * 10, 740 - i * 8, 720 - i * 8),
              outline=(255, 220, 190, a), width=7)
sp.convert("RGB").save(f"{OUT}/bg_space.png", optimize=True)

# ---------------------------------------------------------------- ЗАКАТ
su = Image.new("RGBA", (W, H), (0, 0, 0, 255))
d = ImageDraw.Draw(su, "RGBA")
top = (255, 148, 108)
mid = (255, 196, 130)
bot = (255, 232, 190)
for y in range(H):
    t = y / H
    if t < 0.55:
        k = t / 0.55
        c = tuple(int(top[i] + (mid[i] - top[i]) * k) for i in range(3))
    else:
        k = (t - 0.55) / 0.45
        c = tuple(int(mid[i] + (bot[i] - mid[i]) * k) for i in range(3))
    d.line((0, y, W, y), fill=c + (255,))
# солнце
d.ellipse((250, 470, 470, 690), fill=(255, 246, 214, 255))
d.ellipse((250, 470, 470, 690), outline=(255, 255, 235, 140), width=10)
# облака (бесшовные)
for _ in range(14):
    cx = random.randint(-80, W + 80)
    cy = random.randint(0, H)
    rw = random.randint(90, 220)
    rh = random.randint(20, 44)
    col = (255, 255, 255, random.randint(40, 90))
    layer = Image.new("RGBA", su.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer, "RGBA")
    for yy in (cy, cy - H, cy + H):
        dl.ellipse((cx - rw, yy - rh, cx + rw, yy + rh), fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    su.alpha_composite(layer)
su.convert("RGB").save(f"{OUT}/bg_sunset.png", optimize=True)

# ---------------------------------------------------------------- ГОРОД (полоска у земли)
CW, CH = 720, 520
city = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
d = ImageDraw.Draw(city, "RGBA")
x = -30
while x < CW + 40:
    bw = random.randint(70, 130)
    bh = random.randint(150, 420)
    y0 = CH - bh
    shade = random.choice([(22, 20, 54), (28, 24, 66), (16, 15, 44)])
    d.rectangle((x, y0, x + bw, CH), fill=shade + (255,))
    # окна
    for wy in range(y0 + 16, CH - 16, 26):
        for wx in range(x + 10, x + bw - 12, 22):
            if random.random() < 0.45:
                col = random.choice([(255, 220, 130), (255, 190, 110), (150, 220, 255), (255, 130, 210)])
                d.rectangle((wx, wy, wx + 8, wy + 12), fill=col + (random.randint(150, 235),))
    # крыша
    d.rectangle((x, y0, x + bw, y0 + 8), fill=(58, 50, 96, 255))
    if random.random() < 0.25:
        d.line((x + bw // 2, y0, x + bw // 2, y0 - 40), fill=(90, 80, 130, 255), width=4)
        d.ellipse((x + bw // 2 - 4, y0 - 48, x + bw // 2 + 4, y0 - 40), fill=(255, 90, 90, 255))
    x += bw + random.randint(6, 18)
# земляная полоса
d.rectangle((0, CH - 24, CW, CH), fill=(30, 26, 60, 255))
d.rectangle((0, CH - 24, CW, CH - 18), fill=(92, 82, 140, 255))
city.save(f"{OUT}/bg_city_strip.png", optimize=True)

# ---------------------------------------------------------------- КНОПКИ (9-patch)
def make_button(name, c_light, c_main, c_dark, border=(52, 62, 44, 255)):
    bw, bh, r = 240, 120, 34
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # тень
    d.rounded_rectangle((4, 8, bw - 4, bh - 2), radius=r, fill=(0, 0, 0, 40))
    # корпус с градиентом
    body = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    db = ImageDraw.Draw(body, "RGBA")
    for y in range(bh):
        t = y / bh
        if t < 0.5:
            k = t / 0.5
            c = tuple(int(c_light[i] + (c_main[i] - c_light[i]) * k) for i in range(3))
        else:
            k = (t - 0.5) / 0.5
            c = tuple(int(c_main[i] + (c_dark[i] - c_main[i]) * k) for i in range(3))
        db.line((0, y, bw, y), fill=c + (255,))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, bw - 2, bh - 4), radius=r - 2, fill=255)
    img.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(img, "RGBA")
    # блик сверху
    d.rounded_rectangle((12, 8, bw - 12, 30), radius=12, fill=(255, 255, 255, 70))
    # контур
    d.rounded_rectangle((2, 2, bw - 2, bh - 4), radius=r - 2, outline=border, width=4)
    img.save(f"{OUT}/btn_{name}.png", optimize=True)


make_button("green", (208, 245, 160), (143, 209, 79), (92, 152, 46))
make_button("blue", (168, 226, 255), (79, 195, 247), (38, 122, 160))
make_button("purple", (216, 178, 255), (176, 107, 255), (110, 58, 175))
make_button("orange", (255, 206, 160), (255, 138, 91), (186, 85, 46))
make_button("gray", (255, 253, 246), (232, 228, 216), (188, 182, 166))
make_button("red", (255, 180, 170), (229, 87, 76), (160, 45, 38))

# ---------------------------------------------------------------- ИКОНКИ 96x96 (белые)
IC = 96
def ic_new():
    return Image.new("RGBA", (IC, IC), (0, 0, 0, 0))

def save_ic(img, name):
    img.save(f"{OUT}/ic_{name}.png", optimize=True)

WHITE = (255, 255, 255, 255)

# шестерёнка
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
for i in range(8):
    a = i * math.pi / 4
    cx, cy = 48 + math.cos(a) * 30, 48 + math.sin(a) * 30
    d.rectangle((cx - 9, cy - 9, cx + 9, cy + 9), fill=WHITE)
d.ellipse((14, 14, 82, 82), fill=WHITE)
d.ellipse((34, 34, 62, 62), fill=(0, 0, 0, 0))
save_ic(im, "gear")

# стрелка назад
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.line((64, 20, 32, 48), fill=WHITE, width=11)
d.line((32, 48, 64, 76), fill=WHITE, width=11)
save_ic(im, "back")

# палец (касание)
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.ellipse((30, 26, 66, 62), fill=WHITE)
d.rounded_rectangle((38, 52, 58, 84), radius=10, fill=WHITE)
for r in (38, 30):
    d.arc((48 - r - 8, 48 - r - 4, 48 + r + 8, 48 + r + 4), 200, 340, fill=WHITE, width=5)
save_ic(im, "touch")

# наклон (телефон + стрелки)
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.rounded_rectangle((32, 14, 64, 82), radius=10, outline=WHITE, width=7)
d.rounded_rectangle((40, 26, 56, 62), radius=4, fill=(255, 255, 255, 110))
d.line((12, 48, 24, 48), fill=WHITE, width=6)
d.line((12, 48, 20, 40), fill=WHITE, width=6)
d.line((12, 48, 20, 56), fill=WHITE, width=6)
d.line((84, 48, 72, 48), fill=WHITE, width=6)
d.line((84, 48, 76, 40), fill=WHITE, width=6)
d.line((84, 48, 76, 56), fill=WHITE, width=6)
save_ic(im, "tilt")

# стрелки влево-вправо
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.polygon([(30, 48), (52, 26), (52, 70)], fill=WHITE)
d.polygon([(66, 48), (44, 26), (44, 70)], fill=WHITE)
save_ic(im, "arrows")

# play
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.polygon([(34, 22), (78, 48), (34, 74)], fill=WHITE)
save_ic(im, "play")

# рестарт
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.arc((18, 18, 78, 78), 40, 320, fill=WHITE, width=10)
d.polygon([(74, 12), (84, 40), (56, 36)], fill=WHITE)
save_ic(im, "restart")

# дом
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.polygon([(48, 16), (86, 50), (74, 50), (74, 82), (22, 82), (22, 50), (10, 50)], fill=WHITE)
save_ic(im, "home")

# звук вкл
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.polygon([(16, 38), (34, 38), (54, 20), (54, 76), (34, 58), (16, 58)], fill=WHITE)
d.arc((52, 26, 84, 70), 300, 60, fill=WHITE, width=7)
d.arc((60, 14, 96, 82), 300, 60, fill=WHITE, width=5)
save_ic(im, "sound_on")

# звук выкл
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.polygon([(14, 38), (32, 38), (52, 20), (52, 76), (32, 58), (14, 58)], fill=WHITE)
d.line((62, 34, 86, 62), fill=WHITE, width=8)
d.line((86, 34, 62, 62), fill=WHITE, width=8)
save_ic(im, "sound_off")

# ноты (музыка)
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.ellipse((16, 60, 40, 82), fill=WHITE)
d.ellipse((56, 52, 80, 74), fill=WHITE)
d.line((36, 70, 36, 24), fill=WHITE, width=7)
d.line((76, 62, 76, 18), fill=WHITE, width=7)
d.line((36, 24, 76, 18), fill=WHITE, width=8)
save_ic(im, "music")

# галочка
im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
d.line((20, 50, 40, 72), fill=WHITE, width=11)
d.line((40, 72, 78, 26), fill=WHITE, width=11)
save_ic(im, "check")

# плюс/минус
for name, mode in (("plus", 1), ("minus", 0)):
    im = ic_new(); d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((20, 42, 76, 54), radius=6, fill=WHITE)
    if mode:
        d.rounded_rectangle((42, 20, 54, 76), radius=6, fill=WHITE)
    save_ic(im, name)

# ---------------------------------------------------------------- ПРЕВЬЮ ФОНОВ (миниатюры)
def thumb(name, base, accent):
    tw, th_ = 240, 168
    im = Image.new("RGB", (tw, th_), base)
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(40):
        x, y = random.randint(0, tw), random.randint(0, th_)
        d.ellipse((x, y, x + 2, y + 2), fill=(255, 255, 255, random.randint(90, 220)))
    if accent:
        d.ellipse((tw - 70, 20, tw - 20, 70), fill=accent)
    d.rounded_rectangle((18, 108, 96, 126), radius=6, fill=(143, 209, 79, 255))
    d.rounded_rectangle((110, 84, 188, 102), radius=6, fill=(143, 209, 79, 255))
    d.rounded_rectangle((18, 58, 78, 76), radius=6, fill=(143, 209, 79, 255))
    im.save(f"{OUT}/thumb_{name}.png", optimize=True)


thumb("paper", (251, 247, 236), None)
# сетка на бумаге
im = Image.open(f"{OUT}/thumb_paper.png")
d = ImageDraw.Draw(im, "RGBA")
for x in range(0, 240, 16):
    d.line((x, 0, x, 168), fill=(213, 226, 238, 255))
for y in range(0, 168, 16):
    d.line((0, y, 240, y), fill=(213, 226, 238, 255))
im.save(f"{OUT}/thumb_paper.png", optimize=True)

thumb("city", (20, 16, 54), (253, 243, 201))
thumb("space", (18, 10, 44), (255, 170, 120))
thumb("sunset", (255, 190, 130), (255, 246, 214))

print("готово:", len(os.listdir(OUT)), "файлов в", OUT)
for f in sorted(os.listdir(OUT)):
    print(" ", f, os.path.getsize(os.path.join(OUT, f)) // 1024, "КБ")
