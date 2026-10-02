"""Generate the neutral semantic fixtures (simple illustrations, no real brands or people).

Run once: `python tests/semantic/make_fixtures.py`. The images and expectations are then
reviewed by a human and committed; rerunning rewrites the images only.
"""
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "fixtures")
W, H = 800, 600


def canvas(bg):
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)


def red_mug_on_shelf():
    img, d = canvas((235, 225, 205))
    d.rectangle([0, 420, W, 450], fill=(139, 90, 43))  # shelf
    d.rectangle([330, 320, 460, 420], fill=(190, 40, 40))  # mug body
    d.arc([440, 340, 510, 400], -90, 90, fill=(190, 40, 40), width=14)  # handle
    d.ellipse([330, 310, 460, 335], fill=(120, 20, 20))  # rim
    d.polygon([(120, 420), (150, 300), (180, 420)], fill=(40, 120, 50))  # plant
    return img


def person_figure():
    img, d = canvas((200, 220, 235))
    d.ellipse([340, 120, 460, 240], fill=(224, 172, 140))  # head
    d.rectangle([330, 240, 470, 420], fill=(60, 80, 140))  # torso
    d.rectangle([330, 420, 400, 560], fill=(40, 40, 60))
    d.rectangle([400, 420, 470, 560], fill=(40, 40, 60))
    d.ellipse([370, 160, 385, 175], fill=(30, 30, 30))
    d.ellipse([415, 160, 430, 175], fill=(30, 30, 30))
    return img


def text_screenshot():
    img, d = canvas((250, 250, 250))
    d.rectangle([0, 0, W, 50], fill=(70, 90, 120))
    f = ImageFont.load_default(size=40)
    d.text((40, 90), "Quarterly Summary", fill=(20, 20, 20), font=f)
    d.text((40, 170), "Total: 42 items", fill=(60, 60, 60), font=ImageFont.load_default(size=30))
    d.rectangle([40, 260, 760, 520], outline=(150, 150, 150), width=3)
    return img


def hills_landscape():
    img, d = canvas((135, 190, 235))
    d.ellipse([600, 60, 700, 160], fill=(255, 220, 90))  # sun
    d.polygon([(0, 600), (0, 380), (250, 300), (500, 400), (800, 330), (800, 600)], fill=(60, 140, 70))
    d.polygon([(0, 600), (0, 480), (300, 430), (800, 500), (800, 600)], fill=(40, 100, 50))
    return img


def plain_box_unlabelled():
    img, d = canvas((240, 240, 240))
    d.rectangle([250, 180, 550, 450], fill=(120, 120, 125))
    d.polygon([(250, 180), (550, 180), (500, 130), (300, 130)], fill=(150, 150, 155))
    return img


def living_room():
    img, d = canvas((225, 215, 200))
    d.rectangle([0, 430, W, H], fill=(150, 120, 90))  # floor
    d.rectangle([100, 300, 500, 440], fill=(70, 100, 130))  # sofa seat
    d.rectangle([100, 230, 500, 300], fill=(60, 90, 120))  # sofa back
    d.rectangle([560, 90, 760, 330], fill=(170, 210, 240), outline=(90, 70, 50), width=8)  # window
    return img


FIXTURES = {
    "red-mug-on-shelf": red_mug_on_shelf,
    "person-figure": person_figure,
    "text-screenshot": text_screenshot,
    "hills-landscape": hills_landscape,
    "plain-box-unlabelled": plain_box_unlabelled,
    "living-room": living_room,
    "mug-context-supported": red_mug_on_shelf,
    "hills-context-unsupported": hills_landscape,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIXTURES.items():
        fn().save(os.path.join(OUT, f"{name}.png"))
        print("wrote", name)
