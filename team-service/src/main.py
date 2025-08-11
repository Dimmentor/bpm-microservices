from fastapi import FastAPI
from src.api.endpoints import router as api_router
from src.db.database import engine
from src.db.models import Team, OrgUnit, OrgMember, TeamNews
from sqladmin import Admin, ModelView

app = FastAPI(title="team-service")
app.include_router(api_router, prefix="/api")
admin = Admin(app, engine)


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.name, Team.description, Team.owner_id, Team.invite_code, Team.is_active,
                   Team.created_at, Team.updated_at]


class OrgUnitAdmin(ModelView, model=OrgUnit):
    column_list = [OrgUnit.id, OrgUnit.team_id, OrgUnit.name, OrgUnit.parent_id, OrgUnit.description,
                   OrgUnit.created_at]


class OrgMemberAdmin(ModelView, model=OrgMember):
    column_list = [OrgMember.id, OrgMember.user_id, OrgMember.org_unit_id, OrgMember.position, OrgMember.manager_id]


class TeamNewsAdmin(ModelView, model=TeamNews):
    column_list = [TeamNews.id, TeamNews.team_id, TeamNews.author_id, TeamNews.title, TeamNews.content,
                   TeamNews.is_published,
                   TeamNews.created_at, TeamNews.updated_at]


admin.add_view(TeamAdmin)
admin.add_view(OrgUnitAdmin)
admin.add_view(OrgMemberAdmin)
admin.add_view(TeamNewsAdmin)
