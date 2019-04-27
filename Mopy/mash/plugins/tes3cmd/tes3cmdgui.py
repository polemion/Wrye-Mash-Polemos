# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
#
# Wrye Mash 2018 Polemos fork Copyright (C) 2017-2019 Polemos
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


# Polemos: I guess the original was made by Yakoby?
# Polemos: Refactored, optimised, unicode/cosmetic/regular fixes.


import wx
from mash.mosh import _


dPos = wx.DefaultPosition
dSize = wx.DefaultSize


class cleanop(wx.Dialog):  # Polemos: This is not implemented.

    def __init__( self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u"tes3cmd Clean"), pos=dPos, size=wx.Size(429,217), style=style)

        self.SetSizeHintsSz(dSize, dSize)

        if True: # Content
            self.clean_box0 = wx.CheckBox(self, wx.ID_ANY, _(u"clean cell subrecords AMBI,WHGT duped from masters"), dPos, dSize, 0)
            self.clean_box1 = wx.CheckBox(self, wx.ID_ANY, _(u"clean other complete records duped from masters"), dPos, dSize, 0)
            self.clean_box2 = wx.CheckBox(self, wx.ID_ANY, _(u"clean Evil GMSTs"), dPos, dSize, 0)
            self.clean_box3 = wx.CheckBox(self, wx.ID_ANY, _(u"clean object instances from cells when duped from masters"), dPos, dSize, 0)
            self.clean_box4 = wx.CheckBox(self, wx.ID_ANY, _(u"clean junk cells (no new info from definition in masters)"), dPos, dSize, 0)

            self.cancel_btn = wx.Button(self, wx.ID_ANY, _(u"Cancel"), dPos, dSize, 0)
            self.clean_selected_btn = wx.Button(self, wx.ID_ANY, _(u"Clean Selected"), dPos, dSize, 0)

            [x.SetValue(True) for x in (self.clean_box0, self.clean_box1, self.clean_box2, self.clean_box3, self.clean_box4)]

        if True:  # Sizers
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.AddMany([(self.cancel_btn,0,wx.ALL,5),(self.clean_selected_btn,0,wx.ALL,5)])
            main_sizer.SetMinSize(wx.Size(400, -1))
            main_sizer.AddMany([(self.clean_box0,0,wx.ALL,5),(self.clean_box1,0,wx.ALL,5),(self.clean_box2,0,wx.ALL,5),
                                (self.clean_box3,0,wx.ALL,5),(self.clean_box4,0,wx.ALL,5),(button_sizer, 1, wx.EXPAND, 5)])
            self.SetSizer(main_sizer)

        self.Layout()
        self.Centre(wx.BOTH)

        if True:  # Events
            self.cancel_btn.Bind(wx.EVT_BUTTON, self.OnCancel)
            self.clean_selected_btn.Bind(wx.EVT_BUTTON, self.OnCleanClick)

    def OnCancel(self, event): event.Skip()
    def OnCleanClick(self, event): event.Skip()


class cleaner(wx.Frame):  # Polemos
    def __init__(self, parent, style=wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=_(u"tes3cmd Cleaner"), pos=dPos, size=wx.Size(530, 350), style=style)

        mCleanedModsChoices = []
        self.SetSizeHintsSz(dSize, dSize)

        if True: # Content
            self.main_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, 0)
            self.details_book = wx.Notebook(self.main_panel, wx.ID_ANY, dPos, dSize, 0)
            # Buttons
            self.mSkip = wx.Button(self.main_panel, wx.ID_ANY, _(u"Skip"), dPos, (70, 26), 0)
            self.mStop = wx.Button(self.main_panel, wx.ID_ANY, _(u"Stop"), dPos, (70, 26), 0)
            self.save_log_btn = wx.Button(self.main_panel, wx.ID_ANY, _(u"Save Log"), dPos, dSize, 0)
            # Progress
            self.mProgress = wx.Gauge(self.main_panel, wx.ID_ANY, 100, dPos, dSize, wx.GA_HORIZONTAL|wx.GA_SMOOTH)
            # Mod list/actions
            self.mCleanedMods = wx.ListBox(self.main_panel, wx.ID_ANY, dPos, dSize, mCleanedModsChoices, 0)
            self.clean_mod_info_text = wx.StaticText(self.main_panel, wx.ID_ANY, _(u"Cleaning..."), dPos, dSize, 0)
            self.mStats = wx.StaticText(self.main_panel, wx.ID_ANY, u'', dPos, dSize, 0)
            # Output
            self.output_panel = wx.Panel(self.details_book, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.details_book.AddPage(self.output_panel, _(u"Output"), True)
            self.mLog = wx.TextCtrl(self.output_panel, wx.ID_ANY, u'', dPos, dSize, wx.TE_MULTILINE|wx.TE_READONLY)
            # Errors
            self.errors_panel = wx.Panel(self.details_book, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.details_book.AddPage(self.errors_panel, _(u"Errors"), False)
            self.mErrors = wx.TextCtrl(self.errors_panel, wx.ID_ANY, u'', dPos, dSize, wx.TE_MULTILINE|wx.TE_READONLY)

        if True:  # Layout
            self.mCleanedMods.SetMinSize(wx.Size(150, -1))
            self.clean_mod_info_text.Wrap(-1)
            self.mStats.Wrap(-1)
            self.mStats.SetMinSize(wx.Size(-1, 80))
            # Output
            output_panel_sizer = wx.FlexGridSizer(1, 1, 0, 0)
            output_panel_sizer.AddGrowableCol(0)
            output_panel_sizer.AddGrowableRow(0)
            output_panel_sizer.SetFlexibleDirection(wx.BOTH)
            output_panel_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
            output_panel_sizer.Add(self.mLog, 0, wx.ALL|wx.EXPAND, 5)
            self.output_panel.SetSizer(output_panel_sizer)
            self.output_panel.Layout()
            output_panel_sizer.Fit(self.output_panel)
            # Errors
            errors_panel_sizer = wx.FlexGridSizer(1, 1, 0, 0)
            errors_panel_sizer.AddGrowableCol(0)
            errors_panel_sizer.AddGrowableRow(0)
            errors_panel_sizer.SetFlexibleDirection(wx.BOTH)
            errors_panel_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
            errors_panel_sizer.Add(self.mErrors, 0, wx.ALL|wx.EXPAND, 5)
            self.errors_panel.SetSizer(errors_panel_sizer)
            self.errors_panel.Layout()
            errors_panel_sizer.Fit(self.errors_panel)
            # Info
            info_sizer = wx.FlexGridSizer(3, 1, 0, 0)
            info_sizer.AddGrowableCol(0)
            info_sizer.AddGrowableRow(2)
            info_sizer.SetFlexibleDirection(wx.BOTH)
            info_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
            info_sizer.AddMany([(self.clean_mod_info_text,0,wx.ALL,5),(self.mStats,0,wx.ALL,5),(self.details_book,1,wx.EXPAND|wx.ALL,5)])
            # Details
            details_main_sizer = wx.BoxSizer(wx.HORIZONTAL)
            details_main_sizer.AddMany([(self.mCleanedMods,0,wx.ALL|wx.EXPAND,5),(info_sizer,1,wx.EXPAND,5)])
            # Buttons
            button_Sizer0 = wx.BoxSizer(wx.HORIZONTAL)
            button_Sizer0.AddMany([(self.mSkip,0,wx.ALL,5),(self.mStop,0,wx.ALL,5),(self.mProgress,1,wx.ALIGN_CENTER_VERTICAL|wx.ALL,5)])
            button_sizer1 = wx.BoxSizer(wx.VERTICAL)
            button_sizer1.Add(self.save_log_btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
            # SubMain
            sub_main_sizer = wx.FlexGridSizer(3, 1, 0, 0)
            sub_main_sizer.AddGrowableCol(0)
            sub_main_sizer.AddGrowableRow(1)
            sub_main_sizer.SetFlexibleDirection(wx.BOTH)
            sub_main_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
            sub_main_sizer.AddMany([(button_Sizer0,1,wx.EXPAND,5),(details_main_sizer,1,wx.EXPAND,5),(button_sizer1,1,wx.EXPAND,5)])
            # Main
            self.main_panel.SetSizer(sub_main_sizer)
            self.main_panel.Layout()
            sub_main_sizer.Fit(self.main_panel)
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(self.main_panel, 1, wx.EXPAND|wx.ALL, 0)
            self.SetSizer(main_sizer)
            self.Layout()
            self.Centre(wx.BOTH)

        if True:  # Events
            self.mSkip.Bind(wx.EVT_BUTTON, self.OnSkip)
            self.mStop.Bind(wx.EVT_BUTTON, self.OnStop)
            self.mCleanedMods.Bind(wx.EVT_LISTBOX, self.OnSelect)
            self.save_log_btn.Bind(wx.EVT_BUTTON, self.OnSaveLog)

    def OnSkip(self, event): event.Skip()
    def OnStop(self, event): event.Skip()
    def OnSelect(self, event): event.Skip()
    def OnSaveLog(self, event): event.Skip()
