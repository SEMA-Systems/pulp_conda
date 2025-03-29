import re


def extract_package_info(relative_path):
    """ "
    Tries to extract the name, version and build of a package from the (relative) path string.

    Args:
      The (relative) path string. "name-version-build.{conda,tar.bz2}"
    """

    pattern = r"^(?P<name>.+)-(?P<version>\d.+)-(?P<build>.+)\.(?P<extension>conda|tar\.bz2)$"
    match = re.match(pattern, relative_path)

    if match:
        name = match.group("name")
        version = match.group("version")
        build = match.group("build")
        extension = match.group("extension")
        return name, version, build, extension
    else:
        return None, None, None, None
