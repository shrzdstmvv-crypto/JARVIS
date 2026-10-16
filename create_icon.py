from PIL import Image, ImageDraw, ImageFont


SIZE = 1024

image = Image.new(
    "RGB",
    (SIZE, SIZE),
    (0, 0, 0)
)

draw = ImageDraw.Draw(image)


# Font
font_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
]

font = None

for path in font_paths:
    try:
        font = ImageFont.truetype(
            path,
            760
        )
        break
    except Exception:
        pass

if font is None:
    font = ImageFont.load_default()


# J harfining o'lchami
text = "J"

bbox = draw.textbbox(
    (0, 0),
    text,
    font=font
)

text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (SIZE - text_width) // 2 - bbox[0]
y = (SIZE - text_height) // 2 - bbox[1]


# J harfi
draw.text(
    (x, y),
    text,
    font=font,
    fill=(220, 0, 0)
)


# Yengil qizil glow
glow = Image.new(
    "RGBA",
    (SIZE, SIZE),
    (0, 0, 0, 0)
)

glow_draw = ImageDraw.Draw(glow)

glow_draw.text(
    (x, y),
    text,
    font=font,
    fill=(255, 0, 0, 90)
)

from PIL import ImageFilter

glow = glow.filter(
    ImageFilter.GaussianBlur(18)
)

image = Image.alpha_composite(
    image.convert("RGBA"),
    glow
)


# Asosiy J yana ustidan chiziladi
draw = ImageDraw.Draw(image)

draw.text(
    (x, y),
    text,
    font=font,
    fill=(220, 0, 0)
)


# PNG sifatida saqlash
image = image.convert("RGB")

image.save(
    "jarvis_icon.png",
    "PNG",
    optimize=True
)

print("jarvis_icon.png yaratildi.")