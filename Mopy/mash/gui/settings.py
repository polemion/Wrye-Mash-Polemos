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


import wx, os
from .. import singletons
import scandir, json, io  # Polemos
from ..mosh import dirs, GPath
from ..unimash import _, profileEncodings, defaultEncoding  # Polemos
import dialog as gui  # Polemos
from .. import conf  # Polemos
import wx.richtext as rtc  # Polemos
from credits import About  # Polemos


dPos = wx.DefaultPosition
dSize = wx.DefaultSize
Size = wx.Size
space = ((0,0),1,wx.EXPAND,5)
def SizerMany(n, a): return [wx.BoxSizer(a) for x in range(n)]


class SettingsWindow(wx.Dialog):  # Polemos: Total reconstruction.
    """Class for the settings Dialog."""
    settings = None

    def __init__(self, parent=None, id=-1, size=(470,361), pos=dPos, style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE, settings=None):
        """Settings Dialog."""
        wx.Dialog.__init__(self, parent=parent, id=id, size=size, pos=pos, style=style)
        self.SetSizeHints(-1, -1)
        gui.setIcon(self)

        # Common:
        self.name_po, self.version_po, self.website_po, self.developers_po, self.license_po = About(conf.settings['openmw']).getData()
        self.SetTitle(_(u'Wrye Mash Settings'))
        self.openmw = conf.settings['openmw']
        if settings is not None: self.settings = settings
        else: self.settings = {}
        self.ThemeChoiceList = [x[0] for x in self.importThemeList()]
        self.EncodChoiceList = [('%s, %s' % (x, profileEncodings[x])) for x in profileEncodings]
        self.warnkeys = {x: conf.settings[x] for x in conf.settingDefaults if 'query.' in x}
        self.pathsRestart = False

        # Panels
        self.TabNames = {0:'General', 1:'Paths', 2:'Defaults', 3:'Advanced', 4:'About'}  # Keep this updated for tab events.
        self.settings_notebook = wx.Notebook(self, wx.ID_ANY, dPos, size=(-1, -1))
        self.general_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
        self.paths_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
        self.adv_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
        self.defaults_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
        self.about_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)

        if True:  # General Panel ==================== #
            # Main Menu Settings
            MenuBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Main Menu Settings:'))
            Menu_Sizer = wx.StaticBoxSizer(MenuBox, wx.HORIZONTAL)
            self.Menubar_po = wx.CheckBox(MenuBox, wx.ID_ANY, _(u'Enable Menubar'), dPos, dSize, 0)
            self.Columns_Menu_po = wx.CheckBox(MenuBox, wx.ID_ANY, _(u'Enable Columns Menu'), dPos, dSize, 0)
            # Update Settings
            UpdateBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Update Settings:'))
            Update_Sizer = wx.StaticBoxSizer(UpdateBox, wx.HORIZONTAL)
            self.Update_po = wx.CheckBox(UpdateBox, wx.ID_ANY, _(u'Enable Notifications'), dPos, dSize, 0)
            self.Update_staticText = wx.StaticText(UpdateBox, wx.ID_ANY, _(u'Frequency in Days (0=Everyday):'), dPos, dSize, 0)
            self.fldUpdate = wx.SpinCtrl(UpdateBox, wx.ID_ANY, u'', dPos, size=(45, -1),
                                                style=wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL, max=365, min=0)
            # Interface Settings
            InterfaceBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Interface Settings:'))
            Interface_Sizer = wx.StaticBoxSizer(InterfaceBox, wx.VERTICAL)
            self.HovHigh = wx.CheckBox(InterfaceBox, wx.ID_ANY, _(u'Enable Highlight on Hover in Lists'), dPos, dSize, 0)
            self.LrgFont = wx.CheckBox(InterfaceBox, wx.ID_ANY, _(u'Use Big Fonts in Lists'), dPos, dSize, 0)
            self.MinOnClose = wx.CheckBox(InterfaceBox, wx.ID_ANY, _(u'Minimize to Systray'), dPos, dSize, 0)
            self.ShowErr = wx.CheckBox(InterfaceBox, wx.ID_ANY, _(u'Show Debug Log on Errors'), dPos, dSize, 0)
            self.InterfaceStatic = wx.StaticText(InterfaceBox, wx.ID_ANY, _(u'Theme:'), dPos, dSize, 0)
            self.ThemeChoice = wx.Choice(InterfaceBox, wx.ID_ANY, dPos, dSize, self.ThemeChoiceList)
            self.EncodStatic = wx.StaticText(InterfaceBox, wx.ID_ANY, _(u'Preferred Encoding:'), dPos, dSize, 0)
            self.EncodChoice = wx.Choice(InterfaceBox, wx.ID_ANY, dPos, dSize, self.EncodChoiceList)
            # Layout
            Menu_Sizer.AddMany([(self.Menubar_po,0,wx.ALL,5),space,(self.Columns_Menu_po,0,wx.ALL,5)])
            Update_Sizer.AddMany([(self.Update_po,1,wx.ALL,5),(self.Update_staticText,0,wx.ALL,5),(self.fldUpdate,0,wx.BOTTOM|wx.LEFT|wx.RIGHT,5)])
            IntOpt0_Sizer, IntOpt1_Sizer, IntOpt2_Sizer, IntOpt3_Sizer = SizerMany(4, wx.HORIZONTAL)
            IntOpt0_Sizer.AddMany([(self.HovHigh, 0, wx.ALL, 5),space,(self.LrgFont, 0, wx.ALL, 5)])
            IntOpt1_Sizer.AddMany([(self.MinOnClose, 0, wx.ALL, 5), ((0, 0), 1, wx.EXPAND, 5), (self.ShowErr, 0, wx.ALL, 5)])
            IntOpt2_Sizer.AddMany([(self.InterfaceStatic, 0, wx.ALIGN_CENTER|wx.ALL, 5), ((30, 0), 0, 0, 5),(self.ThemeChoice, 1, wx.ALL, 5)])
            IntOpt3_Sizer.AddMany([(self.EncodStatic, 0, wx.ALIGN_CENTER|wx.ALL, 5), ((30, 0), 0, 0, 5),(self.EncodChoice, 1, wx.ALL, 5)])
            Interface_Sizer.AddMany([(IntOpt0_Sizer, 1, wx.EXPAND, 5),
                        (IntOpt1_Sizer, 0, wx.EXPAND, 5),(IntOpt2_Sizer, 0, wx.EXPAND, 5),(IntOpt3_Sizer, 0, wx.EXPAND, 5)])
            General_Sizer = wx.BoxSizer(wx.VERTICAL)
            General_Sizer.AddMany([(Menu_Sizer, 0, wx.EXPAND|wx.ALL,5),(Update_Sizer,0,wx.EXPAND|wx.ALL,5),((0,0),1,0,5),(Interface_Sizer,1,wx.EXPAND|wx.ALL,5)])
            self.general_panel.SetSizer(General_Sizer)
            self.general_panel.Layout()
            General_Sizer.Fit(self.general_panel)

        if True:  # Paths Panel ==================== #
            # Common
            MainPathsBox = wx.StaticBox(self.paths_panel, wx.ID_ANY, _(u'Main Paths:'))
            MainPaths_Sizer = wx.StaticBoxSizer(MainPathsBox, wx.VERTICAL)
            OptionalPathsBox = wx.StaticBox(self.paths_panel, wx.ID_ANY, _(u'Optional Paths:'))
            OptionalPaths_Sizer = wx.StaticBoxSizer(OptionalPathsBox, wx.VERTICAL)
            Paths_Sizer = wx.BoxSizer(wx.VERTICAL)

            if not self.openmw:  # Regular Morrowind support
                # Main Paths: Morrowind
                self.Morrowind_static = wx.StaticText(MainPathsBox, wx.ID_ANY, u'Morrowind:', dPos, dSize, 0)
                uns = rtc.RichTextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, size=(1, 1))  # Ugly unselect hack...
                self.fldMw = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='fldMw', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseMw = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseMw')
                # Main Paths: Installers
                self.Installers_static = wx.StaticText(MainPathsBox, wx.ID_ANY, _(u'Installers:'), dPos, dSize, 0)
                self.fldInst = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='fldInst', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseInst = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseInst')
                # Optional Paths: MGE XE
                self.MGEXE_static = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'MGE XE:', dPos, dSize, 0)
                self.fldMGEXE = wx.TextCtrl(OptionalPathsBox, wx.ID_ANY, u'', dPos, name='fldMGEXE', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseMGEXE = wx.Button(OptionalPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseMGEXE')
                # Optional Paths: Mlox
                self.Mlox_static = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'Mlox:', dPos, dSize, 0)
                self.fldmlox = wx.TextCtrl(OptionalPathsBox, wx.ID_ANY, u'', dPos, name='fldmlox', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsemlox = wx.Button(OptionalPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsemlox')
                # Optional Paths: TES3cmd
                self.TES3cmd_static0 = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'TES3cmd:', dPos, dSize, 0)
                self.TES3cmd_static1 = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'', size=(-1, -1), style=0)
                self.btnRechkT3cmd = wx.Button(OptionalPathsBox, wx.ID_ANY, _(u'Re-Check'), dPos, size=(70, 24))
                # Layout
                Morrowind_Sizer, Installers_Sizer, Mlox_Sizer, MGEXE_Sizer, TES3cmd_Sizer = SizerMany(5, wx.HORIZONTAL)
                Morrowind_Sizer.AddMany([(self.Morrowind_static,0,wx.TOP|wx.RIGHT,5),
                        ((2,0),0,0,5),(uns,0,0,0),(self.fldMw,1,wx.ALIGN_CENTER,5),(self.btnBrowseMw,0,wx.LEFT,5)])
                Installers_Sizer.AddMany([(self.Installers_static,0,wx.TOP|wx.RIGHT,5),
                        ((16,0),0,0,5),(self.fldInst,1,wx.ALIGN_CENTER,5),(self.btnBrowseInst,0,wx.LEFT,5)])
                Mlox_Sizer.AddMany([(self.Mlox_static,0,wx.TOP|wx.RIGHT,5),
                        ((35,0),0,0,5),(self.fldmlox,1,wx.ALIGN_CENTER,5),(self.btnBrowsemlox,0,wx.LEFT,5)])
                MGEXE_Sizer.AddMany([(self.MGEXE_static,0,wx.TOP|wx.RIGHT,5),
                        ((20,0),0,0,5),(self.fldMGEXE,1,wx.ALIGN_CENTER,5),(self.btnBrowseMGEXE,0,wx.LEFT,5)])
                TES3cmd_Sizer.AddMany([(self.TES3cmd_static0,0,wx.TOP|wx.RIGHT,5),
                        ((11,0),0,0,5),(self.TES3cmd_static1,1,wx.TOP|wx.RIGHT,5),(self.btnRechkT3cmd,0,wx.LEFT,5)])
                MainPaths_Sizer.AddMany([(Morrowind_Sizer,0,wx.EXPAND,5),(Installers_Sizer,0,wx.EXPAND,5)])
                OptionalPaths_Sizer.AddMany([(Mlox_Sizer,0,wx.EXPAND,5),(MGEXE_Sizer,0,wx.EXPAND,5), (TES3cmd_Sizer,0,wx.EXPAND,5)])
                Paths_Sizer.AddMany([(MainPaths_Sizer,0,wx.EXPAND|wx.ALL,5),((0,0),1,0,5),(OptionalPaths_Sizer,0,wx.EXPAND|wx.ALL,5)])

            if self.openmw:  #  OpenMW/TES3mp support
                # Main Paths: OpenMW/TES3mp
                self.OpenMWTES3mp_static = wx.StaticText(MainPathsBox, wx.ID_ANY, _(u'OpenMW/TES3mp:'), dPos, dSize, 0)
                uns = rtc.RichTextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, size=(1, 1))  # Ugly unselect hack...
                self.fldOpenMWloc = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='fldOpenMWloc', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseOpenMWloc = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseOpenMWloc')
                # Main Paths: Downloads
                self.Downloads_static = wx.StaticText(MainPathsBox, wx.ID_ANY, _(u'Downloads:'), dPos, dSize, 0)
                self.fldDownloads = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='fldDownloads', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseDownloads = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseDownloads')
                # Main Paths: DataMods
                self.Mods_static = wx.StaticText(MainPathsBox, wx.ID_ANY, _(u'Mods:'), dPos, dSize, 0)
                self.flddatamods = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='flddatamods', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsedatamods = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsedatamods')
                # Main Paths: openmw.cfg
                self.OpenMWConfigs_static = wx.StaticText(MainPathsBox, wx.ID_ANY, u'openmw.cfg:', dPos, dSize, 0)
                self.fldOpenMWConf = wx.TextCtrl(MainPathsBox, wx.ID_ANY, u'', dPos, name='fldOpenMWConf', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseOpenMWConf = wx.Button(MainPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseOpenMWConf')
                # Optional Paths: Morrowind Data Files
                self.DataFiles_static = wx.StaticText(OptionalPathsBox, wx.ID_ANY, _(u'Morrowind Data Files:'), dPos, dSize, 0)
                self.fldDataFiles = wx.TextCtrl(OptionalPathsBox, wx.ID_ANY, u'', dPos, name='fldDataFiles', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseDataFiles = wx.Button(OptionalPathsBox, wx.ID_OPEN, u"...", dPos, size=(30, 24), name='btnBrowseDataFiles')
                # Optional Paths: TES3mp pluginlist.json
                self.TES3mpConfigs_static = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'TES3mp pluginlist.json:', dPos, dSize, 0)
                self.fldTES3mpConf = wx.TextCtrl(OptionalPathsBox, wx.ID_ANY, u'', dPos, name='fldTES3mpConf', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseTES3mpConf = wx.Button(OptionalPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseTES3mpConf')
                # Optional Paths: Mlox64
                self.Mlox64_static = wx.StaticText(OptionalPathsBox, wx.ID_ANY, u'Mlox:', dPos, dSize, 0)
                self.fldmlox64 = wx.TextCtrl(OptionalPathsBox, wx.ID_ANY, u'', dPos, name='fldmlox64', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsemlox64 = wx.Button(OptionalPathsBox, wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsemlox64')
                # Layout
                OpenMWTES3mp_Sizer, Downloads_Sizer, Mods_Sizer, OpenMWconf_Sizer = SizerMany(4, wx.HORIZONTAL)
                DataFiles_Sizer, TES3mpconf_Sizer, Mlox64_Sizer, = SizerMany(3, wx.HORIZONTAL)
                OpenMWTES3mp_Sizer.AddMany([(self.OpenMWTES3mp_static,0,wx.TOP|wx.RIGHT,5),
                                    ((2,0),0,0,5),(uns,0,0,0),(self.fldOpenMWloc,1,wx.ALIGN_CENTER,5),(self.btnBrowseOpenMWloc,0,wx.LEFT,5)])
                Downloads_Sizer.AddMany([(self.Downloads_static,0,wx.TOP|wx.RIGHT,5),
                                    ((43,0),0,0,5),(self.fldDownloads,1,wx.ALIGN_CENTER,5),(self.btnBrowseDownloads,0,wx.LEFT,5)])
                Mods_Sizer.AddMany([(self.Mods_static,0,wx.TOP|wx.RIGHT,5),
                                    ((72,0),0,0,5),(self.flddatamods,1,wx.ALIGN_CENTER,5),(self.btnBrowsedatamods,0,wx.LEFT,5)])
                OpenMWconf_Sizer.AddMany([(self.OpenMWConfigs_static,0,wx.TOP|wx.RIGHT,5),
                                    ((35,0),0,0,5),(self.fldOpenMWConf,1,wx.ALIGN_CENTER,5),(self.btnBrowseOpenMWConf,0,wx.LEFT,5)])
                DataFiles_Sizer.AddMany([(self.DataFiles_static,0,wx.TOP|wx.RIGHT,5),
                                    ((10,0),0,0,5),(self.fldDataFiles,1,wx.ALIGN_CENTER,5),(self.btnBrowseDataFiles,0,wx.LEFT,5)])
                TES3mpconf_Sizer.AddMany([(self.TES3mpConfigs_static,0,wx.TOP|wx.RIGHT,5),
                                    ((2,0),0,0,5),(self.fldTES3mpConf,1,wx.ALIGN_CENTER,5),(self.btnBrowseTES3mpConf,0,wx.LEFT,5)])
                Mlox64_Sizer.AddMany([(self.Mlox64_static,0,wx.TOP|wx.RIGHT,5),((96,0),0,0,5),
                                (self.fldmlox64,1,wx.ALIGN_CENTER,5),(self.btnBrowsemlox64,0,wx.LEFT,5)])
                MainPaths_Sizer.AddMany([(OpenMWTES3mp_Sizer,0,wx.EXPAND,5),(Downloads_Sizer,0,wx.EXPAND,5),
                                (Mods_Sizer,0,wx.EXPAND,5),(OpenMWconf_Sizer,0,wx.EXPAND,5)])
                OptionalPaths_Sizer.AddMany([(DataFiles_Sizer,0,wx.EXPAND,5),(TES3mpconf_Sizer,0,wx.EXPAND,5),(Mlox64_Sizer,0,wx.EXPAND,5)])
                Paths_Sizer.AddMany([(MainPaths_Sizer,0,wx.EXPAND|wx.ALL,5),((0,0),1,0,5),(OptionalPaths_Sizer,0,wx.EXPAND|wx.ALL,5)])

        if True:  # Defaults Panel ==================== #
            # Warnings Settings
            WarnBox = wx.StaticBox(self.defaults_panel, wx.ID_ANY, _(u'Mash Warning Prompts (Check To Enable):'))
            Warn_Sizer = wx.StaticBoxSizer(WarnBox, wx.HORIZONTAL)
            self.warnList = wx.CheckListBox(WarnBox, wx.ID_ANY, dPos, dSize, [x for x in self.warnkeys], wx.LB_EXTENDED|wx.LB_SORT)
            Warn_Sizer.Add(self.warnList, 1, wx.EXPAND, 5)
            # Column Settings
            ColBox = wx.StaticBox(self.defaults_panel, wx.ID_ANY, _(u'Mash Columns Default Widths:'))
            Col_Sizer = wx.StaticBoxSizer(ColBox, wx.VERTICAL)
            self.Col_staticText = wx.StaticText(ColBox, wx.ID_ANY, _(u'If you wish to reset all the columns widths of Wrye Mash displayed lists\n'
                    u'(e.g.: Mod Lists) to their default settings check the box below and then\nclick the OK button:'), dPos, dSize, 0)
            self.colReset = wx.CheckBox(ColBox, wx.ID_ANY, _(u'Reset All Of Wrye Mash Columns Widths?')+' '*5, dPos, dSize, wx.ALIGN_RIGHT)
            Col_Sizer.AddMany([(self.Col_staticText, 0, wx.EXPAND, 5), (self.colReset, 0, wx.EXPAND|wx.ALL, 5)])
            # Layout
            Defaults_Sizer = wx.BoxSizer(wx.VERTICAL)
            Defaults_Sizer.AddMany([(Warn_Sizer, 1, wx.EXPAND|wx.ALL,5), (Col_Sizer, 0, wx.EXPAND|wx.ALL,5)])
            self.defaults_panel.SetSizer(Defaults_Sizer)
            self.defaults_panel.Layout()
            Defaults_Sizer.Fit(self.defaults_panel)

        if True:  # Advanced Panel ==================== #
            # Common
            advitmsBox = wx.StaticBox( self.adv_panel, wx.ID_ANY, u'Advanced Settings:' )
            advitms_Sizer = wx.StaticBoxSizer(advitmsBox, wx.VERTICAL)

            if not self.openmw:  # Regular Morrowind support
                self.a7zcrcOn = wx.CheckBox(advitmsBox, wx.ID_ANY,
                        u'Use 7zip to calculate crc32 for large files (may give 2%-20% faster "Refresh")', dPos, dSize, 0)
                advitms_Sizer.AddMany([(self.a7zcrcOn, 0, 0, 5)])

            if self.openmw:  # OpenMW/TES3mp support
                advinfo = wx.StaticText(advitmsBox, wx.ID_ANY, _(u'Nothing here yet!'), dPos, dSize, 0)
                advitms_Sizer.AddMany([(advinfo, 0, 0, 5)])

            # Common Layout
            adv_Sizer = wx.BoxSizer(wx.VERTICAL)
            adv_Sizer.Add(advitms_Sizer, 1, wx.EXPAND|wx.ALL, 5)
            self.adv_panel.SetSizer(adv_Sizer)
            self.adv_panel.Layout()
            adv_Sizer.Fit(self.adv_panel)

        if True:  # About Panel ==================== #
            # Title/Version/Image Logo
            self.title = wx.StaticText(self.about_panel, wx.ID_ANY, self.name_po, dPos, dSize, wx.ALIGN_CENTRE)
            self.version = wx.StaticText(self.about_panel, wx.ID_ANY, self.version_po, dPos, dSize, wx.ALIGN_CENTRE)
            self.wrye_bad = wx.StaticBitmap(self.about_panel, wx.ID_ANY, wx.Bitmap('images/wrye_bad.jpg'), dPos, size=(140, 140))
            # Buttons
            self.license_button = wx.Button(self.about_panel, wx.ID_ANY, _(u'License'), dPos, size=(60, 22))
            self.credits_button = wx.Button(self.about_panel, wx.ID_ANY, _(u'Credits'), dPos, size=(60, 22))
            # Contents
            self.contents = rtc.RichTextCtrl(self.about_panel,wx.ID_ANY,u'',dPos,size=(-1,166),
                                style=wx.TE_READONLY|wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS)
            self.contents.SetFocus()
            # URL
            self.home_url = wx.HyperlinkCtrl(self.about_panel,wx.ID_ANY,self.website_po[0],
                                self.website_po[1],dPos,dSize,wx.HL_CONTEXTMENU|wx.HL_DEFAULT_STYLE)
            # Layout
            AboutImage_Sizer, About_Sizer = SizerMany(2, wx.VERTICAL)
            AboutImageBtn_Sizer, AboutMain_Sizer, AboutURL_Sizer = SizerMany(3, wx.HORIZONTAL)
            AboutImageBtn_Sizer.AddMany([(self.license_button,0,wx.RIGHT|wx.LEFT,5),((11,0),0,0,5),(self.credits_button,0,wx.RIGHT|wx.LEFT,5)])
            AboutURL_Sizer.AddMany([space,(self.home_url,0,wx.RIGHT|wx.LEFT|wx.EXPAND,5),space])
            AboutImage_Sizer.AddMany([(self.wrye_bad,0,wx.ALL,5),space,(
                AboutImageBtn_Sizer,0,wx.TOP,5),space,(AboutURL_Sizer,1,wx.EXPAND|wx.TOP,5),space])
            AboutMain_Sizer.AddMany([(AboutImage_Sizer,0,wx.EXPAND,5),(self.contents,1,wx.ALL|wx.EXPAND,5)])
            About_Sizer.AddMany([(self.title,0,wx.EXPAND|wx.RIGHT|wx.LEFT,
                5),(self.version,0,wx.EXPAND|wx.RIGHT|wx.LEFT,5),(AboutMain_Sizer,1,wx.EXPAND,5)])
            self.about_panel.SetSizer(About_Sizer)
            self.about_panel.Layout()
            About_Sizer.Fit(self.about_panel)

        if True:  # Footer
            # Error/Status Messages
            self.Settingstext = wx.StaticText(self, wx.ID_ANY, u'', dPos, dSize, 0)
            # OK/Cancel Buttons
            self.btnOK = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, size=(35, 22), name='btnOK')
            self.btnCancel = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, size=(60, 22), name='btnCancel')
            # Layout
            Buttons_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            Buttons_Sizer.AddMany([(self.Settingstext,1,wx.ALL,5),(self.btnOK,0,wx.RIGHT|wx.LEFT,5),(self.btnCancel,0,wx.RIGHT,5)])

        if True:  # Theming
            # Common
            self.about_panel.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.contents.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.home_url.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.Settingstext.SetForegroundColour((255, 0, 0))
            if not self.openmw:  # Regular Morrowind support
                pass
                '''self.fldMw.SetBackgroundColour(wx.WHITE)
                self.fldInst.SetBackgroundColour(wx.WHITE)
                self.fldmlox.SetBackgroundColour(wx.WHITE)'''
            if self.openmw:  # OpenMW/TES3mp support
                pass
                '''self.fldOpenMWloc.SetBackgroundColour(wx.WHITE)
                self.fldDownloads.SetBackgroundColour(wx.WHITE)
                self.flddatamods.SetBackgroundColour(wx.WHITE)
                self.fldmlox64.SetBackgroundColour(wx.WHITE)
                self.fldOpenMWConf.SetBackgroundColour(wx.WHITE)
                self.fldDataFiles.SetBackgroundColour(wx.WHITE)
                self.fldTES3mpConf.SetBackgroundColour(wx.WHITE)'''
                #boxOpenMWlocDir.SetForegroundColour(wx.WHITE)

        if True:  # Init Conditions
            self.txtWrap()
            self.text_engine(self.developers_po)
            self.btnOK.SetFocus()
            self.InitSettings()

        if True:  # Common
            # Fonts
            self.title.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, '@Arial Unicode MS'))
            self.version.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, '@Arial Unicode MS'))
            self.home_url.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, True, '@Arial Unicode MS'))
            self.Settingstext.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
            # Layout
            self.paths_panel.SetSizer(Paths_Sizer)
            self.paths_panel.Layout()
            Paths_Sizer.Fit(self.paths_panel)
            self.settings_notebook.AddPage(self.general_panel, _(u'General'), True)
            self.settings_notebook.AddPage(self.paths_panel, _(u'Paths'), False)
            self.settings_notebook.AddPage(self.defaults_panel, _(u'Defaults'), False)
            self.settings_notebook.AddPage(self.adv_panel, u"Advanced", False)
            self.settings_notebook.AddPage(self.about_panel, _(u'About'), False)
            main_Sizer = wx.BoxSizer(wx.VERTICAL)
            main_Sizer.AddMany([(self.settings_notebook,1,wx.EXPAND|wx.ALL,5),(Buttons_Sizer,0,wx.RIGHT|wx.LEFT|wx.EXPAND,5)])
            self.SetSizer(main_Sizer)
            self.Layout()

        if True: # =================== Disabled Items ====================== #
            if self.openmw:  # OpenMW
                [x.Disable() for x in (self.Mlox64_static,
                                       self.fldmlox64,
                                       self.btnBrowsemlox64,
                                       self.TES3mpConfigs_static,
                                       self.fldTES3mpConf,
                                       self.btnBrowseTES3mpConf)]
                # ==================== Disabled Items ====================== #

        if True:  # Events:
            self.timer_po()
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnClose)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_BUTTON(self, wx.ID_OPEN, self.OpenDialog)
            if not self.openmw: self.btnRechkT3cmd.Bind(wx.EVT_BUTTON, self.OnDetectTES3cmd)
            self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnShowPage)
            self.license_button.Bind(wx.EVT_BUTTON, self.license_txt)
            self.credits_button.Bind(wx.EVT_BUTTON, self.credits_txt)

    def timer_po(self): # Polemos a simple wx timer.
        """A simple timer to check for problems in settings."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1)

    def OnShowPage(self, event):
        """Focus on OK."""
        if self.TabNames[event.GetSelection()] != 'About':
            self.btnOK.SetFocus()

    def txtWrap(self):
        """Text Form."""
        # Common
        [x.Wrap(-1) for x in (self.Update_staticText,self.InterfaceStatic,self.title,self.version,self.Settingstext)]
        if not self.openmw:  # Regular Morrowind support
            [x.Wrap(-1) for x in (self.Morrowind_static,self.Installers_static,self.Mlox_static)]
        if self.openmw:  # OpenMW/TES3mp support
            [x.Wrap(-1) for x in (self.OpenMWTES3mp_static,self.Downloads_static,self.Mods_static,self.OpenMWConfigs_static,
                                  self.DataFiles_static,self.TES3mpConfigs_static,self.Mlox64_static)]

    def importThemeList(self):
        """Import theme list."""
        themedir = os.path.join(singletons.MashDir, 'themes')
        if not os.path.exists(themedir): os.makedirs(themedir)
        themeList = scandir.listdir(themedir)
        themeData = []*(len(themeList)+1)
        for theme in themeList:
            themePath = os.path.join(themedir, theme)
            with io.open(themePath, 'r', encoding='utf-8') as rawTheme:
                themeRaw = json.load(rawTheme)
                themeData.append((themeRaw['theme.info'], theme))
        if not [name for name in themeData if name[0] == 'Default theme']:themeData.append(('Default theme', None))
        themeData = list(set(themeData))
        themeData.sort(key=lambda x: x[0])
        self.themeData = themeData
        return themeData

    def onUpdate(self, event):
        """Safety check for settings."""
        disable = False
        errors = []
        # Rules
        if True:  # Menu check.
            menu_1 = self.Menubar_po.GetValue()
            menu_2 = self.Columns_Menu_po.GetValue()
            if not menu_1 and not menu_2:
                errors.append(_(u'Please select at least one menu option.'))
                disable = True
        if True:  # Dir conflict check.
            if not self.check_conflicts():
                errors.append(_(u'Conflict in directory settings.'))
                disable = True
        # Actions
        if disable:
            if self.Settingstext.GetLabel() != errors[0]: self.Settingstext.SetLabel(errors[0])
            self.btnOK.Disable()
        else:
            self.Settingstext.SetLabel(u'')
            self.btnOK.Enable()
        [x.Disable() if not self.Update_po.IsChecked() else x.Enable() for x in (self.Update_staticText, self.fldUpdate)]

    def license_txt(self, event):
        """Show License."""
        self.contents.SetValue(u'')
        self.text_engine(self.license_po)
        self.contents.SetFocus()

    def credits_txt(self, event):
        """Show Credits."""
        self.contents.SetValue(u'')
        self.text_engine(self.developers_po)
        self.contents.SetFocus()

    def text_engine(self, text):
        """Text Engine for About Tab."""
        field = self.contents
        for x in text:
            atr, txt = x[1], x[0]
            if atr == 'b':
                field.BeginBold()
                field.WriteText(txt)
                field.EndBold()
            elif atr == 'i':
                field.BeginItalic()
                field.WriteText(txt)
                field.EndItalic()
            elif atr == 'u':
                field.BeginUnderline()
                field.WriteText(txt)
                field.EndUnderline()
            else: field.WriteText(txt)

    def check_conflicts(self):
        """Check for conflicts in path fields."""
        # Regular Morrowind
        if not self.openmw: check = (self.fldMw, self.fldInst)
        # OpenMW/Tes3MP
        else: check = (self.fldOpenMWloc, self.flddatamods, self.fldDownloads, self.fldDataFiles)
        values = [x.GetValue().rstrip('\\ ').lower() for x in check if x.GetValue().rstrip('\\ ')]
        conflicts = {x for x in values if values.count(x) > 1}
        [x.SetForegroundColour(wx.RED) if x.GetValue().rstrip('\\ ').lower() in conflicts else x.SetForegroundColour(wx.BLACK) for x in check]
        return len(set(values)) == len(values)

    def dir_already_set(self):
        """Check for duplicate dir set in settings and colorize their fields."""
        data = ['OpenMWloc', 'Downloads', 'datamods', 'DataFiles']
        data_val = [getattr(self, 'fld%s' % x, None).GetValue() for x in data]
        double = []
        for x in data:
            y = getattr(self, 'fld%s' % x, None).GetValue()
            if data_val.count(y) > 1: double.append(x)
        for x in data:
            if x in double: getattr(self, 'fld%s' % x, None).SetForegroundColour(wx.RED)
            else: getattr(self, 'fld%s' % x, None).SetForegroundColour(wx.BLACK)

    def OpenDialog(self, event):
        """Choosing files or directories."""
        name = event.EventObject.Name[9:]
        if any((conf.dataMap[name].endswith(x) for x in ['.exe','.cfg','.py','.json','.ini','pl'])):
            ext = [x for x in ['.exe','.cfg','.py','.json','.ini','pl'] if conf.dataMap[name].endswith(x)][0]
            dialog = wx.FileDialog(self, _(u'Select %s file location:') % conf.dataMap[name].capitalize(),
                                   '', '%s' % conf.dataMap[name], u'Files (*%s)|*%s' % (ext,ext), style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        else: dialog = wx.DirDialog(self, _(u'%s directory selection') % conf.dataMap[name].capitalize())
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            dialog.Destroy()
            getattr(self, 'fld%s'%name).SetValue(path)
            if self.openmw: self.dir_already_set()

    def menu_config_po(self):
        """Set the menu configuration."""
        menu_changed = False
        if not self.Menubar_po.GetValue() and not self.Columns_Menu_po.GetValue(): return False
        if self.Menubar_po.GetValue() != conf.settings['mash.menubar.enabled']:
            conf.settings['mash.menubar.enabled'] = self.Menubar_po.GetValue()
            menu_changed = True
        if self.Columns_Menu_po.GetValue() != conf.settings['mash.col.menu.enabled']:
            conf.settings['mash.col.menu.enabled'] = self.Columns_Menu_po.GetValue()
            menu_changed = True
        return menu_changed

    def set_settings(self):
        """Save common settings."""
        conf.settings['enable.check'] = self.Update_po.GetValue()
        conf.settings['timeframe.check'] = self.fldUpdate.GetValue()
        conf.settings['interface.lists.color'] = self.HovHigh.GetValue()
        conf.settings['mash.large.fonts'] = self.LrgFont.GetValue()
        conf.settings['app.min.systray'] = self.MinOnClose.GetValue()
        conf.settings['show.debug.log'] = self.ShowErr.GetValue()
        conf.settings['active.theme'] = self.ThemeChoiceNew = [x for num, x in enumerate(self.themeData) if num == self.ThemeChoice.GetSelection()][0]
        conf.settings['profile.encoding'] = self.EncodChoiceNew = [enc for enc in profileEncodings if enc in
                    [x for num, x in enumerate(self.EncodChoiceList) if num == self.EncodChoice.GetSelection()][0]][0]
        for x in self.warnkeys: conf.settings[x]=False if x in self.warnList.GetCheckedStrings() else True
        if self.colReset.GetValue(): self.resetMashLists()

    def resetMashLists(self):
        """Resets the column widths of Mash lists to their default values."""
        # Get default width sizes
        colkeys = {x:conf.settingsOrig[x] for x in conf.settingsOrig if '.colWidths' in x}
        # Common Lists
        mashLists = {singletons.utilsList.list: colkeys['mash.utils.colWidths'],
                     singletons.modList.list: colkeys['mash.mods.colWidths'],
                     singletons.BSArchives.Archives.list: colkeys['mash.Archives.colWidths'],
                     singletons.modsMastersList.list: colkeys['mash.masters.colWidths'],
                     singletons.screensList.list: colkeys['mash.screens.colWidths']
                     }
        # Morrowind Lists
        mashLists.update({singletons.gInstList.gList: colkeys['mash.installers.colWidths'],
                          singletons.saveList.list: colkeys['mash.saves.colWidths'],
                          singletons.savesMastersList.list: colkeys['mash.masters.colWidths']
                          } if not self.openmw else {})
        # OpenMW Lists
        mashLists.update({singletons.ModdataList.list: colkeys['mash.datamods.colWidths'],
                          singletons.ModPackageList.list: colkeys['mash.Packages.colWidths']
                          } if self.openmw else {})
        # Reset list's widths
        for lst in mashLists:
            max = lst.GetColumnCount()
            for num in xrange(max):
                if num < max-1:
                    key = lst.GetColumn(num).GetText().strip()
                    lst.SetColumnWidth(num, mashLists[lst][key])
                else: lst.resizeLastColumn(30)

    def chkSpecialPaths(self):
        """Check for changes in paths which need Wrye restart."""
        if not self.openmw:  # Polemos: Regular Morrowind Settings:
            if conf.settings['mwDir'] != self.fldMw.GetValue(): return True
            elif conf.settings['sInstallersDir'] != self.fldInst.GetValue(): return True

        elif self.openmw:  # Polemos: OpenMW/Tes3MP Settings:
            if conf.settings['openmwDir'] != self.fldOpenMWloc.GetValue(): return True
            elif conf.settings['datamods'] != self.flddatamods.GetValue(): return True
            elif conf.settings['downloads'] != self.fldDownloads.GetValue(): return True
            elif conf.settings['openmwprofile'] != os.path.dirname(self.fldOpenMWConf.GetValue()): return True
            elif conf.settings['openmw.datafiles'] != self.fldDataFiles.GetValue(): return True
            elif conf.settings['TES3mpConf'] != self.fldTES3mpConf.GetValue(): return True
            elif conf.settings['mashdir'] != os.path.join(self.flddatamods.GetValue(), 'Mashdir'): return True

    def OnOk(self, event):
        """Ok button handler."""
        self.pathsRestart = self.chkSpecialPaths()

        if not self.openmw:  # Regular Morrowind Settings:
            conf.settings['mwDir'] = self.fldMw.GetValue()
            conf.settings['mloxpath'] = self.fldmlox.GetValue()
            conf.settings['sInstallersDir'] = self.fldInst.GetValue()
            conf.settings['mgexe.dir'] = self.fldMGEXE.GetValue()
            conf.settings['advanced.7zipcrc32'] = self.a7zcrcOn.GetValue()

        if self.openmw:  # OpenMW/Tes3MP Settings:
            conf.settings['openmwDir'] = self.fldOpenMWloc.GetValue()
            conf.settings['datamods'] = self.flddatamods.GetValue()
            conf.settings['downloads'] = self.fldDownloads.GetValue()
            conf.settings['openmwprofile'] = os.path.dirname(self.fldOpenMWConf.GetValue())
            conf.settings['openmw.datafiles'] = self.fldDataFiles.GetValue()
            conf.settings['TES3mpConf'] = self.fldTES3mpConf.GetValue()
            conf.settings['mlox64path'] = self.fldmlox64.GetValue()
            conf.settings['mashdir'] = os.path.join(self.flddatamods.GetValue(), 'Mashdir')

        for item in self.paths_panel.GetChildren():
            if item.Name.startswith("fld") and item.Name[3:] in conf.dataMap:
                name = conf.dataMap[item.Name[3:]]
                if name in dirs: dirs[name] = GPath(item.GetValue())

        self.set_settings()  # Common Settings
        self.OnClose()
        self.chkRestart()

    def OnClose(self, event=None):
        """Notifications on settings close."""
        conf.settings['mash.settings.pos'] = self.GetPosition()
        self.timer.Stop()
        self.Destroy()

    def OnDetectTES3cmd(self, event=None):
        """Returns TES3cmd.exe path."""
        path = os.path.join(conf.settings['mwDir'], 'Data Files', 'tes3cmd.exe')
        if os.path.exists(path):
            self.TES3cmd_static1.SetLabel(_(u'Detected!'))
            self.TES3cmd_static1.SetForegroundColour(wx.BLUE)
        else:
            self.TES3cmd_static1.SetLabel(_(u'"TES3cmd.exe" not found in "Data Files" directory.'))
            self.TES3cmd_static1.SetForegroundColour(wx.RED)

    def chkRestart(self):
        """Check if Wrye Mash needs to restart."""
        if any((self.menu_config_po(),
                self.LrgFontEx != self.LrgFont.GetValue(),
                self.ShowErrEx != self.ShowErr.GetValue(),
                self.ThemeChoiceEx != self.ThemeChoiceNew,
                self.EncChoiceEx != self.EncodChoiceNew,
                self.pathsRestart
                )): gui.InfoMessage(self, _(u'Please restart Wrye Mash for changes to take effect.'))

    def InitCommon(self):
        """Init Common Settings."""
        self.Menubar_po.SetValue(conf.settings['mash.menubar.enabled'])
        self.Columns_Menu_po.SetValue(conf.settings['mash.col.menu.enabled'])
        self.HovHigh.SetValue(conf.settings['interface.lists.color'])
        self.LrgFont.SetValue(conf.settings['mash.large.fonts'])
        self.MinOnClose.SetValue(conf.settings['app.min.systray'])
        self.ShowErr.SetValue(conf.settings['show.debug.log'])
        self.ThemeChoice.SetSelection([num for num, x in enumerate(self.themeData) if x[0] == conf.settings['active.theme'][0]][0])
        try: self.EncodChoice.SetSelection([num for num, x in enumerate(self.EncodChoiceList) if conf.settings['profile.encoding'] in x][0])
        except: self.EncodChoice.SetSelection([num for num, x in enumerate(self.EncodChoiceList) if defaultEncoding in x][0])
        self.Update_po.SetValue(conf.settings['enable.check'])
        self.fldUpdate.SetValue(conf.settings['timeframe.check'])
        self.warnList.SetCheckedStrings([x for x in self.warnkeys if not self.warnkeys[x]])
        # Items that need Wrye Mash to restart
        self.ShowErrEx = conf.settings['show.debug.log']
        self.LrgFontEx = conf.settings['mash.large.fonts']
        self.ThemeChoiceEx = conf.settings['active.theme']
        self.EncChoiceEx = conf.settings['profile.encoding']

    def InitSettings(self):
        """Init settings.."""
        self.InitCommon()

        if not self.openmw:  # Regular Morrowind Settings:
            # Paths
            for x, y in zip((self.fldMw, self.fldmlox, self.fldInst, self.fldMGEXE),
                            (conf.settings['mwDir'], conf.settings['mloxpath'],
                             conf.settings['sInstallersDir'], conf.settings['mgexe.dir'])):
                try: x.SetValue(y)
                except: pass
            # Misc
            self.OnDetectTES3cmd()
            self.a7zcrcOn.SetValue(conf.settings['advanced.7zipcrc32'])

        if self.openmw:  # OpenMW/Tes3MP Settings
            # Paths
            for x, y in zip((self.fldOpenMWloc,self.flddatamods,self.fldDownloads,self.fldOpenMWConf,self.fldDataFiles,self.fldTES3mpConf,self.fldmlox64),
                            (conf.settings['openmwDir'],conf.settings['datamods'],conf.settings['downloads'],
                             os.path.join(conf.settings['openmwprofile'], 'openmw.cfg'),conf.settings['openmw.datafiles'],
                             conf.settings['TES3mpConf'],conf.settings['mlox64path'])):
                try: x.SetValue(y)
                except: pass
