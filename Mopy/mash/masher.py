# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
#
# Wrye Mash, Polemos fork Copyright (C) 2017-2021 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher
#
#  Copyright on the original code 2005-2009 Wrye
#  Copyright on any non trivial modifications or substantial additions 2009-2011 Melchor
#  Copyright on any non trivial modifications or substantial additions 2011-2016 Yacoby
#  Copyright on any non trivial modifications or substantial additions 2017-2020 Polemos
#
# ======================================================================================

# Original Wrye Mash License and Copyright Notice ======================================
#
#  Wrye Mash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bolt is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Mash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Mash copyright (C) 2005, 2006, 2007, 2008, 2009 Wrye
#
# ========================================================================================


# Imports
from io import BytesIO as BytesIO
from datetime import datetime
import io, os, re, shutil, stat, string, sys, time, warnings, ntpath
from datetime import date
from subprocess import PIPE, check_call  # Polemos: KEEP "check_call" !!!
from threading import Thread
from types import *
import wx, wx.html
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from . import appinfo, balt, bolt, conf, gui, mosh, mprofile
from .gui import dialog as guidialog, interface
from .plugins.tes3cmd import gui as tes3cmdgui
from . import nash  # Polemos: Nexus compatibility import.
from . import singletons
from .balt import colors, Image, Links, Link, SeparatorLink, MenuLink
from .balt import tooltip, fill, staticText, leftSash, hSizer, vSizer
from .bolt import LString, GPath, SubProgress
from .gui.credits import Current_Version
from .gui.settings import SettingsWindow
from .gui.utils import UtilsPanel as UtilsPanel, UtilsList as UtilsList
from .gui.wizard import WizardDialog
from .plugins import tes3cmd
from .unimash import _
from .merrors import StateError as StateError, UncodedError as UncodedError
from .mosh import formatInteger, formatDate, ResetTempDir
from subprocess import Popen
from .unimash import n_path, uniChk, fChk, uniformatDate
from .merrors import MashError as MashError
from wx import adv as wxadv

# Constants
DETACHED_PROCESS = 0x00000008  # Polemos: No console window.
warnings.filterwarnings('ignore')  # Polemos: Filter unneeded warnings.
# Polemos: Constants for wxPython
DPOS = wx.DefaultPosition
DSIZE = wx.DefaultSize
ADRW = wx.BU_AUTODRAW
NBIT = wx.NullBitmap

# --Internet Explorer
try:
    import wx.lib.iewin  # Polemos: Todo: Need to replace this. => [iewin]
except:
    pass


def openmw_enabled():  # Polemos
    """Check if openmw.dat exists and return True if it does."""
    return os.path.exists(os.path.join(singletons.MashDir, 'openmw.dat'))


# Gui Ids
class IdListIterator(object):
    """Iterator for IdList object."""

    def __init__(self, idList):
        """Initialize."""
        self.idList = idList
        self.prevId = idList.baseId - 1
        self.lastId = idList.baseId + idList.size - 1

    def __iter__(self):
        """Iterator method."""
        return self

    def __next__(self):
        """Iterator method."""
        if self.prevId >= self.lastId:
            raise StopIteration
        self.prevId += 1
        return self.prevId

    # Monkey patching
    next = __next__


class IdList(object):
    """List of ids."""

    def __init__(self, baseId, size, *extras):
        self.BASE = baseId
        self.MAX = baseId + size - 1
        self.baseId = baseId
        self.size = size
        # --Extra
        nextId = baseId + size
        for extra in extras:
            setattr(self, extra, nextId)
            nextId += 1

    def __iter__(self):
        """Return iterator."""
        return IdListIterator(self)


# ID Constants

# --Generic
ID_RENAME = 6000
ID_SET = 6001
ID_SELECT = 6002
ID_BROWSER = 6003
ID_NOTES = 6004
ID_EDIT = 6005
ID_BACK = 6006
ID_NEXT = 6007

# --File Menu
ID_REVERT_BACKUP = 6100
ID_REVERT_FIRST = 6101
ID_BACKUP_NOW = 6102

# --Label Menus
ID_LOADERS = IdList(10000, 90, 'SAVE', 'EDIT', 'ALL', 'NONE')
ID_REMOVERS = IdList(10100, 90, 'EDIT', 'EDIT_CELLS')
ID_REPLACERS = IdList(10200, 90, 'EDIT')
ID_GROUPS = IdList(10300, 90, 'EDIT', 'NONE')
ID_RATINGS = IdList(10400, 90, 'EDIT', 'NONE')
ID_PROFILES = IdList(10500, 90, 'EDIT')
ID_CUSTOMS = IdList(10600, 90, 'RUN')  # Polemos


class check_version(object):  # Polemos
    """CyberChecking Mash..."""

    def __init__(self, mode='auto'):
        self.mode = mode
        self.wryemode = conf.settings['openmw']
        self.beta = True if u'beta' in conf.settings['mash.version'][1] else False
        if mode == 'auto':
            if not conf.settings['asked.check']:
                self.askcheck()
                return
            if conf.settings['last.check'] is None: conf.settings['last.check'] = date.today()
            if not conf.settings['enable.check']: return
            if not self.checkdate(): return
        self.notify(self.checknetver())

    def askcheck(self):
        result = guidialog.askdialog(None,
                                      _('Would you like Wrye Mash to notify you whenever a new version is released?'
                                        u'\n\nClick Yes to enable checking every 15 days (recommended).\nIf you click No you can always enable it later'
                                        u' in the settings (and also change how often it checks).'),
                                      _('Wrye Mash Updates?'))
        conf.settings['asked.check'] = True
        if result == wx.ID_YES:  # If YES:
            conf.settings['enable.check'] = True
            conf.settings['timeframe.check'] = 15
            conf.settings['last.check'] = date.today()
        elif result == wx.ID_NO:
            conf.settings['enable.check'] = False  # If NO.

    def checkdate(self):
        today = date.today()
        last_check = conf.settings['last.check']
        if (today - last_check).days >= conf.settings['timeframe.check']:
            return True
        else:
            return False

    def checknetver(self):
        conf.settings['last.check'] = date.today()
        self.newver = nash.WryeWeb.get_mash_ver(nash.WryeWeb(self.wryemode))
        if self.newver is None or self.newver == '' or self.newver == 'error':
            return 'error'
        elif conf.settings['mash.version'][0] <= self.newver and self.beta:
            return True
        elif conf.settings['mash.version'][0] == self.newver:
            return False
        elif conf.settings['mash.version'][0] < self.newver:
            return True

    def notify(self, status):
        if status == 'error':  # On error
            guidialog.ErrorMessage(None, _('An error occurred while trying to check for available updates.'
                                            u'\n\nPlease try again later or visit Wrye Mash home page on Nexus.'),
                                    title=_('Update error'))

        elif status:  # On available update
            result = guidialog.askdialog(None, _('Wrye Mash v%s has been released.\n\nWould you like to download it?'
                                                  u' (Will open your internet browser).' % (self.newver)),
                                          _('Wrye Mash %s released.' % (self.newver)))

            conf.settings['last.check'] = date.today()
            if result == wx.ID_YES:  # If YES:
                if sys.platform == 'win32':  # Windows compatibility (Thinking about Linux).
                    wx.LaunchDefaultBrowser(nash.wrye_download_site('download', self.wryemode))

        elif not status:  # If no update
            conf.settings['last.check'] = date.today()
            if self.mode == 'manual':
                guidialog.InfoMessage(None, _('You seem to have the latest version.\n\n'
                                               u'(Note: This may be wrong if there were significant changes in Morrowind Nexus website).'))


def setmlox():  # Polemos
    """Set/check mlox location and existence."""
    if not conf.settings['openmw']:  # Regular Morrowind
        mlox_Path = conf.settings["mloxpath"]
        mlox_The_Pill = 'mlox.exe'

    if conf.settings['openmw']:  # OpenMW/TES3mp
        mlox_Path = conf.settings["mlox64path"]
        mlox_The_Pill = 'mlox64.exe'

    def mloxOracle(path):
        """Test if mlox exists."""
        try:
            return True if os.path.isfile(path) else False
        except:
            return False

    def detectMlox_dir():
        """Try to detect mlox dir."""
        from .plugins.mlox.loader import Mlox_The_Path

        Agents = [x for x in [conf.settings['sInstallersDir'],
                              conf.settings['datamods'],
                              conf.settings['downloads'],
                              mosh.dirs['mods'].s,
                              singletons.MashDir] if x is not None]
        Trinity = conf.settings['mwDir']

        if not conf.settings['openmw']:  # Regular Morrowind
            try:
                mlox_Neo = Mlox_The_Path(mlox_The_Pill, Agents, Trinity)
                if mloxOracle(mlox_Neo):
                    conf.settings["mloxpath"] = mlox_Neo
                else:
                    conf.settings["mloxpath"] = ''
            except:
                conf.settings["mloxpath"] = ''

        elif conf.settings['openmw']:  # OpenMW/TES3mp
            try:
                mlox_Neo = Mlox_The_Path(mlox_The_Pill, Agents, Trinity)
                if mloxOracle(mlox_Neo):
                    conf.settings["mlox64path"] = mlox_Neo
                else:
                    conf.settings["mlox64path"] = ''
            except:
                conf.settings["mlox64path"] = ''

    if mloxOracle(mlox_Path):
        return
    else:
        detectMlox_dir()


def Remove(file):  # Polemos
    """Really try removing a file."""
    try:
        os.remove(file)
    except:
        try:
            os.chmod(file, stat.S_IWRITE)  # Part pythonic,
        except:
            check_call('attrib -R %s /S' % (file))  # part hackish.
        try:
            os.remove(file)
        except:
            return False
    return True


# Message Dialogs -------------------------------------------------------------

class Checkboxes(balt.ImageList):
    """Checkboxes ImageList. Used by several List classes."""

    def __init__(self):
        imgPath = 'images'
        balt.ImageList.__init__(self, 16, 16)
        for status in ('on', 'off'):
            for color in ('purple', 'blue', 'green', 'orange', 'yellow', 'red', 'white'):
                shortKey = '%s.%s' % (color, status)
                imageKey = 'checkbox.%s' % shortKey
                file = os.path.join(imgPath, r'checkbox_%s_%s.png' % (color, status))
                image = singletons.images[imageKey] = Image(file, wx.BITMAP_TYPE_PNG)
                self.Add(image, shortKey)

    def Get(self, status, on):
        self.GetImageList()
        if on:
            if status <= -20:
                shortKey = 'purple.on'
            elif status <= -10:
                shortKey = 'blue.on'
            elif status <= 0:
                shortKey = 'green.on'
            elif status <= 10:
                shortKey = 'yellow.on'
            elif status <= 20:
                shortKey = 'orange.on'
            else:
                shortKey = 'red.on'
        else:
            if status <= -20:
                shortKey = 'purple.off'
            elif status <= -10:
                shortKey = 'blue.off'
            elif status == 0:
                shortKey = 'green.off'
            elif status <= 10:
                shortKey = 'yellow.off'
            elif status <= 20:
                shortKey = 'orange.off'
            else:
                shortKey = 'red.off'
        return self.indices[shortKey]

    def Getsimple(self, on):
        if on:
            shortKey = 'white.on'
        else:
            shortKey = 'white.off'
        return self.indices[shortKey]


# Icons------------------------------------------------------------------------
installercons = balt.ImageList(16, 16)
imgPath = 'images'
installercons.data.extend({
                              # --Off/Archive
                              'off.green': Image(os.path.join(imgPath, r'checkbox_green_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.grey': Image(os.path.join(imgPath, r'checkbox_grey_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.red': Image(os.path.join(imgPath, r'checkbox_red_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.white': Image(os.path.join(imgPath, r'checkbox_white_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.orange': Image(os.path.join(imgPath, r'checkbox_orange_off.png'),
                                                  wx.BITMAP_TYPE_PNG),
                              'off.yellow': Image(os.path.join(imgPath, r'checkbox_yellow_off.png'),
                                                  wx.BITMAP_TYPE_PNG),
                              # --On/Archive
                              'on.green': Image(os.path.join(imgPath, r'checkbox_green_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.grey': Image(os.path.join(imgPath, r'checkbox_grey_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.red': Image(os.path.join(imgPath, r'checkbox_red_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.white': Image(os.path.join(imgPath, r'checkbox_white_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.orange': Image(os.path.join(imgPath, r'checkbox_orange_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.yellow': Image(os.path.join(imgPath, r'checkbox_yellow_inc.png'), wx.BITMAP_TYPE_PNG),
                              # --Off/Directory
                              'off.green.dir': Image(os.path.join(imgPath, r'diamond_green_off.png'),
                                                     wx.BITMAP_TYPE_PNG),
                              'off.grey.dir': Image(os.path.join(imgPath, r'diamond_grey_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.red.dir': Image(os.path.join(imgPath, r'diamond_red_off.png'), wx.BITMAP_TYPE_PNG),
                              'off.white.dir': Image(os.path.join(imgPath, r'diamond_white_off.png'),
                                                     wx.BITMAP_TYPE_PNG),
                              'off.orange.dir': Image(os.path.join(imgPath, r'diamond_orange_off.png'),
                                                      wx.BITMAP_TYPE_PNG),
                              'off.yellow.dir': Image(os.path.join(imgPath, r'diamond_yellow_off.png'),
                                                      wx.BITMAP_TYPE_PNG),
                              # --On/Directory
                              'on.green.dir': Image(os.path.join(imgPath, r'diamond_green_inc.png'),
                                                    wx.BITMAP_TYPE_PNG),
                              'on.grey.dir': Image(os.path.join(imgPath, r'diamond_grey_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.red.dir': Image(os.path.join(imgPath, r'diamond_red_inc.png'), wx.BITMAP_TYPE_PNG),
                              'on.white.dir': Image(os.path.join(imgPath, r'diamond_white_inc.png'),
                                                    wx.BITMAP_TYPE_PNG),
                              'on.orange.dir': Image(os.path.join(imgPath, r'diamond_orange_inc.png'),
                                                     wx.BITMAP_TYPE_PNG),
                              'on.yellow.dir': Image(os.path.join(imgPath, r'diamond_yellow_inc.png'),
                                                     wx.BITMAP_TYPE_PNG),
                              # --Broken
                              'corrupt': Image(os.path.join(imgPath, r'red_x.png'), wx.BITMAP_TYPE_PNG),
                          }.items())


# Windows ---------------------------------------------------------------------

class SashTankPanel(gui.NotebookPanel):
    """Subclass of a notebook panel designed for a two pane tank panel."""

    def __init__(self, data, parent):
        """Initialize."""
        wx.Panel.__init__(self, parent, -1)
        self.data = data
        self.detailsItem = None
        sashPos = data.getParam('sashPos', 370)
        self.left = leftSash(self, defaultSize=(sashPos, 100), onSashDrag=self.OnSashDrag)
        self.right = wx.Panel(self, style=wx.NO_BORDER)
        # --Events
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnShow(self):
        """Panel is shown. Update self.data."""
        if self.gList.data.refresh(): self.gList.RefreshUI()
        self.SetStatusCount()

    def OnSashDrag(self, event):
        """Handle sash moved."""
        wMin, wMax = 80, self.GetSizeTuple()[0] - 80
        sashPos = max(wMin, min(wMax, event.GetDragRect().width))
        self.left.SetDefaultSize((sashPos, 10))
        wxadv.LayoutAlgorithm().LayoutWindow(self, self.right)
        self.data.setParam('sashPos', sashPos)

    def OnSize(self, event=None):
        wxadv.LayoutAlgorithm().LayoutWindow(self, self.right)

    def OnCloseWindow(self):
        """To be called when containing frame is closing. Use for saving data, scrollpos, etc."""
        self.SaveDetails()
        self.data.save()

    def GetDetailsItem(self):
        """Returns item currently being shown in details view."""
        return self.detailsItem


# ------------------------------------------------------------------------------

class ListEditorData(object):
    """Data capsule for ListEditorDialog. [Abstract]"""

    def __init__(self, parent):
        """Initialize."""
        self.parent = parent  # --Parent window.
        self.showAdd = False
        self.showEdit = False
        self.showRename = False
        self.showRemove = False

    def getItemList(self):
        """Returns item list in correct order."""
        raise mosh.AbstractError
        return []

    def add(self):
        """Peforms add operation. Return new item on success."""
        raise mosh.AbstractError
        return None

    def edit(self, item=None):
        """Edits specified item. Return true on success."""
        raise mosh.AbstractError
        return False

    def rename(self, oldItem, newItem):
        """Renames oldItem to newItem. Return true on success."""
        raise mosh.AbstractError
        return False

    def remove(self, item):
        """Removes item. Return true on success."""
        raise mosh.AbstractError
        return False

    # --Checklist
    def getChecks(self):
        """Returns checked state of items as array of True/False values matching Item list."""
        raise mosh.AbstractError
        return []

    def check(self, item):
        """Checks items. Return true on success."""
        raise mosh.AbstractError
        return False

    def uncheck(self, item):
        """Unchecks item. Return true on success."""
        raise mosh.AbstractError
        return False


# ------------------------------------------------------------------------------

class ListEditorDialog(wx.Dialog):
    """Dialog for editing lists."""

    def __init__(self, parent, id, title, data, type='list'):
        # --Data
        self.data = data  # --Should be subclass of ListEditorData
        self.items = data.getItemList()
        # --GUI
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        wx.EVT_CLOSE(self, self.OnCloseWindow)
        # --List Box
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if type == 'checklist':
            self.list = wx.CheckListBox(self, -1, choices=self.items, style=wx.LB_SINGLE)
            for index, checked in enumerate(self.data.getChecks()): self.list.Check(index, checked)
            self.Bind(wx.EVT_CHECKLISTBOX, self.DoCheck, self.list)
        else:
            self.list = wx.ListBox(self, -1, choices=self.items, style=wx.LB_SINGLE)
        self.list.SetSizeHints(125, 150)
        sizer.Add(self.list, 1, wx.EXPAND | wx.TOP, 4)
        # --Buttons and Events
        if data.showAdd or data.showEdit or data.showRename or data.showRemove:
            sizer_v1 = wx.BoxSizer(wx.VERTICAL)
            if data.showAdd:
                sizer_v1.Add(wx.Button(self, wx.ID_NEW, _('Add')), 0, wx.LEFT | wx.TOP, 4)
                wx.EVT_BUTTON(self, wx.ID_NEW, self.DoAdd)
            if data.showEdit:
                sizer_v1.Add(wx.Button(self, wx.ID_REPLACE, _('Edit')), 0, wx.LEFT | wx.TOP, 4)
                wx.EVT_BUTTON(self, wx.ID_REPLACE, self.DoEdit)
            if data.showRename:
                sizer_v1.Add(wx.Button(self, ID_RENAME, _('Rename')), 0, wx.LEFT | wx.TOP, 4)
                wx.EVT_BUTTON(self, ID_RENAME, self.DoRename)
            if data.showRemove:
                sizer_v1.Add(wx.Button(self, wx.ID_DELETE, _('Remove')), 0, wx.LEFT | wx.TOP, 4)
                wx.EVT_BUTTON(self, wx.ID_DELETE, self.DoRemove)
            sizer.Add(sizer_v1, 0, wx.EXPAND)
        # --Done
        if data.__class__ in conf.settings['mash.window.sizes']:
            self.SetSizer(sizer)
            self.SetSize(conf.settings['mash.window.sizes'][data.__class__])
        else:
            self.SetSizerAndFit(sizer)

    def GetSelected(self):
        return self.list.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)

    def DoCheck(self, event):  # --Checklist commands
        """Handles check/uncheck of listbox item."""
        index = event.GetSelection()
        item = self.items[index]
        if self.list.IsChecked(index):
            self.data.check(item)
        else:
            self.data.uncheck(item)

    def DoAdd(self, event):  # --List Commands
        """Adds a new item."""
        newItem = self.data.add()
        if newItem and newItem not in self.items:
            self.items = self.data.getItemList()
            index = self.items.index(newItem)
            self.list.InsertItems([newItem], index)

    def DoEdit(self, event):
        """Edits the selected item."""
        raise mosh.UncodedError

    def DoRename(self, event):
        """Renames selected item."""
        selections = self.list.GetSelections()
        if not selections:
            wx.Bell()
            return
        # --Rename it
        itemDex = selections[0]
        curName = self.list.GetString(itemDex)
        # --Dialog
        dialog = wx.TextEntryDialog(self, _('Rename to:'), _('Rename'), curName)
        result = dialog.ShowModal()
        # --Okay?
        if result != wx.ID_OK:
            dialog.Destroy()
            return
        newName = dialog.GetValue()
        dialog.Destroy()
        if newName == curName:
            pass
        elif newName in self.items:
            guidialog.ErrorMessage(self, _('Name must be unique.'))
        elif self.data.rename(curName, newName):
            self.items[itemDex] = newName
            self.list.SetString(itemDex, newName)

    def DoRemove(self, event):
        """Removes selected item."""
        selections = self.list.GetSelections()
        if not selections:
            wx.Bell()
            return
        # --Data
        itemDex = selections[0]
        item = self.items[itemDex]
        if not self.data.remove(item): return
        # --GUI
        del self.items[itemDex]
        self.list.Delete(itemDex)

    def OnCloseWindow(self, event):  # --Window Closing
        """Handle window close event. Remember window size, position, etc."""
        sizes = conf.settings.getChanged('mash.window.sizes')
        sizes[self.data.__class__] = self.GetSizeTuple()
        self.Destroy()


# ------------------------------------------------------------------------------

class BSArchivesList(gui.List, gui.ListDragDropMixin):  # Polemos
    """BSA Archives."""
    # --Class Data
    mainMenu = []  # --Column menu
    itemMenu = []  # --Single item menu
    last_itm = []  # Alphabetical search by key press

    def __init__(self, parent):
        """Init."""
        self.openmw = conf.settings['openmw']
        # --Columns
        self.cols = conf.settings['mash.Archives.cols']
        self.colAligns = conf.settings['mash.Archives.colAligns']
        self.colNames = conf.settings['mash.colNames']
        self.colReverse = conf.settings.getChanged('mash.Archives.colReverse')
        self.colWidths = conf.settings['mash.Archives.colWidths']
        # --Data/Items
        singletons.ArchivesList = self
        self.data = data = mosh.BSAdata()
        self.bsafiles = mosh.mwIniFile
        self.active_bsa = 0
        self.sort = conf.settings['mash.Archives.sort']
        # --Links
        self.mainMenu = BSArchivesList.mainMenu
        self.itemMenu = BSArchivesList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT))
        gui.ListDragDropMixin.__init__(self, self.list)
        # --Image List
        checkboxesIL = singletons.images['mash.checkboxes'].GetImageList()
        self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)
        # --Events
        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def Refresh(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified files."""
        self.data.refresh()
        self.chk_data()
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files: self.PopulateItem(file, selected=selected)
        self.set_status()

    def chk_data(self):
        """Remove non existent files."""
        for x in self.data.keys():
            if not os.path.isfile(self.data[x][1]):
                del self.data[x]

    def set_status(self):  # Polemos fix for Mods tab.
        """GUI toolbar status."""
        if not self.openmw:  # Polemos: Regular Morrowind support
            text = _(' Mods: %d/%d | BSAs: %d/%d') % (
                len(mosh.mwIniFile.loadFiles), len(mosh.modInfos.data), self.active_bsa, len(self.items))
        if self.openmw:  # Polemos: OpenMW/TES3mp support
            text = _(' Plugins: %d/%d | BSAs: %d/%d') % (
                len(mosh.mwIniFile.loadFiles), len(mosh.modInfos.data), self.active_bsa, len(self.items))
        singletons.statusBar.SetStatusField(text, 2)

    def bsa_active_count(self):
        """Active bsa enumeration."""
        active = [True for x in range(len(self.data)) if self.data[self.items[x]][2]]
        self.active_bsa = len(active)

    def numBsa(self):
        """Bsa order counter."""
        bsas = [self.data[x] for x in self.items]
        bsas.sort(key=lambda a: a[4])
        return {bsa: str(num + 1) for num, bsa in enumerate([x[0] for x in bsas])}

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        fileName = self.items[itemDex]
        fileInfo = self.data[fileName]
        numBsa = self.numBsa()
        self.bsa_active_count()
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            if col == 'Archive':
                value = fileName
            elif col == '#':
                value = numBsa[fileName]
            elif col == 'Size':
                value = '%sMB' % formatInteger(fileInfo[3] // 1024)
            else:
                value = ''
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --Image
        on = fileInfo[2]
        self.list.SetItemImage(itemDex, self.checkboxes.Getsimple(on))
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):
        """Sort Items"""
        (col, reverse) = self.GetSortSettings(col, reverse)
        conf.settings['mash.Archives.sort'] = col
        self.items.sort(key=lambda a: self.data[a][4])  # Default sort by '#'
        if col == 'Archive':
            self.items.sort(key=str.casefold)
        elif col == '#':
            self.items.sort(key=lambda a: self.data[a][4])
        elif col == 'Size':
            self.items.sort(key=lambda a: self.data[a][3])
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()

    def ToggleBSAactivation(self, archives):
        """Toggle BSA load/unload state."""
        enabled = []
        disabled = []
        if isinstance(archives, str):
            archives = [archives]
        [disabled.append(x) if self.data[x][2] else enabled.append(x) for x in archives]
        if disabled: self.bsafiles.unload(disabled, action='Archives')
        if enabled: self.bsafiles.load(enabled, action='Archives')
        self.Refresh()

    def OnDoubleClick(self, event):
        """Handle double click event."""
        (hitItem, hitFlag) = self.list.HitTest(event.GetPosition())
        if hitItem < 0: return
        fileInfo = self.data[self.items[hitItem]][0]
        self.ToggleBSAactivation(fileInfo)

    def OnColumnResize(self, event):
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.Archives.colWidths')

    def OnLeftDown(self, event):
        """Event: Left Down"""
        (hitItem, hitFlag) = self.list.HitTest((event.GetX(), event.GetY()))
        if hitFlag == 32:
            fileName = self.items[hitItem]
            self.ToggleBSAactivation(fileName)
            self.Refresh()
        event.Skip()  # --Pass Event onward

    def OnKeyDown(self, event):
        fmap = {
            wx.WXK_SPACE: self.OnSpacePress,
            wx.WXK_UP: self.OnUpPress,
            wx.WXK_DOWN: self.OnDownPress,
            65: self.OnAPress,
        }
        kc = event.GetKeyCode()
        if kc in fmap:
            fmap[kc](event)
        else:
            self.OnGenKeys(chr(event.GetKeyCode()))  # Polemos: Alpha, Beta, search...

    def OnGenKeys(self, letter):  # Polemos
        """Selects unicode items by their first letter."""
        while True:
            for x in self.data.keys():
                if self.data[x][0].startswith(letter) or self.data[x][0].startswith(letter.lower()):
                    if self.data[x][0] not in self.last_itm:
                        self.ClearSelected()
                        self.SelectItems(self.data[x][0])
                        self.SetItemFocus(self.data[x][0])
                        self.last_itm.append(self.data[x][0])
                        return
            try:
                del self.last_itm[0]
            except:
                return

    def OnAPress(self, event):
        if event.ControlDown():
            self.SelectAll()
        else:
            self.OnGenKeys('A')

    def OnUpPress(self, event):
        event.Skip()
        self.moveSelected(event, (-1))

    def OnDownPress(self, event):
        event.Skip()
        self.moveSelected(event, (+1))

    def OnSpacePress(self, event):
        self.ToggleBSAactivation(self.GetSelected())
        self.Refresh()

    def chkSort(self):
        """Check column sorting."""
        if conf.settings['mash.Archives.sort'] != '#':
            guidialog.ErrorMessage(self.GetParent(), _('The Archives '
                                                        u'list must be sorted by "Load Order (#)" to\n enable Keyboard or Mouse based sorting.'))
            return False
        return True

    def OnDrop(self, names, toIdx):
        """Support for dragging and dropping list items."""
        if not self.chkSort(): return
        items = self.items[:]
        if len(items) <= 1: return
        # Change item(s) pos in list
        items = [None if x in names else x for x in items]
        items[toIdx:toIdx] = names
        items = [x for x in items if x is not None]
        self.set_chronos(items)

    def moveSelected(self, event, moveMod):
        """Moves selected files up or down (depending on moveMod)."""
        if not event.ControlDown(): return
        if not self.chkSort(): return
        selected = self.GetSelected()
        if not selected: return
        self.moveSelectedFilter(selected, moveMod)

    def moveSelectedFilter(self, origSel, moveMod):
        """Move selected items."""
        selected = [x for x in origSel]
        selected.sort(key=lambda x: self.data[x][4], reverse=(moveMod != -1))
        items = self.GetItems()[:]
        items.sort(key=lambda x: self.data[x][4])
        # Get user order
        for item in selected:
            pos = items.index(item)
            movePos = pos + moveMod
            if movePos < 0 or movePos >= len(items): break
            items[pos], items[movePos] = items[movePos], items[pos]
        self.set_chronos(items)
        self.ClearSelected()
        self.SelectItems(origSel)

    def set_chronos(self, items):  # Polemos
        """Chronos, the father and the son."""
        start_date = 1024695106
        end_date = 1051807050
        mtime = start_date
        step = (end_date - start_date) // len(items)
        for x in items:
            os.utime(self.data[x][1], (time.time(), mtime))
            mtime += step
        self.items = items
        # Polemos: for OpenMW/TES3mp support
        if self.openmw: self.bsafiles.safeSave()
        self.Refresh()


# ------------------------------------------------------------------------------

class ModPackageList(gui.List):  # Polemos
    """Packages mini Tab."""
    mainMenu = []  # Column menu
    itemMenu = []  # Single item menu
    last_itm = []  # Alphabetical search by key press

    def __init__(self, parent):
        """Init."""
        if True:  # Columns
            self.cols = conf.settings['mash.Packages.cols']
            self.colAligns = conf.settings['mash.Packages.colAligns']
            self.colNames = conf.settings['mash.colNames']
            self.colReverse = conf.settings.getChanged('mash.Packages.colReverse')
            self.colWidths = conf.settings['mash.Packages.colWidths']
        if True:  # Data/Items
            self.data = data = mosh.PackagesData()
            self.packagefiles = mosh.mwIniFile
            self.active_package = []
            self.sort = conf.settings['mash.Packages.sort']
        if True:  # Links
            self.mainMenu = ModPackageList.mainMenu
            self.itemMenu = ModPackageList.itemMenu
        if True:  # Parent init
            gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT))
        # --Image List, Polemos, todo: maybe implement... Also check mosh and below.
        # checkboxesIL = singletons.images['mash.checkboxes'].GetImageList()
        # self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)
        if True:  # Events
            self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
            self.list.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def Refresh(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified files."""
        self.data.refresh()
        self.chk_data()
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files:
                self.PopulateItem(file, selected=selected)

    def chk_data(self):
        """Remove non existent files."""
        for x in self.data.keys():
            if not os.path.isfile(self.data[x][1]):
                del self.data[x]

    def installed_packages(self):
        """Check for installed Datamods."""
        active = [True for x in range(len(self.data)) if self.data[self.items[x]][2]]
        self.active_package = len(active)

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        from .mosh import megethos
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        fileName = self.items[itemDex]
        fileInfo = self.data[fileName]
        self.installed_packages()
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            if col == 'Package':
                value = fileName
            elif col == 'Size':
                value = '%s' % megethos(fileInfo[3])
            else:
                value = ''
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --Image, Polemos, todo: maybe implement...
        # installed = fileInfo[2]
        # self.list.SetItemImage(itemDex, self.checkboxes.Getsimple(installed))
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def UnpackPackage(self, package_path):
        """Unpack Package to Downloads folder."""
        # Package data
        package_name_data = bolt.ModNameFactory(package_path).getModName
        if not package_name_data[0]:
            package_name = package_name_data[1]
        else:
            package_name = package_name_data[0]
        tempdir = os.path.join(singletons.MashDir, 'Temp')
        package_tempdir = os.path.join(tempdir, package_name)
        # Reset temp dir
        if not ResetTempDir(self).status: return
        # Get Package info
        package_paths, max_depth, mw_files = bolt.ArchiveInfo(package_path).getPackageData
        package_data = self, package_name, (package_paths, max_depth)
        # Detect mod data files root from Package
        data_files = bolt.DataFilesDetect(package_paths, max_depth, mw_files).getDataFiles()
        # On autodetect failure, call Package Explorer
        if data_files is None:
            explorer = guidialog.ArchiveExplorer(package_data)
            data_files = explorer.GetTreeValue
            if data_files is None: return
        # User input
        dialog = guidialog.ModInstallDialog(self, package_name, data_files, package_data, package_name_data)
        data_files, mod_name = dialog.GetModData
        if data_files is None: return
        # Unpack to tempdir (7zip doesn't allow dir extraction without extracting parent dirs).
        filesLen = bolt.MultiThreadGauge(self, (package_tempdir, package_path, data_files)).getInstallLen
        # Complex package?
        if not filesLen:
            if guidialog.askdialog(self, _('This package\'s structure is too complex to be detected correctly. '
                                            u'Would you like to proceed nevertheless? Click No to abort.\n\nIf you abort, you can retry installing the package and then select the'
                                            u' "Advanced" option to set the package "data files" folder.'),
                                    _('Complex package')) == wx.ID_NO: return
        # Clean some junk
        bolt.CleanJunkTemp()
        # Move to Mods dir
        source_dir = os.path.join(package_tempdir, data_files)
        target_dir = os.path.join(conf.settings['datamods'], mod_name)
        bolt.ModInstall(self, mod_name, conf.settings['datamods'], source_dir, target_dir, filesLen)
        # Mod MetaStamping.
        bolt.MetaStamp(target_dir, package_name_data)
        # Refresh Mash.
        singletons.mashFrame.RefreshData()

    def SortItems(self, col=None, reverse=-2):
        """Sort Items"""
        (col, reverse) = self.GetSortSettings(col, reverse)
        conf.settings['mash.Packages.sort'] = col
        self.items.sort(key=str.casefold)
        if col == 'Package':
            pass  # Default
        elif col == 'Size':
            self.items.sort(key=lambda a: self.data[a][3])
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()

    def OnDoubleClick(self, event):
        """Handle double click event."""
        (hitItem, hitFlag) = self.list.HitTest(event.GetPosition())
        if hitItem < 0: return
        self.UnpackPackage(self.data[self.items[hitItem]][1])

    def OnColumnResize(self, event):
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.Packages.colWidths')

    def OnLeftDown(self, event):
        """Event: Left Down"""
        (hitItem, hitFlag) = self.list.HitTest((event.GetX(), event.GetY()))
        if hitFlag == 32:
            fileName = self.items[hitItem]
            # self.ToggleModActivation(fileName)
            self.Refresh()
        event.Skip()  # --Pass Event onward

    def OnKeyDown(self, event):
        fmap = {
            wx.WXK_SPACE: self.OnSpacePress,
            65: self.OnAPress,
        }
        kc = event.GetKeyCode()
        if kc in fmap:
            fmap[kc](event)
        else:
            self.OnGenKeys(chr(event.GetKeyCode()))  # Polemos: Alpha, Beta, search...

    def OnGenKeys(self, letter):  # Polemos
        """Selects unicode items by their first letter."""
        while True:
            for x in self.data.keys():
                if self.data[x][0].startswith(letter) or self.data[x][0].startswith(letter.lower()):
                    if self.data[x][0] not in self.last_itm:
                        self.ClearSelected()
                        self.SelectItems(self.data[x][0])
                        self.SetItemFocus(self.data[x][0])
                        self.last_itm.append(self.data[x][0])
                        return
            try:
                del self.last_itm[0]
            except:
                return

    def OnAPress(self, event):
        if event.ControlDown():
            self.SelectAll()
        else:
            self.OnGenKeys('A')

    def OnSpacePress(self, event):
        # self.ToggleModActivation(self.GetSelected())
        self.Refresh()


# ------------------------------------------------------------------------------

class MasterList(gui.List):
    mainMenu = []
    itemMenu = []

    def __init__(self, parent, fileInfo):
        self.parent = parent
        self.OpenMW = conf.settings['openmw']
        # --Columns
        self.cols = conf.settings['mash.masters.cols']
        self.colNames = conf.settings['mash.colNames']
        self.colWidths = conf.settings['mash.masters.colWidths']
        self.colAligns = conf.settings['mash.masters.colAligns']
        self.colReverse = conf.settings['mash.masters.colReverse'].copy()
        self.sort = conf.settings['mash.masters.sort']
        # --Data/Items
        self.edited = False
        self.fileInfo = fileInfo
        self.fileIsMod = True
        self.prevId = -1
        self.colswitch = -1
        self.data = {}
        self.items = []  # --These are id numbers
        self.oldMasters = []
        self.newMasters = []
        self.allMasters = []  # --Used for sorting
        self.esmsFirst = conf.settings['mash.masters.esmsFirst']  # ???
        self.selectedFirst = conf.settings['mash.masters.selectedFirst']  # ???
        # --Links
        self.mainMenu = MasterList.mainMenu
        self.itemMenu = MasterList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_EDIT_LABELS))
        # Events
        wx.EVT_LIST_END_LABEL_EDIT(self, self.listId, self.OnLabelEdited)
        self.list.Bind(wx.EVT_LIST_COL_CLICK, self.DoSort)
        # --Image List
        checkboxesIL = self.checkboxes.GetImageList()
        self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)

    def DoSort(self, event):  # Polemos
        """Enable column sorting for masters."""
        self.PopulateItems(self.cols[event.GetColumn()], self.colswitch)

    def OnLabelEdited(self, event):
        """Label Edited"""
        itemDex = event.Index
        newName = event.GetText()
        # --No change?
        if newName in mosh.modInfos:
            masterInfo = self.data[self.items[itemDex]]
            oldName = masterInfo.name
            masterInfo.setName(newName)
            if newName not in self.newMasters: self.newMasters.append(newName)
            if (oldName in self.newMasters) and (not self.getMasterInfos(oldName)): self.newMasters.remove(oldName)
            if newName not in self.allMasters: self.allMasters.append(newName)
            self.ReList()
            self.PopulateItem(itemDex)
            conf.settings.getChanged('mash.mods.renames')[masterInfo.oldName] = newName
        elif newName == '':
            event.Veto()
        else:
            guidialog.ErrorMessage(self, _('File "%s" does not exist.') % (newName,))
            event.Veto()

    def newId(self):
        """NewItemNum"""
        self.prevId += 1
        return self.prevId

    def SetFileInfo(self, fileInfo):
        """Set ModInfo"""
        self.ClearSelected()
        self.edited = False
        self.fileInfo = fileInfo
        self.fileIsMod = fileInfo and fileInfo.isMod()
        self.prevId = -1
        self.data.clear()
        del self.items[:]
        del self.oldMasters[:]
        del self.newMasters[:]
        del self.allMasters[:]
        # --Null fileInfo?
        if not fileInfo:
            self.PopulateItems()
            return
        # --Fill data and populate
        for (masterName, size) in fileInfo.tes3.masters:
            item = self.newId()
            masterInfo = mosh.MasterInfo(masterName, size)
            self.data[item] = masterInfo
            self.items.append(item)
            self.oldMasters.append(masterName)
        self.newMasters.extend(mosh.modInfos.getLoadOrder(self.oldMasters, False))
        self.allMasters.extend(self.newMasters)
        self.PopulateItems()

    def GetMasterStatus(self, item):
        """Get Master Status"""
        masterInfo = self.data[item]
        masterName = masterInfo.name
        status = masterInfo.getStatus()
        if status == 30 or masterName not in self.newMasters: return status
        newIndex = self.newMasters.index(masterName)
        mwIniLoadOrder = mosh.mwIniFile.loadOrder
        if (not self.edited) and (newIndex != self.oldMasters.index(masterName)):
            return 20
        elif status > 0 or self.fileIsMod:
            return status
        elif ((newIndex < len(mwIniLoadOrder)) and (mwIniLoadOrder[newIndex] == masterName)):
            return -10
        else:
            return status

    def GetItems(self):
        """Get Items"""
        return self.items

    def PopulateItem(self, itemDex, mode=0, selected=set()):  # Polemos changes
        """Populate Item"""
        itemId = self.items[itemDex]
        masterInfo = self.data[itemId]
        masterName = masterInfo.name
        cols = self.cols
        for colDex in range(self.numCols):
            # --Value
            col = cols[colDex]
            if col == 'Master':
                value = masterName
            elif col == '#' or col == 'Load Order':
                value = repr(self.allMasters.index(masterName) + 1)
            # --Insert/Set Value
            if mode and (colDex == 0):
                    self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --Text BG
        if not mosh.mwIniFile.isWellOrdered(masterName):
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.load'])
        elif masterInfo.getObjectMap():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.masters.remapped'])
        elif masterInfo.hasChanged():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.masters.changed'])
        elif masterInfo.isExOverLoaded():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.exOverLoaded'])
        elif not masterInfo.isWellOrdered():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.exists'])
        else:
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.not'])
        # --Image
        status = self.GetMasterStatus(itemId)
        on = masterInfo.isLoaded
        self.list.SetItemImage(itemDex, self.checkboxes.Get(status, on))

    def SortItems(self, col=None, reverse=-2):  # Polemos changes
        """Sort Items"""
        (col, reverse) = self.GetSortSettings(col, reverse)
        # --Sort
        data = self.data
        # --Start with sort by type
        if not self.OpenMW:
            self.items.sort(key=lambda a: data[a].name[:-4].lower())
        elif self.OpenMW:
            tmp_modNamesESM = [x for x in self.items if data[x].name[len(data[x].name) - 3:] in ('esm', 'ame')]
            tmp_modNamesESP = [x for x in self.items if data[x].name[len(data[x].name) - 3:] in ('esp', 'don')]
            self.items = tmp_modNamesESM + tmp_modNamesESP
        if col == 'Master':
            pass  # --Done by default
        elif col == 'Load Order' or col == '#':
            allMasters = self.allMasters
            data = self.data
            self.items.sort(key=lambda a: allMasters.index(data[a].name))
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()
        # --ESMs First?
        conf.settings['mash.masters.esmsFirst'] = self.esmsFirst
        if self.esmsFirst or col == 'Load Order':
            if not self.OpenMW:
                self.items.sort(key=lambda a: str(data[a].name[-1]).lower())
            elif self.OpenMW:
                tmp_modNamesESM = [x for x in self.items if data[x].name[len(data[x].name) - 3:] in ('esm', 'ame')]
                tmp_modNamesESP = [x for x in self.items if data[x].name[len(data[x].name) - 3:] in ('esp', 'don')]
                self.items = tmp_modNamesESM + tmp_modNamesESP

    def getMasterInfos(self, masterName):
        """Get instances"""
        masterInfos = []
        for masterInfo in self.data.values():
            if masterInfo.name == masterName: masterInfos.append(masterInfo)
        return masterInfos

    def isLoaded(self, masterInfos):
        """Selection (exists and is selected)"""
        if not masterInfos: return False
        for masterInfo in masterInfos:
            if not masterInfo.isLoaded: return False
        # --Else Okay
        return True

    def load(self, masterName):
        masterInfos = self.getMasterInfos(masterName)
        # --Already selected?
        if self.isLoaded(masterInfos):
            return True
        # --Already at max masters?
        elif len(self.newMasters) == mosh.mwIniFile.maxPlugins:
            guidialog.ErrorMessage(self,
                                    _('Unable to select %s because file already has maximum number of masters.') % (
                                        masterName,))
            return False
        # --New master?
        elif not masterInfos:
            modInfo = mosh.modInfos.get(masterName, None)
            if not modInfo:
                guidialog.ErrorMessage(self, _('Unable to add %s because file doesn\'t exist.') % (masterName,))
                return False
            itemId = self.newId()
            masterInfo = mosh.MasterInfo(masterName, modInfo.size)
            masterInfo.isNew = True
            self.data[itemId] = masterInfo
            self.items.append(itemId)
            masterInfos.append(masterInfo)
            self.newMasters.append(masterName)
            if masterName not in self.allMasters: self.allMasters.append(masterName)
            self.ReList()
        # --File exists?
        if not masterName in mosh.modInfos.keys():
            wx.Bell()
            return
        # --Select master's masters
        for mmName in masterInfos[0].masterNames:
            if not self.load(mmName): return False
        # --Select master
        for masterInfo in masterInfos: masterInfo.isLoaded = True
        if masterName not in self.newMasters:
            self.newMasters.append(masterName)
            if masterName not in self.allMasters: self.allMasters.append(masterName)
            self.ReList()
        # --Done
        return True

    def unload(self, masterName):
        # --Unselect self
        masterInfos = self.getMasterInfos(masterName)
        for masterInfo in masterInfos: masterInfo.isLoaded = False
        if masterName in self.newMasters: self.newMasters.remove(masterName)
        # --Unselect dependents
        for itemId in self.items:
            otherMasterInfo = self.data[itemId]
            if not otherMasterInfo.isLoaded: continue
            if masterName in otherMasterInfo.masterNames: self.unload(otherMasterInfo.name)

    def ReList(self):
        """Relist"""
        self.newMasters = mosh.modInfos.getLoadOrder(self.newMasters, False)
        self.allMasters = mosh.modInfos.getLoadOrder(self.allMasters, False)

    def InitEdit(self):  # Polemos: Added user warning for when masters are auto-removed.
        """InitEdit"""
        remMasters = []
        # --Pre-clean
        for itemId in self.items:
            masterInfo = self.data[itemId]
            # --Missing Master?
            if not masterInfo.modInfo:
                masterName = masterInfo.name
                newName = conf.settings['mash.mods.renames'].get(masterName, None)
                # --Rename?
                if newName and mosh.modInfos.has_key(newName):
                    masterInfo.setName(newName)
                    if newName not in self.newMasters: self.newMasters.append(newName)
                    if newName not in self.allMasters: self.allMasters.append(newName)
                # --Unselect?
                else:
                    remMasters.append(masterName)
                    masterInfo.isLoaded = False
                if masterName in self.newMasters: self.newMasters.remove(masterName)
            # --Fix size
            if masterInfo.modInfo:
                masterInfo.size = masterInfo.modInfo.size
            else:
                masterInfo.size = 0
        # --Done
        self.edited = True
        self.ReList()
        self.PopulateItems()
        self.parent.SetEdited()
        if remMasters:
            tmessage = _('Warning: Some of the masters were automatically deselected.')
            message = _('This action is taken when a master is missing from the load order'
                        u' or when it contains unknown characters.\n\nIf the master exists, before'
                        u' proceeding with any actions, you may want to rename the master file and'
                        u' then "Change to.." the affected masters to the renamed master file'
                        u' (in the masters list).')
            guidialog.ContinueQuery(self, tmessage, message, 'query.masters.update2', _('Update Masters'), nBtn=False)

    def DoItemSort(self, event):
        """Don't do column head sort."""
        pass

    def DoColumnMenu(self, event):
        """Column Menu"""
        if not self.fileInfo: return
        gui.List.DoColumnMenu(self, event)

    def DoItemMenu(self, event):
        """Item Menu"""
        if not self.edited:
            self.OnLeftDown(event)
        else:
            gui.List.DoItemMenu(self, event)

    def OnColumnResize(self, event):
        """Column Resize"""
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.masters.colWidths')

    def check_empty_gui_fields_po(self):  # Polemos
        """Sanity check for Masters."""
        if self.fileInfo is None:
            return True
        else:
            return False

    def OnLeftDown(self, event):  # Polemos: Hackish hooking #2.
        if self.check_empty_gui_fields_po():
            pass
        else:
            self.OnLeftDown_true_po(event)

    def OnLeftDown_true_po(self, event):  # Polemos: Hackish hooking #1.
        """Event: Left Down"""
        if not self.edited:
            tmessage = _("Edit/update the masters list?")
            message = (_("Note that the update process will automatically"
                         u" fix some problems. Be sure to review the changes before saving."))
            if guidialog.ContinueQuery(self, tmessage, message, 'query.masters.update',
                                        _('Update Masters')) != wx.ID_OK: return
            self.InitEdit()
            return
        (hitItem, hitFlag) = self.list.HitTest((event.GetX(), event.GetY()))
        if hitFlag == 32:
            itemId = self.items[hitItem]
            masterInfo = self.data[itemId]
            # --Unselect?
            if masterInfo.isLoaded:
                self.unload(masterInfo.name)
            # --Select?
            else:
                self.load(masterInfo.name)
            # --Repopulate
            self.ReList()
            self.PopulateItems()
        # --Pass event on (for label editing)
        if self.edited: event.Skip()

    def GetNewMasters(self):
        """GetMasters"""
        newMasters = []
        for newMaster in self.newMasters: newMasters.append((newMaster, mosh.modInfos[newMaster].size))
        return newMasters

    def GetMaps(self):
        """Get ModMap"""
        modMap = {}
        objMaps = []
        for itemId in range(len(self.oldMasters)):
            masterInfo = self.data[itemId]
            # --Delete?
            oldMod = itemId + 1
            if not masterInfo.modInfo or not masterInfo.isLoaded:
                modMap[oldMod] = -1  # --Delete
            else:
                masterName = masterInfo.name
                if masterName not in self.newMasters: raise mosh.MoshError(_("Missing master: %s" % masterName))
                newMod = self.newMasters.index(masterName) + 1
                if newMod != oldMod: modMap[oldMod] = newMod
                # --Object map?
                objMap = masterInfo.getObjectMap()
                if objMap: objMaps.append((oldMod, objMap))
        return (modMap, objMaps)

    def getObjMaps(self):
        """Get ObjMaps"""
        objMaps = {}
        for itemId in range(len(self.oldMasters)): masterInfo = self.data[itemId]
        return objMaps


# ------------------------------------------------------------------------------

class ModList(gui.List, gui.ListDragDropMixin):  # Polemos: OpenMW/TES3mp support
    # --Class Data
    mainMenu = []  # --Column menu
    itemMenu = []  # --Single item menu
    last_item = []  # Alphabetical search by key press
    timeChk = False  # Speed list fix

    def __init__(self, parent):
        self.colNames = conf.settings['mash.colNames']
        self.OpenMW = conf.settings['openmw']
        # --Columns
        if not self.OpenMW:  # Morrowind
            self.cols = conf.settings['mash.mods.cols']
            self.colAligns = conf.settings['mash.mods.colAligns']
            self.colReverse = conf.settings.getChanged('mash.mods.colReverse')
            self.colWidths = conf.settings['mash.mods.colWidths']
            self.sort = conf.settings['mash.mods.sort']
            self.esmsFirst = conf.settings['mash.mods.esmsFirst']
            self.selectedFirst = conf.settings['mash.mods.selectedFirst']
        if self.OpenMW:  # OpenMW/TES3mp
            self.cols = conf.settings['openmw.mods.cols']
            self.colAligns = conf.settings['openmw.mods.colAligns']
            self.colReverse = conf.settings.getChanged('openmw.mods.colReverse')
            self.colWidths = conf.settings['openmw.mods.colWidths']
            self.sort = conf.settings['openmw.mods.sort']
            self.esmsFirst = conf.settings['openmw.mods.esmsFirst']
            self.selectedFirst = conf.settings['openmw.mods.selectedFirst']
        # --Data/Items
        self.data = data = mosh.modInfos
        self.details = None  # --Set by panel
        # --Links
        self.mainMenu = ModList.mainMenu
        self.itemMenu = ModList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT))
        gui.ListDragDropMixin.__init__(self, self.list)
        # --Image List
        checkboxesIL = singletons.images['mash.checkboxes'].GetImageList()
        self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)
        # --Events
        wx.EVT_LIST_ITEM_SELECTED(self, self.listId, self.OnItemSelected)
        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def Refresh(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified file. Also calls saveList.Refresh()!"""
        if self.OpenMW: self.data.refresh()
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files: self.PopulateItem(file, selected=selected)
        singletons.modDetails.SetFile(detail)
        singletons.saveList.Refresh()  # --Saves
        self.set_status()

    def set_status(self):  # Polemos
        """Fix for Mods tab."""
        if not self.OpenMW:  # Polemos: Regular Morrowind support
            text = _('Mods: %d/%d | BSAs: %d/%d') % (
                len(mosh.mwIniFile.loadFiles), len(mosh.modInfos.data),
                len(mosh.mwIniFile.get_active_bsa()), len(singletons.BSArchives.Archives.items))
        if self.OpenMW:  # Polemos: OpenMW/TES3mp support
            text = _('Plugins: %d/%d | BSAs: %d/%d') % (
                len(mosh.mwIniFile.loadFiles), len(mosh.modInfos.data),
                len(mosh.mwIniFile.get_active_bsa()), len(singletons.BSArchives.Archives.items))
        singletons.statusBar.SetStatusField(text, 2)

    def numMod(self):  # Polemos
        """Mod order counter."""
        items, data = mosh.modInfos.getLoadOrder(self.items, False)[:], self.data
        items.sort(key=lambda a: data[a].mtime)
        if not self.OpenMW:
            items.sort(key=lambda x: x[-4:].lower())
        else:
            items.sort(key=lambda x: (x.lower().endswith('.esm') or x.lower().endswith('.omwgame'),
                                      x.lower().endswith('.esp') or x.lower().endswith('.omwaddon')))
        num_mod = {mod: str(num + 1) for num, mod in enumerate(items)}
        return num_mod

    def PopulateItem(self, itemDex, mode=0, selected=set()):  # Polemos, added mod order counter, xrange, type.
        """Populate list."""
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        fileName = self.items[itemDex]
        fileInfo = self.data[fileName]
        numMod = self.numMod()
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            if col == 'File':
                value = fileName
            elif col == 'Rating':
                value = mosh.modInfos.table.getItem(fileName, 'rating', '')
            elif col == 'Group':
                value = mosh.modInfos.table.getItem(fileName, 'group', '')
            elif col == 'Modified':
                value = formatDate(fileInfo.mtime)
            elif col == 'Size':
                value = '%sKB' % (formatInteger(fileInfo.size // 1024))
            elif col == 'Author' and fileInfo.tes3:
                value = fileInfo.tes3.hedr.author
            elif col == '#':
                value = numMod[fileName]
            else:
                value = ''
            if mode and (colDex == 0):  # --Insert/SetString
                self.list.InsertItem(itemDex, value)
            else:
                try:
                    self.list.SetItem(itemDex, colDex, value)
                except UnicodeDecodeError:  # Polemos: Korean fix (possibly more)
                    self.list.SetItem(itemDex, colDex, uniChk(value))
        # --Text BG
        if not mosh.mwIniFile.isWellOrdered(fileName):
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.load'])
        elif fileInfo.isExOverLoaded():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.exOverLoaded'])
        elif not fileInfo.isWellOrdered():
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.exists'])
        elif not self.OpenMW and fileName[-1].lower() == 'm':
            self.list.SetItemBackgroundColour(itemDex, colors['mash.esm'])
        elif self.OpenMW and any([fileName[-1].lower() == 'm', fileName[-1].lower() == 'e']):
            self.list.SetItemBackgroundColour(itemDex, colors['mash.esm'])
        else:
            self.list.SetItemBackgroundColour(itemDex, colors['mash.doubleTime.not'])
        # --Image
        status = fileInfo.getStatus()
        on = fileInfo.name in mosh.mwIniFile.loadFiles
        self.list.SetItemImage(itemDex, self.checkboxes.Get(status, on))
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):  # Polemos: changes
        (col, reverse) = self.GetSortSettings(col, reverse)
        self.isReversed = reverse
        if not self.OpenMW: conf.settings['mash.mods.sort'] = col
        if self.OpenMW: conf.settings['openmw.mods.sort'] = col
        loadFiles = mosh.mwIniFile.loadFiles
        data = self.data
        # --Start with sort by load order
        self.items = mosh.modInfos.getLoadOrder(self.items, False)
        if col == 'File':
            self.items.sort(key=lambda a: a[:-4].lower())
            self.items.reverse()
        elif col == 'Author':
            self.items.sort(key=lambda x: data[x].tes3.hedr.author.casefold())
        elif col == 'Rating':
            self.items.sort(key=lambda a: mosh.modInfos.table.getItem(a, 'rating', ''))
        elif col == 'Group':
            self.items.sort(key=lambda a: mosh.modInfos.table.getItem(a, 'group', ''))
        elif col == 'Load Order':
            self.items = mosh.modInfos.getLoadOrder(self.items, False)
        elif col == 'Modified':
            self.items.sort(key=lambda a: data[a].mtime)
        elif col == 'Size':
            self.items.sort(key=lambda a: data[a].size)
        elif col == 'Status':
            self.items.sort(key=lambda a: data[a].getStatus())
        elif col == 'Version':
            self.items.sort(key=lambda a: data[a].tes3.hedr.version)
        elif col == '#':
            self.items.sort(key=lambda a: data[a].mtime)
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()
        # --ESMs First?
        if not self.OpenMW:
            conf.settings['mash.mods.esmsFirst'] = self.esmsFirst
            if self.esmsFirst or col in ['Load Order', '#', 'Modified']:
                self.items.sort(key=lambda x: x[-4:].casefold())
        else:
            conf.settings['openmw.mods.esmsFirst'] = self.esmsFirst
            if self.esmsFirst or col in ['Load Order', '#', 'Modified']:
                self.items.sort(key=lambda x: (x.casefold().endswith('.esm') and x.casefold().endswith('.omwgame'),
                                               x.casefold().endswith('.esp') and x.casefold().endswith('.omwaddon')))
        # --Selected First?
        if not self.OpenMW:
            conf.settings['mash.mods.selectedFirst'] = self.selectedFirst
        else:
            conf.settings['openmw.mods.selectedFirst'] = self.selectedFirst
        if self.selectedFirst: self.items.sort(key=lambda x: (x in loadFiles, x))

    def ToggleModActivation(self, fileNames):  # Polemos, speed things up...
        """This toggles if a mod is unloaded."""
        toUnload = []
        toLoad = []
        if isinstance(fileNames, str):
            fileNames = [fileNames]
        [toUnload.append(x) if self.data.isLoaded(x) else toLoad.append(x) for x in fileNames]
        if toUnload: self.data.unload(toUnload)
        if toLoad:
            try:
                self.data.load(toLoad)
            except mosh.MaxLoadedError:  # todo: add which mods
                guidialog.ErrorMessage(self, _("Unable to add some mods because load list is full."))
                return

    def OnDoubleClick(self, event):
        """Handle doubeclick event."""
        (hitItem, hitFlag) = self.list.HitTest(event.GetPosition())
        if hitItem < 0: return
        fileInfo = self.data[self.items[hitItem]]
        if not singletons.docBrowser:
            DocBrowser().Show()
            if not self.OpenMW: conf.settings['mash.modDocs.show'] = True
            if self.OpenMW: conf.settings['openmw.modDocs.show'] = True
        singletons.docBrowser.SetMod(fileInfo.name)
        singletons.docBrowser.Raise()

    def OnColumnResize(self, event):
        """Column Resize"""
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        if not self.OpenMW: conf.settings.setChanged('mash.mods.colWidths')
        if self.OpenMW: conf.settings.setChanged('openmw.mods.colWidths')

    def OnLeftDown(self, event):
        """Event: Left Down"""
        (hitItem, hitFlag) = self.list.HitTest((event.GetX(), event.GetY()))
        if hitFlag == 32:
            oldDTFiles = mosh.mwIniFile.getDoubleTimeFiles()
            oldFiles = mosh.mwIniFile.loadFiles[:]
            fileName = self.items[hitItem]
            self.ToggleModActivation(fileName)
            newDTFiles = mosh.mwIniFile.getDoubleTimeFiles()
            # --Refresh changed files
            self.Refresh()
            # --Mark sort as dirty
            if self.selectedFirst: self.sortDirty = 1
        # --Pass Event onward
        event.Skip()

    def timeSelChk(self, event):  # Polemos
        """Check time conditions to show item details."""
        self.timer.Stop()
        if self.timeChk:
            self.details.SetFile(self.timeChk)
            if singletons.journalBrowser: singletons.journalBrowser.SetSave(self.timeChk)
        self.timeChk = False

    def OnItemSelected(self, event=None):  # Polemos
        """Time buffer for showing item details."""
        if not singletons.modList.details.master_btn.IsEnabled(): singletons.modList.details.master_btn.Enable()
        if not self.timeChk:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.timeSelChk, self.timer)
            self.timer.Start(50)
        self.timeChk = self.items[event.Index]

    def OnKeyDown(self, event):  # Polemos: added delete item on DEL
        fmap = {
            wx.WXK_SPACE: self.OnSpacePress,
            wx.WXK_UP: self.OnUpPress,
            wx.WXK_DOWN: self.OnDownPress,
            65: self.OnAPress,
            385: self.delOnChar,
            127: self.delOnChar
        }
        kc = event.GetKeyCode()
        if kc in fmap:
            fmap[kc](event)
        else:
            self.OnGenKeys(chr(event.GetKeyCode()))  # Polemos: Alpha, Beta, search...

    def delOnChar(self, event):  # Polemos
        """Deletes selected item."""
        self.DeleteSelected()

    def OnGenKeys(self, letter):  # Polemos: Was missing from Yakoby's version. Faster than skipping events
        """Selects unicode items by their first letter."""
        while True:
            for x in self.items:
                if x.startswith(letter) or x.startswith(letter.lower()):
                    if x not in self.last_item:
                        self.ClearSelected()
                        self.SelectItems(x)
                        self.SetItemFocus(x)
                        self.last_item.append(x)
                        return
            try:
                del self.last_item[0]
            except:
                return

    def OnAPress(self, event):
        if event.ControlDown():
            self.SelectAll()
        else:
            self.OnGenKeys('A')

    def OnUpPress(self, event):
        event.Skip()
        self.moveSelected(event, (-1))

    def OnDownPress(self, event):
        event.Skip()
        self.moveSelected(event, (+1))

    def OnSpacePress(self, event):  # Polemos: Speed up
        self.ToggleModActivation(self.GetSelected())
        self.Refresh()

    def chkSort(self):  # Polemos
        """Check column sorting."""
        if not self.OpenMW:  # Polemos: Regular Morrowind support
            if conf.settings['mash.mods.sort'] != 'Modified' and conf.settings['mash.mods.sort'] != '#':
                guidialog.ErrorMessage(self.GetParent(), _('The Mods '
                                                            u'list must be sorted "by Modified" or by "Load Order (#)" to\nenable Keyboard or Mouse based sorting.'))
                return False
        elif self.OpenMW:  # Polemos: OpenMW/TES3mp support
            if conf.settings['openmw.mods.sort'] != '#':
                guidialog.ErrorMessage(self.GetParent(), _('The Plugins list '
                                                            u'must be sorted by "Load Order (#)" to\nenable Keyboard or Mouse based sorting.'))
                return False
        return True

    def chkReversed(self):
        """Check if list is reversed."""
        if not self.isReversed: return True
        if not self.OpenMW:  # Polemos: Regular Morrowind support
            guidialog.ErrorMessage(self.GetParent(),
                                    _('The Mods list is reversed. Only Keyboard based sorting is allowed (Ctrl+Arrows).'))
        elif self.OpenMW:  # Polemos: OpenMW/TES3mp support
            guidialog.ErrorMessage(self.GetParent(),
                                    _('The Plugins list is reversed. Only Keyboard based sorting is allowed (Ctrl+Arrows).'))
        return False

    def OnDrop(self, names, toIdx):  # Polemos: Complete recoding.
        """Support for dragging and dropping list items"""
        # Notify user if drag and drop is allowed
        if not self.chkSort(): return
        if not self.chkReversed(): return
        # Get item list and sort it by date
        items = self.items[:]
        # Change item(s) pos in list
        items = [None if x in names else x for x in items]
        items[toIdx:toIdx] = names
        items = [x for x in items if x is not None]
        # Get item(s) type(s)
        if not self.OpenMW:
            esm = [x for x in items if x.lower().endswith('.esm')]
            esp = [x for x in items if x.lower().endswith('.esp')]
        elif self.OpenMW:
            esm = [x for x in items if x.lower().endswith('.esm') or x.lower().endswith('.omwgame')]
            esp = [x for x in items if x.lower().endswith('.esp') or x.lower().endswith('.omwaddon')]
        # Fix cases that the first item is in Unix time 1.0
        getTime = lambda x: mosh.modInfos[x].mtime
        curTimes = sorted(getTime(i) for i in items)
        if min(curTimes) <= 1000:
            for i, x in enumerate(items, 1):
                mosh.modInfos[x].setMTime(10000 * i)
        # Set items timestamps (for ordering)
        for fType, itms in {'esm': esm, 'esp': esp}.items():
            for i in range(len(itms) - 1, 0, -1):
                if getTime(itms[i]) <= getTime(itms[i - 1]):
                    mosh.modInfos[itms[i - 1]].setMTime(getTime(itms[i]) - 1)
        # Refresh GUI
        mosh.modInfos.refreshDoubleTime()
        self.Refresh()

    def moveSelected(self, event, moveMod):
        """Moves selected files up or down (depending on moveMod)"""
        if not event.ControlDown(): return
        if not self.chkSort(): return
        if self.isReversed: moveMod = moveMod * (-1)
        selected = self.GetSelected()
        if not selected: return
        if not self.OpenMW:
            self.moveSelectedFilter(selected, moveMod, lambda x: x.lower().endswith('.esp'))
            self.moveSelectedFilter(selected, moveMod, lambda x: x.lower().endswith('.esm'))
        else:
            self.moveSelectedFilter(selected, moveMod,
                                    lambda x: x.lower().endswith('.esp') or x.lower().endswith('.omwaddon'))
            self.moveSelectedFilter(selected, moveMod,
                                    lambda x: x.lower().endswith('.esm') or x.lower().endswith('.omwgame'))
        self.Refresh()
        # Polemos: for OpenMW/TES3mp support
        if self.OpenMW: mosh.mwIniFile.safeSave()

    def moveSelectedFilter(self, origSel, moveMod, pred):
        """Move selected items."""
        selected = [x for x in origSel if pred(x)]
        selected.sort(key=lambda x: mosh.modInfos[x].mtime, reverse=(moveMod != -1))
        items = [x for x in self.GetItems() if pred(x)]
        items.sort(key=lambda x: mosh.modInfos[x].mtime)
        for item in selected:
            pos = items.index(item)
            movePos = pos + moveMod
            if movePos < 0 or movePos >= len(items): break
            items[pos], items[movePos] = items[movePos], items[pos]
        # correct the times on the list
        getTime = lambda x: mosh.modInfos[x].mtime
        for i in range(len(items) - 1, 0, -1):
            if getTime(items[i]) <= getTime(items[i - 1]):
                mosh.modInfos[items[i - 1]].setMTime(getTime(items[i]) - 1)
        mosh.modInfos.refreshDoubleTime()
        self.ClearSelected()
        self.SelectItems(origSel)


# ------------------------------------------------------------------------------

class ModdataList(gui.List, gui.ListDragDropMixin):  # Polemos
    """Show the Mods list (Mods resources list) OpenMW/TES3mp.."""
    mainMenu = []  # --Column menu
    itemMenu = []  # --Single item menu
    last_item = []  # Alphabetical search by key press

    def __init__(self, parent):
        # --Columns
        self.cols = conf.settings['mash.datamods.cols']
        self.colAligns = conf.settings['mash.datamods.colAligns']
        self.colNames = conf.settings['mash.colNames']
        self.colReverse = conf.settings.getChanged('mash.datamods.colReverse')
        self.colWidths = conf.settings['mash.datamods.colWidths']
        # --Data/Items
        self.data = data = mosh.DataModsInfo()
        self.datamods = mosh.mwIniFile
        self.sort = conf.settings['mash.datamods.sort']
        # --Links
        self.mainMenu = ModdataList.mainMenu
        self.itemMenu = ModdataList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT))
        gui.ListDragDropMixin.__init__(self, self.list)
        # --Image List
        checkboxesIL = singletons.images['mash.checkboxes'].GetImageList()
        self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)
        # --Events
        wx.EVT_LIST_ITEM_SELECTED(self, self.listId, self.OnItemSelected)
        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.list.Bind(wx.EVT_CHAR, self.OnChar)

    def Refresh(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified file."""
        self.data.refresh()
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files: self.PopulateItem(file, selected=selected)
        singletons.modList.Refresh()
        singletons.ArchivesList.Refresh()
        singletons.mashFrame.SetStatusCount()

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        """Populate mod list with entries."""
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        fileName = self.items[itemDex].strip()
        fileInfo = self.data[fileName]
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            # --Get Value
            if col == 'Mod Name':
                value = fileInfo[0]
            elif col == '#':
                value = fileInfo[1] + 1
            elif col == 'Flags':
                value = ','.join(fileInfo[2])
            elif col == 'Version':
                value = fileInfo[3]
            elif col == 'Category':
                value = fileInfo[4]
            else:
                value = ''
            # --Insert/SetString
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, str(value, encoding='utf-8', errors='ignore'))  # todo: test this
        # --Image
        on = fileInfo[5]
        self.list.SetItemImage(itemDex, self.checkboxes.Getsimple(on))
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):
        (col, reverse) = self.GetSortSettings(col, reverse)
        conf.settings['mash.datamods.sort'] = col
        data = self.data
        self.items.sort(key=lambda a: data[a][1])  # --Start with sort by order
        if col == 'Mod Name':
            self.items.sort(key=lambda a: data[a][0].lower())
        elif col == '#':
            pass  # --Done by default
        elif col == 'Flags':
            self.items.sort(key=lambda a: data[a][2])
        elif col == 'Category':
            self.items.sort(key=lambda a: data[a][4])
        elif col == 'Version':
            self.items.sort(key=lambda a: data[a][3])
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()

    def ToggleModActivation(self, DataMods):
        """Toggle mod load/unload state."""
        enabled = []
        disabled = []
        if isinstance(DataMods, str):
            DataMods = [DataMods]
        [disabled.append(x) if self.datamods.checkActiveState(x) else enabled.append(x) for x in DataMods]
        if disabled: self.datamods.unloadDatamod(disabled)
        if enabled: self.datamods.loadDatamod(enabled, self.items)
        self.Refresh()

    def OnDoubleClick(self, event):
        """Handle double click event."""
        (hitItem, hitFlag) = self.list.HitTest(event.GetPosition())
        if hitItem < 0: return
        fileInfo = self.data[self.items[hitItem]]
        os.startfile(fileInfo[6])

    def OnChar(self, event):  # $# from FallenWizard
        if (event.GetKeyCode() == 127): self.DeleteSelected()
        event.Skip()  # $#

    def OnColumnResize(self, event):
        """Column Resize"""
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.datamods.colWidths')

    def OnLeftDown(self, event):
        """Event: Left Down"""
        (hitItem, hitFlag) = self.list.HitTest((event.GetX(), event.GetY()))
        if hitFlag == 32:
            fileName = self.items[hitItem]
            self.ToggleModActivation(fileName)
        # --Pass Event onward
        event.Skip()

    def OnItemSelected(self, event):
        """Do stuff when selecting a mod."""
        modName = self.items[event.Index]

    def OnKeyDown(self, event):
        fmap = {
            wx.WXK_SPACE: self.OnSpacePress,
            wx.WXK_UP: self.OnUpPress,
            wx.WXK_DOWN: self.OnDownPress,
            65: self.OnAPress,
        }
        kc = event.GetKeyCode()
        if kc in fmap:
            fmap[kc](event)
        else:
            self.OnGenKeys(chr(event.GetKeyCode()))  # Polemos: Alpha, Beta, search...

    def OnGenKeys(self, letter):  # Polemos
        """Selects unicode items by their first letter."""
        while True:
            for x in self.data.keys():
                if self.data[x][0].startswith(letter) or self.data[x][0].startswith(letter.lower()):
                    if self.data[x][0] not in self.last_item:
                        self.ClearSelected()
                        self.SelectItems(self.data[x][6])
                        self.SetItemFocus(self.data[x][6])
                        self.last_item.append(self.data[x][0])
                        return
            try:
                del self.last_item[0]
            except:
                return

    def OnAPress(self, event):
        if event.ControlDown():
            self.SelectAll()
        else:
            self.OnGenKeys('A')

    def OnUpPress(self, event):
        event.Skip()
        self.moveSelected(event, (-1))

    def OnDownPress(self, event):
        event.Skip()
        self.moveSelected(event, (+1))

    def OnSpacePress(self, event):
        self.ToggleModActivation(self.GetSelected())
        self.Refresh()

    def chkSort(self):  # Polemos
        """Check column sorting."""
        if conf.settings['mash.datamods.sort'] != '#':
            guidialog.ErrorMessage(self.GetParent(), _('The'
                                                        u' Mods list must be sorted by "Load Order (#)" to\n enable Keyboard or Mouse based sorting.'))
            return False
        return True

    def OnDrop(self, names, toIdx):
        """Support for dragging and dropping list items."""
        if not self.chkSort(): return
        selected = self.GetSelected()
        items = [x for x in self.items]
        for mod in selected:
            pos = items.index(mod)
            if pos < toIdx: toIdx -= 1
            items.insert(toIdx, items.pop(pos))
            toIdx += 1
        self.data.moveTo(items)
        self.Refresh()
        singletons.ModdataList.datamods.updateDatamods(self.items)

    def moveSelected(self, event, moveMod):
        """Moves selected files up or down (depending on moveMod)."""
        if not event.ControlDown(): return
        if not self.chkSort(): return
        selected = self.GetSelected()
        if moveMod != -1: selected.reverse()
        items = [x for x in self.items]
        for mod in selected:
            pos = items.index(mod)
            movePos = pos + moveMod
            if movePos < 0 or movePos >= len(items): break
            items.insert(movePos, items.pop(pos))
        self.ClearSelected()
        self.SelectItems(selected)
        self.data.moveTo(items)
        if not selected: return
        self.Refresh()
        singletons.ModdataList.datamods.updateDatamods(self.items)


# ------------------------------------------------------------------------------

class ModDetails(
    wx.Window):  # Polemos: fixed bugs, refactored, optimised, addons. Change invokes dialog. Dialogs saved with "ok", bypassing "Save" btn.
    """Right panel details for Mod/Plugins Tab."""

    def __init__(self, parent):
        """Init."""
        wx.Window.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        # --Singleton
        singletons.modDetails = self
        # --Data
        self.encod = conf.settings['profile.encoding']
        self.openmw = conf.settings['openmw']
        self.maxSash = conf.settings['mash.max.sash']
        self.dtform = '%x, %H:%M:%S'
        self.modInfo = None
        self.edited = False
        if True:  # Content
            # Toolbar: Info text label
            self.infotext = wx.StaticText(self, wx.ID_ANY, u'', DPOS, DSIZE, wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)
            self.infotext.Wrap(-1)
            # Toolbar: Restore Button
            self.restore_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.open'].GetBitmap(), DPOS, DSIZE,
                                               0 | ADRW)
            self.restore_btn.SetBitmapPressed(singletons.images['mod.open'].GetBitmap())
            self.restore_btn.SetBitmapCurrent(singletons.images['mod.open.onhov'].GetBitmap())
            self.restore_btn.SetToolTip(wx.ToolTip(_('Restore Mod Order')))
            # Toolbar: Backup Button
            self.backup_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.save'].GetBitmap(), DPOS, DSIZE,
                                              0 | ADRW)
            self.backup_btn.SetBitmapPressed(singletons.images['mod.save'].GetBitmap())
            self.backup_btn.SetBitmapCurrent(singletons.images['mod.save.onhov'].GetBitmap())
            self.backup_btn.SetToolTip(wx.ToolTip(_('Backup Mod Order')))
            # File/Version Static Text
            self.version = wx.StaticText(self, -1, u'v0.0')
            modText = wx.StaticText(self, -1, _('Morrowind Mod File'))
            # File Name
            self.file = wx.TextCtrl(self, wx.NewId(), u'', size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.file.SetMaxLength(200)
            # Author
            self.author = wx.TextCtrl(self, wx.NewId(), u'', size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.author.SetMaxLength(32)
            # Modified
            self.modified = wx.TextCtrl(self, wx.NewId(), u'', size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.modified.SetMaxLength(32)
            self.cpBtn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.datetime.cp'].GetBitmap(), DPOS, DSIZE,
                                         ADRW)
            self.cpBtn.SetToolTip(wx.ToolTip(_('Copy Mod Datetime')))
            self.psBtn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.datetime.ps'].GetBitmap(), DPOS, DSIZE,
                                         ADRW)
            self.psBtn.SetToolTip(wx.ToolTip(_('Paste Mod Datetime')))
            # Description
            self.description = wx.TextCtrl(self, wx.NewId(), u'', size=(self.maxSash, 130),
                                           style=wx.TE_MULTILINE | wx.TE_READONLY)
            self.description.SetMaxLength(256)
            # Masters
            singletons.modsMastersList = self.masters = MasterList(self, None)
            # Master Menu Button
            self.master_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['master.menu'].GetBitmap(), DPOS,
                                              DSIZE, ADRW)
            self.master_btn.SetBitmapPressed(singletons.images['master.menu'].GetBitmap())
            self.master_btn.SetBitmapCurrent(singletons.images['master.menu.onhov'].GetBitmap())
            self.master_btn.SetToolTip(wx.ToolTip(_('Masters Menu')))
            self.master_btn.Disable()
            # Buttons
            self.save = wx.Button(self, wx.ID_SAVE, size=wx.Size(90, 21))
            self.cancel = wx.Button(self, wx.ID_CANCEL, size=wx.Size(90, 21))
            self.save.Disable()
            self.cancel.Disable()
        if True:  # Theming
            # e.g: self.restore_btn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
            pass
        if True:  # Layout
            # Info sizer
            info_sizer = wx.BoxSizer(wx.VERTICAL)
            info_sizer.Add(self.infotext, 1, wx.EXPAND | wx.RIGHT | wx.LEFT, 5)
            # Toolbar sizer
            tbarSizer = wx.BoxSizer(wx.HORIZONTAL)
            tbarSizer.SetMinSize(wx.Size(170, 24))
            tbarSizer.AddMany([(info_sizer, 1, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, 1),
                               (self.restore_btn, 0, wx.RIGHT | wx.LEFT, 2),
                               (self.backup_btn, 0, wx.RIGHT | wx.LEFT, 2)])
            # DateTime sizer
            dtSizer = wx.BoxSizer(wx.HORIZONTAL)
            dtSizer.AddMany([(self.modified, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5),
                             (self.cpBtn, 0, wx.ALIGN_CENTER_VERTICAL, 5),
                             (self.psBtn, 0, wx.ALIGN_CENTER_VERTICAL, 5)])
            # Go figure sizers
            modSizer = wx.BoxSizer(wx.HORIZONTAL)
            modSizer.AddMany([(modText, 0, 0, 4), ((0, 0), 1), (self.version, 0, wx.RIGHT, 4)])
            mstrSizer = wx.BoxSizer(wx.HORIZONTAL)
            mstrSizer.AddMany([((0, 0), 1), (self.save, 0, wx.RIGHT, 4),
                               (self.master_btn, 0, wx.CENTER, 4), (self.cancel, 0, wx.LEFT, 4), ((0, 0), 1)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(mainSizer)
            mainSizer.AddMany([(tbarSizer, 0, wx.EXPAND, 5), (modSizer, 0, wx.EXPAND), self.file, self.author,
                               (dtSizer, 0, wx.EXPAND), self.description, (self.masters, 1, wx.EXPAND),
                               (mstrSizer, 0, wx.EXPAND | wx.TOP, 4)])
        if True:  # Events
            self.restore_btn.Bind(wx.EVT_BUTTON, self.restore)
            self.backup_btn.Bind(wx.EVT_BUTTON, self.backup)
            self.master_btn.Bind(wx.EVT_BUTTON, self.MasterMenu)
            wx.EVT_LEFT_DOWN(self.file, self.OnEditFile)
            wx.EVT_RIGHT_DOWN(self.file, self.OnEditFile)
            wx.EVT_LEFT_DOWN(self.author, self.OnEditAuthor)
            wx.EVT_RIGHT_DOWN(self.author, self.OnEditAuthor)
            wx.EVT_LEFT_DOWN(self.modified, self.OnEditModified)
            wx.EVT_RIGHT_DOWN(self.modified, self.OnEditModified)
            wx.EVT_LEFT_DOWN(self.description, self.OnEditDescription)
            wx.EVT_RIGHT_DOWN(self.description, self.OnEditDescription)
            self.cpBtn.Bind(wx.EVT_BUTTON, self.cpDTbtnAct)
            self.psBtn.Bind(wx.EVT_BUTTON, self.psDTbtnAct)
            wx.EVT_BUTTON(self, wx.ID_SAVE, self.OnSave)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.clipbrdDatetime = ''
        self.psBtn.Disable() if not self.clipbrdDatetime else self.psBtn.Enable()

    def cpDTbtnAct(self, event):  # Polemos
        """Copy datetime button actions."""
        if not self.modInfo: return
        datetime = self.modify_time_po(False)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(datetime.replace('-', '/').replace(' ', ', ')))
            wx.TheClipboard.Close()
        self.clipbrdDatetime = datetime
        if self.clipbrdDatetime: self.psBtn.Enable()

    def psDTbtnAct(self, event):  # Polemos
        """Paste datetime button actions."""
        if not self.modInfo: return
        start_time_po = self.modify_time_po(False)
        if self.clipbrdDatetime and start_time_po:
            self.OnEditModified(None, self.clipbrdDatetime, start_time_po, False)

    def MasterMenu(self, event):  # Polemos
        """Masters button menu."""
        pos = self.master_btn.GetScreenPosition()
        gui.List.DoColumnMenu(self.masters, pos)

    def restore(self, event):  # Polemos
        """Restore Mod order."""
        # Open backup browser
        BckList = mosh.GetBckList('datasnap').bckList
        backupFile = guidialog.SimpleListDialog(self, BckList, _('Choose a backup to restore:')).Selection
        if backupFile is None: return
        # Mod data
        order_po = mosh.LoadModOrder(backupFile, fname='datasnap').modData
        if len(order_po) <= 1 or not order_po: return
        # Redate
        mtime_first = 1026943162
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
        loadorder_mtime_increment = (mtime_last - mtime_first) // len(order_po)
        mtime = mtime_first
        for mod in order_po:
            try:
                mosh.modInfos[mod].setMTime(mtime)
            except:
                continue
            mtime += loadorder_mtime_increment
        mod_po = mosh.ModInfos('', True)
        [mod_po.unload(x, True) for x in mosh.mwIniFile.loadOrder]
        for x in order_po:
            try:
                singletons.modList.ToggleModActivation(x)
            except:
                continue
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()

    def backup(self, event):  # Polemos
        """Save Mod order."""
        log = mosh.LogFile(BytesIO())
        [log('%s' % name) for num, name in enumerate(mosh.mwIniFile.loadOrder)]
        modOrder = mosh.winNewLines(log.out.getvalue())
        if mosh.SaveModOrder(modOrder, 'plugins', 'datasnap').status: self.showInfo(_('Plugins Order Saved...'))

    def showInfo(self, msg):  # Polemos
        """Inform user about actions."""
        self.infotext.SetLabel(msg)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1000)

    def onUpdate(self, event):  # Polemos
        """Check timer and update info."""
        self.infotext.SetLabel('')
        self.timer.Stop()

    def modify_time_po(self, guiON=True):  # Polemos
        """dialog for editing time."""
        data_files_po = os.path.join(conf.settings['mwDir'], 'Data Files')
        file_po = os.path.join(data_files_po, (self.modInfo.name))
        start_time_po = formatdate64(int(os.path.getmtime(file_po)))
        if guiON:
            dialog = guidialog.date_time_dialog(self, u'Redate Mod', u'Redate selected mod (24h hour format):',
                                                 start_time_po)
            newTimeStr_po = dialog.GetValue()
            return newTimeStr_po, start_time_po
        else:
            return start_time_po

    def modify_dialog_po(self, field, failsafe_po=False):  # Polemos
        """Dialog for editing fields."""
        if field == 'description':
            current_po = self.description.GetValue()
            msg_po = u'Enter a new Description (256 characters max):'
            caption_po = u'Enter Description'
            max_char_po = 256
        elif field == 'author':
            current_po = self.author.GetValue()
            msg_po = u'Enter a new Author name (32 characters max):'
            caption_po = u'Rename Author'
            max_char_po = 32
        elif field == 'filename':
            current_po = self.modInfo.name
            msg_po = u'Select a new filename:'
            caption_po = u'Rename Mod'
            max_char_po = 200
        else:
            failsafe_po = True
        dialog = guidialog.MaxCharDialog(caption_po, max_char_po, current_po, msg_po, self)
        if failsafe_po:
            new_po = current_po
        else:
            new_po = dialog.GetValue()
        return new_po, current_po

    def SetFile(self, fileName='SAME'):
        if fileName == 'SAME':  # --Reset?
            if not self.modInfo or self.modInfo.name not in mosh.modInfos:
                fileName = None
            else:
                fileName = self.modInfo.name
        if not fileName:  # --Empty?
            modInfo = self.modInfo = None
            self.fileStr = ''
            self.authorStr = ''
            self.modifiedStr = ''
            self.descriptionStr = ''
            self.versionStr = ''
        else:  # --Valid fileName?
            modInfo = self.modInfo = mosh.modInfos[fileName]
            # --Remember values for edit checks
            self.fileStr = modInfo.name
            self.authorStr = modInfo.tes3.hedr.author
            self.modifiedStr = formatDate(modInfo.mtime)
            self.descriptionStr = modInfo.tes3.hedr.description
            self.versionStr = u'v%0.1f' % (modInfo.tes3.hedr.version,)
        # --Set fields
        for field, val in zip((self.file, self.author, self.modified, self.description),  # Polemos
                              (self.fileStr, self.authorStr, self.modifiedStr, self.descriptionStr)):
            try:
                field.SetValue(val)
            except:
                field.SetValue(uniChk(val))
        self.version.SetLabel(self.versionStr)
        self.masters.SetFileInfo(modInfo)
        # --Edit State
        self.edited = 0
        self.save.Disable()
        self.cancel.Disable()

    def SetEdited(self):  # Polemos
        self.edited = True
        self.save.Enable()
        self.cancel.Enable()

    def SetEdited_save_po(self):  # Polemos
        """Save button bypass for all dialogs."""
        self.edited = True
        self.OnSave(self)

    def OnBrowser(self, event):
        """Event: Clicked Doc Browser button."""
        if not singletons.docBrowser:
            DocBrowser().Show()
            conf.settings['mash.modDocs.show'] = True
        if self.modInfo:
            singletons.docBrowser.SetMod(self.modInfo.name)
        singletons.docBrowser.Raise()

    def OnTextEdit(self, event):
        if self.modInfo and not self.edited:
            try:
                if ((self.fileStr.encode('utf-8') != self.file.GetValue().encode('utf-8')) or
                        (self.authorStr.encode('utf-8') != self.author.GetValue().encode('utf-8')) or
                        (self.modifiedStr != self.modified.GetValue().encode('utf-8')) or
                        (self.descriptionStr.encode('utf-8') != self.description.GetValue().encode('utf-8'))):
                    self.SetEdited()
            except:
                pass
        event.Skip()

    def OnEditFile(self, event):  # Polemos: Redirect to dialog and more.
        if not self.modInfo: return
        fileStr, old_file_po = self.modify_dialog_po('filename')
        # --Changed?
        if fileStr == old_file_po: return
        # --Extension Changed?
        if fileStr[-4:].lower() != self.fileStr[-4:].lower():
            guidialog.ErrorMessage(self, _("Incorrect file extension: ") + fileStr[-3:])
            self.file.SetValue(self.fileStr)
        # --Else file exists?
        elif os.path.exists(os.path.join(self.modInfo.dir, fileStr)):
            guidialog.ErrorMessage(self, _("File %s already exists.") % (fileStr,))
            self.file.SetValue(self.fileStr)
        else:  # --Okay?
            self.fileStr = fileStr
            self.SetEdited_save_po()

    def OnEditAuthor(self, event):  # Polemos: Redirect to dialog and more.
        if not self.modInfo: return
        authorStr, old_author_po = self.modify_dialog_po('author')
        if authorStr != old_author_po:
            self.authorStr = authorStr
            self.SetEdited_save_po()

    def OnEditModified(self, event, modifiedStr='', oldtimestr_po='',
                       guiON=True):  # Polemos: Redirect to dialog and more.
        if not self.modInfo: return
        if guiON: modifiedStr, oldtimestr_po = self.modify_time_po()
        if modifiedStr == oldtimestr_po: return
        try:
            newTimeTup = time.strptime(modifiedStr, '%m-%d-%Y %H:%M:%S')
            time.mktime(newTimeTup)
        except ValueError:
            guidialog.ErrorMessage(self, _('Unrecognized date: %s' % modifiedStr))
            self.modified.SetValue(self.modifiedStr)
            return
        except OverflowError:
            guidialog.ErrorMessage(self, _('Mash cannot handle files dates greater than January 19, 2038.)'))
            self.modified.SetValue(self.modifiedStr)
            return
        # --Normalize format
        modifiedStr = time.strftime(self.dtform, newTimeTup)
        self.modifiedStr = modifiedStr
        self.modified.SetValue(modifiedStr)  # --Normalize format
        self.SetEdited_save_po()

    def OnEditDescription(self, event):  # Polemos: Redirect to dialog and more.
        if not self.modInfo: return
        descriptionStr, old_descriptionStr_po = self.modify_dialog_po('description')
        if descriptionStr != old_descriptionStr_po:
            self.descriptionStr = descriptionStr
            self.SetEdited_save_po()

    def OnSave(self, event):
        modInfo = self.modInfo
        # --Change Tests
        changeName = (self.fileStr != modInfo.name)
        changeDate = (self.modifiedStr != formatDate(modInfo.mtime))
        changeHedr = ((self.authorStr != modInfo.tes3.hedr.author) or (
                self.descriptionStr != modInfo.tes3.hedr.description))
        changeMasters = self.masters.edited
        # --Only change date?
        if changeDate and not (changeName or changeHedr):
            newTimeTup = time.strptime(self.modifiedStr, self.dtform)
            newTimeInt = int(time.mktime(newTimeTup))
            modInfo.setMTime(newTimeInt)
            self.SetFile(self.modInfo.name)
            mosh.modInfos.refreshDoubleTime()
            singletons.modList.Refresh()
            return
        # --Backup
        modInfo.makeBackup()
        # --Change Name?
        fileName = modInfo.name
        if changeName:
            (oldName, newName) = (modInfo.name, self.fileStr.strip())
            singletons.modList.items[singletons.modList.items.index(oldName)] = newName
            conf.settings.getChanged('mash.mods.renames')[oldName] = newName
            mosh.modInfos.rename(oldName, newName)
            fileName = newName
        # --Change hedr?
        if changeHedr:
            modInfo.tes3.hedr.author = self.authorStr.strip()
            modInfo.tes3.hedr.description = self.descriptionStr.strip()
            modInfo.tes3.hedr.changed = True
            modInfo.writeHedr()
        # --Change masters?
        warning = False
        if changeMasters:
            newMasters = self.masters.GetNewMasters()
            (modMap, objMaps) = self.masters.GetMaps()
            # --Create and use FileRefs
            progress = None
            try:
                progress = guidialog.ProgressDialog(_('Saving'))
                fileRefs = mosh.FileRefs(modInfo, progress=progress)
                progress.setBaseScale(0.0, 0.67)
                fileRefs.load()
                progress(1.0, _('Remap Masters'))
                fileRefs.remap(newMasters, modMap, objMaps)
                progress.setBaseScale(0.67, 0.33)
                fileRefs.safeSave()
            except:
                warning = True
            finally:
                progress = progress.Destroy()
        # --Change date?
        if (changeDate or changeHedr or changeMasters):
            newTimeTup = time.strptime(self.modifiedStr, self.dtform)
            newTimeInt = int(time.mktime(newTimeTup))
            modInfo.setMTime(newTimeInt)
        # --Done
        try:
            mosh.modInfos.refreshFile(fileName)
            self.SetFile(fileName)
        except mosh.Tes3Error:
            guidialog.ErrorMessage(self, _('File corrupted on save!'))
            self.SetFile(None)
        singletons.modList.Refresh()
        if warning: guidialog.ErrorMessage(None,
                                            _('Unable to proceed with your changes. No changes have been saved.\n\n'
                                              u'This has probably happened because some (or one) of your master files in the mod\'s master list contain unknown characters. '
                                              u'Try renaming the target master files before adding them in the master list.'))

    def OnCancel(self, event):
        """On cancel."""
        self.SetFile(self.modInfo.name)


# ------------------------------------------------------------------------------

class BSArchives(wx.Window):  # Polemos:
    """"BSA registration TAB."""

    def __init__(self, parent):
        """Init."""
        wx.Window.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        # --Singleton
        singletons.BSArchives = self
        self.Archives = BSArchivesList(self)
        # --Data
        self.modInfo = None
        self.edited = False
        textWidth = 200
        # --Sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(self.Archives, 1, wx.EXPAND)


# ------------------------------------------------------------------------------

class ModPanel(
    gui.NotebookPanel):  # Polemos: OpenMW/TES3mp support, fixes and BSA/Details mini TAB for BSA reg, adjustable width.
    """Mods/Plugins Panel."""

    def __init__(self, parent):
        """Init."""
        wx.Panel.__init__(self, parent, -1)
        self.openmw = conf.settings['openmw']
        if True:  # Content
            # Panels
            self.main = wx.SplitterWindow(self, wx.ID_ANY, DPOS, DSIZE, wx.SP_3D | wx.SP_LIVE_UPDATE)
            self.leftPanel = wx.Panel(self.main, wx.ID_ANY, DPOS, DSIZE, wx.TAB_TRAVERSAL)
            self.rightPanel = wx.Panel(self.main, wx.ID_ANY, DPOS, DSIZE, wx.TAB_TRAVERSAL)
            # Main Window
            self.Adv_book = wx.Notebook(self.rightPanel, wx.ID_ANY, DPOS, DSIZE, 0)
            self.modDetails = ModDetails(self.Adv_book)
            self.BSArchives = BSArchives(self.Adv_book)
            # Globals
            singletons.modList = ModList(self.leftPanel)
            singletons.modList.details = self.modDetails
            # Mini Tabs
            self.Adv_book.AddPage(singletons.modList.details, _('Mod Details'), True)
            self.Adv_book.AddPage(singletons.BSArchives, _('BSA Archives'), False)
        if True:  # Layout
            self.modDetails.Fit()
            self.BSArchives.Fit()
            self.main.SetMinimumPaneSize(200)
            self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.leftSizer.Add(singletons.modList, 1, wx.GROW)
            self.leftPanel.SetSizer(self.leftSizer)
            self.leftPanel.Layout()
            self.leftSizer.Fit(self.leftPanel)
            rightSizer = wx.BoxSizer(wx.HORIZONTAL)
            rightSizer.Add(self.Adv_book, 0, wx.EXPAND)
            self.rightPanel.SetSizer(rightSizer)
            rightSizer.Fit(self.rightPanel)
            self.rightPanel.Layout()
            self.savedSash = conf.settings['mash.mods.sashPos']
            self.main.SplitVertically(self.leftPanel, self.rightPanel, self.savedSash)
            mainSizer = wx.BoxSizer(wx.HORIZONTAL)
            mainSizer.Add(self.main, 1, wx.EXPAND | wx.ALL, 0)
            self.SetSizer(mainSizer)
            self.Layout()
        if True:  # Sash data
            self.origSize = conf.settings['mash.sash.window.size']
            self.rightSash = conf.settings['mash.sash.window.size'][0] - self.savedSash
            self.maxSash = conf.settings['mash.max.sash']
        if True:  # Events
            self.Bind(wx.EVT_SIZE, self.OnSize)
            self.main.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged)

    def SetStatusCount(self):
        """Sets mod count in last field."""
        try:
            if not self.openmw:  # Polemos: Regular Morrowind support
                text = _('Mods: %d/%d | BSAs: %d/%d') % (len(mosh.mwIniFile.loadFiles),
                                                          len(mosh.modInfos.data),
                                                          singletons.BSArchives.Archives.active_bsa,
                                                          len(singletons.BSArchives.Archives.items))
            if self.openmw:  # Polemos: OpenMW/TES3mp support
                text = _('Plugins: %d/%d | BSAs: %d/%d') % (len(mosh.mwIniFile.loadFiles), len(mosh.modInfos.data),
                                                             len(mosh.mwIniFile.get_active_bsa()),
                                                             len(singletons.BSArchives.Archives.items))
        except:
            text = _('Config file is corrupt.')
        singletons.statusBar.SetStatusField(text, 2)

    def OnSashChanged(self, event):  # Polemos
        """On changing sash size."""
        self.rightSash = self.GetSize()[0] - self.main.GetSashPosition()
        if self.rightSash > self.maxSash:
            self.rightSash = self.maxSash
            self.main.SetSashPosition(self.GetSize()[0] - self.maxSash)
        conf.settings['mash.mods.sashPos'] = self.main.GetSashPosition()

    def OnSize(self, event):  # Polemos: Sash relative sizing and saving.
        """On changing window size."""
        wx.Window.Layout(self)
        singletons.modList.Layout()
        self.modDetails.Layout()
        conf.settings['mash.sash.window.size'] = self.GetSize()
        curSash = conf.settings['mash.sash.window.size'][0] - self.rightSash
        self.main.SetSashPosition(curSash)
        conf.settings['mash.mods.sashPos'] = self.main.GetSashPosition()


# ------------------------------------------------------------------------------

class SaveList(gui.List):  # Polemos: OpenMW support, additions, more...
    # --Class Data
    mainMenu = []  # --Column menu
    itemMenu = []  # --Single item menu
    last_item = []  # Alphabetical search by key press
    timeChk = False  # Speed list fix

    def __init__(self, parent):
        self.openMW = conf.settings['openmw']
        # --Columns
        if not self.openMW:  # Morrowind Support
            self.cols = conf.settings['mash.saves.cols']
            self.colAligns = conf.settings['mash.saves.colAligns']
            self.colReverse = conf.settings.getChanged('mash.saves.colReverse')
            self.colWidths = conf.settings['mash.saves.colWidths']
        if self.openMW:  # OpenMW Support
            self.cols = conf.settings['OpenMW.saves.cols']
            self.colAligns = conf.settings['OpenMW.saves.colAligns']
            self.colReverse = conf.settings.getChanged('OpenMW.saves.colReverse')
            self.colWidths = conf.settings['OpenMW.saves.colWidths']
        self.colNames = conf.settings['mash.colNames']
        # --Data/Items
        self.data = data = mosh.saveInfos
        self.details = None  # --Set by panel
        self.sort = conf.settings['mash.saves.sort'] if not self.openMW else conf.settings['OpenMW.saves.sort']
        # --Links
        self.mainMenu = SaveList.mainMenu
        self.itemMenu = SaveList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT))
        # --Image List
        checkboxesIL = self.checkboxes.GetImageList()
        self.list.SetImageList(checkboxesIL, wx.IMAGE_LIST_SMALL)
        # --Events
        wx.EVT_LIST_ITEM_SELECTED(self, self.listId, self.OnItemSelected)
        self.list.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def Refresh(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified files."""
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files: self.PopulateItem(file, selected=selected)
        singletons.saveDetails.SetFile(detail)

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        fileName = self.items[itemDex]
        fileInfo = self.data[fileName]
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            if col == 'File':
                value = fileName
            elif col == 'Modified':
                value = formatDate(fileInfo.mtime)
            elif col == 'Size':
                value = '%sKB' % formatInteger(fileInfo.size // 1024)
            elif col == 'Save Name' and fileInfo.tes3:
                value = fileInfo.tes3.hedr.description
            elif col == 'Player' and fileInfo.tes3 and fileInfo.tes3.gmdt:
                value = fileInfo.tes3.gmdt.playerName
            elif col == 'Cell' and fileInfo.tes3 and fileInfo.tes3.gmdt:
                value = fileInfo.tes3.gmdt.curCell
            else:
                value = ''
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --Image
        status = fileInfo.getStatus()
        self.list.SetItemImage(itemDex, self.checkboxes.Get(status, False))
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):
        (col, reverse) = self.GetSortSettings(col, reverse)
        if not self.openMW:
            conf.settings['mash.saves.sort'] = col
        else:
            conf.settings['openMW.saves.sort'] = col
        data = self.data
        # --Start with sort by name
        self.items.sort(key=lambda x: x.casefold())
        if col == 'File':
            pass  # --Done by default
        elif col == 'Modified':
            self.items.sort(key=lambda x: data[x].mtime)
        elif col == 'Size':
            self.items.sort(key=lambda x: data[x].size)
        elif col == 'Save Name':
            self.items.sort(key=lambda x: data[x].tes3.hedr.description.casefold())
        # elif col == 'Status':
        #    self.items.sort(key=lambda x: data[x].getStatus())
        elif col == 'Player':
            self.items.sort(key=lambda x: data[x].tes3.gmdt.playerName.casefold())
        elif col == 'Cell':
            self.items.sort(key=lambda x: data[x].tes3.gmdt.curCell.casefold())
        else:
            raise MashError(col)
        # --Ascending
        if reverse: self.items.reverse()

    def OnColumnResize(self, event):
        """Column Resize"""
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        if not self.openMW:
            conf.settings.setChanged('mash.saves.colWidths')
        else:
            conf.settings.setChanged('openMW.saves.colWidths')

    def timeSelChk(self, event):  # Polemos
        """Check time conditions to show item details."""
        self.timer.Stop()
        if self.timeChk:
            self.details.SetFile(self.timeChk)
            if singletons.journalBrowser: singletons.journalBrowser.SetSave(self.timeChk)
        self.timeChk = False

    def OnItemSelected(self, event=None):  # Polemos
        """Time buffer for showing item details."""
        if not singletons.saveList.details.master_btn.IsEnabled(): singletons.saveList.details.master_btn.Enable()
        if not self.timeChk:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.timeSelChk, self.timer)
            self.timer.Start(50)
        self.timeChk = self.items[event.Index]

    def OnKeyDown(self, event):  # Polemos: added delete item on DEL
        fmap = {
            65: self.OnAPress,
            385: self.delOnChar,
            127: self.delOnChar
        }
        kc = event.GetKeyCode()
        if kc in fmap:
            fmap[kc](event)
        else:
            self.OnGenKeys(chr(event.GetKeyCode()))  # Polemos: Alpha, Beta, search...

    def delOnChar(self, event):  # Polemos
        """Deletes selected item."""
        self.DeleteSelected()
        singletons.mashFrame.RefreshData()

    def OnGenKeys(self, letter):  # Polemos: Was missing from Yakoby's version. Faster than skipping events
        """Selects unicode items by their first letter."""
        while True:
            for x in self.items:
                if x.startswith(letter) or x.startswith(letter.lower()):
                    if x not in self.last_item:
                        self.ClearSelected()
                        self.SelectItems(x)
                        self.SetItemFocus(x)
                        self.last_item.append(x)
                        return
            try:
                del self.last_item[0]
            except:
                return

    def OnAPress(self, event):  # Polemos: added CTRL+A to select all which was missing.
        if event.ControlDown():
            self.SelectAll()
        else:
            self.OnGenKeys('A')


# -------------------------------------------------------------------------

class SaveDetails(
    wx.Window):  # Polemos: fixed old bugs, refactored, optimized, plus: every change produces a dialog. Dialogs are saved with "ok", bypassing "Save" button.
    """Savefile details panel."""

    def __init__(self, parent):
        """Init."""
        wx.Window.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        # --Singleton
        singletons.saveDetails = self
        # --Data
        self.openmw = conf.settings['openmw']
        self.maxSash = conf.settings['mash.max.sash']
        readOnlyColour = self.GetBackgroundColour()
        self.saveInfo = None
        self.edited = False
        if True:  # Content
            # --File/Version Static Text
            saveText = wx.StaticText(self, -1, _("Morrowind Save File"))
            self.version = wx.StaticText(self, -1, 'v0.0')
            # --File Name
            self.file = wx.TextCtrl(self, wx.NewId(), "", size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.file.SetMaxLength(256)
            # --Save Name
            self.saveName = wx.TextCtrl(self, wx.NewId(), "", size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.saveName.SetMaxLength(32)
            # --Player Name
            self.playerName = wx.TextCtrl(self, wx.NewId(), "", size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.playerName.SetBackgroundColour(readOnlyColour)
            # --Cell
            self.curCell = wx.TextCtrl(self, wx.NewId(), "", size=(self.maxSash, -1), style=wx.TE_READONLY)
            self.curCell.SetBackgroundColour(readOnlyColour)
            # --Picture
            self.picture = balt.Picture(self, self.maxSash, 128)
            # --Masters
            singletons.savesMastersList = self.masters = MasterList(self, None)
            # Master Menu Button
            self.master_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['master.menu'].GetBitmap(), DPOS,
                                              DSIZE, ADRW)
            self.master_btn.SetBitmapPressed(singletons.images['master.menu'].GetBitmap())
            self.master_btn.SetBitmapCurrent(singletons.images['master.menu.onhov'].GetBitmap())
            self.master_btn.SetToolTip(wx.ToolTip(_('Masters Menu')))
            self.master_btn.Disable()
            # Buttons
            self.save = wx.Button(self, wx.ID_SAVE, size=wx.Size(90, 21))
            self.cancel = wx.Button(self, wx.ID_CANCEL, size=wx.Size(90, 21))
            self.save.Disable()
            self.cancel.Disable()
        if True:  # Theming
            # e.g: self.restore_btn.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
            pass
        if True:  # Layout
            sizer_h0 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_h0.AddMany([(saveText, 0, wx.TOP, 4), ((0, 0), 1), (self.version, 0, wx.TOP | wx.RIGHT, 4)])
            sizer_h1 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_h1.AddMany([((0, 0), 1), (self.save, 0, wx.RIGHT, 4), (self.master_btn, 0, wx.CENTER, 4),
                              (self.cancel, 0, wx.LEFT, 4), ((0, 0), 1)])
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(sizer)
            sizer.AddMany([(sizer_h0, 0, wx.EXPAND), self.file, self.saveName, self.playerName, self.curCell,
                           (self.picture, 0, wx.TOP | wx.BOTTOM, 4), (self.masters, 1, wx.EXPAND),
                           (sizer_h1, 0, wx.EXPAND | wx.TOP, 4)])
        if True:  # Events
            self.master_btn.Bind(wx.EVT_BUTTON, self.MasterMenu)
            wx.EVT_LEFT_DOWN(self.file, self.OnEditFile)
            wx.EVT_RIGHT_DOWN(self.file, self.OnEditFile)
            wx.EVT_LEFT_DOWN(self.saveName, self.OnEditSaveName)
            wx.EVT_RIGHT_DOWN(self.saveName, self.OnEditSaveName)
            wx.EVT_LEFT_DOWN(self.playerName, self.no_action_po)
            wx.EVT_RIGHT_DOWN(self.playerName, self.no_action_po)
            wx.EVT_LEFT_DOWN(self.curCell, self.no_action_po)
            wx.EVT_RIGHT_DOWN(self.curCell, self.no_action_po)
            wx.EVT_BUTTON(self, wx.ID_SAVE, self.OnSave)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

    def MasterMenu(self, event):  # Polemos
        """Masters button menu."""
        pos = self.master_btn.GetScreenPosition()
        gui.List.DoColumnMenu(self.masters, pos)

    def no_action_po(self, pita=None):  # Polemos
        """No action def-ending."""
        pass

    def modify_dialog_po(self, field, failsafe_po=False):  # Polemos
        """Dialog for editing fields."""
        if field == 'name':
            current_po = self.saveNameStr
            msg_po = u'Enter a new name (32 characters max):'
            caption_po = u'Rename Save'
            max_char_po = 32
        elif field == 'filename':
            current_po = self.fileStr
            msg_po = u'Select a new filename:'
            caption_po = u'Rename Save'
            max_char_po = 200
        else:
            failsafe_po = True
        dialog = guidialog.MaxCharDialog(caption_po, max_char_po, current_po, msg_po, self)
        if failsafe_po:
            new_po = current_po
        else:
            new_po = dialog.GetValue()
        return new_po, current_po

    def SetFile(self, fileName='SAME'):
        """Set file to be viewed."""
        # --Reset?
        if fileName == 'SAME':
            if not self.saveInfo or self.saveInfo.name not in mosh.saveInfos:
                fileName = None
            else:
                fileName = self.saveInfo.name
        # --Null fileName?
        if not fileName:
            saveInfo = self.saveInfo = None
            self.fileStr = ''
            self.saveNameStr = ''
            self.playerNameStr = ''
            self.curCellStr = ''
            self.versionStr = ''
            self.picData = None
        # --Valid fileName?
        else:
            saveInfo = self.saveInfo = mosh.saveInfos[fileName]
            # --Remember values for edit checks
            self.fileStr = saveInfo.name
            self.saveNameStr = saveInfo.tes3.hedr.description
            self.playerNameStr = saveInfo.tes3.gmdt.playerName
            self.curCellStr = saveInfo.tes3.gmdt.curCell
            self.versionStr = 'v%0.1f' % (saveInfo.tes3.hedr.version,)
            self.picData = self.saveInfo.getScreenshot()
        # --Set Fields
        self.file.SetValue(self.fileStr)
        self.saveName.SetValue(self.saveNameStr)
        self.playerName.SetValue(self.playerNameStr)
        self.curCell.SetValue(self.curCellStr)
        self.version.SetLabel(self.versionStr)
        self.masters.SetFileInfo(saveInfo)
        # --Picture
        if not self.picData:
            self.picture.SetBitmap(None)
        else:
            image = wx.EmptyImage(128, 128)
            image.SetData(self.picData)
            image = image.Scale(171, 128)
            self.picture.SetBitmap(image.ConvertToBitmap())
        # --Edit State
        self.edited = 0
        self.save.Disable()
        self.cancel.Disable()

    def SetEdited(self):
        """Mark as edited."""
        self.edited = True
        self.save.Enable()
        self.cancel.Enable()

    def SetEdited_save_po(self):  # Polemos
        """Save button bypass for all dialogs."""
        self.edited = True
        self.OnSave(self)

    def OnBrowser(self, event):
        """Event: Clicked Journal Browser button."""
        if not singletons.journalBrowser:
            JournalBrowser().Show()
            conf.settings['mash.journal.show'] = True
        if self.saveInfo:
            singletons.journalBrowser.SetSave(self.saveInfo.name)
        singletons.journalBrowser.Raise()

    def OnTextEdit(self, event):
        """Event: Editing file or save name text."""
        if self.saveInfo and not self.edited:
            if (self.fileStr != self.file.GetValue()) or (self.saveNameStr != self.saveName.GetValue()):
                self.SetEdited()
        event.Skip()

    def OnEditFile(self, event):  # Polemos: Redirect to dialog and more.
        """Event: Finished editing file name."""
        if not self.saveInfo: return
        fileStr, old_file_po = self.modify_dialog_po('filename')
        if fileStr == old_file_po: return
        # --Extension Changed?
        if fileStr[-4:].lower() != self.fileStr[-4:].lower():
            guidialog.ErrorMessage(self, u"Incorrect file extension: " + fileStr[-3:])
            self.file.SetValue(self.fileStr)
        # --Else file exists?
        elif os.path.exists(os.path.join(self.saveInfo.dir, fileStr)):
            guidialog.ErrorMessage(self, u"File %s already exists." % (fileStr,))
            self.file.SetValue(self.fileStr)
        # --Okay?
        else:
            self.fileStr = fileStr
            self.SetEdited_save_po()

    def OnEditSaveName(self, event):  # Polemos: Redirect to dialog and more.
        """Event: Finished editing save name."""
        if not self.saveInfo: return
        saveNameStr, old_name_po = self.modify_dialog_po('name')
        if saveNameStr != old_name_po:
            self.saveNameStr = saveNameStr
            self.SetEdited_save_po()

    def OnSave(self, event):
        """Event: Clicked Save button."""
        saveInfo = self.saveInfo
        # --Change Tests
        changeName = (self.fileStr != saveInfo.name)
        changeHedr = (self.saveNameStr != saveInfo.tes3.hedr.description)
        changeMasters = self.masters.edited
        # --Backup
        saveInfo.makeBackup()
        prevMTime = saveInfo.mtime
        # --Change Name?
        if changeName:
            (oldName, newName) = (saveInfo.name, self.fileStr.strip())
            singletons.saveList.items[singletons.saveList.items.index(oldName)] = newName
            mosh.saveInfos.rename(oldName, newName)
        # --Change hedr?
        if changeHedr:
            saveInfo.tes3.hedr.description = self.saveNameStr.strip()
            saveInfo.tes3.hedr.changed = True
            saveInfo.writeHedr()
        # --Change masters?
        warning = False
        if changeMasters:
            newMasters = self.masters.GetNewMasters()
            (modMap, objMaps) = self.masters.GetMaps()
            # --Create and use FileRefs
            progress = None
            try:
                progress = guidialog.ProgressDialog(_('Saving'))
                fileRefs = mosh.FileRefs(saveInfo, progress=progress)
                progress.setBaseScale(0.0, 0.67)
                fileRefs.load()
                progress(1.0, _('Remap Masters'))
                fileRefs.remap(newMasters, modMap, objMaps)
                progress.setBaseScale(0.67, 0.33)
                fileRefs.safeSave()
            except:
                warning = True
            finally:
                if progress is not None: progress = progress.Destroy()
        # --Restore Date?
        if (changeHedr or changeMasters):
            saveInfo.setMTime(prevMTime)
        # --Done
        try:
            mosh.saveInfos.refreshFile(saveInfo.name)
            self.SetFile(self.saveInfo.name)
        except mosh.Tes3Error:
            guidialog.ErrorMessage(self, _('File corrupted on save!'))
            self.SetFile(None)
        self.SetFile(self.saveInfo.name)
        singletons.saveList.Refresh(saveInfo.name)
        if warning: guidialog.ErrorMessage(None,
                                            _('Unable to proceed with your changes. No changes have been saved.\n\n'
                                              u'This has probably happened because some (or one) of your master files in the save\'s master list contain unknown characters. '
                                              u'Try renaming the target master files before adding them in the master list.'))

    def OnCancel(self, event):
        """Event: Clicked cancel button."""
        self.SetFile(self.saveInfo.name)


# ------------------------------------------------------------------------------

class SavePanel(gui.NotebookPanel):  # Polemos: refactored, adjustable width.
    """Saves Panel."""

    def __init__(self, parent):
        """Init."""
        wx.Panel.__init__(self, parent, -1)
        self.openmw = conf.settings['openmw']
        if True:  # Content
            # Panels
            self.main = wx.SplitterWindow(self, wx.ID_ANY, DPOS, DSIZE, wx.SP_3D | wx.SP_LIVE_UPDATE)
            self.leftPanel = wx.Panel(self.main, wx.ID_ANY, DPOS, DSIZE, wx.TAB_TRAVERSAL)
            self.rightPanel = wx.Panel(self.main, wx.ID_ANY, DPOS, DSIZE, wx.TAB_TRAVERSAL)
            # Main Window
            self.SaveList = SaveList(self.leftPanel)
            self.SaveDetails = SaveDetails(self.rightPanel)
            # Globals
            singletons.saveList = self.SaveList
            singletons.saveList.details = self.SaveDetails
        if True:  # Layout
            self.SaveList.Fit()
            self.SaveDetails.Fit()
            self.main.SetMinimumPaneSize(200)
            self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.leftSizer.Add(singletons.saveList, 1, wx.GROW)
            rightSizer = wx.BoxSizer(wx.HORIZONTAL)
            rightSizer.Add(singletons.saveList.details, 0, wx.EXPAND)
            self.leftPanel.SetSizer(self.leftSizer)
            self.rightPanel.SetSizer(rightSizer)
            self.leftPanel.Layout()
            self.rightPanel.Layout()
            self.leftSizer.Fit(self.leftPanel)
            rightSizer.Fit(self.rightPanel)
            self.savedSash = conf.settings['mash.saves.sashPos']
            self.main.SplitVertically(self.leftPanel, self.rightPanel, self.savedSash)
            mainSizer = wx.BoxSizer(wx.HORIZONTAL)
            mainSizer.Add(self.main, 1, wx.EXPAND | wx.ALL, 0)
            self.SetSizer(mainSizer)
            self.Layout()
        if True:  # Sash data
            self.origSize = conf.settings['mash.sash.window.size']
            self.rightSash = conf.settings['mash.sash.window.size'][0] - self.savedSash
            self.maxSash = conf.settings['mash.max.sash']
        if True:  # Events
            wx.EVT_SIZE(self, self.OnSize)
            self.main.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged)

    def SetStatusCount(self):
        """Sets mod count in last field."""
        text = _('Saves: %d') % (len(mosh.saveInfos.data))
        singletons.statusBar.SetStatusField(text, 2)

    def OnSashChanged(self, event):  # Polemos
        """On changing sash size."""
        self.rightSash = self.GetSize()[0] - self.main.GetSashPosition()
        if self.rightSash > self.maxSash:
            self.rightSash = self.maxSash
            self.main.SetSashPosition(self.GetSize()[0] - self.maxSash)
        conf.settings['mash.saves.sashPos'] = self.main.GetSashPosition()

    def OnSize(self, event=None):
        wx.Window.Layout(self)
        singletons.saveList.Layout()
        self.SaveDetails.Layout()
        conf.settings['mash.sash.window.size'] = self.GetSize()
        curSash = conf.settings['mash.sash.window.size'][0] - self.rightSash
        self.main.SetSashPosition(curSash)
        conf.settings['mash.saves.sashPos'] = self.main.GetSashPosition()


# ------------------------------------------------------------------------------

class InstallersList(balt.Tank, gui.ListDragDropMixin):  # Polemos: refactored, optimised, fixes, addons.
    """The list of installed packages. Subclass of balt.Tank to allow reordering etal."""

    def __init__(self, parent, data, icons=None, mainMenu=None, itemMenu=None, details=None, id=-1,
                 style=(wx.LC_REPORT | wx.LC_SINGLE_SEL)):
        """Init."""
        balt.Tank.__init__(self, parent, data, icons, mainMenu, itemMenu, details, id, style | wx.LC_EDIT_LABELS)
        gui.ListDragDropMixin.__init__(self, self.gList)
        singletons.gInstList = self
        # Events
        self.gList.Bind(wx.EVT_CHAR, self.OnChar)
        self.gList.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)

    def chkSort(self):  # Polemos
        """Check column sorting."""
        if conf.settings['mash.installers.sort'] != 'Order':
            guidialog.ErrorMessage(self.GetParent(),
                                    _('The Installers list must be sorted by "Load Order" to\n enable Keyboard or Mouse based sorting.'))
            return False
        if conf.settings['mash.installers.sortProjects'] or conf.settings['mash.installers.sortActive']:
            guidialog.ErrorMessage(self.GetParent(),
                                    _('The Installers list must not be "Sort by Active" or "Projects first" to enable drag and drop.'))
            return False
        return True

    def chkReversed(self):
        """Check if list is reversed."""
        if not self.isReversed: return True
        guidialog.ErrorMessage(self.GetParent(),
                                _('The Installers list is reversed. Only Keyboard based sorting is allowed (Ctrl+Arrows).'))
        return False

    def OnDrop(self, names, toIdx):
        """Implementing support for drag and drop of installers"""
        # Notify user if drag and drop is allowed
        if not self.chkSort(): return
        if not self.chkReversed(): return
        # Do the job
        self.data.moveArchives([bolt.Path(name) for name in names], toIdx)
        self.data.refresh(what='I')
        self.RefreshUI()

    def OnChar(self,
               event):  # Polemos: Added del => delete, CTRL + A/b +> de/select all, check if ordered by "Load Order", optimized
        """Character events."""
        # CTRL + UP, CTRL + DOWN
        if event.ControlDown() and event.GetKeyCode() in (wx.WXK_UP, wx.WXK_DOWN):
            if not self.chkSort(): return
            selected = self.GetSelected()
            if len(selected) < 1: return
            orderKey = lambda x: self.data.data[x].order
            maxPos = max(self.data.data[x].order for x in self.data.data)
            if event.GetKeyCode() == wx.WXK_DOWN:  # Down
                moveMod = 1 if not self.isReversed else -1
                visibleIndex = self.GetIndex(sorted(self.GetSelected(), key=orderKey)[-1]) + 2
            else:  # Up
                moveMod = -1 if not self.isReversed else 1
                visibleIndex = self.GetIndex(sorted(self.GetSelected(), key=orderKey)[0]) - 2
            for thisFile in sorted(self.GetSelected(), key=orderKey, reverse=(moveMod != -1)):
                newPos = self.data.data[thisFile].order + moveMod
                if newPos < 0 or maxPos < newPos: break
                self.data.moveArchives([thisFile], newPos)
            self.data.refresh(what='I')
            self.RefreshUI()
            # clamp between 0 and maxpos
            visibleIndex = max(0, min(maxPos, visibleIndex))
            self.gList.EnsureVisible(visibleIndex)
        # ENTER - Open selected Installer
        elif event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if len(self.GetSelected()):
                path = self.data.dir.join(self.GetSelected()[0])
                if path.exists(): path.start()
        # Del - Delete Installer
        elif event.GetKeyCode() == wx.WXK_DELETE:
            if len(self.GetSelected()): self.DeleteSelected()
        # CTRL + A - Select all items
        elif event.GetKeyCode() == wx.WXK_CONTROL_A:
            [self.gList.Select(x) for x in range(self.gList.GetItemCount())]
        # CTRL + D - Deselect all items
        elif event.GetKeyCode() == wx.WXK_CONTROL_D:
            [self.gList.Select(x, 0) for x in range(self.gList.GetItemCount())]
        # Else skip event
        else:
            event.Skip()

    def OnDClick(self, event):
        """Double click, open the installer."""
        (hitItem, hitFlag) = self.gList.HitTest(event.GetPosition())
        if hitItem < 0: return
        path = self.data.dir.join(self.GetItem(hitItem))
        if path.exists(): path.start()


# ------------------------------------------------------------------------------

class InstallersPanel(SashTankPanel):  # Polemos: Refactored, changes, store/restore order, additions.
    """Panel for InstallersTank."""
    mainMenu = Links()
    itemMenu = Links()

    def __init__(self, parent):
        """Init."""
        singletons.gInstallers = self
        data = mosh.InstallersData()
        SashTankPanel.__init__(self, data, parent)
        left, right = self.left, self.right
        btnPanel = wx.Panel(right, wx.ID_ANY, DPOS, DSIZE, 0)
        self.instTimer = wx.Timer(self)
        self.instWatch = wx.StopWatch()
        self.instRefr()
        if True:  # Content
            self.gList = InstallersList(left, data, installercons,
                                        InstallersPanel.mainMenu, InstallersPanel.itemMenu, details=self,
                                        style=wx.LC_REPORT)
            self.gList.SetSizeHints(100, 100)
            self.DragAndDrop()  # Polemos: Enable file Drag and Drop
            # Buttons/Status Bar
            oStatus = _('Refreshing...') if conf.settings['mash.installers.enabled'] else _('Deactivated...')
            self.gPackage = wx.StaticText(btnPanel, -1, oStatus, style=wx.TE_READONLY | wx.NO_BORDER)
            self.statusLastMsg = self.gPackage.GetLabel()
            self.statusChanged = False
            self.rPackBtn = wx.BitmapButton(btnPanel, wx.ID_ANY, singletons.images['mod.open'].GetBitmap(), DPOS, DSIZE,
                                            0 | ADRW)
            self.rPackBtn.SetBitmapPressed(singletons.images['mod.open'].GetBitmap())
            self.rPackBtn.SetBitmapCurrent(singletons.images['mod.open.onhov'].GetBitmap())
            self.rPackBtn.SetToolTip(wx.ToolTip(_('Restore Order')))
            self.sPackBtn = wx.BitmapButton(btnPanel, wx.ID_ANY, singletons.images['mod.save'].GetBitmap(), DPOS, DSIZE,
                                            0 | ADRW)
            self.sPackBtn.SetBitmapPressed(singletons.images['mod.save'].GetBitmap())
            self.sPackBtn.SetBitmapCurrent(singletons.images['mod.save.onhov'].GetBitmap())
            self.sPackBtn.SetToolTip(wx.ToolTip(_('Save Order')))
            self.btnList = [(self.gPackage, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                            (self.rPackBtn, 0, wx.ALIGN_CENTER_VERTICAL, 5),
                            (self.sPackBtn, 0, wx.ALIGN_CENTER_VERTICAL, 5)]
            # Info Tabs
            self.gNotebook = wx.Notebook(right, style=wx.NB_MULTILINE)
            self.infoPages = []
            infoTitles = (
                ('gGeneral', _('General')),
                ('gMatched', _('Matched')),
                ('gMissing', _('Missing')),
                ('gMismatched', _('Mismatched')),
                ('gConflicts', _('Conflicts')),
                ('gUnderrides', _('Underridden')),
                ('gDirty', _('Dirty')),
                ('gSkipped', _('Skipped')),)
            for name, title in infoTitles:
                gPage = wx.TextCtrl(self.gNotebook, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
                                    name=name)
                self.gNotebook.AddPage(gPage, title)
                self.infoPages.append([gPage, False])
            self.gNotebook.SetSelection(conf.settings['mash.installers.page'])
            # Sub-Intallers
            self.gSubList = wx.CheckListBox(right, -1)
            # Espms
            self.espms = []
            self.gEspmList = wx.CheckListBox(right, -1)
            # Comments
            self.gCommentstxt = staticText(right,
                                           _('You may add comments (for the selected Installer) in the field below:'))
            self.gComments = wx.TextCtrl(right, -1, style=wx.TE_MULTILINE)
        if True:  # Layout
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany(self.btnList)
            btnPanel.SetSizer(btnSizer)
            btnPanel.Layout()
            btnSizer.Fit(btnPanel)
            right.SetSizer(vSizer(
                (btnPanel, 0, wx.EXPAND, 5),
                (self.gNotebook, 2, wx.GROW | wx.TOP, 0),
                (hSizer(
                    (vSizer(
                        (staticText(right, _('Sub-Packages:')),),
                        (self.gSubList, 1, wx.GROW | wx.TOP, 4),
                    ), 1, wx.GROW),
                    (vSizer(
                        (staticText(right, _('Esp/m Filter:')),),
                        (self.gEspmList, 1, wx.GROW | wx.TOP, 4),
                    ), 1, wx.GROW | wx.LEFT, 2),
                ), 1, wx.GROW | wx.TOP, 4),
                (self.gCommentstxt, 0, wx.TOP, 4),
                (self.gComments, 1, wx.GROW | wx.TOP, 4), ))
            wxadv.LayoutAlgorithm().LayoutWindow(self, right)
            self.gComments.Disable()
        if True:  # Theming
            self.gPackage.SetBackgroundColour(self.GetBackgroundColour())
            btnPanel.SetBackgroundColour(self.GetBackgroundColour())
            [x[0].Disable() for x in self.btnList]
        if True:  # Events
            self.Bind(wx.EVT_TIMER, self.onUpdate, self.instTimer)
            self.instTimer.Start(300)
            self.rPackBtn.Bind(wx.EVT_BUTTON, self.onInstOrdR)
            self.sPackBtn.Bind(wx.EVT_BUTTON, self.onInstOrdS)
            self.gList.gList.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.DoColumnMenu)
            self.gNotebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnShowInfoPage)
            [x[0].Bind(wx.EVT_ENTER_WINDOW, self.hoverInCtrl) for x in self.infoPages]
            singletons.gInstList.gList.Bind(wx.EVT_ENTER_WINDOW, self.hoverInCtrl)
            self.gSubList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckSubItem)
            self.gEspmList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckEspmItem)
            self.Bind(wx.EVT_SIZE, self.OnSize)

    def onUpdate(self, event):  # Polemos
        """Timer events."""
        if singletons.gInstList.gList.droppedItms:  # Drag and Drop
            toDrop = singletons.gInstList.gList.droppedItms
            singletons.gInstList.gList.droppedItms = False
            self.importDraggedItms(toDrop)
        if conf.settings['mash.page'] == 1:  # Installers page
            if conf.settings['mash.installers.enabled']:  # Buttons disable/enable
                [x[0].Enable() for x in self.btnList if not x[0].IsEnabled()]
            else:
                [x[0].Disable() for x in self.btnList if x[0].IsEnabled()]
            if self.statusChanged:  # Messages, time to stay
                if self.instWatch.Time() > 4000:
                    self.statusChanged = False
                    self.instWatch.Pause()
                    self.gPackage.SetLabel(self.statusLastMsg)
        else:
            self.gPackage.SetLabel(self.statusLastMsg)  # When changing Tab

    def importDraggedItms(self, fPaths):  # Polemos
        """Import Drag and Dropped files to installers dir."""
        if guidialog.askdialog(self,
                                _('Import Installers?\n\nClick "Yes" to copy the dragged and dropped installers into the'
                                  u' "Installers" directory.\nClick "No" to cancel the operation.'),
                                _('Import package(s)?')) == wx.ID_NO: return
        actions = 0
        for sourcePath in fPaths:
            fpath, fname = ntpath.split(sourcePath)
            if os.path.isfile(sourcePath):  # Importing a file
                if os.path.isfile(os.path.join(conf.settings['sInstallersDir'], fname)):
                    if guidialog.askdialog(self, _('A file with the same name already '
                                                    u'exists. Overwrite "%s"?' % fname),
                                            _('Overwrite file?')) == wx.ID_NO: continue
                # Copy/overwrite file to destination
                actions += 1
                try:
                    shutil.copyfile(sourcePath, os.path.join(conf.settings['sInstallersDir'], fname))
                except shutil.Error:
                    guidialog.ErrorMessage(None, _('Operation aborted:'
                                                    u' You cannot import a package from Installers directory on the Installers directory.'))
                except IOError:
                    guidialog.ErrorMessage(None,
                                            _('Operation failed: Access denied. Unable to write on the destination.'))
                    return
            elif os.path.isdir(sourcePath):  # Importing a directory
                if os.path.isdir(os.path.join(conf.settings['sInstallersDir'], fname)):
                    if guidialog.askdialog(self, _('A directory with the same name already '
                                                    u'exists. Overwrite "%s"?' % fname),
                                            _('Overwrite directory?')) == wx.ID_NO: continue
                # Copy/overwrite directory to destination
                actions += 1
                mosh.CopyTree(self, sourcePath, os.path.join(conf.settings['sInstallersDir'], fname))
        # Refresh GUI
        if actions:
            singletons.gInstallers.refreshed = False
            singletons.gInstallers.fullRefresh = False
            singletons.gInstallers.OnShow()

    def onInstOrdR(self, event):  # Polemos
        """On restoring installers order."""
        # Open backup browser
        BckList = mosh.GetBckList('paksnap').bckList
        backupFile = guidialog.SimpleListDialog(self, BckList, _('Choose a backup to restore:')).Selection
        if backupFile is None: return
        # Installers data
        instData = mosh.LoadModOrder(backupFile, fname='paksnap').modData
        if not instData: return
        # Apply order
        for index, archive in enumerate([x[1] for x in instData]):
            self.data[archive].order = index
        singletons.gInstallers.data.setChanged()
        singletons.gInstallers.data.refresh(what='N')
        singletons.gInstList.RefreshUI()
        # Notify
        self.instStatusCh(_('Restored Installers Order...'))
        # Re-install packages?
        if guidialog.askdialog(self,
                                _('Installers order has been Restored. Re-install your packages using your restored order?\n\n'
                                  u'Your packages need to be re-installed to sync the overriding conflicts with the new ordering.\n\nIf you click "Yes", then Wrye '
                                  u'Mash will automatically install your packages, sequentially, starting from the last package in your order, and continuing'
                                  u' up to the first package (to respect overrides).\nOnly the packages present in the restored list and which were '
                                  u'installed when the list was created will be re-installed, the rest will be ignored.\n\nClick "No" to skip'
                                  u' the process.'), _('Re-install packages?')) == wx.ID_NO: return
        # Re-install packages
        toInstall = [x[1] for x in instData if x[2]]
        progress = balt.Progress(_('Installing...'), '\n' + ' ' * 60)
        try:
            singletons.gInstallers.data.install(toInstall, progress, False, True)
        finally:
            progress.Destroy()
            singletons.gInstallers.data.refresh(what='N')
            singletons.gInstallers.RefreshUIMods()
        # Notify
        self.instStatusCh(_('Synced restored order...'))

    def onInstOrdS(self, event):  # Polemos
        """On storing installers order."""
        instList = [(x, singletons.gInstList.gList.GetItemText(x, 0), 1 if singletons.gInstList.data.getGuiKeys(
            singletons.gInstList.GetItem(x))[0].split('.')[0] == 'on' else 0) for x in
                    range(singletons.gInstList.gList.GetItemCount())]
        if mosh.SaveModOrder(instList, 'installers', 'paksnap').status:
            self.instStatusCh(_('Stored Installers Order...'))
        else:
            self.instStatusCh(_('Failed...'))

    def instStatusCh(self, msg):  # Polemos
        """Set a temporal status message."""
        self.statusChanged = True
        self.gPackage.SetLabel(msg)
        self.instWatch.Start()

    def instRefr(self):  # Polemos
        """Refreshing."""
        self.refreshed = False
        self.refreshing = False
        self.frameActivated = False
        self.fullRefresh = False

    def DragAndDrop(self):  # Polemos, disabled for now, todo: fix and re-enable
        """"Enable File Drag and Drop."""
        # dragDrop = self.enableFileDragDrop(singletons.gInstList.gList)
        # singletons.gInstList.gList.SetDropTarget(dragDrop)
        singletons.gInstList.gList.droppedItms = False

    def DoColumnMenu(self, event):  # -# D.C.-G.
        """Modified to avoid system error if installers path is not reachable."""
        if not os.access(mosh.dirs['installers'].s, os.W_OK): pass
        self.gList.DoColumnMenu(event)

    def OnShow(self):  # Polemos: Typos plus reflect new menu.
        """Panel is shown. Update self.data."""
        if conf.settings.get('mash.installers.isFirstRun', True):
            conf.settings['mash.installers.isFirstRun'] = conf.settings['mash.installers.enabled'] = False
            message = _(
                u'Do you wish to enable "Installers"?\n\nIf you do, Mash will first need to initialize some data. '
                u'If you have many mods installed, this may take on the order of five minutes or more.\nIf you'
                u' prefer to not enable "Installers" at this time, you can always enable it later on from the menu.')
            result = guidialog.askdialog(None, message, self.data.title)
            conf.settings['mash.installers.enabled'] = True if result == wx.ID_YES else False
        if not conf.settings['mash.installers.enabled']: return
        if self.refreshing: return
        data = self.gList.data
        if not self.refreshed or (
                self.frameActivated and (data.refreshRenamedNeeded() or data.refreshInstallersNeeded())):
            self.refreshing = True
            progress = balt.Progress(_('Refreshing Installers...'), '\n' + ' ' * 60)
            try:
                what = ('DIS', 'I')[self.refreshed]
                modified = data.refresh(progress, what, self.fullRefresh)
                if modified: self.gList.RefreshUI()
                if modified == "noDir": guidialog.WarningMessage(self, _('"%s" cannot be accessed.'
                                                                          u'\nThis path is possibly on a remote drive, or misspelled, or non writable.' %
                                                                          mosh.dirs['installers'].s))
                self.fullRefresh = False
                self.frameActivated = False
                self.refreshing = False
                self.refreshed = True
            finally:
                if progress is not None: progress.Destroy()
        self.SetStatusCount()

    def OnShowInfoPage(self, event):
        """A specific info page has been selected."""
        if event.GetId() == self.gNotebook.GetId():
            index = event.GetSelection()
            gPage, initialized = self.infoPages[index]
            if self.detailsItem and not initialized:
                self.RefreshInfoPage(index, self.data[self.detailsItem])
            event.Skip()

    def SetStatusCount(self):
        """Sets status bar count field."""
        active = len([x for x in self.data.values() if x.isActive])
        text = _('Packages: %d/%d') % (active, len(self.data.data))
        singletons.statusBar.SetStatusField(text, 2)

    def SaveDetails(self):  # --Details view (if it exists)
        """Saves details if they need saving."""
        conf.settings['mash.installers.page'] = self.gNotebook.GetSelection()
        if not self.detailsItem: return
        if not self.gComments.IsModified(): return
        installer = self.data[self.detailsItem]
        installer.comments = self.gComments.GetValue()
        self.data.setChanged()

    def RefreshUIMods(self):
        """Refresh UI plus refresh mods state."""
        self.gList.RefreshUI()
        if mosh.modInfos.refresh():
            del mosh.modInfos.mtimesReset[:]
            singletons.modList.Refresh('ALL')

    def enableGUI(self):  # Polemos
        """Enables disabled gui elements if an item is selected."""
        if not self.gComments.IsEnabled():
            self.gCommentstxt.Enable()
            self.gComments.Enable()
            self.gComments.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.gComments.Refresh()

    def RefreshDetails(self, item=None):
        """Refreshes detail view associated with data from item."""
        if item not in self.data: item = None
        if item is not None: self.enableGUI()
        self.SaveDetails()  # --Save previous details
        self.detailsItem = item
        del self.espms[:]
        if item:
            installer = self.data[item]
            # --Name
            self.gPackage.SetLabel(
                item.s if not (item.s.startswith('==') or item.s.endswith('==')) else _('Please select a package...'))
            # --Info Pages
            currentIndex = self.gNotebook.GetSelection()
            for index, (gPage, state) in enumerate(self.infoPages):
                self.infoPages[index][1] = False
                if (index == currentIndex):
                    self.RefreshInfoPage(index, installer)
                else:
                    gPage.SetValue('')
            # --Sub-Packages
            self.gSubList.Clear()
            if len(installer.subNames) <= 2:
                self.gSubList.Clear()
            else:
                balt.setCheckListItems(self.gSubList, [x.replace('&', '&&') for x in installer.subNames[1:]],
                                       installer.subActives[1:])
            # --Espms
            if not installer.espms:
                self.gEspmList.Clear()
            else:
                names = self.espms = sorted(installer.espms)
                names.sort(key=lambda x: x.cext != '.esm')
                balt.setCheckListItems(self.gEspmList, [x.s.replace('&', '&&') for x in names],
                                       [x not in installer.espmNots for x in names])
            # --Comments
            self.gComments.SetValue(installer.comments)
        else:
            self.gPackage.SetLabel(_('Please select a package...'))
            for index, (gPage, state) in enumerate(self.infoPages):
                self.infoPages[index][1] = True
                gPage.SetValue('')
            self.gSubList.Clear()
            self.gEspmList.Clear()
            self.gComments.SetValue('')
        self.statusLastMsg = self.gPackage.GetLabel()

    def RefreshInfoPage(self, index, installer):  # Polemos: fixes
        """Refreshes notebook page."""
        gPage, initialized = self.infoPages[index]
        if initialized:
            return
        else:
            self.infoPages[index][1] = True
        pageName = gPage.GetName()
        sNone = _('[None]')

        def sortKey(file):
            dirFile = file.lower().rsplit('\\', 1)
            if len(dirFile) == 1: dirFile.insert(0, '')
            return dirFile

        def dumpFiles(files, default='', header='', isPath=False):
            if files:
                if isPath:
                    files = [x.s for x in files]
                else:
                    files = list(files)
                sortKeys = dict((x, sortKey(x)) for x in files)
                files.sort(key=lambda x: sortKeys[x])
                buff = ''
                if header: buff = header + '\n'
                buff += '\n'.join(files)
                return buff
            elif header:
                return header + '\n'
            else:
                return ''

        if pageName == 'gGeneral':
            info = _('== Overview\n')
            info += _('Type: ')
            info += (_('Archive'), _('Project'))[isinstance(installer, mosh.InstallerProject)]
            info += '\n'
            if installer.type == 1:
                info += _('Structure: Simple\n')
            elif installer.type == 2:
                if len(installer.subNames) == 2:
                    info += _('Structure: Complex/Simple\n')
                else:
                    info += _('Structure: Complex\n')
            elif installer.type < 0:
                info += _('Structure: Corrupt/Incomplete\n')
            else:
                info += _('Structure: Unrecognized\n')
            nConfigured = len(installer.data_sizeCrc)
            nMissing = len(installer.missingFiles)
            nMismatched = len(installer.mismatchedFiles)
            info += _('Compressed: %s kb\n') % formatInteger(installer.size // 1024)
            info += _('Files: %s\n') % formatInteger(len(installer.fileSizeCrcs))
            info += _('Configured: %s (%s kb)\n') % (
                formatInteger(nConfigured), formatInteger(installer.unSize // 1024))
            info += _('  Matched: %s\n') % formatInteger(nConfigured - nMissing - nMismatched)
            info += _('  Missing: %s\n') % formatInteger(nMissing)
            info += _('  Conflicts: %s\n') % formatInteger(nMismatched)
            info += '\n'
            # --Infoboxes
            try:
                gPage.SetValue(info + dumpFiles(installer.data_sizeCrc, sNone, _('== Configured Files'), isPath=True))
            except:
                pass
        elif pageName == 'gMatched':
            try:
                gPage.SetValue(
                    dumpFiles(set(installer.data_sizeCrc) - installer.missingFiles - installer.mismatchedFiles,
                              isPath=True))
            except:
                pass
        elif pageName == 'gMissing':
            try:
                gPage.SetValue(dumpFiles(installer.missingFiles, isPath=True))
            except:
                pass
        elif pageName == 'gMismatched':
            try:
                gPage.SetValue(dumpFiles(installer.mismatchedFiles, sNone, isPath=True))
            except:
                pass
        elif pageName == 'gConflicts':
            try:
                gPage.SetValue(self.data.getConflictReport(installer, 'OVER'))
            except:
                pass
        elif pageName == 'gUnderrides':
            try:
                gPage.SetValue(self.data.getConflictReport(installer, 'UNDER'))
            except:
                pass
        elif pageName == 'gDirty':
            try:
                gPage.SetValue(dumpFiles(installer.dirty_sizeCrc, isPath=True))
            except:
                pass
        elif pageName == 'gSkipped':
            try:
                gPage.SetValue('\n'.join((
                    dumpFiles(installer.skipExtFiles, sNone, _('== Skipped (Extension)')),
                    dumpFiles(installer.skipDirFiles, sNone, _('== Skipped (Dir)')),)) or sNone)
            except:
                pass

    def refreshCurrent(self, installer):
        """Refreshes current item while retaining scroll positions."""
        installer.refreshDataSizeCrc()
        installer.refreshStatus(self.data)
        subScrollPos = self.gSubList.GetScrollPos(wx.VERTICAL)
        espmScrollPos = self.gEspmList.GetScrollPos(wx.VERTICAL)
        self.gList.RefreshUI(self.detailsItem)
        self.gSubList.ScrollLines(subScrollPos)
        self.gEspmList.ScrollLines(espmScrollPos)

    def OnCheckSubItem(self, event):
        """Handle check/uncheck of item."""
        selected = self.gSubList.GetSelections()
        installer = self.data[self.detailsItem]
        for index in range(self.gSubList.GetCount()):
            installer.subActives[index + 1] = self.gSubList.IsChecked(index)
        self.refreshCurrent(installer)
        for i in selected: self.gSubList.Select(i)

    def OnCheckEspmItem(self, event):
        """Handle check/uncheck of item."""
        installer = self.data[self.detailsItem]
        espmNots = installer.espmNots
        for index, espm in enumerate(self.espms):
            if self.gEspmList.IsChecked(index):
                espmNots.discard(espm)
            else:
                espmNots.add(espm)
        self.refreshCurrent(installer)

    def SaveCfgFile(self):  # -# D.C.-G.
        """Save the installers path in mash.ini."""
        self.data.saveCfgFile()


# ------------------------------------------------------------------------------

class DataModsPanel(gui.NotebookPanel):  # Polemos
    """Downloads and Mods data folders (like MO) panel. OpenMW/TES3mp."""

    def __init__(self, parent):
        """Init."""
        wx.Panel.__init__(self, parent, -1)
        if True:  # Content
            # Mods list
            singletons.ModdataList = ModdataList(self)
            singletons.ModdataList.SetMinSize(wx.Size(350, -1))
            # Toolbar: Info text label
            self.infotext = wx.StaticText(self, wx.ID_ANY, u'', DPOS, DSIZE, wx.ALIGN_LEFT | wx.ST_NO_AUTORESIZE)
            self.infotext.Wrap(-1)
            # Toolbar: Restore Button
            self.restore_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.open'].GetBitmap(), DPOS, DSIZE,
                                               ADRW)
            self.restore_btn.SetBitmapPressed(singletons.images['mod.open'].GetBitmap())
            self.restore_btn.SetBitmapCurrent(singletons.images['mod.open.onhov'].GetBitmap())
            self.restore_btn.SetToolTip(wx.ToolTip(_('Restore Mod Order')))
            # Toolbar: Backup Button
            self.backup_btn = wx.BitmapButton(self, wx.ID_ANY, singletons.images['mod.save'].GetBitmap(), DPOS, DSIZE,
                                              ADRW)
            self.backup_btn.SetBitmapPressed(singletons.images['mod.save'].GetBitmap())
            self.backup_btn.SetBitmapCurrent(singletons.images['mod.save.onhov'].GetBitmap())
            self.backup_btn.SetToolTip(wx.ToolTip(_('Backup Mod Order')))
            # Packages list
            singletons.ModPackageList = ModPackageList(self)
            singletons.ModPackageList.SetMinSize(wx.Size(110, -1))
            self.hid_chkBox = wx.CheckBox(self, wx.ID_ANY, _('Show Hidden'), DPOS, DSIZE, 0)
        if True:  # Theming
            self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
            singletons.ModdataList.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            singletons.ModdataList.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.infotext.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
            singletons.ModPackageList.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        if True:  # Sizers
            # Mods list
            moddata_sizer = wx.BoxSizer(wx.HORIZONTAL)
            moddata_sizer.SetMinSize(wx.Size(350, -1))
            moddata_sizer.Add(singletons.ModdataList, 1, wx.ALL | wx.EXPAND, 1)
            # Info sizer
            info_sizer = wx.BoxSizer(wx.VERTICAL)
            info_sizer.Add(self.infotext, 1, wx.ALL | wx.EXPAND, 5)
            # Toolbar sizer
            toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
            toolbar_sizer.SetMinSize(wx.Size(170, 24))
            toolbar_sizer.AddMany([(info_sizer, 1, wx.ALIGN_CENTER | wx.ALL, 1),
                                   (self.restore_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 2),
                                   (self.backup_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 2)])
            # Packages toolbar sizer
            packageTsizer = wx.BoxSizer(wx.HORIZONTAL)
            packageTsizer.Add(self.hid_chkBox, 0, wx.RIGHT | wx.LEFT, 5)
            # Packages list sizer
            packages_sizer = wx.BoxSizer(wx.VERTICAL)
            packages_sizer.SetMinSize(wx.Size(270, -1))
            packages_sizer.AddMany(
                [(singletons.ModPackageList, 1, wx.ALL | wx.EXPAND, 1), (packageTsizer, 0, wx.EXPAND, 5)])
            # Packages Sizer
            packagesDetails_sizer = wx.BoxSizer(wx.VERTICAL)
            packagesDetails_sizer.SetMinSize(wx.Size(170, -1))
            packagesDetails_sizer.AddMany([(toolbar_sizer, 0, wx.EXPAND, 5), (packages_sizer, 1, wx.EXPAND, 5)])
            # Main sizer
            main_sizer = wx.BoxSizer(wx.HORIZONTAL)
            main_sizer.AddMany([(moddata_sizer, 1, wx.EXPAND, 5), (packagesDetails_sizer, 0, wx.EXPAND, 5)])
            self.SetSizer(main_sizer)
            # Finishing touch
            self.Layout()
            main_sizer.Fit(self)
        if True:  # Events
            self.restore_btn.Bind(wx.EVT_BUTTON, self.restore)
            self.backup_btn.Bind(wx.EVT_BUTTON, self.backup)
            self.hid_chkBox.Bind(wx.EVT_CHECKBOX, self.hiddenChk)
        self.initSettings()
        self.hid_chkBox.Disable()  # Polemos, todo: enable at some point...

    def initSettings(self):
        """Initial settings."""
        if conf.settings['mash.DataMods.packages.showHidden']: self.hid_chkBox.SetValue(True)

    def hiddenChk(self, event):
        """Store checked box value and applies changes."""
        conf.settings['mash.DataMods.packages.showHidden'] = self.hid_chkBox.GetValue()

    def restore(self, event):
        """Restore Mod order."""
        # Open backup browser
        BckList = mosh.GetBckList('modsnap').bckList
        backupFile = guidialog.SimpleListDialog(self, BckList, _('Choose a backup to restore:')).Selection
        if backupFile is None: return
        # Mod, plugin and archive data
        modData = mosh.LoadModOrder(backupFile, 'modsnap').modData
        activePlugins = mosh.mwIniFile.loadOrder[:]
        activeBSA = [x for x in singletons.ArchivesList.items if singletons.ArchivesList.data[x][2]]
        self.showInfo(_('Mod Order Loaded...'))
        # Reorder mods
        singletons.ModdataList.data.moveTo([x[1] for x in modData])
        singletons.ModdataList.datamods.updateDatamods(modData)
        singletons.ModdataList.Refresh()
        # Reactivate mods if needed
        for mod in modData:
            if mod[0]:
                if not singletons.ModdataList.datamods.checkActiveState(mod[1]):
                    singletons.ModdataList.ToggleModActivation(mod[1])
            else:
                if singletons.ModdataList.datamods.checkActiveState(mod[1]):
                    singletons.ModdataList.ToggleModActivation(mod[1])
        singletons.ModdataList.Refresh()
        # Enable previously active plugins
        for plugin in activePlugins:
            try:
                singletons.modList.ToggleModActivation(plugin)
            except:
                continue
        # Enable previously active archives
        for bsa in activeBSA:
            try:
                singletons.ArchivesList.ToggleBSAactivation(bsa)
            except:
                pass
        # Refresh Plugins Tab
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()

    def backup(self, event):
        """Save Mod order."""
        modOrder = [singletons.ModdataList.data[x] for x in singletons.ModdataList.items]
        if mosh.SaveModOrder(modOrder, 'mods', 'modsnap').status: self.showInfo(_('Mods Order Saved...'))

    def showInfo(self, msg):
        """Inform user about actions."""
        self.infotext.SetLabel(msg)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1000)

    def onUpdate(self, event):
        """Check timer and update info."""
        self.infotext.SetLabel('')
        self.timer.Stop()

    def OnShow(self):
        """Panel is shown. Update self.data."""
        if mosh.DataModsInfo().refresh: singletons.ModdataList.Refresh()
        self.SetStatusCount()

    def SetStatusCount(self):
        """Sets status bar count field."""
        active = len([x[5] for x in singletons.ModdataList.data.itervalues() if x[5]])
        try:
            text = _('Mods:   %d/%d') % (active, len(singletons.ModdataList.data))
        except:
            text = _('Config file is corrupt.')
        singletons.statusBar.SetStatusField(text, 2)


# ------------------------------------------------------------------------------

class ScreensList(gui.List):  # Polemos: Fixes and more
    """ScreenList data."""
    mainMenu = Links()  # --Column menu
    itemMenu = Links()  # --Single item menu

    def __init__(self, parent):
        """Init."""
        # --Columns
        self.cols = conf.settings['mash.screens.cols']
        self.colAligns = conf.settings['mash.screens.colAligns']
        self.colNames = conf.settings['mash.colNames']
        self.colReverse = conf.settings.getChanged('mash.screens.colReverse')
        self.colWidths = conf.settings['mash.screens.colWidths']
        # --Data/Items
        self.data = mosh.screensData = mosh.ScreensData()
        self.sort = conf.settings['mash.screens.sort']
        # --Links
        self.mainMenu = ScreensList.mainMenu
        self.itemMenu = ScreensList.itemMenu
        # --Parent init
        gui.List.__init__(self, parent, -1, ctrlStyle=(wx.LC_REPORT | wx.SUNKEN_BORDER))
        # --Event
        wx.EVT_LIST_ITEM_SELECTED(self, self.listId, self.OnItemSelected)

    def RefreshUI(self, files='ALL', detail='SAME'):
        """Refreshes UI for specified files."""
        # --Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else:
            selected = {detail}
        # --Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, str):
            self.PopulateItem(files, selected=selected)
        else:  # --Iterable
            for file in files:
                self.PopulateItem(file, selected=selected)
        singletons.mashFrame.SetStatusCount()

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        # --String name of item?
        if not type(itemDex) is int:
            itemDex = self.items.index(itemDex)
        fileName = GPath(self.items[itemDex])
        fileInfo = self.data[fileName]
        cols = self.cols
        for colDex in range(self.numCols):
            col = cols[colDex]
            if col == 'Image':
                value = fileName.s
            elif col == 'Size':
                value = '%sKB' % formatInteger(fileInfo[2] // 1024)
            else:
                value = ''
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --Selection State
        if fileName in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):  # Polemos: cosmetic changes
        (col, reverse) = self.GetSortSettings(col, reverse)
        conf.settings['mash.screens.sort'] = col
        data = self.data
        # --Start with sort by name
        self.items.sort()
        if col == 'Image':
            pass  # --Done by default
        elif col == 'Size':
            self.items.sort(key=lambda x: data[x][2])
        else:
            raise mosh.SortKeyError(_('Unrecognized sort key: %s' % col))
        # --Ascending
        if reverse: self.items.reverse()

    def OnColumnResize(self, event):
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.screens.colWidths')

    def OnItemSelected(self, event=None):
        fileName = self.items[event.Index]
        filePath = mosh.screensData.dir.join(fileName)
        bitmap = (filePath.exists() and wx.Bitmap(filePath.s)) or None
        self.picture.SetBitmap(bitmap)


# ------------------------------------------------------------------------------

class ScreensPanel(gui.NotebookPanel):
    """Screenshots tab."""

    def __init__(self, parent):
        """Init."""
        wx.Panel.__init__(self, parent, -1)
        # --Left
        sashPos = conf.settings.get('mash.screens.sashPos', 120)
        left = self.left = leftSash(self, defaultSize=(sashPos, 100), onSashDrag=self.OnSashDrag)
        right = self.right = wx.Panel(self, style=wx.NO_BORDER)
        # --Contents
        singletons.screensList = ScreensList(left)
        singletons.screensList.SetSizeHints(100, 100)
        singletons.screensList.picture = balt.Picture(right, 1024, 768)
        # --Layout
        right.SetSizer(hSizer((singletons.screensList.picture, 1, wx.GROW)))
        wxadv.LayoutAlgorithm().LayoutWindow(self, right)
        # --Event
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def SetStatusCount(self):  # Polemos: just a preference "typo" fix
        """Sets status bar count field."""
        text = _('Screenshots: %d') % (len(singletons.screensList.data.data),)
        singletons.statusBar.SetStatusField(text, 2)

    def OnSashDrag(self, event):
        """Handle sash moved."""
        wMin, wMax = 80, self.GetSizeTuple()[0] - 80
        sashPos = max(wMin, min(wMax, event.GetDragRect().width))
        self.left.SetDefaultSize((sashPos, 10))
        wxadv.LayoutAlgorithm().LayoutWindow(self, self.right)
        singletons.screensList.picture.Refresh()
        conf.settings['mash.screens.sashPos'] = sashPos

    def OnSize(self, event=None):
        wxadv.LayoutAlgorithm().LayoutWindow(self, self.right)

    def OnShow(self):
        """Panel is shown. Update self.data."""
        if mosh.screensData.refresh(): singletons.screensList.RefreshUI()
        self.SetStatusCount()


# ------------------------------------------------------------------------------

class MashNotebook(wx.Notebook):  # -# D.C.-G. MashNotebook modified for utils panel. Polemos: OpenMW/TES3mp support
    """Mash Notebooks."""

    def __init__(self, parent, id):
        """Init."""
        wx.Notebook.__init__(self, parent, id)
        # Set notebook pages
        if not conf.settings['openmw']:  # Polemos: Regular Morrowind support
            self.AddPage(UtilsPanel(self), _('Utilities'))
            self.AddPage(InstallersPanel(self), _('Installers'))
            self.AddPage(ModPanel(self), _('Mods'))
            self.AddPage(SavePanel(self), _('Saves'))
            self.AddPage(ScreensPanel(self), _('Screenshots'))
        if conf.settings['openmw']:  # Polemos: OpenMW/TES3mp support
            self.AddPage(UtilsPanel(self), _('Utilities'))
            self.AddPage(DataModsPanel(self), _('Mods'))
            self.AddPage(ModPanel(self), _('Plugins'))
            self.AddPage(SavePanel(self), _('Saves'))
            self.AddPage(ScreensPanel(self), _('Screenshots'))
        # Active page
        pageIndex = conf.settings['mash.page']
        if conf.settings['mash.installers.fastStart'] and pageIndex == 1 and not conf.settings['openmw']:
            pageIndex = 2
        self.SetSelection(pageIndex)
        conf.settings['mash.page'] = pageIndex
        # Event
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnShowPage)

    def OnShowPage(self, event):  # Polemos: Hooked menu and page global id update.
        """Call page's OnShow command."""
        if event.GetId() == self.GetId():
            conf.settings['mash.page'] = event.GetSelection()
            self.GetPage(event.GetSelection()).OnShow()
            MenuBar((event.GetSelection()))
            event.Skip()


# ------------------------------------------------------------------------------

class MashStatusBar(wx.StatusBar):  # Polemos: recoding, refactoring, additions
    """Mash status bar."""
    links = []

    def __init__(self, parent):
        """Init."""
        wx.StatusBar.__init__(self, parent, -1)
        singletons.statusBar = self
        self.SetFieldsCount(3)
        self.SetMinHeight(21)
        self.buttons = []
        self.SetStatusWidths([18 * len(self.links) + 55, -1, 150])
        links = self.links
        self.buttons.extend((link.GetBitmapButton(self, style=wx.NO_BORDER) for link in links))
        self.OnSize()
        self.profile()
        # Events
        wx.EVT_SIZE(self, self.OnSize)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def profile(self):
        """Show the active profile in the statusbar field."""
        self.profile_text = _('Active Profile: %s' % conf.settings['profile.active'])
        self.SetStatusText(self.profile_text, 1)

    def OnSize(self, event=None):
        """Set items pos in statusbar."""
        rect = self.GetFieldRect(0)
        (xPos, yPos) = (rect.x + 1, rect.y + 1)
        for button in self.buttons:
            button.SetPosition((xPos, yPos))
            xPos += 27
        if event: event.Skip()

    def SetStatusField(self, text="", field=1):
        """Set's display text as specified, starts a 5" timer to reset."""
        self.SetStatusText(text, field)
        self.timer = wx.Timer(self)
        self.timer.Start(5000)

    def OnTimer(self, event):
        """Reset's display text as specified and stops the timer."""
        self.profile()
        self.timer.Stop()


# ------------------------------------------------------------------------------

class MashFrame(wx.Frame):  # Polemos: Added a Menubar, OpenMW/TES3mp support, more.
    """Main application frame."""
    mincush = False

    def __init__(self, parent=None, pos=wx.DefaultPosition, size=(885, 550), style=wx.DEFAULT_FRAME_STYLE):
        """Initialization."""
        wx.Frame.__init__(self, parent, -1, u'Wrye Mash', pos, size, style)
        # The One
        singletons.mashFrame = self
        # Data
        self.knownCorrupted = set()
        self.OpenMW = conf.settings['openmw']
        # MainFrame
        self.SetTitle()
        guidialog.setIcon(self)
        # Status Bar
        self.SetStatusBar(MashStatusBar(self))
        # Content
        self.notebook = notebook = MashNotebook(self, -1)
        # MenuBar
        MenuBar()
        # Layout
        if conf.settings['mash.virgin']: self.Centre(wx.BOTH)
        minSize = conf.settings['mash.frameSize.min']
        self.SetSizeHints(minSize[0], minSize[1])
        if self.GetSize()[0] < minSize[0]: self.SetSize([minSize[0], conf.settings['mash.frameSize'][1]])
        if self.GetSize()[1] < minSize[1]: self.SetSize([conf.settings['mash.frameSize'][0], minSize[1]])
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(notebook, 1, wx.GROW)
        self.SetSizer(self.sizer)
        # Events
        wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_ICONIZE(self, self.OnIconize)
        wx.EVT_ACTIVATE(self, self.RefreshData)

    def Refresh_StatusBar(self):  # Polemos
        """Call to refresh any StatusBar changes."""
        singletons.statusBar.Destroy()
        MashStatusBar.links = []
        InitStatusBar()
        self.SetStatusBar(MashStatusBar(self))

    def SetTitle(self, title=None):  # Polemos: Small cosmetic change. Todo: Part of possible "full" profile solution.
        """Set title. Set to default if no title supplied."""
        if title is None: title = u'Wrye Mash %s' % (conf.settings['mash.version'][1],)
        wx.Frame.SetTitle(self, title)

    def SetStatusCount(self):
        """Sets the status bar count field. Actual work is done by current panel."""
        if hasattr(self, 'notebook'):  # --Hack to get around problem with screens tab.
            self.notebook.GetPage(self.notebook.GetSelection()).SetStatusCount()

    def RefreshData(self, event=None):  # Polemos: changes
        """Refreshes all data. Can be called manually, but is also triggered by window activation event."""
        if True:  # --Events -------------------------------#
            if event and not event.GetActive(): return  # --Ignore deactivation events.
            if conf.settings['mash.virgin']: conf.settings['mash.virgin'] = False

        if True:  # --UPDATES-------------------------------#
            popMods = popSaves = None
            # --Check morrowind.ini and mods directory...
            if mosh.mwIniFile.refresh() | mosh.modInfos.refresh():
                mosh.mwIniFile.refreshDoubleTime()
                popMods = 'ALL'
            # --Have any mtimes been reset?
            if mosh.modInfos.mtimesReset:
                resetList = '\n* '.join(mosh.modInfos.mtimesReset)
                del mosh.modInfos.mtimesReset[:]
                guidialog.InfoMessage(self,
                                       _('Modified dates have been reset for some mod files:\n\n* %s' % resetList))
                popMods = 'ALL'
            # --Check savegames directory...
            if mosh.saveInfos.refresh(): popSaves = 'ALL'
            # Check For OpenMW/TES3mp Data folders and packages.
            if self.OpenMW:
                mosh.mwIniFile.FullRefresh()
                singletons.ModPackageList.Refresh()
            # Check Archives.
            if singletons.ArchivesList:
                singletons.ArchivesList.Refresh()
            # Repopulate Morrowind Mods.
            if popMods:
                singletons.modList.Refresh(popMods)
            # --Will repop saves too.
            elif popSaves:
                singletons.saveList.Refresh(popSaves)
            if not self.OpenMW:
                # Is MGE XE in Morrowind Dir?
                if not conf.settings['mgexe.detected']:
                    if os.path.isfile(os.path.join(conf.settings['mwDir'], 'MGEXEgui.exe')):
                        conf.settings['mgexe.detected'] = True
                        self.Refresh_StatusBar()
                # Notify about MWSE 1024 plugin option support
                if not conf.settings['query.mwse.max.plugins']:
                    conf.settings['query.mwse.max.plugins'] = True
                    if os.path.isfile(os.path.join(conf.settings['mwDir'], 'MWSE.dll')):
                        result = guidialog.askdialog(self, _("MWSE detected on Morrowind's installation!\n\n"
                                                              u"Thanks to Nullcascade and Greatness7, Wrye Mash now supports the MWSE's 1024 "
                                                              u"raised plugin limit! Please do note that the implementation is still in beta "
                                                              u"and that any plugin manipulation moving forward, will take this change into "
                                                              u"account.\nAny bug reports should also be forwarded on the MWSE team.\n\n"
                                                              u"Click YES if you wish to enable MWSE 1024 plugin support (this can always be "
                                                              u"changed later the advanced options of the settings). Click NO if you do not "
                                                              u"wish to change anything."), _('MWSE detected!'))
                        if result == wx.ID_YES: conf.settings['mash.extend.plugins'] = True
            # --Current notebook panel
            if singletons.gInstallers: singletons.gInstallers.frameActivated = True
            if self.notebook:
                self.notebook.GetPage(self.notebook.GetSelection()).OnShow()
            # Duplicate entries found in configuration files?
            if mosh.mwIniFile.loadFilesDups:
                mosh.mwIniFile.safeSave()

        if True:  # --WARNINGS------------------------------#
            # --Does morrowind.ini have any bad or missing files?
            if mosh.mwIniFile.loadFilesBad:
                message = (_("Missing files and/or incorrect entries have been removed from load list:\n\n  %s")
                           % (', '.join(mosh.mwIniFile.loadFilesBad),))
                mosh.mwIniFile.safeSave()
                guidialog.WarningMessage(self, message)
            # --Was load list too long?
            if mosh.mwIniFile.loadFilesExtra:
                message = (_("Load list has been truncated because it was too long:\n\n  %s")
                           % (', '.join(mosh.mwIniFile.loadFilesExtra),))
                mosh.mwIniFile.safeSave()
                guidialog.WarningMessage(self, message)
            # --Any new corrupted mod files?
            corruptMods, message = set(mosh.modInfos.corrupted.keys()), ''
            if not corruptMods <= self.knownCorrupted:
                message += _("The following mod files have corrupted headers: \n\n")
                message += u','.join(sorted(corruptMods)) + '.'
                self.knownCorrupted |= corruptMods
            # --Any new corrupted saves?
            corruptSaves = set(mosh.saveInfos.corrupted.keys())
            if not corruptSaves <= self.knownCorrupted:
                if message: message += '\n'
                message += _('The following save files have corrupted headers: \n\n')
                message += u','.join(sorted(corruptSaves)) + '.'
                self.knownCorrupted |= corruptSaves
            # Show warning messages.
            if message: guidialog.WarningMessage(self, message)
            # --Any Y2038 Resets?
            if mosh.y2038Resets:
                message = (_('Mash cannot handle dates greater than January 19, 2038. Accordingly, the dates for the '
                             u'following files have been reset to an earlier date: \n%s.') % u', '.join(
                    sorted(mosh.y2038Resets)))
                del mosh.y2038Resets[:]
                guidialog.WarningMessage(self, message)

    def OnIconize(self, event):  # Polemos
        """Handle minimize event."""
        if conf.settings['app.min.systray']:
            if not self.mincush:
                self.mincush = True
                self.sysTray = interface.SysTray(self, conf.settings['openmw'])
            else:
                self.mincush = False
        else:
            event.Skip()

    def systrayRun(self, event):
        """Execute Morrowind/OpenMw from systray."""
        App_Morrowind.Execute(App_Morrowind(), event)

    def CleanSettings(self):
        """Cleans junk from settings before closing."""
        # --Clean rename dictionary.
        modNames = set(mosh.modInfos.data.keys())
        modNames.update(mosh.modInfos.table.data.keys())
        renames = mosh.settings.getChanged('mash.mods.renames')
        for key, value in renames.items():
            if value not in modNames: del renames[key]
        # --Clean backup
        for fileInfos in (mosh.modInfos, mosh.saveInfos):
            goodNames = set(fileInfos.data.keys())
            backupDir = os.path.join(fileInfos.dir, conf.settings['mosh.fileInfo.backupDir'])
            if not os.path.isdir(backupDir): continue
            for name in sorted(os.listdir(backupDir)):
                path = os.path.join(backupDir, name)
                if name[-1] == 'f': name = name[:-1]
                if name not in goodNames and os.path.isfile(path): os.remove(path)

    def OnCloseWindow(self, event):  # Polemos: Wrye Mash shutdown.
        """Handle Close event. Save application data."""
        self.CleanSettings()
        if singletons.docBrowser: singletons.docBrowser.DoSave()
        if not self.IsIconized() and not self.IsMaximized():
            conf.settings['mash.framePos'] = self.GetPosition()
            conf.settings['mash.frameSize'] = self.GetSizeTuple()
        conf.settings['mash.page'] = self.notebook.GetSelection()
        mosh.modInfos.table.save()
        for index in range(self.notebook.GetPageCount()): self.notebook.GetPage(index).OnCloseWindow()
        if singletons.settingsWindow: singletons.settingsWindow.Destroy()
        if not self.OpenMW: singletons.gInstallers.SaveCfgFile()  # Polemos: Regular Morrowind support
        if event is not None: event.Skip()
        conf.settings.save()
        try:  # Polemos: Systray actions
            if self.IsIconized(): self.sysTray.onExit()
        except:
            pass
        self.Destroy()
        appinfo.app.ExitMainLoop()


# ------------------------------------------------------------------------------

class MenuBar(object):  # Polemos
    """Main Menu."""

    def __init__(self, panel=None):
        """Init."""
        self.parent = singletons.mashFrame
        self.openMW = conf.settings['openmw']
        singletons.MenuBar = self
        if panel is None:
            try:
                panel = conf.settings['mash.page']
            except:
                panel = 2
        # Door keeper of the Menubar.
        if conf.settings['mash.menubar.enabled']: self.Menu_po(panel)

    def statusbar_status(self, event):
        """Change default status bar field (for showing menu help strings)."""
        # Polemos: It took me days to invent a way of doing this. Couldn't find any documentation.
        try:
            singletons.statusBar.SetStatusField(self.MainMenuGUI.GetHelpString(event.GetId()), 1)
        except:
            singletons.statusBar.profile()
        if self.refresh_panel == 2:
            self.mods_view_cond()
            self.mods_misc_cond()
        if self.refresh_panel == 1 and not self.openMW:
            self.installers_view_cond()
        elif self.refresh_panel == 3:
            self.saves_view_cond()

    def Menu_po(self, panel):
        """Finally a real menu for Wrye Mash. It also has a disable option for the hardcore!..."""
        # Menu init
        self.MainMenuGUI = wx.MenuBar()
        panel = int(panel)
        self.refresh_panel = panel
        self.PanelMenu = wx.Menu()
        # Mw/OpenMw menu items
        self.MashMenu(panel)
        # Show the Menu
        self.parent.SetMenuBar(self.MainMenuGUI)
        wx.EVT_MENU_HIGHLIGHT_ALL(self.parent, self.statusbar_status)

    def MashMenu(self, panel):
        """Morrowind Menu."""
        if panel == 0:  # Utilities
            self.utilities_menu()

        elif panel == 1:  # Installers/DataMods
            self.sortbyMenu = wx.Menu()
            self.settings_menu = wx.Menu()
            if not self.openMW:
                self.installers_menu()
            else:
                self.DataMods_menu()

        elif panel == 2:  # Mods/Plugins
            self.sub_PanelMenu0 = wx.Menu()
            self.sub_PanelMenu1 = wx.Menu()
            self.sortbyMenu = wx.Menu()
            self.settings_menu = wx.Menu()
            self.misc_modMenu = wx.Menu()
            self.misc_subMenu0 = wx.Menu()
            self.misc_subMenu1 = wx.Menu()
            if not self.openMW:
                self.mod_menu()
            else:
                self.plugins_menu()

        elif panel == 3:  # Saves
            self.sortbyMenu = wx.Menu()
            self.misc_saveMenu = wx.Menu()
            if not self.openMW:
                self.saves_menu()
            else:
                self.OpenMWsaves_menu()

        elif panel == 4:  # Screenshots
            self.screens_menu()

    def refresh_menubar(self, panel=None):
        """Refreshes menubar items. Call individually with: singletons.MenuBar.{x}_cond()."""
        if panel is None:
            try:
                panel = self.refresh_panel
            except:
                panel = 2

        if not self.openMW and panel == 1:
            # Morrowind Installers Tab
            self.installers_view_cond()
            self.installers_settings_cond()

        elif panel == 2:
            # Mw Mods Tab, OpenMW Plugins Tab
            self.mods_load_cond()
            self.mods_view_cond()
            self.mods_settings_cond()
            self.mods_misc_cond()

        elif panel == 3:
            # Saves Tab
            self.saves_profiles_cond()
            self.saves_view_cond()
            self.saves_misc_cond()

    def utilities_menu(self):
        """"Utilities panel menu."""
        # Utilitie items:
        self.ID_new_utilitie = self.PanelMenu.Append(wx.ID_ANY, _("&New"), _("Create New Utilitie."))
        self.ID_modify_utilitie = self.PanelMenu.Append(wx.ID_ANY, _("&Modify"), _("Modify Selected Utilitie."))
        self.ID_delete_utilitie = self.PanelMenu.Append(wx.ID_ANY, _("&Delete"), _("Delete Selected Utilitie."))
        self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
        # Events
        self.parent.Bind(wx.EVT_MENU, self.Create_New_Utilitie, self.ID_new_utilitie)
        self.parent.Bind(wx.EVT_MENU, self.Modify_Selected_Utilitie, self.ID_modify_utilitie)
        self.parent.Bind(wx.EVT_MENU, self.Delete_Selected_Utilitie, self.ID_delete_utilitie)

    def Create_New_Utilitie(self, event):
        """Create New Utilitie."""
        singletons.utilsList.NewItem()
        singletons.utilsList.RefreshUI()

    def Modify_Selected_Utilitie(self, event):
        """Modify Selected Utilitie."""
        singletons.utilsList.ModifyItem()
        singletons.utilsList.RefreshUI()

    def Delete_Selected_Utilitie(self, event):
        """Delete Selected Utilitie."""
        singletons.utilsList.DeleteItem()
        singletons.utilsList.RefreshUI()

    def installers_menu(self):
        """"Installers panel menu."""
        self.data_inst = mosh.InstallersData()
        # "Actions" items:
        self.ID_Installers_Import = self.PanelMenu.Append(wx.ID_ANY, _("Import Package..."),
                                                          _("Import a package into the Installers directory."))
        self.PanelMenu.AppendSeparator()
        self.ID_Installers_Open = self.PanelMenu.Append(wx.ID_ANY, _("Open..."),
                                                        _("Open installer file and view contents."))
        self.ID_Files_Open_installers_po = self.PanelMenu.Append(wx.ID_ANY, _("Open Installers dir"),
                                                                 _("Go to Installers directory."))
        self.PanelMenu.AppendSeparator()
        self.ID_Installers_Refresh = self.PanelMenu.Append(wx.ID_ANY, _("Refresh Data"), _("Refreshes installers."))
        self.ID_full_Installers_Refresh = self.PanelMenu.Append(wx.ID_ANY, _("Full Refresh"),
                                                                _("Refreshes all data. Warning: Time consuming."))
        self.PanelMenu.AppendSeparator()
        self.ID_Installers_AddMarker = self.PanelMenu.Append(wx.ID_ANY, _("Add Marker..."),
                                                             _("Add a Marker in the installers list."))
        self.PanelMenu.AppendSeparator()
        self.ID_Installers_AnnealAll = self.PanelMenu.Append(wx.ID_ANY, _("Anneal All"),
                                                             _("Correct underrides in anPackages and install missing files from active anPackages."))
        self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Installers_ImportP, self.ID_Installers_Import)
        self.parent.Bind(wx.EVT_MENU, self.Installers_Open, self.ID_Installers_Open)
        self.parent.Bind(wx.EVT_MENU, self.Files_Open_installers_po, self.ID_Files_Open_installers_po)
        self.parent.Bind(wx.EVT_MENU, self.Installers_Refresh, self.ID_Installers_Refresh)
        self.parent.Bind(wx.EVT_MENU, self.full_Installers_Refresh, self.ID_full_Installers_Refresh)
        self.parent.Bind(wx.EVT_MENU, self.Installers_AddMarker, self.ID_Installers_AddMarker)
        self.parent.Bind(wx.EVT_MENU, self.Installers_AnnealAll, self.ID_Installers_AnnealAll)

        # "View" items:
        self.ins_sort0 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Active'), _('Sort by Active installer files.'),
                                                wx.ITEM_CHECK)
        self.ins_sort1 = self.sortbyMenu.Append(wx.ID_ANY, _('Projects First'), _('Show Projects First.'),
                                                wx.ITEM_CHECK)
        self.sortbyMenu.AppendSeparator()
        self.ins_sort2 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Package'), _('Sort by Package ordering.'),
                                                wx.ITEM_CHECK)
        self.ins_sort3 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Order'), _('Sort by Date time ordering.'),
                                                wx.ITEM_CHECK)
        self.ins_sort4 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Group'), _('Sort by Group ordering.'),
                                                wx.ITEM_CHECK)
        self.ins_sort5 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Modified'), _('Sort by Modified ordering.'),
                                                wx.ITEM_CHECK)
        self.ins_sort6 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Size'), _('Sort by Size ordering.'),
                                                wx.ITEM_CHECK)
        self.ins_sort7 = self.sortbyMenu.Append(wx.ID_ANY, _('Sort by Files'), _('Sort by Files ordering.'),
                                                wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.sortbyMenu, _('&View'))
        # Conditions
        self.installers_view_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Installers_SortActive, self.ins_sort0)
        self.parent.Bind(wx.EVT_MENU, self.Installers_SortProjects, self.ins_sort1)
        self.parent.Bind(wx.EVT_MENU, self.PackageIns, self.ins_sort2)
        self.parent.Bind(wx.EVT_MENU, self.OrderIns, self.ins_sort3)
        self.parent.Bind(wx.EVT_MENU, self.GroupIns, self.ins_sort4)
        self.parent.Bind(wx.EVT_MENU, self.ModifiedIns, self.ins_sort5)
        self.parent.Bind(wx.EVT_MENU, self.SizeIns, self.ins_sort6)
        self.parent.Bind(wx.EVT_MENU, self.FilesIns, self.ins_sort7)

        # "Settings" items:
        self.ins_sort0a = self.settings_menu.Append(wx.ID_ANY, _("Enabled"), _("Enable Installers."), wx.ITEM_CHECK)
        self.ins_sort1a = self.settings_menu.Append(wx.ID_ANY, _("Avoid at Startup"),
                                                    _("When enabled Mash will not open in the Installers screen on program start."),
                                                    wx.ITEM_CHECK)
        self.ins_sort2a = self.settings_menu.Append(wx.ID_ANY, _("Progress Extra Info"),
                                                    _("Show extra information in the progress bar (filename, size, CRC) while refreshing."),
                                                    wx.ITEM_CHECK)
        self.settings_menu.AppendSeparator()
        self.ins_sort3a = self.settings_menu.Append(wx.ID_ANY, _("Auto-Anneal"), _("Auto-Anneal Installers."),
                                                    wx.ITEM_CHECK)
        self.ins_sort4a = self.settings_menu.Append(wx.ID_ANY, _("Clean Data Directory"),
                                                    _("Remove empty Installer Directories."), wx.ITEM_CHECK)
        self.settings_menu.AppendSeparator()
        self.ins_sort5a = self.settings_menu.Append(wx.ID_ANY, _("Show Inactive Conflicts"),
                                                    _("Show Inactive Conflicts."), wx.ITEM_CHECK)
        self.ins_sort6a = self.settings_menu.Append(wx.ID_ANY, _("Show Lower Conflicts"), _("Show Lower Conflicts."),
                                                    wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.settings_menu, _('&Settings'))
        # Conditions
        self.installers_settings_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Installers_Enabled, self.ins_sort0a)
        self.parent.Bind(wx.EVT_MENU, self.Installers_AvoidOnStart, self.ins_sort1a)
        self.parent.Bind(wx.EVT_MENU, self.Progress_Enabled, self.ins_sort2a)
        self.parent.Bind(wx.EVT_MENU, self.Installers_AutoAnneal, self.ins_sort3a)
        self.parent.Bind(wx.EVT_MENU, self.Installers_RemoveEmptyDirs, self.ins_sort4a)
        self.parent.Bind(wx.EVT_MENU, self.Installers_ConflictsReportShowsInactive, self.ins_sort5a)
        self.parent.Bind(wx.EVT_MENU, self.Installers_ConflictsReportShowsLower, self.ins_sort6a)

    def installers_view_cond(self):
        """"Conditions."""
        self.ins_sort0.Check(conf.settings['mash.installers.sortActive'])
        self.ins_sort1.Check(conf.settings['mash.installers.sortProjects'])
        sort_list = {"Package": self.ins_sort2, "Order": self.ins_sort3, "Group": self.ins_sort4,
                     "Modified": self.ins_sort5, "Size": self.ins_sort6, "Files": self.ins_sort7}
        [sort_list[x].Check() if x == conf.settings['mash.installers.sort'] else sort_list[x].Check(False) for x in
         sort_list.keys()]

    def installers_settings_cond(self):
        """"Conditions"""
        self.ins_sort0a.Check(conf.settings['mash.installers.enabled'])
        self.ins_sort1a.Check(conf.settings['mash.installers.fastStart'])
        self.ins_sort2a.Check(conf.settings['mash.installers.show.progress.info'])
        self.ins_sort3a.Check(conf.settings['mash.installers.autoAnneal'])
        self.ins_sort4a.Check(conf.settings['mash.installers.removeEmptyDirs'])
        self.ins_sort5a.Check(conf.settings['mash.installers.conflictsReport.showInactive'])
        self.ins_sort6a.Check(conf.settings['mash.installers.conflictsReport.showLower'])

    # Settings ================== #
    def Installers_Enabled(self, event):
        Installers_Enabled.Execute(Installers_Enabled(), event)

    def Installers_AvoidOnStart(self, event):
        Installers_AvoidOnStart.Execute(Installers_AvoidOnStart(), event)

    def Progress_Enabled(self, event):
        Progress_info.Execute(Progress_info(), event)

    def Installers_AutoAnneal(self, event):
        Installers_AutoAnneal.Execute(Installers_AutoAnneal(), event)

    def Installers_RemoveEmptyDirs(self, event):
        Installers_RemoveEmptyDirs.Execute(Installers_RemoveEmptyDirs(), event)

    # View ====================== #
    def Installers_SortActive(self, event):
        Installers_SortActive.Execute(Installers_SortActive(), event)

    def Installers_SortProjects(self, event):
        Installers_SortProjects.Execute(Installers_SortProjects(), event)

    def PackageIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Package'), event)

    def OrderIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Order'), event)

    def GroupIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Group'), event)

    def ModifiedIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Modified'), event)

    def SizeIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Size'), event)

    def FilesIns(self, event):
        Installers_SortBy.Execute(Installers_SortBy('Files'), event)

    # Actions =================== #
    def Installers_ImportP(self, event):
        Installers_Import.Execute(Installers_Import(), event)

    def Installers_Open(self, event):
        """Open installer file."""
        try:
            dir = self.data_inst.dir
            file = singletons.gInstallers.detailsItem
            if file is None: guidialog.ErrorMessage(None,
                                                     _('Please select an Installer file first (from the Installers list).'))
            dir.join(file).start()
        except:
            pass

    def Files_Open_installers_po(self, event):
        """Open Installers dir."""
        dir = mosh.dirs['installers']
        if not dir.exists(): dir.makedirs()
        dir.start()

    def Installers_Refresh(self, event):
        Installers_Refresh.Execute(Installers_Refresh(False), event)

    def full_Installers_Refresh(self, event):
        Installers_Refresh.Execute(Installers_Refresh(True), event)

    def Installers_AddMarker(self, event):
        Installers_AddMarker.Execute(Installers_AddMarker(), event)

    def Installers_AnnealAll(self, event):
        Installers_AnnealAll.Execute(Installers_AnnealAll(), event)

    def Installers_ConflictsReportShowsInactive(self, event):
        Installers_ConflictsReportShowsInactive.Execute(Installers_ConflictsReportShowsInactive(), event)

    def Installers_ConflictsReportShowsLower(self, event):
        Installers_ConflictsReportShowsLower.Execute(Installers_ConflictsReportShowsLower(), event)

    def DataMods_menu(self):
        """DataMods panel menu."""
        if True:  # "Actions" items:
            self.ID_Files_Open_DataMods = self.PanelMenu.Append(wx.ID_ANY, _("Open DataMods dir"),
                                                                _("Go to DataMods directory."))
            self.ID_Files_Open_Packages = self.PanelMenu.Append(wx.ID_ANY, _("Open Downloads dir"),
                                                                _("Go to Downloads directory."))
            self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
            # Events:
            self.parent.Bind(wx.EVT_MENU, self.Files_Open_DataMods, self.ID_Files_Open_DataMods)
            self.parent.Bind(wx.EVT_MENU, self.Files_Open_Packages, self.ID_Files_Open_Packages)

    # Actions =================== #
    def Files_Open_DataMods(self, event):
        Open_Datamods_po.Execute(Open_Datamods_po(), event)

    def Files_Open_Packages(self, event):
        Open_Packages_po.Execute(Open_Packages_po(), event)

    def plugins_menu(self):
        """OpenMW Plugins panel menu."""
        self.window_mod_po = singletons.modList
        # "Actions" items:
        self.mods_build_load()
        self.PanelMenu.AppendMenu(wx.ID_ANY, _('&Load'), self.sub_PanelMenu0)
        self.PanelMenu.AppendSeparator()
        self.ID_plugins_CopyActive = self.PanelMenu.Append(wx.ID_ANY, _("Copy Active Mods List"),
                                                           _("Copy Active Mods List to clipboard."))
        if True:  # "Snapshots" sub-items:
            self.ID_snapshot_po_take = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Take fast snapshot"),
                                                                  _("Take a fast snapshot of your mod order."))
            self.ID_snapshot_po_restore = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Restore fast snapshot"),
                                                                     _("Restore a fast snapshot of your mod order"))
            self.ID_snapshot_po_select = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Restore saved snapshot"),
                                                                    _("Find a saved snapshot file to restore your mod order."))
            self.sub_PanelMenu1.AppendSeparator()
            self.ID_snapshot_po_import = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Import snapshot(s)"),
                                                                    _("Import snapshot(s) files from a directory."))
            self.ID_snapshot_po_export = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Export snapshot"),
                                                                    _("Export snapshot to a chosen directory."))
            self.PanelMenu.AppendMenu(wx.ID_ANY, _('&Snapshots'), self.sub_PanelMenu1)
        self.PanelMenu.AppendSeparator()
        self.ID_Conf_Bck = self.PanelMenu.Append(wx.ID_ANY, _("Backup/Restore Config files"),
                                                 _("Take a manual backup/restore of your Configuration."))
        self.ID_Files_Open = self.PanelMenu.Append(wx.ID_ANY, _("Open \"Data Files\" dir"),
                                                   _("Open \"Data Files\" directory."))
        self.ID_Files_Unhide_mod = self.PanelMenu.Append(wx.ID_ANY, _("Unhide..."), _("Unhide selected mod.")).Enable(
            False)
        self.PanelMenu.AppendSeparator()
        self.ID_Create_Mashed_Patch = self.PanelMenu.Append(wx.ID_ANY, _("Create Mashed Patch"),
                                                            _("Automates creation, enabling and list importing for Mashed Patch."))
        self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_CopyActive, self.ID_plugins_CopyActive)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_take, self.ID_snapshot_po_take)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_restore, self.ID_snapshot_po_restore)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_select, self.ID_snapshot_po_select)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_import, self.ID_snapshot_po_import)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_export, self.ID_snapshot_po_export)
        self.parent.Bind(wx.EVT_MENU, self.Conf_Bck, self.ID_Conf_Bck)
        self.parent.Bind(wx.EVT_MENU, self.Files_Open, self.ID_Files_Open)
        # self.parent.Bind(wx.EVT_MENU, self.Files_Unhide_mod, self.ID_Files_Unhide_mod)
        self.parent.Bind(wx.EVT_MENU, self.Create_Mashed_Patch, self.ID_Create_Mashed_Patch)

        # "View" items:
        self.mod_sort0 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Type"), _("Sort by type."), wx.ITEM_CHECK)
        self.mod_sort1 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Selection"), _("Sort by selected items."),
                                                wx.ITEM_CHECK)
        self.sortbyMenu.AppendSeparator()
        self.mod_sort2 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by File"), _("Sort by File ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort3 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Author"), _("Sort by Author ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort4 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Group"), _("Sort by Group ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort5 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Load Order"), _("Sort by Load Order."),
                                                wx.ITEM_CHECK)
        self.mod_sort6 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Modified"), _("Sort by Modified ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort7 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Rating"), _("Sort by Rating ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort8 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Size"), _("Sort by Size ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort9 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Status"), _("Sort by Status ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort10 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Version"), _("Sort by Version ordering."),
                                                 wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.sortbyMenu, _('&View'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_EsmsFirst, self.mod_sort0)
        self.parent.Bind(wx.EVT_MENU, self.Mods_SelectedFirst, self.mod_sort1)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_File, self.mod_sort2)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Author, self.mod_sort3)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Group, self.mod_sort4)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Load_Order, self.mod_sort5)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Modified, self.mod_sort6)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Rating, self.mod_sort7)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Size, self.mod_sort8)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Status, self.mod_sort9)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_byVersion, self.mod_sort10)

        # "Settings" items:
        self.ID_plugins_OpenMWcfg = self.settings_menu.Append(wx.ID_ANY, _("OpenMW.cfg..."), _("Open OpenMW.cfg."))
        self.ID_plugins_IniTweaks = self.settings_menu.Append(wx.ID_ANY, _("CFG Tweaks..."),
                                                              _("Integrate CFG Tweaks.")).Enable(False)
        self.ID_Reset_Beth_Dates = self.settings_menu.Append(wx.ID_ANY, _("Reset Bethesda Dates"),
                                                             _("Resets the dates of the Bethesda Masters and Archives. Can help with problems with Steam.")).Enable(
            False)
        self.settings_menu.AppendSeparator()
        self.ID_plugins_LockTimes = self.mod_sort0b = self.settings_menu.Append(wx.ID_ANY, _("Lock Order"),
                                                                                _("Prevents undesired changes in mods order outside of Mash."),
                                                                                wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.settings_menu, _('&Settings'))
        # Conditions
        self.mods_settings_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.plugins_OpenMWcfg, self.ID_plugins_OpenMWcfg)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_IniTweaks, self.ID_plugins_IniTweaks)
        # self.parent.Bind(wx.EVT_MENU, self.Reset_Beth_Dates, self.ID_Reset_Beth_Dates)
        self.parent.Bind(wx.EVT_MENU, self.Mods_LockTimes, self.ID_plugins_LockTimes)

        # "Misc" items:
        if True:  # Mlox sub-items:
            self.mlox0 = self.misc_subMenu0.Append(wx.ID_ANY, _("&Launch Mlox"), _("Launch Mlox utility."))
            self.mlox1 = self.misc_subMenu0.Append(wx.ID_ANY, _("&Revert Changes"),
                                                   _("Revert Mlox's most recent changes."))
            self.misc_modMenu.AppendMenu(wx.ID_ANY, _('&Mlox'), self.misc_subMenu0).Enable(False)
        if True:  # TES3cmd sub-items:
            self.TES3cmd0 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Fixit (all active)"),
                                                      _("Executes \"tes3cmd.exe fixit --hide-backups --backup-dir\" and creates a multipatch."))
            self.TES3cmd1 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Restore modified files"),
                                                      _("Restore changed files from backup dir."))
            self.misc_subMenu1.AppendSeparator()
            self.TES3cmd2 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Create MultiPatch"),
                                                      _("It produces a powerful patch file based on your current load order to solve various problems."))
            self.misc_modMenu.AppendMenu(wx.ID_ANY, _('&TES3cmd'), self.misc_subMenu1).Enable(False)
        self.misc_modMenu.AppendSeparator()
        self.TES3lint_Settings = self.misc_modMenu.Append(wx.ID_ANY, _("TES3lint Settings"),
                                                          _("Configure TES3lint flags and settings.")).Enable(False)
        # self.Custom_Commands = self.misc_modMenu.Append(wx.ID_ANY, _("Custom Commands..."), _("Create, save, edit and delete Custom Commands."))
        self.misc_modMenu.AppendSeparator()
        self.ID_plugins_check_updates = self.misc_modMenu.Append(wx.ID_ANY, _("Check for Updates"),
                                                                 _("Check for new Wrye  Mash releases. Note: Depends on Nexus working status."))
        self.MainMenuGUI.Append(self.misc_modMenu, _('&Misc'))
        # Conditions
        self.mods_misc_cond()
        # Events:
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Mlox, self.mlox0)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Mlox_revert, self.mlox1)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_Fixit, self.TES3cmd0)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_restore, self.TES3cmd1)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_multipatch, self.TES3cmd2)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_TES3lint_Settings, self.TES3lint_Settings)
        # self.parent.Bind(wx.EVT_MENU, self.Mods_Custom_Commands, self.Custom_Commands)
        self.parent.Bind(wx.EVT_MENU, self.Mods_check_updates, self.ID_plugins_check_updates)

    def mod_menu(self):
        """Morrowind Mods panel menu."""
        self.window_mod_po = singletons.modList
        # "Actions" items:
        if True:  # "Load" sub-items:
            self.mods_build_load()
            self.PanelMenu.AppendMenu(wx.ID_ANY, _('&Load'), self.sub_PanelMenu0)
        self.PanelMenu.AppendSeparator()
        self.ID_Mods_CopyActive = self.PanelMenu.Append(wx.ID_ANY, _("Copy Active Mods List"),
                                                        _("Copy Active Mods List to clipboard."))
        if True:  # "Snapshots" sub-items:
            self.ID_snapshot_po_take = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Take fast snapshot"),
                                                                  _("Take a fast snapshot of your mod order."))
            self.ID_snapshot_po_restore = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Restore fast snapshot"),
                                                                     _("Restore a fast snapshot of your mod order"))
            self.ID_snapshot_po_select = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Restore saved snapshot"),
                                                                    _("Find a saved snapshot file to restore your mod order."))
            self.sub_PanelMenu1.AppendSeparator()
            self.ID_snapshot_po_import = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Import snapshot(s)"),
                                                                    _("Import snapshot(s) files from a directory."))
            self.ID_snapshot_po_export = self.sub_PanelMenu1.Append(wx.ID_ANY, _("Export snapshot"),
                                                                    _("Export snapshot to a chosen directory."))
            self.PanelMenu.AppendMenu(wx.ID_ANY, _('&Snapshots'), self.sub_PanelMenu1)
        self.PanelMenu.AppendSeparator()
        self.ID_Conf_Bck = self.PanelMenu.Append(wx.ID_ANY, _("Backup/Restore Morrowind.ini"),
                                                 _("Take a manual backup/restore of your Configuration."))
        self.ID_Files_Open = self.PanelMenu.Append(wx.ID_ANY, _("Open \"Data Files\" dir"),
                                                   _("Open \"Data Files\" directory."))
        self.ID_Files_Unhide_mod = self.PanelMenu.Append(wx.ID_ANY, _("Unhide..."), _("Unhide selected mod."))
        self.PanelMenu.AppendSeparator()
        self.ID_Create_Mashed_Patch = self.PanelMenu.Append(wx.ID_ANY, _("Create Mashed Patch"),
                                                            _("Automates creation, enabling and importing for Mashed Patch."))
        self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_CopyActive, self.ID_Mods_CopyActive)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_take, self.ID_snapshot_po_take)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_restore, self.ID_snapshot_po_restore)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_select, self.ID_snapshot_po_select)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_import, self.ID_snapshot_po_import)
        self.parent.Bind(wx.EVT_MENU, self.snapshot_po_export, self.ID_snapshot_po_export)
        self.parent.Bind(wx.EVT_MENU, self.Conf_Bck, self.ID_Conf_Bck)
        self.parent.Bind(wx.EVT_MENU, self.Files_Open, self.ID_Files_Open)
        self.parent.Bind(wx.EVT_MENU, self.Files_Unhide_mod, self.ID_Files_Unhide_mod)
        self.parent.Bind(wx.EVT_MENU, self.Create_Mashed_Patch, self.ID_Create_Mashed_Patch)

        # "View" items:
        self.mod_sort0 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Type"), _("Sort by type."), wx.ITEM_CHECK)
        self.mod_sort1 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Selection"), _("Sort by selected items."),
                                                wx.ITEM_CHECK)
        self.sortbyMenu.AppendSeparator()
        self.mod_sort2 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by File"), _("Sort by File ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort3 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Author"), _("Sort by Author ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort4 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Group"), _("Sort by Group ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort5 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Load Order"), _("Sort by Load Order."),
                                                wx.ITEM_CHECK)
        self.mod_sort6 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Modified"), _("Sort by Modified ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort7 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Rating"), _("Sort by Rating ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort8 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Size"), _("Sort by Size ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort9 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Status"), _("Sort by Status ordering."),
                                                wx.ITEM_CHECK)
        self.mod_sort10 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Version"), _("Sort by Version ordering."),
                                                 wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.sortbyMenu, _('&View'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_EsmsFirst, self.mod_sort0)
        self.parent.Bind(wx.EVT_MENU, self.Mods_SelectedFirst, self.mod_sort1)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_File, self.mod_sort2)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Author, self.mod_sort3)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Group, self.mod_sort4)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Load_Order, self.mod_sort5)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Modified, self.mod_sort6)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Rating, self.mod_sort7)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Size, self.mod_sort8)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_by_Status, self.mod_sort9)
        self.parent.Bind(wx.EVT_MENU, self.sort_mods_byVersion, self.mod_sort10)

        # "Settings" items:
        self.ID_Mods_MorrowindIni = self.settings_menu.Append(wx.ID_ANY, _("Morrowind.ini..."),
                                                              _("Open Morrowind.ini."))
        self.ID_Mods_IniTweaks = self.settings_menu.Append(wx.ID_ANY, _("INI Tweaks..."), _("Integrate INI Tweaks."))
        self.ID_Mods_Replacers = self.settings_menu.Append(wx.ID_ANY, _("Replacers..."), _("Configure Replacers."))
        self.ID_Reset_Beth_Dates = self.settings_menu.Append(wx.ID_ANY, _("Reset Bethesda Dates"),
                                                             _("Resets the dates of the Bethesda Masters and Archives. Can help with problems with Steam."))
        self.settings_menu.AppendSeparator()
        self.mod_sort0b = self.settings_menu.Append(wx.ID_ANY, _("Lock Times"),
                                                    _("Prevents undesired changes in mods order."), wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.settings_menu, _('&Settings'))
        # Conditions
        self.mods_settings_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_MorrowindIni, self.ID_Mods_MorrowindIni)
        self.parent.Bind(wx.EVT_MENU, self.Mods_IniTweaks, self.ID_Mods_IniTweaks)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Replacers, self.ID_Mods_Replacers)
        self.parent.Bind(wx.EVT_MENU, self.Reset_Beth_Dates, self.ID_Reset_Beth_Dates)
        self.parent.Bind(wx.EVT_MENU, self.Mods_LockTimes, self.mod_sort0b)

        # "Misc" items:
        if True:  # Mlox sub-items:
            self.mlox0 = self.misc_subMenu0.Append(wx.ID_ANY, _("&Launch Mlox"), _("Launch Mlox utility."))
            self.mlox1 = self.misc_subMenu0.Append(wx.ID_ANY, _("&Revert Changes"),
                                                   _("Revert Mlox's most recent changes."))
            self.misc_modMenu.AppendMenu(wx.ID_ANY, _('&Mlox'), self.misc_subMenu0)
        if True:  # TES3cmd sub-items:
            self.TES3cmd0 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Fixit (all active)"),
                                                      _("Executes \"tes3cmd.exe fixit --hide-backups --backup-dir\" and creates a multipatch."))
            self.TES3cmd1 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Restore modified files"),
                                                      _("Restore changed files from backup dir."))
            self.misc_subMenu1.AppendSeparator()
            self.TES3cmd2 = self.misc_subMenu1.Append(wx.ID_ANY, _("&Create MultiPatch"),
                                                      _("It produces a powerful patch file based on your current load order to solve various problems."))
            self.misc_modMenu.AppendMenu(wx.ID_ANY, _('&TES3cmd'), self.misc_subMenu1)
        self.misc_modMenu.AppendSeparator()
        self.TES3lint_Settings = self.misc_modMenu.Append(wx.ID_ANY, _("TES3lint Settings"),
                                                          _("Configure TES3lint flags and settings."))
        self.Custom_Commands = self.misc_modMenu.Append(wx.ID_ANY, _("Custom Commands..."),
                                                        _("Create, save, edit and delete Custom Commands."))
        self.misc_modMenu.AppendSeparator()
        self.ID_Mods_check_updates = self.misc_modMenu.Append(wx.ID_ANY, _("Check for Updates"),
                                                              _("Check for new Wrye  Mash releases. Note: Depends on Nexus working status."))
        self.MainMenuGUI.Append(self.misc_modMenu, _('&Misc'))
        # Conditions
        self.mods_misc_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Mods_Mlox, self.mlox0)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Mlox_revert, self.mlox1)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_Fixit, self.TES3cmd0)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_restore, self.TES3cmd1)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Tes3cmd_multipatch, self.TES3cmd2)
        self.parent.Bind(wx.EVT_MENU, self.Mods_TES3lint_Settings, self.TES3lint_Settings)
        self.parent.Bind(wx.EVT_MENU, self.Mods_Custom_Commands, self.Custom_Commands)
        self.parent.Bind(wx.EVT_MENU, self.Mods_check_updates, self.ID_Mods_check_updates)

    def mods_load_cond(self):
        """Conditions (special case)."""
        panel = self.sub_PanelMenu0
        if not mosh.mwIniFile.loadFiles:
            panel.FindItemById(ID_LOADERS.SAVE).Enable(False)
        else:
            panel.FindItemById(ID_LOADERS.SAVE).Enable()
        if conf.settings['mash.loadLists.need.refresh']:
            conf.settings['mash.loadLists.need.refresh'] = False
            pan_del = panel.Delete
            pan_get = panel.GetMenuItems
            [pan_del(x.GetId()) for x in pan_get()]
            self.mods_build_load()

    def mods_build_load(self):
        """Special menu constructor."""
        Mods_LoadList.AppendToMenu(Mods_LoadList(), self.sub_PanelMenu0, singletons.modList, None)

    def mods_view_cond(self):
        """Conditions."""
        self.mod_sort0.Check() if self.window_mod_po.esmsFirst else self.mod_sort0.Check(False)
        self.mod_sort1.Check() if self.window_mod_po.selectedFirst else self.mod_sort1.Check(False)
        sort_list = {'File': self.mod_sort2, 'Author': self.mod_sort3, 'Group': self.mod_sort4, '#': self.mod_sort5,
                     'Modified': self.mod_sort6,
                     'Rating': self.mod_sort7, 'Size': self.mod_sort8, 'Status': self.mod_sort9,
                     'Version': self.mod_sort10}
        [sort_list[x].Check() if x == self.window_mod_po.sort else sort_list[x].Check(False) for x in sort_list.keys()]

    def mods_settings_cond(self):
        """Conditions."""
        self.mod_sort0b.Check() if mosh.modInfos.resetMTimes else self.mod_sort0b.Check(False)

    def mods_misc_cond(self):
        """Conditions."""
        [x.Enable(True) if os.path.isfile(conf.settings["mloxpath"]) else x.Enable(False) for x in
         (self.mlox0, self.mlox1)]
        [x.Enable(True) if tes3cmd.getLocation() else x.Enable(False) for x in
         (self.TES3cmd0, self.TES3cmd1, self.TES3cmd2)]

    # Misc ================= #
    def Mods_Mlox(self, event):
        Mods_Mlox.LaunchMlox(Mods_Mlox(), event)

    def Mods_Mlox_revert(self, event):
        Mods_Mlox.MloxRevert(Mods_Mlox(), event)

    def Mods_Tes3cmd_Fixit(self, event):
        Mods_Tes3cmd_Fixit.Execute(Mods_Tes3cmd_Fixit(), event)

    def Mods_Tes3cmd_restore(self, event):
        Mods_Tes3cmd_restore.Execute(Mods_Tes3cmd_restore(), event)

    def Mods_Tes3cmd_multipatch(self, event):
        Mods_Tes3cmd_multipatch.Execute(Mods_Tes3cmd_multipatch(), event)

    def Mods_TES3lint_Settings(self, event):
        Mods_TESlint_Config.Execute(Mods_TESlint_Config(), event)

    def Mods_Custom_Commands(self, event):
        Mods_custom_menu.Execute(Mods_custom_menu(), event)

    def Mods_check_updates(self, event):
        Check_for_updates.Execute(Check_for_updates(), event)

    # Settings ================== #
    def Mods_MorrowindIni(self, event):
        Mods_MorrowindIni.Execute(Mods_MorrowindIni(), event)

    def plugins_OpenMWcfg(self, event):
        os.startfile(os.path.join(conf.settings['openmwprofile'], 'openmw.cfg'))

    def Mods_IniTweaks(self, event):
        Mods_IniTweaks.Execute(Mods_IniTweaks(), event)

    def Mods_Replacers(self, event):
        Mods_Replacers.Execute(Mods_Replacers(), event)

    def Reset_Beth_Dates(self, event):
        Reset_Beth_Dates.Execute(Reset_Beth_Dates(), event)

    def Mods_LockTimes(self, event):
        Mods_LockTimes.Execute(Mods_LockTimes(), event)

    # View ==============#
    def Mods_EsmsFirst(self, event):
        Mods_EsmsFirst.Execute(Mods_EsmsFirst(), event)

    def Mods_SelectedFirst(self, event):
        Mods_SelectedFirst.Execute(Mods_SelectedFirst(), event)

    def sort_mods_by_File(self, event):
        self.window_mod_po.PopulateItems("File", -1)

    def sort_mods_by_Author(self, event):
        self.window_mod_po.PopulateItems("Author", -1)

    def sort_mods_by_Group(self, event):
        self.window_mod_po.PopulateItems("Group", -1)

    def sort_mods_by_Load_Order(self, event):
        self.window_mod_po.PopulateItems('#', -1)

    def sort_mods_by_Modified(self, event):
        self.window_mod_po.PopulateItems("Modified", -1)

    def sort_mods_by_Rating(self, event):
        self.window_mod_po.PopulateItems("Rating", -1)

    def sort_mods_by_Size(self, event):
        self.window_mod_po.PopulateItems("Size", -1)

    def sort_mods_by_Status(self, event):
        self.window_mod_po.PopulateItems("Status", -1)

    def sort_mods_byVersion(self, event):
        self.window_mod_po.PopulateItems("Version", -1)

    # Actions ============#
    def Mods_CopyActive(self, event):
        Mods_CopyActive.Execute(Mods_CopyActive(), event)

    def snapshot_po_take(self, event):
        snapshot_po_take.Execute(snapshot_po_take(), event)

    def snapshot_po_restore(self, event):
        snapshot_po_restore.Execute(snapshot_po_restore(), event)

    def snapshot_po_select(self, event):
        snapshot_po_select.Execute(snapshot_po_select(), event)

    def snapshot_po_import(self, event):
        snapshot_po_import.Execute(snapshot_po_import(), event)

    def snapshot_po_export(self, event):
        snapshot_po_export.Execute(snapshot_po_export(), event)

    def Conf_Bck(self, event):
        Mods_Conf_Bck.Execute(Mods_Conf_Bck(), event)

    def Files_Open(self, event):
        Files_Open.Execute(Files_Open(), event)

    def Files_Unhide_mod(self, event):
        Files_Unhide.Execute(Files_Unhide(), event, 'mod')

    def Create_Mashed_Patch(self, event):
        Create_Mashed_Patch.Execute(Create_Mashed_Patch(), event)

    def OpenMWsaves_menu(self):
        """OpenMWsaves_menu panel menu."""
        # "Profiles" items
        self.idList = ID_PROFILES
        self.window_saves = singletons.saveList
        self.built_profiles_saves()
        # self.MainMenuGUI.Append(self.PanelMenu, _('&Profiles'))

        # Events
        wx.EVT_MENU(self.parent, self.idList.EDIT, self.DoEdit)
        wx.EVT_MENU_RANGE(self.parent, self.idList.BASE, self.idList.MAX, self.DoList)

        # "View" items:
        self.sav_sort0 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by File"), _("Sort by File"), wx.ITEM_CHECK)
        # self.sav_sort1 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Cell"), _("Sort by Cell"), wx.ITEM_CHECK)
        self.sav_sort2 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Modified"), _("Sort by Modified"),
                                                wx.ITEM_CHECK)
        # self.sav_sort3 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Player"), _("Sort by Player"), wx.ITEM_CHECK)
        # self.sav_sort4 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Save Name"), _("Sort by Save Name"), wx.ITEM_CHECK)
        self.sav_sort5 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Size"), _("Sort by Size"), wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.sortbyMenu, _('&View'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_File, self.sav_sort0)
        # self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Cell, self.sav_sort1)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Modified, self.sav_sort2)
        # self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Player, self.sav_sort3)
        # self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Save_Name, self.sav_sort4)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Status, self.sav_sort5)

        # "Misc" items:
        self.ID_Files_Open_saves_po = self.misc_saveMenu.Append(wx.ID_ANY, _("&Open Saves dir"),
                                                                _("Open default saves directory."))
        # self.ID_Files_Unhide = self.misc_saveMenu.Append(wx.ID_ANY, _("&Unhide..."), _("Unhide hidden save files."))
        self.MainMenuGUI.Append(self.misc_saveMenu, _('&Misc'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Files_Open_saves_po, self.ID_Files_Open_saves_po)
        # self.parent.Bind(wx.EVT_MENU, self.Files_Unhide, self.ID_Files_Unhide)

    def saves_menu(self):
        """Saves panel menu."""
        # "Profiles" items
        self.idList = ID_PROFILES
        self.window_saves = singletons.saveList
        self.built_profiles_saves()
        self.MainMenuGUI.Append(self.PanelMenu, _('&Profiles'))
        # Events
        wx.EVT_MENU(self.parent, self.idList.EDIT, self.DoEdit)
        wx.EVT_MENU_RANGE(self.parent, self.idList.BASE, self.idList.MAX, self.DoList)

        # "View" items:
        self.sav_sort0 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by File"), _("Sort by File"), wx.ITEM_CHECK)
        self.sav_sort1 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Cell"), _("Sort by Cell"), wx.ITEM_CHECK)
        self.sav_sort2 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Modified"), _("Sort by Modified"),
                                                wx.ITEM_CHECK)
        self.sav_sort3 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Player"), _("Sort by Player"), wx.ITEM_CHECK)
        self.sav_sort4 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Save Name"), _("Sort by Save Name"),
                                                wx.ITEM_CHECK)
        self.sav_sort5 = self.sortbyMenu.Append(wx.ID_ANY, _("Sort by Size"), _("Sort by Size"), wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.sortbyMenu, _('&View'))
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_File, self.sav_sort0)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Cell, self.sav_sort1)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Modified, self.sav_sort2)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Player, self.sav_sort3)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Save_Name, self.sav_sort4)
        self.parent.Bind(wx.EVT_MENU, self.sortby_saves_Status, self.sav_sort5)

        # "Misc" items:
        self.ID_Files_Open_saves_po = self.misc_saveMenu.Append(wx.ID_ANY, _("&Open Saves dir"),
                                                                _("Open default saves directory."))
        self.ID_Files_Unhide = self.misc_saveMenu.Append(wx.ID_ANY, _("&Unhide..."), _("Unhide hidden save files."))
        self.ID_Saves_MapGridLines = self.map_sav = self.misc_saveMenu.Append(wx.ID_ANY, _("&World Map Gridlines"),
                                                                              _("World Map Gridlines??"),
                                                                              wx.ITEM_CHECK)
        self.MainMenuGUI.Append(self.misc_saveMenu, _('&Misc'))
        # Conditions
        self.saves_misc_cond()
        # Events:
        self.parent.Bind(wx.EVT_MENU, self.Files_Open_saves_po, self.ID_Files_Open_saves_po)
        self.parent.Bind(wx.EVT_MENU, self.Files_Unhide, self.ID_Files_Unhide)
        self.parent.Bind(wx.EVT_MENU, self.Saves_MapGridLines, self.ID_Saves_MapGridLines)

    def saves_profiles_cond(self):
        """Conditions (special case)."""
        panel_get = self.PanelMenu.GetMenuItems
        panel_label = self.PanelMenu.GetLabel
        panel_del = self.PanelMenu.Delete
        panel_id = self.PanelMenu.FindItemById
        cur_me = [panel_label(x.GetId()) for x in panel_get()]
        chg_me = self.GetItems()[:]
        has_renames = True if [True for x in chg_me if x not in cur_me] else False
        if len(panel_get()) - 2 == len(self.GetItems()) and not has_renames:
            items = self.GetItems()
            curProfile = conf.settings.get('mash.profile', self.defaultName)
            if curProfile not in items: curProfile = self.defaultName
            [panel_id(id).Check(item.lower() == curProfile.lower()) for id,
            item in zip(self.idList, items) if panel_label(id) == conf.settings['mash.profile']]
        else:
            [panel_del(x.GetId()) for x in panel_get()]
            self.built_profiles_saves()

    def saves_view_cond(self):
        """Conditions."""
        if not self.openMW:
            sort_list = {"File": self.sav_sort0, "Cell": self.sav_sort1, "Modified": self.sav_sort2,
                         "Player": self.sav_sort3, "Save Name": self.sav_sort4, "Size": self.sav_sort5}
        elif self.openMW:
            sort_list = {"File": self.sav_sort0, "Modified": self.sav_sort2, "Size": self.sav_sort5}

        [sort_list[x].Check() if x == self.window_saves.sort else sort_list[x].Check(False) for x in sort_list.keys()]

    def saves_misc_cond(self):
        """Conditions."""
        self.map_sav.Check() if conf.settings['mash.worldMap.gridLines'] else self.map_sav.Check(False)

    def built_profiles_saves(self):
        """Special menu constructor."""
        panel_add = self.PanelMenu.Append
        panel_add_it = self.PanelMenu.AppendItem
        menu_pa = self.PanelMenu
        panel_add(self.idList.EDIT, _("Edit Profiles..."), _('Edit Saved Profiles.'))
        menu_pa.AppendSeparator()
        items = self.GetItems()
        curProfile = conf.settings.get('mash.profile', self.defaultName)
        if curProfile not in items: curProfile = self.defaultName
        for id, item in zip(self.idList, items):
            menuItem = wx.MenuItem(menu_pa, id, item, _('Activate %s profile.' % item), kind=wx.ITEM_RADIO)
            panel_add_it(menuItem)
            menuItem.Check(item.lower() == curProfile.lower())

    # Misc ================= #
    def Files_Open_saves_po(self, event):
        """Open Saves dir."""
        dir = GPath(self.window_saves.data.dir)
        if not dir.exists(): dir.makedirs()
        dir.start()

    def Files_Unhide(self, event):
        Files_Unhide.Execute(Files_Unhide(), event, 'save')

    def Saves_MapGridLines(self, event):
        conf.settings['mash.worldMap.gridLines'] = not conf.settings['mash.worldMap.gridLines']

    # View ================= #
    def sortby_saves_File(self, event):
        self.window_saves.PopulateItems("File", -1)

    def sortby_saves_Cell(self, event):
        self.window_saves.PopulateItems("Cell", -1)

    def sortby_saves_Modified(self, event):
        self.window_saves.PopulateItems("Modified", -1)

    def sortby_saves_Player(self, event):
        self.window_saves.PopulateItems("Player", -1)

    def sortby_saves_Save_Name(self, event):
        self.window_saves.PopulateItems("Save Name", -1)

    def sortby_saves_Status(self, event):
        self.window_saves.PopulateItems("Status", -1)

    # Profiles ============= #
    def GetItems(self):
        """Profile items."""
        self.hidden = os.path.join(mosh.saveInfos.dir, conf.settings['mosh.fileInfo.hiddenDir'])
        self.defaultName = _('Default')
        self.defaultDir = os.path.join(self.hidden, self.defaultName)
        if not os.path.exists(self.defaultDir): os.makedirs(self.defaultDir)
        isGood = lambda a: os.path.isdir(os.path.join(self.hidden, a))
        items = [dir for dir in os.listdir(self.hidden) if isGood(dir)]
        items.sort(key=str.lower)
        items.sort(key=lambda a: a != self.defaultName)
        return items

    def DoEdit(self, event):
        """Show profiles editing dialog."""
        data = Saves_ProfilesData(self.window_saves, self.hidden, self.defaultName)
        dialog = ListEditorDialog(self.window_saves, -1, _('Save Profiles'), data)
        dialog.ShowModal()
        dialog.Destroy()

    def DoList(self, event):
        """Handle selection of Profiles label."""
        # --Profile Names
        arcProfile = conf.settings.get('mash.profile', self.defaultName)
        srcProfile = self.GetItems()[event.GetId() - self.idList.BASE]
        if srcProfile == arcProfile: return
        # --Dirs
        arcDir, srcDir = [os.path.join(self.hidden, dir) for dir in (arcProfile, srcProfile)]
        savesDir = mosh.saveInfos.dir
        # --Progress
        progress = None
        arcFiles = sorted(mosh.saveInfos.data)
        srcFiles = sorted(name for name in os.listdir(srcDir) if (len(name) > 5 and name[-4:].lower() == '.ess'))
        arcCount, srcCount = len(arcFiles), len(srcFiles)
        if (arcCount + srcCount) == 0: return
        try:
            progress = guidialog.ProgressDialog(_('Moving Files'))
            # --Move arc saves to arc profile directory
            for num, saveName in enumerate(arcFiles):
                progress(1.0 * num // (arcCount + srcCount), saveName)
                savesPath, profPath = [os.path.join(dir, saveName) for dir in (savesDir, arcDir)]
                if not os.path.exists(profPath): os.rename(savesPath, profPath)
            arcIniPath = os.path.join(arcDir, 'Morrowind.ini')
            shutil.copyfile(mosh.mwIniFile.path, arcIniPath)
            conf.settings['mash.profile'] = srcProfile
            # --Move src profile directory saves to saves directory.
            for num, saveName in enumerate(srcFiles):
                progress(1.0 * (arcCount + num) // (arcCount + srcCount), saveName)
                savesPath, profPath = [os.path.join(dir, saveName) for dir in (savesDir, srcDir)]
                if not os.path.exists(savesPath): os.rename(profPath, savesPath)
            srcIniPath = os.path.join(srcDir, 'Morrowind.ini')
            if os.path.exists(srcIniPath): shutil.copyfile(srcIniPath, mosh.mwIniFile.path)
            singletons.mashFrame.SetTitle('Wrye Mash: %s' % srcProfile)
        finally:
            progress.Destroy()
        self.window_saves.details.SetFile(None)
        singletons.statusBar.profile()

    def screens_menu(self):
        """"Screenshots panel menu."""
        # Actions items:
        self.ID_Files_Open_screens_po = self.PanelMenu.Append(wx.ID_ANY, _("&Open Screenshots dir"),
                                                              _("Open default screenshots directory."))
        if not self.openMW:
            self.ID_Config_ScreenShots = self.PanelMenu.Append(wx.ID_ANY, _("&Configure screenshots"),
                                                               _("Here you can change screenshots naming and directory."))
        self.MainMenuGUI.Append(self.PanelMenu, _('&Actions'))
        # Events
        self.parent.Bind(wx.EVT_MENU, self.Files_Open_screens_po, self.ID_Files_Open_screens_po)
        if not self.openMW: self.parent.Bind(wx.EVT_MENU, self.Config_ScreenShots, self.ID_Config_ScreenShots)

    def Files_Open_screens_po(self, event):
        """Open default screenshots directory."""
        Files_Open_screens_po.Execute(Files_Open_screens_po(), event)
        singletons.screensList.RefreshUI()

    def Config_ScreenShots(self, event):
        """Change screenshots naming and directory"""
        Config_ScreenShots.Execute(Config_ScreenShots(), event)
        singletons.screensList.RefreshUI()


# --------------------------------------------------------------------------------- #

class DocBrowser(wx.Frame):  # Polemos: Refactored
    """Doc Browser frame."""

    def __init__(self, modName=None):
        """Intialize. modName -- current modname (or None)."""
        # Singleton
        singletons.docBrowser = self
        # Window
        pos = conf.settings['mash.modDocs.pos']
        size = conf.settings['mash.modDocs.size']
        wx.Frame.__init__(self, singletons.mashFrame, -1, _('Doc Browser'), pos, size, style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour(wx.NullColour)
        self.SetIcons(singletons.images['mash.main.ico'].GetIconBundle())
        self.SetSizeHints(250, 250)
        # Data
        self.modName = modName
        self.data = mosh.modInfos.table.getColumn('doc')
        self.docEdit = mosh.modInfos.table.getColumn('docEdit')
        self.docType = None
        self.docIsWtxt = False
        # Contents
        self.modNameBox = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.modNameList = wx.ListBox(self, -1, choices=sorted(self.data.keys()), style=wx.LB_SINGLE | wx.LB_SORT)
        self.setButton = wx.Button(self, ID_SET, _("Set Doc..."))
        self.forgetButton = wx.Button(self, wx.ID_DELETE, _("Forget Doc..."))
        self.renameButton = wx.Button(self, ID_RENAME, _("Rename Doc..."))
        self.editButton = wx.ToggleButton(self, ID_EDIT, _("Edit Doc..."))
        self.prevButton = wx.Button(self, ID_BACK, "<<")
        self.nextButton = wx.Button(self, ID_NEXT, ">>")
        self.docNameBox = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.plainText = wx.TextCtrl(self, -1, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH2)
        self.htmlText = wx.lib.iewin.IEHtmlWindow(self, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)  # iewin
        # --Layout
        self.mainSizer = vSizer(
            (hSizer(  # --Buttons
                (self.setButton, 0, wx.GROW),
                (self.forgetButton, 0, wx.GROW),
                (self.renameButton, 0, wx.GROW),
                (self.editButton, 0, wx.GROW),
                (self.prevButton, 0, wx.GROW),
                (self.nextButton, 0, wx.GROW),
            ), 0, wx.GROW | wx.ALL ^ wx.BOTTOM, 4),
            (hSizer(  # --Mod name, doc name
                (self.docNameBox, 2, wx.GROW),
            ), 0, wx.GROW | wx.TOP | wx.BOTTOM, 4),
            (self.plainText, 3, wx.GROW),
            (self.htmlText, 3, wx.GROW),
        )
        sizer = hSizer(
            (vSizer(
                (self.modNameBox, 0, wx.GROW),
                (self.modNameList, 1, wx.GROW | wx.TOP, 4),
            ), 0, wx.GROW | wx.TOP | wx.RIGHT, 4),
            (self.mainSizer, 1, wx.GROW),
        )
        # --Set
        self.SetSizer(sizer)
        self.SetMod(modName)
        self.SetDocType('txt')
        # --Events
        self.modNameList.Bind(wx.EVT_LISTBOX, self.DoSelectMod)
        wx.EVT_BUTTON(self.setButton, ID_SET, self.DoSet)
        wx.EVT_BUTTON(self.forgetButton, wx.ID_DELETE, self.DoForget)
        wx.EVT_BUTTON(self.renameButton, ID_RENAME, self.DoRename)
        wx.EVT_TOGGLEBUTTON(self.editButton, ID_EDIT, self.DoEdit)
        wx.EVT_BUTTON(self.prevButton, ID_BACK, self.DoPrevPage)
        wx.EVT_BUTTON(self.nextButton, ID_NEXT, self.DoNextPage)
        wx.EVT_CLOSE(self, self.OnCloseWindow)

    def GetIsWtxt(self, docPath=None):
        """Determines whether specified path is a wtxt file."""
        docPath = docPath or self.data.get(self.modName, '')
        if not os.path.exists(docPath): return False
        textFile = open(docPath)
        maText = re.match(r'^=.+=#\s*$', textFile.readline())
        textFile.close()
        return (maText is not None)

    def DoHome(self, event):
        """Handle "Home" button click."""
        self.htmlText.GoHome()

    def DoPrevPage(self, event):
        """Handle "Back" button click."""
        self.htmlText.GoBack()

    def DoNextPage(self, event):
        """Handle "Next" button click."""
        self.htmlText.GoForward()

    def DoEdit(self, event):
        """Handle "Edit Doc" button click."""
        self.DoSave()
        editing = self.editButton.GetValue()
        self.docEdit[self.modName] = editing
        self.docIsWtxt = self.GetIsWtxt()
        if self.docIsWtxt:
            self.SetMod(self.modName)
        else:
            self.plainText.SetEditable(editing)

    def DoForget(self, event):
        """Handle "Forget Doc" button click. Sets help document for current mod name to None."""
        # --Already have mod data?
        modName = self.modName
        if modName not in self.data: return
        index = self.modNameList.FindString(modName)
        if index != wx.NOT_FOUND: self.modNameList.Delete(index)
        del self.data[modName]
        self.SetMod(modName)

    def DoSelectMod(self, event):
        """Handle mod name combobox selection."""
        self.SetMod(event.GetString())

    def DoSet(self, event):
        """Handle "Set Doc" button click."""
        # --Already have mod data?
        modName = self.modName
        if modName in self.data:
            (docsDir, fileName) = os.path.split(self.data[modName])
        else:
            docsDir = (conf.settings['mash.modDocs.dir'] or os.path.join(conf.settings['mwDir'], 'Data Files'))
            fileName = ''
        # --Dialog
        dialog = wx.FileDialog(self, _("Select doc for %s:") % (modName,), docsDir, fileName, '*.*', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return None
        path = dialog.GetPath()
        dialog.Destroy()
        conf.settings['mash.modDocs.dir'] = os.path.split(path)[0]
        if modName not in self.data: self.modNameList.Append(modName)
        self.data[modName] = path
        self.SetMod(modName)

    def DoRename(self, event):
        """Handle "Rename Doc" button click."""
        modName = self.modName
        oldPath = self.data[modName]
        (workDir, fileName) = os.path.split(oldPath)
        # --Dialog
        dialog = wx.FileDialog(self, _("Rename file to:"), workDir, fileName, '*.*',
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return None
        path = dialog.GetPath()
        dialog.Destroy()
        # --OS renaming
        if path.lower() == oldPath.lower(): return
        if os.path.exists(path): os.remove(path)
        os.rename(oldPath, path)
        if self.docIsWtxt:
            oldHtml, newHtml = (os.path.splitext(xxx)[0] + '.html' for xxx in (oldPath, path))
            if os.path.exists(newHtml): os.remove(newHtml)
            if os.path.exists(oldHtml): os.rename(oldHtml, newHtml)
        # --Remember change
        conf.settings['mosh.workDir'] = os.path.split(path)[0]
        self.data[modName] = path
        self.SetMod(modName)

    def DoSave(self):
        """Saves doc, if necessary."""
        if not self.plainText.IsModified(): return
        docPath = self.data.get(self.modName, '')
        self.plainText.SaveFile(docPath)
        self.plainText.DiscardEdits()
        if self.docIsWtxt:
            from . import wtxt
            docsDir = os.path.join((mosh.modInfos.dir).encode('utf-8'), 'Docs')
            wtxt.genHtml(docPath, cssDir=docsDir)

    def SetMod(self, modName):
        """Sets the mod to show docs for."""
        # --Save Current Edits
        self.DoSave()
        # --New modName
        self.modName = modName
        # --ModName
        if modName:
            self.modNameBox.SetValue(modName)
            index = self.modNameList.FindString(modName)
            self.modNameList.SetSelection(index)
            self.setButton.Enable(True)
        else:
            self.modNameBox.SetValue('')
            self.modNameList.SetSelection(wx.NOT_FOUND)
            self.setButton.Enable(False)
        # --Doc Data
        docPath = self.data.get(modName, '')
        docExt = os.path.splitext(docPath)[1].lower()
        self.docNameBox.SetValue(os.path.basename(docPath))
        self.forgetButton.Enable(docPath != '')
        self.renameButton.Enable(docPath != '')
        # --Edit defaults to false.
        self.editButton.SetValue(False)
        self.editButton.Enable(False)
        self.plainText.SetEditable(False)
        self.docIsWtxt = False
        # --View/edit doc.
        if not docPath:
            self.plainText.SetValue('')
            self.SetDocType('txt')
        elif not os.path.exists(docPath):
            myTemplate = os.path.join(mosh.modInfos.dir, 'Docs', _('My Readme Template.txt'))
            mashTemplate = os.path.join(mosh.modInfos.dir, 'Docs', _('Mash Readme Template.txt'))
            if os.path.exists(myTemplate):
                template = ''.join(open(myTemplate).readlines())
            elif os.path.exists(mashTemplate):
                template = ''.join(open(mashTemplate).readlines())
            else:
                template = '= $modName ' + ('=' * (74 - len(modName))) + '#\n' + docPath
            defaultText = string.Template(template).substitute(modName=modName)
            self.plainText.SetValue(defaultText)
            self.SetDocType('txt')
            if docExt in {'.txt', '.etxt'}:
                self.editButton.Enable(True)
                editing = self.docEdit.get(modName, True)
                self.editButton.SetValue(editing)
                self.plainText.SetEditable(editing)
            self.docIsWtxt = (docExt == '.txt')
        elif docExt in {'.htm', '.html', '.mht'}:
            self.htmlText.Navigate(docPath)
            self.SetDocType('html')
        else:
            self.editButton.Enable(True)
            editing = self.docEdit.get(modName, False)
            self.editButton.SetValue(editing)
            self.plainText.SetEditable(editing)
            self.docIsWtxt = self.GetIsWtxt(docPath)
            htmlPath = self.docIsWtxt and (os.path.splitext(docPath)[0] + '.html')
            if htmlPath and (not os.path.exists(htmlPath) or
                             (os.path.getmtime(docPath) > os.path.getmtime(htmlPath))):
                from . import wtxt
                docsDir = os.path.join(mosh.modInfos.dir, 'Docs')
                wtxt.genHtml(docPath, cssDir=docsDir)
            if not editing and htmlPath and os.path.exists(htmlPath):
                self.htmlText.Navigate(htmlPath)
                self.SetDocType('html')
            else:
                self.plainText.LoadFile(docPath)
                self.SetDocType('txt')

    def SetDocType(self, docType):  # --Set Doc Type
        """Shows the plainText or htmlText view depending on document type (i.e. file name extension)."""
        if docType == self.docType: return
        sizer = self.mainSizer
        if docType == 'html':
            sizer.Show(self.plainText, False)
            sizer.Show(self.htmlText, True)
            self.prevButton.Enable(True)
            self.nextButton.Enable(True)
        else:
            sizer.Show(self.plainText, True)
            sizer.Show(self.htmlText, False)
            self.prevButton.Enable(False)
            self.nextButton.Enable(False)
        self.Layout()

    def OnCloseWindow(self, event):  # --Window Closing
        """Handle window close event. Remember window size, position, etc."""
        self.DoSave()
        conf.settings['mash.modDocs.show'] = False
        if not self.IsIconized() and not self.IsMaximized():
            conf.settings['mash.modDocs.pos'] = self.GetPosition()
            conf.settings['mash.modDocs.size'] = self.GetSizeTuple()
        self.Destroy()


# ------------------------------------------------------------------------------

class JournalBrowser(wx.Frame):  # Polemos: Small OCD edits.
    """Journal Browser frame."""

    def __init__(self, saveName=None):
        """Intialize. saveName -- current saveName (or None)."""
        # --Data
        self.saveName = saveName
        self.data = None
        self.counter = 0
        # --Singleton
        singletons.journalBrowser = self
        # --Window
        pos = conf.settings['mash.journal.pos']
        size = conf.settings['mash.journal.size']
        wx.Frame.__init__(self, singletons.mashFrame, -1, _('Journal'), pos, size, style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour(wx.NullColour)
        self.SetSizeHints(250, 250)
        # --Application Icons
        self.SetIcons(singletons.images['mash.main.ico'].GetIconBundle())
        self.htmlText = wx.lib.iewin.IEHtmlWindow(self, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)  # iewin
        # Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.htmlText, 1, wx.GROW)
        self.SetSizer(mainSizer)
        # --Events
        wx.EVT_CLOSE(self, self.OnCloseWindow)
        # --Set
        self.SetSave(saveName)

    def SetSave(self, saveName):
        """Sets the mod to show docs for."""
        self.saveName = saveName
        if not saveName:
            text = ''
        elif saveName in mosh.saveInfos:
            text = mosh.saveInfos[saveName].getJournal()
        else:
            text = _('[Savefile %s not found.]') % (saveName,)
        self.htmlText.LoadString(text)

    def OnCloseWindow(self, event):  # --Window Closing
        """Handle window close event. Remember window size, position, etc."""
        conf.settings['mash.journal.show'] = False
        if not self.IsIconized() and not self.IsMaximized():
            conf.settings['mash.journal.pos'] = self.GetPosition()
            conf.settings['mash.journal.size'] = self.GetSizeTuple()
        self.Destroy()


# ------------------------------------------------------------------------------

class MashApp(object):
    """Mash Application class."""

    # Polemos: Added settings, file check, updates check, mlox detection,
    # OpenMW/TES3mp support, User profile, theme, more...

    def OnInit(self):
        """wxWindows: Initialization handler."""
        # Check if another Wrye Mash instance is already running.
        if not self.chkInstance(): return False
        # Load saved configuration (if it exists).
        InitSettings()  # conf.settings['...'] are known from here.
        # Set current (true) Wrye Mash dir.
        singletons.MashDir = appinfo.MashDir
        # Credits and License
        self.appInfo()
        # Current Wrye Mash version:
        conf.settings['mash.version'] = Current_Version()
        # OpenMW switch.
        conf.settings['openmw'] = openmw_enabled()
        # Check/Set mwDir or OpenMW/TES3mp dir.
        if not conf.settings['openmw']:  # Regular Morrowind
            if not self.SetMWDir(): return False
            conf.settings['wizard.first.mw'] = False
        if conf.settings['openmw']:  # OpenMW/TES3mp support
            if not all([self.SetopenMWDir(), self.detectopenmw_profile()]): return False
            conf.settings['mashdir'] = os.path.join(conf.settings['datamods'], 'Mashdir')
            conf.settings['wizard.first.openmw'] = False
        # Init theme engine
        gui.interface.ThemeEngine(conf.settings['active.theme'])
        # Check Wrye Mash Profile.
        mprofile.user_profile()
        # From here we are sure that mwDir or openMWdir is correct.
        conf.settings['all.ok'] = True
        InitDirs()
        # Exit if Installers dir is not set.
        if not conf.settings['all.ok']: return False
        # Check for updates.
        check_version()
        # Init Menus.
        if conf.settings['mash.col.menu.enabled']:
            InitLinks()
        else:
            InitLinks_no_col_menu()
        # Init images.
        InitImages()
        # Init colors.
        InitColors()
        # Mlox/Mlox64 detect/set.
        setmlox()
        # --Init Data
        self.InitData()
        self.InitVersion()
        # --Locale
        wx.Locale(wx.LANGUAGE_DEFAULT)
        # --WMFrame
        frame = MashFrame(pos=conf.settings['mash.framePos'], size=conf.settings['mash.frameSize'])
        appinfo.app.SetTopWindow(frame)
        frame.Show()
        # --Error log
        from . import errorlog
        errorlog.ErrorLog(frame)
        # --DocBrowser, JournalBrowser, HelpDialog
        if conf.settings['mash.modDocs.show']: DocBrowser().Show()
        if conf.settings['mash.journal.show']: JournalBrowser().Show()
        if conf.settings.get('mash.help.show'): guidialog.HelpDialog(singletons.mashFrame,
                                                                      singletons.images, conf.settings['mash.help.pos'],
                                                                      conf.settings['mash.help.size']).Show()
        # Notify that all is ok.
        return True

    def chkInstance(self):
        """Check if there is only one instance of Wrye Mash running."""
        self.name = 'WryeMash2018-Polemos-fork-21061979-%s' % wx.GetUserId()
        self.instance = wx.SingleInstanceChecker(self.name)
        if self.instance.IsAnotherRunning():
            msg = u'Another instance of Wrye Mash is already running!!!'
            wx.MessageBox(msg, u'Quitting...', style=wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
            print('%s: [Warning] %s' % (datetime.now(), msg))
            return False
        return True

    def SetMWDir(self):  # Polemos: Self detection breaks so many things... let the system give the correct encoding.
        """Configuration process for Regular Morrowind. Called by OnInit()."""
        while True:
            # Already set?
            if os.path.exists(os.path.join(conf.settings['mwDir'], 'Morrowind.ini')): return True
            if conf.settings['wizard.first.mw']:  # Welcome!
                if not guidialog.WelcomeDialog(None, _('Welcome to Wrye Mash %s.' % conf.settings['mash.version'][3]),
                                                _('Click OK to start Wrye Mash configuration wizard.')).ShowModal(): return False
            else:  # Problems, notify user.
                guidialog.ErrorMessage(None, _('There'
                                                u' is something wrong with your settings.\n\nClick OK to start Wrye Mash configuration wizard.'))
            while True:
                if WizardDialog().ShowModal():
                    MWdir = os.path.join(conf.settings['mwDir'], 'Morrowind.ini')
                    # Everything OK?
                    if os.path.exists(MWdir):
                        mosh.dirs['app'] = GPath(MWdir)
                        return True
                    # Retry?
                    if guidialog.ErrorQuery(None, _('Morrowind.ini not found in %s! Try again or quit?') % (MWdir,),
                                             _('Try again or quit?')) != wx.ID_YES: return False
                else:
                    return False

    def SetopenMWDir(self):  # Polemos: OpenMW/Tes3MP support.
        """Configuration process for OpenMW/Tes3MP. Called by OnInit()."""
        while True:
            # Already set?
            if self.CheckopenMWDirs(): return True
            if conf.settings['wizard.first.openmw']:  # Welcome!
                if not guidialog.WelcomeDialog(None, _('Welcome to Wrye Mash %s.' % conf.settings['mash.version'][3]),
                                                _('Click OK to start the OpenMW/Tes3MP settings wizard.')).ShowModal(): return False
            else:  # Problems, notify user.
                guidialog.ErrorMessage(None, _('There is something wrong'
                                                u' with your settings.\n\nClick OK to start the OpenMW/Tes3MP settings wizard.'))
            while True:
                if WizardDialog().ShowModal():
                    # Everything OK?
                    errors = self.CheckopenMWDirs('advanced')
                    if not errors:
                        return True
                    else:
                        problems = (',\n'.join(errors) + '.')
                    # Retry?
                    if guidialog.ErrorQuery(None, _('Problems occurred! Try again or quit?\n\n%s' % problems),
                                             _('Try again or quit?')) != wx.ID_YES: return False
                else:
                    return False

    def setopenmw_profile(self):  # Polemos: OpenMW/Tes3MP.
        """Dialog to select OpenMW profile directory."""
        while True:
            openmwprofileDirDialog = wx.DirDialog(None, _("Select your OpenMW profile directory."))
            result = openmwprofileDirDialog.ShowModal()
            openmwprofileDir = openmwprofileDirDialog.GetPath()
            openmwprofileDirDialog.Destroy()
            if result == wx.ID_OK:  # --Valid OpenMW profile directory?
                if os.path.isfile(os.path.join(openmwprofileDir, 'openmw.cfg')):
                    conf.settings['openmwprofile'] = openmwprofileDir
                    return True
                else:
                    msg = _('Openmw.cfg was not found in OpenMW Profile directory. Try again?')
            else:  # --User canceled?
                msg = _('OpenMW profile directory was not declared! Try again?')
            # --Retry?
            if guidialog.WarningQuery(None, msg, _('OpenMW Profile Directory.')) != wx.ID_YES: return False

    def detectopenmw_profile(self):  # Polemos: OpenMW/Tes3MP.
        """Detect OpenMW profile directory."""
        try:
            if os.path.isfile(os.path.join(conf.settings['openmwprofile'], 'openmw.cfg')): return True
        except:
            pass
        if conf.settings['wizard.first.openmw']: return False
        choice = guidialog.ManualDetectDialog(None, _("There was a problem locating OpenMW profile folder.\n"
                                                       u"(Openmw.cfg and 'Saves' dir reside there).\n\nHow do you wish to proceed?"),
                                               _('OpenMW Profile Directory not found!'))
        if choice == wx.ID_NO:
            return self.setopenmw_profile()
        elif choice == wx.ID_YES:
            try:
                user = os.environ['USERPROFILE']
                openmwcfg = os.path.join(user, 'Documents', 'my games', 'openmw')
                test_openmwcfg = os.path.join(user, 'Documents', 'my games', 'openmw', 'openmw.cfg')
                if os.path.exists(test_openmwcfg):
                    conf.settings['openmwprofile'] = openmwcfg
                    return True
            except:
                if guidialog.WarningQuery(None, _('Failed to autodetect OpenMW Profile folder! Search manually?'),
                                           _('OpenMW profile Directory')) == wx.ID_YES: return self.setopenmw_profile()
        return False

    def CheckopenMWDirs(self, mode='simple'):  # Polemos: OpenMW/Tes3MP.
        """Check if OpenMW/Tes3MP directories exist and if they are valid(where possible)."""
        # Set directory variables (Try/Except is for Unicode sanity).
        try:
            tes3mpdir = (_('TES3mp executable not found'), os.path.join(conf.settings['openmwDir'], 'tes3mp.exe'))
        except:
            tes3mpdir = (_('TES3mp  executable not found'), None)
        try:
            TES3mpConf = (_('TES3mp profile (pluginlist.json) not found'), conf.settings['TES3mpConf'])
        except:
            TES3mpConf = (_('TES3mp profile (pluginlist.json) not found'), None)
        try:
            openmwDir = (
                _('OpenMW Launcher not found'), os.path.join(conf.settings['openmwDir'], 'openmw-launcher.exe'))
        except:
            openmwDir = (_('OpenMW Launcher not found'), None)
        try:
            mods = (_('"Mods" folder not found'), conf.settings['datamods'])
        except:
            mods = (_('"Mods" folder not found'), None)
        try:
            downloads = (_('"Downloads" folder not found'), conf.settings['downloads'])
        except:
            downloads = (_('"Downloads" folder not found'), None)
        try:
            openmwprofile = (_('OpenMW profile folder not found'), conf.settings['openmwprofile'])
        except:
            openmwprofile = (_('OpenMW profile folder not found'), None)
        # Check if TES3mp is enabled.
        if conf.settings['tes3mp']:  # TES3mp enabled?
            openmw_paths = dict((tes3mpdir, openmwDir, mods, downloads, openmwprofile, TES3mpConf,))
        elif not conf.settings['tes3mp']:  # Regular OpenMW.
            openmw_paths = dict((openmwDir, mods, downloads, openmwprofile,))
        # Simple or advanced check.
        if mode == 'simple':
            try:
                if not [x for x in [os.path.exists(openmw_paths[x]) for x in openmw_paths] if not x]:
                    return True
                else:
                    return False
            except:
                return False
        elif mode == 'advanced':
            return [x for x in openmw_paths if openmw_paths[x] is None or not os.path.exists(openmw_paths[x])]

    def InitData(self):  # Polemos: OpenMW/TES3mp support
        """Inits variables and Redirects initializations. Called by OnInit()."""
        conf.settings['custom.commands.refresh'] = True
        conf.settings['custom.commands.cache'] = {}
        if not conf.settings['openmw']:
            self.InitData_regular()
        elif conf.settings['openmw']:
            self.InitData_openmw()

    def InitData_regular(self):  # Polemos: for Morrowind support
        """Initialize all data. Called by OnInit() for regular morrowind."""
        mwDir = conf.settings['mwDir']
        mosh.dirs['app'] = GPath(mwDir)
        mosh.mwIniFile = mosh.MWIniFile(mwDir)
        mosh.mwIniFile.refresh()
        mosh.modInfos = mosh.ModInfos(os.path.join(mwDir, 'Data Files'))
        mosh.modInfos.refresh()
        mosh.saveInfos = mosh.SaveInfos(os.path.join(mwDir, 'Saves'))
        mosh.saveInfos.refresh()

    def InitData_openmw(self):  # Polemos: for OpenMW/TES3mp support
        """Initialize all data. Called by OnInit() for openmw/tes3mp."""
        mwDir = conf.settings['openmwDir']
        mosh.dirs['app'] = GPath(mwDir)  # openmw dir location
        mosh.mwIniFile = mosh.MWIniFile(conf.settings['openmwprofile'])  # openmw.cfg location
        mosh.mwIniFile.refresh()
        mosh.modInfos = mosh.ModInfos(mwDir)  # openmw.cfg location
        mosh.modInfos.refresh()
        mosh.saveInfos = mosh.SaveInfos(os.path.join(conf.settings['openmwprofile'], 'Saves'))
        mosh.saveInfos.refresh()

    def appInfo(self):
        """Saves/Updates Wrye Mash License and Credits."""
        from .gui.credits import protoLicence, protoSource, protoGNU
        from stat import S_IWUSR, S_IREAD
        try:
            sources = {
                os.path.join(singletons.MashDir, 'License.txt'): '\n'.join([x[0].rstrip() for x in protoLicence()]),
                os.path.join(singletons.MashDir, 'Credits.txt'): '\n'.join([x[0].rstrip() for x in protoSource()]),
                os.path.join(singletons.MashDir, 'gpl.txt'): protoGNU()}
            for src in sources.keys():
                if os.path.isfile(src):
                    os.chmod(src, S_IWUSR | S_IREAD)
                with io.open(src, 'w', encoding='utf8') as fl:
                    fl.write(sources[src])
        except:
            pass

    def InitVersion(self):
        """Perform any version to version conversion. Called by OnInit()."""
        version = conf.settings['mash.version'][0]
        # --Version 0.42: MTimes from settings to ModInfos.table.
        if version < 42:
            mtimeKey = 'mosh.modInfos.mtimes'
            if mtimeKey in conf.settings:
                modCol = mosh.modInfos.table.getColumn('mtime')
                for key, value in conf.settings[mtimeKey].items():
                    modCol[key] = value[0]
                del conf.settings[mtimeKey]
        # --Version 0.50 (0.60?): Genre to group
        if version < 60:
            colGenre = mosh.modInfos.table.getColumn('genre')
            colGroup = mosh.modInfos.table.getColumn('group')
            for fileName in colGenre.keys():
                colGroup[fileName] = colGenre[fileName]
                del colGenre[fileName]
                print(fileName)
            if conf.settings['mash.mods.sort'] == 'Genre': conf.settings['mash.mods.sort'] = 'Group'
            colWidths = conf.settings['mash.mods.colWidths']
            if 'Genre' in colWidths:
                colWidths['Group'] = colWidths['Genre']
                del colWidths['Genre']
                conf.settings.setChanged('mash.mods.colWidths')
        # --Version 0.71: Convert refRemoversdata to tuples
        if version < 71 and 'mash.refRemovers.data' in conf.settings:
            import types
            data = conf.settings['mash.refRemovers.data']
            for remover, path in data.items():
                if isinstance(path, str):
                    data[remover] = (path,)
            conf.settings.setChanged('mash.refRemovers.data')


# Links -----------------------------------------------------------------------
# class Link(object):
#    """Abstract class for a menuitem or button. These objects are added to a
#    list, and the menuitems are then built on demand through the AppendToMenu
#    method. Execution of the command is carried out by the Do method.
#
#    Design allows control items to be created by 1) defining link classes, and
#    2) creating link objects all at once in an initLinks method. This design
#    keeps link coding from being buried in the interface that it's attached to.
#    """
#    def __init__(self):
#        self.id = None
#
#    def AppendToMenu(self,menu,window,data):
#        self.window = window
#        self.data = data
#        if not self.id: self.id = wx.NewId()
#        wx.EVT_MENU(window,self.id,self.Execute)
#
#    def Execute(self, event):
#        """Event: link execution."""
#        raise mosh.AbstractError
#
##------------------------------------------------------------------------------
# class SeparatorLink(Link):
#    """Menu item separator line."""
#    def AppendToMenu(self,menu,window,data):
#        menu.AppendSeparator()
#
##------------------------------------------------------------------------------
# class MenuLink(Link):
#    """Submenu. Create this and then add other menu items to its links member."""
#    def __init__(self,name):
#        Link.__init__(self)
#        self.name = name
#        self.links = []
#
#    def AppendToMenu(self,menu,window,data):
#        subMenu = wx.Menu()
#        for link in self.links:
#            link.AppendToMenu(subMenu,window,data)
#        menu.AppendMenu(-1,self.name,subMenu)

def RefreshNotify(parent=None, text=u'Installer/package is missing. Click OK to auto-refresh catalog.'):  # Polemos
    """Notify and refresh."""
    guidialog.ErrorMessage(parent, text)
    singletons.gInstallers.refreshed = False
    singletons.gInstallers.fullRefresh = False
    singletons.gInstallers.OnShow()


# Files Links -----------------------------------------------------------------

class Files_Open(Link):  # Polemos: typos.. and main menu compatibility.
    """Opens "data files" directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open "Data Files" dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
            dir = GPath(self.window.data.dir)
        except:
            dir = mosh.dirs['mods'] = mosh.dirs['app'].join('Data Files')
        if not dir.exists(): dir.makedirs()
        dir.start()


# ------------------------------------------------------------------------------

class Files_Open_saves_po(Link):  # Polemos: More personality for saves tab.
    """Opens saves directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open Saves dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = GPath(self.window.data.dir)
        if not dir.exists(): dir.makedirs()
        dir.start()


# ------------------------------------------------------------------------------

class Open_Datamods_po(Link):  # Polemos
    """Opens Datamods directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open Datamods dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = conf.settings['datamods']
        if not os.path.exists(dir): os.makedirs(dir)
        os.startfile(dir)


# ------------------------------------------------------------------------------

class Open_Packages_po(Link):  # Polemos
    """Opens Datamods directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open Downloads dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = conf.settings['downloads']
        if not os.path.exists(dir): os.makedirs(dir)
        os.startfile(dir)


# ------------------------------------------------------------------------------

class Files_Open_screens_po(Link):  # Polemos: More personality for screens tab.
    """Opens screenshots directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open Screenshots dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = mosh.screensData.dir
        if not dir.exists(): dir.makedirs()
        dir.start()


# ------------------------------------------------------------------------------

class move_screens_po(Link):  # Polemos: New action for Screenshots. Not implemented yet  todo: implement this
    """Moves screenshots to the new screenshots directory."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Move Screenshots'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        mwdir = GPath(mosh.settings['mwDir'])
        dir = mosh.screensData.dir
        os.rename("path/to/current/file.foo", "path/to/new/destination/for/file.foo")


# ------------------------------------------------------------------------------

class Files_Open_installers_po(Link):  # Polemos: For installers tab.
    """Opens data directory in explorer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open Installers dir'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = mosh.dirs['installers']
        if not dir.exists(): dir.makedirs()
        dir.start()


# ------------------------------------------------------------------------------

class Files_SortBy(Link):  # Polemos: Modified to translate "#" into "Load order" in columns.
    """Sort files by specified key (sortCol)."""

    def __init__(self, sortCol, prefix=''):
        Link.__init__(self)
        self.sortCol = sortCol
        self.sortName = conf.settings['mash.colNames'][sortCol]
        self.prefix = prefix
        if self.sortCol == 'Load Order': self.sortCol = '#'
        if self.sortName == '    File': self.sortName = 'File'  # wx.Reasons.

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, self.prefix + self.sortName, kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if window.sort == self.sortCol or (self.sortCol == '#' and window.sort == 'Load Order'): menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        self.window.PopulateItems(self.sortCol, -1)
        try:
            singletons.MenuBar.saves_view_cond()
        except:
            pass


# ------------------------------------------------------------------------------

class Masters_SortBy(Link):  # Polemos
    """Sort Masters by specified key (sortCol)."""

    def __init__(self, sortCol, prefix=''):
        """Init."""
        Link.__init__(self)
        self.sortCol = sortCol
        self.sortName = conf.settings['mash.colNames'][sortCol]
        self.prefix = prefix
        if self.sortCol == 'Load Order': self.sortCol = '#'
        if self.sortName == 'Master': self.sortName = 'Name'

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, self.prefix + self.sortName, kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if window.sort == self.sortCol or (self.sortCol == '#' and window.sort == 'Load Order'): menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        self.window.PopulateItems(self.sortCol, -1)


# ------------------------------------------------------------------------------
class Mods_Tes3cmd_multipatch(Link):  # Polemos: Added Create Multipatch option with tes3cmd.
    """Create Multipatch with TES3cmd."""

    def AppendToMenu(self, menu, window, data):
        self.window = window
        menuItem = menu.Append(wx.ID_ANY, _('Create MultiPatch'))  # Multiverse...
        menuId = menuItem.GetId()
        wx.EVT_MENU(window, menuId, self.Execute)
        if not tes3cmd.getLocation(): menuItem.Enable(False)

    def Execute(self, event):  # Polemos: fixes and more.
        try:
            test = self.window
        except:
            self.window = singletons.modList
        # User warnings
        if not tes3cmd.getLocation():
            guidialog.ErrorMessage(self.window, _("Couldn't find tes3cmd.exe to launch"))
            return
        if guidialog.WarningQuery(self.window, _('This might take a while. '
                                                  u'Are you sure you wish to continue?'),
                                   _('TES3cmd')) != wx.ID_YES: return
        # Begin
        cmd = tes3cmd.Basic()
        t3_thread = Thread(target=cmd.multipatch)
        t3_thread.start()
        with wx.WindowDisabler():
            wait = wx.BusyInfo('Please wait for TES3CMD to finish (this may take some time)...')
            while t3_thread.isAlive(): wx.GetApp().Yield()
        del wait
        TES3cmd_log = guidialog.AdvLog(self.window, _('TES3cmd MultiPatch'), 'TES3cmd.log', 'MultiPatch')
        # Stderr
        if cmd.err:
            TES3cmd_log.write(_('\nErrors:\n-------\n'), 'RED')
            [TES3cmd_log.write(line, 'RED') for line in cmd.err]
            TES3cmd_log.write('\n\n')
        # Stdout
        if cmd.out:
            TES3cmd_log.write(_('\nOutput:\n--------\n'))
            [TES3cmd_log.write(line) for line in cmd.out]
        TES3cmd_log.finished()
        # Finished
        TES3cmd_log.ShowModal()
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class Mods_Tes3cmd_restore(Link):  # Polemos: added restore to tes3cmd. Compatible with menubar.
    """Restore tes3cmd backup file(s). (Move files back to Data Files.)"""

    def __init__(self, type='mod'):
        """Init."""
        Link.__init__(self)
        self.type = type

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Restore modified files'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
            self.type = 'mod'
        source_moved_po = ''
        destDir = self.window.data.dir.strip()
        srcDir = '%s\\' % os.path.join(destDir, 'tes3cmdbck')
        if self.type == 'mod':
            wildcard = u'Morrowind Mod Files (*.esp;*.esm)|*.esp;*.esm'
        elif self.type == 'save':
            wildcard = u'Morrowind Save files (*.ess)|*.ess'
        else:
            wildcard = '*.*'
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        dialog = wx.FileDialog(self.window, message=u'Restore files:', defaultDir=srcDir, defaultFile='',
                               wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        srcPaths = dialog.GetPaths()
        dialog.Destroy()
        for srcPath in srcPaths:
            (newSrcDir, srcFileName) = os.path.split(srcPath)
            if newSrcDir.lower() == destDir.lower():
                guidialog.ErrorMessage(self.window, _("You can't restore files from this directory."))
                return
            destPath = os.path.join(destDir, srcFileName)
            if os.path.exists(destPath):
                source_moved_po = '%s\n%s' % (source_moved_po, srcFileName)
                shutil.move(srcPath, destPath)
            else:
                shutil.move(srcPath, destPath)
        guidialog.InfoMessage(self.window, _('Restored:\n%s\n') % (source_moved_po,))
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class Files_Unhide(Link):  # Polemos: made compatible with Menu bar.
    """Unhide file(s). (Move files back to Data Files or Save directory.)"""

    def __init__(self, type='mod'):
        Link.__init__(self)
        self.type = type

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Unhide..."))
        menu.AppendItem(menuItem)

    def Execute(self, event, mtype=None):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            if mtype == 'mod':
                self.window = singletons.modList
            elif mtype == 'save':
                self.window = singletons.saveList
        if mtype is not None: self.type = mtype
        destDir = self.window.data.dir
        srcDir = os.path.join(destDir, conf.settings['mosh.fileInfo.hiddenDir'])
        if self.type == 'mod':
            wildcard = u'Morrowind Mod Files (*.esp;*.esm)|*.esp;*.esm'
        elif self.type == 'save':
            wildcard = u'Morrowind Save files (*.ess)|*.ess'
        else:
            wildcard = '*.*'
        # --File dialog
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        dialog = wx.FileDialog(self.window, u'Unhide files:', srcDir, u'', wildcard, wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        srcPaths = dialog.GetPaths()
        dialog.Destroy()
        # --Iterate over Paths
        for srcPath in srcPaths:
            # --Copy from dest directory?
            (newSrcDir, srcFileName) = os.path.split(srcPath)
            if newSrcDir == destDir:
                guidialog.ErrorMessage(self.window, _("You can't unhide files from this directory."))
                return
            # --File already unhidden?
            destPath = os.path.join(destDir, srcFileName)
            if os.path.exists(destPath):
                guidialog.WarningMessage(self.window,
                                          _("File skipped: %s. File is already present.") % (srcFileName,))
            # --Move it?
            else:
                shutil.move(srcPath, destPath)
        # --Repopulate
        singletons.mashFrame.RefreshData()


# File Links ------------------------------------------------------------------

class File_Delete(Link):
    """Delete the file and all backups."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menu.AppendItem(wx.MenuItem(menu, self.id, _('Delete')))

    def Execute(self, event):
        """Handle menu selection."""
        message = _('Delete these files? This operation cannot be undone.')
        message += '\n* ' + '\n* '.join(sorted(self.data))
        dialog = wx.MessageDialog(self.window, message, _('Delete Files'),
                                  style=wx.YES_NO | wx.ICON_EXCLAMATION)
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        dialog.Destroy()
        # --Are mods?
        isMod = self.window.data[self.data[0]].isMod()
        # --Do it
        for fileName in self.data:
            self.window.data.delete(fileName)
        # --Refresh stuff
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Screen_Delete(Link):  # Polemos: Added "Delete screenshots".
    """Delete the Screenshot file(s) (only)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Delete...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(data) > 0)

    def Execute(self, event):
        """Handle menu selection."""
        screens_dir = mosh.screensData.dir
        screen_names = ''
        for x in self.data: screen_names += n_path(x) + '\n'
        # for x in map(GPath, self.data): screens_del.append(screens_dir.join(x))  # ???
        screens_del = [screens_dir.join(GPath(x)) for x in self.data]              # ???
        if len(self.data) == 0:
            return
        elif len(self.data) == 1:
            message = _('Delete this screenshot?\nThis operation cannot be undone:\n\n%s' % screen_names)
        elif len(self.data) >= 1:
            message = _('Delete these %s screenshots?\nThis operation cannot be undone:\n\n%s' % (
                len(self.data), screen_names))
        dialog = wx.MessageDialog(self.window, message, _('Delete Screenshots'),
                                  style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        dialog.Destroy()
        # --Are mods?
        for filepath in [GPath(item) for item in self.data]:
            self.window.data.delete(filepath)
        # --Refresh stuff
        singletons.screensList.RefreshUI()


# ------------------------------------------------------------------------------

class File_Duplicate(Link):
    """Create a duplicate of the file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Duplicate...'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        data = self.data
        fileName = data[0]
        fileInfo = self.window.data[fileName]
        (root, ext) = os.path.splitext(fileName)
        (destDir, destName, wildcard) = (fileInfo.dir, root + ' Copy' + ext, '*' + ext)
        if not os.path.exists(destDir): os.makedirs(destDir)
        dialog = wx.FileDialog(self.window, _('Duplicate as:'), destDir, destName, wildcard,
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        (destDir, destName) = os.path.split(dialog.GetPath())
        dialog.Destroy()
        if (destDir == fileInfo.dir) and (destName == fileName):
            guidialog.ErrorMessage(self.window, _("Files cannot be duplicated to themselves!"))
            return
        self.window.data.copy(fileName, destDir, destName, setMTime=True)
        if destName != fileName: self.window.data.table.copyRow(fileName, destName)
        if destDir == fileInfo.dir:
            self.window.Refresh(detail=fileName)
        else:
            self.window.Refresh()


# ------------------------------------------------------------------------------

class File_Hide(Link):
    """Hide the file. (Move it to Mash/Hidden directory.)"""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menu.AppendItem(wx.MenuItem(menu, self.id, _('Hide')))

    def Execute(self, event):
        """Handle menu selection."""
        tmessage = _('Hide these files?')
        message = _('Note that hidden files are simply moved to the Mash/Hidden subdirectory.')
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.hideFiles.continue',
                                    _('Hide Files')) != wx.ID_OK: return
        # --Do it
        destRoot = os.path.join(self.window.data.dir, conf.settings['mosh.fileInfo.hiddenDir'])
        fileInfos = self.window.data
        fileGroups = fileInfos.table.getColumn('group')
        for fileName in self.data:
            destDir = destRoot
            # --Use author subdirectory instead?
            author = fileInfos[fileName].tes3.hedr.author
            authorDir = os.path.join(destRoot, author)
            if author and os.path.isdir(authorDir):
                destDir = authorDir
            # --Use group subdirectory instead?
            elif fileName in fileGroups:
                groupDir = os.path.join(destRoot, fileGroups[fileName])
                if os.path.isdir(groupDir): destDir = groupDir
            if not self.window.data.moveIsSafe(fileName, destDir):
                message = (_('A file named %s already exists in the hidden files directory. Overwrite it?') % (
                    fileName,))
                if guidialog.WarningQuery(self.window, message, _('Hide Files')) != wx.ID_YES: continue
            self.window.data.move(fileName, destDir)
        # --Refresh stuff
        self.window.Refresh()


# ------------------------------------------------------------------------------

class File_MoveTo(Link):
    """Hide the file(s). I.e., move it/them to user selected directory."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menu.AppendItem(wx.MenuItem(menu, self.id, _('Move To...')))

    def Execute(self, event):
        """Handle menu selection."""
        destDir = os.path.join(self.window.data.dir, conf.settings['mosh.fileInfo.hiddenDir'])
        destDir = guidialog.DirDialog(self.window, _('Move To...'), destDir)
        if not destDir: return
        # --Do it
        fileInfos = self.window.data
        for fileName in self.data:
            if not self.window.data.moveIsSafe(fileName, destDir):
                message = (_('A file named %s already exists in the destination directory. Overwrite it?') % (
                    fileName,))
                if guidialog.WarningQuery(self.window, message, _('Hide Files')) != wx.ID_YES: continue
            self.window.data.move(fileName, destDir)
        # --Refresh stuff
        self.window.Refresh()


def formatdate64(value):  # Polemos: changed the date format to accommodate problematic locales.
    """Like formatDate() but avoid user errors when asked for redate."""
    return time.strftime("%m-%d-%Y %H:%M:%S", time.localtime(value))


# ------------------------------------------------------------------------------

class File_Redate(Link):  # Polemos fixes
    """Redate selected files from a specified date."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Redate...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        # --Get current start time.
        fileInfos = self.window.data
        # --Work out start time
        selInfos = [fileInfos[fileName] for fileName in self.data]
        selInfos.sort(key=lambda a: a.mtime)
        if len(selInfos):
            startTime = selInfos[0].mtime
        else:
            startTime = time.time()
        # --Ask user for revised time.
        start_time_po = formatdate64(int(startTime))
        dialog = guidialog.date_time_dialog(self.window,
                                             title=_('Redate Mod(s)'),
                                             caption=_('Redate selected mod(s) (24h hour format):'),
                                             datetime=start_time_po)
        newTimeStr = dialog.GetValue()
        if newTimeStr == time.strptime(newTimeStr, '%m-%d-%Y %H:%M:%S'): return
        try:
            newTimeTup = time.strptime(newTimeStr, '%m-%d-%Y %H:%M:%S')
            newTime = int(time.mktime(newTimeTup))
        except ValueError:
            guidialog.ErrorMessage(self.window, _('Unrecognized date: ') + newTimeStr)
            return
        except OverflowError:
            guidialog.ErrorMessage(self,
                                    _('Mash can only handle dates in between January 1, 1970 and January 19, 2038.'))
            return
        # --Do it
        for fileInfo in selInfos:
            fileInfo.setMTime(newTime)
            newTime += conf.settings['advanced.redate.interval']
        # --Refresh
        fileInfos.refreshDoubleTime()
        self.window.Refresh()


# ------------------------------------------------------------------------------

class File_Redate_Sys_Time(Link):  # By Abot, adapted by Polemos.
    """Redate selected files from current system time."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Redate from current system time'))
        menu.AppendItem(menuItem)
        if len(data) < 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        tmsg = _(
            u'This command will update the time of selected file(s), starting from current system time, keeping the same plugin order.')
        msg = _(
            u'It cannot be undone (at least, not in a single step).\n\nIt is meant to be used with files displayed in loading order.\n'
            u'If you know what you are doing, this function is great to sort/move entire groups of files that must be loaded last,'
            u' keeping the relative loading order (just ctrl+click or shift+click the files to organize).')
        if guidialog.ContinueQuery(self.window,
                                    tmsg, msg, 'query.redate.curtime.continue', _('Redate from current system time'),
                                    False) != wx.ID_OK: return
        # Scan
        fileInfos, newTime = self.window.data, time.time()
        # Do it
        for fileName in self.data:
            fileInfos[fileName].setMTime(newTime)
            newTime += conf.settings['advanced.redate.interval']
        # Refresh
        fileInfos.refreshDoubleTime()
        self.window.Refresh()


# ------------------------------------------------------------------------------

class File_Redate_Sel_Time(Link):  # By Abot, adapted by Polemos.
    """Redate selected files from selected file time."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Redate first selected file time'))
        menu.AppendItem(menuItem)
        if len(data) < 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        tmsg = _(
            u'This command will update the time of selected files, starting from the time of first selected file, keeping the same file order.')
        msg = _(
            u'It cannot be undone (at least, not in a single step).\nIt is meant to be used with files displayed in loading order.\n'
            u'If you know what you are doing, this function is great to sort/move entire groups of files keeping the relative loading order '
            u'(just ctrl+click or shift+click the files to organize).')
        if guidialog.ContinueQuery(self.window,
                                    tmsg, msg, 'query.redate.fltime.continue', _('Redate first selected file time'),
                                    False) != wx.ID_OK: return
        # Scan for earliest date
        fileInfos = self.window.data
        newTime = fileInfos[self.data[0]].mtime
        for fileName in self.data:
            newTime = min(newTime, fileInfos[fileName].mtime)
        # Do it
        for fileName in self.data:
            fileInfos[fileName].setMTime(newTime)
            newTime += conf.settings['advanced.redate.interval']
        # Refresh
        fileInfos.refreshDoubleTime()
        self.window.Refresh()


# ------------------------------------------------------------------------------

class File_Sort(Link):
    """Sort the selected files."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Sort'))
        menu.AppendItem(menuItem)
        if len(data) < 2: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        interval = conf.settings['advanced.redate.interval']
        tmessage = _('This command will sort the selected files alphabetically,'
                     u' assigning\n them dates %s seconds apart each other.' % interval)
        message = _('It cannot be undone.\n\nNote that some mods need to be '
                    u'in a specific order to work correctly, and this sort operation may break that order.')
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.sortMods.continue',
                                    _('Sort Mods')) != wx.ID_OK: return
        # --Scan for earliest date
        fileInfos = self.window.data
        newTime = min(fileInfos[fileName].mtime for fileName in self.data)
        # --Do it
        for fileName in sorted(self.data, key=lambda a: a[:-4].lower()):
            fileInfos[fileName].setMTime(newTime)
            newTime += interval
        # --Refresh
        fileInfos.refreshDoubleTime()
        self.window.Refresh()


# ------------------------------------------------------------------------------

class File_Snapshot(Link):
    """Take a snapshot of the file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Snapshot...'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        pass
        data = self.data
        fileName = data[0]
        fileInfo = self.window.data[fileName]
        (destDir, destName, wildcard) = fileInfo.getNextSnapshot()
        if not os.path.exists(destDir): os.makedirs(destDir)
        dialog = wx.FileDialog(self.window, _('Save snapshot as:'), destDir, destName, wildcard,
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        (destDir, destName) = os.path.split(dialog.GetPath())
        dialog.Destroy()
        # --Extract version number
        fileRoot = os.path.splitext(fileName)[0]
        destRoot = os.path.splitext(destName)[0]
        fileVersion = mosh.getMatch(re.search(r'[ _]+v?([\.0-9]+)$', fileRoot), 1)
        snapVersion = mosh.getMatch(re.search(r'-[0-9\.]+$', destRoot))
        fileHedr = fileInfo.tes3.hedr
        if (fileVersion or snapVersion) and mosh.reVersion.search(fileHedr.description):
            newDescription = mosh.reVersion.sub(r'\1 ' + fileVersion + snapVersion,
                                                fileHedr.description, 1)
            fileInfo.writeDescription(newDescription)
            self.window.details.SetFile(fileName)
        # --Copy file
        self.window.data.copy(fileName, destDir, destName)


# ------------------------------------------------------------------------------

class File_RevertToSnapshot(Link):
    """Revert to Snapshot."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Revert to Snapshot...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileInfo = self.window.data[self.data[0]]
        fileName = fileInfo.name
        # --Snapshot finder
        destDir = self.window.data.dir
        srcDir = os.path.join(destDir, conf.settings['mosh.fileInfo.snapshotDir'])
        wildcard = fileInfo.getNextSnapshot()[2]
        # --File dialog
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        try:
            dialog = wx.FileDialog(self.window, _('Revert %s to snapshot:') % (fileName,), srcDir, '', wildcard,
                                   wx.FD_OPEN)
        except:
            dialog = wx.FileDialog(self.window, _('Revert to snapshot?'), srcDir, '', wildcard, wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        snapPath = dialog.GetPath()
        snapName = os.path.basename(snapPath)
        dialog.Destroy()
        # --Warning box
        try:
            message = (_("Revert %s to snapshot %s dated %s?") % (
                fileInfo.name, snapName, formatDate(mosh.getmtime(snapPath))))
            dialog = wx.MessageDialog(self.window, message, _('Revert to Snapshot'),
                                      style=wx.YES_NO | wx.ICON_EXCLAMATION)
        except:
            message = (_("Revert to snapshot dated %s?") % (formatDate(mosh.getmtime(snapPath))))
            dialog = wx.MessageDialog(self.window, message, _('Revert to Snapshot'),
                                      style=wx.YES_NO | wx.ICON_EXCLAMATION)
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        wx.BeginBusyCursor()
        destPath = os.path.join(fileInfo.dir, fileInfo.name)
        shutil.copy(snapPath, destPath)
        fileInfo.setMTime()
        try:
            self.window.data.refreshFile(fileName)
        except mosh.Tes3Error:
            guidialog.ErrorMessage(self, _('Snapshot file is corrupt!'))
            self.window.details.SetFile(None)
        wx.EndBusyCursor()
        self.window.Refresh(fileName)


# ------------------------------------------------------------------------------

class File_Backup(Link):
    """Backup file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Backup'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileInfo = self.window.data[self.data[0]]
        fileInfo.makeBackup(True)


# ------------------------------------------------------------------------------

class File_Open(Link):
    """Open specified file(s)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) > 0)

    def Execute(self, event):
        """Handle selection."""
        dir = self.window.data.dir
        for file in self.data:
            dir.join(file).start()


# ------------------------------------------------------------------------------

class File_RevertToBackup(object):
    """Revert to last or first backup."""

    def AppendToMenu(self, menu, window, data):
        self.window = window
        self.data = data
        # --Backup Files
        singleSelect = len(data) == 1
        self.fileInfo = window.data[data[0]]
        # --Backup Item
        wx.EVT_MENU(window, ID_REVERT_BACKUP, self.Execute)
        menuItem = wx.MenuItem(menu, ID_REVERT_BACKUP, _('Revert to Backup'))
        menu.AppendItem(menuItem)
        self.backup = os.path.join(self.fileInfo.dir,
                                   conf.settings['mosh.fileInfo.backupDir'], self.fileInfo.name)
        menuItem.Enable(singleSelect and os.path.exists(self.backup))
        # --First Backup item
        wx.EVT_MENU(window, ID_REVERT_FIRST, self.Execute)
        menuItem = wx.MenuItem(menu, ID_REVERT_FIRST, _('Revert to First Backup'))
        menu.AppendItem(menuItem)
        self.firstBackup = self.backup + 'f'
        menuItem.Enable(singleSelect and os.path.exists(self.firstBackup))

    def Execute(self, event):  # Polemos fixes
        """Handle menu selection."""
        fileInfo = self.fileInfo
        fileName = fileInfo.name
        # --Backup/FirstBackup?
        if event.GetId() == ID_REVERT_BACKUP:
            backup = self.backup
        else:
            backup = self.firstBackup
        try:  # --Warning box
            message = _("Revert %s to backup dated %s?") % (fileName, uniformatDate(mosh.getmtime(self.backup)))
            dialog = wx.MessageDialog(self.window, message, _('Revert to Backup'),
                                      style=wx.YES_NO | wx.ICON_EXCLAMATION)
        except:
            message = _("Revert file to backup dated %s?") % (uniformatDate(mosh.getmtime(self.backup)))
            dialog = wx.MessageDialog(self.window, message, _('Revert to Backup'),
                                      style=wx.YES_NO | wx.ICON_EXCLAMATION)
        if dialog.ShowModal() == wx.ID_YES:
            wx.BeginBusyCursor()
            dest = os.path.join(fileInfo.dir, fileName)
            shutil.copy(backup, dest)
            fileInfo.setMTime()
            try:
                self.window.data.refreshFile(fileName)
            except mosh.Tes3Error:
                guidialog.ErrorMessage(self, _('Old file is corrupt!'))
            wx.EndBusyCursor()
        dialog.Destroy()
        self.window.Refresh(fileName)


# ------------------------------------------------------------------------------

class File_Remove_RefsSafeCells(ListEditorData):
    """Data capsule for load list editing dialog."""

    def __init__(self, parent):
        """Initialize."""
        self.data = conf.settings['mash.refRemovers.safeCells']
        self.data.sort(key=lambda a: a.lower())
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRemove = True

    def getItemList(self):
        """Returns safe cells in alpha order."""
        return self.data[:]

    def add(self):
        """Adds a safe cell."""
        # --Dialog
        dialog = wx.TextEntryDialog(self.parent, _('Cell Name:'), _('Add Safe Cell'))
        result = dialog.ShowModal()
        # --Canceled or empty?
        if result != wx.ID_OK or not dialog.GetValue():
            dialog.Destroy()
            return None
        newCell = dialog.GetValue()
        dialog.Destroy()
        # --Already have it?
        if newCell in self.data: return None
        conf.settings.setChanged('mash.refRemovers.safeCells')
        self.data.append(newCell)
        self.data.sort(key=lambda a: a.lower())
        return newCell

    def remove(self, item):
        """Remove a safe cell."""
        conf.settings.setChanged('mash.refRemovers.safeCells')
        self.data.remove(item)
        return True


# ------------------------------------------------------------------------------

class File_Remove_RefsData(ListEditorData):
    """Data capsule for ref remover editing dialog."""

    def __init__(self, parent):
        """Initialize."""
        self.data = conf.settings['mash.refRemovers.data']
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRename = True
        self.showRemove = True

    def getItemList(self):
        """Returns load list keys in alpha order."""
        return sorted(self.data.keys(), key=lambda a: a.lower())

    def add(self):
        """Adds a new ref remover."""
        # --File dialog
        workDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        dialog = wx.FileDialog(self.parent, _('Select Ref Remover file or files:'),
                               workDir, '', '*.*', wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return None
        paths = dialog.GetPaths()
        dialog.Destroy()
        if len(paths) == 0:
            return None
        elif len(paths) == 1:
            conf.settings.setChanged('mash.refRemovers.data')
            name = os.path.splitext(os.path.basename(paths[0]))[0]
        else:
            root, number = _('Combo %d'), 1
            while (root % (number,)) in self.data:
                number += 1
            name = root % (number,)
        conf.settings['mosh.workDir'] = os.path.split(paths[0])[0]
        self.data[name] = paths
        return name

    def rename(self, oldName, newName):
        """Renames oldName to newName."""
        # --Right length?
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent,
                                    _('Name must be between 1 and 64 characters long.'))
            return False
        # --Rename
        conf.settings.setChanged('mash.refRemovers.data')
        self.data[newName] = self.data[oldName]
        del self.data[oldName]
        return newName

    def remove(self, item):
        """Removes load list."""
        conf.settings.setChanged('mash.refRemovers.data')
        del self.data[item]
        return True


# ------------------------------------------------------------------------------

class File_Remove_Refs(object):
    """Add ref remover links."""

    def __init__(self):
        """Initialize."""
        self.safeCells = conf.settings['mash.refRemovers.safeCells']
        self.removers = conf.settings['mash.refRemovers.data']

    def GetItems(self):
        items = list(self.removers.keys())
        items.sort(key=lambda x: x.casefold())
        return items

    def AppendToMenu(self, menu, window, data):
        """Append ref remover items to menu."""
        self.window = window
        self.data = data
        menu.Append(ID_REMOVERS.EDIT, _('Edit Removers...'))
        menu.Append(ID_REMOVERS.EDIT_CELLS, _('Edit Safe Cells...'))
        menu.AppendSeparator()
        enable = len(data) == 1
        ids = iter(ID_REMOVERS)
        for item in self.GetItems():
            try:
                menuItem = wx.MenuItem(menu, ids.next(), item)
                menu.AppendItem(menuItem)
                menuItem.Enable(enable)
            except StopIteration:
                pass
        # --Events
        wx.EVT_MENU(window, ID_REMOVERS.EDIT, self.DoData)
        wx.EVT_MENU(window, ID_REMOVERS.EDIT_CELLS, self.DoCells)
        wx.EVT_MENU_RANGE(window, ID_REMOVERS.BASE, ID_REMOVERS.MAX, self.DoList)

    def DoList(self, event):
        """Handle selection of one ref removers."""
        # --Continue Query
        tmessage = _('Please Note:')
        message = _(
            u"This command will remove ALL instances of the refs listed in the associated file, EXCEPT for instances "
            u"in safe cells. Be SURE that the cells you use for storage (strongholds, etc.) are included in the safe cells list, or"
            u" you risk losing the items you have stored in them!")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.refRemovers.continue',
                                    _('Remove Refs by Id...')) != wx.ID_OK:
            return
        # --Do it
        removerName = self.GetItems()[event.GetId() - ID_REMOVERS.BASE]
        removerPaths = self.removers[removerName]
        # --Get objIds
        objIds = set()
        for removerPath in removerPaths:
            with open(removerPath) as removerFile:
                reObjId = re.compile('"?(.*?)"?\t')
                for line in removerFile:
                    maObjId = reObjId.match(line)
                    if not maObjId or not maObjId.group(1): continue
                    objIds.add(maObjId.group(1))
        # --File Refs
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        caption = _('Refs Removed: ') + fileName
        progress = guidialog.ProgressDialog(caption)
        log = mosh.LogFile(BytesIO())
        try:
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            fileRefs.removeRefsById(objIds, self.safeCells)
            fileRefs.log = mosh.Log()  # --Null log. (Don't want orphan deletion in log.)
            fileRefs.removeOrphanContents()
            fileRefs.log = log
            fileRefs.safeSave()
            guidialog.LogMessage(self.window, '', log.out.getvalue(), caption)
        finally:
            progress.Destroy()
            self.window.Refresh(fileName)

    def DoCells(self, event):
        """Show safe cells editing dialog."""
        data = File_Remove_RefsSafeCells(self.window)
        dialog = ListEditorDialog(self.window, -1, _('Safe Cells'), data)
        dialog.list.SetSizeHints(250, 150)
        dialog.Fit()
        dialog.ShowModal()
        dialog.Destroy()

    def DoData(self, event):
        """Show ref removers editing dialog."""
        data = File_Remove_RefsData(self.window)
        dialog = ListEditorDialog(self.window, -1, _('Ref Removers'), data)
        dialog.ShowModal()
        dialog.Destroy()


# ------------------------------------------------------------------------------

class File_Replace_RefsData(ListEditorData):
    """Data capsule for ref replacer editing dialog."""

    def __init__(self, parent):
        """Initialize."""
        self.data = conf.settings['mash.refReplacers.data']
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRename = True
        self.showRemove = True

    def getItemList(self):
        """Returns load list keys in alpha order."""
        return sorted(self.data.keys(), key=lambda a: a.lower())

    def add(self):
        """Adds a new ref replacer."""
        # --File dialog
        workDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        dialog = wx.FileDialog(self.parent, _('Select Ref Replacer list file:'),
                               workDir, '', '*.*', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return None
        path = dialog.GetPath()
        dialog.Destroy()
        conf.settings['mosh.workDir'] = os.path.split(path)[0]
        conf.settings.setChanged('mash.refReplacers.data')
        name = os.path.splitext(os.path.basename(path))[0]
        self.data[name] = path
        return name

    def rename(self, oldName, newName):
        """Renames oldName to newName."""
        # --Right length?
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent,
                                    _('Name must be between 1 and 64 characters long.'))
            return False
        # --Rename
        conf.settings.setChanged('mash.refReplacers.data')
        self.data[newName] = self.data[oldName]
        del self.data[oldName]
        return newName

    def remove(self, item):
        """Removes replacer."""
        conf.settings.setChanged('mash.refReplacers.data')
        del self.data[item]
        return True


# ------------------------------------------------------------------------------

class File_Replace_Refs(object):
    """Add ref replacer links."""

    def __init__(self):
        """Initialize."""
        self.replacers = conf.settings['mash.refReplacers.data']

    def GetItems(self):
        items = list(self.replacers.keys())
        items.sort(key=lambda x: x.casefold())
        return items

    def AppendToMenu(self, menu, window, data):
        """Append ref replacer items to menu."""
        self.window = window
        self.data = data
        menu.Append(ID_REPLACERS.EDIT, _('Edit Replacers...'))
        menu.AppendSeparator()
        ids = iter(ID_REPLACERS)
        enable = (len(data) == 1)
        for item in self.GetItems():
            try:
                menuItem = wx.MenuItem(menu, ids.next(), item)
                menu.AppendItem(menuItem)
                menuItem.Enable(enable)
            except StopIteration:
                pass
        # --Events
        wx.EVT_MENU(window, ID_REPLACERS.EDIT, self.DoData)
        wx.EVT_MENU_RANGE(window, ID_REPLACERS.BASE, ID_REPLACERS.MAX, self.DoList)

    def DoList(self, event):  # Polemos: fixes
        """Handle selection of one ref replacers."""
        tmsg = _('Please Note:')
        msg = _('This command will replace all instances of objects listed in the replacer file with other objects.')
        if guidialog.ContinueQuery(self.window, tmsg, msg, 'query.refReplacers.continue',
                                    _('Replace Refs by Id...')) != wx.ID_OK: return
        # --File Refs
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        caption = _('Refs Replaced: %s' % fileName)
        progress = guidialog.ProgressDialog(caption)
        log = mosh.LogFile(BytesIO())
        try:
            # --Replacer
            replacerName = self.GetItems()[event.GetId() - ID_REPLACERS.BASE]
            replacerPath = self.replacers[replacerName]
            refReplacer = mosh.RefReplacer(replacerPath)
            # --Source Mod?
            srcModName = refReplacer.srcModName
            if srcModName and srcModName not in mosh.modInfos:
                renames = conf.settings['mash.mods.renames']
                if srcModName in renames:
                    srcModName = renames[srcModName]
                    refReplacer.srcModName = srcModName
                else:
                    guidialog.ErrorMessage(self.window,
                                            _('Source mod %s is not in Data Files folder.') % (srcModName,))
                    return
            log.setHeader(_('Source Mod'))
            log(srcModName or _('None'))
            # --File Refs
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            if not fileRefs.replaceRefsById(refReplacer):
                guidialog.InfoMessage(self.window, _('No replacements necessary.'))
            else:
                fileRefs.sortRecords()
                fileRefs.safeSave()
                fileInfo.refresh()
                fileInfo.writeAuthorWM()
                self.window.details.SetFile(fileName)
                guidialog.LogMessage(self.window, u'', log.out.getvalue(), caption)
        finally:
            if progress is not None: progress.Destroy()
            self.window.Refresh(fileName)

    def DoData(self, event):
        """Show ref replacers editing dialog."""
        data = File_Replace_RefsData(self.window)
        dialog = ListEditorDialog(self.window, -1, _('Ref Replacers'), data)
        dialog.ShowModal()
        dialog.Destroy()


# ------------------------------------------------------------------------------

class GetLinearList(Link):  # By Abot, adapted by Polemos.
    """Copy to clipboard a mods linear file list."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Copy linear mod list'))
        menu.AppendItem(menuItem)
        if len(data) < 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle selection."""
        tmsg = _('This command will copy to the clipboard selected mods linear file list.')
        msg = _('For pasting in Windows applications file load dialog boxes (e.g. TESFaith#, TESPCS, etc).')
        if guidialog.ContinueQuery(self.window,
                                    tmsg, msg, 'query.linear.file.list', _('Copy selected mods linear file list'),
                                    False) != wx.ID_OK: return
        # Scan for earliest date
        s = s1 = u''
        for fileName in self.data:
            s1 += '"%s" ' % fileName
            if len(s1) > 240:
                s1 = ''
                s += '\n"%s"' % fileName
            else:
                s += '"%s" ' % fileName
        # Copy to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject('%s\n\n------------\n%s' % ('\n'.join(self.data), s)))
            wx.TheClipboard.Close()


# ------------------------------------------------------------------------------

class File_RepairRefs(Link):
    """Repairs the save game's refs by comparing their type and id against the types and ids of the save game's masters."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Repair Refs'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        if fileInfo.getStatus() > 10:
            guidialog.WarningMessage(self.window,
                                      _('File master list is out of date. Please edit masters before attempting repair.'))
            return
        progress, dialog = None, None
        try:
            # --Log and Progress
            caption = _('Repairing ') + fileName
            progress = guidialog.ProgressDialog(caption)
            log = mosh.LogFile(BytesIO())
            # --World Refs
            worldRefs = mosh.WorldRefs(log=log, progress=progress)
            try:
                worldRefs.addMasters(fileInfo.masterNames)
            except mosh.Tes3RefError as error:
                progress = progress.Destroy()
                message = _(
                    u'%s has bad refs and must be repaired first.\n\nExample Bad Ref from %s:\nCell: %s\nObject Id: %s\nObject Index: '
                    u'%d\nMod Index: %d (%s)' % (
                        error.inName, error.inName, error.cellId, error.objId, error.iObj, error.iMod,
                        error.masterName))
                guidialog.ErrorMessage(self.window, message)
                return
            # --File Refs for Save File
            progress.setBaseScale()
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            (cntRepaired, cntDeleted, cntUnnamed) = worldRefs.repair(fileRefs)
            # --No problems?
            if not (cntRepaired or cntDeleted or cntUnnamed):
                progress = progress.Destroy()
                guidialog.InfoMessage(self.window, _('No problems found!'))
                return
            # --Save
            fileRefs.safeSave()
            progress = progress.Destroy()
            # --Problem Dialog
            message = _('Objects repaired: %d.\nObjects deleted: %d.' % (cntRepaired, cntDeleted))
            # InfoMessage(self.window,message)
            guidialog.LogMessage(self.window, message, log.out.getvalue(), caption)
        # --Done
        finally:
            if progress is not None: progress.Destroy()
            if dialog: dialog.Destroy()
            self.window.Refresh(fileName)


# ------------------------------------------------------------------------------

class File_SortRecords(Link):
    """Sorts the records in the file.
    This is just to make records easier to find in TESCS Details view."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Sort Records'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --Continue Query
        tmessage = _('Please Note:')
        message = _("This function will sort the records of the selected esp for easier viewing "
                    u"in the Details view of TESCS. Generally, this is only useful for active modders.")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.sortRecords.continue',
                                    _('Sort Records...')) != wx.ID_OK:
            return
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        fileRep = mosh.FileRep(fileInfo)
        fileRep.load()
        fileRep.sortRecords()
        fileRep.safeSave()
        guidialog.InfoMessage(self.window, _("Record sort completed."))


# ------------------------------------------------------------------------------

class File_StatsList(gui.List):
    def __init__(self, parent, data):
        # --Columns
        self.cols = conf.settings['mash.fileStats.cols']
        self.colNames = conf.settings['mash.colNames']
        self.colWidths = conf.settings['mash.fileStats.colWidths']
        self.colAligns = conf.settings['mash.fileStats.colAligns']
        self.colReverse = conf.settings['mash.fileStats.colReverse'].copy()
        # --Data/Items
        self.data = data
        self.sort = conf.settings['mash.fileStats.sort']
        # --Links
        self.mainMenu = []
        self.itemMenu = []
        # --Parent init
        gui.List.__init__(self, parent, -1)

    def PopulateItem(self, itemDex, mode=0, selected=set()):
        """Populate Item."""
        type = self.items[itemDex]
        itemData = self.data[type]
        cols = self.cols
        for colDex in range(self.numCols):
            # --Value
            col = cols[colDex]
            if col == 'Type':
                value = type
            elif col == 'Count':
                value = formatInteger(itemData[0])
            elif col == 'Size':
                value = formatInteger(itemData[1]) + ' B'
            # --Insert/Set Value
            if mode and (colDex == 0):
                self.list.InsertItem(itemDex, value)
            else:
                self.list.SetItem(itemDex, colDex, value)
        # --State
        if type in selected:
            self.list.SetItemState(itemDex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def SortItems(self, col=None, reverse=-2):  # --Sort Items
        """Setup."""
        if not col:
            col = self.sort
            reverse = self.colReverse.get(col, 0)
        elif reverse < 0:
            reverse = self.colReverse.get(col, 0)
            if self.sort == col: reverse = not reverse
        self.sort = col
        self.colReverse[col] = reverse
        # --Sort
        data = self.data
        # --Start with sort by type
        self.items.sort(key=lambda x: x.casefold())
        if col == 'Type':
            pass  # --Done by default
        elif col == 'Count':
            self.items.sort(key=lambda x: data[x][0])
        elif col == 'Size':
            self.items.sort(key=lambda x: data[x][1])
        # --Reverse?
        if reverse: self.items.reverse()


# ------------------------------------------------------------------------------

class File_Stats(Link):
    """Show file statistics."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Statistics'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --Assume a single selection for now...
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        fileInfo.getStats()
        frame = wx.Frame(self.window, -1, fileName, size=(200, 300),
                         style=(wx.RESIZE_BORDER | wx.CAPTION | wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CLIP_CHILDREN))
        frame.SetIcons(singletons.images['mash.main.ico'].GetIconBundle())
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(File_StatsList(frame, fileInfo.stats), 1, wx.EXPAND)
        frame.SetSizer(sizer)
        frame.Show()


# Installers Links -----------------------------------------------------------------

class Installers_AddMarker(Link):  # Polemos: made compatible with menubar, fixes.
    """Add an installer marker."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Add Marker...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.gTank
        except:
            self.data = singletons.gInstallers.data
            self.gTank = singletons.gInstallers.gList
        name = balt.askText(self.gTank, _('Enter a title:'), _('Add Marker'))
        if not name: return
        name = u'==%s==' % name
        self.data.addMarker(name)
        try:
            self.data.refresh(what='OS')
        except:
            self.data.refresh(mosh.InstallersData(), what='OS')
        singletons.gInstallers.RefreshUIMods()


# ------------------------------------------------------------------------------

class Installers_AnnealAll(Link):  # Polemos: made compatible with menubar.
    """Anneal all packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Anneal All'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.data
        except:
            self.data = singletons.gInstallers.data
        progress = balt.Progress(_("Annealing..."), '\n' + ' ' * 60)
        try:
            self.data.anneal(progress=progress)
        finally:
            progress.Destroy()
            self.data.refresh(what='NS')
            singletons.gInstallers.RefreshUIMods()


# ------------------------------------------------------------------------------

class Installers_AutoAnneal(Link):
    """Toggle autoAnneal setting."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Auto-Anneal'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.autoAnneal'])

    def Execute(self, event):
        """Handle selection."""
        conf.settings['mash.installers.autoAnneal'] ^= True
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_Enabled(Link):  # Polemos: made compatible with menubar.
    """Flips installer state."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Enabled'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.enabled'])

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.gTank
        except:
            self.title = u'Installers'
            self.gTank = singletons.gInstallers.gList
        enabled = conf.settings['mash.installers.enabled']
        message = _('Do you wish to enable "Installers"? If you do, Mash will first need to initialize some data. '
                    u'If there are many new mods to process this may take on the order of five minutes or more.')
        if not enabled and not balt.askYes(self.gTank, fill(message, 80), self.title):
            singletons.MenuBar.installers_settings_cond()
            return
        enabled = conf.settings['mash.installers.enabled'] = not enabled
        if enabled:
            singletons.gInstallers.refreshed = False
            singletons.gInstallers.OnShow()
            singletons.gInstallers.gList.RefreshUI()
        else:
            singletons.gInstallers.gList.gList.DeleteAllItems()
            singletons.gInstallers.RefreshDetails(None)
        singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Progress_info(Link):  # Polemos
    """Enables/disables extra info in progress bar."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Progress Extra Info'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.show.progress.info'])

    def Execute(self, event):
        """Handle selection."""
        self.title = u'Progress Bar Info'
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        enabled = conf.settings['mash.installers.show.progress.info']
        message = _(
            u"Do you wish to show extra information in the progress bar (filename, size, CRC) while refreshing? "
            u"This may decrease speed a lot. It is recommended only on fast computers or for debugging.")
        if not enabled and not balt.askYes(self.gTank, fill(message, 80), self.title):
            if conf.settings['mash.menubar.enabled']: singletons.MenuBar.installers_settings_cond()
            return
        enabled = conf.settings['mash.installers.show.progress.info'] = not enabled
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_ConflictsReportShowsInactive(Link):  # Polemos: made compatible with menubar.
    """Toggles option to show lower on conflicts report."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Show Inactive Conflicts'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.conflictsReport.showInactive'])

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        conf.settings['mash.installers.conflictsReport.showInactive'] ^= True
        self.gTank.RefreshUI()
        singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_ConflictsReportShowsLower(Link):  # Polemos: made compatible with menubar.
    """Toggles option to show lower on conflicts report."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Show Lower Conflicts'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.conflictsReport.showLower'])

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        conf.settings['mash.installers.conflictsReport.showLower'] ^= True
        self.gTank.RefreshUI()
        singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_AvoidOnStart(Link):
    """Ensures faster Mash startup by preventing Installers from being startup tab."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Avoid at Startup'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.fastStart'])

    def Execute(self, event):
        """Handle selection."""
        conf.settings['mash.installers.fastStart'] ^= True
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_Import(Link):  # Polemos
    """Add a new package (user friendly)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Import Package...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        package = guidialog.FileDialog(None, _('Choose a package to import into the Installers directory.'),
                                        wildcard=_('Archive files (*.*)|*.*'))
        if package is None: return
        sourcePath, pakFile = package
        # Move or copy?
        mc_query = guidialog.askdialog(None, _('Remove the original file after importing it?\n\n'
                                                u'If you click Yes the original file will be deleted (after it is copied into the Installers directory).\n'
                                                u'If the file fails to be copied, the deletion will be aborted automatically.'),
                                        _('Remove original file?'), True)
        if mc_query == wx.ID_CANCEL: return
        # Check if a file with the same name exists
        targPath = os.path.join(conf.settings['sInstallersDir'], pakFile)
        if os.path.isfile(targPath):
            overwrite = guidialog.askdialog(None,
                                             _('A package with the same name already exists in the Installers directory.\n\n'
                                               u'Click Yes to overwrite the existing package or click No to abort the import process.'),
                                             _('Overwrite file?'))
            if overwrite == wx.ID_NO: return
        # Copy/overwrite file to destination
        try:
            shutil.copyfile(sourcePath, targPath)
        except shutil.Error:
            guidialog.ErrorMessage(None,
                                    _('Operation aborted: You cannot import a package from Installers into the Installers.'))
            return
        except IOError:
            guidialog.ErrorMessage(None, _('Operation failed: Access denied. Unable to write on the destination.'))
            return
        except:
            return
        # Refresh GUI
        singletons.gInstallers.OnShow()
        # Delete source?
        if mc_query == wx.ID_YES:
            try:
                os.remove(sourcePath)
            except:
                guidialog.WarningMessage(None, _('The package was successfully imported into the Installers '
                                                  u'directory but Wrye Mash wasn\'t able to delete the original file. You may have to delete the source file manually.'))


# ------------------------------------------------------------------------------

class Installers_Refresh(Link):
    """Refreshes all Installers data."""

    def __init__(self, fullRefresh=False):
        Link.__init__(self)
        self.fullRefresh = fullRefresh

    def AppendToMenu(self, menu, window, data):
        if not conf.settings['mash.installers.enabled']: return
        Link.AppendToMenu(self, menu, window, data)
        self.title = (_('Refresh Data'), _('Full Refresh'))[self.fullRefresh]
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.gTank
        except:  # Polemos: made compatible with menubar.
            self.gTank = singletons.gInstallers.gList
            self.title = u'Full Refresh'
        if self.fullRefresh:
            message = balt.fill(_("Refresh ALL data from scratch? This may take five to ten "
                                  u"minutes (or more) depending on the number of mods you have installed."))
            if not balt.askWarning(self.gTank, fill(message, 80), self.title): return
        singletons.gInstallers.refreshed = False
        singletons.gInstallers.fullRefresh = self.fullRefresh
        singletons.gInstallers.OnShow()


# ------------------------------------------------------------------------------

class Installers_RemoveEmptyDirs(Link):
    """Toggles option to remove empty directories on file scan."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Clean Data Directory'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.removeEmptyDirs'])

    def Execute(self, event):
        """Handle selection."""
        conf.settings['mash.installers.removeEmptyDirs'] ^= True
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.installers_settings_cond()


# ------------------------------------------------------------------------------

class Installers_SortActive(Link):  # Polemos: made compatible with menubar.
    """Sort by type."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Sort by Active"), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.sortActive'])

    def Execute(self, event):
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        conf.settings['mash.installers.sortActive'] ^= True
        self.gTank.SortItems()
        singletons.MenuBar.installers_view_cond()


# ------------------------------------------------------------------------------

class Installers_SortProjects(Link):  # Polemos: made compatible with menubar.
    """Sort dirs to the top."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Projects First"), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.sortProjects'])

    def Execute(self, event):
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        conf.settings['mash.installers.sortProjects'] ^= True
        self.gTank.SortItems()
        singletons.MenuBar.installers_view_cond()


# ------------------------------------------------------------------------------

class Installers_SortBy(Link):  # Polemos
    """Sort files by specified key (sortCol)."""

    def __init__(self, sortCol, prefix=''):
        Link.__init__(self)
        self.sortCol = sortCol
        self.sortName = conf.settings['mash.colNames'][sortCol]
        self.prefix = prefix

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, self.prefix + self.sortName, kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if conf.settings['mash.installers.sort'] == self.sortCol: menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.gTank
        except:
            self.gTank = singletons.gInstallers.gList
        self.gTank.SortItems(self.sortCol, 'INVERT')
        try:
            singletons.MenuBar.installers_view_cond()
        except:
            pass


# ------------------------------------------------------------------------------

class Installers_SortStructure(Link):
    """Sort by type."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Sort by Structure"), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.installers.sortStructure'])

    def Execute(self, event):
        conf.settings['mash.installers.sortStructure'] ^= True
        self.gTank.SortItems()


# Installer Links -------------------------------------------------------------

class InstallerLink(Link):
    """Common functions for installer links..."""

    def isSingle(self):
        """Indicates whether or not is single installer."""
        return len(self.selected) == 1

    def isSingleProject(self):
        """Indicates whether or not is single project."""
        if len(self.selected) != 1:
            return False
        else:
            return isinstance(self.data[self.selected[0]], mosh.InstallerProject)

    def isSingleArchive(self):
        """Indicates whether or not is single archive."""
        if len(self.selected) != 1:
            return False
        else:
            return isinstance(self.data[self.selected[0]], mosh.InstallerArchive)

    def getProjectPath(self):
        """Returns whether build directory exists."""
        archive = self.selected[0]
        return mosh.dirs['builds'].join(archive.sroot)

    def projectExists(self):
        if not len(self.selected) == 1: return False
        return self.getProjectPath().exists()


# ------------------------------------------------------------------------------

class Installer_Anneal(InstallerLink):
    """Anneal all packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Anneal'))
        menu.AppendItem(menuItem)

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            return True
        return False

    def Execute(self, event):
        """Handle selection."""
        if self.chkMarker(): return
        progress = balt.Progress(_('Annealing...'), '\n' + ' ' * 60)
        try:
            self.data.anneal(self.selected, progress)
        finally:
            progress.Destroy()
            self.data.refresh(what='NS')
            singletons.gInstallers.RefreshUIMods()


# ------------------------------------------------------------------------------

class Installer_Delete(balt.Tank_Delete):
    """Deletes selected file from tank."""

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        if self.data.lastKey == self.selected[0]:
            balt.showWarning(self.gTank, _('This is a special marker and it cannot be deleted.'))
            return True
        return False

    def Execute(self, event):
        if self.chkMarker(): return
        balt.Tank_Delete.Execute(self, event)
        self.data.refreshOrder()
        self.data.refresh(what='N')
        self.gTank.RefreshUI()


# ------------------------------------------------------------------------------

class Installer_Rename(InstallerLink):  # Polemos
    """Renames selected file from tank."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        self.title = _('Rename...')
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)
        menuItem.Enable(self.isSingle())

    def Execute(self, event):
        """Handle selection."""
        curName = self.selected[0]
        # Check if selected is the special ==Last== marker
        if self.data.lastKey == self.selected[0]:
            balt.showWarning(self.gTank, _('This is a special marker and it cannot be renamed.'))
            return
        # Check if selected is a marker
        if all([n_path(curName).startswith('=='), n_path(curName).endswith('==')]):
            pos = self.data[curName].order
            name = balt.askText(self.gTank, _('Rename marker as:'), _('Rename Marker'))
            if not name: return
            try:
                name = u'==%s==' % name
                del self.data[curName]
                self.data.addMarker(name)
                self.data.moveArchives([name], pos)
            except:
                pass
            finally:
                self.data.refresh(what='OS')
                singletons.gInstallers.RefreshUIMods()
            return
        # Check if the file was deleted without Mash knowing it.
        try:
            instExist = mosh.dirs['installers'].join(curName).exists()
        except:
            instExist = mosh.dirs['installers'].join(n_path(curName)).exists()
        if not instExist:
            RefreshNotify()
            return
        # All ok? Continue...
        try:
            result = balt.askText(self.gTank, _('Rename %s as:') % curName.s, self.title, curName.s)
        except:
            result = balt.askText(self.gTank, _('Rename %s as:') % n_path(curName), self.title, n_path(curName))
        result = (result or '').strip()
        if not result: return
        # --Error checking
        newName = GPath(result).tail
        if not newName.s:
            balt.showWarning(self.gTank, _('%s is not a valid name.') % result)
            return
        if newName in self.data:
            balt.showWarning(self.gTank,
                             _('%s already exists or the new name is the same as the original.') % newName.s)
            return
        if self.data.dir.join(curName).isfile() and curName.cext != newName.cext:
            balt.showWarning(self.gTank, _('%s does not have correct extension (%s).') % (newName.s, curName.ext))
            return
        # --Rename
        try:
            wx.BeginBusyCursor()
            if not self.data.rename(curName, newName):
                balt.showError(self.gTank, _('Access Denied.'))
                return
        except:
            balt.showError(self.gTank, _('%s is not a valid name.') % result)
            return
        finally:
            wx.EndBusyCursor()
        self.data.refresh(what='NS')
        self.gTank.RefreshUI()


# ------------------------------------------------------------------------------

class Installer_Duplicate(InstallerLink):
    """Duplicates selected Installer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        self.title = _('Duplicate...')
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)
        menuItem.Enable(self.isSingle())

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            balt.showWarning(self.gTank, _('This is a marker and it cannot be duplicated.'))
            return True
        return False

    def Execute(self, event):  # Polemos: fixes
        """Handle selection."""
        if self.chkMarker(): return
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        # Check if the file was deleted without Mash knowing it.
        try:
            instExist = mosh.dirs['installers'].join(curName).exists()
        except:
            instExist = mosh.dirs['installers'].join(n_path(curName)).exists()
        if not instExist:
            RefreshNotify()
            return
        # All ok? Continue...
        newName = 'BCK-%s%s' % (root, ext)
        index = 0
        while newName in self.data:
            newName = root + (_(' Copy (%d)') % index) + ext
            index += 1
        try:
            result = balt.askText(self.gTank, _("Duplicate %s as:") % curName.s, self.title, newName)
        except:
            result = balt.askText(self.gTank, _("Duplicate %s as:") % n_path(curName), self.title, n_path(newName))
        result = (result or '').strip()
        if not result: return
        # --Error checking
        newName = GPath(result).tail
        if not newName.s:
            balt.showWarning(self.gTank, _("%s is not a valid name.") % result)
            return
        if newName in self.data:
            balt.showWarning(self.gTank, _("%s already exists.") % newName.s)
            return
        if self.data.dir.join(curName).isfile() and curName.cext != newName.cext:
            balt.showWarning(self.gTank, _("%s does not have correct extension (%s).") % (newName.s, curName.ext))
            return
        # --Duplicate
        try:
            wx.BeginBusyCursor()
            self.data.copy(curName, newName)
        except:
            balt.showError(self.gTank, _("%s is not a valid name.") % result)
            return
        finally:
            wx.EndBusyCursor()
        self.data.refresh(what='N')
        self.gTank.RefreshUI()


# ------------------------------------------------------------------------------

class Installer_HasExtraData(InstallerLink):
    """Toggle hasExtraData flag on installer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Has Extra Directories'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Enable(self.isSingle())
        if self.isSingle():
            installer = self.data[self.selected[0]]
            menuItem.Check(installer.hasExtraData)

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            return True
        return False

    def Execute(self, event):
        """Handle selection."""
        if self.chkMarker(): return
        installer = self.data[self.selected[0]]
        installer.hasExtraData ^= True
        installer.refreshDataSizeCrc()
        installer.refreshStatus(self.data)
        self.data.refresh(what='N')
        self.gTank.RefreshUI()


# ------------------------------------------------------------------------------

class Installer_Install(InstallerLink):
    """Install selected packages."""

    mode_title = {'DEFAULT': _('Install'), 'LAST': _('Install Last'), 'MISSING': _('Install Missing')}

    def __init__(self, mode='DEFAULT'):
        Link.__init__(self)
        self.mode = mode

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        self.title = self.mode_title[self.mode]
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            balt.showWarning(self.gTank, _('This is a marker and it cannot be installed.'))
            return True
        return False

    def Execute(self, event):
        """Handle selection."""
        if self.chkMarker(): return
        progress = balt.Progress(_('Installing...'), '\n' + ' ' * 60)
        try:
            last = (self.mode == 'LAST')
            override = (self.mode != 'MISSING')
            self.data.install(self.selected, progress, last, override)
        finally:
            progress.Destroy()
            self.data.refresh(what='N')
            singletons.gInstallers.RefreshUIMods()


# ------------------------------------------------------------------------------

class Installer_Move(InstallerLink):
    """Moves selected installers to desired spot."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Move To...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        curPos = min(self.data[x].order for x in self.selected)
        message = _(
            u'Move selected archives to what position?\nEnter position number.\nLast: -1; First of Last: -2; Semi-Last: -3.')
        newPos = balt.askText(self.gTank, message, self.title, repr(curPos))
        if not newPos: return
        newPos = newPos.strip()
        if not re.match('^-?\d+$', newPos):
            balt.showError(self.gTank, _('Position must be an integer.'))
            return
        newPos = int(newPos)
        if newPos == -3:
            newPos = self.data[self.data.lastKey].order
        elif newPos == -2:
            newPos = self.data[self.data.lastKey].order + 1
        elif newPos < 0:
            newPos = len(self.data.data)
        self.data.moveArchives(self.selected, newPos)
        self.data.refresh(what='N')
        self.gTank.RefreshUI()


# ------------------------------------------------------------------------------

class Installers_Open(balt.Tank_Open):  # -# D.C.-G.:Added to avoid errors when the installers path is unreachable.
    """Open selected file(s) from the menu."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open...'))
        menu.AppendItem(menuItem)
        if not os.access(mosh.dirs["installers"].s, os.W_OK): menuItem.Enable(False)  # -#
        menuItem.Enable(bool(self.selected))


class Installer_Open(balt.Tank_Open):
    """Open selected file(s)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open...'))
        menu.AppendItem(menuItem)
        self.selected = [x for x in self.selected if x != self.data.lastKey]
        menuItem.Enable(bool(self.selected))


# ------------------------------------------------------------------------------

class Installer_Repack(InstallerLink):  # Polemos
    """Repacks selected installer."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Repack'))
        menu.AppendItem(menuItem)
        if len(self.selected) > 1:
            menuItem.Enable(False)
        elif os.path.isdir(os.path.join(conf.settings['sInstallersDir'], self.selected[0].s)):
            menuItem.Enable(False)
        else:
            menuItem.Enable(bool(self.selected))
        self.window = window

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            balt.showWarning(self.gTank, _('This is a marker and it cannot be re-packed.'))
            return True
        return False

    def Execute(self, event):
        """Handle selection."""
        if self.chkMarker(): return
        package_name = self.selected[0].s
        package_path = os.path.join(conf.settings['sInstallersDir'], package_name)
        tempdir = os.path.join(singletons.MashDir, 'Temp')
        package_tempdir = os.path.join(tempdir, package_name)
        # Is the file missing?
        if not os.path.isfile(package_path):
            RefreshNotify()
            return
        # Reset temp dir
        if not ResetTempDir(self.window).status: return
        # Get Package info
        package_paths, max_depth, mw_files = bolt.ArchiveInfo(package_path).getPackageData
        package_data = self.window, package_name, (package_paths, max_depth)
        # Call package explorer
        explorer = guidialog.ArchiveExplorer(package_data, title=_('Repack Package...'))
        data_files = explorer.GetTreeValue
        if data_files is None: return
        # Unpack to tempdir (7zip doesn't allow dir extraction without extracting parent dirs).
        bolt.MultiThreadGauge(self.window, (package_tempdir, package_path, data_files))
        # Clean some junk
        bolt.CleanJunkTemp()
        # Move to Mods dir
        pack_source = os.path.join(package_tempdir, data_files)
        pack_name = os.path.join(conf.settings['sInstallersDir'], 'repack-%s' % package_name)
        pack_target = ['%s.7z' % pack_name.rstrip(x) if pack_name.endswith(x) else pack_name for x in ['.zip', 'rar']][
            0]
        # Repack
        bolt.MultiThreadGauge(self.window, (pack_source, pack_target), mode='pack')


# ------------------------------------------------------------------------------

class Installer_Refresh(InstallerLink):
    """Rescans selected Installers."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Refresh'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        dir = self.data.dir
        progress = balt.Progress(_("Refreshing Packages..."), '\n' + ' ' * 60)
        progress.setFull(len(self.selected))
        forceRefresh = False  # Polemos: Fixes cases where an installer is deleted without Mash knowing
        try:
            for index, archive in enumerate(self.selected):
                progress(index, _("Refreshing Packages...\n") + archive.s)
                installer = self.data[archive]
                apath = mosh.dirs['installers'].join(archive)
                installer.refreshBasic(apath, SubProgress(progress, index, index + 1), True)
                self.data.hasChanged = True
        except:
            forceRefresh = True
        finally:
            if progress is not None: progress.Destroy()
        self.data.refresh(what='NS')
        self.gTank.RefreshUI()
        if forceRefresh: RefreshNotify()


# ------------------------------------------------------------------------------

class Installer_Uninstall(InstallerLink):
    """Uninstall selected Installers."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Uninstall'))
        menu.AppendItem(menuItem)

    def chkMarker(self):  # Polemos
        """Check for marker attr."""
        curName = self.selected[0]
        isdir = self.data.dir.join(curName).isdir()
        if isdir:
            root, ext = curName, ''
        else:
            root, ext = curName.rootExt
        tmpName = '%s%s' % (root, ext)
        if all([n_path(tmpName).startswith('=='), n_path(tmpName).endswith('==')]) or self.data.lastKey == \
                self.selected[0]:
            balt.showWarning(self.gTank, _('This is a marker and it cannot be uninstalled.'))
            return True
        return False

    def Execute(self, event):
        """Handle selection."""
        if self.chkMarker(): return
        progress = balt.Progress(_("Uninstalling..."), u'Please wait...\n' + ' ' * 60)
        try:
            self.data.uninstall(self.selected, progress)
        finally:
            progress.Destroy()
            self.data.refresh(what='NS')
            singletons.gInstallers.RefreshUIMods()


# InstallerArchive Links ------------------------------------------------------

class InstallerArchive_Unpack(InstallerLink):
    """Install selected packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        self.title = _('Unpack to Project...')
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)
        menuItem.Enable(self.isSingleArchive())

    def Execute(self, event):
        archive = self.selected[0]
        installer = self.data[archive]
        project = archive.root
        result = balt.askText(self.gTank, _("Unpack %s to Project:") % archive.s, self.title, project.s)
        result = (result or '').strip()
        if not result: return
        # --Error checking
        project = GPath(result).tail
        if not project.s or project.cext in ('.rar', '.zip', '.7z'):
            balt.ShowWarning(self.gTank, _("%s is not a valid project name.") % result)
            return
        if self.data.dir.join(project).isfile():
            balt.ShowWarning(self.gTank, _("%s is a file.") % project.s)
            return
        if project in self.data:
            if not balt.askYes(self.gTank, _("%s already exists. Overwrite it?") % project.s, self.title, False):
                return
        # --Copy to Build
        progress = balt.Progress(_("Unpacking to Project..."), '\n' + ' ' * 60)
        try:
            installer.unpackToProject(archive, project, SubProgress(progress, 0, 0.8))
            if project not in self.data: self.data[project] = mosh.InstallerProject(project)
            iProject = self.data[project]
            pProject = mosh.dirs['installers'].join(project)
            iProject.refreshed = False
            iProject.refreshBasic(pProject, SubProgress(progress, 0.8, 0.99), True)
            if iProject.order == -1:
                self.data.refreshOrder()
                self.data.moveArchives([project], installer.order + 1)
            self.data.refresh(what='NS')
            self.gTank.RefreshUI()
        finally:
            progress.Destroy()


# InstallerProject Links ------------------------------------------------------

class InstallerProject_Sync(InstallerLink):
    """Install selected packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        self.title = _('Sync from Data')
        menuItem = wx.MenuItem(menu, self.id, self.title)
        menu.AppendItem(menuItem)
        enabled = False
        if self.isSingleProject():
            project = self.selected[0]
            installer = self.data[project]
            enabled = bool(installer.missingFiles or installer.mismatchedFiles)
        menuItem.Enable(enabled)

    def Execute(self, event):
        project = self.selected[0]
        installer = self.data[project]
        missing = installer.missingFiles
        mismatched = installer.mismatchedFiles
        message = _("Update %s according to data directory?\nFiles to delete: %d\nFiles to update: %d") % (
            project.s, len(missing), len(mismatched))
        if not balt.askWarning(self.gTank, message, self.title): return
        # --Sync it, baby!
        progress = balt.Progress(self.title, '\n' + ' ' * 60)
        try:
            progress(0.1, _("Updating files."))
            installer.syncToData(project, missing | mismatched)
            pProject = mosh.dirs['installers'].join(project)
            installer.refreshed = False
            installer.refreshBasic(pProject, SubProgress(progress, 0.1, 0.99), True)
            self.data.refresh(what='NS')
            self.gTank.RefreshUI()
        finally:
            progress.Destroy()


# ------------------------------------------------------------------------------

class InstallerProject_SyncPack(InstallerLink):
    """Install selected packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Sync and Pack'))
        menu.AppendItem(menuItem)
        menuItem.Enable(self.projectExists())

    def Execute(self, event):
        raise UncodedError


# ------------------------------------------------------------------------------

class InstallerProject_Pack(InstallerLink):  # Not enabled
    """Pack selected projects."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Pack Project'))
        menu.AppendItem(menuItem)
        menuItem.Enable(self.projectExists())

    def Execute(self, event):
        raise UncodedError


# ModData Links ---------------------------------------------------------------

class Remove_Mod(Link):  # Polemos
    """Remove selected."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menu.AppendItem(wx.MenuItem(menu, self.id, _('Remove...')))

    def Execute(self, event):
        """Handle menu selection."""
        if len(self.data) == 1:
            msg = _('Remove selected mod?\nThis operation cannot be undone.\n')
        else:
            msg = _('Remove selected mods? This operation cannot be undone.')
        msg += '\n* ' + '\n* '.join((self.window.data[x][0] for x in self.data))
        dialog = wx.MessageDialog(self.window, msg, _('Remove Selected...'), style=wx.YES_NO | wx.ICON_EXCLAMATION)
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        dialog.Destroy()
        # Remove mod(s)
        try:
            bolt.RemoveTree((self.window.data[x][6] for x in self.data))
        except:
            guidialog.ErrorMessage(self.window, _('Removal failed. Access denied.'))
        # Refresh
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Rename_Mod(Link):  # Polemos
    """Rename selected."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Rename...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        dialog = guidialog.RenameDialog(self.window, self.window.data[self.data[0]][0])
        newModName = dialog.GetModName
        if not newModName:
            dialog.Destroy()
            return
        oldModFolder = self.window.data[self.data[0]][6]
        newModFolder = os.path.join(conf.settings['datamods'], newModName)
        # Check if it already exists
        if self.onExists(newModFolder): return
        # Rename Mod
        try:
            os.rename(oldModFolder, newModFolder)
        except:
            self.onExists(newModFolder)
            return
        # Mod info
        order = singletons.ModdataList.items[:]
        active = singletons.ModdataList.datamods.checkActiveState(oldModFolder)
        # Reorder mod
        for num, x in enumerate(order):
            if x == oldModFolder: order[num] = newModFolder
        singletons.ModdataList.data.moveTo(order)
        singletons.ModdataList.Refresh()
        # Reactivate mod if needed and enable changes on ini
        if active: singletons.ModdataList.ToggleModActivation(newModFolder)
        singletons.ModdataList.Refresh()

    def onExists(self, newModFolder=None):
        """If mod name already exists."""
        if newModFolder is None or os.path.exists(newModFolder):
            guidialog.ErrorMessage(self.window, _('Rename failed. Another mod with the same name already exists.'))
            return True


# ------------------------------------------------------------------------------

class HomePage_Mod(Link):  # Polemos
    """Go to mod's web site."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Visit mod\'s webpage'))
        menu.AppendItem(menuItem)
        menuItem.Enable(all([len(self.data) == 1, self.checkMeta()]))

    def checkMeta(self):
        """Check if Metafile has any web info."""
        metadir = self.window.data[self.data[0]][6]
        metadata = bolt.MetaParse(metadir).Data
        try:
            repo, ID = metadata[u'Repo'], metadata[u'ID']
        except:
            return False
        if not repo or not ID: return False
        self.webData = repo, ID
        return True

    def Execute(self, event):
        """Handle menu selection."""
        nash.VisitWeb(self.webData)


# Package Links ---------------------------------------------------------------

class Install_Package(Link):  # Polemos
    """Install selected package."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Install...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)  # Polemos, todo: multiple installs?

    def Execute(self, event):
        """Handle menu selection."""
        package = os.path.join(conf.settings['downloads'], self.data[0])
        singletons.ModPackageList.UnpackPackage(package)


# ------------------------------------------------------------------------------

class Open_Package(Link):  # Polemos
    """Open selected package."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Open...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        package = os.path.join(conf.settings['downloads'], self.data[0])
        os.startfile(package)


# ------------------------------------------------------------------------------

class Remove_Package(Link):  # Polemos
    """Removes selected packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menu.AppendItem(wx.MenuItem(menu, self.id, _('Delete...')))

    def Execute(self, event):
        """Handle menu selection."""
        if len(self.data) == 1:
            msg = _('Delete selected package? This operation cannot be undone.\n')
        else:
            msg = _('Delete selected packages? This operation cannot be undone.\n')
        msg += '\n* ' + '\n* '.join((self.window.data[x][0] for x in self.data))
        dialog = wx.MessageDialog(self.window, msg, _('Delete Selected...'), style=wx.YES_NO | wx.ICON_EXCLAMATION)
        if dialog.ShowModal() != wx.ID_YES:
            dialog.Destroy()
            return
        dialog.Destroy()
        # Remove package(s)
        failed = [x for x in self.data if not Remove(os.path.join(conf.settings['downloads'], x))]
        if failed: guidialog.ErrorMessage(self.window,
                                           _('Access denied: Failed deleting the following packages:\n%s' % '\n'.join(
                                               failed)))
        # Refresh
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Hide_Package(Link):  # Polemos
    """Hides selected packages."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Hide...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(False)  # Polemos, todo: enable

    def Execute(self, event):
        """Handle menu selection."""
        packNames = [self.window.data[x][0] for x in self.data]
        packDirs = [os.path.join(conf.settings['downloads'], x) for x in self.data]
        # Hide package(s)

        # Refresh
        self.window.Refresh()


# Mods Links ------------------------------------------------------------------

class Mods_LoadListData(ListEditorData):
    """Data capsule for load list editing dialog."""

    def __init__(self, parent):
        """Initialize."""
        self.data = conf.settings['mash.loadLists.data']
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showRename = True
        self.showRemove = True

    def getItemList(self):
        """Returns load list keys in alpha order."""
        return sorted(self.data.keys(), key=lambda a: a.lower())

    def rename(self, oldName, newName):
        """Renames oldName to newName."""
        # --Right length?
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent, _('Name must be between 1 and 64 characters long.'))
            return False
        # --Rename
        conf.settings.setChanged('mash.loadLists.data')
        self.data[newName] = self.data[oldName]
        del self.data[oldName]
        return newName

    def remove(self, item):
        """Removes load list."""
        conf.settings.setChanged('mash.loadLists.data')
        del self.data[item]
        return True


# ------------------------------------------------------------------------------

class Mods_custom_menu(Link):  # Polemos: Added a Custom Commands menu.
    """Create Custom Commands."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Custom Commands...'),
                               _('Create, save, edit and delete Custom Commands.'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        self.window = singletons.mashFrame
        dialog = mosh.CommandsData(self.window)
        dialog.execute()


# ------------------------------------------------------------------------------

class Mods_LoadList(object):  # Polemos: Added compability with menubar, optimized, refactored, more...
    """Add load list links."""

    def __init__(self):
        """Init."""
        self.data = conf.settings['mash.loadLists.data']

    def GetItems(self):
        """Return sorted mod items."""
        items = list(self.data.keys())
        items.sort(key=lambda x: x.casefold())
        return items

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        if data is not None:
            self.window = window
        elif data is None:
            self.window, window = singletons.modList, singletons.mashFrame
        menu_ap = menu.Append
        event_m = wx.EVT_MENU
        menu_ap(ID_LOADERS.ALL, _('All'), u'Select all mods.')
        menu_ap(ID_LOADERS.NONE, _('None'), u'Deselect all mods.')
        menu_ap(ID_LOADERS.SAVE, _('Save List...'), u'Save active mod list.')
        menu_ap(ID_LOADERS.EDIT, _('Edit Lists...'), u'Edit active mod lists.')
        menu.AppendSeparator()
        ids = iter(ID_LOADERS)
        try:
            [menu_ap(ids.next(), item, _('Select: %s list.' % item)) for item in self.GetItems()]
        except StopIteration:
            pass
        # --Disable Save?
        if not mosh.mwIniFile.loadFiles: menu.FindItemById(ID_LOADERS.SAVE).Enable(False)
        # --Events
        event_m(window, ID_LOADERS.NONE, self.DoNone)
        event_m(window, ID_LOADERS.ALL, self.DoAll)
        event_m(window, ID_LOADERS.SAVE, self.DoSave)
        event_m(window, ID_LOADERS.EDIT, self.DoEdit)
        wx.EVT_MENU_RANGE(window, ID_LOADERS.BASE, ID_LOADERS.MAX, self.DoList)

    def DoNone(self, event):
        """Deselect all items."""
        loadFiles = mosh.mwIniFile.loadFiles[:]
        mosh.modInfos.unload([loadFile for loadFile in loadFiles])
        self.refresh('items')

    def DoAll(self, event):
        """Select all items."""
        self.DoItems(mosh.modInfos.data)
        self.refresh('items')

    def DoList(self, event):
        """Load list."""
        item = self.GetItems()[event.GetId() - ID_LOADERS.BASE]
        self.DoItems(self.data[item])
        self.refresh('items')

    def DoItems(self, modlist):
        """Set items of the list."""
        for loadFile in modlist:
            try:
                mosh.modInfos.load(loadFile, False)
            except mosh.MaxLoadedError:
                guidialog.ErrorMessage(self.window,
                                        _("Unable to add mod %s because load list is full.") % (loadFile,))
                break

    def DoSave(self, event):
        """Save list."""
        if len(self.data) >= ID_LOADERS.size:  # --No slots left?
            guidialog.ErrorMessage(self,
                                    _('All load list slots are full. Please delete an existing load list before adding another.'))
            return
        dialog = wx.TextEntryDialog(self.window, _('Save current load list as:'), u'Wrye Mash')
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            newItem = dialog.GetValue()
            dialog.Destroy()
            if len(newItem) == 0 or len(newItem) > 64:
                guidialog.ErrorMessage(self.window, _('Load list name must be between 1 and 64 characters long.'))
            else:
                self.data[newItem] = mosh.mwIniFile.loadFiles[:]
                conf.settings.setChanged('mash.loadLists.data')
                conf.settings['mash.loadLists.need.refresh'] = True
        # --Not Okay
        else:
            dialog.Destroy()
        self.refresh('menu')

    def DoEdit(self, event):
        """Edit list names."""
        data = Mods_LoadListData(self.window)
        dialog = ListEditorDialog(self.window, -1, _('Load Lists'), data)
        dialog.ShowModal()
        conf.settings['mash.loadLists.need.refresh'] = True
        self.refresh('menu')

    def refresh(self, mode):
        """Refreshes tab."""
        if mode == 'items':
            mosh.mwIniFile.safeSave()
            self.window.PopulateItems()
        if mode == 'menu': singletons.MenuBar.mods_load_cond()
        singletons.statusBar.profile()


# ------------------------------------------------------------------------------

class Mods_EsmsFirst(Link):  # Polemos: made compatible with toolbar menu.
    """Sort esms to the top."""

    def __init__(self, prefix=''):
        """Init."""
        Link.__init__(self)
        self.prefix = prefix

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, self.prefix + _('Type'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if window.esmsFirst: menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        self.window.esmsFirst = not self.window.esmsFirst
        self.window.PopulateItems()
        singletons.MenuBar.mods_view_cond()


# ------------------------------------------------------------------------------

class Mods_TESlint_Config(Link):  # Polemos: A TES3lint config dialog.
    """Settings for TES3lint integration."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('TES3lint Settings'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        self.window = singletons.modDetails
        pos = conf.settings['tes3lint.pos']
        import plugins.tes3lint.settings
        plugins.tes3lint.settings.TES3lint_Settings(self.window, pos)


# ------------------------------------------------------------------------------

class snapshot_po_take(Link):  # Polemos
    """Take snapshot."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Take fast snapshot'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modDetails
        srcDir = os.path.join(singletons.MashDir, 'snapshots')
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        text = '\n'.join([x for x in mosh.mwIniFile.loadOrder])
        with io.open((os.path.join(srcDir, 'snapshot.txt')), 'w', encoding=conf.settings['profile.encoding']) as f:
            try:
                f.write(text)
                msg = _('Active mods snapshot taken.')
            except Exception as err:
                msg = _('Unable to take snapshot. Reason:\n   %s' % err)
        guidialog.InfoMessage(self.window, msg)


# ------------------------------------------------------------------------------

class snapshot_po_restore(Link):  # Polemos
    """Restore snapshot."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Restore fast snapshot'))
        menu.AppendItem(menuItem)
        if not os.path.isfile((os.path.join(singletons.MashDir, 'snapshots', 'snapshot.txt'))): menuItem.Enable(False)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modDetails
        srcDir = os.path.join(singletons.MashDir, 'snapshots')
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        if not os.path.isfile((os.path.join(srcDir, 'snapshot.txt'))):
            guidialog.ErrorMessage(self.window, _('You need to create a snapshot file first.'))
            return
        try:
            with io.open((os.path.join(srcDir, 'snapshot.txt')), 'r', encoding=conf.settings['profile.encoding']) as f:
                restore_po = f.readlines()
        except:
            guidialog.ErrorMessage(self.window, _('Couldn\'t open the snapshot file.'))
            return
        if len(restore_po) <= 1: return
        order_po = [line.rstrip() for line in restore_po]
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
        loadorder_mtime_increment = (mtime_last - 1026943162) // len(order_po)
        mtime = 1026943162
        missing_po = ''
        for p in order_po:
            try:
                mosh.modInfos[p].setMTime(mtime)
            except:
                missing_po = '%s\n%s' % (missing_po, p)
                continue
            mtime += loadorder_mtime_increment
        mod_po = mosh.ModInfos('', True)
        [mod_po.unload(x, True) for x in mosh.mwIniFile.loadOrder]
        for x in order_po:
            try:
                singletons.modList.ToggleModActivation(x)
            except:
                continue
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()
        if missing_po:
            guidialog.WarningMessage(self.window, _('Snapshot restored but the'
                                                     u' following mod files were missing from your installation: \n\n%s\n') % (
                                          missing_po,))
        else:
            guidialog.InfoMessage(self.window, _('Active mods snapshot restored.'))


# ------------------------------------------------------------------------------

class snapshot_po_import(Link):  # Polemos
    """Import snapshot."""

    def __init__(self, type='txt'):
        """Init."""
        Link.__init__(self)
        self.type = type

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Import snapshot(s)'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modDetails
        osDrive = os.path.splitdrive(singletons.MashDir)[0]
        import_po = ''
        destDir = os.path.join(singletons.MashDir, 'snapshots')
        if self.type == 'txt':
            wildcard = u'Snapshot Files (*.txt)|*.txt'
        else:
            wildcard = '*.*'
        if not os.path.exists(destDir): os.makedirs(destDir)
        dialog = wx.FileDialog(self.window, u'Import snapshot file(s):', osDrive, '', wildcard,
                               wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        srcPaths = dialog.GetPaths()
        dialog.Destroy()
        for srcPath in srcPaths:
            (newSrcDir, srcFileName) = os.path.split(srcPath)
            if newSrcDir == destDir:
                guidialog.ErrorMessage(self.window,
                                        _("You can't import snapshots from this directory (It is the destination)."))
                return
            else:
                import_po = '%s\n%s' % (import_po, srcFileName)
                shutil.copy(srcPath, (os.path.join(destDir, srcFileName)))
        guidialog.InfoMessage(self.window, _("Snapshot(s) imported: \n%s\n") % (import_po,))
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class snapshot_po_select(Link):  # Polemos
    """Select a saved snapshot."""

    def __init__(self, type='txt'):
        """Init."""
        Link.__init__(self)
        self.type = type

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Restore saved snapshot'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modDetails
        srcDir = os.path.join(singletons.MashDir, 'snapshots')
        if self.type == 'txt':
            wildcard = u'Snapshot Files (*.txt)|*.txt'
        else:
            wildcard = '*.*'
        if not os.path.exists(srcDir): os.makedirs(srcDir)
        dialog = wx.FileDialog(self.window, u'Select snapshot file:', srcDir, '', wildcard, wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        srcPath = dialog.GetPath()
        dialog.Destroy()
        try:
            with io.open(srcPath, 'r', encoding=conf.settings['profile.encoding']) as f:
                select_po = f.readlines()
        except:
            guidialog.ErrorMessage(self.window, _('There was a problem opening this snapshot.'))
            return
        if len(select_po) <= 1: return
        order_po = [line.rstrip() for line in select_po]
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
        loadorder_mtime_increment = (mtime_last - 1026943162) // len(order_po)
        mtime = 1026943162
        missing_po = ''
        for p in order_po:
            try:
                mosh.modInfos[p].setMTime(mtime)
            except:
                missing_po = '%s\n%s' % (missing_po, p)
                continue
            mtime += loadorder_mtime_increment
        mod_po = mosh.ModInfos('', True)
        [mod_po.unload(x, True) for x in mosh.mwIniFile.loadOrder]
        for x in order_po:
            try:
                singletons.modList.ToggleModActivation(x)
            except:
                continue
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()
        if missing_po != '':
            guidialog.WarningMessage(self.window, _("Snapshot restored but "
                                                     u"the following mod files were missing from your installation: \n\n%s\n") % (
                                          missing_po,))
        elif missing_po == '':
            guidialog.InfoMessage(self.window, _('Active mods snapshot restored.'))


# ------------------------------------------------------------------------------

class snapshot_po_export(Link):  # Polemos
    """Export a snapshot."""

    def __init__(self, type='txt'):
        """Init."""
        Link.__init__(self)
        self.type = type

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Export snapshot'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modDetails
        destDir = os.path.join(singletons.MashDir, 'snapshots')
        if self.type == 'txt':
            wildcard = u'Snapshot Files (*.txt)|*.txt'
        else:
            wildcard = '*.*'
        if not os.path.exists(destDir): os.makedirs(destDir)
        destName = 'snapshot.txt'
        dialog = wx.FileDialog(self.window,
                               _('Export snapshot as:'), destDir, destName, wildcard,
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        (destDir, destName) = os.path.split(dialog.GetPath())
        dialog.Destroy()
        text = '\n'.join([x for x in mosh.mwIniFile.loadOrder])
        with io.open((os.path.join(destDir, destName)), 'w', encoding=conf.settings['profile.encoding']) as f:
            try:
                f.write(text)
                msg = _('Active mods snapshot taken and exported to: \n%s' % (destDir,))
            except Exception as err:
                msg = _('Unable to take/export snapshot. Reason:\n   %s' % err)
        guidialog.InfoMessage(self.window, msg)


# ------------------------------------------------------------------------------

class Mods_CopyActive(Link):  # Polemos: optimized, added a dialog informing about copying into the clipboard.
    """Copy active mods to clipboard."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Copy Active Mods List'))
        menu.AppendItem(menuItem)

    def Execute(self, event):  # Polemos fix
        """Handle selection."""
        window = singletons.mashFrame
        title = _('Active Mods:\n')
        text = title + '\n'.join([u'%03d  %s' % (num + 1, name) for num, name in enumerate(mosh.mwIniFile.loadOrder)])
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(wx.TextDataObject(text))
            except:
                wx.TheClipboard.SetData(wx.TextDataObject(text.decode(conf.settings['profile.encoding'])))
            wx.TheClipboard.Close()
            guidialog.InfoMessage(window, _('Active Mod Order copied to clipboard.'))


# ------------------------------------------------------------------------------

class Mods_MorrowindIni(Link):  # Polemos: made compatible with menubar.
    """Open Morrowind.ini."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Morrowind.ini...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(os.path.exists(os.path.join(conf.settings['mwDir'], 'Morrowind.ini')))

    def Execute(self, event):
        """Handle selection."""
        os.startfile(os.path.join(conf.settings['mwDir'], 'Morrowind.ini'))


# ------------------------------------------------------------------------------

class Mods_Conf_Bck(Link):  # Polemos
    """Manual backup of Morrowind/OpenMW configuration files."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        openmw = conf.settings['openmw']
        Link.AppendToMenu(self, menu, window, data)
        if not openmw:
            menuItem = wx.MenuItem(menu, self.id, _('Backup/Restore Morrowind.ini'))
        elif openmw:
            menuItem = wx.MenuItem(menu, self.id, _('Backup/Restore Conf files'))
        menu.AppendItem(menuItem)
        if not openmw:
            path = os.path.join(conf.settings['mwDir'], 'Morrowind.ini')
        elif openmw:
            path = os.path.join(conf.settings['openmwprofile'], 'OpenMW.cfg')
        menuItem.Enable(os.path.exists(path))

    def Execute(self, event):
        """Handle selection."""
        guidialog.ConfBackup()


# ------------------------------------------------------------------------------

class Mods_OpenMWcfg(Link):  # Polemos
    """Open OpenMW.cfg."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('OpenMW.cfg...'))
        menu.AppendItem(menuItem)
        path = os.path.join(conf.settings['openmwprofile'], 'OpenMW.cfg')
        menuItem.Enable(os.path.exists(path))

    def Execute(self, event):
        """Handle selection."""
        path = os.path.join(conf.settings['openmwprofile'], 'OpenMW.cfg')
        os.startfile(path)


# ------------------------------------------------------------------------------

class Mods_SelectedFirst(Link):  # Polemos: made compatible with toolbar menu.
    """Sort loaded mods to the top."""

    def __init__(self, prefix=''):
        """Init."""
        Link.__init__(self)
        self.prefix = prefix

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, self.prefix + _('Selection'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if window.selectedFirst: menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        self.window.selectedFirst = not self.window.selectedFirst
        self.window.PopulateItems()
        singletons.MenuBar.mods_view_cond()


# ------------------------------------------------------------------------------

class Mods_LockTimes(Link):
    """Turn on resetMTimes feature."""

    def AppendToMenu(self, menu, window, data):
        """Add to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Lock Times'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        if mosh.modInfos.resetMTimes: menuItem.Check()

    def Execute(self, event):
        """Handle menu selection."""
        mosh.modInfos.resetMTimes = not mosh.modInfos.resetMTimes
        conf.settings['mosh.modInfos.resetMTimes'] = mosh.modInfos.resetMTimes
        if mosh.modInfos.resetMTimes:
            mosh.modInfos.refreshMTimes()
        else:
            mosh.modInfos.mtimes.clear()
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.mods_settings_cond()


# ------------------------------------------------------------------------------

class Mods_ReplacersData(ListEditorData):
    """Data capsule for resource replacers dialog."""

    def __init__(self, parent):
        """Initialize."""
        self.data = mosh.modInfos.getResourceReplacers()
        # --GUI
        ListEditorData.__init__(self, parent)

    def getItemList(self):
        """Returns load list keys in alpha order."""
        return sorted(self.data.keys(), key=lambda a: a.lower())

    def getChecks(self):
        """Returns checked state of items as array of True/False values matching Item list."""
        checked = []
        for item in self.getItemList(): checked.append(self.data[item].isApplied())
        return checked

    def check(self, item):
        """Checks items. Return true on success."""
        progress = None
        try:
            progress = guidialog.ProgressDialog(item)
            self.data[item].apply(progress)
            return True
        finally:
            if progress is not None: progress.Destroy()

    def uncheck(self, item):
        """Unchecks item. Return true on success."""
        try:
            wx.BeginBusyCursor()
            self.data[item].remove()
            return True
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------

class Mods_Replacers(Link):  # Polemos: made compatible with toolbar menu.
    """Mod Replacers dialog."""

    def AppendToMenu(self, menu, window, data):
        """Append ref replacer items to menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Replacers...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        data = Mods_ReplacersData(self.window)
        dialog = ListEditorDialog(self.window, -1, _('Replacers'), data, 'checklist')
        dialog.ShowModal()
        dialog.Destroy()


# ------------------------------------------------------------------------------

class Check_for_updates(Link):  # Polemos
    """Check for updates."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Check for updates'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        check_version('manual')
        singletons.statusBar.profile()


# ------------------------------------------------------------------------------

class Reset_Beth_Dates(Link):  # Polemos
    """Reset dates for Bethesda ESMs and BSAs."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Reset Bethesda Dates'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        data_files = mosh.dirs['mods'].s
        # Thanks John Moonsugar for the dates...
        DatesIndex = {'bloodmoon.bsa': 1051807050,
                      'bloodmoon.esm': 1051807050,
                      'morrowind.bsa': 1024695106,
                      'morrowind.esm': 1024695106,
                      'tribunal.bsa': 1035940926,
                      'tribunal.esm': 1035940926}
        # Reset Bethesda dates
        [os.utime(os.path.join(data_files, x), (DatesIndex[x.lower()],
                                                DatesIndex[x.lower()])) for x in os.listdir(data_files) if
         x.lower() in DatesIndex.keys()]
        # Finish
        try:
            test = self.window
        except:
            self.window = singletons.BSArchives.Archives
        guidialog.InfoMessage(self.window, _('The dates of the Bethesda Masters'
                                              u' (.ESM) and Archives (.BSA)\nhave been reset to their original dates.'))
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Create_Mashed_Patch(Link):  # Polemos
    """An easy way to create a mashed patch (Good for newbies)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Create Mashed Patch'))
        menu.AppendItem(menuItem)
        self.window = singletons.modList

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        # Check if TES3cmd is installed and if yes suggest multipatch
        if tes3cmd.getLocation():
            tmessage = _('TES3cmd detected.')
            message = _('Since you have TES3cmd installed you can use the TES3cmd Multipatch'
                        u' instead of Mashed Patch. TES3cmd\'s Multipatch is more powerful than'
                        u' the Mashed Patch since it not only creates merged leveled lists but'
                        u' also patches several other problems. You may create a multipatch by'
                        u' going on the TES3cmd menu and selecting it.')
            guidialog.ContinueQuery(self.window, tmessage, message, 'query.tes3cmd.multipatch', _('Mashed Patch?'),
                                     nBtn=False)
        # Proceed with Mashed Patch actions
        data_files = fChk(mosh.dirs['mods'].s)
        source_file = os.path.join(singletons.MashDir, 'Extras', 'Mashed Lists.esp')
        if not conf.settings['openmw']:  # Polemos: Regular Morrowind support
            dest_file = os.path.join(data_files, 'Mashed Lists.esp')
        elif conf.settings['openmw']:  # Polemos: OpenMW support
            dest_file = os.path.join(conf.settings['mashdir'], 'Mashed Lists.esp')
        if not os.path.isfile(source_file):
            guidialog.WarningMessage(self.window,
                                      _('"Extras" folder is missing from Wrye Mash installation.\nPlease re-install the application.'))
            return
        if os.path.isfile(dest_file):
            dialog = guidialog.askdialog(self.window, _('Replace existing Mashed Patch?'), _('Mashed Patch'))
            if dialog == wx.ID_YES:
                if not Remove(dest_file):
                    guidialog.WarningMessage(self.window,
                                              _('Access Denied.\n\nCannot remove old "Mashed Lists.esp".'))
                    return
                self.create_patch(source_file, dest_file)
        else:
            self.create_patch(source_file, dest_file)
        return

    def create_patch(self, source_file, dest_file):
        """Create Mashed Patch."""
        shutil.copyfile(source_file, dest_file)
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()
        if 'Mashed Lists.esp' not in mosh.mwIniFile.loadOrder: singletons.modList.ToggleModActivation(
            'Mashed Lists.esp')
        Mod_Import_MergedLists.Execute(Mod_Import_MergedLists(), ['Mashed Lists.esp', self.window])
        mosh.modInfos.refreshDoubleTime()
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Mods_IniTweaks(Link):  # Polemos: made compatible with toolbar menu.
    """Import LCV Schedules to mod file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('INI Tweaks...'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        # --Continue Query
        tmessage = _('Please Note:')
        message = _(
            u"Modifies games settings in Morrowind.ini by applying changes defined in a .mit (Morrowind INI Tweak) file.")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.iniTweaks.continue',
                                    _('INI Tweaks')) != wx.ID_OK:
            return
        # --File dialog
        mitDir = os.path.join(mosh.modInfos.dir, 'Mits')
        if not os.path.exists(mitDir):
            mitDir = conf.settings['mwDir']
        dialog = wx.FileDialog(self.window, _('INI Tweaks'), mitDir, '', '*.mit', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        mitPath = dialog.GetPath()
        dialog.Destroy()
        mosh.mwIniFile.applyMit(mitPath)
        guidialog.InfoMessage(self.window, _('%s applied.') % (os.path.split(mitPath)[1],), _('INI Tweaks'))


# ------------------------------------------------------------------------------

class Mods_Tes3cmd_Fixit():  # Polemos: made compatible with toolbar menu, more.
    """TES3cmd fixit."""

    def AppendToMenu(self, menu, window, data):
        self.window = window
        menuItem = menu.Append(wx.ID_ANY, _('Fixit (all active)'))
        menuId = menuItem.GetId()
        wx.EVT_MENU(window, menuId, self.Execute)
        if not tes3cmd.getLocation(): menuItem.Enable(False)

    def Execute(self, event):  # Polemos: fixes and more.
        try:
            test = self.window
        except:
            self.window = singletons.modList
        # User warnings
        if not tes3cmd.getLocation():
            guidialog.ErrorMessage(self.window, _("Couldn't find tes3cmd.exe to launch"))
            return
        if guidialog.WarningQuery(self.window, _('This is a lengthy process. '
                                                  u'Are you sure you wish to continue?'),
                                   _('TES3cmd')) != wx.ID_YES: return
        # Begin
        cmd = tes3cmd.Basic()
        t3_thread = Thread(target=cmd.fixit)
        t3_thread.start()
        with wx.WindowDisabler():
            wait = wx.BusyInfo(_('Please wait for TES3CMD to finish (this may take some time)...'))
            while t3_thread.isAlive(): wx.GetApp().Yield()
        del wait
        TES3cmd_log = guidialog.AdvLog(self.window, _('TES3cmd Fixit'), 'TES3cmd.log', 'Fixit')

        # Stderr
        if cmd.err:
            TES3cmd_log.write(_('\nErrors:\n-------\n'), 'RED')
            [TES3cmd_log.write(line, 'RED') for line in cmd.err]
            TES3cmd_log.write('\n\n')
        # Stdout
        if cmd.out:
            TES3cmd_log.write(_('\nOutput:\n--------\n'))
            [TES3cmd_log.write(line) for line in cmd.out]
        TES3cmd_log.finished()
        # Finished
        TES3cmd_log.ShowModal()
        singletons.mashFrame.RefreshData()
        self.chkResults()

    def chkResults(self):  # Polemos: Dedicated to Wrye Mash's bug finder Champion... StaticNation
        """Check TES3cmd mod list for irregularities."""
        # Are the bethesda masters first in order?
        self.modItems = singletons.modList.items[:]
        if len(self.modItems) <= 1: return
        self.bethMasters = ['morrowind.esm', 'tribunal.esm', 'bloodmoon.esm']
        if not all(
                [True if beth == nobeth.lower() else False for beth, nobeth in zip(self.bethMasters, self.modItems)]):
            reorder = self.reorderESM()
        else:
            reorder = False
        if not reorder: self.simpleReorder()

    def simpleReorder(self):
        """Ask to redate all mods with continuous dates."""
        tmessage = _('Would you like to re-date your mod order with continuous dates?')
        message = _('Note: This might not be necessary. Do it only if you wish to avoid having ESMs '
                    u'and ESPs sharing the same time stamps (aesthetics).')
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.fixit.order',
                                    _('Re-date Order?')) != wx.ID_OK: return
        self.applyOrder(self.modItems)

    def reorderESM(self):
        """Reorder Bethesda Masters to be first in order."""
        msg = _(
            u'The Bethesda masters (Morrowind.esm, Tribunal.esm and Bloodmoon.esm) are not first in the mod order anymore. '
            u'Would you like to move them in front of the other masters?')
        if guidialog.WarningQuery(None, msg, _('Bethesda Masters Warning')) != wx.ID_YES: return False
        result = [x for x in self.modItems if x.lower() in self.bethMasters]
        result.extend([x for x in self.modItems if x.lower() not in self.bethMasters])
        self.applyOrder(result)
        return True

    def applyOrder(self, order_po):  # Adapted from mlox source
        """Reorder mod list."""
        active = mosh.mwIniFile.loadOrder[:]
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
        loadorder_mtime_increment = (mtime_last - 1026943162) // len(order_po)
        mtime = 1026943162
        for mod in order_po:
            mosh.modInfos[mod].setMTime(mtime)
            mtime += loadorder_mtime_increment
        mod_po = mosh.ModInfos('', True)
        [mod_po.unload(x, True) for x in mosh.mwIniFile.loadOrder]
        [singletons.modList.ToggleModActivation(x) for x in order_po if x in active]
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class Mods_Mlox():  # Polemos discarding mlox.py in favor of mlox.exe. Almost complete recoding.
    """Mlox implementation."""

    def __init__(self):
        """Init."""
        # self.settingsKey = 'mash.ext.mlox.oldorder' # Polemos: Todo: Use this.
        self.mloxpath = conf.settings["mloxpath"]
        self.mloxdir = os.path.dirname(self.mloxpath)

    def AppendToMenu(self, menu, window, data):
        """Conditionally append item to menu."""
        self.window = window
        launchMloxId = self.AddToMenu(menu, _('Launch Mlox'))
        revertId = self.AddToMenu(menu, _('Revert Changes'))
        wx.EVT_MENU(window, launchMloxId, self.LaunchMlox)
        wx.EVT_MENU(window, revertId, self.MloxRevert)

    def AddToMenu(self, menu, text):
        """Adds an item to the menu, but disables it if mlox isn't found returns the id of the item."""
        menuItem = menu.Append(wx.ID_ANY, text)
        menuItem.Enable(os.path.isfile(self.mloxpath))
        return menuItem.GetId()

    def parseMlox(self, output):
        """Mlox mod order parser."""
        if os.path.isfile(os.path.join(self.mloxdir, output)):
            with io.open(os.path.join(self.mloxdir, output), 'r',
                         encoding=conf.settings['profile.encoding']) as mloxOut:
                return mloxOut.readlines(), True
        return None, False

    def mlox_order_files(self):
        """Parse mlox output."""
        cur_po_order, cur_po = self.parseMlox('current_loadorder.out')
        new_po_order, new_po = self.parseMlox('mlox_new_loadorder.out')
        cur_po_exist, changed_po = False, False
        if all([cur_po, new_po]): cur_po_exist, changed_po = True, cur_po_order != new_po_order
        return (cur_po_exist, cur_po_order, new_po_order, changed_po)

    def LaunchMlox(self, event):
        """Launch mlox."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        try:
            os.chdir(self.mloxdir)
            if os.path.isfile(self.mloxpath):
                os.spawnl(os.P_NOWAIT, 'mlox.exe', 'mlox.exe')
                guidialog.InfoMessage(self.window, _('Click OK when mlox is closed.'))
            else:
                guidialog.ErrorMessage(self.window, _('Couldn\'t find mlox.exe to launch'))
        except:
            guidialog.ErrorMessage(self.window, _('Couldn\'t find mlox.exe to launch'))
        os.chdir(singletons.MashDir)

    def MloxRevert(self, event):
        """Revert mlox changes."""
        try:
            test = self.window
        except:
            self.window = singletons.modList
        cur_po_exist, cur_po_order, new_po_order, changed_po = self.mlox_order_files()
        if not cur_po_exist:
            guidialog.ErrorMessage(self.window,
                                    _('Cannot revert, mlox.exe is missing or mlox directory is incorrect.'))
        elif cur_po_order == new_po_order:
            guidialog.ErrorMessage(self.window, _('Cannot revert, nothing changed since last mlox execution.'))
        else:
            self.MloxSort()

    def MloxSort(self):
        """Sort mod order."""
        cur_po_exist, cur_po_order, new_po_order, changed_po = self.mlox_order_files()
        old_mod_list = [line.rstrip() for line in cur_po_order]
        mtime_first = 1026943162
        # Apply order
        if len(old_mod_list) > 1:
            mtime_last = int(time.time())
            if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
            loadorder_mtime_increment = (mtime_last - mtime_first) // len(old_mod_list)
            mtime = mtime_first
            for p in old_mod_list:
                mosh.modInfos[p].setMTime(mtime)
                mtime += loadorder_mtime_increment
            mosh.modInfos.refreshDoubleTime()
            singletons.modList.Refresh()


# Mod Links -------------------------------------------------------------------

class Mod_GroupsData(object):
    """Stub class for backward compatibility with old settings files."""
    pass


# ------------------------------------------------------------------------------

class Mod_LabelsData(ListEditorData):
    """Data capsule for label editing dialog."""

    def __init__(self, parent, strings):
        """Initialize."""
        # --Strings
        self.column = strings.column
        self.setKey = strings.setKey
        self.addPrompt = strings.addPrompt
        # --Key/type
        self.data = conf.settings[self.setKey]
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRename = True
        self.showRemove = True

    def getItemList(self):
        """Returns load list keys in alpha order."""
        return sorted(self.data, key=lambda a: a.lower())

    def add(self):
        """Adds a new group."""
        # --Name Dialog
        # --Dialog
        dialog = wx.TextEntryDialog(self.parent, self.addPrompt)
        result = dialog.ShowModal()
        # --Okay?
        if result != wx.ID_OK:
            dialog.Destroy()
            return
        newName = dialog.GetValue()
        dialog.Destroy()
        if newName in self.data:
            guidialog.ErrorMessage(self.parent, _('Name must be unique.'))
            return False
        elif len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent, _('Name must be between 1 and 64 characters long.'))
            return False
        conf.settings.setChanged(self.setKey)
        self.data.append(newName)
        self.data.sort()
        return newName

    def rename(self, oldName, newName):
        """Renames oldName to newName."""
        # --Right length?
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent, _('Name must be between 1 and 64 characters long.'))
            return False
        # --Rename
        conf.settings.setChanged(self.setKey)
        self.data.remove(oldName)
        self.data.append(newName)
        self.data.sort()
        # --Edit table entries.
        colGroup = self.parent.data.table.getColumn(self.column)
        for fileName in colGroup.keys():
            if colGroup[fileName] == oldName: colGroup[fileName] = newName
        self.parent.PopulateItems()
        # --Done
        return newName

    def remove(self, item):
        """Removes group."""
        conf.settings.setChanged(self.setKey)
        self.data.remove(item)
        # --Edit table entries.
        colGroup = self.parent.data.table.getColumn(self.column)
        for fileName in colGroup.keys():
            if colGroup[fileName] == item: del colGroup[fileName]
        self.parent.PopulateItems()
        # --Done
        return True


# ------------------------------------------------------------------------------

class Mod_Labels(object):
    """Add mod label links."""

    def __init__(self):
        """Initialize."""
        self.labels = conf.settings[self.setKey]

    def GetItems(self):
        items = self.labels[:]
        items.sort(key=lambda a: a.lower())
        return items

    def AppendToMenu(self, menu, window, data):
        """Append label list to menu."""
        self.window = window
        self.data = data
        menu.Append(self.idList.EDIT, self.editMenu)
        menu.AppendSeparator()
        menu.Append(self.idList.NONE, _('None'))
        ids = iter(self.idList)
        for item in self.GetItems():
            try:
                menu.Append(ids.next(), item)
            except StopIteration:
                pass
        # --Events
        wx.EVT_MENU(window, self.idList.EDIT, self.DoEdit)
        wx.EVT_MENU(window, self.idList.NONE, self.DoNone)
        wx.EVT_MENU_RANGE(window, self.idList.BASE, self.idList.MAX, self.DoList)

    def DoNone(self, event):
        """Handle selection of None."""
        fileLabels = self.window.data.table.getColumn(self.column)
        for fileName in self.data: del fileLabels[fileName]
        self.window.PopulateItems()

    def DoList(self, event):
        """Handle selection of label."""
        label = self.GetItems()[event.GetId() - self.idList.BASE]
        fileLabels = self.window.data.table.getColumn(self.column)
        for fileName in self.data: fileLabels[fileName] = label
        self.window.Refresh(self.data)

    def DoEdit(self, event):
        """Show label editing dialog."""
        data = Mod_LabelsData(self.window, self)
        dialog = ListEditorDialog(self.window, -1, self.editWindow, data)
        dialog.ShowModal()
        dialog.Destroy()


# ------------------------------------------------------------------------------

class Mod_Groups(Mod_Labels):
    """Add mod group links."""

    def __init__(self):
        """Initialize."""
        self.column = 'group'
        self.setKey = 'mash.mods.groups'
        self.editMenu = _('Edit Groups...')
        self.editWindow = _('Groups')
        self.addPrompt = _('Add group:')
        self.idList = ID_GROUPS
        Mod_Labels.__init__(self)


# ------------------------------------------------------------------------------

class Mod_Ratings(Mod_Labels):
    """Add mod rating links."""

    def __init__(self):
        """Initialize."""
        self.column = 'rating'
        self.setKey = 'mash.mods.ratings'
        self.editMenu = _('Edit Ratings...')
        self.editWindow = _('Ratings')
        self.addPrompt = _('Add rating:')
        self.idList = ID_RATINGS
        Mod_Labels.__init__(self)


# ------------------------------------------------------------------------------

class Mod_CopyToEsmp(Link):
    """Create an esp(esm) copy of selected esm(esp)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Copy to Esm'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)
        # --Filetype
        fileInfo = self.fileInfo = window.data[data[0]]
        if fileInfo.isEsm(): menuItem.SetText(_('Copy to Esp'))

    def Execute(self, event):
        """Handle menu selection."""
        fileInfo = self.fileInfo
        newType = (fileInfo.isEsm() and 'esp') or 'esm'
        modsDir = fileInfo.dir
        curName = fileInfo.name
        newName = curName[:-3] + newType
        # --Replace existing file?
        if os.path.exists(os.path.join(modsDir, newName)):
            result = guidialog.WarningMessage(self.window, _('Replace existing %s?') % (newName,),
                                               style=(wx.YES_NO | wx.ICON_EXCLAMATION))
            if result != wx.ID_YES: return
            mosh.modInfos[newName].makeBackup()
        # --Copy, set type, update mtime.
        self.window.data.copy(curName, modsDir, newName, True)
        self.window.data.table.copyRow(curName, newName)
        newInfo = self.window.data[newName]
        newInfo.setType(newType)
        # --Repopulate
        self.window.Refresh(detail=newName)


# ------------------------------------------------------------------------------

class Mod_Export_Dialogue(Link):
    """Export dialog from mod to text file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Dialogue'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        textName = os.path.splitext(fileName)[0] + '_Dialogue.txt'
        textDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        # --File dialog
        dialog = wx.FileDialog(self.window, _('Export dialogs to:'), textDir, textName, '*.*',
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        textPath = dialog.GetPath()
        dialog.Destroy()
        (textDir, textName) = os.path.split(textPath)
        conf.settings['mosh.workDir'] = textDir
        conf.settings['mash.dialEdit.path'] = textPath
        # --Export
        fileDials = mosh.FileDials(mosh.modInfos[fileName])
        fileDials.load()
        fileDials.dumpText(textPath, 'topic')


# ------------------------------------------------------------------------------

class Mod_Export_Scripts(Link):
    """Export scripts from mod to text file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Scripts'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        textName = os.path.splitext(fileName)[0] + '_Scripts.mws'
        textDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        # --File dialog
        dialog = wx.FileDialog(self.window, _('Export scripts to:'), textDir, textName, '*.*',
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        textPath = dialog.GetPath()
        dialog.Destroy()
        (textDir, textName) = os.path.split(textPath)
        conf.settings['mosh.workDir'] = textDir
        conf.settings['mash.scriptEdit.path'] = textPath
        # --Export
        fileScripts = mosh.FileScripts(mosh.modInfos[fileName])
        fileScripts.load()
        fileScripts.dumpText(textPath)


# ------------------------------------------------------------------------------

class Mod_Import_Dialogue(Link):
    """Import dialog from text file to mod."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Dialogue'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        textPath = conf.settings.get('mash.dialEdit.path')
        if textPath:
            (textDir, textName) = os.path.split(textPath)
        else:
            textName = os.path.splitext(fileName)[0] + '_Dialogue.txt'
            textDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        # --File dialog
        dialog = wx.FileDialog(self.window, _('Import dialogs from:'), textDir, textName, '*.*', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        textPath = dialog.GetPath()
        dialog.Destroy()
        (textDir, textName) = os.path.split(textPath)
        conf.settings['mosh.workDir'] = textDir
        conf.settings['mash.dialEdit.path'] = textPath
        # --Import
        fileInfo = mosh.modInfos[fileName]
        fileInfo.makeBackup()
        fileDials = mosh.FileDials(fileInfo)
        fileDials.load()
        report = fileDials.loadText(textPath)
        fileDials.save()
        fileInfo.setMTime()
        fileInfo.refresh()
        self.window.Refresh(fileName)
        guidialog.LogMessage(self.window, '', report, fileName)


# ------------------------------------------------------------------------------

class Mod_Import_LCVSchedules(Link):
    """Import LCV Schedules to mod file."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('LCV Schedules'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        # --Continue Query
        tmessage = _("Generates LCV schedule scripts from an LCV schedule text file, and inserts\n"
                     u"(but does not compile) the scripts into the current mod file.")
        message = _("You should not use this feature unless you know exactly what you're doing.")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.schedules.import.continue',
                                    _('Import LCV Schedules...')) != wx.ID_OK: return

        # --File dialog
        def pickScheduleFile(caption, textPath):
            """Shows file dialog to pick schedule file."""
            if textPath:
                (textDir, textName) = os.path.split(textPath)
            else:
                textDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
                textName = 'LCV Schedules.etxt'
            dialog = wx.FileDialog(self.window, caption, textDir, textName, '*.*', wx.FD_OPEN)
            if dialog.ShowModal() != wx.ID_OK:
                textPath = None
            else:
                textPath = dialog.GetPath()
            dialog.Destroy()
            return textPath

        # --Get text path
        table = self.window.data.table
        textPath = table.getItem(fileName, 'schedules.path')
        textPath = pickScheduleFile(_('Import LCV schedules from:'), textPath)
        if not textPath: return
        (textDir, textName) = os.path.split(textPath)
        table.setItem(fileName, 'schedules.path', textPath)
        # --Import
        caption = textName
        log = mosh.LogFile(BytesIO())
        try:
            generator = mosh.ScheduleGenerator()
            generator.log = log
            generator.loadText(textPath, pickScheduleFile)
            fileInfo = mosh.modInfos.data.get(fileName)
            generator.save(fileInfo)
            fileInfo.refresh()
            self.window.Refresh(fileName)
        finally:
            guidialog.LogMessage(self.window, u'', log.out.getvalue(), caption)


# ------------------------------------------------------------------------------

class Mod_Import_MergedLists(Link):
    """Import merged lists from load file."""

    def AppendToMenu(self, menu, window, data):
        """Append link to a menu."""
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Merged Lists'))
        menu.AppendItem(menuItem)
        enable = (len(self.data) == 1 and mosh.modInfos[self.data[0]].tes3.hedr.author == 'Wrye Mash')
        menuItem.Enable(enable)

    def Execute(self, event):
        """Handle activation event."""
        try:
            fileName = self.data[0]
        except:
            fileName = event[0]
            self.window = event[1]
        fileInfo = mosh.modInfos[fileName]
        caption = fileName
        log = mosh.LogFile(BytesIO())
        progress = guidialog.ProgressDialog(caption)
        try:
            progress.setMax(10 + len(mosh.mwIniFile.loadOrder))
            proCounter = 0
            progress(proCounter, _('Loading %s' % fileName))
            fileLists = mosh.FileLists(fileInfo)
            fileLists.log = log
            fileLists.load()
            fileLists.beginMerge()
            proCounter += 5
            # --Go through load list
            bethMasters = {'Morrowind.esm', 'Tribunal.esm', 'Bloodmoon.esm'}
            for loadName in mosh.mwIniFile.loadOrder:
                progress(proCounter, _('Reading: %s' % loadName))
                proCounter += 1
                loadInfo = mosh.modInfos[loadName]
                # --Skip bethesda masters and mods with 'Wrye Mash' as author
                if (loadName in bethMasters or loadInfo.tes3.hedr.author == 'Wrye Mash'): continue
                # --TesTool file?
                if loadName == 'Merged_Leveled_Lists.esp':
                    message = _("TesTool Merged_Leveled_Lists.esp skipped. Please remove it from your load list.")
                    guidialog.WarningMessage(self.window, message)
                    continue
                newFL = mosh.FileLists(loadInfo, False)
                newFL.load()
                fileLists.mergeWith(newFL)
            progress(proCounter, _('Saving: %s' % fileName))
            fileLists.completeMerge()
            fileLists.sortRecords()
            fileLists.safeSave()
            proCounter += 5
            # --Date
            fileInfo.refresh()
            fileHedr = fileInfo.tes3.hedr
            description = fileHedr.description
            reLists = re.compile('^Lists: .*$', re.M)
            description = reLists.sub(r'Lists: %s' % (formatDate(time.time()),), description)
            fileInfo.writeDescription(description)
            self.window.Refresh(fileName)
        finally:
            progress.Destroy()
            logValue = log.out.getvalue()
            if logValue:
                guidialog.LogMessage(self.window, '', logValue, caption)
            else:
                guidialog.InfoMessage(self.window, _("No lists required merging."))


# ------------------------------------------------------------------------------

class Mod_Import_Scripts(Link):
    """Import scripts from text file to mod."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Scripts'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(self.data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        textPath = conf.settings.get('mash.scriptEdit.path')
        if textPath:
            (textDir, textName) = os.path.split(textPath)
        else:
            textName = os.path.splitext(fileName)[0] + '_Scripts.mws'
            textDir = conf.settings.get('mosh.workDir', conf.settings['mwDir'])
        # --File dialog
        dialog = wx.FileDialog(self.window, _('Import scripts from:'), textDir, textName, '*.*', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        textPath = dialog.GetPath()
        dialog.Destroy()
        (textDir, textName) = os.path.split(textPath)
        conf.settings['mosh.workDir'] = textDir
        conf.settings['mash.dialEdit.path'] = textPath
        # --Import
        fileInfo = mosh.modInfos[fileName]
        fileInfo.makeBackup()
        fileScripts = mosh.FileScripts(fileInfo)
        fileScripts.load()
        changed = fileScripts.loadText(textPath)
        if changed:
            fileScripts.save()
            fileInfo.setMTime()
            fileInfo.refresh()
            self.window.Refresh(fileName)
            report = _('Scripts changed:\n* ') + '\n* '.join(changed)
            guidialog.LogMessage(self.window, '', report, fileName)
        else:
            guidialog.InfoMessage(self.window, _('No scripts changed.'))


# ------------------------------------------------------------------------------

class Mod_Tes3cmd_Clean(Link):  # Polemos: Optimized code.
    """TES3cmd clean."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Clean with TES3cmd'))
        menu.AppendItem(menuItem)
        if not tes3cmd.getLocation(): menuItem.Enable(False)

    def Execute(self, event):
        self.form = tes3cmdgui.Cleaner(self.window, self.data)
        self.form.Show()
        self.form.Start(self.OnDone)

    def OnDone(self):
        logDir = os.path.join(conf.settings['mwDir'], u'Data Files', u'tes3cmd', u'Logs')
        if not os.path.exists(logDir): os.makedirs(logDir)
        for fileName in self.form.files:
            with io.open(os.path.join(logDir, '%s.log' % fileName), 'w', encoding='utf-8') as log:
                log.write(self.form.GetLog(fileName))
        self.window.Refresh()


# ------------------------------------------------------------------------------

class Mod_Tes3cmd_Sync(Link):  # By Abot, adapted by Polemos.
    """Update header field and sync the list of masters."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Sync masters'))
        menu.AppendItem(menuItem)
        if not tes3cmd.getLocation(): menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        tmsg = _('Update header field and sync the list of masters.')
        msg = _(
            u'This command will Update header field for the number of records in the plugin (if incorrect) and sync the list of masters'
            u' to the masters installed in "Data Files" by executing "tes3cmd.exe header --synchronize --debug --hide-backups --backup-dir"'
            u' (debug option is set so information may be displayed, as by default no messages are shown with this command).')
        if guidialog.ContinueQuery(self.window, tmsg,
                                    msg, 'query.tes3cmd.sync',
                                    _('Update header field and sync masters')) != wx.ID_OK: return
        # Scan
        cmd = tes3cmd.Basic()
        t3_thread = Thread(target=cmd.syncMasters, args=[self.data])
        t3_thread.start()
        with wx.WindowDisabler():
            wait = wx.BusyInfo('Please wait for TES3CMD to finish (this may take some time)...')
            while t3_thread.isAlive(): wx.GetApp().Yield()
        del wait
        TES3cmd_log = guidialog.AdvLog(self.window, _('Updating header field and syncing masters'), 'TES3cmd.log',
                                        'HeaderMasterSync')
        # Stdout (no stderr is needed here)
        if cmd.out:
            TES3cmd_log.write(_('\nOutput:\n--------\n'))
            [TES3cmd_log.write(line) for line in cmd.out]
        TES3cmd_log.finished()
        # Finished
        TES3cmd_log.ShowModal()
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class Mod_TES3lint(Link):  # Polemos
    """Implemented TES3lint."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Check with TES3lint'))
        menu.AppendItem(menuItem)
        try:
            test = self.window
        except:
            self.window = singletons.modDetails

    def chkPaths(self, tes3lint=True, perl=True):
        if not os.path.isfile(conf.settings['tes3lint.location']): tes3lint = False
        if not os.path.isfile(conf.settings['tes3lint.perl']): perl = False
        return tes3lint, perl

    def CheckSettings(self):
        tes3lint, perl = self.chkPaths()
        if not tes3lint or not perl:
            guidialog.WarningMessage(self.window, _('You need to set/change '
                                                     u'some settings before you continue.\n\nClick OK to open the TES3lint configuration window.'))
            pos = conf.settings['tes3lint.pos']
            import plugins.tes3lint.settings as init
            init.TES3lint_Settings(self.window, pos)
            tes3lint, perl = self.chkPaths()
            if not tes3lint or not perl: return False
        return True

    def Execute(self, event):
        if not self.CheckSettings(): return
        last_args = conf.settings['tes3lint.last']
        self.cmd_factory(self.data, last_args)

    def cmd_factory(self, targets, last_args):
        perl = conf.settings['tes3lint.perl']
        tes3lint = conf.settings['tes3lint.location']
        if not conf.settings['openmw']: cwd = mosh.dirs['mods'].s  # Regular Morrowind support, Data Files dir.
        basic_flags = ['-n', '-r', '-a']
        if last_args[0] != 3:
            flag = basic_flags[last_args[0]]
        else:
            flag = '-f %s' % ', '.join(last_args[1])
        if last_args[2]:
            extra0 = '-D'
        else:
            extra0 = ''
        if last_args[3]:
            extra1 = '-v'
        else:
            extra1 = ''
        args = '%s %s %s' % (flag, extra0, extra1)
        command = 'cd /D "%s" & "%s" "%s" %s' % (cwd, perl, tes3lint, args)
        self.target_list = [('"%s"' % x) for x in targets]
        self.command_list = ['%s %s' % (command, x) for x in self.target_list]
        self.showlog()

    def showlog(self):
        self.log = guidialog.AdvLog(self.window, _('TES3lint Log.'), 'TES3lint.log', 'TES3lint')
        self.log.Show()
        tl_thread = Thread(target=self.subprocess)
        tl_thread.start()
        with wx.WindowDisabler():
            while tl_thread.isAlive(): wx.GetApp().Yield()
        self.log.ShowModal()

    def subprocess(self):
        for target in self.target_list:
            for cmd in self.command_list:
                ins = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, bufsize=1, universal_newlines=True)
                # , creationflags=DETACHED_PROCESS <== produces problems with perl scripts
                out, err = ins.communicate()
                if err: [self.log.write(line, 'RED') for line in err]
                if out: [self.log.write(line) for line in out]
                self.log.write('\n')
        self.log.finished()


# ------------------------------------------------------------------------------

class Mod_Tes3cmd_Merge(Link):  # By Abot, adapted by Polemos.
    """Create an esp containing all records present in selected mods."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Merge with TES3CMD'))
        menu.AppendItem(menuItem)
        if len(data) < 2 or not tes3cmd.getLocation(): menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        tmsg = _(
            u'This command will merge selected files to create "dumb.esp" containing all records present in the selected mods.')
        msg = _(
            u'This command will call "tes3cmd.exe dumb --debug --raw-with-header" passing selected files to create a file named '
            u'"dumb.esp" containing all records present in the selected mods (debug option is set so information may be displayed,'
            u' as by default no messages are shown with this command).\n\nPlease note that not all mods are mergable and may not '
            u'produce any results.')
        if guidialog.ContinueQuery(self.window, tmsg,
                                    msg, 'query.tes3cmd.merge', _('Dump selected files records to dumb.esp'),
                                    False) != wx.ID_OK: return
        # Scan
        cmd = tes3cmd.Basic()
        t3_thread = Thread(target=cmd.merge, args=[self.data])
        t3_thread.start()
        with wx.WindowDisabler():
            wait = wx.BusyInfo('Please wait for TES3CMD to finish (this may take some time)...')
            while t3_thread.isAlive(): wx.GetApp().Yield()
        del wait
        TES3cmd_log = guidialog.AdvLog(self.window, _('Merging records'), 'TES3cmd.log', 'Merge')
        # Stdout (no stderr is needed here)
        if cmd.out:
            TES3cmd_log.write(_('\nOutput:\n--------\n'))
            [TES3cmd_log.write(line) for line in cmd.out]
        TES3cmd_log.finished()
        # Finished
        TES3cmd_log.ShowModal()
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class Mods_custom_menu_item(object):  # Polemos
    """Add Custom Commands links."""

    def __init__(self):
        """Init."""
        self.window = singletons.mashFrame
        self.refresh()

    def refresh(self):
        data = mosh.CommandsData(self.window)
        self.data = data.Get()

    def GetItems(self):
        self.refresh()
        if self.data != {}:
            items = list(self.data.keys())
            items.sort(key=lambda x: x.casefold())
            return items

    def AppendToMenu(self, menu, window, data):
        if data is None: window = singletons.mashFrame
        self.item = data
        menu_ap = menu.Append
        event_m = wx.EVT_MENU
        menu_ap(ID_CUSTOMS.RUN, _('Run Custom...'), _('Run a Custom Command.'))
        menu.AppendSeparator()
        ids = iter(ID_CUSTOMS)
        try:
            [menu_ap(ids.next(), item, _('Execute %s command.' % item)) for item in self.GetItems()]
        except StopIteration:
            pass
        except:
            pass
        # Events
        event_m(window, ID_CUSTOMS.RUN, self.RunCMD)
        wx.EVT_MENU_RANGE(window, ID_CUSTOMS.BASE, ID_CUSTOMS.MAX, self.RunItem)

    def RunCMD(self, event):
        dialog = guidialog.RunDialog(self.window)
        user_command = dialog.GetValue
        targets = self.item
        if user_command:
            self.cmd_factory(_('Execution Log'), targets, user_command)
        else:
            return

    def RunItem(self, event):
        name = self.GetItems()[event.GetId() - ID_CUSTOMS.BASE]
        targets = self.item
        user_command = self.data[name]
        self.cmd_factory(name, targets, user_command)

    def cmd_factory(self, name, targets, user_command):
        if not conf.settings['openmw']: cwd = mosh.dirs['mods'].s  # Regular Morrowind support, Data Files dir.
        user_command = re.sub('%target%', '%target%', user_command, flags=re.IGNORECASE)  # In case of Case cases.
        user_command = user_command.replace('"%target%"', '%target%').replace("'%target%'", '%target%').replace(
            '%target%', '"%target%"')
        self.target_list = [user_command.replace('"%target%"', '"%s"' % x) for x in targets]
        self.command_list = ['cd /D "%s" & %s' % (cwd, x) for x in self.target_list]
        self.showlog(name)

    def showlog(self, title):
        self.log = guidialog.AdvLog(self.window, _('Execution Log for %s' % title), 'output.log')
        self.log.Show()
        lg_thread = Thread(target=self.subprocess)
        lg_thread.start()
        with wx.WindowDisabler():
            while lg_thread.isAlive(): wx.GetApp().Yield()
        self.log.ShowModal()

    def subprocess(self, id=None):
        for y in self.target_list:
            for x in self.command_list:
                ins = Popen(x, stdout=PIPE, stderr=PIPE, shell=True, bufsize=1, universal_newlines=True)
                # , creationflags=DETACHED_PROCESS <== produces problems with perl scripts
                out, err = ins.communicate()
                self.log.write('\n\n%s\n\n' % y, 'BLUE')
                if err: [self.log.write(line, 'RED') for line in err]
                if out: [self.log.write(line) for line in out]
        self.log.finished()


# ------------------------------------------------------------------------------

class Mod_RenumberRefs(Link):
    """Renumbers the references of an esp in an attempt to avoid local ref conflicts between mods."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Renumber Refs'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(data) == 1 and self.window.data[self.data[0]].isEsp())

    def Execute(self, event):
        """Handle menu selection."""
        import random
        # --Continue Query
        tmessage = _("Renumbers new objects placed by esp,")
        message = _("thus reducing likelihood of local ref conflicts between mods. Note that using TESCS on this mod "
                    u"will undo this renumbering. Also if an existing save game depends on this mod, doubling will likely result.")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.renumberRefs.continue',
                                    _('Renumber References...')) != wx.ID_OK:
            return
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        progress = None
        dialog = None
        try:
            # --Log and Progress
            log = mosh.LogFile(BytesIO())
            # --File Refs
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            # --Pick new object index number
            curFirst = fileRefs.getFirstObjectIndex()
            if curFirst == 0:
                guidialog.InfoMessage(self.window, _("No local references to renumber."))
                return
            table = self.window.data.table
            first = table.getItem(fileName, 'firstObjectIndex', random.randint(1001, 10001))
            dialog = wx.TextEntryDialog(self.window, _("Enter first objectIndex. [Current value: %d]") % (curFirst,),
                                        _('First Object Index'), repr(first))
            if dialog.ShowModal() != wx.ID_OK: return
            first = int(dialog.GetValue())
            if not (0 < first <= 100000):
                guidialog.ErrorMessage(self.window, _("Object index must be an integer in range 1:100,000."))
                return
            if first == curFirst:
                guidialog.ErrorMessage(self.window, _("New object index is same as old object index!"))
                return
            # --Renumber objects
            caption = _('Renumbering %s' % fileName)
            progress = guidialog.ProgressDialog(caption)
            changed = fileRefs.renumberObjects(first)
            fileRefs.safeSave()
            progress = progress.Destroy()
            guidialog.InfoMessage(self.window, _("References changed: %d.") % (changed,))
            if first == 1:
                table.delItem(fileName, 'firstObjectIndex')
            else:
                table.setItem(fileName, 'firstObjectIndex', first)
        # --Done
        finally:
            if progress is not None: progress.Destroy()
            if dialog: dialog.Destroy()
            self.window.Refresh(fileName)

    def getNewFirst(self, curFirst, newFirst):
        """Puts up a dialog asking user to select a new first number."""
        return 2000


# ------------------------------------------------------------------------------

class Mod_ShowReadme(Link):
    """Open the readme."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Readme...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        if not singletons.docBrowser:
            DocBrowser().Show()
            conf.settings['mash.modDocs.show'] = True
        singletons.docBrowser.SetMod(fileInfo.name)
        singletons.docBrowser.Raise()


# ------------------------------------------------------------------------------

class Mod_UpdatersData(ListEditorData):
    """Data capsule for Mod Updaters dialog."""

    def __init__(self, parent, toMod):
        # --Data
        self.toMod = toMod
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRemove = True

    def getItemList(self):
        """Returns fromMod list in correct order."""
        objectMaps = mosh.modInfos.getObjectMaps(self.toMod)
        return sorted(objectMaps.keys(), key=lambda a: a.lower())

    def remove(self, fromMod):
        """Removes object mapping from fromMod to self.toMod."""
        mosh.modInfos.removeObjectMap(fromMod, self.toMod)
        mosh.modInfos.saveObjectMaps()
        return True

    def add(self):
        """Peforms add operation."""
        # --Select mod file
        modDir = mosh.modInfos.dir
        wildcard = _('Morrowind Mod Files') + ' (*.esp;*.esm)|*.esp;*.esm'
        # --File dialog
        dialog = wx.FileDialog(self.parent, _('Select previous version:'), modDir, '', wildcard, wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return None
        fromPath = dialog.GetPath()
        dialog.Destroy()
        # --In right directory?
        (fromDir, fromMod) = os.path.split(fromPath)
        if fromDir.lower() != modDir.lower():
            guidialog.ErrorMessage(self.parent, _('Previous mod file must be located in Data Files directory.'))
            return None
        # --Old Refs
        oldInfo = mosh.modInfos[fromMod]
        oldRefs = oldInfo.extras.get('FileRefs')
        if not oldRefs:
            oldRefs = oldInfo.extras['FileRefs'] = mosh.FileRefs(oldInfo, True, True)
            oldRefs.refresh()
        # --New Refs
        newInfo = mosh.modInfos[self.toMod]
        newRefs = newInfo.extras.get('FileRefs')
        if not newRefs:
            newRefs = newInfo.extras['FileRefs'] = mosh.FileRefs(newInfo, True, True)
            newRefs.refresh()
        # --Remap
        objectMap = newRefs.getObjectMap(oldRefs)
        # --Save objectmap?
        if objectMap:
            mosh.modInfos.addObjectMap(fromMod, self.toMod, objectMap)
            mosh.modInfos.saveObjectMaps()
            return fromMod
        # --No object map to save?
        else:
            guidialog.InfoMessage(self.parent,
                                   _("No updater required for conversion from %s to %s.") % (fromMod, self.toMod))
            return None


# ------------------------------------------------------------------------------

class Mod_Updaters(Link):
    """Show dialog for editing updaters."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Updaters...'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        data = Mod_UpdatersData(self.window, self.data[0])
        dialog = ListEditorDialog(self.window, -1, _('Updaters'), data)
        dialog.ShowModal()
        dialog.Destroy()


# Saves Links -----------------------------------------------------------------

class Saves_ProfilesData(ListEditorData):
    """Data capsule for save profiles editing dialog."""

    def __init__(self, parent, hidden, defaultName):
        """Initialize."""
        self.hidden, self.defaultName = hidden, defaultName
        # --GUI
        ListEditorData.__init__(self, parent)
        self.showAdd = True
        self.showRename = True
        self.showRemove = True

    def getItemList(self):
        """Returns load list keys in alpha order."""
        # --Get list of directories in Hidden, but do not include default.
        isGood = lambda a: os.path.isdir(os.path.join(self.hidden, a))
        profiles = [dir for dir in os.listdir(self.hidden) if isGood(dir)]
        profiles.sort(key=str.lower)
        profiles.sort(key=lambda a: a != self.defaultName)
        return profiles

    def add(self):
        """Adds a new profile."""
        newName = guidialog.TextEntry(self.parent, _('Enter profile name:'))
        if not newName: return False
        if newName in self.getItemList():
            guidialog.ErrorMessage(self.parent, _('Name must be unique.'))
            return False
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent, _('Name must be between 1 and 64 characters long.'))
            return False
        os.mkdir(os.path.join(self.hidden, newName))
        return newName

    def rename(self, oldName, newName):
        """Renames profile oldName to newName."""
        newName = newName.strip()
        lowerNames = (name.lower() for name in self.getItemList())
        # --Error checks
        if oldName == self.defaultName:
            guidialog.ErrorMessage(self.parent, self.defaultName + _(' cannot be renamed.'))
            return False
        if newName.lower() in lowerNames:
            guidialog.ErrorMessage(self, _('Name must be unique.'))
            return False
        if len(newName) == 0 or len(newName) > 64:
            guidialog.ErrorMessage(self.parent, _('Name must be between 1 and 64 characters long.'))
            return False
        # --Rename
        oldDir, newDir = (os.path.join(self.hidden, dir) for dir in (oldName, newName))
        os.rename(oldDir, newDir)
        if oldName == conf.settings['mash.profile']:
            conf.settings['mash.profile'] = newName
        return newName

    def remove(self, profile):
        """Removes load list."""
        # --Can't remove active or Default directory.
        if profile == conf.settings['mash.profile']:
            guidialog.ErrorMessage(self.parent, _('Active profile cannot be removed.'))
            return False
        if profile == self.defaultName:
            guidialog.ErrorMessage(self.parent, _('Default profile cannot be removed.'))
            return False
        # --Get file count. If > zero, verify with user.
        profileDir = os.path.join(self.hidden, profile)
        files = [file for file in os.listdir(profileDir) if mosh.reSaveFile.search(file)]
        if files:
            message = _('Delete profile %s and the %d save files it contains?') % (profile, len(files))
            if guidialog.WarningQuery(self.parent, message, _('Delete Profile')) != wx.ID_YES:
                return False
        # --Remove directory
        shutil.rmtree(profileDir)  # --DO NOT SCREW THIS UP!!!
        return True


# ------------------------------------------------------------------------------

class Saves_Profiles(object):
    """Select a save set profile -- i.e. swap save files in/out."""

    def __init__(self):
        """Initialize."""
        self.idList = ID_PROFILES

    def GetItems(self):
        self.hidden = os.path.join(mosh.saveInfos.dir, conf.settings['mosh.fileInfo.hiddenDir'])
        self.defaultName = _('Default')
        self.defaultDir = os.path.join(self.hidden, self.defaultName)
        if not os.path.exists(self.defaultDir): os.makedirs(self.defaultDir)
        isGood = lambda a: os.path.isdir(os.path.join(self.hidden, a))
        items = [dir for dir in os.listdir(self.hidden) if isGood(dir)]
        items.sort(key=str.lower)
        items.sort(key=lambda a: a != self.defaultName)
        return items

    def AppendToMenu(self, menu, window, data):
        """Append label list to menu."""
        self.window = window
        # --Edit
        menu.Append(self.idList.EDIT, _("Edit Profiles..."))
        menu.AppendSeparator()
        # --Profiles
        items = self.GetItems()
        curProfile = conf.settings.get('mash.profile', self.defaultName)
        if curProfile not in items: curProfile = self.defaultName
        for id, item in zip(self.idList, items):
            menuItem = wx.MenuItem(menu, id, item, kind=wx.ITEM_CHECK)
            menu.AppendItem(menuItem)
            menuItem.Check(item.lower() == curProfile.lower())
        # --Events
        wx.EVT_MENU(window, self.idList.EDIT, self.DoEdit)
        wx.EVT_MENU_RANGE(window, self.idList.BASE, self.idList.MAX, self.DoList)

    def DoEdit(self, event):
        """Show profiles editing dialog."""
        data = Saves_ProfilesData(self.window, self.hidden, self.defaultName)
        dialog = ListEditorDialog(self.window, -1, _('Save Profiles'), data)
        dialog.ShowModal()
        dialog.Destroy()
        singletons.MenuBar.saves_profiles_cond()

    def DoList(self, event):
        """Handle selection of label."""
        # --Profile Names
        arcProfile = conf.settings.get('mash.profile', self.defaultName)
        srcProfile = self.GetItems()[event.GetId() - self.idList.BASE]
        if srcProfile == arcProfile: return
        # --Dirs
        arcDir, srcDir = [os.path.join(self.hidden, dir) for dir in (arcProfile, srcProfile)]
        savesDir = mosh.saveInfos.dir
        # --Progress
        progress = None
        arcFiles = sorted(mosh.saveInfos.data)
        srcFiles = sorted(name for name in os.listdir(srcDir) if (len(name) > 5 and name[-4:].lower() == '.ess'))
        arcCount, srcCount = len(arcFiles), len(srcFiles)
        if (arcCount + srcCount) == 0: return
        try:
            progress = guidialog.ProgressDialog(_('Moving Files'))
            # --Move arc saves to arc profile directory
            for num, saveName in enumerate(arcFiles):
                progress(1.0 * num // (arcCount + srcCount), saveName)
                savesPath, profPath = [os.path.join(dir, saveName) for dir in (savesDir, arcDir)]
                if not os.path.exists(profPath): os.rename(savesPath, profPath)
            arcIniPath = os.path.join(arcDir, 'Morrowind.ini')
            shutil.copyfile(mosh.mwIniFile.path, arcIniPath)
            conf.settings['mash.profile'] = srcProfile
            # --Move src profile directory saves to saves directory.
            for num, saveName in enumerate(srcFiles):
                progress(1.0 * (arcCount + num) // (arcCount + srcCount), saveName)
                savesPath, profPath = [os.path.join(dir, saveName) for dir in (savesDir, srcDir)]
                if not os.path.exists(savesPath): os.rename(profPath, savesPath)
            srcIniPath = os.path.join(srcDir, 'Morrowind.ini')
            if os.path.exists(srcIniPath): shutil.copyfile(srcIniPath, mosh.mwIniFile.path)
            singletons.mashFrame.SetTitle('Wrye Mash: %s' % srcProfile)  # Polem-fix
        finally:
            progress.Destroy()
        self.window.details.SetFile(None)


# ------------------------------------------------------------------------------

class Saves_MapGridLines(Link):
    """Turns Map Gridlines on/off."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('World Map Gridlines'), kind=wx.ITEM_CHECK)
        menu.AppendItem(menuItem)
        menuItem.Check(conf.settings['mash.worldMap.gridLines'])

    def Execute(self, event):
        """Handle menu selection."""
        conf.settings['mash.worldMap.gridLines'] = not conf.settings['mash.worldMap.gridLines']
        if conf.settings['mash.menubar.enabled']: singletons.MenuBar.saves_misc_cond()


# Save Links ------------------------------------------------------------------

class Save_Duplicate(File_Duplicate):
    """Create a duplicate of the (savegame) file."""

    def Execute(self, event):
        """Handle menu selection."""
        data = self.data
        fileName = data[0]
        fileInfo = self.window.data[fileName]
        saveName = fileInfo.tes3.hedr.description + _(" Copy")
        if len(saveName) > 31: saveName = saveName[:31]
        # --Save name
        dialog = wx.TextEntryDialog(self.window, _('Duplicate as:'), _('Duplicate'), saveName)
        result = dialog.ShowModal()
        saveName = dialog.GetValue()
        dialog.Destroy()
        if result != wx.ID_OK or not saveName: return
        if len(saveName) > 31: saveName = saveName[:31]
        # --File Name
        base = re.sub(r'\W', '', saveName)
        if not base: base = 'SaveGame'
        if len(base) > 8: base = base[:8]
        count = 0
        destName = "%s%04d.ess" % (base, count)
        destDir = fileInfo.dir
        while os.path.exists(os.path.join(destDir, destName)):
            count += 1
            destName = "%s%04d.ess" % (base, count)
        # --Copy file and table info.
        self.window.data.copy(fileName, destDir, destName, setMTime=True)
        self.window.data.table.copyRow(fileName, destName)
        # --Set save name in new file
        saveInfo = self.window.data[destName]
        saveInfo.tes3.hedr.description = saveName
        saveInfo.tes3.hedr.changed = True
        saveInfo.writeHedr()
        # --Repopulate
        self.window.Refresh(detail=destName)


# ------------------------------------------------------------------------------

class Save_LoadMasters(Link):
    """Sets the load list to the save game's masters."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Load Masters'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        # --Clear current mods
        loadFiles = mosh.mwIniFile.loadFiles[:]
        for loadFile in loadFiles: mosh.modInfos.unload(loadFile, 0)
        # --Select my mods
        missing = []
        for masterName in fileInfo.masterNames:
            try:
                mosh.modInfos.load(masterName, 0)
            except KeyError as error:
                missing.append(error.args[0])
        mosh.mwIniFile.safeSave()
        # --Repopulate mods
        singletons.modList.PopulateItems()
        singletons.saveList.PopulateItems()
        self.window.details.SetFile(fileName)
        # --Missing masters?
        if missing:
            message = (_('Please update masters to correct for missing masters (%s).') % (','.join(missing),))
            guidialog.WarningMessage(self.window, message)


# ------------------------------------------------------------------------------

class Save_MapNotes(Link):
    """Extracts map notes from save game."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Map Notes'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):  # Polemos: beautification.
        """Handle menu selection."""
        reNewLine = re.compile(r'\n')
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        caption = _('Map Notes: ') + fileName
        progress = guidialog.ProgressDialog(caption)
        log = mosh.LogFile(BytesIO())
        try:
            fileRefs = mosh.FileRefs(fileInfo, True, True, log=log, progress=progress)
            fileRefs.refresh()
            for cell in sorted(fileRefs.cells, cmp=lambda a, b: a.cmpId(b)):
                log.setHeader(cell.getId())
                for endRecord in cell.endRecords:
                    if endRecord.name == 'MPNT':
                        log('  ' + reNewLine.sub(r'\n  ', mosh.cstrip(endRecord.data)))
        finally:
            if progress is not None: progress.Destroy()
            guidialog.ScrolledtextMessage(None, log.out.getvalue(), "Map Notes", False)


# ------------------------------------------------------------------------------

class Save_Remove_SpawnedCreatures(Link):
    """Removes all lvcrs (leveled creature spawn points)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Spawned Creatures'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        caption = fileName
        progress = guidialog.ProgressDialog(caption)
        count = 0
        try:
            fileRefs = mosh.FileRefs(fileInfo, progress=progress)
            fileRefs.refresh()
            count = fileRefs.removeLvcrs()
            if count:
                fileRefs.removeOrphanContents()
                fileRefs.safeSave()
                guidialog.InfoMessage(self.window, _("%d spawn points removed/reset.") % (count,))
            else:
                guidialog.InfoMessage(self.window, _("No spawn points to remove/reset!"))
        finally:
            if progress is not None: progress.Destroy()
            self.window.Refresh(fileName)


# ------------------------------------------------------------------------------

class Save_Remove_DebrisCells(Link):
    """Removes all debris cells -- cells that are not supported by any of the master files."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Debris Cells'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --Continue Query
        tmessage = _(
            u"This command will remove all references in cells that have been visited,\nbut are not supported by the current set of masters.")
        message = _(
            u"Typically this is used to cleanup exterior cells that were added by mods that have since been removed. Note "
            u"that if you have intentionally placed objects into such cells (e.g., a travelling ship), then those objects WILL BE LOST!")
        if guidialog.ContinueQuery(self.window, tmessage, message, 'query.removeDebrisCells.continue',
                                    _('Remove Debris Cells')) != wx.ID_OK: return
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        progress = guidialog.ProgressDialog(fileName)
        log = mosh.LogFile(BytesIO())
        count = 0
        try:
            # --Log and Progress
            caption = _('Removing Debris Cells')
            # --World Refs
            worldRefs = mosh.WorldRefs(log=log, progress=progress)
            try:
                worldRefs.addMasters(fileInfo.masterNames)
            except mosh.Tes3RefError as error:
                progress = progress.Destroy()
                message = ((
                                   _("%s has bad refs and must be repaired first.\n") +
                                   _("\nExample Bad Ref from %s:") +
                                   _("\n  Cell: %s\n  Object Id: %s\n  Object Index: %d") +
                                   _("\n  Mod Index: %d (%s)")) %
                           (error.inName, error.inName, error.cellId, error.objId, error.iObj, error.iMod,
                            error.masterName))
                guidialog.ErrorMessage(self.window, message)
                return
            # --File refs
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            count = worldRefs.removeDebrisCells(fileRefs)
            if count:
                fileRefs.safeSave()
                guidialog.LogMessage(self.window, '', log.out.getvalue(), fileName)
            else:
                guidialog.InfoMessage(self.window, _("No orphaned content present."))
        finally:
            progress.Destroy()
            self.window.Refresh(fileName)


# ------------------------------------------------------------------------------

class Save_RepairAll(Link):
    """Repairs the save game's refs by comparing their type and id against the types and ids of the save game's masters."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Repair All'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        if fileInfo.getStatus() > 10:
            guidialog.WarningMessage(self.window,
                                      _("File master list is out of date. Please edit masters before attempting repair."))
            return
        progress = None
        dialog = None
        try:
            # --Log and Progress
            caption = _('Repairing ') + fileName
            progress = guidialog.ProgressDialog(caption)
            log = mosh.LogFile(BytesIO())
            # --World Refs
            worldRefs = mosh.WorldRefs(log=log, progress=progress)
            try:
                worldRefs.addMasters(fileInfo.masterNames)
            except mosh.Tes3RefError as error:
                progress = progress.Destroy()
                message = ((
                                   _("%s has bad refs and must be repaired first.\n") +
                                   _("\nExample Bad Ref from %s:") +
                                   _("\n  Cell: %s\n  Object Id: %s\n  Object Index: %d") +
                                   _("\n  Mod Index: %d (%s)")) %
                           (error.inName, error.inName, error.cellId, error.objId, error.iObj, error.iMod,
                            error.masterName))
                guidialog.ErrorMessage(self.window, message)
                return
            # --File Refs for Save File
            progress.setBaseScale()
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            (cntRepaired, cntDeleted, cntUnnamed) = worldRefs.repair(fileRefs)
            # --Save games only...
            # --Remove debris records.
            cntDebris = worldRefs.removeDebrisRecords(fileRefs)
            # --Remove orphan contents
            log.setHeader(_("Orphaned content records:"))
            cntOrphans = fileRefs.removeOrphanContents()
            # --Remove bad leveled lists
            log.setHeader(_("Overriding lists:"))
            cntLists = worldRefs.removeOverLists(fileRefs)
            # --No problems?
            if not (cntRepaired or cntDeleted or cntUnnamed or cntDebris or cntOrphans or cntLists):
                progress = progress.Destroy()
                guidialog.InfoMessage(self.window, _("No problems found!"))
                return
            fileRefs.safeSave()
            progress = progress.Destroy()
            # --Problem Dialog
            message = (_("Objects repaired: %d.\nObjects deleted: %d.") % (cntRepaired, cntDeleted))
            message += (_("\nDebris records deleted: %d.\nOrphan contents deleted: %d.") % (cntDebris, cntOrphans))
            message += (_("\nOverriding lists deleted: %d.") % (cntLists,))
            guidialog.LogMessage(self.window, message, log.out.getvalue(), caption)
        # --Done
        finally:
            if progress is not None: progress.Destroy()
            if dialog: dialog.Destroy()
            self.window.Refresh(fileName)
        if progress is not None: progress.Destroy()


# ------------------------------------------------------------------------------

class Save_Review(Link):
    """Presents a list of warnings of possible problems."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Review'))
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def Execute(self, event):
        """Handle menu selection."""
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        progress = None
        try:
            # --Log and Progress
            caption = _('Review of %s' % fileName)
            progress = guidialog.ProgressDialog(caption)
            log = mosh.LogFile(BytesIO())
            # --File Refs for Save File
            fileRefs = mosh.FileRefs(fileInfo, log=log, progress=progress)
            fileRefs.refresh()
            progress.Destroy()
            # --List Bad refs
            fileRefs.listBadRefScripts()
            # --No problems?
            if not log.out.getvalue():
                guidialog.InfoMessage(self.window, _("Nothing noteworthy found."))
                return
            # --Problem Dialog
            guidialog.LogMessage(self.window, '', log.out.getvalue(), caption)
        # --Done
        finally:
            if progress is not None: progress.Destroy()


# ------------------------------------------------------------------------------

class Save_ShowJournal(Link):
    """Open the journal."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Journal...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(data) == 1)

    def Execute(self, event):
        """Handle menu selection."""
        fileName = self.data[0]
        if not singletons.journalBrowser:
            JournalBrowser().Show()
            conf.settings['mash.journal.show'] = True
        singletons.journalBrowser.SetSave(fileName)
        singletons.journalBrowser.Raise()


# ------------------------------------------------------------------------------

class Save_UpdateWorldMap(Link):  # Polemos: Added (I hope) support for MCP extended world map
    """Updates the savegame's world map."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menutxt = _('Update Map') if not conf.settings[
            'mash.mcp.extend.map'] else _('Update extended Map (MCP)')
        menuItem = wx.MenuItem(menu, self.id, menutxt)
        menu.AppendItem(menuItem)
        if len(data) != 1: menuItem.Enable(False)

    def mcpWarn(self):
        """Warn about MCP beta map function."""
        tmessage = _('MCP extended map support enabled.')
        message = _('This is an untested and beta support for reflecting added and removed landmasses, on saved games'
                    u' patched with MCP\'s extended map. Again, obviously, you need to have your game patched by MCP first.'
                    u'\n\nBefore proceeding make a backup of the saved game you wish to update, so that you may revert to it in case'
                    u' your saved game map is destroyed.\n\nYou have been warned, you are responsible for any actions taken, proceed'
                    u' with caution, take a backup and do it for science.\n\nClick "Yes" to proceed OR click "No" to abort...')
        if guidialog.ContinueQuery(self.window, tmessage,
                                    message, 'query.mcp.extended.map',
                                    _('Update extended Map (MCP)')) != wx.ID_OK: return False
        return True

    def Execute(self, event):
        """Handle menu selection."""
        if conf.settings['mash.mcp.extend.map']:
            if not self.mcpWarn(): return
        # --File Info
        fileName = self.data[0]
        fileInfo = self.window.data[fileName]
        if fileInfo.getStatus() > 10:
            guidialog.WarningMessage(self.window, _(
                u"File master list is out of date. Please edit masters before attempting repair."))
            return
        progress = None
        dialog = None
        try:
            # --Log and Progress
            caption = _('Re-mapping ') + fileName
            progress = guidialog.ProgressDialog(caption)
            # --World Refs
            worldRefs = mosh.WorldRefs(progress=progress)
            try:
                worldRefs.addMasters(fileInfo.masterNames)
            except mosh.Tes3RefError as error:
                progress = progress.Destroy()
                message = ((
                                   _("%s has bad refs and must be repaired first.\n") +
                                   _("\nExample Bad Ref from %s:") +
                                   _("\n  Cell: %s\n  Object Id: %s\n  Object Index: %d") +
                                   _("\n  Mod Index: %d (%s)")) %
                           (error.inName, error.inName, error.cellId, error.objId, error.iObj, error.iMod,
                            error.masterName))
                guidialog.ErrorMessage(self.window, message)
                return
            # --File Refs for Save File
            progress.setBaseScale()
            fileRefs = mosh.FileRefs(fileInfo, progress=progress)
            fileRefs.refresh()
            if not conf.settings['mash.mcp.extend.map']:  # Regular map support
                worldRefs.repairWorldMap(fileRefs, conf.settings['mash.worldMap.gridLines'])
            else:  # MCP extended map support
                worldRefs.repairWorldMapMCP(fileRefs, conf.settings['mash.worldMap.gridLines'])
            fileRefs.safeSave()
            progress = progress.Destroy()
            guidialog.InfoMessage(self.window, _('World map updated.'))
        # --Done
        finally:
            if progress is not None: progress.Destroy()
            if dialog: dialog.Destroy()
            self.window.Refresh(fileName)


# Masters Links ---------------------------------------------------------------

class Masters_CopyList(Link):
    """Copies list of masters to clipboard."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Copy List"))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        fileInfo = self.window.fileInfo
        fileName = fileInfo.name
        # --Get masters list
        caption = _('Masters for %s:') % (fileName,)
        log = mosh.LogFile(BytesIO())
        log.setHeader(caption)
        for num, name in enumerate(fileInfo.masterNames):
            version = mosh.modInfos.getVersion(name)
            if version:
                log('%03d  %s  (Version %s)' % (num + 1, name, version))
            else:
                log('%03d  %s' % (num + 1, name))
        # --Copy to clipboard
        if (wx.TheClipboard.Open()):
            text = mosh.winNewLines(log.out.getvalue())
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()


# ------------------------------------------------------------------------------

class Masters_Update(Link):
    """Updates masters list and prepares it for further manual editing. Automatically fixes: names, sizes and load order."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Update"))
        menu.AppendItem(menuItem)
        menuItem.Enable(not self.window.edited)

    def Execute(self, event):
        """Handle menu selection."""
        self.window.InitEdit()


# ------------------------------------------------------------------------------

class Masters_SyncToLoad(Link):
    """Syncs master list to current load list (for save games) or to masters files in current load list (for mods)."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        if self.window.fileInfo.isMod():
            menuItem = wx.MenuItem(menu, self.id, _("Sync to Load ESMs"))
        else:
            menuItem = wx.MenuItem(menu, self.id, _("Sync to Load List"))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        if not self.window.edited: self.window.InitEdit()
        # --Data
        fileInfo = self.window.fileInfo
        fileName = fileInfo.name
        # --Precheck Circularity
        if fileInfo.isMod():
            newMasters = []
            for loadFile in mosh.mwIniFile.loadFiles:
                if loadFile[-1].lower() == 'm': newMasters.append(loadFile)
            if mosh.modInfos.circularMasters([fileName], newMasters):
                guidialog.ErrorMessage(self.window,
                                        _("Cannot Sync to Load ESMs, since resulting master list would be circular."))
                return
        # --Unselect all
        for masterName in self.window.newMasters[:]: self.window.unload(masterName)
        # --Select esms?
        if fileInfo.isMod():
            fileName = fileInfo.name
            for loadFile in mosh.mwIniFile.loadFiles:
                if loadFile[-1].lower() == 'm': self.window.load(loadFile)
        # --Select all?
        else:
            for loadFile in mosh.mwIniFile.loadFiles: self.window.load(loadFile)
        # --Repop
        self.window.PopulateItems()


# ------------------------------------------------------------------------------

class Masters_RestoreModOrder(Link):  # Polemos
    """Changes mod order using the master list of the current saved game as the source."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        if self.window.fileInfo.isMod():
            return
        else:
            menuItem = wx.MenuItem(menu, self.id, _('Restore Mod Order from Save'))
        menu.AppendItem(menuItem)

    def Execute(self, event):
        """Handle menu selection."""
        order_po = self.window.oldMasters[:]
        if len(order_po) <= 1: return
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562  # Sun Dec  7 14:59:56 CST 2008
        loadorder_mtime_increment = (mtime_last - 1026943162) // len(order_po)
        mtime = 1026943162
        missing_po = ''
        for p in order_po:
            try:
                mosh.modInfos[p].setMTime(mtime)
            except:
                missing_po = '%s\n%s' % (missing_po, p)
                continue
            mtime += loadorder_mtime_increment
        mod_po = mosh.ModInfos('', True)
        [mod_po.unload(x, True) for x in mosh.mwIniFile.loadOrder]
        for x in order_po:
            try:
                singletons.modList.ToggleModActivation(x)
            except:
                continue
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        self.window.Refresh()
        singletons.mashFrame.RefreshData()
        if missing_po:
            guidialog.WarningMessage(self.window, _("Mod order restored but the"
                                                     u" following mod files were either missing or stored in an unknown encoding "
                                                     u"(try renaming them if they exist): \n\n%s\n") % (
                                          missing_po.decode(conf.settings['profile.encoding'], 'replace'),))
        else:
            guidialog.InfoMessage(self.window, _('Mod order successfully restored.'))


# Master Links ----------------------------------------------------------------

class Master_ChangeTo(Link):
    """Rename/replace master through file dialog."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Change to..."))
        menu.AppendItem(menuItem)
        menuItem.Enable(self.window.edited)

    def Execute(self, event):
        """Handle menu selection."""
        itemId = self.data[0]
        masterInfo = self.window.data[itemId]
        masterName = masterInfo.name
        # --File Dialog
        wildcard = _('Morrowind Mod Files') + ' (*.esp;*.esm)|*.esp;*.esm'
        dialog = wx.FileDialog(self.window, _('Change master name to:'), mosh.modInfos.dir, masterName, wildcard,
                               wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        (newDir, newName) = os.path.split(dialog.GetPath())
        dialog.Destroy()
        # --Valid directory?
        if newDir.encode('utf-8').lower() != mosh.modInfos.dir.encode('utf-8').lower():
            guidialog.ErrorMessage(self.window, _("File must be selected from Morrowind Data Files directory."))
            return
        elif newName == masterName:
            return
        # --Unselect item?
        if masterInfo.isLoaded: self.window.unload(masterName)
        # --Save Name
        masterInfo.setName(newName)
        self.window.load(newName)
        self.window.PopulateItems()


# Screen Links ------------------------------------------------------------------

class Config_ScreenShots(Link):  # Polemos: changed "Next Shot.." to a better name...
    """Sets screenshot base name and number."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Configure screenshots'))
        menu.AppendItem(menuItem)

    def Execute(self, event):  # Polemos: Compatibility changes for the menu bar.
        ini = mosh.mwIniFile
        base = ini.getSetting('General', 'Screen Shot Base Name', 'ScreenShot')
        next = ini.getSetting('General', 'Screen Shot Index', '0')
        rePattern = re.compile(r'^(.+?)(\d*)$', re.I)
        try:
            pattern = balt.askText(self.window, _("Screenshot base name, optionally with next screenshot number.\n"
                                                  u"E.g. ScreenShot or ScreenShot_101 or Subdir\\ScreenShot_201."),
                                   _("Configure screenshots."), base + next)
        except:
            pattern = balt.askText(singletons.screensList,
                                   _("Screenshot base name, optionally with next screenshot number.\n"
                                     u"E.g. ScreenShot or ScreenShot_101 or Subdir\\ScreenShot_201."),
                                   _("Configure screenshots."), base + next)
        if not pattern: return
        maPattern = rePattern.match(pattern)
        newBase, newNext = maPattern.groups()
        settings = {LString('General'): {
            LString('Screen Shot Base Name'): newBase,
            LString('Screen Shot Index'): (newNext or next),
            LString('Screen Shot Enable'): '1',
        }}
        screensDir = GPath(newBase).head
        if screensDir:
            if not screensDir.isabs(): screensDir = mosh.dirs['app'].join(screensDir)
            screensDir.makedirs()
        ini.saveSettings(settings)
        mosh.screensData.refresh()
        try:
            self.window.RefreshUI()
        except:
            singletons.screensList.RefreshUI()


# ------------------------------------------------------------------------------

class Screen_ConvertToJpg(Link):
    """Converts selected images to jpg files."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Convert to jpg'))
        menu.AppendItem(menuItem)
        convertable = [name for name in self.data if GPath(name).cext != '.jpg']
        menuItem.Enable(len(convertable) > 0)

    def Execute(self, event):
        # --File Info
        srcDir = self.window.data.dir
        progress = balt.Progress(_("Converting to Jpg"))
        try:
            progress.setFull(len(self.data))
            srcDir = mosh.screensData.dir
            for index, fileName in enumerate(self.data):
                progress(index, fileName.s)
                srcPath = srcDir.join(fileName)
                destPath = srcPath.root + '.jpg'
                if srcPath == destPath or destPath.exists(): continue
                bitmap = wx.Bitmap(srcPath.s)
                result = bitmap.SaveFile(destPath.s, wx.BITMAP_TYPE_JPEG)
                if not result: continue
                srcPath.remove()
        finally:
            if progress: progress.Destroy()
            mosh.screensData.refresh()
            self.window.RefreshUI()


# ------------------------------------------------------------------------------

class Screen_Rename(Link):
    """Renames files by pattern."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _('Rename...'))
        menu.AppendItem(menuItem)
        menuItem.Enable(len(data) > 0)

    def Execute(self, event):
        # --File Info
        rePattern = re.compile(r'^([^\\/]+?)(\d*)(\.(jpg|bmp|png))$', re.I)
        fileName0 = self.data[0]
        pattern = balt.askText(self.window, _("Enter new name. E.g. Screenshot 123.bmp"), _("Rename Files"),
                               fileName0.s)
        if not pattern: return
        maPattern = rePattern.match(pattern)
        if not maPattern:
            balt.showError(self.window, _("Bad extension or file root: %s" % pattern))
            return
        root, numStr, ext = maPattern.groups()[:3]
        numLen = len(numStr)
        num = int(numStr or 0)
        screensDir = mosh.screensData.dir
        for oldName in [GPath(item) for item in self.data]:
            newName = GPath(root) + numStr + oldName.ext
            if newName != oldName:
                oldPath = screensDir.join(oldName)
                newPath = screensDir.join(newName)
                if not newPath.exists(): oldPath.moveTo(newPath)
            num += 1
            numStr = repr(num)
            numStr = '0' * (numLen - len(numStr)) + numStr
        mosh.screensData.refresh()
        self.window.RefreshUI()


# App Links -------------------------------------------------------------------

class App_Morrowind(Link):
    """Launch Morrowind/OpenMW."""

    def GetBitmapButton(self, window, style=0):
        if not self.id: self.id = wx.NewId()
        button = wx.BitmapButton(window, self.id, singletons.images['morrowind'].GetBitmap(), style=style)
        self.edition = _("Launch Morrowind") if not conf.settings['openmw'] else _("Launch OpenMW")
        self.dir = conf.settings['mwDir'] if not conf.settings['openmw'] else conf.settings['openmwDir']
        self.progexe = 'Morrowind.exe' if not conf.settings['openmw'] else 'openmw-launcher.exe'
        button.SetToolTip(wx.ToolTip(self.edition))
        wx.EVT_BUTTON(button, self.id, self.Execute)
        return button

    def Execute(self, event):
        """Handle menu selection."""
        try:
            os.chdir(self.dir)
            os.spawnl(os.P_NOWAIT, self.progexe, self.progexe)
            if conf.settings.get('mash.autoQuit.on', False): singletons.mashFrame.Close()
        except:
            guidialog.WarningMessage(None, _('There was a problem launching %s.') % self.progexe)
        finally:
            os.chdir(singletons.MashDir)


# ------------------------------------------------------------------------------

class App_mge_xe(Link):  # Polemos: Added MGE XE in status bar.
    """Launch MGE XE, if found."""

    def GetBitmapButton(self, window, style=0):
        if not self.id: self.id = wx.NewId()
        button = wx.BitmapButton(window, self.id, singletons.images['MGEXEgui'].GetBitmap(), style=style)
        button.SetToolTip(wx.ToolTip(_('Launch MGE XE')))
        wx.EVT_BUTTON(button, self.id, self.Execute)
        return button

    def Execute(self, event):
        """Handle menu selection."""
        try:
            mgeexe_path = conf.settings['mgexe.dir'] if os.path.isfile(conf.settings['mgexe.dir']
                                                                       ) else '' or os.path.join(conf.settings['mwDir'],
                                                                                                 'MGEXEgui.exe')
            if os.path.isfile(mgeexe_path):
                conf.settings['mgexe.dir'] = mgeexe_path
                conf.settings['mgexe.detected'] = True
                os.spawnl(os.P_NOWAIT, mgeexe_path, 'MGEXEgui.exe')
            else:
                raise OSError()
        except:
            guidialog.WarningMessage(None,
                                      _('MGE XE executable not found.\n\nMGEXEgui.exe was not found in Morrowind Directory.'))
            conf.settings['mgexe.dir'] = ''
            conf.settings['mgexe.detected'] = False
            singletons.mashFrame.Refresh_StatusBar()


# ------------------------------------------------------------------------------

class App_mlox_po(Link):  # Polemos, new tool (mlox) in status bar.
    """Launch Mlox, if found."""

    def GetBitmapButton(self, window, style=0):
        if not self.id: self.id = wx.NewId()
        button = wx.BitmapButton(window, self.id, singletons.images['mlox'].GetBitmap(), style=style)
        button.SetToolTip(wx.ToolTip(_('Launch Mlox')))
        wx.EVT_BUTTON(button, self.id, self.Execute)
        return button

    def Execute(self, event):
        """Handle menu selection."""

        try:
            if os.path.isfile(conf.settings['mloxpath']):
                os.chdir(os.path.dirname(conf.settings['mloxpath']))
                os.spawnl(os.P_NOWAIT, conf.settings['mloxpath'], ' ')
                guidialog.InfoMessage(None, _('Click OK when mlox is closed.'))
            else:
                raise OSError()
        except:
            guidialog.WarningMessage(None, _('Mlox.exe was not found in the defined directory.'))
            singletons.mashFrame.Refresh_StatusBar()
            return
        finally:
            os.chdir(singletons.MashDir)
        # Import mlox output
        log = mosh.LogFile(BytesIO())
        [log('%s' % (name)) for num, name in enumerate(mosh.mwIniFile.loadOrder)]
        text = mosh.winNewLines(log.out.getvalue())
        mtime = 1026943162
        for x in text:
            try:
                mosh.modInfos[x].setMTime(mtime)
            except:
                continue
        mosh.modInfos.refreshDoubleTime()
        singletons.modList.Refresh()
        singletons.mashFrame.RefreshData()


# ------------------------------------------------------------------------------

class AutoQuit_Button(Link):
    """Button toggling application closure when launching Morrowind."""

    def __init__(self):
        """Init."""
        Link.__init__(self)
        self.gButton = None

    def SetState(self, state=None):
        """Sets state related info. If newState != none, sets to new state first.
        For convenience, returns state when done."""
        if state is None:  # --Default
            state = conf.settings.get('mash.autoQuit.on', False)
        elif state == -1:  # --Invert
            state = not conf.settings.get('mash.autoQuit.on', False)
        conf.settings['mash.autoQuit.on'] = state
        image = singletons.images[('check.off', 'check.on')[state]]
        tip = (_('Auto-Quit Disabled'), _('Auto-Quit Enabled'))[state]
        self.gButton.SetBitmapLabel(image.GetBitmap())
        self.gButton.SetToolTip(tooltip(tip))

    def GetBitmapButton(self, window, style=0):
        """Replaces button image after state change."""
        bitmap = singletons.images['check.off'].GetBitmap()
        gButton = self.gButton = wx.BitmapButton(window, -1, bitmap, style=style)
        gButton.Bind(wx.EVT_BUTTON, self.Execute)
        gButton.SetSize((24, 24))
        self.SetState()
        return gButton

    def Execute(self, event):
        """Invert state."""
        self.SetState(-1)


# ------------------------------------------------------------------------------

class App_Settings(Link):  # Added D.C.-G. for SettingsWindow. Polemos: Changes, addons.
    """Show settings window."""

    def GetBitmapButton(self, window, style=0):
        if not self.id: self.id = wx.NewId()
        button = wx.BitmapButton(window, self.id, singletons.images['settings'].GetBitmap(), style=style)
        button.SetToolTip(wx.ToolTip(_("Settings Window")))
        wx.EVT_BUTTON(button, self.id, self.Execute)
        return button

    def Execute(self, event):
        """Handle menu selection."""
        singletons.settingsWindow = SettingsWindow(parent=singletons.mashFrame, pos=conf.settings['mash.settings.pos'])
        singletons.settingsWindow.ShowModal()
        singletons.mashFrame.Refresh_StatusBar()


# ------------------------------------------------------------------------------

class App_Help(Link):
    """Show help browser."""

    def GetBitmapButton(self, window, style=0):
        if not self.id: self.id = wx.NewId()
        button = wx.BitmapButton(window, self.id, singletons.images['help'].GetBitmap(), style=style)
        button.SetToolTip(wx.ToolTip(_('Help File')))
        wx.EVT_BUTTON(button, self.id, self.Execute)
        return button

    def Execute(self, event):
        """Handle menu selection."""
        guidialog.HelpDialog(singletons.mashFrame, singletons.images,
                              conf.settings['mash.help.pos'], conf.settings['mash.help.size']).Show()
        conf.settings['mash.help.show'] = True


# ------------------------------------------------------------------------------

class Utils_Delete(Link):  # Added D.C.-G. for Utils panel.
    """Create a new utility."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Delete"))
        menu.AppendItem(menuItem)
        menuItem.Enable(True)

    def Execute(self, event):
        """Handle menu selection."""
        self.window.DeleteItem()


# ------------------------------------------------------------------------------

class Utils_Modify(Link):  # Added D.C.-G. for Utils panel.
    """Create a new utility."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("Modify"))
        menu.AppendItem(menuItem)
        menuItem.Enable(True)

    def Execute(self, event):
        """Handle menu selection."""
        self.window.ModifyItem()


# ------------------------------------------------------------------------------

class Utils_New(Link):  # Added D.C.-G. for Utils panel.
    """Create a new utility."""

    def AppendToMenu(self, menu, window, data):
        Link.AppendToMenu(self, menu, window, data)
        menuItem = wx.MenuItem(menu, self.id, _("New"))
        menu.AppendItem(menuItem)
        menuItem.Enable(True)

    def Execute(self, event):
        """Handle menu selection."""
        self.window.NewItem()


# Initialization --------------------------------------------------------------

def InitSettings():
    """Initialize settings (configuration store). First, read from file, then
    load defaults (defaults will not overwrite items extracted from file)."""
    res = mosh.initSettings()
    conf.settings = mosh.settings
    conf.settings.loadDefaults(conf.settingDefaults)
    if res:
        print('%s: [Notice] Configuration loaded.' % datetime.now())
    else:
        print('%s: [Warning] No configuration found, loading default configuration.' % datetime.now())


def installers_choose():  # Polemos.
    """Select Installers dir if not already defined."""
    guidialog.WarningMessage(None, _('Installers dir is not defined. Click OK to select a folder to'
                                      u' use (for mod installers).\n\nIf you are upgrading and you get this message, select your old Installers directory.'))
    while True:
        InstallersDialog = wx.DirDialog(None, _("Select your Installers directory."))
        result = InstallersDialog.ShowModal()
        InstallersDir = InstallersDialog.GetPath()
        InstallersDialog.Destroy()
        # --User canceled?
        if result != wx.ID_OK:
            retryDialog = wx.MessageDialog(None, _('You need to set the Installers directory to'
                                                   u' proceed. Are you sure you want to exit?'), _('Exit?'),
                                           wx.YES_NO | wx.ICON_EXCLAMATION)
            result = retryDialog.ShowModal()
            retryDialog.Destroy()
            if result == wx.ID_YES:
                conf.settings['all.ok'] = False
                return
        else:
            conf.settings['sInstallersDir'] = InstallersDir
            return


def InitDirs():  # Polemos: Added Installers dir check + OpenMW/TES3mp support.
    """Initialise directories."""
    if not conf.settings['openmw']:  # Regular Morrowind
        if conf.settings['sInstallersDir'] is None: installers_choose()
        if conf.settings['all.ok']:
            mosh.initDirs()
        else:
            return
        # Polemos: Mash.ini produces more problems than benefits. Removed for now. todo: Enable on conditions
        '''if GPath('mash.ini').exists():
            try: mosh.initDirs()
            except:
                installers_choose()
                if conf.settings['all.ok']: mosh.initDirs()
                else: return
        else:
            if conf.settings['sInstallersDir'] is None: installers_choose()
            if conf.settings['all.ok']: mosh.initDirs()
            else: return'''
    elif conf.settings['openmw']:  # OpenMW/TES3mp support
        try:
            mosh.initDirs()
        except:
            raise StateError(_('Problem to init dirs.'))


def InitImages():  # -# D.C.-G. for SettingsWindow, Polemos addons and changes (separator, mlox, mge-xe, interface...)
    """Initialize images (icons, checkboxes, etc.)."""
    imgPath, png, jpg, ico = 'images', wx.BITMAP_TYPE_PNG, wx.BITMAP_TYPE_JPEG, wx.BITMAP_TYPE_ICON
    # --Standard
    singletons.images['morrowind'] = Image(os.path.join(imgPath, r'morrowind.png'), png)
    singletons.images["settings"] = Image(os.path.join(imgPath, r"settings.png"), png)
    singletons.images['help'] = Image(os.path.join(imgPath, r'help.png'), png)
    singletons.images['mash.ico'] = Image(os.path.join(imgPath, r'Wrye Mash.ico'), ico)
    singletons.images['mash.ico.raw'] = Image(os.path.join(imgPath, r'wr_b_mini.png'), png)
    # --Misc
    singletons.images['mlox'] = Image(os.path.join(imgPath, r'mlox.png'), png)
    singletons.images['MGEXEgui'] = Image(os.path.join(imgPath, r'mgexegui.png'), png)
    singletons.images['wizard'] = Image(os.path.join(imgPath, r'daggerfall.png'), png)
    singletons.images['warning'] = Image(os.path.join(imgPath, r'warning.png'), png)
    singletons.images['wr_mini'] = Image(os.path.join(imgPath, r'wr_b_mini.png'), png)
    # --Varius
    singletons.images['about'] = Image(os.path.join(imgPath, r'wrye_bad.jpg'), png)
    singletons.images['wr_help'] = Image(os.path.join(imgPath, r'wrye_bad.png'), png)
    # --Interface
    singletons.images['check.on'] = Image(os.path.join(imgPath, r'check-on.png'), png)
    singletons.images['check.off'] = Image(os.path.join(imgPath, r'check-off.png'), png)
    singletons.images['mod.open'] = Image(os.path.join(imgPath, r'open.png'), png)
    singletons.images['mod.open.onhov'] = Image(os.path.join(imgPath, r'open-hov.png'), png)
    singletons.images['mod.save'] = Image(os.path.join(imgPath, r'save.png'), png)
    singletons.images['mod.save.onhov'] = Image(os.path.join(imgPath, r'save-hov.png'), png)
    singletons.images['mod.datetime.cp'] = Image(os.path.join(imgPath, r'mcopy.png'), png)
    singletons.images['mod.datetime.ps'] = Image(os.path.join(imgPath, r'mpaste.png'), png)
    singletons.images['master.menu'] = Image(os.path.join(imgPath, r'master.png'), png)
    singletons.images['master.menu.onhov'] = Image(os.path.join(imgPath, r'master.png'), png)
    # --Help browser
    singletons.images['help.bsas'] = Image(os.path.join(imgPath, r'bsas.jpg'), jpg)
    singletons.images['help.docbrowser'] = Image(os.path.join(imgPath, r'doc-browser.jpg'), jpg)
    singletons.images['help.installers'] = Image(os.path.join(imgPath, r'installers.jpg'), jpg)
    singletons.images['help.mods'] = Image(os.path.join(imgPath, r'mods.jpg'), jpg)
    singletons.images['help.saves'] = Image(os.path.join(imgPath, r'saves.jpg'), jpg)
    singletons.images['help.screenshots'] = Image(os.path.join(imgPath, r'screenshots.jpg'), jpg)
    singletons.images['help.settings'] = Image(os.path.join(imgPath, r'settings.jpg'), jpg)
    singletons.images['help.utilities'] = Image(os.path.join(imgPath, r'utilities.jpg'), jpg)
    singletons.images['help.settings2'] = Image(os.path.join(imgPath, r'settings2.jpg'), jpg)
    # --Checkboxes
    singletons.images['mash.checkboxes'] = Checkboxes()
    singletons.images['checkbox.green.on.32'] = (Image(os.path.join(imgPath, r'checkbox_green_on_32.png'), png))
    singletons.images['checkbox.blue.on.32'] = (Image(os.path.join(imgPath, r'checkbox_blue_on_32.png'), png))
    singletons.images['checkbox.red.x'] = Image(os.path.join(imgPath, r'checkbox_red_x.png'), png)
    # --App Main Icon
    wryeMashIcon = balt.ImageBundle()
    wryeMashIcon.Add(singletons.images['mash.ico.raw'])
    singletons.images['mash.main.ico'] = wryeMashIcon


def InitColors():  # Polemos
    """Initialize colors."""
    colors['mash.esm'] = colors['mash.installers.dirty'] = gui.interface.internalStyle['list.background']
    colors['mash.doubleTime.not'] = (235, 235, 235)
    colors['mash.doubleTime.exists'] = (255, 220, 220)
    colors['mash.doubleTime.load'] = (255, 100, 100)
    colors['mash.exOverLoaded'] = (0xFF, 0x99, 0)
    colors['mash.masters.remapped'] = (100, 255, 100)
    colors['mash.masters.changed'] = (220, 255, 220)
    colors['mash.installers.skipped'] = (0xe0, 0xe0, 0xe0)
    colors['mash.installers.outOfOrder'] = (0xDF, 0xDF, 0xC5)
    colors['bash.installers.dirty'] = (0xFF, 0xBB, 0x33)


def Mw():  # Todo: Temporal solution, change.
    """More compact."""
    return True if not conf.settings['openmw'] else False


def InitStatusBar():  # -# D.C.-G. for SettingsWindow, Polemos addons and changes.
    """Initialize status bar links."""
    MashStatusBar.links.append(App_Morrowind())
    MashStatusBar.links.append(AutoQuit_Button())
    if all([os.path.isfile(conf.settings['mgexe.dir']) or os.path.isfile(
            os.path.join(conf.settings['mwDir'], 'MGEXEgui.exe')), Mw()]):
        if not conf.settings['mgexe.dir']: conf.settings['mgexe.dir'] = os.path.join(conf.settings['mwDir'],
                                                                                     'MGEXEgui.exe')
        MashStatusBar.links.append(App_mge_xe())
    if all([os.path.isfile(conf.settings["mloxpath"]), Mw()]):
        MashStatusBar.links.append(App_mlox_po())
    MashStatusBar.links.append(App_Settings())
    MashStatusBar.links.append(App_Help())


def InitMasterLinks():  # Polemos: Added sort-by, restore mod order from save
    """Initialize master list menus."""
    MasterList.mainMenu.append(Masters_CopyList())
    MasterList.mainMenu.append(Masters_SyncToLoad())
    MasterList.mainMenu.append(Masters_Update())
    MasterList.mainMenu.append(SeparatorLink())
    if True:  # --Sort by
        sortMenu = MenuLink(_("Sort by"))
        sortMenu.links.append(Masters_SortBy('Master'))
        sortMenu.links.append(Masters_SortBy('Load Order'))
        MasterList.mainMenu.append(sortMenu)
    if Mw():
        MasterList.mainMenu.append(SeparatorLink())
        MasterList.mainMenu.append(Masters_RestoreModOrder())


def InitMasterLinks_items():  # Polemos: Different initialization for items links.
    """Item links"""
    MasterList.itemMenu.append(Master_ChangeTo())


def InitArchivesLinks():  # Polemos: menu for Archives mini Tab
    """Initialize Archives list menus."""
    if Mw(): BSArchivesList.mainMenu.append(Reset_Beth_Dates())


def InitArchivesLinks_items():  # Polemos: items links for Archives mini Tab
    """Initialize master list menus."""
    pass


def InitUtilsLinks():  # -# Added D.C.-G. for Utils panel. Polemos: Enabled item context menu for Utilitie Tab.
    """Initialize the Utils Panel list menu."""
    UtilsList.mainMenu.append(Utils_New())
    UtilsList.mainMenu.append(Utils_Modify())
    UtilsList.mainMenu.append(Utils_Delete())


def InitUtilsLinks_items():  # Polemos: Different initialization for items links.
    """Utils Items"""
    UtilsList.itemMenu.append(Utils_Modify())
    UtilsList.itemMenu.append(Utils_Delete())


def InitInstallerLinks():  # Polemos: Added open installers dir, enable extra info in progress bar, added new sorting items.
    """Initialize Installer tab menus."""
    # Add new
    InstallersPanel.mainMenu.append(Installers_Import())
    InstallersPanel.mainMenu.append(Installers_Import())
    InstallersPanel.mainMenu.append(SeparatorLink())
    # Sorting
    sortMenu = MenuLink(_('Sort by'))
    sortMenu.links.append(Installers_SortActive())
    sortMenu.links.append(Installers_SortProjects())
    sortMenu.links.append(SeparatorLink())
    sortMenu.links.append(Installers_SortBy('Package'))
    sortMenu.links.append(Installers_SortBy('Order'))
    sortMenu.links.append(Installers_SortBy('Group'))
    sortMenu.links.append(Installers_SortBy('Modified'))
    sortMenu.links.append(Installers_SortBy('Size'))
    sortMenu.links.append(Installers_SortBy('Files'))
    # sortMenu.links.append(Installers_SortStructure()) # Polemos: todo: Keep? Remove?
    InstallersPanel.mainMenu.append(sortMenu)
    # --Actions
    InstallersPanel.mainMenu.append(SeparatorLink())
    InstallersPanel.mainMenu.append(Installers_Open())
    InstallersPanel.mainMenu.append(Files_Open_installers_po())
    InstallersPanel.mainMenu.append(Installers_Refresh(fullRefresh=False))
    InstallersPanel.mainMenu.append(Installers_Refresh(fullRefresh=True))
    InstallersPanel.mainMenu.append(SeparatorLink())
    InstallersPanel.mainMenu.append(Installers_AddMarker())
    InstallersPanel.mainMenu.append(SeparatorLink())
    InstallersPanel.mainMenu.append(Installers_AnnealAll())
    # --Behavior
    InstallersPanel.mainMenu.append(SeparatorLink())
    InstallersPanel.mainMenu.append(Installers_AvoidOnStart())
    InstallersPanel.mainMenu.append(Installers_Enabled())
    InstallersPanel.mainMenu.append(Progress_info())
    InstallersPanel.mainMenu.append(SeparatorLink())
    InstallersPanel.mainMenu.append(Installers_AutoAnneal())
    InstallersPanel.mainMenu.append(Installers_RemoveEmptyDirs())
    InstallersPanel.mainMenu.append(Installers_ConflictsReportShowsInactive())
    InstallersPanel.mainMenu.append(Installers_ConflictsReportShowsLower())


def InitInstallerLinks_items():  # Polemos: Different initialization for items links.
    """Item links"""
    # --File
    InstallersPanel.itemMenu.append(Installer_Open())
    InstallersPanel.itemMenu.append(Installer_Repack())
    InstallersPanel.itemMenu.append(Installer_Duplicate())
    InstallersPanel.itemMenu.append(Installer_Rename())
    InstallersPanel.itemMenu.append(Installer_Delete())
    # --Install, uninstall, etc.
    InstallersPanel.itemMenu.append(SeparatorLink())
    InstallersPanel.itemMenu.append(Installer_Refresh())
    InstallersPanel.itemMenu.append(Installer_Move())
    InstallersPanel.itemMenu.append(SeparatorLink())
    InstallersPanel.itemMenu.append(Installer_HasExtraData())
    InstallersPanel.itemMenu.append(SeparatorLink())
    InstallersPanel.itemMenu.append(Installer_Anneal())
    InstallersPanel.itemMenu.append(Installer_Install())
    InstallersPanel.itemMenu.append(Installer_Install('LAST'))
    InstallersPanel.itemMenu.append(Installer_Install('MISSING'))
    InstallersPanel.itemMenu.append(Installer_Uninstall())
    InstallersPanel.itemMenu.append(SeparatorLink())
    # --Build
    InstallersPanel.itemMenu.append(InstallerArchive_Unpack())
    InstallersPanel.itemMenu.append(InstallerProject_Sync())


def InitModDataLinks():  # Polemos
    """Initialize ModData tab menus."""
    ModdataList.mainMenu.append(Open_Datamods_po())
    ModdataList.mainMenu.append(Open_Packages_po())


def InitModDataLinks_items():  # Polemos: Different initialization for items links.
    """Item links"""
    ModdataList.itemMenu.append(Remove_Mod())
    ModdataList.itemMenu.append(Rename_Mod())
    ModdataList.itemMenu.append(SeparatorLink())
    ModdataList.itemMenu.append(HomePage_Mod())


def InitPackageLinks():  # Polemos
    """Initialize ModData tab menus."""
    ModPackageList.mainMenu.append(Open_Packages_po())


def InitPackageLinks_items():  # Polemos: Different initialization for items links.
    """Item links"""
    ModPackageList.itemMenu.append(Install_Package())
    ModPackageList.itemMenu.append(Remove_Package())
    ModPackageList.itemMenu.append(SeparatorLink())
    ModPackageList.itemMenu.append(Open_Package())
    ModPackageList.itemMenu.append(Hide_Package())


def InitModLinks():  # Polemos addons and changes.
    """Initialize Mods tab menus."""
    if True:  # --Load
        loadMenu = MenuLink(_("Load"))
        loadMenu.links.append(Mods_LoadList())
        ModList.mainMenu.append(loadMenu)
    if True:  # --Sort by
        sortMenu = MenuLink(_("Sort by"))
        sortMenu.links.append(Mods_EsmsFirst())
        sortMenu.links.append(Mods_SelectedFirst())
        sortMenu.links.append(SeparatorLink())
        sortMenu.links.append(Files_SortBy('File'))
        sortMenu.links.append(Files_SortBy('Author'))
        sortMenu.links.append(Files_SortBy('Group'))
        sortMenu.links.append(Files_SortBy('Load Order'))
        if Mw(): sortMenu.links.append(Files_SortBy('Modified'))
        sortMenu.links.append(Files_SortBy('Rating'))
        sortMenu.links.append(Files_SortBy('Size'))
        sortMenu.links.append(Files_SortBy('Status'))
        sortMenu.links.append(Files_SortBy('Version'))
        ModList.mainMenu.append(sortMenu)
    ModList.mainMenu.append(SeparatorLink())
    if Mw():  # --Mlox
        mlox = MenuLink(_("Mlox"))
        mlox.links.append(Mods_Mlox())
        ModList.mainMenu.append(mlox)
    if Mw():  # --tes3cmd
        # Polemos: Extended tes3cmd menu.
        tes3cmd = MenuLink(_("TES3cmd"))
        tes3cmd.links.append(Mods_Tes3cmd_Fixit())
        tes3cmd.links.append(Mods_Tes3cmd_restore())
        tes3cmd.links.append(SeparatorLink())
        tes3cmd.links.append(Mods_Tes3cmd_multipatch())
        ModList.mainMenu.append(tes3cmd)
    if Mw(): ModList.mainMenu.append(SeparatorLink())
    if Mw(): ModList.mainMenu.append(Mods_TESlint_Config())
    if Mw(): ModList.mainMenu.append(Mods_custom_menu())
    if Mw(): ModList.mainMenu.append(SeparatorLink())
    ModList.mainMenu.append(Mods_CopyActive())
    if True:  # Polemos: added "snapshot" menu.
        snapshot_po = MenuLink(_("Snapshots"))
        snapshot_po.links.append(snapshot_po_take())
        snapshot_po.links.append(snapshot_po_restore())
        snapshot_po.links.append(snapshot_po_select())
        snapshot_po.links.append(SeparatorLink())
        snapshot_po.links.append(snapshot_po_import())
        snapshot_po.links.append(snapshot_po_export())
        ModList.mainMenu.append(snapshot_po)
    ModList.mainMenu.append(SeparatorLink())
    if Mw(): ModList.mainMenu.append(Files_Open())
    if Mw(): ModList.mainMenu.append(Files_Unhide('mod'))
    ModList.mainMenu.append(SeparatorLink())
    ModList.mainMenu.append(Check_for_updates())
    ModList.mainMenu.append(SeparatorLink())
    ModList.mainMenu.append(Create_Mashed_Patch())
    if Mw(): ModList.mainMenu.append(Reset_Beth_Dates())
    if Mw():
        ModList.mainMenu.append(Mods_MorrowindIni())
    else:
        ModList.mainMenu.append(Mods_OpenMWcfg())
    ModList.mainMenu.append(Mods_Conf_Bck())
    if Mw(): ModList.mainMenu.append(Mods_IniTweaks())
    if Mw(): ModList.mainMenu.append(Mods_Replacers())
    ModList.mainMenu.append(SeparatorLink())
    ModList.mainMenu.append(Mods_LockTimes())


def InitModLinks_items():  # Polemos: Different initialization for items links.
    """ModList: Item Links"""
    if Mw():  # --File
        fileMenu = MenuLink(_('File'))
        fileMenu.links.append(File_Backup())
        fileMenu.links.append(File_Duplicate())
        fileMenu.links.append(File_Snapshot())
        fileMenu.links.append(SeparatorLink())
        fileMenu.links.append(File_Delete())
        fileMenu.links.append(File_Hide())
        fileMenu.links.append(SeparatorLink())
        fileMenu.links.append(File_Redate())
        fileMenu.links.append(File_Redate_Sys_Time())
        fileMenu.links.append(File_Redate_Sel_Time())
        fileMenu.links.append(File_Sort())
        fileMenu.links.append(SeparatorLink())
        fileMenu.links.append(File_RevertToBackup())
        fileMenu.links.append(File_RevertToSnapshot())
        ModList.itemMenu.append(fileMenu)
    if True:  # --Groups
        groupMenu = MenuLink(_('Group'))
        groupMenu.links.append(Mod_Groups())
        ModList.itemMenu.append(groupMenu)
    if True:  # --Ratings
        ratingMenu = MenuLink(_('Rating'))
        ratingMenu.links.append(Mod_Ratings())
        ModList.itemMenu.append(ratingMenu)
        ModList.itemMenu.append(SeparatorLink())
    if True:  # --Export
        exportMenu = MenuLink(_('Export'))
        exportMenu.links.append(Mod_Export_Dialogue())
        exportMenu.links.append(Mod_Export_Scripts())
        ModList.itemMenu.append(exportMenu)
    if True:  # --Import
        importMenu = MenuLink(_('Import'))
        importMenu.links.append(Mod_Import_Dialogue())
        importMenu.links.append(Mod_Import_LCVSchedules())
        importMenu.links.append(Mod_Import_MergedLists())
        importMenu.links.append(Mod_Import_Scripts())
        importMenu.links.append(SeparatorLink())
        importMenu.links.append(File_Replace_Refs())
        ModList.itemMenu.append(importMenu)
        ModList.itemMenu.append(GetLinearList())
        ModList.itemMenu.append(SeparatorLink())
    if Mw():
        ModList.itemMenu.append(Mod_Tes3cmd_Clean())
        ModList.itemMenu.append(Mod_Tes3cmd_Sync())
        ModList.itemMenu.append(Mod_TES3lint())
        ModList.itemMenu.append(Mod_Tes3cmd_Merge())
        custom_menu = MenuLink(_('Custom Commands'))
        custom_menu.links.append(Mods_custom_menu_item())
        ModList.itemMenu.append(custom_menu)
    ModList.itemMenu.append(SeparatorLink())
    ModList.itemMenu.append(Mod_ShowReadme())
    ModList.itemMenu.append(Mod_CopyToEsmp())
    ModList.itemMenu.append(Mod_RenumberRefs())
    ModList.itemMenu.append(File_RepairRefs())
    ModList.itemMenu.append(File_SortRecords())
    ModList.itemMenu.append(File_Stats())
    ModList.itemMenu.append(Mod_Updaters())


def InitSaveLinks():  # Polemos: More personality for the Saves tab.
    """Initialize save tab menus."""
    if True:  # --Sort
        sortMenu = MenuLink(_("Sort by"))
        sortMenu.links.append(Files_SortBy('File'))
        sortMenu.links.append(Files_SortBy('Cell'))
        sortMenu.links.append(Files_SortBy('Modified'))
        sortMenu.links.append(Files_SortBy('Player'))
        sortMenu.links.append(Files_SortBy('Save Name'))
        sortMenu.links.append(Files_SortBy('Size'))
        SaveList.mainMenu.append(sortMenu)
    if Mw():  # --Save Subdirs
        subDirMenu = MenuLink(_("Profile"))
        subDirMenu.links.append(Saves_Profiles())
        SaveList.mainMenu.append(subDirMenu)
    SaveList.mainMenu.append(SeparatorLink())
    SaveList.mainMenu.append(Files_Open_saves_po())  # Polemos: give file_open it's own text...
    if Mw(): SaveList.mainMenu.append(Files_Unhide('save'))
    if Mw(): SaveList.mainMenu.append(Saves_MapGridLines())


def InitSaveLinks_items():  # Polemos: Different initialization for items links.
    """SaveList: Item Links"""
    if True:  # --File
        fileMenu = MenuLink(_("File"))  # >>
        fileMenu.links.append(File_Backup())
        fileMenu.links.append(Save_Duplicate())
        fileMenu.links.append(File_Snapshot())
        fileMenu.links.append(SeparatorLink())
        fileMenu.links.append(File_Delete())
        fileMenu.links.append(File_MoveTo())
        fileMenu.links.append(SeparatorLink())
        fileMenu.links.append(File_RevertToBackup())
        fileMenu.links.append(File_RevertToSnapshot())
        SaveList.itemMenu.append(fileMenu)
    SaveList.itemMenu.append(SeparatorLink())
    if Mw():
        removeMenu = MenuLink(_("Remove"))
        removeMenu.links.append(Save_Remove_DebrisCells())
        removeMenu.links.append(Save_Remove_SpawnedCreatures())
        removeMenu.links.append(SeparatorLink())
        removeMenu.links.append(File_Remove_Refs())
        SaveList.itemMenu.append(removeMenu)
        SaveList.itemMenu.append(SeparatorLink())
        SaveList.itemMenu.append(Save_ShowJournal())
        SaveList.itemMenu.append(Save_LoadMasters())
        SaveList.itemMenu.append(Save_MapNotes())
        SaveList.itemMenu.append(Save_RepairAll())
        # SaveList.itemMenu.append(Save_Review()) #--Not that useful.  <====> Polemos: Code exists and is working, should we insert it?
        SaveList.itemMenu.append(File_Stats())
        SaveList.itemMenu.append(Save_UpdateWorldMap())


def InitScreenLinks():  # Polemos: More personality for screens tab.
    """Initialize screens tab menus."""
    ScreensList.mainMenu.append(Files_Open_screens_po())
    if Mw():
        ScreensList.mainMenu.append(SeparatorLink())
        ScreensList.mainMenu.append(Config_ScreenShots())
    # ScreensList.mainMenu.append(move_screens_po())  => Polemos TODO: Not implemented yet (move from images MWdir to the new Screens dir).


def InitScreenLinks_items():  # Polemos: Different initialization for items links.
    """ScreensList: Item Links"""
    ScreensList.itemMenu.append(File_Open())
    ScreensList.itemMenu.append(Screen_Rename())
    ScreensList.itemMenu.append(Screen_Delete())
    ScreensList.itemMenu.append(SeparatorLink())
    ScreensList.itemMenu.append(Screen_ConvertToJpg())


def InitLinks():  # Polemos: Modified for extra menu functioning. For "Column Menu".
    """Call other link initializers."""
    InitStatusBar()
    InitMasterLinks()
    InitMasterLinks_items()
    InitArchivesLinks()
    InitArchivesLinks_items()
    if Mw():
        InitInstallerLinks()
        InitInstallerLinks_items()
    else:
        InitModDataLinks()
        InitModDataLinks_items()
        InitPackageLinks()
        InitPackageLinks_items()
    InitModLinks()
    InitModLinks_items()
    InitSaveLinks()
    InitSaveLinks_items()
    InitScreenLinks()
    InitScreenLinks_items()
    InitUtilsLinks()
    InitUtilsLinks_items()


def InitLinks_no_col_menu():  # Polemos: For "Menubar".
    """Call other link initializers."""
    InitStatusBar()
    InitMasterLinks()  # Polemos: needed for master menu button
    InitMasterLinks_items()
    InitArchivesLinks_items()
    if Mw():
        InitInstallerLinks_items()
    else:
        InitModDataLinks_items()
        InitPackageLinks_items()
    InitModLinks_items()
    InitSaveLinks_items()
    InitScreenLinks_items()
    InitUtilsLinks_items()


# Main ------------------------------------------------------------------------ #
if __name__ == '__main__':
    print('Compiled')
