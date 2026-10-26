from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, status

from app.application.use_cases.courses.create_course import (
    CreateCourseCommand,
    CreateCourseUseCase,
)
from app.application.use_cases.courses.delete_course import DeleteCourseUseCase, CourseDeleteCommand
from app.application.use_cases.courses.update_course import (
    UpdateCourseCommand,
    UpdateCourseUseCase,
)
from app.application.use_cases.lectures.create_lecture import (
    CreateLectureCommand,
    CreateLectureUseCase,
)
from app.application.use_cases.lectures.delete_lecture import DeleteLectureUseCase, DeleteLectureCommand
from app.application.use_cases.lectures.update_lecture import (
    UpdateLectureCommand,
    UpdateLectureUseCase,
)
from app.application.use_cases.modules.create_module import (
    CreateModuleCommand,
    CreateModuleUseCase,
)
from app.application.use_cases.modules.delete_module import DeleteModuleUseCase, DeleteModuleCommand
from app.application.use_cases.modules.update_module import (
    UpdateModuleCommand,
    UpdateModuleUseCase,
)
from app.application.use_cases.sections.create_sections import CreateSectionUseCase, CreateSectionCommand
from app.application.use_cases.sections.delete_section import DeleteSectionUseCase, DeleteSectionCommand
from app.application.use_cases.sections.update_section import (
    UpdateSectionCommand,
    UpdateSectionUseCase,
)
from app.presentation.api.schemas import (
    CourseResponse,
    CreateCourseRequest,
    CreateLectureRequest,
    CreateModuleRequest,
    CreateSectionRequest,
    LectureResponse,
    ModuleResponse,
    SectionResponse,
    UpdateCourseRequest,
    UpdateLectureRequest,
    UpdateModuleRequest,
    UpdateSectionRequest,
    ErrorResponse,
)
from app.presentation.api.security import ADMIN_RESPONSES, AUTH_REQUIRED

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    route_class=DishkaRoute,
    dependencies=AUTH_REQUIRED,
    responses=ADMIN_RESPONSES,
)




@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED,
             summary="Create course",
             description=(
                     "Creates a new course in the administrative API. "
                     "The course is the root entity of the content tree."
             ),
             responses={
                 400: {
                     "description": "Domain or application validation error.",
                     "model": ErrorResponse,
                 },
             },
)
async def create_course(request: CreateCourseRequest, use_case: FromDishka[CreateCourseUseCase]) -> CourseResponse:
    result = await use_case.execute(
        CreateCourseCommand(
            title=request.title,
            description=request.description
        )
    )
    return CourseResponse.model_validate(result)



@router.put("/courses/{course_id}", response_model=CourseResponse,
            summary="Update course",
            description=(
                    "Updates an existing course by its identifier. "
                    "Allows changing the course title and description."
            ),
            responses={
                400: {
                    "description": "Domain or application validation error.",
                    "model": ErrorResponse,
                },
                404: {
                    "description": "Course was not found.",
                    "model": ErrorResponse,
                },
            },
)
async def update_course(course_id: UUID, request: UpdateCourseRequest, use_case: FromDishka[UpdateCourseUseCase]) -> CourseResponse:
    result = await use_case.execute(
        UpdateCourseCommand(
            course_id=course_id,
            title=request.title,
            description=request.description,
        )
    )
    return CourseResponse.model_validate(result)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete course",
               description="Deletes a course by its identifier.",
               responses={
                   404: {
                       "description": "Course was not found.",
                       "model": ErrorResponse,
                   }
               }
)
async def  delete_course(course_id: UUID, use_case: FromDishka[DeleteCourseUseCase]) -> None:
    await use_case.execute(CourseDeleteCommand(course_id=course_id))



@router.post("/courses/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED,
             summary="Create module",
             description=(
                     "Creates a new module inside an existing course. "
                     "Modules are used to group sections within a course."
             ),
             responses={
                 400: {
                     "description": "Domain or application validation error.",
                     "model": ErrorResponse,
                 },
                 404: {
                     "description": "Course was not found.",
                     "model": ErrorResponse,
                 },
             },
)
async def create_module(course_id: UUID, request: CreateModuleRequest, use_case: FromDishka[CreateModuleUseCase]) -> ModuleResponse:
    result = await use_case.execute(
        CreateModuleCommand(
            course_id=course_id,
            title=request.title,
            description=request.description,
            position=request.position,
        )
    )
    return ModuleResponse.model_validate(result)



@router.put("/modules/{module_id}", response_model=ModuleResponse,
            summary="Update module",
            description=(
                    "Updates an existing module by its identifier. "
                    "Allows changing the module title, description and position."
            ),
            responses={
                400: {
                    "description": "Domain or application validation error.",
                    "model": ErrorResponse,
                },
                404: {
                    "description": "Module was not found.",
                    "model": ErrorResponse,
                },
            },
)
async def update_module(module_id: UUID, request: UpdateModuleRequest, use_case: FromDishka[UpdateModuleUseCase]) -> ModuleResponse:
    result = await use_case.execute(
        UpdateModuleCommand(
            module_id=module_id,
            title=request.title,
            description=request.description,
            position=request.position,
        )
    )
    return ModuleResponse.model_validate(result)



@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete module",
               description="Deletes a module by its identifier.",
               responses={
                   404: {
                       "description": "Module or Course was not found.",
                       "model": ErrorResponse,
                   }
               })
async def delete_module(module_id: UUID, use_case: FromDishka[DeleteModuleUseCase]) -> None:
    await use_case.execute(DeleteModuleCommand(module_id=module_id))



@router.post("/modules/{module_id}/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED,
             summary="Create section",
             description=(
                     "Creates a new section inside an existing module. "
                     "Sections are used to group lectures within a module."
             ),
             responses={
                 400: {
                     "description": "Domain or application validation error.",
                     "model": ErrorResponse,
                 },
                 404: {
                     "description": "Module was not found.",
                     "model": ErrorResponse,
                 },
             },
)
async def create_section(module_id: UUID, request: CreateSectionRequest, use_case: FromDishka[CreateSectionUseCase]) -> SectionResponse:
    result = await use_case.execute(
        CreateSectionCommand(
            module_id=module_id,
            title=request.title,
            description=request.description,
            position=request.position,
        )
    )
    return SectionResponse.model_validate(result)



@router.put("/sections/{section_id}", response_model=SectionResponse,
            summary="Update section",
            description=(
                    "Updates an existing section by its identifier. "
                    "Allows changing the section title, description and position."
            ),
            responses={
                400: {
                    "description": "Domain or application validation error.",
                    "model": ErrorResponse,
                },
                404: {
                    "description": "Section was not found.",
                    "model": ErrorResponse,
                },
            },
)
async def update_section(section_id: UUID, request: UpdateSectionRequest, use_case: FromDishka[UpdateSectionUseCase]) -> SectionResponse:
    result = await use_case.execute(
        UpdateSectionCommand(
            section_id=section_id,
            title=request.title,
            description=request.description,
            position=request.position,
        )
    )
    return SectionResponse.model_validate(result)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete section",
               description="Deletes a section by its identifier.",
               responses={
                   404: {
                       "description": "Section or Module was not found.",
                       "model": ErrorResponse
                   }
               }
)
async def delete_section(section_id: UUID, use_case: FromDishka[DeleteSectionUseCase]) -> None:
    await use_case.execute(DeleteSectionCommand(section_id=section_id))


@router.post("/sections/{section_id}/lectures", response_model=LectureResponse, status_code=status.HTTP_201_CREATED,
             summary="Create lecture",
             description=(
                     "Creates a new lecture inside an existing section. "
                     "A lecture is the final content item in the course tree."
             ),
             responses={
                 400: {
                     "description": "Domain or application validation error.",
                     "model": ErrorResponse,
                 },
                 404: {
                     "description": "Section was not found.",
                     "model": ErrorResponse,
                 },
             },
)
async def create_lecture(section_id: UUID, request: CreateLectureRequest, use_case: FromDishka[CreateLectureUseCase]) -> LectureResponse:
    result = await use_case.execute(
        CreateLectureCommand(
            section_id=section_id,
            title=request.title,
            content=request.content,
            position=request.position,
        )
    )
    return LectureResponse.model_validate(result)


@router.put("/lectures/{lecture_id}", response_model=LectureResponse,
            summary="Update lecture",
            description=(
                    "Updates an existing lecture by its identifier. "
                    "Allows changing the lecture title, content and position."
            ),
            responses={
                400: {
                    "description": "Domain or application validation error.",
                    "model": ErrorResponse,
                },
                404: {
                    "description": "Lecture was not found.",
                    "model": ErrorResponse,
                },
            },
)
async def update_lecture(lecture_id: UUID, request: UpdateLectureRequest, use_case: FromDishka[UpdateLectureUseCase]) -> LectureResponse:
    result = await use_case.execute(
        UpdateLectureCommand(
            lecture_id=lecture_id,
            title=request.title,
            content=request.content,
            position=request.position,
        )
    )
    return LectureResponse.model_validate(result)



@router.delete("/lectures/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete lecture",
               description="Deletes a lecture by its identifier.",
               responses={
                   404: {
                       "description": "Lecture or Section was not found.",
                       "model": ErrorResponse
                   }
               }
)
async def delete_lecture(lecture_id: UUID, use_case: FromDishka[DeleteLectureUseCase]) -> None:
    await use_case.execute(DeleteLectureCommand(lecture_id=lecture_id))


