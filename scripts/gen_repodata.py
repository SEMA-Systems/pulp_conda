#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import os
import argparse
import shutil
import subprocess

OUTPUT_DIR = "repodata"

def list_package_urls(full_url):
    if not full_url.endswith('/'):
        full_url += '/'
    response = requests.get(full_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    return [full_url + link.get('href') for link in soup.find_all('a') if link.get('href').endswith('.tar.bz2')]

def download_packages(urls, arch):
    output_dir = os.path.join(OUTPUT_DIR, arch)
    os.makedirs(output_dir, exist_ok=True)
    for url in urls:
        filename = url.split('/')[-1]
        dest_path = os.path.join(output_dir, filename)
        if os.path.exists(dest_path):
            print(f"[{arch}] Skipping {filename} (already exists)")
            continue
        print(f"[{arch}] Downloading {filename}...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

# Run conda-index on the output folder
def run_conda_index():
    print("Running conda-index on repodata folder...")
    subprocess.run(["conda", "index", OUTPUT_DIR], check=True)


def main():
    parser = argparse.ArgumentParser(description="Download Conda packages for multiple architectures from a Pulp repo.")
    parser.add_argument("--repo-url", required=True, help="Base URL to the Conda base repo (e.g. http://localhost/pulp/content/conda)")
    parser.add_argument("--archs", required=True, help="Comma-separated list of architectures (e.g. noarch,linux-64)")

    # Remove output dir
    if os.path.exists(OUTPUT_DIR):
        print(f"Removing existing '{OUTPUT_DIR}' folder...")
        shutil.rmtree(OUTPUT_DIR)

    args = parser.parse_args()
    base_url = args.repo_url.rstrip('/')
    arch_list = [arch.strip() for arch in args.archs.split(',')]

    for arch in arch_list:
        full_url = f"{base_url}/{arch}/"
        print(f"\nFetching package list from: {full_url}")
        try:
            urls = list_package_urls(full_url)
            print(f"[{arch}] Found {len(urls)} packages.")
            download_packages(urls, arch)
        except Exception as e:
            print(f"[{arch}] Error: {e}")

    run_conda_index()

    print("\n✅ All done.")

if __name__ == "__main__":
    main()
