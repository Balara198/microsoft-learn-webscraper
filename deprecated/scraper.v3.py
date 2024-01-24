from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as rq
import json
import os
import logging
import time

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

    def __init__(self, name: str, path: str):

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

    def create_folder_if_not_exists(self, name):
        return Folder(name, self.full_path)


class Catalog:
    FILE_NAME = f'../material/catalog.v2.json'

    def __init__(self):
        self.courses = []
        self.load_from_file()

    def _course_registered(self, course_num):
        return len(self.courses) > course_num

    def register_course(self, course_num, n_modules):
        if not self._course_registered(course_num):
            self.courses.append({"n_modules": n_modules, "modules": []})
            self.save_to_file()

    def _module_registered(self, course_num, module_num):
        return len(self.courses[course_num]["modules"]) > module_num

    def register_module(self, course_num, module_num, n_lessons):
        if not self._module_registered(course_num, module_num):
            self.courses[course_num]["modules"][module_num] = {"lessons": [False for i in range(n_lessons)]}
            self.save_to_file()

    def complete_lesson(self, course_num, module_num, lesson_num):
        self.courses[course_num]["modules"][module_num]["lessons"][lesson_num] = True
        self.save_to_file()

    def is_module_complete(self, course_num, module_num):
        return False not in self.courses[course_num]["modules"][module_num]["lessons"]

    def is_course_complete(self, course_num):
        if not self._course_registered(course_num):
            return False
        n_modules = self.courses[course_num]["n_modules"]
        for n in range(n_modules):
            if not self._module_registered(course_num, n):
                return False
            if not self.is_module_complete(course_num, n):
                return False
        return True

    def save_to_file(self):
        with open(self.FILE_NAME, 'w') as file:
            json.dump(self.courses, file)

    def load_from_file(self):
        if os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, 'r') as file:
                self.courses = json.load(file)


class Course:

    def __init__(self, num: int, element: WebElement, catalog: Catalog, parent_folder: Folder):
        self.num = num
        self.catalog = catalog

        texts = element.text.split("\n")
        name = f'{self.num}. {texts[1]}'
        self.n_modules = int(texts[2].split(' ')[0])
        self.folder = parent_folder.create_folder_if_not_exists(name)
        self.catalog.register_course(self.num, self.n_modules)

        self.url = element.find_element(By.CLASS_NAME, 'card-title').get_attribute('href')

    @staticmethod
    def find_module_elements():
        time.sleep(5)
        elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "box")))
        return list(filter(lambda element: element.text, elements))

    def save(self):
        if not self.catalog.is_course_complete(self.num):
            driver.switch_to.new_window('tab')
            driver.get(self.url)
            module_elements = self.find_module_elements()
            if len(module_elements) != self.n_modules:
                raise ValueError(f"A kurzus {self.n_modules} modullal rendelkezik, de {len(module_elements)} modul lett megtalálva.")
            for i, module_element in enumerate(module_elements):
                if not self.catalog.is_module_complete(self.num, i):
                    module = Module(i, module_element, self.folder, self)
                    module.save()
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])


class Module:
    def __init__(self, num: int, element: WebElement, catalog: Catalog, course: Course):
        self.num = num
        self.catalog = catalog
        self.course = course

        texts = element.text.split('\n')
        name = f'{self.num}. {texts[1]}'
        self.n_lessons = int(texts[4].split(' ')[0])
        self.folder = self.course.folder.create_folder_if_not_exists(name)
        self.catalog.register_module(self.course.num, self.num, self.n_lessons)

        self.url = element.find_element(By.CLASS_NAME, 'display-block').get_attribute('href')

    @staticmethod
    def find_lesson_elements():
        time.sleep(2)
        
