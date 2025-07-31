#!/bin/bash
## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/EPGImport-99/main/installer.sh -O - | /bin/bash

version='99'
changelog='\n--My Fake Version'
TMPPATH=/tmp/EPGImport-99-main
TMPSources=/tmp/EPGimport-Sources-main
FILEPATH=/tmp/epgimport.tar.gz

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/EPGImport
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/EPGImport
fi

if [ -f /var/lib/dpkg/status ]; then
    OSTYPE=DreamOs
else
    OSTYPE=OE20
fi

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y wget || { echo "Failed to install wget"; exit 1; }
    else
        opkg update && opkg install wget || { echo "Failed to install wget"; exit 1; }
    fi
fi

# Determine requests package depending on Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    Packagerequests=python3-requests
else
    Packagerequests=python-requests
fi

# Install python requests package if missing
if ! grep -qs "Package: $Packagerequests" /var/lib/*/status; then
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y "$Packagerequests" || { echo "Failed to install $Packagerequests"; exit 1; }
    else
        opkg update && opkg install "$Packagerequests" || { echo "Failed to install $Packagerequests"; exit 1; }
    fi
fi

# Cleanup old temp files/folders
[ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
[ -d "$TMPSources" ] && rm -rf "$TMPSources"
[ -f "$FILEPATH" ] && rm -f "$FILEPATH"

mkdir -p "$TMPPATH" || { echo "Failed to create temp directory"; exit 1; }
cd "$TMPPATH" || exit 1

# Download main plugin archive
wget --no-check-certificate 'https://github.com/Belfagor2005/EPGImport-99/archive/refs/heads/main.tar.gz' -O "$FILEPATH" || {
    echo "Download failed"; exit 1;
}

# Extract plugin archive
tar -xzf "$FILEPATH" -C /tmp/ || {
    echo "Extraction failed"; exit 1;
}

# Copy plugin files
cp -r /tmp/EPGImport-99-main/usr/ / || {
    echo "Copy failed"; exit 1;
}

# Verify plugin installation
if [ ! -d "$PLUGINPATH" ]; then
    echo "Installation failed: $PLUGINPATH missing"
    exit 1
fi

# Prepare sources folder and download sources archive
mkdir -p "$TMPSources" || { echo "Failed to create sources directory"; exit 1; }
mkdir -p '/etc/epgimport' || { echo "Failed to create epgimport directory"; exit 1; }

cd "$TMPSources" || exit 1
wget --no-check-certificate 'https://github.com/doglover3920/EPGimport-Sources/archive/refs/heads/main.tar.gz' -O sources.tar.gz || {
    echo "Sources download failed"; exit 1;
}

tar -xzf sources.tar.gz || {
    echo "Sources extraction failed"; exit 1;
}

cp -r "$TMPSources/EPGimport-Sources-main"/* '/etc/epgimport' || {
    echo "Sources copy failed"; exit 1;
}

# Cleanup temporary files
rm -rf "$TMPPATH" "$TMPSources" "$FILEPATH" /tmp/EPGImport-99-main /tmp/sources.tar.gz
sync

# System info
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "/etc/image-version" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "/etc/image-version" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

echo "#########################################################
#          EPGImport $version INSTALLED SUCCESSFULLY      #
#########################################################
BOX MODEL: $box_type
IMAGE: ${distro_value:-Unknown} ${distro_version:-Unknown}"

# Restart Enigma2 or fallback
if [ -f /usr/bin/enigma2 ]; then
    killall -9 enigma2
else
    init 4 && sleep 2 && init 3
fi

exit 0
