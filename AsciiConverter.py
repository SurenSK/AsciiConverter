import bisect
from PIL import Image
from typing import List
import time


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
    def flatten_tuples(data: list, invert: bool, alpha: bool, mode: str) -> List[int]:
        lum_list = []
        for pixel in data:
            r, g, b = pixel[0], pixel[1], pixel[2]
            a = 1 if len(pixel) == 3 else pixel[3] / 255
            lum = 0

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

        return lum_list

    @staticmethod
    def list_to_2d(data_flat: List[int], height: int, width: int) -> List[List[int]]:
        array_2d = []
        for x in range(0, height):
            row = []
            for y in range(0, width):
                row.append(data_flat[(x * width) + y])
            array_2d.append(row)
        return array_2d

    def data_to_chars_dithered(self, invert: bool, alpha: bool, mode: str) -> List[List[str]]:
        lum_data = AsciiConverter.flatten_tuples(self.raw_data, invert, alpha, mode)
        data = AsciiConverter.list_to_2d(lum_data, self.im.height, self.im.width)
        vals = AsciiConverter.default_charset[1]
        vals[:] = [(val * (255 / max(vals))) for val in vals]
        chars_arr = [["" for x in range(self.im.width)] for y in range(self.im.height)]
        err_arr = [[0 for x in row] for row in chars_arr]

        for x in range(0, self.im.width):
            pos_x = x + 1
            neg_x = x - 1
            for y in range(0, self.im.height):
                pos_y = y + 1
                index = bisect.bisect_left(vals, min(data[y][x], 255))
                error = (data[y][x] - vals[index])
                if abs(data[y][x] - vals[max(index - 1, 0)]) < abs(error):
                    index -= 1
                    error = (data[y][x] - vals[index])
                err_arr[y][x] = error
                error /= 16

                if pos_x < self.im.width:
                    data[y][pos_x] = data[y][pos_x] + (error * 7)
                if x > 0 and pos_y < self.im.height:
                    data[pos_y][neg_x] = data[pos_y][neg_x] + (error * 3)
                if pos_y < self.im.height:
                    data[pos_y][x] = data[pos_y][x] + (error * 5)
                if pos_x < self.im.width and pos_y < self.im.height:
                    data[pos_y][pos_x] = data[pos_y][pos_x] + error

                chars_arr[y][x] = AsciiConverter.default_charset[0][index]

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
        img_str = ""
        for row in self.glyphs_data:
            for elem in row:
                img_str += elem*2
            img_str += "\n\r"
        print(img_str)


time1 = time.time()
face = AsciiConverter("face3.jpg")
time2 = time.time()
print(time2 - time1)
face.display_image('')
time2 = time.time()
print(time2 - time1)
