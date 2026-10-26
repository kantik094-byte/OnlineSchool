from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import CourseNotFoundError, CourseModuleNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.ordering import close_gap


@dataclass(slots=True)
class DeleteModuleCommand:
    module_id: UUID



class DeleteModuleUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: DeleteModuleCommand) -> None:
        await require_content_manager(self.idp)

        module = await self.uow.modules.get_by_id(command.module_id)
        if module is None:
            raise CourseModuleNotFoundError("Module not found.")

        course = await self.uow.courses.get_for_update(module.course_id)
        if course is None:
            raise CourseNotFoundError("Course not found.")

        siblings = await self.uow.modules.get_by_ids(course.module_ids)
        module = next((item for item in siblings if item.id == command.module_id), None)
        if module is None:
            raise CourseModuleNotFoundError("Module not found.")

        course.remove_module(command.module_id)
        await self.uow.modules.remove(module)
        await self.uow.courses.update(course)
        await self.uow.modules.update_many(close_gap(siblings, module.position))

        await self.uow.commit()
