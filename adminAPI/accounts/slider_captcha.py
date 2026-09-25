"""Slider captcha (SliderCaptcha-style) backed by Django cache."""

from __future__ import annotations

import base64
import math
import random
import statistics
import uuid
from io import BytesIO
from pathlib import Path

from django.core.cache import cache
from PIL import Image, ImageDraw

CAPTCHA_TTL = 300
CAPTCHA_CACHE_PREFIX = 'slider_captcha:'

WIDTH = 278
HEIGHT = 155
SLIDER_L = 42
SLIDER_R = 9
PI = math.pi
# 与 vue3-slide-verify 默认 accuracy=5 对齐（客户端为 <=5，服务端用 > 判定）
OFFSET_TOLERANCE = 6
MIN_TRAIL_POINTS = 4

IMAGE_DIR = Path(__file__).resolve().parent / 'captcha_images'


def _load_background() -> Image.Image:
    files = sorted(IMAGE_DIR.glob('Pic*.jpg'))
    if not files:
        image = Image.new('RGB', (WIDTH, HEIGHT), color=(72, 120, 180))
        draw = ImageDraw.Draw(image)
        for _ in range(40):
            draw.line(
                (
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                ),
                fill=(
                    random.randint(120, 220),
                    random.randint(120, 220),
                    random.randint(120, 220),
                ),
                width=1,
            )
        return image
    path = random.choice(files)
    image = Image.open(path).convert('RGB')
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def _draw_puzzle_shape(draw: ImageDraw.ImageDraw, x: int, y: int, fill) -> None:
    l = SLIDER_L
    r = SLIDER_R
    draw.line([(x, y), (x + l / 2, y)], fill=fill, width=1)
    draw.pieslice(
        [x + l / 2 - r, y - r, x + l / 2 + r, y + r],
        start=130,
        end=405,
        fill=fill,
    )
    draw.line([(x + l, y), (x + l, y + l / 2)], fill=fill, width=1)
    draw.pieslice(
        [x + l - r, y + l / 2 - r, x + l + r, y + l / 2 + r],
        start=220,
        end=400,
        fill=fill,
    )
    draw.line([(x + l, y + l), (x, y + l)], fill=fill, width=1)
    draw.pieslice(
        [x - r, y + l / 2 - r, x + r, y + l / 2 + r],
        start=90,
        end=270,
        fill=fill,
    )
    draw.line([(x, y + l), (x, y)], fill=fill, width=1)


def _create_piece_mask(width: int, height: int, x: int, y: int) -> Image.Image:
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    _draw_puzzle_shape(draw, x, y, fill=255)
    return mask


def _cut_puzzle(source: Image.Image, x: int, y: int) -> tuple[Image.Image, Image.Image, int]:
    """Return background with hole, puzzle piece image, and block top offset."""
    mask = _create_piece_mask(WIDTH, HEIGHT, x, y)
    piece_full = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    piece_full.paste(source, (0, 0))
    piece_full.putalpha(mask)

    piece_w = SLIDER_L + SLIDER_R * 2 + 3
    piece_y = y - SLIDER_R * 2 - 1
    piece_crop = piece_full.crop((x - 3, piece_y, x - 3 + piece_w, piece_y + piece_w))

    # 缺口：纯色空槽（仅此处替换原图，不再叠加描边，避免看起来像多一块拼图）
    slot = Image.new('RGB', (WIDTH, HEIGHT), (236, 240, 246))
    background = Image.composite(slot, source, mask)

    return background, piece_crop, piece_y


def _to_data_url(image: Image.Image, fmt: str = 'PNG') -> str:
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    mime = 'image/png' if fmt.upper() == 'PNG' else 'image/jpeg'
    return f'data:{mime};base64,{encoded}'


def create_slider_captcha() -> dict:
    """Create slider captcha session; frontend renders puzzle via vue3-slide-verify."""
    source = _load_background()
    piece_len = SLIDER_L + SLIDER_R * 2 + 3
    x = random.randint(piece_len + 10, WIDTH - (piece_len + 10))

    captcha_id = uuid.uuid4().hex
    cache.set(
        f'{CAPTCHA_CACHE_PREFIX}{captcha_id}',
        {'x': x, 'verified': False},
        CAPTCHA_TTL,
    )
    return {
        'captcha_id': captcha_id,
        'background': _to_data_url(source),
        'offset': x,
        'width': WIDTH,
        'height': HEIGHT,
    }


def _verify_trail(trail: list) -> bool:
    """SliderCaptcha server-side trajectory check (stddev != 0)."""
    if not isinstance(trail, list) or len(trail) < MIN_TRAIL_POINTS:
        return False
    try:
        values = [int(v) for v in trail]
    except (TypeError, ValueError):
        return False
    if len(set(values)) == 1:
        return False
    try:
        return statistics.pstdev(values) != 0
    except statistics.StatisticsError:
        return False


def verify_slider_captcha(
    captcha_id: str | None,
    offset: int | float | None,
    trail: list | None,
) -> bool:
    """Verify slider offset and optional drag trail; mark captcha as verified."""
    if not captcha_id or offset is None:
        return False
    cache_key = f'{CAPTCHA_CACHE_PREFIX}{captcha_id}'
    data = cache.get(cache_key)
    if not data or data.get('verified'):
        return False
    try:
        offset_value = int(offset)
    except (TypeError, ValueError):
        return False
    expected_x = int(data['x'])
    if abs(offset_value - expected_x) > OFFSET_TOLERANCE:
        return False
    if trail is not None and not _verify_trail(trail):
        return False
    cache.set(
        cache_key,
        {'x': expected_x, 'verified': True},
        CAPTCHA_TTL,
    )
    return True


def consume_verified_captcha(captcha_id: str | None) -> bool:
    """Consume a verified captcha once during login."""
    if not captcha_id:
        return False
    cache_key = f'{CAPTCHA_CACHE_PREFIX}{captcha_id}'
    data = cache.get(cache_key)
    cache.delete(cache_key)
    return bool(data and data.get('verified'))
