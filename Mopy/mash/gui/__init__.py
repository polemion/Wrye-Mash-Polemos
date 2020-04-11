# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
#
# Wrye Mash, Polemos fork Copyright (C) 2017-2019 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher
#
#  Copyright on the original code 2005-2009 Wrye
#  Copyright on any non trivial modifications or substantial additions 2009-2011 Melchor
#  Copyright on any non trivial modifications or substantial additions 2011-2016 Yacoby
#  Copyright on any non trivial modifications or substantial additions 2017-2019 Polemos
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


import cPickle  # Polemos: Used to be pickle, changed obviously.
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from .. import singletons
from ..merrors import InterfaceError as InterfaceError
from .. import balt
from .. import mosh
from ..unimash import _   # Polemos
from .. import conf  # Polemos
import interface  # Polemos


# Constants
wxListAligns = [wx.LIST_FORMAT_LEFT, wx.LIST_FORMAT_RIGHT, wx.LIST_FORMAT_CENTRE]


class ListDragDropMixin:
    """
    This allows the simple dragging and dropping in lists, although this doesn't
    allow dragging between lists

    Due to the design of other parts of the program this doesn't actually
    move the item in the list and leaves it up to the implementation of
    OnDrop to do that work
    """
    def __init__(self, listCtrl):
        listCtrl.Bind(wx.EVT_LIST_BEGIN_DRAG, self._DoStartDrag)
        self.listCtrl = listCtrl

        dt = ListDrop(listCtrl.GetId(), self._DdInsert)
        self.listCtrl.SetDropTarget(dt)

    def OnDrop(self, names, startIndex):
        """
        The event for an item being dropped, should be overridden
        names - The names of the item (its text)
        startIndex - The index that the items should be inserted
        """
        pass

    def _DoStartDrag(self, e):
        selected = []
        idx = -1
        while True:  # find all the selected items and put them in a list
            idx = self.listCtrl.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1: break
            selected.append(self.listCtrl.GetItemText(idx))
        data = wx.CustomDataObject('ListItems%d' % self.listCtrl.GetId())
        data.SetData(cPickle.dumps(selected))  #  Polemos: Used to be pickle
        ds = wx.DropSource(self.listCtrl)
        ds.SetData(data)
        ds.DoDragDrop(True)

    def _DdInsert(self, x, y, selected):
        """Insert text at given x, y coordinates --- used with drag-and-drop."""
        # Find insertion point.
        toIdx, flags = self.listCtrl.HitTest((x, y))
        if toIdx == wx.NOT_FOUND:
            if flags & wx.LIST_HITTEST_NOWHERE: toIdx = self.listCtrl.GetItemCount()
            else: return
        # Get bounding rect for the item being dropped onto and if the user is
        # dropping into the lower half of the rect, we want to insert _after_ this item.
        try:  # Polemos fix
            rect = self.listCtrl.GetItemRect(toIdx)
            if y > rect.y + rect.height/2: toIdx += 1
        except: pass
        self.OnDrop(selected, toIdx)
        #ensure the moved items are selected
        for itemDex in xrange(self.listCtrl.GetItemCount()):
            self.listCtrl.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)
        idx = -1
        while True:
            idx = self.listCtrl.GetNextItem(idx, wx.LIST_NEXT_ALL)
            if idx == -1: break
            elif self.listCtrl.GetItemText(idx) in selected:
                self.listCtrl.Select(idx)


class ListDrop(wx.PyDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, dataId, setFn):
        """
        dataId - The id of the list, this ensures that we can't dragdrop between lists
        setFn - Function to call on drop.
        """
        wx.PyDropTarget.__init__(self)
        self.setFn = setFn
        # specify the type of data we will accept
        self.data = wx.CustomDataObject('ListItems%d' % dataId)
        self.SetDataObject(self.data)

    def OnData(self, x, y, d):
        """Called when OnDrop returns True.  We need to get the data and do something with it."""
        # copy the data from the drag source to our data object
        if self.GetData():
            selected = cPickle.loads(self.data.GetData())  # Polemos: Used to be pickle
            self.setFn(x, y, selected)
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d


class ListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style=style)
        ListCtrlAutoWidthMixin.__init__(self)


class List(wx.Panel):  # Polemos: Additions.
    """The listctrl control of all Mash lists (but the installers)."""
    prev_item = None

    def __init__(self,parent,id=-1,ctrlStyle=(wx.LC_REPORT|wx.LC_SINGLE_SEL)):
        """Init."""
        wx.Panel.__init__(self,parent,id, style=wx.WANTS_CHARS)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetSizeHints(-1,50)
        #--ListCtrl
        listId = self.listId = wx.NewId()
        self.list = ListCtrl(self, listId, style=ctrlStyle)
        self.checkboxes = singletons.images['mash.checkboxes']
        #--Columns
        self.PopulateColumns()
        #--Items
        self.sortDirty = 0
        self.PopulateItems()
        self.hitIcon = 0
        self.mouseItem = None
        #--Events
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LEFT_DOWN(self.list,self.OnLeftDown)
        wx.EVT_COMMAND_RIGHT_CLICK(self.list, listId, self.DoItemMenu)
        wx.EVT_LIST_COL_CLICK(self, listId, self.DoItemSort)
        wx.EVT_LIST_COL_RIGHT_CLICK(self, listId, self.DoColumnMenu)
        wx.EVT_LIST_COL_END_DRAG(self, listId, self.OnColumnResize)
        wx.EVT_MOTION(self.list, self.OnMouse)
        wx.EVT_LEAVE_WINDOW(self.list, self.OnMouse)
        # Theming
        if interface.style['lists.font.color'] is not None:
            [self.list.SetItemTextColour(x, interface.style['lists.font.color']) for x in xrange(self.list.GetItemCount())]
            self.fontDefaultColor = interface.style['lists.font.color']
        else: self.fontDefaultColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)

    def OnMouse(self, event):  # Polemos
        """Mouse hover/leaving actions."""
        if conf.settings['interface.lists.color']:
            if event.Moving():
                (mouseItem, HitFlag) = self.list.HitTest(event.GetPosition())
                if mouseItem != self.mouseItem and mouseItem != -1:
                    self.mouseItem = mouseItem
                    itemColor = self.list.GetItemTextColour(mouseItem) if self.list.GetItemTextColour(
                        mouseItem) != wx.NullColour else self.fontDefaultColor
                    self.lastItemColor = (mouseItem, itemColor)
                    self.MouseEffect(mouseItem)
            elif event.Leaving() and self.mouseItem is not None and self.mouseItem != -1:
                try: self.list.SetItemTextColour(self.lastItemColor[0], self.lastItemColor[1])
                except: pass
        event.Skip()

    def MouseEffect(self, item):  # Polemos: Added a small effect.
        """Handle mouse over item by showing tip or similar."""
        try:
            self.list.SetItemTextColour(item, interface.style['mouse.hover'])
            self.list.SetItemTextColour(self.prev_item[0], self.prev_item[1])
        except: pass
        try: self.prev_item = self.lastItemColor
        except: pass  # Happens

    def PopulateColumns(self):  # Polemos: added list alignments per col name.
        """Create/name columns in ListCtrl."""
        right_align_po = ['Size']
        center_align_po = ['Version', 'flags', '#']
        cols = self.cols
        self.numCols = len(cols)
        for colDex in xrange(self.numCols):
            colKey = cols[colDex]
            colName = self.colNames.get(colKey,colKey)
            wxListAlign = wxListAligns[self.colAligns.get(colKey,0)]
            if colName in right_align_po : wxListAlign = wx.LIST_FORMAT_RIGHT
            if colName in center_align_po: wxListAlign = wx.LIST_FORMAT_CENTER
            self.list.InsertColumn(colDex,colName,wxListAlign)
            self.list.SetColumnWidth(colDex, self.colWidths.get(colKey,30))
        if conf.settings['mash.large.fonts']:  # Polemos: Big fonts for tired eyes
            self.list.SetFont(wx.Font(*interface.internalStyle['big.font']))
        if interface.style['lists.font.color'] is not None:  # Polemos: Theme engine
            self.list.SetTextColour(interface.style['lists.font.color'])

    def PopulateItem(self,itemDex,mode=0,selected=set()):
        """Populate ListCtrl for specified item. [ABSTRACT]"""
        raise mosh.AbstractError

    def GetItems(self):
        """Set and return self.items."""
        self.items = self.data.keys()
        return self.items

    def PopulateItems(self,col=None,reverse=-2,selected='SAME'):
        """Sort items and populate entire list."""
        #--Sort Dirty?
        if self.sortDirty:
            self.sortDirty = 0
            (col, reverse) = (None,-1)
        #--Items to select afterwards. (Defaults to current selection.)
        if selected == 'SAME': selected = set(self.GetSelected())
        #--Reget items
        self.GetItems()
        self.SortItems(col,reverse)
        #--Delete Current items
        listItemCount = self.list.GetItemCount()
        #--Populate items
        for itemDex in xrange(len(self.items)):
            mode = int(itemDex >= listItemCount)
            self.PopulateItem(itemDex,mode,selected)
        #--Delete items?
        while self.list.GetItemCount() > len(self.items):
            self.list.DeleteItem(self.list.GetItemCount()-1)

    def ClearSelected(self):
        for itemDex in xrange(self.list.GetItemCount()):
            self.list.SetItemState(itemDex, 0, wx.LIST_STATE_SELECTED)

    def GetSelected(self):
        """Return list of items selected (highlighted) in the interface."""
        #--No items?
        if not 'items' in self.__dict__: return []
        selected = []
        itemDex = -1
        while True:
            itemDex = self.list.GetNextItem(itemDex, wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
            if itemDex == -1: break
            else: selected.append(self.items[itemDex])
        return selected

    def SelectItems(self, items):
        itemDex = -1
        while True:
            itemDex = self.list.GetNextItem(itemDex, wx.LIST_NEXT_ALL)
            if itemDex == -1: break
            elif self.items[itemDex] in items: self.list.Select(itemDex)

    def SelectAll(self):
        itemDex = -1
        while True:
            itemDex = self.list.GetNextItem(itemDex, wx.LIST_NEXT_ALL)
            if itemDex == -1: break
            else: self.list.Select(itemDex)

    def SetItemFocus(self, item):  # Polemos
        """Focus on selected item in the list (for AlphaNumeric KeyPresses)."""
        itemDex = -1
        while True:
            itemDex = self.list.GetNextItem(itemDex, wx.LIST_NEXT_ALL)
            if itemDex == -1: break
            elif self.items[itemDex] == item: self.list.Focus(itemDex)

    def DeleteSelected(self):  #$# from FallenWizard
        """Deletes selected items."""
        items = self.GetSelected()
        if items:
            message = _(u'Delete these items? This operation cannot be undone.')
            message += '\n* ' + '\n* '.join(x for x in sorted(items))
            if balt.askYes(self,message,_(u'Delete Items')):
                for item in items: self.data.delete(item)
            singletons.modList.Refresh() #$#

    def GetSortSettings(self,col,reverse):
        """Return parsed col, reverse arguments. Used by SortSettings.
        col: sort variable.
        Defaults to last sort. (self.sort)
        reverse: sort order
        1: Descending order
        0: Ascending order
        -1: Use current reverse settings for sort variable, unless
            last sort was on same sort variable -- in which case,
            reverse the sort order.
        -2: Use current reverse setting for sort variable.
        """
        #--Sort Column
        if not col: col = self.sort
        #--Reverse
        oldReverse = self.colReverse.get(col,0)
        if col == 'Load Order': #--Disallow reverse for Load Order
            reverse = 0
        elif reverse == -1 and col == self.sort:
            reverse = not oldReverse
        elif reverse < 0: reverse = oldReverse
        #--Done
        self.sort = col
        self.colReverse[col] = reverse
        return (col,reverse)

    def DoColumnMenu(self,event):  # Polemos: added Master Menu button pos
        """Column Menu"""
        if not self.mainMenu: return
        #--Build Menu
        try: column = event.GetColumn()
        except: column = event
        menu = wx.Menu()
        for link in self.mainMenu:
            link.AppendToMenu(menu,self,column)
        #--Show/Destroy Menu
        self.PopupMenu(menu)
        menu.Destroy()

    def OnColumnResize(self,event):
        """Column Resize"""
        pass

    def DoItemSort(self, event):
        """Item Sort"""
        self.PopulateItems(self.cols[event.GetColumn()],-1)

    def DoItemMenu(self,event):
        """Item Menu"""
        selected = self.GetSelected()
        if not selected: return
        #--Build Menu
        menu = wx.Menu()
        for link in self.itemMenu:
            link.AppendToMenu(menu,self,selected)
        #--Show/Destroy Menu
        self.PopupMenu(menu)
        menu.Destroy()

    def OnSize(self, event):
        """Size Change"""
        size = self.GetClientSizeTuple()
        self.list.SetSize(size)

    def OnLeftDown(self,event):
        """Event: Left Down"""
        event.Skip()


class NotebookPanel(wx.Panel):
    """Parent class for notebook panels."""

    def SetStatusCount(self):
        """Sets status bar count field."""
        singletons.statusBar.SetStatusField('', 2)

    def OnShow(self):
        """To be called when particular panel is changed to and/or shown for first time.
        Default version does nothing, but derived versions might update data."""
        self.SetStatusCount()

    def OnCloseWindow(self):
        """To be called when containing frame is closing. Use for saving data, scrollpos, etc."""
        pass
