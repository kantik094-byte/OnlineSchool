from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import (
    QuestionAlreadyUsedError,
    QuestionNotFoundError, SectionNotFoundError,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities import Lecture
from app.domain.entities.question import Question, QuestionType
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateQuestionCommand:
    question_id: UUID
    text: str
    position: int
    question_type: QuestionType
    max_attempts: int
    reward_points: int


class UpdateQuestionUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: UpdateQuestionCommand) -> Question:
        question = await self.access.ensure_can_manage_question(command.question_id)

        # Блокируем родителя
        section = await self.uow.sections.get_for_update(question.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        has_attempts = await self.uow.question_attempts.exists_by_question_id(question.id)
        if has_attempts:
            raise QuestionAlreadyUsedError('Question already has student attempts and cannot be changed safely.')


        # При обновлении вопроса (если обновляется позиция), необходимо закрыть гэп на старом месте и открыть окно на новом
        # Обновлять позиции нужно как у лекций, так и у вопросов
        sibling_lectures = await self.uow.lectures.get_by_ids(section.lecture_ids)
        sibling_questions = await self.uow.questions.get_by_ids(section.question_ids)

        question = next((item for item in sibling_questions if item.id == command.question_id), None)
        if question is None:
            raise QuestionNotFoundError('Question not found.')

        siblings = sibling_lectures + sibling_questions

        siblings_without_update_item = [item for item in siblings if item.id != question.id]
        check_insert_position(siblings_without_update_item, command.position)
        old_position = question.position

        siblings_positions_updated = move_position(siblings_without_update_item, old_position, command.position)

        lecture_position_updated = [lecture for lecture in siblings_positions_updated if isinstance(lecture, Lecture)]
        question_position_updated = [question for question in siblings_positions_updated if isinstance(question, Question)]

        question.update(
            text=command.text,
            position=command.position,
            question_type=command.question_type,
            max_attempts=command.max_attempts,
            reward_points=command.reward_points,
        )

        await self.uow.lectures.update_many(lecture_position_updated)
        await self.uow.questions.update_many(question_position_updated)
        await self.uow.questions.update(question)
        await self.uow.commit()
        return question