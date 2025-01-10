#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from . import isDreambox
from Components.MenuList import MenuList
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont, getDesktop
# from skin import applySkinFactor, fonts, parameters
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
import os

FHD = False
WQHD = False
if getDesktop(0).size().width() == 1920:
    FHD = True
if getDesktop(0).size().width() == 2560:
    WQHD = True

expandableIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/expandable.png"))
expandedIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/expanded.png"))
selectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/lock_on.png"))
unselectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/lock_off.png"))

"""
# if isDreambox:
    # expandableIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/expandable.png"))
    # expandedIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/expanded.png"))
    # selectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/lock_on.png"))
    # unselectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/lock_off.png"))
# else:
    # # issue
	# # gPixmap: Failed to access '/usr/share/enigma2/icons/expandable.png': No such file or directory
	# # gPixmap: Failed to access '/usr/share/enigma2/icons/expanded.png': No such file or directory
    # expandableIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/expandable.png"))
    # expandedIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/expanded.png"))
    # selectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/lock_on.png"))
    # unselectpng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/lock_off.png"))
"""
    
def loadSettings():
    global cat_desc_loc, entry_desc_loc, cat_icon_loc, entry_icon_loc

    # Parametri per WQHD, FHD e HD
    if WQHD:
        # isCategory
        x, y, w, h = (60, 4, 1200, 60)  # Maggiore spazio per descrizione in WQHD
        cat_desc_loc = (x, y, w, h)  # Icona e testo
        x, y, w, h = (0, 3, 50, 55)  # Icona 50x55 per WQHD
        cat_icon_loc = (x, y, w, h)

        # Centrare l'icona in altezza (verticalmente)
        icon_vertical_offset = (h - 55) // 2
        cat_icon_loc = (x, y + icon_vertical_offset, w, h)

        # isExpanded
        indent = x + w
        x, y, w, h = (35, 4, 1200, 60)  # Maggiore spazio per descrizione espansa
        entry_desc_loc = (x + indent + 30, y, w - indent, h)  # Spazio extra tra icona e testo
        x, y, w, h = (30, 3, 50, 55)  # Icona 50x55 per WQHD
        entry_icon_loc = (x + indent, y, w, h)

    elif FHD:
        # isCategory
        x, y, w, h = (50, 3, 650, 40)
        cat_desc_loc = (x, y, w, h)  # icona e testo
        x, y, w, h = (0, 2, 40, 45)  # Icona 40x45 per FHD
        cat_icon_loc = (x, y, w, h)

        # Centrare l'icona in altezza (verticalmente)
        icon_vertical_offset = (h - 45) // 2
        cat_icon_loc = (x, y + icon_vertical_offset, w, h)
        
        # isEspanded
        indent = x + w
        x, y, w, h = (25, 3, 650, 40)
        entry_desc_loc = (x + indent + 25, y, w - indent, h)  # Aggiunto spazio extra tra icona e testo
        x, y, w, h = (20, 2, 40, 45)  # Icona 40x45 per FHD
        entry_icon_loc = (x + indent, y, w, h)

    else:  # HD (1280x720)
        # isCategory
        x, y, w, h = (30, 3, 500, 30)  # Spazio ridotto per descrizione in HD
        cat_desc_loc = (x, y, w, h)  # Icona e testo
        x, y, w, h = (0, 2, 30, 35)  # Icona 30x35 per HD
        cat_icon_loc = (x, y, w, h)

        # Centrare l'icona in altezza (verticalmente)
        icon_vertical_offset = (h - 35) // 2
        cat_icon_loc = (x, y + icon_vertical_offset, w, h)

        # isExpanded
        indent = x + w
        x, y, w, h = (20, 3, 500, 30)  # Spazio per descrizione espansa
        entry_desc_loc = (x + indent + 35, y, w - indent, h)  # Spazio extra tra icona e testo
        x, y, w, h = (20, 2, 30, 35)  # Icona 30x35 per HD
        entry_icon_loc = (x + indent, y, w, h)

    # Separa icona e descrizione con uno spazio orizzontale
    entry_desc_loc = (entry_desc_loc[0] + 10, entry_desc_loc[1], entry_desc_loc[2], entry_desc_loc[3])

    """
    # x, y, w, h = parameters.get("ExpandableListDescr", applySkinFactor(40, 3, 650, 30))
    # cat_desc_loc = (x, y, w, h)
    # x, y, w, h = parameters.get("ExpandableListIcon", applySkinFactor(0, 2, 30, 25))
    # cat_icon_loc = (x, y, w, h)

    # indent = x + w  # indentation for the selection list entries

    # # selection list (skin parameters also used in enigma2)
    # x, y, w, h = parameters.get("SelectionListDescr", applySkinFactor(25, 3, 650, 30))
    # entry_desc_loc = (x + indent, y, w - indent, h)
    # x, y, w, h = parameters.get("SelectionListLock", applySkinFactor(0, 2, 25, 24))
    # entry_icon_loc = (x + indent, y, w, h)
    """

if isDreambox:
    boxPythonMultiContent = eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND
else:
    boxPythonMultiContent = eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST


def category(description, isExpanded=False):
    global cat_desc_loc, cat_icon_loc
    icon = expandedIcon if isExpanded else expandableIcon
    return [
        (description, isExpanded, []),
        (eListboxPythonMultiContent.TYPE_TEXT,) + cat_desc_loc + (0, RT_HALIGN_LEFT, description),
        (boxPythonMultiContent,) + cat_icon_loc + (icon,)
    ]


def entry(description, value, selected):
    global entry_desc_loc, entry_icon_loc
    res = [
        (description, value, selected),
        (eListboxPythonMultiContent.TYPE_TEXT,) + entry_desc_loc + (0, RT_HALIGN_LEFT, description)
    ]
    if selected:
        # selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))
        res.append((boxPythonMultiContent,) + entry_icon_loc + (selectpng,))
    else:
        # selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_off.png"))
        res.append((boxPythonMultiContent,) + entry_icon_loc + (unselectpng,))
    return res


def expand(cat, value=True):
    # cat is a list of data and icons
    if cat[0][1] != value:
        if WQHD:
            ix, iy, iw, ih = (10, 10, 25, 70)
        elif FHD:
            ix, iy, iw, ih = (10, 5, 25, 50)
        else:
            ix, iy, iw, ih = (10, 2, 25, 25)
        icon = expandedIcon if value else expandableIcon
        t = cat[0]
        cat[0] = (t[0], value, t[2])
        cat[2] = (boxPythonMultiContent,) + cat_icon_loc + (icon,)


def isExpanded(cat):
    return cat[0][1]


def isCategory(item):
    # Return whether list enty is a Category
    return hasattr(item[0][2], 'append')


class ExpandableSelectionList(MenuList):
    def __init__(self, tree=None, enableWrapAround=False):
        'tree is expected to be a list of categories'
        MenuList.__init__(self, [], enableWrapAround, content=eListboxPythonMultiContent)
        # font = fonts.get("SelectionList", applySkinFactor("Regular", 20, 30))
        if WQHD:
            font = ("Regular", 48, 70)  # Altezza riga: 70
        elif FHD:
            font = ("Regular", 32, 50)  # Altezza riga: 50
        else:
            font = ("Regular", 24, 34)  # Altezza riga: 30

        self.l.setFont(0, gFont(font[0], font[1]))
        self.l.setItemHeight(font[2])
        self.tree = tree or []
        self.updateFlatList()

    def updateFlatList(self):
        # Update the view of the items by flattening the tree
        lc = []
        for cat in self.tree:
            lc.append(cat)
            if isExpanded(cat):
                for item in cat[0][2]:
                    lc.append(entry(*item))
        self.setList(lc)

    def toggleSelection(self):
        idx = self.getSelectedIndex()
        item = self.list[idx]
        # Only toggle selections, not expandables...
        if isCategory(item):
            expand(item, not item[0][1])
            self.updateFlatList()
        else:
            # Multiple items may have the same key. Toggle them all,
            # in both the visual list and the hidden items
            i = item[0]
            key = i[1]
            sel = not i[2]
            for idx, e in enumerate(self.list):
                if e[0][1] == key:
                    self.list[idx] = entry(e[0][0], key, sel)
            for cat in self.tree:
                for idx, e in enumerate(cat[0][2]):
                    if e[1] == key and e[2] != sel:
                        cat[0][2][idx] = (e[0], e[1], sel)
            self.setList(self.list)

    def enumSelected(self):
        for cat in self.tree:
            for entry in cat[0][2]:
                if entry[2]:
                    yield entry


loadSettings()
