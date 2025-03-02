# SPDX-FileCopyrightText: Copyright ELECFREAKS
# SPDX-License-Identifier: MIT

"""
`picoed.display`
====================================================

CircuitPython driver for the Pico:ed matrix display.

"""

try:
    from adafruit_is31fl3731 import IS31FL3731
except ImportError:
    raise ImportError(
        "no module named 'adafruit_is31fl3731'. see: https://github.com/adafruit/Adafruit_CircuitPython_IS31FL3731.git"
    )

_BITMAP = (
    b"\x00\x00\x00\x00\x00",
    b"\x00\x00\x5f\x00\x00",
    b"\x00\x07\x00\x07\x00",
    b"\x14\x7f\x14\x7f\x14",
    b"\x24\x2a\x7f\x2a\x12",
    b"\x23\x13\x08\x64\x62",
    b"\x36\x49\x55\x22\x50",
    b"\x00\x05\x03\x00\x00",
    b"\x00\x1c\x22\x41\x00",
    b"\x00\x41\x22\x1c\x00",
    b"\x08\x2a\x1c\x2a\x08",
    b"\x08\x08\x3e\x08\x08",
    b"\x00\x50\x30\x00\x00",
    b"\x08\x08\x08\x08\x08",
    b"\x00\x60\x60\x00\x00",
    b"\x20\x10\x08\x04\x02",
    b"\x3e\x51\x49\x45\x3e",
    b"\x00\x42\x7f\x40\x00",
    b"\x42\x61\x51\x49\x46",
    b"\x21\x41\x45\x4b\x31",
    b"\x18\x14\x12\x7f\x10",
    b"\x27\x45\x45\x45\x39",
    b"\x3c\x4a\x49\x49\x30",
    b"\x01\x71\x09\x05\x03",
    b"\x36\x49\x49\x49\x36",
    b"\x06\x49\x49\x29\x1e",
    b"\x00\x36\x36\x00\x00",
    b"\x00\x56\x36\x00\x00",
    b"\x00\x08\x14\x22\x41",
    b"\x14\x14\x14\x14\x14",
    b"\x41\x22\x14\x08\x00",
    b"\x02\x01\x51\x09\x06",
    b"\x32\x49\x79\x41\x3e",
    b"\x7e\x11\x11\x11\x7e",
    b"\x7f\x49\x49\x49\x36",
    b"\x3e\x41\x41\x41\x22",
    b"\x7f\x41\x41\x22\x1c",
    b"\x7f\x49\x49\x49\x41",
    b"\x7f\x09\x09\x01\x01",
    b"\x3e\x41\x41\x51\x32",
    b"\x7f\x08\x08\x08\x7f",
    b"\x00\x41\x7f\x41\x00",
    b"\x20\x40\x41\x3f\x01",
    b"\x7f\x08\x14\x22\x41",
    b"\x7f\x40\x40\x40\x40",
    b"\x7f\x02\x04\x02\x7f",
    b"\x7f\x04\x08\x10\x7f",
    b"\x3e\x41\x41\x41\x3e",
    b"\x7f\x09\x09\x09\x06",
    b"\x3e\x41\x51\x21\x5e",
    b"\x7f\x09\x19\x29\x46",
    b"\x46\x49\x49\x49\x31",
    b"\x01\x01\x7f\x01\x01",
    b"\x3f\x40\x40\x40\x3f",
    b"\x1f\x20\x40\x20\x1f",
    b"\x7f\x20\x18\x20\x7f",
    b"\x63\x14\x08\x14\x63",
    b"\x03\x04\x78\x04\x03",
    b"\x61\x51\x49\x45\x43",
    b"\x00\x00\x7f\x41\x41",
    b"\x02\x04\x08\x10\x20",
    b"\x41\x41\x7f\x00\x00",
    b"\x04\x02\x01\x02\x04",
    b"\x40\x40\x40\x40\x40",
    b"\x00\x01\x02\x04\x00",
    b"\x20\x54\x54\x54\x78",
    b"\x7f\x48\x44\x44\x38",
    b"\x38\x44\x44\x44\x20",
    b"\x38\x44\x44\x48\x7f",
    b"\x38\x54\x54\x54\x18",
    b"\x08\x7e\x09\x01\x02",
    b"\x08\x14\x54\x54\x3c",
    b"\x7f\x08\x04\x04\x78",
    b"\x00\x44\x7d\x40\x00",
    b"\x20\x40\x44\x3d\x00",
    b"\x00\x7f\x10\x28\x44",
    b"\x00\x41\x7f\x40\x00",
    b"\x7c\x04\x18\x04\x78",
    b"\x7c\x08\x04\x04\x78",
    b"\x38\x44\x44\x44\x38",
    b"\x7c\x14\x14\x14\x08",
    b"\x08\x14\x14\x18\x7c",
    b"\x7c\x08\x04\x04\x08",
    b"\x48\x54\x54\x54\x20",
    b"\x04\x3f\x44\x40\x20",
    b"\x3c\x40\x40\x20\x7c",
    b"\x1c\x20\x40\x20\x1c",
    b"\x3c\x40\x30\x40\x3c",
    b"\x44\x28\x10\x28\x44",
    b"\x0c\x50\x50\x50\x3c",
    b"\x44\x64\x54\x4c\x44",
    b"\x00\x08\x36\x41\x00",
    b"\x00\x00\x7f\x00\x00",
    b"\x00\x41\x36\x08\x00",
    b"\x18\x04\x18\x20\x18",
)


class Image():
    """An image to show on the Pico:ed LED display."""

    NO = b"\x00\x00\x00\x00\x00\x41\x22\x14\x08\x14\x22\x41\x00\x00\x00\x00\x00"
    SQUARE = b"\x00\x00\x00\x00\x00\x00\x3E\x22\x22\x22\x3E\x00\x00\x00\x00\x00\x00"
    RECTANGLE = b"\xFF\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\xFF"
    RHOMBUS = b"\x00\x00\x00\x00\x00\x08\x14\x22\x41\x22\x14\x08\x00\x00\x00\x00\x00"
    TARGET = b"\x00\x00\x00\x00\x00\x08\x1C\x36\x63\x36\x1C\x08\x00\x00\x00\x00\x00"
    CHESSBOARD = b"\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A\x55\x2A"
    HAPPY = b"\x00\x00\x00\x00\x10\x20\x46\x40\x40\x40\x46\x20\x10\x00\x00\x00\x00"
    SAD = b"\x00\x00\x00\x00\x40\x22\x12\x10\x10\x10\x12\x22\x40\x00\x00\x00\x00"
    YES = b"\x00\x00\x00\x00\x00\x00\x08\x10\x20\x10\x08\x04\x02\x00\x00\x00\x00"
    HEART = b"\x00\x00\x00\x00\x00\x0E\x1F\x3F\x7E\x3F\x1F\x0E\x00\x00\x00\x00\x00"
    TRIANGLE = b"\x00\x00\x40\x60\x50\x48\x44\x42\x41\x42\x44\x48\x50\x60\x40\x00\x00"
    CHAGRIN = b"\x00\x00\x00\x00\x22\x14\x08\x40\x40\x40\x08\x14\x22\x00\x00\x00\x00"
    SMILING_FACE = b"\x00\x00\x00\x00\x00\x06\x36\x50\x50\x50\x36\x06\x00\x00\x00\x00\x00"
    CRY = b"\x60\x70\x70\x38\x02\x02\x64\x50\x50\x50\x64\x02\x02\x38\x70\x70\x60"
    DOWNCAST = b"\x00\x00\x00\x02\x0A\x11\x08\x40\x40\x40\x08\x11\x0A\x02\x00\x00\x00"
    LOOK_RIGHT = b"\x00\x00\x00\x00\x00\x00\x00\x26\x2F\x06\x00\x06\x0F\x06\x00\x00\x00"
    LOOK_LEFT = b"\x00\x00\x00\x06\x0F\x06\x00\x06\x2F\x26\x00\x00\x00\x00\x00\x00\x00"
    TONGUE = b"\x00\x00\x00\x00\x04\x12\x14\x70\x70\x70\x16\x16\x00\x00\x00\x00\x00"
    PEEK_RIGHT = b"\x00\x00\x04\x04\x04\x0C\x0C\x40\x40\x40\x04\x04\x04\x0C\x0C\x00\x00"
    PEEK_LEFT = b"\x00\x00\x0C\x0C\x04\x04\x04\x40\x40\x40\x0C\x0C\x04\x04\x04\x00\x00"
    TEAR_EYES = b"\x00\x00\x00\x06\x7F\x06\x20\x40\x40\x40\x20\x06\x7F\x06\x00\x00\x00"
    PROUD = b"\x01\x07\x0F\x0F\x0F\x0F\x47\x41\x41\x41\x27\x0F\x0F\x0F\x0F\x07\x01"
    SNEER_LEFT = b"\x00\x00\x00\x0C\x08\x0C\x2C\x40\x40\x40\x2C\x08\x0C\x0C\x00\x00\x00"
    SNEER_RIGHT = b"\x00\x00\x00\x0C\x0C\x08\x2C\x40\x40\x40\x2C\x0C\x08\x0C\x00\x00\x00"
    SUPERCILIOUS_LOOK = b"\x00\x00\x00\x0E\x0C\x0E\x00\x20\x20\x20\x00\x0E\x0C\x0E\x00\x00\x00"
    EXCITED = b"\x60\x70\x70\x3E\x01\x06\x30\x50\x50\x50\x30\x06\x01\x3E\x70\x70\x60"

    def __new__(cls, value=None):
        if value is not None and isinstance(value, str):
            data = []
            for y in range(7):
                if y < 6:
                    if value[(y + 1) * 18 - 1] != ":":
                        raise ValueError('Each line of data must be separated with a ":"')
                for x in range(17):
                    data.append([x, y, int(value[y * 18 + x])])
            return data
        else:
            return [[0, 0, 0]]


class Display(IS31FL3731):
    """Supports the Pico:ed display by ELECFREAKS"""

    width = 17
    height = 7

    _current_frame = 0

    @staticmethod
    def pixel_addr(x, y):
        """Translates an x, y coordinate to a pixel index."""
        if x > 8:
            x = 17 - x
            y += 8
        else:
            y = 7 - y
        return x * 16 + y

    def _draw(self, buffer, brightness):
        self._current_frame = 0 if self._current_frame else 1
        self.frame(self._current_frame, show=False)
        self.fill(0)
        for x in range(self.width):
            col = buffer[x]
            for y in range(self.height):
                bit = 1 << y & col
                if bit:
                    self.pixel(x, y, brightness)
        self.frame(self._current_frame, show=True)

    def clear(self):
        """Clears the LED display."""
        self.fill(0)

    def scroll(self, value, brightness=30):
        """Scrolls a number or text on the LED display."""
        if brightness < 0:
            brightness = 0
        if brightness > 255:
            brightness = 255

        buf = bytearray(self.width)
        text = str(value)

        if len(text) == 1:
            text += '  '
        elif len(text) == 2:
            text += ' '
        elif len(text) != 3:
            text += '   '

        if len(text) == 3:
            for buf_index, _ in enumerate(buf):
                font = bytearray(_BITMAP[ord(text[buf_index // 6]) - 32])
                font.append(0)
                buf[buf_index] = font[buf_index % 6]
            self._draw(buf, brightness)
        else:
            for text_index in range(len(text) * 6):
                for buf_index in range(len(buf) - 1):
                    buf[buf_index] = buf[buf_index + 1]
                font = bytearray(_BITMAP[ord(text[text_index // 6]) - 32])
                font.append(0)
                buf[len(buf) - 1] = font[text_index % 6]
                self._draw(buf, brightness)

    def show(self, value, brightness=30):
        """Shows images, letters or digits on the LED display."""
        if isinstance(value, (int, float, str)):
            self.scroll(value, brightness)

        elif isinstance(value, bytes):
            self._draw(value, brightness)
        else:
            self._current_frame = 0 if self._current_frame else 1
            self.frame(self._current_frame, show=False)
            self.fill(0)
            for pixel in value:
                self.pixel(pixel[0], pixel[1], int(pixel[2] * 255 / 9))
            self.frame(self._current_frame, show=True)
