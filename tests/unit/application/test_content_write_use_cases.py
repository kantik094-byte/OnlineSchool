from uuid import uuid4

import pytest

from app.application.exceptions import CourseNotFoundError, ModuleNotFoundError, SectionNotFoundError, LectureNotFoundError, \
    AccessDeniedError, AuthenticationError
from app.application.use_cases.courses.create_course import CreateCourseUseCase, CreateCourseCommand
from app.application.use_cases.courses.update_course import UpdateCourseUseCase, UpdateCourseCommand
from app.application.use_cases.lectures.create_lecture import CreateLectureUseCase, CreateLectureCommand
from app.application.use_cases.lectures.update_lecture import UpdateLectureUseCase, UpdateLectureCommand
from app.application.use_cases.modules.create_module import CreateModuleUseCase, CreateModuleCommand
from app.application.use_cases.modules.update_module import UpdateModuleUseCase, UpdateModuleCommand
from app.application.use_cases.sections.create_sections import CreateSectionUseCase, CreateSectionCommand
from app.application.use_cases.sections.update_section import UpdateSectionUseCase, UpdateSectionCommand
from app.domain.entities import Course
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section
from tests.fakes import FakeIdentityProvider
from tests.conftest import admin, student


@pytest.mark.asyncio
async def test_create_course_adds_course_and_commits_by_admin(uow, admin) -> None:

    use_case = CreateCourseUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    result = await use_case.execute(
        CreateCourseCommand(
            title="FastAPI course",
            description="Clean architecture in practice.",
        )
    )

    assert result.id in uow.courses.items
    assert result.title == "FastAPI course"
    assert result.description == "Clean architecture in practice."
    assert uow.committed is True




@pytest.mark.asyncio
async def test_negative_create_course_by_student(uow, student) -> None:

    use_case = CreateCourseUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateCourseCommand(
                title="FastAPI course",
                description="Clean architecture in practice.",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_course_by_anon(uow) -> None:

    use_case = CreateCourseUseCase(uow=uow, idp=FakeIdentityProvider(None))

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateCourseCommand(
                title="FastAPI course",
                description="Clean architecture in practice.",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_update_course_changes_existing_course_by_admin(uow, admin) -> None:

    course = Course(id=uuid4(), title="Old", description="Old description")
    await uow.courses.add(course)

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        UpdateCourseCommand(
            course_id=course.id,
            title="New",
            description="New description",
        )
    )

    assert result.title == "New"
    assert result.description == "New description"
    assert uow.committed is True


@pytest.mark.asyncio
async def test_negative_update_course_changes_existing_course_by_student(uow, student) -> None:

    course = Course(id=uuid4(), title="Old", description="Old description")
    await uow.courses.add(course)

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=course.id,
                title="New",
                description="New description",
            )
        )

    course_in_storage = await uow.courses.get_by_id(course.id)

    assert course_in_storage.title == course.title
    assert course_in_storage.description == course.description


@pytest.mark.asyncio
async def test_negative_update_course_changes_existing_course_by_anon(uow) -> None:

    course = Course(id=uuid4(), title="Old", description="Old description")
    await uow.courses.add(course)

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=course.id,
                title="New",
                description="New description",
            )
        )

    course_in_storage = await uow.courses.get_by_id(course.id)

    assert course_in_storage.title == course.title
    assert course_in_storage.description == course.description


@pytest.mark.asyncio
async def test_update_course_raises_not_found_when_course_is_missing(uow, admin) -> None:

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(CourseNotFoundError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=uuid4(),
                title="New",
                description="New description",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_update_course_when_course_is_missing_by_student(uow, student) -> None:

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=uuid4(),
                title="New",
                description="New description",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_update_course_when_course_is_missing_by_anon(uow) -> None:

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=uuid4(),
                title="New",
                description="New description",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_module_adds_module_to_course_and_commits(uow, admin) -> None:

    course = Course(id=uuid4(), title="Course", description="Description")
    await uow.courses.add(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        CreateModuleCommand(
            course_id=course.id,
            title="Module 1",
            description="Module description",
            position=1,
        )
    )

    assert result.id in uow.modules.items
    assert result.id in course.module_ids
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_create_module_by_student(uow, student) -> None:
    course = Course(id=uuid4(), title="Course", description="Description")
    await uow.courses.add(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=course.id,
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_module_by_anon(uow) -> None:
    course = Course(id=uuid4(), title="Course", description="Description")
    await uow.courses.add(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=course.id,
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_module_raises_not_found_when_course_is_missing(uow, admin) -> None:

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(CourseNotFoundError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=uuid4(),
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_module_when_course_is_missing_by_student(uow, student) -> None:

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=uuid4(),
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_module_when_course_is_missing_by_anon(uow) -> None:

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=uuid4(),
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False


@pytest.mark.asyncio
async def test_update_module_changes_existing_module(uow, admin) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Old module",
        description="Old description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        UpdateModuleCommand(
            module_id=module.id,
            title="New module",
            description="New description",
            position=2,
        )
    )

    assert result.title == "New module"
    assert result.description == "New description"
    assert result.position == 2
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_update_module_changes_existing_module_by_student(uow, student) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Old module",
        description="Old description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateModuleCommand(
                module_id=module.id,
                title="New module",
                description="New description",
                position=2,
            )
        )

    module_in_storage = await uow.modules.get_by_id(module.id)

    assert module_in_storage.title == module.title
    assert module_in_storage.description == module.description
    assert module_in_storage.position == module.position




@pytest.mark.asyncio
async def test_negative_update_module_changes_existing_module_by_anon(uow) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Old module",
        description="Old description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateModuleCommand(
                module_id=module.id,
                title="New module",
                description="New description",
                position=2,
            )
        )

    module_in_storage = await uow.modules.get_by_id(module.id)

    assert module_in_storage.title == module.title
    assert module_in_storage.description == module.description
    assert module_in_storage.position == module.position



@pytest.mark.asyncio
async def test_update_module_raises_not_found_when_module_is_missing(uow, admin) -> None:

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(ModuleNotFoundError):
        await use_case.execute(
            UpdateModuleCommand(
                module_id=uuid4(),
                title="New module",
                description="New description",
                position=2,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False


@pytest.mark.asyncio
async def test_create_section_adds_section_to_module_and_commits(uow, admin) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Module",
        description="Description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        CreateSectionCommand(
            module_id=module.id,
            title="Section 1",
            description="Section description",
            position=1,
        )
    )

    assert result.id in uow.sections.items
    assert result.id in module.section_ids
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_create_section_by_student(uow, student) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Module",
        description="Description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=module.id,
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False




@pytest.mark.asyncio
async def test_negative_create_section_by_anon(uow) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Module",
        description="Description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=module.id,
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_section_raises_not_found_when_module_is_missing(uow, admin) -> None:

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(ModuleNotFoundError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=uuid4(),
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_section_when_module_is_missing_by_student(uow, student) -> None:

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=uuid4(),
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_section_when_module_is_missing_by_anon(uow) -> None:

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=uuid4(),
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_update_section_changes_existing_section(uow, admin) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Old section",
        description="Old description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        UpdateSectionCommand(
            section_id=section.id,
            title="New section",
            description="New description",
            position=2,
        )
    )

    assert result.title == "New section"
    assert result.description == "New description"
    assert result.position == 2
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_update_section_changes_existing_section_by_student(uow, student) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Old section",
        description="Old description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=section.id,
                title="New section",
                description="New description",
                position=2,
            )
        )

    section_in_storage = await uow.sections.get_by_id(section.id)

    assert section_in_storage.title == section.title
    assert section_in_storage.description == section.description
    assert section_in_storage.position == section.position




@pytest.mark.asyncio
async def test_negative_update_section_changes_existing_section_by_anon(uow) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Old section",
        description="Old description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=section.id,
                title="New section",
                description="New description",
                position=2,
            )
        )

    section_in_storage = await uow.sections.get_by_id(section.id)

    assert section_in_storage.title == section.title
    assert section_in_storage.description == section.description
    assert section_in_storage.position == section.position



@pytest.mark.asyncio
async def test_update_section_raises_not_found_when_section_is_missing(uow, admin) -> None:

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(SectionNotFoundError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=uuid4(),
                title="New section",
                description="New description",
                position=2,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_update_section_when_section_is_missing_by_student(uow, student) -> None:

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=uuid4(),
                title="New section",
                description="New description",
                position=2,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_update_section_when_section_is_missing_by_anon(uow) -> None:

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=uuid4(),
                title="New section",
                description="New description",
                position=2,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_lecture_adds_lecture_to_section_and_commits(uow, admin) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Section",
        description="Description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        CreateLectureCommand(
            section_id=section.id,
            title="Lecture 1",
            content="Lecture content",
            position=1,
        )
    )

    assert result.id in uow.lectures.items
    assert result.id in section.lecture_ids
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_create_lecture_by_student(uow, student) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Section",
        description="Description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=section.id,
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_lecture_by_anon(uow) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Section",
        description="Description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=section.id,
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_lecture_raises_not_found_when_section_is_missing(uow, admin) -> None:

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(SectionNotFoundError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=uuid4(),
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_create_lecture_when_section_is_missing_by_student(uow, student) -> None:

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=uuid4(),
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_create_lecture_when_section_is_missing_by_anon(uow) -> None:

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=uuid4(),
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_update_lecture_changes_existing_lecture(uow, admin) -> None:

    lecture = Lecture(
        id=uuid4(),
        section_id=uuid4(),
        title="Old lecture",
        content="Old content",
        position=1,
    )
    await uow.lectures.add(lecture)

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(admin))
    result = await use_case.execute(
        UpdateLectureCommand(
            lecture_id=lecture.id,
            title="New lecture",
            content="New content",
            position=2,
        )
    )

    assert result.title == "New lecture"
    assert result.content == "New content"
    assert result.position == 2
    assert uow.committed is True



@pytest.mark.asyncio
async def test_negative_update_lecture_changes_existing_lecture_by_student(uow, student) -> None:

    lecture = Lecture(
        id=uuid4(),
        section_id=uuid4(),
        title="Old lecture",
        content="Old content",
        position=1,
    )
    await uow.lectures.add(lecture)

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=lecture.id,
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    lecture_in_storage = await uow.lectures.get_by_id(lecture.id)

    assert lecture_in_storage.title == lecture.title
    assert lecture_in_storage.content == lecture.content
    assert lecture_in_storage.position == lecture.position



@pytest.mark.asyncio
async def test_negative_update_lecture_changes_existing_lecture_by_anon(uow) -> None:

    lecture = Lecture(
        id=uuid4(),
        section_id=uuid4(),
        title="Old lecture",
        content="Old content",
        position=1,
    )
    await uow.lectures.add(lecture)

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=lecture.id,
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    lecture_in_storage = await uow.lectures.get_by_id(lecture.id)

    assert lecture_in_storage.title == lecture.title
    assert lecture_in_storage.content == lecture.content
    assert lecture_in_storage.position == lecture.position


@pytest.mark.asyncio
async def test_update_lecture_raises_not_found_when_lecture_is_missing(uow, admin) -> None:

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(admin))

    with pytest.raises(LectureNotFoundError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=uuid4(),
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False


@pytest.mark.asyncio
async def test_negative_update_lecture_when_lecture_is_missing_by_student(uow, student) -> None:

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(student))

    with pytest.raises(AccessDeniedError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=uuid4(),
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.asyncio
async def test_negative_update_lecture_when_lecture_is_missing_by_anon(uow) -> None:

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider())

    with pytest.raises(AuthenticationError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=uuid4(),
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False