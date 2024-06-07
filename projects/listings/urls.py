from django.urls import path
from taiga.projects.listings.views import ProjectListView, ProjectListMembers, ProjectDetailView, AddProjectMember, UsersList, AssignUserToProjects

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list_view"),
    path("projects/<int:project_id>/", ProjectDetailView.as_view(), name="project_detail_view"),
    path("projects/<int:project_id>/add-members/", AddProjectMember.as_view(), name="add_project_members"),
    path("projects/members/", ProjectListMembers.as_view(), name="project_members_view"),
    path("users/", UsersList.as_view(), name="users_list"),
    path("assign-user-to-projects/", AssignUserToProjects.as_view(), name="assign_user_to_projects"),
]
