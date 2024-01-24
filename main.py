from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as rq
from bs4 import BeautifulSoup

import os
import logging
import time

import Catalog

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
        self.full_path = None
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


def save_course(num: int, element: WebElement, parent_folder: Folder):
    element_texts = element.text.split("\n")

    num_of_modules = int(element_texts[2].split(' ')[0])
    name = element_texts[1]
    folder_name = f'{num}. {name}'
    folder = Folder(name=folder_name, parent=parent_folder)
    Catalog.add_course(num, name, folder.full_path, num_of_modules)

    url = element.find_element(By.CLASS_NAME, 'card-title').get_attribute('href')

    # Saving modules
    driver.switch_to.new_window('tab')
    driver.get(url)
    time.sleep(2)
    elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "box")))
    module_elements = list(filter(lambda e: e.text, elements))

    if num_of_modules != len(module_elements):
        raise Exception(
            f"Module number mismatch: course have {num_of_modules} modules, but {len(module_elements)} was found.")

    while Catalog.has_next_module(num):
        module_num = Catalog.next_module(num)
        save_module(num, module_num, module_elements[module_num], folder)

    driver.close()
    driver.switch_to.window(driver.window_handles[-1])


def save_module(course_num: int, num: int, element: WebElement, parent_folder: Folder):
    element_texts = element.text.split('\n')

    name = element_texts[1]
    num_of_lessons = int(element_texts[4].split(' ')[0])
    folder_name = f'{num}. {name}'
    folder = Folder(name=folder_name, parent=parent_folder)
    Catalog.add_module(course_num, num, name, folder.full_path, num_of_lessons)

    display_blocks = element.find_elements(By.CLASS_NAME, "display-block")
    url_container = list(filter(lambda x: x.text == name, display_blocks))[0]
    url = url_container.get_attribute("href")

    # Saving lessons
    driver.switch_to.new_window('tab')
    driver.get(url)
    time.sleep(2)
    lesson_elements = driver.find_elements(By.CLASS_NAME, "module-unit")

    if num_of_lessons != len(lesson_elements):
        raise Exception(
            f"Lesson number mismatch: module have {num_of_lessons} lessons, but {len(lesson_elements)} was found.")

    while Catalog.has_next_lesson(course_num, num):
        lesson_num = Catalog.next_lesson(course_num, num)
        save_lesson(course_num, num, lesson_num, lesson_elements[lesson_num], folder)

    driver.close()
    driver.switch_to.window(driver.window_handles[-1])


def save_lesson(course_num: int, module_num: int, num: int, element: WebElement, parent_folder: Folder):
    name = element.text.split('\n')[0]
    file_name = f'{num}. {name}'
    parent_path = parent_folder.full_path
    html_path = f'{parent_path}\\{file_name}.html'
    css_path = f'{parent_path}\\{file_name}.css'

    Catalog.add_lesson(course_num, module_num, num, name, html_path)

    url = element.find_element(By.CLASS_NAME, "unit-title").get_attribute("href")

    driver.switch_to.new_window('tab')
    driver.get(url)

    if name == "Knowledge check":
        with open(html_path, "w"):
            pass

    else:
        stylesheet_element = driver.find_element(By.CSS_SELECTOR, "link[rel='stylesheet']")

        with open(css_path, "wb") as f:
            stylesheet_url = stylesheet_element.get_attribute("href")
            f.write(rq.get(stylesheet_url).content)

        with open(html_path, "w", encoding='utf-8') as f:
            stylesheet_soup = BeautifulSoup(stylesheet_element.get_attribute('outerHTML'), 'html.parser')
            stylesheet_soup.find('link')["href"] = f'{file_name}.css'
            f.write(str(stylesheet_soup))

            content_panel = driver.find_element(By.CSS_SELECTOR,
                                                "div.modular-content-container.has-body-background.box")
            content = content_panel.get_attribute('outerHTML')
            f.write(content)

    driver.close()
    driver.switch_to.window(driver.window_handles[-1])


def delete_content_media(html: str):
    selectors = [
        "div.xp-tag-hexagon",
        "span.docon.docon-status-warning-outline",
        "span.docon.docon-status-error-outline",
        "span.docon.docon-status-info-outline"
        "span.docon.docon-lightbulb",
        "button.action.position-relative.display-none-print",
        "div#next-section",
        "div.buttons.buttons-right.margin-bottom-none.margin-top-sm"
    ]


def download_video():
    # Példa a 0.0.1 lesson-ben
    video_container = driver.find_element(By.CLASS_NAME, "embeddedvideo")
    # TODO:
    #  - switch to iframe
    #  - get iframe's "src" attribute
    #  - Open the video on new tab
    #  - Start the video, stop it and click on download by imitating key-presses:
    #    * TAB -> ENTER -> ENTER -> TAB -> TAB -> ENTER -> ENTER -> DOWN -> DOWN -> ENTER
    #  - --New tab opened with the source video-- switch to last window handler.
    #  - Imitate key-presses to stop and download the video:
    #    * SPACE -> TAB -> TAB -> TAB -> TAB -> TAB -> ENTER -> ENTER -> ENTER
    #  - Close tab.
    #  - Switch to last window handler.
    #  - Close tab.
    video_iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[title='Video Player']")
    n = 0
    video_iframe = video_iframes[n]
    video_url = video_iframe.get_attribute("src")
    driver.switch_to.new_window('tab')
    driver.get(video_url)
    time.sleep(1)
    driver.find_element(By.TAG_NAME, "button").click()
    download_button = WebDriverWait(
        driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-info$='.mp4']")))
    video_url = download_button.get_attribute("data-info")
    if video_url.startswith('//'):
        video_url = "https:" + video_url
    else:
        raise Exception(f'Unknown video url format: {video_url}')
    resp = rq.get(video_url)
    # TODO with open ...

    # At the end switch back
    driver.switch_to.default_content()


def find_courses() -> list[WebElement]:
    time.sleep(2)

    see_more_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-title='See more']")))
    see_more_button.click()

    courses = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-template")))
    return courses


def main():
    driver.get("https://learn.microsoft.com/en-us/credentials/certifications/exams/az-305/")
    course_elements = find_courses()

    Catalog.NUM_OF_COURSES = len(course_elements)
    Catalog.load_from_json()

    work_dir = Folder('material', ROOT_DIR)

    while Catalog.has_next_course():
        num = Catalog.next_course()
        save_course(num, course_elements[num], work_dir)


def experiment():
    driver.get("https://learn.microsoft.com/en-us/training/modules/"
               "describe-core-architectural-components-of-azure/3-get-started-azure-accounts")

    module_num = 0
    num = 1

    work_dir = Folder('test-material', ROOT_DIR)
    path = work_dir.full_path
    css_name = "test.css"
    html_name = "test.html"

    stylesheet_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "link[rel='stylesheet']")))
    with open(f"{path}\\{css_name}", "wb") as f:
        stylesheet_url = stylesheet_element.get_attribute("href")
        f.write(rq.get(stylesheet_url).content)

    stylesheet_soup = BeautifulSoup(stylesheet_element.get_attribute('outerHTML'), 'html.parser')
    stylesheet_soup.find('link')["href"] = css_name

    content_panel = driver.find_element(By.ID, "unit-inner-section")
    content = content_panel.get_attribute('outerHTML')
    content_soup = BeautifulSoup(content, 'html.parser')

    images_bs4 = content_soup.find_all("img", {"src": True})
    images_sel = content_panel.find_elements(By.CSS_SELECTOR, "img[src]")
    images_idx = range(len(images_sel))

    for i, bs4_img, sel_img in zip(images_idx, images_bs4, images_sel):
        url = sel_img.get_attribute("src")
        img_ext = url.split(".")[-1]
        img_name = f"{module_num}.{num}.{i}.{img_ext}"
        with open(f"{path}\\{img_name}", "wb") as img_file:
            resp = rq.get(url)
            img_file.write(resp.content)
        bs4_img["src"] = img_name

    video_containers_bs4 = content_soup.find_all("div", {"class": "embeddedvideo"})
    video_containers_sel = driver.find_elements(By.CLASS_NAME, "embeddedvideo")
    video_containers_idx = range(len(video_containers_sel))

    for i, bs4_video_con, sel_video_con in zip(video_containers_idx, video_containers_bs4, video_containers_sel):
        url = sel_video_con.find_element(By.TAG_NAME, "iframe").get_attribute("src")
        driver.switch_to.new_window("tab")
        driver.get(url)

        time.sleep(1)

        poster_url = driver.find_element(By.CSS_SELECTOR, "video.f-video-player").get_attribute("poster")
        if poster_url.startswith("//"):
            poster_url = "https:"+poster_url
        elif poster_url.startswith("http"):
            pass
        else:
            raise Exception(f'Unknown poster url format: {poster_url}')
        poster_name = f"poster.{module_num}.{num}.{i}.png"
        with open(f"{path}\\{poster_name}", "wb") as poster_file:
            poster_file.write(rq.get(poster_url).content)

        driver.find_element(By.TAG_NAME, "button").click()
        download_button = WebDriverWait(
            driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-info$='.mp4']")))
        video_url = download_button.get_attribute("data-info")
        if video_url.startswith('//'):
            video_url = "https:" + video_url
        else:
            raise Exception(f'Unknown video url format: {video_url}')
        resp = rq.get(video_url)
        video_name = f"video.{module_num}.{num}.{i}.mp4"
        with open(f"{path}\\{video_name}", "wb") as video_file:
            video_file.write(resp.content)

        video_ref = content_soup.new_tag("a", href=video_name)
        # TODO resize the image
        poster_tag = content_soup.new_tag("img", src=poster_name)
        video_ref.append(poster_tag)
        bs4_video_con.replace_with(video_ref)

    with open(f"{path}\\{html_name}", "w", encoding='utf-8') as f:
        f.write(str(stylesheet_soup))

        f.write(str(content_soup))

    # TODO delete icons and unnecessary elements.
    driver.get(f"{path}\\{html_name}")
    input()


def validate():
    path = os.path.abspath("material")
    for course in os.listdir(path):
        course_path = f'{path}\\{course}'
        for module in os.listdir(course_path):
            module_path = f'{course_path}\\{module}'
            lesson_files = os.listdir(module_path)
            lessons = filter(lambda s: s.endswith(".html"), lesson_files)
            for lesson in lessons:
                lesson_path = f'{module_path}\\{lesson}'
                driver.get(lesson_path)
                input('Nyomj meg egy gombot a követező megnyitásához.')

# main()
# experiment()
validate()
