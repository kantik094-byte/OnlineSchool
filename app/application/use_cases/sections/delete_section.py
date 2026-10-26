from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import SectionNotFoundError, CourseModuleNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.ordering import close_gap


@dataclass(slots=True)
class DeleteSectionCommand:
    section_id: UUID


class DeleteSectionUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: DeleteSectionCommand) -> None:
        await require_content_manager(self.idp)

        section = await self.uow.sections.get_by_id(command.section_id)
        if section is None:
            raise SectionNotFoundError("Section not found.")

        module = await self.uow.modules.get_for_update(section.module_id)
        if module is None:
            raise CourseModuleNotFoundError("Module not found.")

        siblings = await self.uow.sections.get_by_ids(module.section_ids)
        section = next((item for item in siblings if item.id == command.section_id), None)
        if section is None:
            raise SectionNotFoundError("Section not found.")

        module.remove_section(command.section_id)
        await self.uow.sections.remove(section)
        await self.uow.modules.update(module)
        await self.uow.sections.update_many(close_gap(siblings, section.position))

        await self.uow.commit()


