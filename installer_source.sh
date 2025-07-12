#!/bin/bash
## setup source command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/EPGImport-99/main/installer_source.sh -O - | /bin/bash

version="1"
changelog="\n--Update Source xml EPGImport"
TMPSources=/var/volatile/tmp/EPGimport-Sources-main

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/EPGImport
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/EPGImport
fi

if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
else
    STATUS=/var/lib/opkg/status
    OSTYPE=OE20
fi

if ! command -v wget >/dev/null; then
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y wget || { echo "Failed to install wget"; exit 1; }
    else
        opkg update && opkg install wget || { echo "Failed to install wget"; exit 1; }
    fi
fi

if [ ! -d "$PLUGINPATH" ]; then
    echo "EPGImport plugin not found at $PLUGINPATH"
    exit 1
fi

mkdir -p "$TMPSources" || { echo "Failed to create temp directory"; exit 1; }
mkdir -p '/etc/epgimport' || { echo "Failed to create epgimport directory"; exit 1; }

cd "$TMPSources" || exit 1
wget --no-check-certificate "https://github.com/Belfagor2005/EPGimport-Sources/archive/refs/heads/main.tar.gz" -O main.tar.gz || {
    echo "Download failed"; exit 1;
}

tar -xzf main.tar.gz || {
    echo "Extraction failed"; exit 1;
}

find "$TMPSources/EPGimport-Sources-main" -type f -name "*.bb" -delete
cp -r "$TMPSources/EPGimport-Sources-main"/* '/etc/epgimport' || {
    echo "Copy failed"; exit 1;
}

rm -rf "$TMPSources"
sync

box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
FILE="/etc/image-version"
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

echo "#########################################################
#          EPGImport Sources $version INSTALLED         #
#########################################################
BOX MODEL: $box_type
IMAGE: ${distro_value:-Unknown} ${distro_version:-Unknown}"

exit 0