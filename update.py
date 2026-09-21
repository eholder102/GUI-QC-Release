import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import time
import logging
from pathlib import Path
from urllib.request import Request, urlopen
import ssl
import certifi

APP_DIR = Path(__file__).resolve().parent
UPDATE_INFO_FILE = APP_DIR / "update_ready.json"
LOG_FILE = APP_DIR / "debug.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    encoding="utf-8",
    level=logging.DEBUG,
    force=True
)

logger = logging.getLogger("update")

logger.info("========== UPDATE.PY STARTED ==========")
logger.info("APP_DIR: %s", APP_DIR)
logger.info("LOG_FILE: %s", LOG_FILE)

GITHUB_OWNER = "eholder102"
GITHUB_REPO = "GUI-QC-Release"


def get_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

    logger.info("Checking GitHub for latest release")

    request = Request(
        url,
        headers={
            "User-Agent": "QC-Release-Updater"
        }
    )

    context = ssl.create_default_context(
    cafile=certifi.where()
)

    with urlopen(
        request,
        timeout=10,
        context=context
    ) as response:
        release = json.loads(response.read().decode("utf-8"))

    logger.info(
        "Latest GitHub release: %s",
        release.get("tag_name")
    )

    return release


def version_tuple(version):
    return tuple(
        int(x)
        for x in version.lstrip("v").split(".")
    )


def update_available(current_version, latest_version):
    return version_tuple(latest_version) > version_tuple(current_version)


def download_update(download_url):
    logger.info("Downloading update from GitHub")

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="QCReleaseUpdate_"
        )
    )

    zip_path = temp_dir / "update.zip"

    request = Request(
        download_url,
        headers={
            "User-Agent": "QC-Release-Updater"
        }
    )

    context = ssl.create_default_context(
    cafile=certifi.where()
)

    with urlopen(
        request,
        timeout=10,
        context=context
    ) as response:

        with open(
            zip_path,
            "wb"
        ) as file:

            shutil.copyfileobj(
                response,
                file
            )

    logger.info(
        "Update downloaded successfully"
    )

    return temp_dir, zip_path


def install_update(zip_path, temp_dir):

    logger.info("Installing update")

    extract_dir = temp_dir / "extracted"
    extract_dir.mkdir()

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as archive:

        archive.extractall(
            extract_dir
        )

    contents = list(
        extract_dir.iterdir()
    )

    if (
        len(contents) == 1
        and contents[0].is_dir()
    ):
        source_dir = contents[0]
    else:
        source_dir = extract_dir

    protected = {
        "Python",
        "credentials.json",
        "sheetstoken.json",
        "drivetoken.json",
        "Reports",
        "Labels",
        "debug.log",
        "saved_batches.txt",
        "temp_test_sheet.pdf",
        "annotated_temp_test_sheet.pdf",
    }

    for item in source_dir.iterdir():

        if item.name in protected:

            logger.debug(
                "Skipping protected item: %s",
                item.name
            )

            continue

        destination = APP_DIR / item.name

        logger.info(
            "Updating: %s",
            item.name
        )

        if item.is_dir():

            shutil.copytree(
                item,
                destination,
                dirs_exist_ok=True
            )

        else:

            shutil.copy2(
                item,
                destination
            )

    logger.info(
        "Update installation complete"
    )


def wait_for_process(pid):
    logger.info("Waiting for QC Release process %s to close", pid)

    import ctypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    for i in range(60):
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid
        )

        if not handle:
            error = ctypes.get_last_error()

            logger.info(
                "Process check %d/60: PID %s no longer exists (Windows error %s)",
                i + 1,
                pid,
                error
            )

            return True

        exit_code = ctypes.c_ulong()

        success = kernel32.GetExitCodeProcess(
            handle,
            ctypes.byref(exit_code)
        )

        kernel32.CloseHandle(handle)

        if not success:
            logger.info(
                "Process check %d/60: could not query PID %s",
                i + 1,
                pid
            )
            return True

        logger.info(
            "Process check %d/60: PID %s exit code = %s",
            i + 1,
            pid,
            exit_code.value
        )

        if exit_code.value != STILL_ACTIVE:
            logger.info(
                "QC Release process %s has exited",
                pid
            )
            return True

        time.sleep(1)

    logger.error(
        "Timed out waiting for QC Release process %s to close",
        pid
    )

    return False

def launch_application():

    logger.info(
        "Starting updated QC Release"
    )

    subprocess.Popen(
        [
            str(APP_DIR / "Python" / "pythonw.exe"),
            str(APP_DIR / "main.py"),
        ],
        cwd=str(APP_DIR)
    )


def main():

    logger.info("Updater arguments: %s", sys.argv)

    if len(sys.argv) < 3:
        logger.warning("Updater started with insufficient arguments")
        return

    current_version = sys.argv[1]

    try:

        # ---------------------------------------------------------
        # INSTALL UPDATE
        # ---------------------------------------------------------

        if sys.argv[2] == "--install":

            if len(sys.argv) < 5:
                logger.error("Not enough arguments for install mode")
                return

            zip_path = Path(sys.argv[3])
            temp_dir = Path(sys.argv[4])

            logger.info("Install mode started")
            logger.info("Update ZIP: %s", zip_path)
            logger.info("Temp directory: %s", temp_dir)

            logger.info("Waiting for QC Release to finish closing...")
            logger.info("About to sleep for 3 seconds")

            time.sleep(3)

            logger.info("Finished sleeping, starting installation")

            install_update(
                zip_path,
                temp_dir
            )

            launch_application()

            logger.info(
                "Update completed successfully"
            )

            return

        # ---------------------------------------------------------
        # UPDATE CHECK
        # ---------------------------------------------------------

        logger.info(
            "Checking for updates. Current version: %s",
            current_version
        )

        release = get_latest_release()

        latest_version = release["tag_name"]

        logger.info(
            "Current version: %s | Latest version: %s",
            current_version,
            latest_version
        )

        if not update_available(
            current_version,
            latest_version
        ):

            logger.info("Application is up to date")
            return

        logger.info(
            "Update available: %s -> %s",
            current_version,
            latest_version
        )

        update_asset = None

        for asset in release.get("assets", []):

            if asset["name"].lower() == "update.zip":

                update_asset = asset
                break

        if update_asset is None:

            logger.warning(
                "No update.zip found in GitHub release"
            )

            return

        temp_dir, zip_path = download_update(
            update_asset["browser_download_url"]
        )

        with open(
            UPDATE_INFO_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {
                    "version": latest_version,
                    "zip_path": str(zip_path),
                    "temp_dir": str(temp_dir)
                },
                file
            )

        logger.info(
            "Update downloaded and marked as ready: %s",
            latest_version
        )

    except Exception:

        logger.exception(
            "Updater failed"
        )


if __name__ == "__main__":
    main()
