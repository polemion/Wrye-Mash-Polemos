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


import os
import wx
from .. import singletons
from .. import conf
from .. import mosh
from ..balt import Links, leftSash, hSizer, vSizer
from ..unimash import _
from .. import gui
from . import dialog
from subprocess import PIPE
from ..sfix import Popen  # Polemos fix
import ushlex  # Polemos addon


class FakeColumnEvent:
    """The cake..."""

    def __init__(self, numCols):
        """is a..."""
        self.column = numCols

    def GetColumn(self):
        """lie..."""
        return self.column


class UtilsPanel(gui.NotebookPanel):  # Polemos: changes and fixes.
    """Utilities tab."""

    def __init__(self,parent):
        """Initialize."""
        wx.Panel.__init__(self, parent, -1)
        #--Left
        sashPos = conf.settings.get('mash.utils.sashPos',120)
        left = self.left = leftSash(self,defaultSize=(sashPos,100),onSashDrag=self.OnSashDrag)
        right = self.right = wx.Panel(self,style=wx.NO_BORDER)
        #--Contents
        singletons.utilsList = UtilsList(left)
        singletons.utilsList.SetSizeHints(100, 100)
        #--Layout
        left.SetSizer(hSizer((singletons.utilsList, 1, wx.GROW), ((10, 0), 0)))
        self.gCommandLine = wx.TextCtrl(right,-1,style=wx.TE_READONLY)
        self.gArguments = wx.TextCtrl(right,-1,style=wx.TE_READONLY)
        self.gDescription = wx.TextCtrl(right,-1,style=wx.TE_MULTILINE|wx.TE_READONLY)
        singletons.utilsList.commandLine = self.gCommandLine
        singletons.utilsList.arguments = self.gArguments
        singletons.utilsList.description = self.gDescription
        right.SetSizer(vSizer((self.gCommandLine,0,wx.GROW), (self.gArguments,0,wx.GROW), (self.gDescription,1,wx.GROW)))
        wx.LayoutAlgorithm().LayoutWindow(self, right)
        # --Events
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def SetStatusCount(self):  # Polemos: fix
        """Sets status bar count field."""
        text = _(u'Utilities: %d') % (len(singletons.utilsList.data.data),)
        singletons.statusBar.SetStatusField(text, 2)

    def OnSashDrag(self,event):
        """Handle sash moved."""
        wMin,wMax = 80,self.GetSizeTuple()[0]-80
        sashPos = max(wMin,min(wMax,event.GetDragRect().width))
        self.left.SetDefaultSize((sashPos,10))
        wx.LayoutAlgorithm().LayoutWindow(self, self.right)
        conf.settings['mash.utils.sashPos'] = sashPos

    def OnSize(self, event=None):
        wx.LayoutAlgorithm().LayoutWindow(self, self.right)

    def OnShow(self):
        """Panel is shown. Update self.data."""
        if mosh.UtilsData.refresh(): singletons.utilsList.RefreshUI()  # This is selfless, don't self it.
        self.SetStatusCount()


class UtilsList(gui.List):  # Polemos: Changes and optimizations.
    """Class Data"""
    mainMenu = Links() #--Column menu
    itemMenu = Links() #--Single item menu

    def __init__(self, parent):
        #--Columns
        self.cols = conf.settings['mash.utils.cols']
        self.colAligns = conf.settings['mash.utils.colAligns']
        self.colNames = conf.settings['mash.colNames']
        self.colReverse = conf.settings.getChanged('mash.utils.colReverse')
        self.colWidths = conf.settings['mash.utils.colWidths']
        #--Data/Items
        self.data = mosh.UtilsData = mosh.UtilsData()
        self.sort = conf.settings['mash.utils.sort']
        #--Links
        self.mainMenu = UtilsList.mainMenu
        self.itemMenu = UtilsList.itemMenu
        #--Parent init
        gui.List.__init__(self,parent,-1,ctrlStyle=(wx.LC_REPORT|wx.SUNKEN_BORDER))
        #--Events
        wx.EVT_LIST_ITEM_SELECTED(self,self.listId,self.OnItemSelected)
        wx.EVT_LIST_ITEM_ACTIVATED(self,self.listId,self.OnItemActivated)

    def RefreshUI(self,files='ALL',detail='SAME'):
        """Refreshes UI for specified files."""
        #--Details
        if detail == 'SAME':
            selected = set(self.GetSelected())
        else: selected = {detail}
        #--Populate
        if files == 'ALL':
            self.PopulateItems(selected=selected)
        elif isinstance(files, basestring):  # Polemos fix
            self.PopulateItem(files,selected=selected)
        else: #--Iterable
            for file in files: self.PopulateItem(file,selected=selected)
        singletons.mashFrame.SetStatusCount()

    def PopulateItem(self,itemDex,mode=0,selected=set()):  # Polemos: Donkey patching.
        """Populate Item"""
        if not type(itemDex) is int: itemDex = self.items.index(itemDex)
        item = self.items[itemDex].strip()
        fileInfo = self.data[item]
        show_fileName = os.path.splitext((os.path.basename(fileInfo[0])))[0]
        cols = self.cols
        for colDex in xrange(self.numCols):
            col = cols[colDex]
            if col == 'File':
                value = show_fileName
            elif col == 'ID':
                value = item
            elif col == 'Flag':   # Polemos: Not enabled, todo: remove?
                value = ''
            else: value = ''
            if mode and (colDex == 0):
                try: self.list.InsertStringItem(itemDex, value)
                except: self.list.InsertStringItem(itemDex, value.decode('utf-8', errors='ignore'))
            else:
                try: self.list.SetStringItem(itemDex, colDex, value)
                except:
                    try:self.list.SetStringItem(itemDex, colDex, value.decode('utf-8'))
                    except:
                        try: self.list.SetStringItem(itemDex, colDex, str(value))
                        except: self.list.SetStringItem(itemDex, colDex, value.encode('utf-8'))
        #--Selection State
        if item in selected:
            self.list.SetItemState(itemDex,wx.LIST_STATE_SELECTED,wx.LIST_STATE_SELECTED)
        else: self.list.SetItemState(itemDex,0,wx.LIST_STATE_SELECTED)

    def SortItems(self,col=None,reverse=-2):  # Polemos: new ID and flag implementation.
        """Sort Items"""
        (col, reverse) = self.GetSortSettings(col,reverse)
        conf.settings['mash.utils.sort'] = col
        data = self.data
        #--Start with sort by name
        self.items.sort()
        if col == 'File': pass #--Done by default
        elif col == 'ID': pass
        elif col == 'Flag':   # Polemos: Not enabled, todo: remove?
            pass
        else: raise mosh.SortKeyError(_(u'Unrecognized sort key: %s' % col))  # Polemos: fix
        #--Ascending
        if reverse: self.items.reverse()

    def OnColumnResize(self,event):
        """Column Resize"""
        colDex = event.GetColumn()
        colName = self.cols[colDex]
        self.colWidths[colName] = self.list.GetColumnWidth(colDex)
        conf.settings.setChanged('mash.utils.colWidths')

    def OnItemSelected(self,event=None):  # Polemos: This is Unicode kebab, not sandwich.
        """..."""
        ID = event.GetText()
        if str(ID) in str(self.data.keys()):
            self.commandLine.SetValue(self.data[ID][0])
            self.arguments.SetValue(self.data[ID][1])
            desc = self.data[ID][2]
            if (desc.startswith('"') and desc.endswith('"')) or (desc.startswith("'") and desc.endswith("'")):
                self.description.SetValue(eval(desc))
            else: self.description.SetValue(desc)

    def OnItemActivated(self, event=None):  # Polemos: Many changes here. Well, unicode and thingathingies.
        """Launching the utility."""
        ID = event.GetText()
        if str(ID) in str(self.data.keys()):
            u = self.data[ID][0]
            cwd_po = os.path.dirname(u)
            args_tmp_po = ushlex.split(self.data[ID][1])
            try:
                args_po = ''
                for x in args_tmp_po: args_po = '%s %s' % (args_po, x)
                if args_po != '': args_po = ' "%s"' % (args_po)
            except: args_po = ''

            try:
                # Polemos: todo: temporarily removed - reinstate at some point
                '''if u.lower() == "mish":
                    import mish
                    argsList = self.data[ID][1].split()
                    sys_argv_org = sys.argv
                    mish.sys.argv = ["mish"] + argsList
                    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nMISH output.\n\nArguments: %s\n" % self.arguments.Value
                    mish.callables.main()
                    sys.argv = sys_argv_org
                    #
                    return # <-- bad hack ?'''

                try:
                    command = 'start "Launching..." /D "%s" "%s"%s' % (
                    cwd_po.decode('utf-8'), u.decode('utf-8'), args_po.decode('utf-8'))
                    Popen(command, shell=True, stdin=PIPE, stdout=PIPE)

                except:
                    command = ('start "Launching..." /D "%s" "%s"%s' % (
                    cwd_po.encode('utf-8').decode('utf-8'), u.encode('utf-8').decode('utf-8'),
                    args_po.encode('utf-8').decode('utf-8')))
                    Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
            except: gui.dialog.WarningMessage(self, _(u"A problem "
                        u"has occurred while opening '%s'.\nYou should edit 'utils.dcg' and update the corresponding line." % u))

    def NewItem(self):
        """Adds a new utility to the list."""
        dialog = gui.dialog.UtilsDialog(self, new=True)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        result = dialog.result
        if result:
            if result[0] not in ("", None) and result[1] not in ("", None):
                self.data[result[0]] = result[1:]
                self.data.save()
                self.DoItemSort(FakeColumnEvent(0))
                self.RefreshUI()

    def ModifyItem(self): # Polemos: Unicode edits.
        """Modification of an item. This function modifies an item or does nothing."""
        names = self.GetSelected()
        item = self.list.GetFirstSelected()
        idx = 0
        while idx < len(names):
            name = names[idx]
            try: dialog = gui.dialog.UtilsDialog(self, new=False, data=((name,) + self.data[name]))
            except: dialog = gui.dialog.UtilsDialog(self, new=False, data=((name.decode('utf-8'),) + self.data[name]))
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                return
            result = dialog.result
            if result:
                if result[0] not in ("", None) and result[1] not in ("", None):
                    if result[0] != name:
                        self.data[result[0]] = result[1:]
                        for name in names:
                            self.list.DeleteItem(self.list.GetFirstSelected())
                            self.data.pop(name)
                        self.data.save()
                        self.commandLine.SetValue("")
                        self.arguments.SetValue("")
                        self.description.SetValue("")
                        self.DoItemSort(FakeColumnEvent(0))
                        self.RefreshUI()
                    self.data[result[0]] = result[1:]
                    self.data.save()
            idx += 1
            item = self.list.GetNextSelected(item)
        self.DoItemSort(FakeColumnEvent(0))
        self.RefreshUI()

    def DeleteItem(self):
        """Deletes an item. This function deletes the selected item or does nothing."""
        names = self.GetSelected()
        for name in names:
            self.list.DeleteItem(self.list.GetFirstSelected())
            self.data.pop(name)
        self.data.save()
        self.commandLine.SetValue("")
        self.arguments.SetValue("")
        self.description.SetValue("")
        self.DoItemSort(FakeColumnEvent(0))
        self.RefreshUI()
