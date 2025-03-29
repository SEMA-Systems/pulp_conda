from django.db import transaction
from django_filters import CharFilter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from pulpcore.plugin.viewsets import RemoteFilter
from pulpcore.plugin import viewsets as core
from pulpcore.plugin.actions import ModifyRepositoryActionMixin
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import dispatch
from pulpcore.plugin.models import ContentArtifact, Artifact, PulpTemporaryFile


from . import models, serializers, tasks

from .utils import extract_package_info


class PackageFilter(core.ContentFilter):
    """
    FilterSet for Package.
    """

    class Meta:
        model = models.Package
        fields = [
            # ...
        ]


class PackageViewSet(core.SingleArtifactContentUploadViewSet):
    """
    A ViewSet for Package.

    Define endpoint name which will appear in the API endpoint for this content type.
    For example::
        https://pulp.example.com/pulp/api/v3/content/conda/packages/

    Also specify queryset and serializer for Package.
    """

    endpoint_name = "packages"
    queryset = models.Package.objects.all()
    serializer_class = serializers.PackageSerializer
    filterset_class = PackageFilter

    @transaction.atomic
    def create(self, request):
        """
        Handle conda package upload.
        """

        file = request.data["file"]
        repository_name = request.data["repository"]

        if not repository_name:
            return None

        name, version, build, extension = extract_package_info(file.name)

        if None in [name, version, build, extension]:
            return None

        repository = models.CondaRepository.objects.get(name=repository_name)

        try:
            temp_file = PulpTemporaryFile(file=file)
            artifact = Artifact.from_pulp_temporary_file(temp_file)
        except Exception:
            temp_file.delete()
            return None

        data = {
            "name": name,
            "version": version,
            "build": build,
            "extension": extension,
            "relative_path": f"{name}-{version}-{build}.{extension}",
        }

        serializer = serializers.PackageSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        package = models.Package.objects.filter(name=name, version=version, build=build, extension=extension).first()
        if not package:
            package = models.Package(
                name = name,
                version = version,
                build = build,
                extension = extension,
            )

            package.save()

            ContentArtifact.objects.create(
                content = package,
                artifact = artifact,
                relative_path = package.relative_path,
            )

            result = dispatch(
                tasks.publish_package,
                kwargs = {"repository_pk": repository.pk, "package_pk": package.pk},
                exclusive_resources = [repository, package],
            )

            return core.OperationPostponedResponse(result, request)
        else:
            artifact.delete()
            return None

class RepodataFilter(core.ContentFilter):
    """
    FilterSet for Repodata.
    """

    sha256 = CharFilter(field_name="digest")

    class Meta:
        model = models.Repodata
        fields = ["sha256"]

class RepodataViewSet(core.SingleArtifactContentUploadViewSet):
    """
    A ViewSet for Repodata.

    Define endpoint name which will appear in the API endpoint for this content type.
    For example:
        https://pulp.example.com/pulp/api/v3/content/conda/repodatas/

    Also specify queryset and serializer for Package.
    """

    endpoint_name = "repodatas"
    queryset = models.Repodata.objects.all()
    serializer_class = serializers.RepodataSerializer
    filterset_class = RepodataFilter

    @transaction.atomic
    def create(self, request):
        """
        Handle repodata.json upload.
        """

        file = request.data["file"]
        repository_name = request.data["repository"]

        if not repository_name:
            return None

        repository = models.CondaRepository.objects.get(name=repository_name)
        try:
            temp_file = PulpTemporaryFile(file=file)
            artifact = Artifact.from_pulp_temporary_file(temp_file)
        except Exception:
            temp_file.delete()
            return None

        data = {
            "digest": artifact.sha256,
            "relative_path": "repodata.json",
        }

        serializer = serializers.RepodataSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        repodata = models.Repodata.objects.filter(digest=artifact.sha256).first()
        if not repodata:
            repodata = models.Repodata(
                digest = artifact.sha256,
            )

            repodata.save()

            ContentArtifact.objects.create(
                content = repodata,
                artifact = artifact,
                relative_path = repodata.relative_path,
            )

            result = dispatch(
                tasks.publish_repodata,
                kwargs = {"repository_pk": repository.pk, "repodata_pk": repodata.pk},
                exclusive_resources = [repository, repodata],
            )

            return core.OperationPostponedResponse(result, request)
        else:
            artifact.delete()
            return None

class CondaRemoteFilter(RemoteFilter):
    """
    A FilterSet for CondaRemote.
    """

    class Meta:
        model = models.CondaRemote
        fields = [
            # ...
        ]


class CondaRemoteViewSet(core.RemoteViewSet):
    """
    A ViewSet for CondaRemote.

    Similar to the CondaContentViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "conda"
    queryset = models.CondaRemote.objects.all()
    serializer_class = serializers.CondaRemoteSerializer


class CondaRepositoryViewSet(core.RepositoryViewSet, ModifyRepositoryActionMixin):
    """
    A ViewSet for CondaRepository.

    Similar to the CondaContentViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "conda"
    queryset = models.CondaRepository.objects.all()
    serializer_class = serializers.CondaRepositorySerializer

    # This decorator is necessary since a sync operation is asyncrounous and returns
    # the id and href of the sync task.
    @extend_schema(
        description="Trigger an asynchronous task to sync content.",
        summary="Sync from remote",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Dispatches a sync task.
        """
        repository = self.get_object()
        serializer = RepositorySyncURLSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        remote = serializer.validated_data.get("remote")
        mirror = serializer.validated_data.get("mirror")

        result = dispatch(
            tasks.synchronize,
            [repository, remote],
            kwargs={
                "remote_pk": str(remote.pk),
                "repository_pk": str(repository.pk),
                "mirror": mirror,
            },
        )
        return core.OperationPostponedResponse(result, request)


class CondaRepositoryVersionViewSet(core.RepositoryVersionViewSet):
    """
    A ViewSet for a CondaRepositoryVersion represents a single
    Conda repository version.
    """

    parent_viewset = CondaRepositoryViewSet


class CondaPublicationViewSet(core.PublicationViewSet):
    """
    A ViewSet for CondaPublication.

    Similar to the CondaContentViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "conda"
    queryset = models.CondaPublication.objects.exclude(complete=False)
    serializer_class = serializers.CondaPublicationSerializer

    # This decorator is necessary since a publish operation is asyncrounous and returns
    # the id and href of the publish task.
    @extend_schema(
        description="Trigger an asynchronous task to publish content",
        responses={202: AsyncOperationResponseSerializer},
    )
    def create(self, request):
        """
        Publishes a repository.

        Either the ``repository`` or the ``repository_version`` fields can
        be provided but not both at the same time.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get("repository_version")

        result = dispatch(
            tasks.publish,
            [repository_version.repository],
            kwargs={"repository_version_pk": str(repository_version.pk)},
        )
        return core.OperationPostponedResponse(result, request)


class CondaDistributionViewSet(core.DistributionViewSet):
    """
    A ViewSet for CondaDistribution.

    Similar to the CondaContentViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "conda"
    queryset = models.CondaDistribution.objects.all()
    serializer_class = serializers.CondaDistributionSerializer
