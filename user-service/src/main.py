from fastapi import FastAPI
from src.api.endpoints import router as api_router
from sqladmin import Admin, ModelView
from src.db.database import engine
from src.db.models import User

app = FastAPI(title="Auth Service")
app.include_router(api_router, prefix="/api")
admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.name, User.hashed_password, User.role, User.status, User.team_id,
                   User.created_at]


admin.add_view(UserAdmin)
