import os
import statistics
from math import floor

import pyocr
import pytesseract
from PIL import Image, ImageOps
from pyocr.cuneiform import image_to_string

REQUIRED_PIXEL_COLOR = (34, 34, 34)  # 222222
EXPECTED_PIXELS_PER_LINE = 250


class CuneiRecognizer():
    pass


class TesseractRecognizer():
    pass


class Recognizer(object):

    def __init__(self, debug=False) -> None:
        super().__init__()
        self.debug = debug

    def recognize_image(self, image_file):
        img = Image.open(image_file)
        text_boxes = self.find_text_boxes_in_image(img, REQUIRED_PIXEL_COLOR)
        parsed_text = self.recognize_text_from_boxes(img, text_boxes)
        return parsed_text

    def find_text_boxes_in_image(self, img, pixel_color):
        """
        Пытается найти строки таблицы на картинке
        """
        width, height = img.size
        line_y_match_found = False
        box_list = []
        new_box = {}

        """
        Бегаем по линиям слева-направа и сверху вниз
        Если хотя бы один пиксель на линии совпал - значит коробка началась или продолжается
        Если ни один не совпал - значит коробка кончилась
        """
        rightmost_x = None

        for y in range(0, height - 1):
            line_x_match_found = False
            leftmost_x = None
            pixels_found = 0

            #        print("Line #{}, rightmost is {}".format(y, rightmost_x))
            for x in range(0, width - 1):
                r, g, b = img.getpixel((x, y))
                if (r, g, b) == pixel_color:
                    pixels_found += 1
                    if leftmost_x is None:
                        leftmost_x = x

                    if pixels_found >= EXPECTED_PIXELS_PER_LINE:
                        # img.putpixel((x, y), (255, 192, 200))
                        line_x_match_found = True
                        rightmost_x = x

            if line_x_match_found is True and line_y_match_found is False:
                line_y_match_found = True
                new_box['start'] = [leftmost_x, y]
            elif line_x_match_found is False and line_y_match_found is True:
                line_y_match_found = False
                new_box['end'] = [rightmost_x, y]
                box_list.append(new_box)
                new_box = {}
                rightmost_x = None

        """
        У картинки справа могут быть схожего цвета пиксели, тогда они попадут в правую границу, и расширят её зазря.
        Можно конечно считать накопление непрерывных пикселей нужного цвета ПЕРЕД расширением, но пока
        попробуем просто медиану от всех найденых границ
        """
        rightmost_list = list(map(lambda item: item['end'][0], box_list))
        global_rightmost_x = statistics.median(rightmost_list)
        for k in box_list:
            k['end'][0] = global_rightmost_x

        #if self.debug:
        #    image_name_chunks = os.path.splitext(os.path.basename(img.filename))
        #    img.save("debug_images/pinkg-{}{}".format(image_name_chunks[0], image_name_chunks[1]))

        return box_list

    def extract_numbers_from_image(self, cropped_chunk, image_name=None):
        """
        Работает через cuneiForm.
        :param cropped_chunk:
        :param image_name:
        :return:
        """
        threshold_numbers = 70
        converted_numbers = self.get_part_with_numbers(cropped_chunk)
        converted_numbers = self.grayscale(converted_numbers, threshold_numbers)
        converted_numbers = self.add_border(converted_numbers)

        if image_name is not None and self.debug:
            converted_numbers.save('debug_images/' + 'extracted_numbers-' + image_name)

        line_and_word_boxes = image_to_string(
            converted_numbers,
            lang='ruseng',
            builder=pyocr.builders.LineBoxBuilder()
        )
        text_numbers_data = self.merge_nearest_chars(line_and_word_boxes)
        return text_numbers_data

    def extract_name_from_image(self, cropped_chunk, counter):
        threshold_names = 120
        """
        Для имен еще надо:
         - отрезать слева иконку и класс
         - попытаться примерно угадать, где вторая строка с уровнем и званием, и удалить её тоже
        """
        image_with_name = self.get_part_with_name(cropped_chunk)
        # cut icon and class
        imgwidth, imgheight = image_with_name.size
        percentage_value_x = 0.35
        percentage_value_y = 0.5
        newwidth = floor(imgwidth * percentage_value_x)
        newheight = floor(imgheight * percentage_value_y)
        box = (newwidth, 0, floor(imgwidth * 0.8), newheight)
        image_with_name = image_with_name.crop(box)

        converted_names = image_with_name
        # converted_names = grayscale(image_with_name, threshold_names)
        # converted_names = add_border(converted_names)

        cropped_img = Image.new('RGB', converted_names.size, 255)
        cropped_img.paste(converted_names)
        # cropped_img.save('chunk-{}-{}'.format(counter, threshold_names) + '.png')

        try:
            # cuneiform
            line_and_word_boxes = image_to_string(
                converted_names,
                lang='eng'
                #            builder=pyocr.builders.LineBoxBuilder()
            )
            text_data_cunei = line_and_word_boxes
            # for lb in line_and_word_boxes:
            #    print('LB', lb.content)
        except pyocr.error.CuneiformError:
            text_data_cunei = None
            pass
        # text_data = merge_nearest_chars(line_and_word_boxes)
        text_data_tesseract = pytesseract.image_to_string(converted_names)
        return {'tesseract': text_data_tesseract, 'cunei': text_data_cunei}

    def recognize_text_from_boxes(self, img, text_boxes):
        """

        :param img: Opened source image
        :param text_boxes: list of coordinates for each row
        :return:
        """
        counter = 0
        result = []
        for box in text_boxes:
            counter += 1

            image_copy = img.copy()
            crop_coords = (box['start'][0], box['start'][1], box['end'][0], box['end'][1])
            cropped_chunk = image_copy.crop(crop_coords)

            image_name_chunks = os.path.splitext(os.path.basename(img.filename))
            image_name_for_debugging = "{}-{}{}".format(
                image_name_chunks[0], counter, image_name_chunks[1]
            )
            # cropped_chunk.save("debug_images/cropped-{}-{}{}".format(image_name_chunks[0], counter, image_name_chunks[1]))
            # print(image_name_for_debugging)

            text_numbers_data = self.extract_numbers_from_image(cropped_chunk, image_name=image_name_for_debugging)
            text_names_data = self.extract_name_from_image(cropped_chunk, counter)
            result.append({
                'number': text_numbers_data,
                'names': text_names_data
            })
        return result

    def merge_nearest_chars(self, boxes, less_than_pixels=20):
        data = []
        current = {'value': '', 'pos': ()}
        for box in boxes:
            if current['value'] == '':
                current['value'] = box.content
            else:
                distance = box.position[0][0] - current['pos'][1][0]
                if distance > 0 and distance <= less_than_pixels:
                    current['value'] += box.content
                else:
                    data.append(current['value'])
                    current['value'] = box.content

            current['pos'] = box.position

        data.append(current['value'])
        return data

    def crop_image(self, infile):
        im = Image.open(infile)
        imgwidth, imgheight = im.size
        newwidth = floor(imgwidth / 2)
        box = (newwidth, 0, imgwidth, imgheight)
        cropped = im.crop(box)
        img = Image.new('RGB', (imgheight, newwidth), 255)
        img.paste(cropped)
        return img

    def add_border(self, imgfile):
        return ImageOps.expand(imgfile, border=20, fill='white')

    def cut_image_in_half(self, infile):
        cropped = self.crop_image(infile)
        cropped = self.grayscale(cropped)
        path = os.path.join('/tmp', "IMG-cut-bw.png")
        cropped.save(path)

    def grayscale(self, img, threshold=100):
        # threshold = 80
        fn = lambda x: 255 if x > threshold else 0
        r = img.convert('L').point(fn, mode='1')
        return r

    def get_part_with_name(self, img):
        w, h = img.size
        coords = (0, 0, floor(w / 2), h)
        img_copy = img.copy()
        cropped = img_copy.crop(coords)
        return cropped

    def get_part_with_numbers(self, img):
        w, h = img.size
        coords = (floor(w / 2), 0, w, h)
        img_copy = img.copy()
        cropped = img_copy.crop(coords)
        return cropped


def ocr_core(filename):
    text = pytesseract.image_to_string(
        Image.open(filename),
    )
    return text


def ocr_open_image(image):
    text = pytesseract.image_to_string(
        image,
        config='--oem 3 -c tessedit_char_whitelist=0123456789'
    )
    return text

    # img.save(dirname + '/' + 'pink-' + filename)
