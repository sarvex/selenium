#!/usr/bin/env python

import codecs
import hashlib
import json
import urllib3

# Find the current stable versions of each browser we
# support and the sha256 of these. That's useful for
# updating `//common:repositories.bzl`

http = urllib3.PoolManager()

def calculate_hash(url):
    h = hashlib.sha256()
    r = http.request('GET', url, preload_content=False)
    for b in iter(lambda: r.read(4096), b""):
        h.update(b)
    return h.hexdigest()

def chromedriver():
    r = http.request('GET', 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
    v = r.data.decode('utf-8')

    content = ""

    linux = f'https://chromedriver.storage.googleapis.com/{v}/chromedriver_linux64.zip'
    sha = calculate_hash(linux)
    content += """
    http_archive(
        name = "linux_chromedriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"chromedriver\\"])",
    )
    """ % (
        linux,
        sha,
    )

    mac = f'https://chromedriver.storage.googleapis.com/{v}/chromedriver_mac64.zip'
    sha = calculate_hash(mac)
    content += """
    http_archive(
        name = "mac_chromedriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"chromedriver\\"])",
    )
    """ % (
        mac,
        sha,
    )
    return content

def chrome():
    # Find the current latest stable revision
    r = http.request('GET', 'https://omahaproxy.appspot.com/all.json?channel=stable&os=linux')
    max_version = int(json.loads(r.data)[0]['versions'][0]['branch_base_position'])
    min_version = max_version - 1500

    # count down from most recent to a version which has something for everyone
    for v in range(max_version, min_version, -1):
        r = http.request(
            'HEAD',
            f'https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/{v}/chrome-linux.zip',
        )
        if r.status != 200:
            continue

        r = http.request(
            'HEAD',
            f'https://storage.googleapis.com/chromium-browser-snapshots/Mac/{v}/chrome-mac.zip',
        )
        if r.status != 200:
            continue

        content = ""

        linux = f'https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/{v}/chrome-linux.zip'
        sha = calculate_hash(linux)

        content += """
    http_archive(
        name = "linux_chrome",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"chrome-linux\\"])",
    )
    """ % (
            linux,
            sha,
        )

        mac = f'https://storage.googleapis.com/chromium-browser-snapshots/Mac/{v}/chrome-mac.zip'
        sha = calculate_hash(mac)

        content += """
    http_archive(
        name = "mac_chrome",
        url = "%s",
        sha256 = "%s",
        strip_prefix = "chrome-mac",
        build_file_content = "exports_files([\\"Chromium.app\\"])",
    )
    """ % (
            mac,
            sha,
        )

        return content
    raise RuntimeError("Cannot find stable chrome")

def edge():
    r = http.request('GET', 'https://msedgedriver.azureedge.net/LATEST_STABLE')
    v = r.data.decode('utf-16').strip()

    content = ""

    edge = f"https://officecdn-microsoft-com.akamaized.net/pr/C1297A47-86C4-4C1F-97FA-950631F94777/MacAutoupdate/MicrosoftEdge-{v}.pkg?platform=Mac&Consent=0&channel=Stable"
    sha = calculate_hash(edge)

    content += """
    pkg_archive(
        name = "mac_edge",
        url = "%s",
        sha256 = "%s",
        move = {
            "MicrosoftEdge-%s.pkg/Payload/Microsoft Edge.app": "Edge.app",
        },
        build_file_content = "exports_files([\\"Edge.app\\"])",
    )
    """ % (
        edge,
        sha,
        v,
    )

    return content

def edgedriver():
    r = http.request('GET', 'https://msedgedriver.azureedge.net/LATEST_STABLE')
    v = r.data.decode('utf-16').strip()

    content = ""

    linux = f"https://msedgedriver.azureedge.net/{v}/edgedriver_linux64.zip"
    sha = calculate_hash(linux)
    content += """
    http_archive(
        name = "linux_edgedriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"msedgedriver\\"])",
    )
    """ % (
        linux,
        sha,
    )

    mac = f"https://msedgedriver.azureedge.net/{v}/edgedriver_mac64.zip"
    sha = calculate_hash(mac)
    content += """
    http_archive(
        name = "mac_edgedriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"msedgedriver\\"])",
    )
    """ % (
        mac,
        sha,
    )
    return content

def geckodriver():
    content = ""

    r = http.request('GET', 'https://api.github.com/repos/mozilla/geckodriver/releases/latest')
    for a in json.loads(r.data)['assets']:
        if a['name'].endswith('-linux64.tar.gz'):
            url = a['browser_download_url']
            sha = calculate_hash(url)
            content = content + \
                  """
    http_archive(
        name = "linux_geckodriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"geckodriver\\"])",
    )
    """ % (url, sha)

        if a['name'].endswith('-macos.tar.gz'):
            url = a['browser_download_url']
            sha = calculate_hash(url)
            content = content + \
                  """
    http_archive(
        name = "mac_geckodriver",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"geckodriver\\"])",
    )
        """ % (url, sha)
    return content

def firefox():
    r = http.request('GET', 'https://product-details.mozilla.org/1.0/firefox_versions.json')
    v = json.loads(r.data)['LATEST_FIREFOX_VERSION']

    content = ""

    linux = f"https://ftp.mozilla.org/pub/firefox/releases/{v}/linux-x86_64/en-US/firefox-{v}.tar.bz2"
    sha = calculate_hash(linux)
    content += """
    http_archive(
        name = "linux_firefox",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"firefox\\"])",
    )
    """ % (
        linux,
        sha,
    )

    mac = "https://ftp.mozilla.org/pub/firefox/releases/%s/mac/en-US/Firefox%%20%s.dmg" % (v, v)
    sha = calculate_hash(mac)
    content += """
    dmg_archive(
        name = "mac_firefox",
        url = "%s",
        sha256 = "%s",
        build_file_content = "exports_files([\\"Firefox.app\\"])",
    )
    """ % (
        mac,
        sha,
    )

    return content

if __name__ == '__main__':
    content = """
# This file has been generated using `bazel run scripts:pinned_browsers`

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("//common/private:dmg_archive.bzl", "dmg_archive")
load("//common/private:drivers.bzl", "local_drivers")
load("//common/private:pkg_archive.bzl", "pkg_archive")

def pin_browsers():
    local_drivers()
"""
    content += firefox()
    content = content + geckodriver()
    content = content + edge()
    content = content + edgedriver()
    content = content + chrome()
    content = content + chromedriver()

    print(content)
