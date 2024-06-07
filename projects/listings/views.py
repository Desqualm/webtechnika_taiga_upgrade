from django.shortcuts import render
from taiga.projects.models import Project, Membership
from taiga.projects.serializers import ProjectSerializer, MembershipSerializer
from taiga.projects import utils as project_utils
from taiga.users.models import User
from taiga.users.serializers import UserSerializer
from taiga.users import utils as user_utils
from taiga.base.api import generics
from taiga.base.api.views import APIView
from taiga.base.response import Response
from taiga.base import status
import json
from django.utils import timezone
from django.http import JsonResponse


class ProjectListView(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    sort_options = [
        ('name', 'Nazwa (rosnąco)'),
        ('-name', 'Nazwa (malejąco)'),
        ('total_fans', 'Liczba fanów (rosnąco)'),
        ('-total_fans', 'Liczba fanów (malejąco)'),
        ('created_date', 'Data utworzenia (Od najnowszych)'),
        ('-created_date', 'Data utworzenia (Od najstarszych)'),
        ('modified_date', 'Data modyfikacji (Od najnowszych)'),
        ('-modified_date', 'Data modyfikacji (Od najstarszych)'),
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get('sort_by')
        filter_by_tags = self.request.GET.getlist('filter_by_tag')

        if sort_by:
            queryset = queryset.order_by(sort_by)

        if filter_by_tags:
            for tag in filter_by_tags:
                queryset = queryset.filter(tags__contains=[tag])

        return queryset

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = project_utils.attach_extra_info(qs, user=self.request.user)
        projects_list = self.generate_projects_list(qs)
        unique_tags = Project.objects.values_list('tags', flat=True).distinct()
        unique_tags = list({tag for tags in unique_tags for tag in tags})

        context = {
            'projects_list': projects_list,
            'sort_options': self.sort_options,
            'unique_tags': unique_tags,
            'selected_sort': request.GET.get('sort_by', ''),
            'selected_filters': request.GET.getlist('filter_by_tag', []),
        }
        return render(request, 'project_list.html', context)

    def generate_projects_list(self, queryset):
        projects_list = []
        for project in queryset:
            projects_list.append({'name': project.name, 'id': project.id})
        return projects_list


class ProjectDetailView(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_url_kwarg = 'project_id'

    def retrieve(self, request, *args, **kwargs):
        project_id = self.kwargs.get('project_id')
        try:
            project = self.get_queryset().get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(project)
        data = serializer.data

        created_date = timezone.localtime(data['created_date']).strftime("%Y-%m-%d %H:%M:%S")
        modified_date = timezone.localtime(data['modified_date']).strftime("%Y-%m-%d %H:%M:%S")

        data['created_date'] = created_date
        data['modified_date'] = modified_date

        return Response(data)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = project_utils.attach_extra_info(qs, user=self.request.user)
        return qs


class ProjectListMembers(generics.ListAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = project_utils.attach_members(qs)
        return qs


class AddProjectMember(APIView):
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        user_ids = json.loads(request.body).get("user_ids")

        for user_id in user_ids:
            Membership.objects.create(project=project, user_id=user_id, role_id=48)

        return Response({"message": "Users added to project successfully"}, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = project_utils.attach_members(qs)
        return qs


class AssignUserToProjects(APIView):
    def post(self, request):
        data = json.loads(request.body)
        user_ids = data.get("user_ids")
        project_ids = data.get("project_ids")

        if not user_ids or not project_ids:
            return Response({"message": "User IDs and Project IDs are required"}, status=status.HTTP_400_BAD_REQUEST)

        for user_id in user_ids:
            for project_id in project_ids:
                try:
                    project = Project.objects.get(id=project_id)
                    Membership.objects.create(project=project, user_id=user_id, role_id=48)
                except Project.DoesNotExist:
                    continue

        return Response({"message": "Users assigned to projects successfully"}, status=status.HTTP_201_CREATED)


class UsersList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        qs = super().get_queryset()
        qs = user_utils.attach_extra_info(qs)
        users_list = self.generate_users_list(qs)
        return JsonResponse({'users_list': users_list})

    def generate_users_list(self, queryset):
        users_list = []
        for user in queryset:
            users_list.append({'name': user.full_name, 'id': user.id, 'username': user.username})
        return users_list