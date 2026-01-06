SUMMARY = "EPGImport Plugin"
MAINTAINER = "Lululla"
SECTION = "base"
PRIORITY = "required"
LICENSE = "CLOSED"

inherit gitpkgv allarch

SRCREV = "${AUTOREV}"
PV = "1.0+git${SRCPV}"
PKGV = "1.0+git${GITPKGV}"
PR = "r0"

SRC_URI = "git://github.com/Belfagor2005/EPGImport-99.git;protocol=https;branch=main"

S = "${WORKDIR}/git"

do_install() {
    install -d ${D}${libdir}/enigma2/python/Plugins/Extensions/EPGImport
    cp -r ${S}/usr/lib/enigma2/python/Plugins/Extensions/EPGImport/* \
          ${D}${libdir}/enigma2/python/Plugins/Extensions/EPGImport/
}

FILES:${PN} = "${libdir}/enigma2/python/Plugins/Extensions/EPGImport"