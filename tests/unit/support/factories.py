from uuid import uuid4

from app.domain.entities import User, UserRole
from app.domain.entities.course import Course
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section
from tests.unit.support.fakes import FakeUnitOfWork


class UserFactory:

    def get_admin(self, **fields) -> User:
        return User(**{'id': uuid4(), 'email': 'admin@example.com', 'hashed_password': 'hashed::x', 'role': UserRole.ADMIN, **fields})

    def get_student(self, **fields) -> User:
        return User(**{'id': uuid4(), 'email': 'student@example.com', 'hashed_password': 'hashed::x', 'role': UserRole.STUDENT, **fields})



class ContentFactory:
    """Создаёт сущности прямо в FakeUnitOfWork и сразу связывает их с родителем.

    Позиция по умолчанию — следующая свободная, заголовок — по порядку.
    Любое поле можно переопределить: await content.module(course, position=1, title="Intro").
    """

    def __init__(self, uow: FakeUnitOfWork) -> None:
        self.uow = uow

    async def course(self, **fields) -> Course:
        course = Course(**{'id': uuid4(), 'title': 'Course', 'description': 'Description', **fields})

        await self.uow.courses.add(course)
        return course

    async def module(self, course: Course, **fields) -> Module:
        position = len(course.module_ids) + 1
        module = Module(**{'id': uuid4(), 'course_id': course.id, 'title': f'Module {position}',
                           'description': 'Description', 'position': position, **fields})

        course.add_module(module.id)
        await self.uow.modules.add(module)
        return module

    async def section(self, module: Module, **fields) -> Section:
        position = len(module.section_ids) + 1
        section = Section(**{'id': uuid4(), 'module_id': module.id, 'title': f'Section {position}',
                             'description': 'Description', 'position': position, **fields})

        module.add_section(section.id)
        await self.uow.sections.add(section)
        return section

    async def lecture(self, section: Section, **fields) -> Lecture:
        position = len(section.lecture_ids) + 1
        lecture = Lecture(**{'id': uuid4(), 'section_id': section.id, 'title': f'Lecture {position}',
                             'content': 'Content', 'position': position, **fields})

        section.add_lecture(lecture.id)
        await self.uow.lectures.add(lecture)
        return lecture