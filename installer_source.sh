#!/bin/bash

## setup source command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/EPGImport-99/main/installer_source.sh -O - | /bin/bash


## Only This 2 lines to edit with new version ######
version='1'
changelog='\n--Update Source xml EPGImport'

##############################################################

TMPSources=/var/volatile/tmp/EPGimport-Sources-main

if [ ! -d /usr/lib64 ]; then
	PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/EPGImport
else
	PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/EPGImport
fi

## check depends packges
if [ -f /var/lib/dpkg/status ]; then
   STATUS=/var/lib/dpkg/status
   OSTYPE=DreamOs
else
   STATUS=/var/lib/opkg/status
   OSTYPE=OE20
fi
echo ""
if python --version 2>&1 | grep -q '^Python 3\.'; then
	echo "You have Python3 image"
	PYTHON=PY3
	Packagesix=python3-six
	Packagerequests=python3-requests
else
	echo "You have Python2 image"
	PYTHON=PY2
	Packagerequests=python-requests
fi


if [ -f /usr/bin/wget ]; then
    echo "wget exist"
else
	if [ $OSTYPE = "DreamOs" ]; then
		echo "dreamos"
		apt-get update && apt-get install wget
	else
		opkg update && opkg install wget
	fi
fi


if [ $PYTHON = "PY3" ]; then
	if grep -qs "Package: $Packagesix" cat $STATUS ; then
		echo ""
	else
		opkg update && opkg --force-reinstall --force-overwrite install python3-six
	fi
fi
echo ""
if grep -qs "Package: $Packagerequests" cat $STATUS ; then
	echo ""
else
	echo "Need to install $Packagerequests"
	echo ""
	if [ $OSTYPE = "DreamOs" ]; then
		apt-get update && apt-get install python-requests -y
	 
	elif [ $PYTHON = "PY3" ]; then
		opkg update && opkg --force-reinstall --force-overwrite install python3-requests
	elif [ $PYTHON = "PY2" ]; then
	  
		opkg update && opkg --force-reinstall --force-overwrite install python-requests
	
	fi
fi
echo ""


set -e
if [ $OSTYPE = "DreamOs" ]; then
   echo "# Your image is OE2.5/2.6 #"
   echo ""
else
   echo "# Your image is OE2.0 #"
   echo ""
fi

sleep 2


## Check if plugin installed correctly
if [ ! -d $PLUGINPATH ]; then
	echo "Some thing wrong .. Plugin not installed"
	exit 1
fi


## Check and update source from doglover3920
# TMPSources=/var/volatile/tmp/EPGimport-Sources-main
mkdir -p $TMPSources
cd $TMPSources
wget --no-check-certificate 'https://github.com/doglover3920/EPGimport-Sources/archive/refs/heads/main.tar.gz'
tar -xzf main.tar.gz
cp -r $TMPSources/EPGimport-Sources-main/* '/usr/lib/enigma2/python/Plugins/Extensions/EPGImport/source/'
set +e
cd
sleep 2


rm -rf $TMPSources > /dev/null 2>&1
sync

# # Identify the box type from the hostname file
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname)
distro_value=$(grep '^distro=' "$FILE" | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)
echo "#########################################################
#               INSTALLED SUCCESSFULLY                  #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################

^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OO SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: $distro_value
IMAGE VERSION: $distro_version"

sleep 5
exit 0