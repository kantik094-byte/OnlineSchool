from dataclasses import dataclass
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities.course import Course


@dataclass(slots=True)
class UpdateCourseCommand:
    course_id: UUID
    title: str
    description: str


class UpdateCourseUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: UpdateCourseCommand) -> Course:
        course = await self.access.ensure_can_manage_course(command.course_id)

        course.update(title=command.title, description=command.description)
        await self.uow.courses.update(course)
        await self.uow.commit()
        return course
