import json
import os

FILE_NAME = f'catalog.v2.json'

COURSES = []

def _course_exists(course_num):
    return len(COURSES) > course_num

def add_course(course_num, n_modules):
    if not _course_exists(course_num):
        COURSES.append({"n_modules": n_modules, "modules": []})
        save_to_file()

def _module_exists(course_num, module_num):
    return len(COURSES[course_num]["modules"]) > module_num

def add_module(course_num, module_num, n_lessons):
    if not _module_exists(course_num, module_num):
        COURSES[course_num]["modules"].append({"lessons": [False for i in range(n_lessons)]})
        save_to_file()

def complete_lesson(course_num, module_num, lesson_num):
    COURSES[course_num]["modules"][module_num]["lessons"][lesson_num] = True
    save_to_file()

def is_module_complete(course_num, module_num):
    return False not in COURSES[course_num]["modules"][module_num]["lessons"]

def is_course_complete(course_num):
    if not _course_exists(course_num):
        return False
    n_modules = COURSES[course_num]["n_modules"]
    for n in range(n_modules):
        if not _module_exists(course_num, n):
            return False
        if not is_module_complete(course_num, n):
            return False
    return True


def save_to_file():
    with open(FILE_NAME, 'w') as file:
        json.dump(COURSES, file)

def load_from_file():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as file:
            COURSES = json.load(file)
