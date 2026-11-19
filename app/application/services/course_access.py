from uuid import UUID

from app.application.exceptions import (
    CourseNotFoundError,
    CourseModuleNotFoundError,
    SectionNotFoundError, AccessDeniedError, QuestionNotFoundError, LectureNotFoundError,
)
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities import User, Question, Lecture
from app.domain.entities.course import Course
from app.domain.entities.module import Module
from app.domain.entities.section import Section


class CourseAccessService:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def ensure_can_create_course(self) -> User:
        user = await self.idp.get_current_user()
        if not user.can_manage_learning_content():
            raise AccessDeniedError('User cannot create courses.')
        return user

    def check_course(self, user: User, course: Course) -> None:
        if not user.can_manage_course(course):
            raise AccessDeniedError('User cannot manage this course.')

    async def ensure_can_manage_course(self, course_id: UUID,) -> Course:
        user = await self.idp.get_current_user()
        course = await self.uow.courses.get_by_id(course_id)

        if course is None:
            raise CourseNotFoundError('Course not found.')

        self.check_course(user, course)

        return course

    async def ensure_can_manage_module(self, module_id: UUID,) -> Module:
        module = await self.uow.modules.get_by_id(module_id)
        if module is None:
            raise CourseModuleNotFoundError('Module not found.')

        await self.ensure_can_manage_course(module.course_id)
        return module

    async def ensure_can_manage_section(self, section_id: UUID,) -> Section:
        section = await self.uow.sections.get_by_id(section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        await self.ensure_can_manage_module(section.module_id)
        return section

    async def ensure_can_manage_question(self, question_id: UUID) -> Question:
        question = await self.uow.questions.get_by_id(question_id)
        if question is None:
            raise QuestionNotFoundError('Question not found.')
        await self.ensure_can_manage_section(question.section_id)
        return question

    async def ensure_can_manage_lecture(self, lecture_id: UUID) -> Lecture:
        lecture = await self.uow.lectures.get_by_id(lecture_id)
        if lecture is None:
            raise LectureNotFoundError('Lecture not found.')
        await self.ensure_can_manage_section(lecture.section_id)
        return lecture
