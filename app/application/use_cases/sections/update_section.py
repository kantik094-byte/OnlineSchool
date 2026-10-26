from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import SectionNotFoundError, CourseModuleNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.section import Section
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateSectionCommand:
    section_id: UUID
    title: str
    description: str
    position: int


class UpdateSectionUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: UpdateSectionCommand) -> Section:
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

        siblings = [item for item in siblings if item.id != section.id]
        check_insert_position(siblings, command.position)
        old_position = section.position

        section.update(
            title=command.title,
            description=command.description,
            position=command.position,
        )

        await self.uow.sections.update_many(move_position(siblings, old_position, command.position))
        await self.uow.sections.update(section)
        await self.uow.commit()

        return section
