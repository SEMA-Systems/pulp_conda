from logging import getLogger

from django.db import models

from pulpcore.plugin.models import (
    Content,
    ContentArtifact,
    Remote,
    Repository,
    Publication,
    Distribution,
)
from pulpcore.plugin.util import get_domain_pk

from .utils import extract_package_info

logger = getLogger(__name__)


class Package(Content):
    """
    The "conda" content type.

    Content of this type represents a single conda package uniquely identified by name, version, build and platform.

    Fields:
        name (str): The name of the conda package.
        version (str): The version of the conda package.
        build (str): The build number of the conda package.
        extension (str): The extension of the conda package.
    """

    TYPE = "package"

    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    build = models.CharField(max_length=255)
    extension = models.CharField(max_length=8)
    _pulp_domain = models.ForeignKey("core.Domain", default=get_domain_pk, on_delete=models.PROTECT)

    @property
    def relative_path(self):
        """
        Returns relative_path.
        """
        return f"{self.name}-{self.version}-{self.build}.{self.extension}"

    @staticmethod
    def init_from_artifact_and_relative_path(artifact, relative_path):
        name, version, build, extension = extract_package_info(relative_path)

        return Package(name=name, version=version, build=build, extension=extension)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("name", "version", "build", "extension", "_pulp_domain")

class Repodata(Content):
    """
    The "repodata" content type.

    Content of this type represents a single conda package uniquely identified by name, version, build and platform.

    Fields:
        digest (str): The SHA256 HEX digest of the repodata.json.
    """

    PROTECTED_FROM_RECLAIM = False

    TYPE = "repodata"

    digest = models.CharField(max_length=64, null=False)
    _pulp_domain = models.ForeignKey("core.Domain", default=get_domain_pk, on_delete=models.PROTECT)

    @property
    def relative_path(self):
        """
        Returns relative_path.
        """
        return "repodata.json"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("digest", "_pulp_domain")

class CondaPublication(Publication):
    """
    A Publication for CondaContent.

    Define any additional fields for your new publication if needed.
    """

    TYPE = "conda"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CondaRemote(Remote):
    """
    A Remote for CondaContent.

    Define any additional fields for your new remote if needed.
    """

    TYPE = "conda"

    def get_remote_artifact_content_type(self, relative_path=None):
        name, version, build, extension = extract_package_info(relative_path)

        if None in [name, version, build, extension]:
            return None

        return Package

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CondaRepository(Repository):
    """
    A Repository for CondaContent.

    Define any additional fields for your new repository if needed.
    """

    TYPE = "conda"

    CONTENT_TYPES = [Package, Repodata]
    REMOTE_TYPES = [CondaRemote]

    PULL_THROUGH_SUPPORTED = True

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class CondaDistribution(Distribution):
    """
    A Distribution for CondaContent.

    Define any additional fields for your new distribution if needed.
    """

    TYPE = "conda"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
