import os
from io import StringIO

from invoke import run, task

os.environ["DIC_BASE_DIR"] = os.path.join(".", ".deviceinfocompare")


@task
def designer(context):
    run("qt6-tools designer ui/deviceinfocompare.ui")


@task
def build(context):
    DIC_VERSION = (
        open(os.path.join("deviceinfocompare", "VERSION.txt"), "r", encoding="utf8")
        .read()
        .strip()
    )

    run(
        f'pyinstaller \
--name=deviceinfocompare-v{DIC_VERSION} \
--noconfirm --onefile \
--icon "./ui/icon.ico" \
--add-data "./deviceinfocompare;deviceinfocompare/" \
--add-data "./ui;ui/" \
--add-data "./cdic.py;." \
"./cdic.py"'
    )


@task
def update_version_txt(context):
    DIC_VERSION = (
        open(os.path.join("deviceinfocompare", "VERSION.txt"), "r", encoding="utf8")
        .read()
        .strip()
    )

    latest_commit_msg = StringIO()
    run("git log -1 --pretty=%B", out_stream=latest_commit_msg)
    latest_commit_msg = latest_commit_msg.getvalue().strip()

    major, minor, patch = (int(i) for i in DIC_VERSION.split("."))

    if "#patch" in latest_commit_msg:
        patch += 1
    elif "#minor" in latest_commit_msg:
        patch = 0
        minor += 1
    elif "#major" in latest_commit_msg:
        patch, minor = 0, 0
        major += 1

    NEW_VER = ".".join([str(i) for i in (major, minor, patch)])

    if NEW_VER == DIC_VERSION:
        print("No new version marker, skipping")
    else:
        open(
            os.path.join("deviceinfocompare", "VERSION.txt"), "w", encoding="utf8"
        ).write(NEW_VER)
        print(f"New version is {NEW_VER}")
        run(f'git add -A . && git commit -m "#bump to {NEW_VER}"')


@task(pre=(update_version_txt,))
def tag(context):
    """Auto add tag to git commit depending on deviceinfocompare version"""

    DIC_VERSION = (
        open(os.path.join("deviceinfocompare", "VERSION.txt"), "r", encoding="utf8")
        .read()
        .strip()
    )

    latest_tag = StringIO()

    run("git describe --abbrev=0 --tags", out_stream=latest_tag, warn=True)
    latest_tag = latest_tag.getvalue().strip()

    if f"v{DIC_VERSION}" != latest_tag:
        run(f"git tag v{DIC_VERSION}")
        run(f"git push --tags")
    else:
        print("No new version, skipping")
