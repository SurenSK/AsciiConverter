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
        print("Opened...")
        self.raw_data = self.im.getdata()
        print("Got raw data...")
        self.glyphs_data = self.data_to_chars_dithered(self.invert_flag, self.alpha_flag, self.mode_type)
        print("Converted data to glyphs...")

    def flatten_tuples(self, invert: bool, alpha: bool, mode: str) -> List[int]:
        data = self.raw_data
        if len(self.im.mode) == 1:
            lum_list = [0]*len(data)
            if invert is True:
                for i in range(len(data)):
                    lum_list[i] = 255 - int(data[i])
            else:
                for i in range(len(data)):
                    lum_list[i] = int(data[i])
        else:
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

    # ~400s Total when collating chars into printable string
    def data_to_chars_dithered(self, invert: bool, alpha: bool, mode: str):
        # TODO Instead of calculating the base luminance first
        #  stream in first two rows, convert first to chars, return 2nd as correction row
        t0 = time.time()
        lum_data = self.flatten_tuples(invert, alpha, mode)
        print("Got lumin data... t=", end='')
        print(time.time() - t0)
        t1 = time.time()
        glyphs_arr = ["0"]*len(lum_data)
        print("Preset char array... t=", end='')
        print(time.time() - t1)
        t2 = time.time()
        h = self.im.height
        w = self.im.width
        chars = AsciiConverter.default_charset[0]
        vals = AsciiConverter.default_charset[1]
        vals[:] = [(val * (255 / max(vals))) for val in vals]
        print("Preset metadata... t=", end='')
        print(time.time() - t2)

        c_pixel_index = -1
        r_pixel_index = c_pixel_index + 1
        d_pixel_index = c_pixel_index + w
        dr_pixel_index = d_pixel_index + 1
        dl_pixel_index = d_pixel_index - 1

        t3 = time.time()
        for row in range(h - 1):
            if row % 1000 == 0:
                print("Finished", row, "rows; t =", time.time() - t3)
                t3 = time.time()

            c_pixel_index += 1
            r_pixel_index += 1
            d_pixel_index += 1
            dr_pixel_index += 1
            dl_pixel_index += 1
            # print(lum_data[c_pixel_index], "7-", lum_data[r_pixel_index],
            # " 1-", lum_data[dr_pixel_index], " 5-", lum_data[d_pixel_index])
            index = bisect.bisect_left(vals, min(lum_data[c_pixel_index], 255))
            error = (lum_data[c_pixel_index] - vals[index])
            if abs(lum_data[c_pixel_index] - vals[max(index - 1, 0)]) < abs(error):
                index -= 1
                error = (lum_data[c_pixel_index] - vals[index])
            error = int(error / 13)

            lum_data[r_pixel_index] = lum_data[r_pixel_index] + (error * 7)
            lum_data[dr_pixel_index] = lum_data[dr_pixel_index] + error
            lum_data[d_pixel_index] = lum_data[d_pixel_index] + (error * 5)
            glyphs_arr[c_pixel_index] = chars[index]

            for col in range(1, w - 1):
                c_pixel_index += 1
                r_pixel_index += 1
                d_pixel_index += 1
                dr_pixel_index += 1
                dl_pixel_index += 1
                # print(lum_data[c_pixel_index], "7-", lum_data[r_pixel_index],
                # " 1-", lum_data[dr_pixel_index], " 5-", lum_data[d_pixel_index],
                # " 3-", lum_data[dl_pixel_index])
                index = bisect.bisect_left(vals, min(lum_data[c_pixel_index], 255))
                error = (lum_data[c_pixel_index] - vals[index])
                if abs(lum_data[c_pixel_index] - vals[max(index - 1, 0)]) < abs(error):
                    index -= 1
                    error = (lum_data[c_pixel_index] - vals[index])
                error /= 16
                lum_data[r_pixel_index] = lum_data[r_pixel_index] + (error * 7)
                lum_data[dr_pixel_index] = lum_data[dr_pixel_index] + error
                lum_data[d_pixel_index] = lum_data[d_pixel_index] + (error * 5)
                lum_data[dl_pixel_index] = lum_data[dl_pixel_index] + (error * 3)
                glyphs_arr[c_pixel_index] = chars[index]

            c_pixel_index += 1
            d_pixel_index += 1
            dl_pixel_index += 1
            # print(lum_data[c_pixel_index], "5-", lum_data[d_pixel_index],
            # " 3-", lum_data[dl_pixel_index])
            index = bisect.bisect_left(vals, min(lum_data[c_pixel_index], 255))
            error = (lum_data[c_pixel_index] - vals[index])
            if abs(lum_data[c_pixel_index] - vals[max(index - 1, 0)]) < abs(error):
                index -= 1
                error = (lum_data[c_pixel_index] - vals[index])
            error /= 8
            lum_data[d_pixel_index] = lum_data[d_pixel_index] + (error * 5)
            lum_data[dl_pixel_index] = lum_data[dl_pixel_index] + (error * 3)
            glyphs_arr[c_pixel_index] = chars[index]

        c_pixel_index = ((h - 1) * w) - 1
        r_pixel_index = c_pixel_index + 1
        for col in range(w - 1):
            c_pixel_index += 1
            r_pixel_index += 1
            # print(lum_data[c_pixel_index], "7-", lum_data[r_pixel_index])
            index = bisect.bisect_left(vals, min(lum_data[c_pixel_index], 255))
            error = (lum_data[c_pixel_index] - vals[index])
            if abs(lum_data[c_pixel_index] - vals[max(index - 1, 0)]) < abs(error):
                index -= 1
                error = (lum_data[c_pixel_index] - vals[index])
            lum_data[r_pixel_index] = lum_data[r_pixel_index] + error
            glyphs_arr[c_pixel_index] = chars[index]

        c_pixel_index = (w * h) - 1
        index = bisect.bisect_left(vals, min(lum_data[c_pixel_index], 255))
        error = (lum_data[c_pixel_index] - vals[index])
        if abs(lum_data[c_pixel_index] - vals[max(index - 1, 0)]) < abs(error):
            index -= 1
        glyphs_arr[c_pixel_index] = chars[index]

        return glyphs_arr

    def resize_image(self, new_width: int, new_height: int, mode) -> None:
        self.im = self.im.resize((new_width, new_height), mode)
        self.raw_data = self.im.getdata()
        self.glyphs_data = self.data_to_chars_dithered(
            self.invert_flag, self.alpha_flag, self.mode_type)

    def recalculate_image(self, invert: bool, alpha: bool, mode: str) -> None:
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

    def display_image(self, end_char: str):
        self.glyphs_data.append("")
        img_str = ""
        for i in range(0, len(self.glyphs_data)):
            if i % self.im.width == 0:
                # img_str += "\r\n"
                print(img_str)
                img_str = ""
            img_str += str(self.glyphs_data[i]*2)
            img_str += str(end_char)
        # print(img_str)


t_start = time.time()
img = AsciiConverter("face3.jpg")
print("Total time to init...", end='')
print(time.time() - t_start)

img.display_image('')
print("Total time to print...", end='')
print(time.time() - t_start)
