from uuid import uuid4

import pytest

from app.application.use_cases.courses.get_course import GetCourseUseCase, GetCourseQuery
from app.application.use_cases.courses.get_course_structure import GetCourseStructureUseCase, GetCourseStructureQuery
from app.application.use_cases.courses.get_courses import GetCoursesUseCase, GetCoursesQuery
from app.application.use_cases.lectures.get_lecture import GetLectureUseCase, GetLectureQuery
from app.domain.entities import Course
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section


@pytest.mark.asyncio
async def test_get_course_by_id(uow):
    course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    await uow.courses.add(course)

    use_case = GetCourseUseCase(uow.courses)

    result = await use_case.execute(
        GetCourseQuery(course_id=course.id)
    )

    assert result == course


@pytest.mark.asyncio
async def test_get_courses(uow):
    first_course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    await uow.courses.add(first_course)

    second_course = Course(id=uuid4(), title="SQLAlchemy course", description="ORM in practice.")
    await uow.courses.add(second_course)

    use_case = GetCoursesUseCase(uow.courses)
    result = await use_case.execute(GetCoursesQuery())

    assert result == [first_course, second_course]



@pytest.mark.asyncio
async def test_get_course_structure(uow):
    course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    module = Module(id=uuid4(), course_id=course.id, title="Module 1", description="Module description", position=1)
    section = Section(id=uuid4(), module_id=module.id, title="Section 1", description="Section description", position=1)
    lecture = Lecture(id=uuid4(), section_id=section.id, title="Lecture 1", content="First lecture", position=1)

    course.module_ids.append(module.id)
    module.section_ids.append(section.id)
    section.lecture_ids.append(lecture.id)

    await uow.courses.add(course)
    await uow.modules.add(module)
    await uow.sections.add(section)
    await uow.lectures.add(lecture)

    use_case = GetCourseStructureUseCase(
        uow.courses,
        uow.modules,
        uow.sections,
        uow.lectures,
    )

    result = await use_case.execute(GetCourseStructureQuery(course_id=course.id))

    assert result.id == course.id
    assert result.title == course.title
    assert result.description == course.description

    for module_id, module_result in zip(course.module_ids, result.modules):
        assert module_id == module_result.id
        assert module.title == module_result.title
        assert module.description == module_result.description
        assert module.position == module_result.position

        for section_id, section_result in zip(module.section_ids, module_result.sections):
            assert section_id == section_result.id
            assert section.title == section_result.title
            assert section.description == section_result.description
            assert section.position == section_result.position

            for lecture_id, lecture_result in zip(section.lecture_ids, section_result.lectures):
                assert lecture_id == lecture_result.id
                assert lecture.title == lecture_result.title
                assert lecture.position == lecture_result.position



@pytest.mark.asyncio
async def test_get_lecture(uow):
    lecture = Lecture(id=uuid4(), section_id=uuid4(), title="Lecture 1", content="First lecture", position=1)
    await uow.lectures.add(lecture)

    use_case = GetLectureUseCase(uow.lectures)

    result = await use_case.execute(GetLectureQuery(lecture_id=lecture.id))

    assert lecture == result







