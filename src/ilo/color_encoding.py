import colorsys
import math
import webcolors

BASIC_COLOR_NAMES = [
    "Blue",
    "Yellow",
    "Magenta",
    "Cyan",
    "Orange",
    "Purple",
    "Pink",
    "Dark Green",
    "White",
    "Deep Pink",
    "Cornflower Blue",
]


def expand_4bit(v: int) -> int:
    return (v * 255 + 7) // 14


def base62_value(c: str) -> int:
    if '0' <= c <= '9':
        return ord(c) - ord('0')
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if 'a' <= c <= 'z':
        return ord(c) - ord('a') + 36
    return 0


def base62_to_rgb(s: str):
    index = base62_value(s[0]) * 62 + base62_value(s[1])

    rq = (index >> 8) & 0x0F
    gq = (index >> 4) & 0x0F
    bq = index & 0x0F

    r = expand_4bit(rq)
    g = expand_4bit(gq)
    b = expand_4bit(bq)

    return r, g, b


def closest_color_name(rgb: tuple[int, int, int]) -> str:
    def convert(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        r, g, b = rgb
        return colorsys.rgb_to_hsv(r / 256, g / 256, b / 256)

    target_col = convert(rgb)

    min_distance = float("inf")
    closest_name = "black"

    colors = webcolors.names()

    for name in colors:
        r, g, b = webcolors.name_to_rgb(name)
        col = convert((r, g, b))

        distance = math.sqrt(
            sum(
                (b - a) ** 2 for a, b in zip(col, target_col)
            )
        )

        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name


def base62_to_name(c: str) -> str:
    rgb = base62_to_rgb(c)
    return closest_color_name(rgb)


__all__ = ("BASIC_COLOR_NAMES","base62_to_rgb",)
