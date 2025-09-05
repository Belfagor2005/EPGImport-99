#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
****************************************
*        coded by Lululla              *
*             05/09/2025               *
****************************************
# Info corvoboys.org
"""

from os import listdir, makedirs, chdir, remove, walk
from os.path import join, isdir, exists, dirname
from shutil import rmtree, copyfileobj, copytree, copy2
import tarfile

# Compatibilità Python 2/3
try:
    import urllib.request as urllib_request  # Python 3
    import urllib.error as urllib_error
    PYTHON3 = True
except ImportError:
    import urllib2 as urllib_request  # Python 2
    import urllib2 as urllib_error
    PYTHON3 = False

try:
    import ssl
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False


def make_dirs(directory):
    """Create directory if it does not exist."""
    try:
        if not exists(directory):
            makedirs(directory)
    except OSError as e:
        print("Error creating directory {}: {}".format(directory, e))
        raise


def url_open(url, context=None):
    """Open URL with Python 2/3 compatibility."""
    try:
        if PYTHON3 and SSL_AVAILABLE and context:
            return urllib_request.urlopen(url, context=context)
        elif PYTHON3:
            return urllib_request.urlopen(url)
        else:
            # Python 2 - no context parameter
            return urllib_request.urlopen(url)
    except urllib_error.URLError as e:
        print("Error opening URL {}: {}".format(url, e))
        raise
    except Exception as e:
        print("Unexpected error opening URL: {}".format(e))
        raise


def copytree_compat(src, dst):
    """Copy tree with Python 2 and 3 compatibility."""
    if exists(dst):
        rmtree(dst, ignore_errors=True)
    copytree(src, dst)


def safe_remove(filepath):
    """Safely remove a file if it exists."""
    try:
        if exists(filepath):
            remove(filepath)
    except OSError as e:
        print("Error removing file {}: {}".format(filepath, e))


def safe_rmtree(dirpath):
    """Safely remove a directory tree if it exists."""
    try:
        if exists(dirpath):
            rmtree(dirpath, ignore_errors=True)
    except OSError as e:
        print("Error removing directory {}: {}".format(dirpath, e))


def extract_tarfile(tar, path):
    """Extract tar file with Python 2/3 compatibility."""
    if PYTHON3:
        # Python 3.12+ with filter support
        if hasattr(tarfile, 'data_filter'):
            tar.extractall(path, filter='data')
        else:
            tar.extractall(path)
    else:
        # Python 2 compatibility
        tar.extractall(path)


def main(url, removeExisting=True):
    TMPSources = "/tmp/EPGImport-Sources"
    dest_dir = "/etc/epgimport"
    SETTINGS_FILE = "/etc/enigma2/epgimport.conf"

    print("Starting EPG import update...")
    print("URL: {}".format(url))
    print("Temp directory: {}".format(TMPSources))
    print("Destination: {}".format(dest_dir))

    # Create directories
    make_dirs(TMPSources)
    make_dirs(dest_dir)

    # Change to temp directory
    chdir(TMPSources)
    tarball = "main.tar.gz"

    # SSL context (only for Python 3 with SSL)
    context = None
    if PYTHON3 and SSL_AVAILABLE:
        try:
            context = ssl._create_unverified_context()
        except:
            context = None
            print("SSL context creation failed, proceeding without")

    # Download the file
    response = None
    try:
        print("Downloading from {}...".format(url))
        response = url_open(url, context)
        with open(tarball, "wb") as out_file:
            copyfileobj(response, out_file)
        print("Download completed successfully")
    except Exception as e:
        print("Download failed: {}".format(e))
        return False
    finally:
        if response:
            response.close()

    # Remove existing files if requested
    if removeExisting:
        print("Cleaning destination directory...")
        for item in listdir(dest_dir):
            item_path = join(dest_dir, item)
            try:
                if isdir(item_path):
                    rmtree(item_path, ignore_errors=True)
                else:
                    if item.endswith(".xml") or item.endswith(".txt"):
                        remove(item_path)
            except OSError as e:
                print("Warning: Could not remove {}: {}".format(item_path, e))

    # Extract the tar file
    extracted_dir = None
    try:
        print("Extracting archive...")
        with tarfile.open(tarball, "r:gz") as tar:
            # Get the root directory name from the first member
            first_member = tar.getmembers()[0]
            if first_member.isdir():
                extracted_dir = join(TMPSources, first_member.name)
            else:
                extracted_dir = join(TMPSources, dirname(first_member.name))

            extract_tarfile(tar, TMPSources)

        print("Extraction completed to: {}".format(extracted_dir))

    except tarfile.TarError as e:
        print("Error extracting tar file: {}".format(e))
        safe_rmtree(TMPSources)
        return False
    except Exception as e:
        print("Unexpected error during extraction: {}".format(e))
        safe_rmtree(TMPSources)
        return False

    # Remove unwanted files and directories
    print("Cleaning up extracted files...")
    if exists(extracted_dir):
        for root, dirs, files in walk(extracted_dir):
            # Remove .github directories
            if '.github' in dirs:
                github_path = join(root, '.github')
                safe_rmtree(github_path)
                dirs.remove('.github')  # Prevent walking into removed dir

            # Remove .bb files
            for file in files:
                if file.endswith(".bb"):
                    bb_path = join(root, file)
                    safe_remove(bb_path)

    # Copy files to destination
    print("Copying files to destination...")
    if exists(extracted_dir):
        for item in listdir(extracted_dir):
            src_item = join(extracted_dir, item)
            dst_item = join(dest_dir, item)

            try:
                if isdir(src_item):
                    if exists(dst_item):
                        rmtree(dst_item, ignore_errors=True)
                    copytree(src_item, dst_item)
                else:
                    # Only copy XML and related files
                    if item.endswith(('.xml', '.txt', '.conf')):
                        copy2(src_item, dst_item)
            except Exception as e:
                print("Error copying {}: {}".format(item, e))

    # Cleanup
    print("Cleaning up temporary files...")
    safe_rmtree(TMPSources)

    # Optional: Remove settings file (commented out by default)
    # if exists(SETTINGS_FILE):
    #     safe_remove(SETTINGS_FILE)
    #     print("Settings file removed")

    # Sync filesystem if available
    try:
        from os import sync
        sync()
        print("Filesystem synced")
    except ImportError:
        pass  # sync not available on all systems

    print("EPG import update completed successfully!")
    return True


if __name__ == "__main__":
    # Example URL - replace with your actual URL
    url = "https://github.com/Belfagor2005/extracted_dir/archive/refs/heads/main.tar.gz"
    import sys
    # You can also get URL from command line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]

    success = main(url)
    sys.exit(0 if success else 1)
