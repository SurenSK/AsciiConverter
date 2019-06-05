import bisect
from PIL import Image
from typing import List
from typing import Tuple

class AsciiConverter:
    glyphs = " `'^,~*)/{}[?+iclr&utIzx$knhbdXqmQ#BMW"
    lumens = [3, 8, 9, 11, 12, 14, 16, 17, 20, 21, 22, 23, 24, 25,
              27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 39,
              39, 40, 41, 42, 43, 46, 47, 49, 53, 54, 55, 57]
    default_charset = (glyphs, lumens)

    def __init__(self, path: str):
        self.invert_flag = False
        self.alpha_flag = False
        self.mode_type = "luminance"
        self.im = Image.open(path)
        self.raw_data = self.im.getdata()
        self.glyphs_data = self.data_to_chars_dithered(
            self.invert_flag, self.alpha_flag, self.mode_type)

    @staticmethod
    def flatten_tuples(data: List[Tuple[int, int, int]], invert: bool, alpha: bool, mode: str) -> List[int]:
        lum_list = []
        for pixel in data:
            r, g, b = pixel[0], pixel[1], pixel[2]
            a = 1 if len(pixel) == 3 else pixel[3] / 255

            if mode == "luminance":
                lum = round((0.2126 * r + 0.7152 * g + 0.0722 * b), 4)
            elif mode == "lightness":
                lum = round((max(r + g + b) + min(r + g + b)) / 2, 4)
            elif mode == "average":
                lum = round((r + g + b) / 3, 4)
            elif mode == "norm":
                lum = round(((r ** 2 + g ** 2 + b ** 2) ** 0.5) / 3, 4)
            elif mode == "r":
                lum = r
            elif mode == "g":
                lum = g
            elif mode == "b":
                lum = b
            elif mode == "max":
                lum = max(r, g, b)
            elif mode == "min":
                lum = min(r, g, b)

            lum = lum * a if alpha is True else lum
            lum = 255 - lum if invert is True else lum

            lum_list.append(lum)

        print(type(lum_list))
        print(type(lum_list[0]))
        return lum_list

    @staticmethod
    def list_to_2d(data_flat: list, height: int, width: int) -> list:
        array_2d = []
        for x in range(0, height):
            row = []
            for y in range(0, width):
                row.append(data_flat[(x * width) + y])
            array_2d.append(row)
        return array_2d

    def data_to_chars_dithered(self, invert: bool, alpha: bool, mode: str) -> list:
        lum_data = AsciiConverter.flatten_tuples(self.raw_data, invert, alpha, mode)
        data = AsciiConverter.list_to_2d(lum_data, self.im.height, self.im.width)
        chars = AsciiConverter.default_charset[0]
        vals = AsciiConverter.default_charset[1]
        vals[:] = [(val * (255 / max(vals))) for val in vals]
        chars_arr = [[0 for x in range(len(data[0]))] for y in range(len(data))]
        err_arr = [[0 for x in range(len(data[0]))] for y in range(len(data))]

        for x in range(0, len(data[0])):
            for y in range(0, len(data)):
                index = bisect.bisect_left(vals, min(data[y][x], 255))

                error = data[y][x] - vals[index]
                if abs(data[y][x] - vals[max(index - 1, 0)]) < abs(error):
                    index -= 1
                    error = data[y][x] - vals[index]
                err_arr[y][x] = '', int(error)

                if x < (len(data[0]) - 1):
                    data[y][x + 1] = data[y][x + 1] + error * 7 / 16
                if x > 0 and y < (len(data) - 1):
                    data[y + 1][x - 1] = data[y + 1][x - 1] + error * 3 / 16
                if y < (len(data) - 1):
                    data[y + 1][x] = data[y + 1][x] + error * 5 / 16
                if x < (len(data[0]) - 1) and y < (len(data) - 1):
                    data[y + 1][x + 1] = data[y + 1][x + 1] + error * 1 / 16

                chars_arr[y][x] = chars[index] * 2
        return chars_arr

    def resize_image(self, new_width: int, new_height: int, mode):
        self.im = self.im.resize((new_width, new_height), mode)
        self.raw_data = self.im.getdata()
        self.glyphs_data = self.data_to_chars_dithered(
            self.invert_flag, self.alpha_flag, self.mode_type)

    def recalculate_image(self, invert: bool, alpha: bool, mode: str):
        self.invert_flag = invert
        self.alpha_flag = alpha
        self.mode_type = mode
        self.glyphs_data = self.data_to_chars_dithered(
            self.invert_flag, self.alpha_flag, self.mode_type)

    def list_im_info(self) -> None:
        print("width", self.im.width)
        print("height", self.im.height)
        print("#pixels", self.im.width * self.im.height)
        print("type", self.im.format)

    def list_glyph_frequencies(self) -> None:
        for c in AsciiConverter.default_charset[0]:
            print(c + c, sum(row.count(c + c) for row in self.glyphs_data))

    def display_image(self, end_char: str) -> None:
        for row in self.glyphs_data:
            for elem in row:
                print(elem, end=end_char)
            print()


face = AsciiConverter("face3.jpg")
face.resize_image(90, 90, Image.LANCZOS)
face.display_image('')
