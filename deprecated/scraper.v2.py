from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import logging
import time

from deprecated import Catalog

logging.basicConfig(level=logging.INFO)

service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_position(3000, 0)
driver.maximize_window()

ROOT_DIR = os.getcwd()



class Folder:
    ILLEGAL_CHARACTERS = ':"/\\|?*'
    MAX_FILENAME_LENGTH = 211

    def __init__(self, name: str, path: str = None, parent: 'Folder' = None):
        if (parent is None) == (path is None):
            raise ValueError("path or parent must be provided, but not both of them.")
        if parent is not None:
            self.parent = parent
            self.path = parent.full_path
        else:
            self.path = path
        self.original_name = name
        self.name = self.clean_name()
        self.full_path = f'{self.path}/{self.name}'
        self.create_if_not_exists()

    def clean_name(self):
        name = ''.join(filter(lambda x: x not in self.ILLEGAL_CHARACTERS, self.original_name))
        name = name[:self.MAX_FILENAME_LENGTH]
        return name

    def create_if_not_exists(self):
        if not os.path.isdir(self.full_path):
            os.mkdir(self.full_path)


# noinspection PyMethodParameters
# class Catalog:
#     FILE_NAME = f'material\\catalog.v2.json'
#
#     COURSES = []
#
#     def _course_exists(course_num):
#         return len(Catalog.COURSES) > course_num
#
#     def add_course(course_num, n_modules):
#         if not Catalog._course_exists(course_num):
#             Catalog.COURSES.append({"n_modules": n_modules, "modules": []})
#             Catalog.save_to_file()
#
#     def _module_exists(course_num, module_num):
#         return len(Catalog.COURSES[course_num]["modules"]) > module_num
#
#     def add_module(course_num, module_num, n_lessons):
#         if not Catalog._module_exists(course_num, module_num):
#             Catalog.COURSES[course_num]["modules"].append({"lessons": [False for i in range(n_lessons)]})
#             Catalog.save_to_file()
#
#     def complete_lesson(course_num, module_num, lesson_num):
#         Catalog.COURSES[course_num]["modules"][module_num]["lessons"][lesson_num] = True
#         Catalog.save_to_file()
#
#     def is_module_complete(course_num, module_num):
#         return False not in Catalog.COURSES[course_num]["modules"][module_num]["lessons"]
#
#     def is_course_complete(course_num):
#         if not Catalog._course_exists(course_num):
#             return False
#         n_modules = Catalog.COURSES[course_num]["n_modules"]
#         for n in range(n_modules):
#             if not Catalog._module_exists(course_num, n):
#                 return False
#             if not Catalog.is_module_complete(course_num, n):
#                 return False
#         return True
#
#
#     def save_to_file():
#         with open(Catalog.FILE_NAME, 'w') as file:
#             json.dump(Catalog.COURSES, file)
#
#     def load_from_file():
#         if os.path.exists(Catalog.FILE_NAME):
#             with open(Catalog.FILE_NAME, 'r') as file:
#                 Catalog.COURSES = json.load(file)


# class Catalog:
#
#     FILE_NAME = f'material\\catalog.v2.json'
#
#     def __init__(self, courses=None):
#         self.courses = courses or []
#         self.load_from_file()
#
#     def save_to_file(self):
#         with open(self.FILE_NAME, 'w') as file:
#             json.dump(self.courses, file)
#
#     def load_from_file(self):
#         if os.path.exists(self.FILE_NAME):
#             with open(self.FILE_NAME, 'r') as file:
#                 self.courses = json.load(file)
#
#     def add_course(self, course_num):
#         if len(self.courses) == course_num:
#             self.courses.append([])
#             self.save_to_file()
#
#     def add_modules(self, course_num, num_of_module):
#         if not self.courses[course_num]:
#             for i in range(num_of_module):
#                 self.courses[course_num].append([])
#             self.save_to_file()
#
#     def add_lessons(self, course_num, module_num, num_of_lessons):
#         self.courses[course_num][module_num] = [False for i in range(num_of_lessons)]
#         self.save_to_file()
#
#     def complete_lesson(self, course_num, module_num, lesson_num):
#         self.courses[course_num][module_num][lesson_num] = True
#         self.save_to_file()
#
#     def is_module_complete(self, course_num, module_num):
#         return (False not in self.courses[course_num][module_num]) and self.courses[course_num][module_num]
#
#     def is_course_complete(self, course_num):
#         return False not in [self.courses[course_num][module_num] for module_num in range(len(self.courses[course_num]))]

class Course:

    def __init__(self, number: int, element: WebElement, parent_folder: Folder):
        self.number = number
        self.element = element
        self.parent_folder = parent_folder

        texts = element.text.split("\n")
        self.name = f'{number}. {texts[1]}'
        self.folder = Folder(name=self.name, parent=self.parent_folder)
        self.num_of_modules = int(texts[2].split(' ')[0])
        Catalog.add_course(self.number, self.num_of_modules)

        self.url = element.find_element(By.CLASS_NAME, 'card-title').get_attribute('href')

    @staticmethod
    def find_modules():
        time.sleep(5)
        elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "box")))
        modules = list(filter(lambda element: element.text, elements))
        return modules

    def save(self):
        if not Catalog.is_course_complete(self.number):
            driver.switch_to.new_window('tab')
            driver.get(self.url)
            modules = self.find_modules()
            for i, m in enumerate(modules):
                if not Catalog.is_module_complete(self.number, i):
                    module = Module(i, m, self.folder, self)
                    module.save()
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])


class Module:
    def __init__(self, number: int, element: WebElement, parent_folder: Folder, course: Course):
        self.number = number
        self.element = element
        self.parent_folder = parent_folder

        input()

    def save(self):
        pass


def find_courses() -> list[WebElement]:
    time.sleep(2)
    elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-template")))
    courses = list(filter(lambda element: element.text, elements))

    return courses


def main():
    driver.get("https://learn.microsoft.com/en-us/credentials/certifications/exams/az-305/")
    courses = find_courses()
    Catalog.load_from_file()
    work_dir = Folder('material', ROOT_DIR)

    for i, c in enumerate(courses):
        course = Course(i, c, work_dir)
        course.save()
        input()


if __name__ == '__main__':
    main()
