from dataclasses import dataclass
from uuid import uuid4

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities.course import Course


@dataclass(slots=True)
class CreateCourseCommand:
    title: str
    description: str


class CreateCourseUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: CreateCourseCommand) -> Course:
        user = await self.access.ensure_can_create_course()

        course = Course(
            id=uuid4(),
            author_id=user.id,
            title=command.title,
            description=command.description,
        )
        await self.uow.courses.add(course)
        await self.uow.commit()
        return course
