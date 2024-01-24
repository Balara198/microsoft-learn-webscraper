from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as rq
import os

service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
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
        self.full_path = f'{self.path}/{self.name}'

    def update_catalog(self, child: 'FileLike' = None, complete: bool = False):
        if child is None:
            ret = {'name': self.name, 'original_name': self.original_name, 'path': self.path, 'complete': complete}
        else:
            ret = child

        if self.parent is not None:
            self.parent.update_catalog(ret)

    def clean_name(self):
        name = ''.join(filter(lambda x: x not in self.ILLEGAL_CHARACTERS, self.original_name))
        name = name[:self.MAX_FILENAME_LENGTH]
        return name


class Folder(FileLike):

    def __init__(self, name: str, path: str = None, parent: 'Folder' = None):
        super().__init__(name=name, path=path, parent=parent)
        self.create_if_not_exists()

    def create_if_not_exists(self):
        if not os.path.isdir(self.full_path):
            os.mkdir(self.full_path)
            self.update_catalog()

    def create_file(self, name: str, extension: str = None):
        return File(name=name, extension=extension, parent=self)

    def create_folder(self, name: str):
        return Folder(name=name, parent=self)


class RootFolder(Folder):

    def __init__(self, name: str, path: str):
        super().__init__(name=name, path=path)


class File(FileLike):

    def __init__(self, name: str, extension: str = None, path: str = None, parent: Folder = None):
        if extension is None:
            self.extension = name.split('.')[-1]
        else:
            self.extension = extension
            name = f'{name}.{self.extension}'
        super().__init__(name=name, path=path, parent=parent)

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
        self.update_catalog(complete=True)


def find_modules():
    elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "box")))
    modules = filter(lambda element: element.text, elements)
    return list(modules)


class Course:
    def __init__(self, number: int, element: WebElement, root_folder: RootFolder):
        self.number = number
        self.element = element
        self.root_folder = root_folder

        texts = element.text.split("\n")
        self.name = f'{number}. {texts[1]}'
        self.num_of_modules = int(texts[2].split(' ')[0])
        self.url = element.find_element(By.CLASS_NAME, 'button').get_attribute('href')

    def save(self):
        driver.switch_to.new_window('tab')
        driver.get(self.url)
        modules = find_modules()
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])


class Module:
    def __init__(self, number: int, element: WebElement, folder: Folder):
        self.number = number
        self.element = element
        self.folder = folder


def find_courses() -> list[WebElement]:
    elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-template")))
    courses = filter(lambda element: element.text, elements)
    return list(courses)


def main():
    work_dir = Folder('material', ROOT_DIR)
    catalog = work_dir.create_file('catalog.json')

    driver.get("https://learn.microsoft.com/en-us/credentials/certifications/exams/az-305/")

    courses = find_courses()


if __name__ == '__main__':
    main()
