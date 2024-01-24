import json
import os


from CatalogItems import Course, Module, Lesson

FILE_NAME = f'../../catalog.v2.json'

COURSES: [Course] = []


def _course_exists(course_num):
    return len(COURSES) > course_num


def add_course(name, path, course_num, n_modules):
    if not _course_exists(course_num):
        COURSES.append(Course(name, path, n_modules))
        save_to_file()


# def _module_exists(course_num, module_num):
#     return len(COURSES[course_num].modules) > module_num


def add_module(course_num, module_num, name, path, num_of_lessons):
    # if not _module_exists(course_num, module_num):
    #     COURSES[course_num].add_module(name, path, num_of_lessons)
    #     save_to_file()
    c: Course = COURSES[course_num]
    c.add_module(module_num, name, path, num_of_lessons)

def add_lesson(course_num, module_num, lesson_num, name, path):
    c: Course = COURSES[course_num]
    c.add_lesson(module_num, lesson_num, name, path)

def is_module_complete(course_num, module_num):
    return COURSES[course_num].modules[module_num].is_completed()


def is_course_complete(course_num):
    if not _course_exists(course_num):
        return False
    return COURSES[course_num].is_completed()


def to_json():
    return list(map(Course.to_json, COURSES))


def load_from_json(_json: list):
    return list(map(Course.load_from_json, _json))


def save_to_file():
    with open(FILE_NAME, 'w') as file:
        json.dump(to_json(), file)


def load_from_file():
    global COURSES
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as file:
            COURSES = load_from_json(json.load(file))
