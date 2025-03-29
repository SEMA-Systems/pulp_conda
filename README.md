# pulp-conda

A Pulp plugin to support hosting your own conda.

## Package upload

In order to upload a conda package to Pulp there are two steps that have to be done:

1. Upload the package
1. Upload the corresponding ```repodata.json``` for the ```noarch``` and your own architecture

### Workflow

1. Create a ```noarch``` repository. **Without a ```noarch``` repository the ```conda``` CLI will not work!**
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/repositories/conda/conda/" \
-d '{"name": "noarch"}' \
-H "Content-Type: application/json"
```

2. Create a repository for your architecture. We suggest that you follow the naming convention of supported conda architectures, i.e. ```linux-32, linux-64, linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64cle, linux-s390x, noarch, osx-64, osx-arm64, win-32, win-64```.
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/repositories/conda/conda/" \
-d '{"name": "<repository_name>"}' \
-H "Content-Type: application/json"
```

3. Create a ```noarch``` distribution. **Without a ```noarch``` distribution the ```conda``` CLI will not work!**
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/distributions/conda/conda/" \
-d '{"name": "noarch", "base_path": "noarch", "repository": "<noarch_repository_href>"}' \
-H "Content-Type: application/json"
```

4. Create a distribution for your architecture. **The ```base_path``` needs to follow the naming convention of supported conda architectures for the ```conda``` CLI to work, i.e. ```linux-32, linux-64, linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64cle, linux-s390x, noarch, osx-64, osx-arm64, win-32, win-64```.**
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/distributions/conda/conda/" \
-d '{"name": "<distribution_name>", "base_path": "<base_path>", "repository": "<repository_href>"}' \
-H "Content-Type: application/json"
```

5. Upload a package and attach it to the repository for your architecture. A new repository version is automatically crated.
```sh
curl -sk -u <username>:<password> "<base_url>/pulp/api/v3/content/conda/packages/" \
-F "file=@<path_to_file>" -F "repository=<repository_name>"
```

6. Upload a ```repodata.json``` for the ```noarch``` repository. **Without a ```repodata.json``` in the ```noarch``` repository, the ```conda``` CLI will not work!**
```sh
curl -sk -u <username>:<password> "<base_url>/pulp/api/v3/content/conda/repodatas/" \
-F "file=@<path_to_file>" -F "repository=noarch"
```

7. Upload a ```repodata.json``` for your architecture. **Without a ```repodata.json``` the ```conda``` CLI will cannot resolve your package!**
```sh
curl -sk -u <username>:<password> "<base_url>/pulp/api/v3/content/conda/repodatas/" \
-F "file=@<path_to_file>" -F "repository=<repository_name>"
```

## Pull-through Cache

In order to enable the pull-through cache feature one needs to create a remote which points to the reopsitory to be pulled from and a distribution to serve it from the Pulp server.

1. Create a ```noarch``` remote to a repository (e.g. ```https://repo.anaconda.com/pkgs/main/noarch```). **Without a ```noarch``` distribution the ```conda``` CLI will not work!**
```sh
curl -sk -u <user>:<password> -X POST "<base_url>/pulp/api/v3/remotes/conda/conda/" \
-d '{"name": "noarch", "url": "<noarch_remote_url>"}' \
-H 'Content-Type: application/json'
```

2. Create a remote to a repository for your architecture (e.g. ```https://repo.anaconda.com/pkgs/main/<architecture>```). We suggest that you follow the naming convention of supported conda architectures, i.e. ```linux-32, linux-64, linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64cle, linux-s390x, noarch, osx-64, osx-arm64, win-32, win-64```.
```sh
curl -sk -u <user>:<password> -X POST "<base_url>/pulp/api/v3/remotes/conda/conda/" \
-d '{"name": "<remote_name>", "url": "<remote_url>"}' \
-H 'Content-Type: application/json'
```

3. Create a ```noarch``` distribution and link the ````noarch``` remote to it. **Without a ```noarch``` distribution the ```conda``` CLI will not work!**
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/distributions/conda/conda/" \
-d '{"name": "cache/noarch", "base_path": "cache/noarch", "remote": "<noarch_remote_href>"}' \
-H "Content-Type: application/json"
```

4. Create a distribution for your architecture and link the remote to it. **The ```base_path``` needs to follow the naming convention of supported conda architectures for the ```conda``` CLI to work, i.e. ```linux-32, linux-64, linux-aarch64, linux-armv6l, linux-armv7l, linux-ppc64cle, linux-s390x, noarch, osx-64, osx-arm64, win-32, win-64```.**
```sh
curl -sk -u <username>:<password> -X POST "<base_url>/pulp/api/v3/distributions/conda/conda/" \
-d '{"name": "cache/<distribution_name>", "base_path": "cache/<base_path>", "remote": "<remote_href>"}' \
-H "Content-Type: application/json"
```

## Conda CLI configuration

If you have followed all instructions above you can now replace the channels in your ```conda``` configuration file.
```sh
channels:
  - http://localhost/pulp/content/
  - http://localhost/pulp/content/cache/
```

This first channel looks for the package in the repositories where you upload your own packages and the second channel is the pull-through cache you set up. Therefore, all downloads of packages go through the Pulp server.