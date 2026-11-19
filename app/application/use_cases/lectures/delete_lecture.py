from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import LectureNotFoundError, SectionNotFoundError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities import Lecture, Question
from app.domain.ordering import close_gap


@dataclass(slots=True)
class DeleteLectureCommand:
    lecture_id: UUID



class DeleteLectureUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: DeleteLectureCommand) -> None:
        lecture = await self.access.ensure_can_manage_lecture(command.lecture_id)

        # Блокируем родителя
        section = await self.uow.sections.get_for_update(lecture.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        # При удалении лекции, необходимо обновить позиции не только лекций, но и вопросов
        sibling_lectures = await self.uow.lectures.get_by_ids(section.lecture_ids)
        sibling_questions = await self.uow.questions.get_by_ids(section.question_ids)

        lecture = next((item for item in sibling_lectures if item.id == command.lecture_id), None)
        if lecture is None:
            raise LectureNotFoundError('Lecture not found.')

        siblings = sibling_lectures + sibling_questions
        siblings_positions_updated = close_gap(siblings, lecture.position)

        lecture_position_updated = [lecture for lecture in siblings_positions_updated if isinstance(lecture, Lecture)]
        question_position_updated = [question for question in siblings_positions_updated if isinstance(question, Question)]

        section.remove_lecture(command.lecture_id)
        await self.uow.lectures.remove(lecture)
        await self.uow.sections.update(section)
        await self.uow.lectures.update_many(lecture_position_updated)
        await self.uow.questions.update_many(question_position_updated)

        await self.uow.commit()


