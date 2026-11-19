from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import LectureNotFoundError, SectionNotFoundError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities import Question
from app.domain.entities.lecture import Lecture
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateLectureCommand:
    lecture_id: UUID
    title: str
    content: str
    position: int


class UpdateLectureUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: UpdateLectureCommand) -> Lecture:
        lecture = await self.access.ensure_can_manage_lecture(command.lecture_id)

        # Блокируем родителя
        section = await self.uow.sections.get_for_update(lecture.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        # При обновлении лекции (если обновляется позиция), необходимо закрыть гэп на старом месте и открыть окно на новом
        # Обновлять позиции нужно как у лекций, так и у вопросов
        sibling_lectures = await self.uow.lectures.get_by_ids(section.lecture_ids)
        sibling_questions = await self.uow.questions.get_by_ids(section.question_ids)

        lecture = next((item for item in sibling_lectures if item.id == command.lecture_id), None)
        if lecture is None:
            raise LectureNotFoundError('Lecture not found.')

        siblings = sibling_lectures + sibling_questions

        siblings_without_update_item = [item for item in siblings if item.id != lecture.id]
        check_insert_position(siblings_without_update_item, command.position)
        old_position = lecture.position

        siblings_positions_updated = move_position(siblings_without_update_item, old_position, command.position)

        lecture_position_updated = [lecture for lecture in siblings_positions_updated if isinstance(lecture, Lecture)]
        question_position_updated = [question for question in siblings_positions_updated if isinstance(question, Question)]

        lecture.update(
            title=command.title,
            content=command.content,
            position=command.position,
        )

        await self.uow.lectures.update_many(lecture_position_updated)
        await self.uow.questions.update_many(question_position_updated)
        await self.uow.lectures.update(lecture)
        await self.uow.commit()

        return lecture
