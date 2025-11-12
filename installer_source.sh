#!/bin/bash
## setup source command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/EPGImport-99/main/installer_source.sh -O - | /bin/bash

version="1"
changelog="\n--Update Source xml EPGImport"

TMPSources=/tmp/EPGimport-Sources-install

echo "Starting EPGImport Sources installation..."

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/EPGImport
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/EPGImport
fi

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    [ -d "$TMPSources" ] && rm -rf "$TMPSources"
}

# Detect OS type
detect_os() {
    if [ -f /var/lib/dpkg/status ]; then
        OSTYPE="DreamOs"
        STATUS="/var/lib/dpkg/status"
    elif [ -f /etc/opkg/opkg.conf ] || [ -f /var/lib/opkg/status ]; then
        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"
    else
        OSTYPE="Unknown"
        STATUS=""
    fi
    echo "🔍 Detected OS type: $OSTYPE"
}

detect_os

# Cleanup before starting
cleanup

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "📥 Installing wget..."
    case "$OSTYPE" in
        "DreamOs")
            apt-get update && apt-get install -y wget || { echo "❌ Failed to install wget"; exit 1; }
            ;;
        "OE")
            opkg update && opkg install wget || { echo "❌ Failed to install wget"; exit 1; }
            ;;
        *)
            echo "❌ Unsupported OS type. Cannot install wget."
            exit 1
            ;;
    esac
fi

# Check if EPGImport plugin is installed
if [ ! -d "$PLUGINPATH" ]; then
    echo "❌ EPGImport plugin not found at $PLUGINPATH"
    echo "⚠️ Please install EPGImport plugin first"
    exit 1
fi

# Download and install EPG sources
echo "⬇️ Downloading EPG sources..."
mkdir -p "$TMPSources"
mkdir -p '/etc/epgimport'

wget --no-check-certificate 'https://github.com/Belfagor2005/EPGimport-Sources/archive/refs/heads/main.tar.gz' -O "$TMPSources/main.tar.gz"
if [ $? -ne 0 ]; then
    echo "❌ Failed to download EPG sources!"
    cleanup
    exit 1
fi

echo "📦 Extracting sources..."
tar -xzf "$TMPSources/main.tar.gz" -C "$TMPSources"
if [ $? -ne 0 ]; then
    echo "❌ Failed to extract EPG sources!"
    cleanup
    exit 1
fi

# Remove .bb files (bitbake files)
echo "🧹 Cleaning up unnecessary files..."
find "$TMPSources/EPGimport-Sources-main" -type f -name "*.bb" -delete

# Install sources
echo "🔧 Installing EPG sources..."
if [ -d "$TMPSources/EPGimport-Sources-main" ]; then
    cp -r "$TMPSources/EPGimport-Sources-main"/* '/etc/epgimport/' 2>/dev/null
    echo "✅ EPG sources installed to /etc/epgimport/"
else
    echo "❌ Sources directory not found after extraction!"
    cleanup
    exit 1
fi

sync

# Verify installation
echo "🔍 Verifying installation..."
if [ -d "/etc/epgimport" ] && [ -n "$(ls -A "/etc/epgimport" 2>/dev/null)" ]; then
    echo "✅ EPG sources directory found and not empty: /etc/epgimport"
    echo "📁 Installed sources:"
    ls -la "/etc/epgimport/" | head -10
    echo ""
    echo "Total files installed: $(find "/etc/epgimport" -type f | wc -l)"
else
    echo "❌ EPG sources installation failed - directory is empty!"
    cleanup
    exit 1
fi

# Cleanup
cleanup
sync

# System info
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

cat <<EOF

#########################################################
#          EPGImport Sources $version INSTALLED         #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################
^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OS SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
EOF

echo ""
echo "✅ EPGImport sources installation completed successfully!"
exit 0