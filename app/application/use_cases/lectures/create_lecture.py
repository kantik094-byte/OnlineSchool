from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.exceptions import SectionNotFoundError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities import Question
from app.domain.entities.lecture import Lecture
from app.domain.ordering import make_room, check_insert_position


@dataclass(slots=True)
class CreateLectureCommand:
    section_id: UUID
    title: str
    content: str
    position: int


class CreateLectureUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: CreateLectureCommand) -> Lecture:
        await self.access.ensure_can_manage_section(command.section_id)

        section = await self.uow.sections.get_for_update(command.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        # Необходимо обновить позиции не только лекций, но и вопросов
        sibling_lectures = await self.uow.lectures.get_by_ids(section.lecture_ids)
        sibling_questions = await self.uow.questions.get_by_ids(section.question_ids)
        siblings = sibling_lectures + sibling_questions

        check_insert_position(siblings, command.position)
        siblings_positions_updated = make_room(siblings, command.position)

        # Отделяем лекции и обновляем только лекции
        lecture_position_updated = [lecture for lecture in siblings_positions_updated if isinstance(lecture, Lecture)]
        await self.uow.lectures.update_many(lecture_position_updated)

        # Отделяем вопросы и обновляем только вопросы
        question_position_updated = [question for question in siblings_positions_updated if isinstance(question, Question)]
        await self.uow.questions.update_many(question_position_updated)

        lecture = Lecture(
            id=uuid4(),
            section_id=command.section_id,
            title=command.title,
            content=command.content,
            position=command.position,
        )

        section.add_lecture(lecture.id)
        await self.uow.lectures.add(lecture)
        await self.uow.sections.update(section)
        await self.uow.commit()
        return lecture
