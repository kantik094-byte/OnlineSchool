from uuid import uuid4

import pytest

from app.domain.entities.section import Section
from app.domain.exceptions import InvalidSectionError


def test_section_is_created_with_valid_data() -> None:
    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title='Section 1',
        description='Description',
        position=1,
    )

    assert section.title == 'Section 1'
    assert section.description == 'Description'
    assert section.lecture_ids == []


def test_add_lecture_to_section() -> None:
    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title='Section 1',
        description='Description',
        position=1,
    )

    lecture_id = uuid4()
    section.add_lecture(lecture_id=lecture_id)

    assert len(section.lecture_ids) == 1
    assert lecture_id in section.lecture_ids



def test_remove_lecture_from_section() -> None:
    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title='Section 1',
        description='Description',
        position=1,
    )

    lecture_id = uuid4()
    section.add_lecture(lecture_id=lecture_id)

    section.remove_lecture(lecture_id)

    assert len(section.lecture_ids) == 0



def test_remove_lecture_raises_error_when_lecture_id_is_not_exist() -> None:
    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title='Section 1',
        description='Description',
        position=1,
    )

    lecture_id = uuid4()
    section.add_lecture(lecture_id=lecture_id)

    deleting_id = uuid4()
    with pytest.raises(InvalidSectionError):
        section.remove_lecture(deleting_id)

    assert len(section.lecture_ids) == 1
    assert lecture_id in section.lecture_ids



def test_section_raises_error_when_title_is_blank() -> None:
    with pytest.raises(InvalidSectionError):
        Section(
            id=uuid4(),
            module_id=uuid4(),
            title='   ',
            description='Description',
            position=1,
        )


def test_section_raises_error_when_position_is_not_positive() -> None:
    with pytest.raises(InvalidSectionError):
        Section(
            id=uuid4(),
            module_id=uuid4(),
            title='Section 1',
            description='Description',
            position=0,
        )
