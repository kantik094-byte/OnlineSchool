from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import CourseNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork


@dataclass(slots=True)
class CourseDeleteCommand:
    course_id: UUID


class DeleteCourseUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider):
        self.uow = uow
        self.idp = idp

    async def execute(self, command: CourseDeleteCommand) -> None:
        await require_content_manager(self.idp)

        course = await self.uow.courses.get_by_id(command.course_id)
        if course is None:
            raise CourseNotFoundError("Course not found.")

        await self.uow.courses.remove(course)
        await self.uow.commit()