import os
import logging


class Lesson:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def is_completed(self):
        return os.path.exists(self.path)

    def to_json(self):
        return {"completed": self.is_completed(), "name": self.name, "path": self.path}

    @staticmethod
    def load_from_json(lesson: dict):
        name = lesson["name"]
        path = lesson["path"]
        return Lesson(name, path)

class Module:

    def __init__(self, name, path, num_of_lessons, lessons: [Lesson] = []):
        self.name = name
        self.path = path
        self.num_of_lessons = num_of_lessons
        self.lessons: [Lesson] = lessons

    def is_completed(self):
        if os.path.exists(self.path):
            if False not in [lesson.is_completed() for lesson in self.lessons]:
                return len(self.lessons) == self.num_of_lessons
        return False

    def lesson_exists(self, lesson_num):
        return lesson_num < len(self.lessons)

    def lesson_completed(self, lesson_num):
        return self.lesson_exists(lesson_num) and self.lessons[lesson_num].is_completed()

    def add_lesson(self, lesson_num, name, path):
        if not self.lesson_exists(lesson_num):
            if lesson_num != len(self.lessons):
                raise Exception("Lesson tried to be added too soon.")
            self.lessons.append(Lesson(name, path))
        else:
            lesson: Lesson = self.lessons[lesson_num]
            lesson_name = lesson.name
            message = f'Lesson "{name} already exists.' if name == lesson_name else \
                f'Lesson "{name}" already exists, but under the name: "{lesson_name}"'
            logging.warning(message)

    def to_json(self):
        lessons = list(map(Lesson.to_json, self.lessons))
        return {"name": self.name,
                "path": self.path,
                "num_of_lessons": self.num_of_lessons,
                "lessons": lessons}

    @staticmethod
    def load_from_json(module: dict):
        name = module["name"]
        path = module["path"]
        num_of_lessons = module["num_of_lessons"]
        lessons = list(map(Lesson.load_from_json, module["lessons"]))
        return Module(name, path, num_of_lessons, lessons)

class Course:

    def __init__(self, name, path, num_of_modules, modules: [Module] = []):
        self.name = name
        self.path = path
        self.num_of_modules = num_of_modules
        self.modules = modules

    def is_completed(self):
        if os.path.exists(self.path):
            if False not in [module.is_completed() for module in self.modules]:
                return len(self.modules) == self.num_of_modules
        return False

    def module_exists(self, module_num):
        return module_num < len(self.modules)

    def lesson_exists(self, module_num, lesson_num):
        return self.modules[module_num].lesson_exists(lesson_num)

    def module_completed(self, module_num):
        return self.module_exists(module_num) and self.modules[module_num].is_complete()

    def lesson_completed(self, module_num, lesson_num):
        return self.lesson_exists(module_num, lesson_num) and self.modules[module_num].lesson_completed(lesson_num)

    def add_module(self, module_num, name, path, num_of_lessons):
        if not self.module_exists(module_num):
            self.modules.append(Module(name, path, num_of_lessons))
            if module_num != len(self.modules):
                f'Cannot added {module_num}. module to course "{name}". Next module must be the {len(self.modules)}. one.'
        else:
            module: Module = self.modules[module_num]
            lesson_name = module.name
            message = f'Lesson "{name} already exists.' if name == lesson_name else \
                f'Lesson "{name}" already exists, but under the name: "{lesson_name}"'
            logging.warning(message)

    def add_lesson(self, module_num, lesson_num, name, path):
        if not self.module_exists(module_num):
            message = f'{lesson_num}. lesson of {module_num}. module cannot be added to course "{self.name}", becasue'\
                      f' {module_num}. module not exists. Number of modules of this course is: {len(self.modules)}.'
            raise Exception(message)
        if not self.lesson_exists(module_num, lesson_num):
            self.modules[module_num].add_lesson(name, path)

    def to_json(self):
        return {"name": self.name,
                "path": self.path,
                "num_of_modules": self.num_of_modules,
                "modules": list(map(Module.to_json, self.modules))}

    @staticmethod
    def load_from_json(course: dict):
        name = course["name"]
        path = course["path"]
        num_of_modules = course["num_of_modules"]
        modules = list(map(Module.load_from_json, course["modules"]))
        return Course(name, path, num_of_modules, modules)