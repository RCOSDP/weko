import base64
import random
import typing as t
from captcha.image import ImageCaptcha, random_color
from PIL.Image import new as createImage, Image, QUAD, BILINEAR
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFilter import SMOOTH

ColorTuple = t.Union[t.Tuple[int, int, int], t.Tuple[int, int, int, int]]

class ImageCaptchaEx(ImageCaptcha):
    lookup_table: t.List[int] = [int(i * 1.97) for i in range(256)]

    def _draw_character(
        self,
        c: str,
        draw: ImageDraw,
        color: ColorTuple) -> Image:
        font = random.choice(self.truefonts)
        _, _, w, h = draw.multiline_textbbox((1, 1), c, font=font)

        dx1 = random.randint(0, 4)
        dy1 = random.randint(0, 6)
        im = createImage('RGBA', (w + dx1, h + dy1))
        Draw(im).text((dx1, dy1), c, font=font, fill=color)

        # rotate
        if (c != '+') and (c != '-'):
            im = im.crop(im.getbbox())
            im = im.rotate(random.uniform(-30, 30), BILINEAR, expand=True)

            # warp
            dx2 = w * random.uniform(0.1, 0.3)
            dy2 = h * random.uniform(0.2, 0.3)
            x1 = int(random.uniform(-dx2, dx2))
            y1 = int(random.uniform(-dy2, dy2))
            x2 = int(random.uniform(-dx2, dx2))
            y2 = int(random.uniform(-dy2, dy2))
            w2 = w + abs(x1) + abs(x2)
            h2 = h + abs(y1) + abs(y2)
            data = (
                x1, y1,
                -x1, h2 - y2,
                w2 + x2, h2 + y2,
                w2 - x2, -y1,
            )
            im = im.resize((w2, h2))
            im = im.transform((w, h), QUAD, data)
        else:
            im = im.resize((w + dx1, int(1.5*h)))
            im = im.crop((int((w + dx1) / 2.0 - w), int(0.6*h), int((w + dx1) / 2.0 + w) , int(0.6*h)+h))
        return im

    def create_captcha_image(
            self,
            chars: str,
            color: ColorTuple,
            background: ColorTuple) -> Image:
        """Create the CAPTCHA image itself.

        :param chars: text to be generated.
        :param color: color of the text.
        :param background: color of the background.

        The color should be a tuple of 3 numbers, such as (0, 255, 255).
        """
        image = createImage('RGB', (self._width, self._height), background)
        draw = Draw(image)

        images: t.List[Image] = []
        for c in chars:
            if random.random() > 0.5:
                images.append(self._draw_character(" ", draw, color))
            images.append(self._draw_character(c, draw, color))

        text_width = sum([im.size[0] for im in images])

        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars))
        rand = int(0.25 * average)
        offset = int(average * 0.1)

        for im in images:
            w, h = im.size
            mask = im.convert('L').point(self.lookup_table)
            image.paste(im, (offset, int((self._height - h) / 2)), mask)
            offset = offset + w + random.randint(-rand, 0)

        if width > self._width:
            image = image.resize((self._width, self._height))

        return image

    def generate_image(self, chars: str) -> Image:
        """Generate the image of the given characters.

        :param chars: text to be generated.
        """
        background = random_color(238, 255)
        color = random_color(10, 200, random.randint(220, 255))
        im = self.create_captcha_image(chars, color, background)
        self.create_noise_dots(im, color, width=6, number=100)
        self.create_noise_curve(im, color)
        im = im.filter(SMOOTH)
        return im


def get_captcha_info():
    ascii_letters = 'abdefhijkmnprtuvwy'
    val1 = random.randint(10, 99)
    val2 = random.randint(10, 99)
    question = list()
    answer = 0
    if random.random() > 0.5 :
        if val1 > val2:
            question = list(str(val1) + '-' + str(val2))
            answer = val1 - val2
        else:
            question = list(str(val2) + '-' + str(val1))
            answer = val2 - val1
    else:
        question = list(str(val1) + '+' + str(val2))
        answer = val1 + val2

    for _ in range(3):
        letter = random.choice(ascii_letters)
        question.insert(random.randint(0, len(question)), letter)

    image = ImageCaptchaEx(width=360, height=78).generate(''.join(question))

    return {
        'image': base64.b64encode(image.getvalue()),
        'answer': answer
    }
