import json
import os


class Lesson:
    def __init__(self, num, name, path):
        self.num = num
        self.name = name
        self.path = path

    def is_completed(self):
        return os.path.exists(self.path)

    def to_json(self):
        return {"completed": self.is_completed(), "num": self.num, "name": self.name, "path": self.path}

    @staticmethod
    def load_from_json(lesson: dict):
        num = lesson["num"]
        name = lesson["name"]
        path = lesson["path"]
        return Lesson(num, name, path)


class Module:
    def __init__(self, num, name, path, num_of_lessons, lessons=None):
        if lessons is None:
            lessons = []
        self.num = num
        self.name = name
        self.path = path
        self.num_of_lessons = num_of_lessons
        self.lessons: [Lesson] = lessons

    def exists(self):
        return os.path.exists(self.path)

    def is_completed(self):
        exists = self.exists()
        all_lessons_added = len(self.lessons) == self.num_of_lessons
        lessons_completed = all(map(Lesson.is_completed, self.lessons))
        return exists and all_lessons_added and lessons_completed

    def add_lesson(self, lesson: Lesson):
        lesson_num = lesson.num
        if lesson_num < len(self.lessons):
            self.lessons[lesson_num] = lesson
        elif lesson_num == len(self.lessons):
            self.lessons.append(lesson)
        else:
            raise Exception("Lesson added too soon.")

    def next_lesson(self):
        for i, lesson in enumerate(self.lessons):
            if not lesson.is_completed():
                return i
        if len(self.lessons) >= self.num_of_lessons:
            return -1
        return len(self.lessons)

    def to_json(self):
        lessons = list(map(Lesson.to_json, self.lessons))
        return {"num": self.num,
                "name": self.name,
                "path": self.path,
                "num_of_lessons": self.num_of_lessons,
                "lessons": lessons}

    @staticmethod
    def load_from_json(module: dict):
        num = module["num"]
        name = module["name"]
        path = module["path"]
        num_of_lessons = module["num_of_lessons"]
        lessons = list(map(Lesson.load_from_json, module["lessons"]))
        return Module(num, name, path, num_of_lessons, lessons)


class Course:
    def __init__(self, num, name, path, num_of_modules, modules: [Module] = None):
        if modules is None:
            modules = []
        self.num = num
        self.name = name
        self.path = path
        self.num_of_modules = num_of_modules
        self.modules: [Module] = modules

    def exists(self):
        return os.path.exists(self.path)

    def is_completed(self):
        exists = self.exists()
        all_modules_added = self.num_of_modules == len(self.modules)
        modules_completed = all(map(Module.is_completed, self.modules))
        return exists and all_modules_added and modules_completed

    def add_module(self, module: Module):
        module_num = module.num
        if module_num == len(self.modules):
            self.modules.append(module)
        elif module_num > len(self.modules):
            raise Exception("Module added too soon.")

    def next_module(self):
        for i, module in enumerate(self.modules):
            if not module.is_completed():
                return i
        if len(self.modules) >= self.num_of_modules:
            return -1
        return len(self.modules)

    def to_json(self):
        return {"num": self.num,
                "name": self.name,
                "path": self.path,
                "num_of_modules": self.num_of_modules,
                "modules": list(map(Module.to_json, self.modules))}

    @staticmethod
    def load_from_json(course: dict):
        num = course["num"]
        name = course["name"]
        path = course["path"]
        num_of_modules = course["num_of_modules"]
        modules = list(map(Module.load_from_json, course["modules"]))
        return Course(num, name, path, num_of_modules, modules)


FILE_NAME = f'catalog.v2.json'
COURSES: [Course] = []
NUM_OF_COURSES = 0


def _next(course_num=None, module_num=None):
    # Next course
    if course_num is None:
        for i, course in enumerate(COURSES):
            if not course.is_completed():
                return i
        if len(COURSES) >= NUM_OF_COURSES:
            return -1
        return len(COURSES)

    # Next module
    elif module_num is None:
        return COURSES[course_num].next_module()

    # Next lesson
    else:
        return COURSES[course_num].modules[module_num].next_lesson()


def next_course():
    course = _next()
    if course == -1:
        raise Exception("No more courses left.")
    return course


def next_module(course_num):
    module = _next(course_num)
    if module == -1:
        raise Exception("No more modules left.")
    return module


def next_lesson(course_num, module_num):
    lesson = _next(course_num, module_num)
    if lesson == -1:
        raise Exception("No more lessons left.")
    return lesson


def has_next_course():
    return _next() != -1


def has_next_module(course_num):
    return _next(course_num) != -1


def has_next_lesson(course_num, module_num):
    return _next(course_num, module_num) != -1


def add_course(num, name, path, num_of_modules):
    course = Course(num, name, path, num_of_modules)
    if num > len(COURSES):
        raise Exception("Course added too soon.")
    elif num == len(COURSES):
        COURSES.append(course)
    else:
        if not COURSES[num].exists():
            COURSES[num] = course

    to_json()


def add_module(course_num, num, name, path, num_of_lessons):
    module = Module(num, name, path, num_of_lessons)
    if course_num >= len(COURSES):
        raise Exception('Module cannot be added, because course not exists.')
    course: Course = COURSES[course_num]
    course.add_module(module)

    to_json()


def add_lesson(course_num, module_num, num, name, path):
    lesson = Lesson(num, name, path)
    if course_num >= len(COURSES):
        raise Exception('Lesson cannot be added, because course does not exists.')
    course: Course = COURSES[course_num]
    if module_num >= len(course.modules):
        raise Exception('Lesson cannot be added, because module does not exists.')
    module: Module = course.modules[module_num]
    module.add_lesson(lesson)

    to_json()


def to_json():
    with open(FILE_NAME, 'w') as file:
        courses_json = list(map(Course.to_json, COURSES))
        json.dump(courses_json, file)


def load_from_json():
    global COURSES
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as file:
            courses_json = json.load(file)
            COURSES = list(map(Course.load_from_json, courses_json))

