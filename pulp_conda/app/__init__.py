from pulpcore.plugin import PulpPluginAppConfig


class PulpCondaPluginAppConfig(PulpPluginAppConfig):
    """Entry point for the conda plugin."""

    name = "pulp_conda.app"
    label = "conda"
    version = "0.0.0.dev"
    python_package_name = "pulp_conda"
    domain_compatible = True
