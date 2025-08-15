import asyncio
from fastapi import FastAPI
from src.api.endpoints import router
from src.db.database import engine
from src.db.models import User
from sqladmin import Admin, ModelView

from src.services.event_consumers import setup_user_consumers


app = FastAPI(title="User Service", version="1.0.0")
app.include_router(router, prefix="/api")
admin = Admin(app, engine)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(setup_user_consumers())


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.email, User.name, User.hashed_password, User.role, User.status,
        User.team_id, User.invite_code, User.phone, User.position, User.department,
        User.created_at, User.updated_at
    ]


admin.add_view(UserAdmin)
