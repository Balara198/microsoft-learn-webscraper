import time

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import requests as rq

def save_lesson(path: str, identifier: str, name: str, driver: WebDriver):
    """
    :param path: Path of the folder, the lesson will be saved.
    :param identifier: Numeric identifier of the lesson in the following format: <course_num>.<module_num>.lesson<num>
    :param name: Name of the lesson.
    :param driver: Webdriver instance to reach the page.
    :return: None
    """

    css_name = f"{name}.css"
    html_name = f"{name}.html"

    # The following element is referring to the .css file containing the style information for the page.
    stylesheet_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "link[rel='stylesheet']")))
    # Saving the .css
    with open(f"{path}\\{css_name}", "wb") as css_file:
        stylesheet_url = stylesheet_element.get_attribute("href")
        css_file.write(rq.get(stylesheet_url).content)

    # Finding the HTML container of the content, and creating a bs4 object to parse it.
    content_sel = driver.find_element(By.CSS_SELECTOR,
                                            "div.modular-content-container.has-body-background.box")
    content = content_sel.get_attribute("outerHTML")
    content_bs4 = BeautifulSoup(content, 'html.parser')


def process_images(content_sel: WebElement, content_bs4: BeautifulSoup, identifier: str, path: str) -> None:
    images_bs4 = content_bs4.find_all("img", {"src": True})
    images_sel = content_sel.find_elements(By.CSS_SELECTOR, "img[src]")
    images_idx = range(len(images_sel))

    for img_idx, img_bs4, img_sel in zip(images_idx, images_bs4, images_sel):
        url = img_sel.get_attribute("src")
        img_ext = url.split(".")[-1]
        img_name = f"{identifier}.{img_idx}.{img_ext}"
        with open(f"{path}\\{img_name}", "wb") as img_file:
            resp = rq.get(url)
            img_file.write(resp.content)
        img_bs4["src"] = img_name


def save_videos(content_sel: WebElement, content_bs4: BeautifulSoup, identifier: str, path: str, driver: WebDriver) -> str:
    video_containers_bs4 = content_bs4.find_all("div", {"class": "embeddedvideo"})
    video_containers_sel = content_sel.find_elements(By.CLASS_NAME, "embeddedvideo")
    video_containers_idx = range(len(video_containers_sel))

    for vid_idx, vid_bs4, vid_sel in zip(video_containers_idx, video_containers_bs4, video_containers_sel):
        video_identifier = f"{identifier}.{vid_idx}"

        url = vid_sel.find_element(By.TAG_NAME, "iframe").get_attribute("src")
        driver.switch_to.new_window("tab")
        driver.get(url)
        time.sleep(1)

        save_video_poster(driver=driver, identifier=video_identifier, path=path)

        driver.find_element(By.TAG_NAME, "button").click()
        download_button = WebDriverWait(
            driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-info$='.mp4']")))
        video_url = download_button.get_attribute("data-info")
        if video_url.startswith('//'):
            video_url = "https:" + video_url
        elif not video_url.startswith('http'):
            raise Exception(f'Unknown video url format: {video_url}')


def save_video_poster(driver: WebDriver, identifier: str, path: str) -> None:
    poster_url = driver.find_element(By.CSS_SELECTOR, "video.f-video-player").get_attribute("poster")
    if poster_url.startswith("//"):
        poster_url = "https:" + poster_url
    elif not poster_url.startswith("http"):
        raise Exception(f'Unknown poster url format: {poster_url}')

    poster_name = f"poster.{identifier}.png"
    with open(f"{path}\\{poster_name}", "wb") as poster_file:
        poster_file.write(rq.get(poster_url).content)
