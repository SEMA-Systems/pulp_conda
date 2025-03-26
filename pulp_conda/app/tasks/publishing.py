import logging
import tempfile
from gettext import gettext as _

from pulpcore.plugin.models import (
    RepositoryVersion,
    PublishedArtifact,
    PublishedMetadata,
    RemoteArtifact,
)

from pulp_conda.app.models import CondaRepository, Repodata, Package, CondaDistribution


log = logging.getLogger(__name__)


def publish_package(repository_pk, package_pk):
    """
    Create a new Repository version when a new package is uploaded and switch distribution to new version.

    Args:
        repository_pk (str): Create a new version for this repository.
        package_pk (str): Add this package to the new repository version.
    """

    repository = CondaRepository.objects.get(pk=repository_pk)
    distribution = CondaDistribution.objects.get(repository=repository)

    with repository.new_version() as new_version:
        new_version.add_content(Package.objects.filter(pk=package_pk))

    distribution.repository_version = new_version
    distribution.save()

def publish_repodata(repository_pk, repodata_pk):
    """
    Create a new Repository version when a new repodata is uploaded and switch distribution to new version.

    Args:
        repository_pk (str): Create a new version for this repository.
        repodata_pk (str): Add this repodata.json to the new repository version.
    """

    repository = CondaRepository.objects.get(pk=repository_pk)
    distribution = CondaDistribution.objects.get(repository=repository)

    with repository.new_version() as new_version:
        # Since there should always only be one repodata.json in a given repository, it is save to delete all objects.
        # All objects = last uploaded repodata.json. This is needed because otherwise there are two files with the same
        # relative_path and Pulp does not know which one to serve.
        new_version.remove_content(Repodata.objects.all())
        new_version.add_content(Repodata.objects.filter(pk=repodata_pk))

    distribution.repository_version = new_version
    distribution.save()