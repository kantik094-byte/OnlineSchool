from dataclasses import dataclass
from uuid import uuid4

from app.application.authorization import require_content_manager
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.course import Course


@dataclass(slots=True)
class CreateCourseCommand:
    title: str
    description: str


class CreateCourseUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: CreateCourseCommand) -> Course:
        await require_content_manager(self.idp)

        async with self.uow:
            course = Course(
                id=uuid4(),
                title=command.title,
                description=command.description,
            )
            await self.uow.courses.add(course)
            await self.uow.commit()
            return course