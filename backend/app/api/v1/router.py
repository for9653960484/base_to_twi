from fastapi import APIRouter

from app.modules.equipment.router import router as equipment_router
from app.modules.documents.router import router as documents_router
from app.modules.tech_cards.router import router as tech_cards_router
from app.modules.maintenance_calendar.router import router as calendar_router
from app.modules.instructions.router import router as instructions_router
from app.modules.twi_courses.router import router as courses_router
from app.modules.competencies.router import router as competencies_router
from app.modules.users.router import router as users_router
from app.modules.hr.router import router as hr_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.brandbook.router import router as brandbook_router
from app.modules.ai_processing.router import router as ai_router

api_router = APIRouter()

api_router.include_router(equipment_router, prefix="/equipment", tags=["Equipment"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(tech_cards_router, prefix="/tech-cards", tags=["Tech Cards"])
api_router.include_router(calendar_router, prefix="/maintenance-calendar", tags=["Maintenance Calendar"])
api_router.include_router(instructions_router, prefix="/instructions", tags=["Instructions"])
api_router.include_router(courses_router, prefix="/courses", tags=["TWI Courses"])
api_router.include_router(competencies_router, prefix="/competencies", tags=["Competencies"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(hr_router, prefix="/hr", tags=["HR Integration"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge Q&A"])
api_router.include_router(brandbook_router, prefix="/brandbook", tags=["Brandbook"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Processing"])
