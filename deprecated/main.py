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


class FileLike:
    ILLEGAL_CHARACTERS = ':"/\\|?*'
    MAX_FILENAME_LENGTH = 211

    def __init__(self, name: str, path: str = None, parent: 'Folder' = None):
        if parent is None == path is None:
            raise ValueError("path or parent must be provided, but not both of them.")
        if parent is not None:
            self.parent = parent
            self.path = parent.full_path
        else:
            self.path = path
        self.original_name = name
        self.name = self.clean_name()
        self.full_path = f'{self.path}\\{self.name}'

    def clean_name(self):
        name = ''.join(filter(lambda x: x not in self.ILLEGAL_CHARACTERS, self.original_name))
        name = name[:self.MAX_FILENAME_LENGTH]
        return name


class Folder(FileLike):

    def __init__(self, name: str, path: str = None, parent: 'Folder' = None):
        super().__init__(name=name, path=path, parent=parent)
        logging.info(f"FOLDER initialized with {'parent' if parent else 'path'} parameter at {self.full_path}")
        self.create_if_not_exists()

    def create_if_not_exists(self):
        if not os.path.isdir(self.full_path):
            os.mkdir(self.full_path)
            logging.info(f"\tCREATED")
        else:
            logging.info(f"\tNOT CREATED")

    def create_file(self, name: str, extension: str = None):
        return File(name=name, extension=extension, parent=self)

    def create_folder(self, name: str):
        return Folder(name=name, parent=self)


class File(FileLike):

    def __init__(self, name: str, extension: str = None, path: str = None, parent: Folder = None):
        if extension is None:
            self.extension = name.split('.')[-1]
        else:
            self.extension = extension
            name = f'{name}.{self.extension}'
        super().__init__(name=name, path=path, parent=parent)

        logging.info(f"FILE initialized with {'parent' if parent else 'path'} parameter at {self.full_path}")

    def clean_name(self):
        '''
        If the name of the file is too long (in windows 211 character is the maximum filename), then thes characters
        exceeding that size will be sliced off. As a result we might lose the file extensions from the filename, so the
        function have been overridden in case of the File class.
        '''
        name = ''.join(filter(lambda x: x not in self.ILLEGAL_CHARACTERS, self.original_name))
        name = name[:self.MAX_FILENAME_LENGTH]
        if not name.endswith(f'.{self.extension}'):
            extension_length = len(self.extension) + 1
            name = f'{name[:-extension_length]}.{self.extension}'
        return name

    def download(self, url):
        content = rq.get(url).content
        with open(self.full_path, 'wb') as f:
            f.write(content)
        logging.info(f"DOWNLOAD:\n\t\tFROM: {url}\n\t\tTO: {self.full_path}")


class Course:
    def __init__(self, number: int, element: WebElement, root_folder: Folder, catalog: 'Catalog'):
        self.number = number
        self.element = element
        self.root_folder = root_folder
        self.folder: Folder = None
        self.catalog = catalog

        texts = element.text.split("\n")
        self.name = f'{number}. {texts[1]}'
        self.num_of_modules = int(texts[2].split(' ')[0])
        self.url = element.find_element(By.CLASS_NAME, 'card-title').get_attribute('href')

        logging.info(f"COURSE_{self.number} initialized:")

        if not self.catalog.modules_added(self.number):
            logging.info(f"\t\t{self.num_of_modules} added.")
            self.catalog.add_modules(self.number, self.num_of_modules)
            self.folder = root_folder.create_folder(self.name)

        else:
            logging.info("\t\tModules already been added.")

    @staticmethod
    def find_modules():
        time.sleep(5)
        elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "box")))
        modules = list(filter(lambda element: element.text, elements))
        logging.info(f"\t\tFIND_MODULES: {len(modules)} modules found.")
        return modules

    def save(self):
        logging.info(f"COURSE: saving started!")
        if not self.catalog.is_course_complete(self.number):
            logging.info("\t\tIncomplete saving")
            driver.switch_to.new_window('tab')
            driver.get(self.url)
            modules = self.find_modules()
            for i, m in enumerate(modules):
                if not self.catalog.is_module_complete(self.number, i):
                    module = Module(i, m, self.folder, self)
                    module.save()
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
        else:
            logging.info("\t\tSaving already been completed")

    def complete_module(self, module_num):
        self.catalog.complete_module(self.number, module_num)


class Module:
    def __init__(self, number: int, element: WebElement, folder: Folder, course: Course):
        self.number = number
        self.element = element
        self.folder = folder
        self.course = course

        logging.info(f"\t\tMODULE: initalized.")

    def save(self):
        self.course.complete_module(self.number)
        logging.info("\t\t\t\tSAVING successful!")


WORK_DIR = Folder('material', ROOT_DIR)


class Catalog:
    FILE_NAME = f'{WORK_DIR.full_path}\\catalog.json'

    def __init__(self, courses: int):
        self.courses = [{'complete': False, 'modules': []} for i in range(courses)]
        self.open()

    def open(self):
        if os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, 'r') as file:
                self.courses = json.load(file)

    def save(self):
        with open(self.FILE_NAME, "w") as file:
            json.dump(self.courses, file)

    def is_course_complete(self, course_num: int):
        return self.courses[course_num]['complete']

    def modules_added(self, course_num):
        return len(self.courses[course_num]['modules']) != 0

    def add_modules(self, course_num, num_of_modules):
        self.courses[course_num]['modules'] = [False for i in range(num_of_modules)]
        self.save()

    def is_module_complete(self, course_num, module_num):
        return self.courses[course_num]['modules'][module_num]

    def complete_module(self, course_num, module_num):
        self.courses[course_num]['modules'][module_num] = True
        if False not in self.courses[course_num]['modules']:
            self.courses[course_num]['complete'] = True
        self.save()

    # def add_course(self, path: str):
    #     course_name = path.split('\\')[-1]
    #     if course_name not in self.courses:
    #         self.courses['course_name'] = {'modules':  {}, 'complete': False}
    #
    # def add_module(self, path: str):
    #     course_name, module_name = path.split('\\')[-2:]
    #     if course_name not in self.courses:
    #         raise ValueError(f'Parent course of module not exists\n\tpath:{path}')
    #     if module_name not in self.courses['course_name']['modules']:
    #         self.courses['course_name']['modules'][module_name] = {'complete': False}


def find_courses() -> list[WebElement]:
    time.sleep(2)
    elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-template")))
    courses = list(filter(lambda element: element.text, elements))
    for e in courses:
        logging.info("\t\tCOURSE_NAME: " + e.text.split('\n')[1])
    logging.info(f"FIND_COURSES: {len(courses)} courses found.")
    return courses


def main():
    driver.get("https://learn.microsoft.com/en-us/credentials/certifications/exams/az-305/")
    courses = find_courses()
    catalog = Catalog(len(courses))

    for i, c in enumerate(courses):
        course = Course(i, c, WORK_DIR, catalog)
        course.save()
        input()


if __name__ == '__main__':
    main()
