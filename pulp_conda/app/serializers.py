from gettext import gettext as _
from rest_framework import serializers

from pulpcore.plugin import serializers as core_serializers
from pulpcore.plugin import models as core_models
from pulpcore.plugin.util import get_domain_pk

from . import models


class PackageSerializer(core_serializers.SingleArtifactContentUploadSerializer):
    """
    A serializer for Package.
    """

    name = serializers.CharField()
    version = serializers.CharField()
    build = serializers.CharField()
    extension = serializers.CharField()
    relative_path = serializers.CharField()

    class Meta:
        fields = core_serializers.SingleArtifactContentUploadSerializer.Meta.fields + (
            "name",
            "version",
            "build",
            "extension",
            "relative_path",
        )
        model = models.Package

class RepodataSerializer(core_serializers.SingleArtifactContentUploadSerializer):
    """
    A serializer for Repodata.
    """

    digest = serializers.CharField()
    relative_path = serializers.CharField()

    class Meta:
        fields = (
            core_serializers.SingleArtifactContentUploadSerializer.Meta.fields + (
                "digest",
                "relative_path",
            )
        )
        model = models.Repodata

class CondaRemoteSerializer(core_serializers.RemoteSerializer):
    """
    A Serializer for CondaRemote.

    Add any new fields if defined on CondaRemote.
    Similar to the example above, in CondaContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.RemoteSerializer.Meta.validators + [myValidator1, myValidator2]

    By default the 'policy' field in platform.RemoteSerializer only validates the choice
    'immediate'. To add on-demand support for more 'policy' options, e.g. 'streamed' or 'on_demand',
    re-define the 'policy' option as follows::

    policy = serializers.ChoiceField(
        help_text="The policy to use when downloading content. The possible values include: "
                  "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default.",
        choices=models.Remote.POLICY_CHOICES,
        default=models.Remote.IMMEDIATE
    )
    """

    class Meta:
        fields = core_serializers.RemoteSerializer.Meta.fields
        model = models.CondaRemote


class CondaRepositorySerializer(core_serializers.RepositorySerializer):
    """
    A Serializer for CondaRepository.

    Add any new fields if defined on CondaRepository.
    Similar to the example above, in CondaContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.RepositorySerializer.Meta.validators + [myValidator1, myValidator2]
    """

    class Meta:
        fields = core_serializers.RepositorySerializer.Meta.fields
        model = models.CondaRepository


class CondaPublicationSerializer(core_serializers.PublicationSerializer):
    """
    A Serializer for CondaPublication.

    Add any new fields if defined on CondaPublication.
    Similar to the example above, in CondaContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.PublicationSerializer.Meta.validators + [myValidator1, myValidator2]
    """

    class Meta:
        fields = core_serializers.PublicationSerializer.Meta.fields
        model = models.CondaPublication


class CondaDistributionSerializer(core_serializers.DistributionSerializer):
    """
    A Serializer for CondaDistribution.

    Add any new fields if defined on CondaDistribution.
    Similar to the example above, in CondaContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.DistributionSerializer.Meta.validators + [
            myValidator1, myValidator2]
    """

    remote = core_serializers.DetailRelatedField(
        required=False,
        help_text=_("Remote that can be used to fetch content when using pull-through caching."),
        view_name_pattern=r"remotes(-.*/.*)?-detail",
        queryset=core_models.Remote.objects.all(),
        allow_null=True,
    )


    # uncomment these lines and remove the publication field if not using publications
    # repository_version = RepositoryVersionRelatedField(
    #     required=False, help_text=_("RepositoryVersion to be served"), allow_null=True
    # )

    class Meta:
        fields = core_serializers.DistributionSerializer.Meta.fields + ("remote",)
        model = models.CondaDistribution
