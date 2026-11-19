from dataclasses import dataclass
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService


@dataclass(slots=True)
class CourseDeleteCommand:
    course_id: UUID


class DeleteCourseUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: CourseDeleteCommand) -> None:
        course = await self.access.ensure_can_manage_course(command.course_id)

        await self.uow.courses.remove(course)
        await self.uow.commit()