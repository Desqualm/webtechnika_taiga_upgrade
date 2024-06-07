from taiga.base.api import serializers
from taiga.projects.models import Project


class ProjectIdSerializers(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id']
