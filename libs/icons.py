"""Линейные иконки в стиле Feather, нарисованные через PIL.

Tk не умеет SVG, а эмодзи задание запрещает. Поэтому каждая иконка описана
примитивами в системе координат 24×24 (той же, что viewBox исходных SVG) и
растеризуется в CTkImage с прозрачным фоном — так одна иконка ложится на любую
подложку и не требует подгонки цвета фона.

Рисуем с четырёхкратным увеличением и уменьшаем LANCZOS: PIL не умеет
сглаживать линии, и это единственный способ получить ровные края.
"""

from PIL import Image, ImageDraw, ImageTk
import customtkinter as ctk

from libs import theme

SS = 4          # кратность супер-сэмплинга
BOX = 24.0      # система координат описаний

# Каждая иконка — список примитивов:
#   line  (x1,y1,x2,y2)              обводка
#   poly  ([(x,y)...], closed)       ломаная обводкой
#   circ  (cx,cy,r)                  окружность обводкой
#   rect  (x,y,w,h,r)                прямоугольник обводкой
#   arc   (cx,cy,r,start,end)        дуга обводкой
#   fpoly ([(x,y)...])               заливка
#   fcirc (cx,cy,r)                  заливка
#   frect (x,y,w,h,r)                заливка
ICONS = {
    "music": [("poly", [(9, 18), (9, 5), (21, 3), (21, 16)], False),
              ("circ", 6, 18, 3), ("circ", 18, 16, 3)],
    "star": [("poly", [(12, 2), (15.09, 8.26), (22, 9.27), (17, 14.14), (18.18, 21.02),
                       (12, 17.77), (5.82, 21.02), (7, 14.14), (2, 9.27), (8.91, 8.26)], True)],
    "star_filled": [("fpoly", [(12, 2), (15.09, 8.26), (22, 9.27), (17, 14.14), (18.18, 21.02),
                               (12, 17.77), (5.82, 21.02), (7, 14.14), (2, 9.27), (8.91, 8.26)])],
    "clock": [("circ", 12, 12, 10), ("poly", [(12, 6), (12, 12), (16, 14)], False)],
    "plus": [("line", 12, 5, 12, 19), ("line", 5, 12, 19, 12)],
    "search": [("circ", 11, 11, 7), ("line", 21, 21, 16.65, 16.65)],
    "list": [("line", 8, 6, 21, 6), ("line", 8, 12, 21, 12), ("line", 8, 18, 21, 18),
             ("fcirc", 3.2, 6, 1.1), ("fcirc", 3.2, 12, 1.1), ("fcirc", 3.2, 18, 1.1)],
    "grid": [("rect", 3, 3, 7, 7, 1.5), ("rect", 14, 3, 7, 7, 1.5),
             ("rect", 3, 14, 7, 7, 1.5), ("rect", 14, 14, 7, 7, 1.5)],
    "settings": [("circ", 12, 12, 3.2), ("circ", 12, 12, 8)] +
                [("line", 12, 12, 12, 12) for _ in ()] +
                [("line",
                  12 + 8 * __import__("math").cos(__import__("math").radians(a)),
                  12 + 8 * __import__("math").sin(__import__("math").radians(a)),
                  12 + 10.6 * __import__("math").cos(__import__("math").radians(a)),
                  12 + 10.6 * __import__("math").sin(__import__("math").radians(a)))
                 for a in range(0, 360, 45)],
    "mic": [("rect", 9, 2, 6, 12, 3), ("arc", 12, 10, 7, 0, 180), ("line", 12, 17, 12, 22)],
    "cable": [("rect", 7, 7, 10, 10, 1.5), ("line", 3, 12, 7, 12), ("line", 17, 12, 21, 12)],
    "headphones": [("arc", 12, 13, 9, 180, 360), ("line", 3, 13, 3, 18), ("line", 21, 13, 21, 18),
                   ("rect", 1.5, 14, 4, 7, 2), ("rect", 18.5, 14, 4, 7, 2)],
    "sort": [("line", 3, 6, 21, 6), ("line", 6, 12, 18, 12), ("line", 10, 18, 14, 18)],
    "play": [("fpoly", [(7, 4.5), (20.5, 12), (7, 19.5)])],
    "pause": [("frect", 6, 5, 4, 14, 1), ("frect", 14, 5, 4, 14, 1)],
    "stop": [("frect", 5, 5, 14, 14, 2)],
    "volume": [("poly", [(11, 5), (6, 9), (2, 9), (2, 15), (6, 15), (11, 19)], True),
               ("arc", 12, 12, 5, -45, 45), ("arc", 12, 12, 10, -45, 45)],
    "download": [("poly", [(21, 15), (21, 20), (19, 21), (5, 21), (3, 20), (3, 15)], False),
                 ("poly", [(7, 10), (12, 15), (17, 10)], False), ("line", 12, 15, 12, 3)],
    "dots": [("fcirc", 5, 12, 1.6), ("fcirc", 12, 12, 1.6), ("fcirc", 19, 12, 1.6)],
    "close": [("line", 6, 6, 18, 18), ("line", 18, 6, 6, 18)],
    "eq": [("frect", 5, 9, 3, 10, 1.5), ("frect", 10, 3, 3, 18, 1.5),
           ("frect", 15, 7, 3, 13, 1.5), ("frect", 20, 12, 3, 7, 1.5)],
    "trash": [("line", 3, 6, 21, 6), ("poly", [(19, 6), (18, 21), (6, 21), (5, 6)], False),
              ("poly", [(9, 6), (9, 3), (15, 3), (15, 6)], False)],
    "check": [("poly", [(4, 12.5), (9.5, 18), (20, 6)], False)],
}

def _rgba(color):
    """#RGB и #RRGGBB в кортеж RGBA. Короткую форму поддерживаем потому, что
    она законна в CSS и легко попадёт сюда из токенов при правке темы."""
    h = color.lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"нераспознанный цвет: {color!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


_cache = {}


def _render(name, px, color, stroke):
    """Растеризовать одну иконку в RGBA нужного цвета."""
    spec = ICONS[name]
    s = px * SS / BOX
    w = int(px * SS)
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sw = max(1, int(round(stroke * s)))
    rgb = _rgba(color)

    def P(x, y):
        return (x * s, y * s)

    for item in spec:
        kind = item[0]
        if kind == "line":
            d.line([P(item[1], item[2]), P(item[3], item[4])], fill=rgb, width=sw)
        elif kind == "poly":
            pts = [P(x, y) for x, y in item[1]]
            if item[2]:
                pts.append(pts[0])
            d.line(pts, fill=rgb, width=sw, joint="curve")
        elif kind == "circ":
            cx, cy, r = item[1], item[2], item[3]
            d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=rgb, width=sw)
        elif kind == "rect":
            x, y, ww, hh, r = item[1], item[2], item[3], item[4], item[5]
            d.rounded_rectangle([P(x, y), P(x + ww, y + hh)], radius=r * s, outline=rgb, width=sw)
        elif kind == "arc":
            cx, cy, r = item[1], item[2], item[3]
            d.arc([P(cx - r, cy - r), P(cx + r, cy + r)], item[4], item[5], fill=rgb, width=sw)
        elif kind == "fpoly":
            d.polygon([P(x, y) for x, y in item[1]], fill=rgb)
        elif kind == "fcirc":
            cx, cy, r = item[1], item[2], item[3]
            d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], fill=rgb)
        elif kind == "frect":
            x, y, ww, hh, r = item[1], item[2], item[3], item[4], item[5]
            d.rounded_rectangle([P(x, y), P(x + ww, y + hh)], radius=r * s, fill=rgb)

    return img.resize((px, px), Image.LANCZOS)


def icon(name, size=18, token="text_2", stroke=2.0, light=None, dark=None):
    """CTkImage с раздельными вариантами для светлой и тёмной темы.

    CustomTkinter сам подставит нужный при переключении оформления, поэтому
    вызывающему коду не надо знать текущий режим.
    """
    lc = light or theme.hexc(token, "light")
    dc = dark or theme.hexc(token, "dark")
    key = (name, size, lc, dc, stroke)
    if key not in _cache:
        _cache[key] = ctk.CTkImage(light_image=_render(name, size, lc, stroke),
                                   dark_image=_render(name, size, dc, stroke),
                                   size=(size, size))
    return _cache[key]


_photo_cache = {}


def photo(name, size=18, token="text_2", stroke=2.0):
    """PhotoImage для лёгких tk-виджетов (tkinter.Label) — цвет по текущей теме.

    Строки списка звуков собраны из обычных tk-виджетов, а не из CTk: их 80
    штук, и CTkButton/CTkLabel с внутренним Canvas у каждого делали перестройку
    списка тяжёлой. CTkImage сюда не подходит — ему нужен CTk-виджет.
    Кэш ключуется по конкретному hex, поэтому после смены темы возьмётся
    картинка нужного цвета.
    """
    color = theme.hexc(token)
    key = (name, size, color, stroke)
    if key not in _photo_cache:
        _photo_cache[key] = ImageTk.PhotoImage(_render(name, size, color, stroke))
    return _photo_cache[key]
