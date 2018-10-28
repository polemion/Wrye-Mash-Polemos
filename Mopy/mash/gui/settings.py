# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
#
# Wrye Mash 2018 Polemos fork Copyright (C) 2017-2018 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher
#
#  Copyright on the original code 2005-2009 Wrye
#  Copyright on any non trivial modifications or substantial additions 2009-2011 Melchor
#  Copyright on any non trivial modifications or substantial additions 2011-2016 Yacoby
#  Copyright on any non trivial modifications or substantial additions 2017-2018 Polemos
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
import scandir, json, codecs  # Polemos
from ..mosh import _, dirs, GPath
import dialog as gui  # Polemos
from .. import conf  # Polemos
import wx.richtext as rtc  # Polemos
from credits import About  # Polemos


dPos = wx.DefaultPosition
dSize = wx.DefaultSize
Size = wx.Size


class SettingsWindow(wx.Dialog):  # Polemos: Total reconstruction.
    """Class for the settings Dialog."""
    settings = None

    def __init__(self, parent=None, id=-1, size=(464,331), pos=dPos, style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE, settings=None):
        """Settings Dialog."""
        wx.Dialog.__init__(self, parent=parent, id=id, size=size, pos=pos, style=style)
        self.name_po, self.version_po, self.website_po, self.developers_po, self.license_po = About(conf.settings['openmw']).getData()

        # Common:
        self.SetTitle(_(u'Wrye Mash Settings'))
        self.openmw = conf.settings['openmw']
        if settings is not None: self.settings = settings
        else: self.settings = {}
        self.ThemeChoiceList = [x[0] for x in self.importThemeList()]
        self.pathsRestart = False
        self.SetSizeHints(-1, -1)
        self.TabNames = {0:'General', 1:'Paths', 2:'About'}  # Keep this updated.
        self.settings_notebook = wx.Notebook(self, wx.ID_ANY, dPos, size=(-1, -1))

        if True:  # General Panel
            self.general_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            # Main Menu Settings
            MenuBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Main Menu Settings:'))
            Menu_Sizer = wx.StaticBoxSizer(MenuBox, wx.HORIZONTAL)
            self.Menubar_po = wx.CheckBox(Menu_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Enable Menubar'), dPos, dSize, 0)
            self.Columns_Menu_po = wx.CheckBox(Menu_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Enable Columns Menu'), dPos, dSize, 0)
            # Update Settings
            UpdateBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Update Settings:'))
            Update_Sizer = wx.StaticBoxSizer(UpdateBox, wx.HORIZONTAL)
            self.Update_po = wx.CheckBox(Update_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Enable Notifications'), dPos, dSize, 0)
            self.Update_staticText = wx.StaticText(Update_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Frequency in Days (0=Everyday):'), dPos, dSize, 0)
            self.fldUpdate = wx.SpinCtrl(Update_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, size=(45, -1),
                                                style=wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL, max=365, min=0)
            # Interface Settings
            InterfaceBox = wx.StaticBox(self.general_panel, wx.ID_ANY, _(u'Interface Settings:'))
            Interface_Sizer = wx.StaticBoxSizer(InterfaceBox, wx.VERTICAL)
            self.HovHigh = wx.CheckBox(Interface_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Enable Highlight on Hover in Lists'), dPos, dSize, 0)
            self.LrgFont = wx.CheckBox(Interface_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Use Big Fonts in Lists'), dPos, dSize, 0)
            self.MinOnClose = wx.CheckBox(Interface_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Minimize to Systray'), dPos, dSize, 0)
            self.ShowErr = wx.CheckBox(Interface_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Show Debug Log on Errors'), dPos, dSize, 0)
            self.InterfaceStatic = wx.StaticText(Interface_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Theme:'), dPos, dSize, 0)
            self.ThemeChoice = wx.Choice(Interface_Sizer.GetStaticBox(), wx.ID_ANY, dPos, dSize, self.ThemeChoiceList)
            # Sizers ========================================= #
            Menu_Sizer.AddMany([(self.Menubar_po,0,wx.ALL,5),((0,0),1,wx.EXPAND,5),(self.Columns_Menu_po,0,wx.ALL,5)])
            Update_Sizer.AddMany([(self.Update_po,1,wx.ALL,5),(self.Update_staticText,0,wx.ALL,5),(self.fldUpdate,0,wx.BOTTOM|wx.LEFT|wx.RIGHT,5)])
            IntOpt0_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            IntOpt1_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            IntOpt2_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            IntOpt0_Sizer.AddMany([(self.HovHigh, 0, wx.ALL, 5),((0,0),1,wx.EXPAND,5),(self.LrgFont, 0, wx.ALL, 5)])
            IntOpt1_Sizer.AddMany([(self.MinOnClose, 0, wx.ALL, 5), ((0, 0), 1, wx.EXPAND, 5), (self.ShowErr, 0, wx.ALL, 5)])
            IntOpt2_Sizer.AddMany([(self.InterfaceStatic, 0, wx.ALIGN_CENTER|wx.ALL, 5),((30, 0), 0, 0, 5),(self.ThemeChoice, 1, wx.ALL, 5)])
            Interface_Sizer.AddMany([(IntOpt0_Sizer, 1, wx.EXPAND, 5),(IntOpt1_Sizer, 0, wx.EXPAND, 5),(IntOpt2_Sizer, 0, wx.EXPAND, 5)])
            General_Sizer = wx.BoxSizer(wx.VERTICAL)
            General_Sizer.AddMany([(Menu_Sizer, 0, wx.EXPAND|wx.ALL,5),(Update_Sizer,0,wx.EXPAND|wx.ALL,5),((0,0),1,0,5),(Interface_Sizer,1,wx.EXPAND|wx.ALL,5)])
            self.general_panel.SetSizer(General_Sizer)
            self.general_panel.Layout()
            General_Sizer.Fit(self.general_panel)

        if True:  # Paths Panel
            # Common
            self.paths_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            MainPathsBox = wx.StaticBox(self.paths_panel, wx.ID_ANY, _(u'Main Paths:'))
            MainPaths_Sizer = wx.StaticBoxSizer(MainPathsBox, wx.VERTICAL)
            OptionalPathsBox = wx.StaticBox(self.paths_panel, wx.ID_ANY, _(u'Optional Paths:'))
            OptionalPaths_Sizer = wx.StaticBoxSizer(OptionalPathsBox, wx.VERTICAL)
            Paths_Sizer = wx.BoxSizer(wx.VERTICAL)

            if not self.openmw:  # Regular Morrowind support
                # ===== Main Paths ===== #
                # Morrowind
                self.Morrowind_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'Morrowind:', dPos, dSize, 0)
                uns = rtc.RichTextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, size=(1, 1))  # Ugly unselect hack...
                self.fldMw = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldMw', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseMw = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseMw')
                # Installers
                self.Installers_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Installers:'), dPos, dSize, 0)
                self.fldInst = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldInst', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseInst = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseInst')
                # ===== Optional Paths ==== #
                # Mlox
                self.Mlox_static = wx.StaticText(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'Mlox:', dPos, dSize, 0)
                self.fldmlox = wx.TextCtrl(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldmlox', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsemlox = wx.Button(OptionalPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsemlox')
                # Sizers ========================================= #
                Morrowind_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Installers_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Mlox_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Morrowind_Sizer.AddMany([(self.Morrowind_static,0,wx.TOP|wx.RIGHT,5),((1,0),0,0,5),(uns,0,0,0),(self.fldMw,1,wx.ALIGN_CENTER,5),(self.btnBrowseMw,0,wx.LEFT,5)])
                Installers_Sizer.AddMany([(self.Installers_static,0,wx.TOP|wx.RIGHT,5),((16,0),0,0,5),(self.fldInst,1,wx.ALIGN_CENTER,5),(self.btnBrowseInst,0,wx.LEFT,5)])
                Mlox_Sizer.AddMany([(self.Mlox_static,0,wx.TOP|wx.RIGHT,5),((35,0),0,0,5),(self.fldmlox,1,wx.ALIGN_CENTER,5),(self.btnBrowsemlox,0,wx.LEFT,5)])
                MainPaths_Sizer.AddMany([(Morrowind_Sizer,0,wx.EXPAND,5),(Installers_Sizer,0,wx.EXPAND,5)])
                OptionalPaths_Sizer.AddMany([(Mlox_Sizer,0,wx.EXPAND,5)])  # Thinking ahead.
                Paths_Sizer.AddMany([(MainPaths_Sizer,0,wx.EXPAND|wx.ALL,5),((0,0),1,0,5),(OptionalPaths_Sizer,0,wx.EXPAND|wx.ALL,5)])

            if self.openmw:  #  OpenMW/TES3mp support
                # ===== Main Paths ===== #
                # OpenMW/TES3mp
                self.OpenMWTES3mp_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, _(u'OpenMW/TES3mp:'), dPos, dSize, 0)
                uns = rtc.RichTextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, size=(1, 1))  # Ugly unselect hack...
                self.fldOpenMWloc = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldOpenMWloc', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseOpenMWloc = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseOpenMWloc')
                # Downloads
                self.Downloads_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Downloads:'), dPos, dSize, 0)
                self.fldDownloads = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldDownloads', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseDownloads = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseDownloads')
                # DataMods
                self.Mods_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Mods:'), dPos, dSize, 0)
                self.flddatamods = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='flddatamods', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsedatamods = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsedatamods')
                # openmw.cfg
                self.OpenMWConfigs_static = wx.StaticText(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'openmw.cfg:', dPos, dSize, 0)
                self.fldOpenMWConf = wx.TextCtrl(MainPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldOpenMWConf', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseOpenMWConf = wx.Button(MainPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseOpenMWConf')
                # ===== Optional Paths ==== #
                # Morrowind Data Files
                self.DataFiles_static = wx.StaticText(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, _(u'Morrowind Data Files:'), dPos, dSize, 0)
                self.fldDataFiles = wx.TextCtrl(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldDataFiles', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseDataFiles = wx.Button(OptionalPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u"...", dPos, size=(30, 24), name='btnBrowseDataFiles')
                # TES3mp pluginlist.json
                self.TES3mpConfigs_static = wx.StaticText(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'TES3mp pluginlist.json:', dPos, dSize, 0)
                self.fldTES3mpConf = wx.TextCtrl(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldTES3mpConf', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowseTES3mpConf = wx.Button(OptionalPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowseTES3mpConf')
                # Mlox64
                self.Mlox64_static = wx.StaticText(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'Mlox:', dPos, dSize, 0)
                self.fldmlox64 = wx.TextCtrl(OptionalPaths_Sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, name='fldmlox64', size=(-1, 20), style=wx.TE_RICH)
                self.btnBrowsemlox64 = wx.Button(OptionalPaths_Sizer.GetStaticBox(), wx.ID_OPEN, u'...', dPos, size=(30, 24), name='btnBrowsemlox64')
                # Sizers ========================================= #
                OpenMWTES3mp_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Downloads_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Mods_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                OpenMWconf_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                DataFiles_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                TES3mpconf_Sizer = wx.BoxSizer(wx.HORIZONTAL)
                Mlox64_Sizer = wx.BoxSizer(wx.HORIZONTAL)
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
                Mlox64_Sizer.AddMany([(self.Mlox64_static,0,wx.TOP|wx.RIGHT,5),((96,0),0,0,5),(self.fldmlox64,1,wx.ALIGN_CENTER,5),(self.btnBrowsemlox64,0,wx.LEFT,5)])
                MainPaths_Sizer.AddMany([(OpenMWTES3mp_Sizer,0,wx.EXPAND,5),(Downloads_Sizer,0,wx.EXPAND,5),(Mods_Sizer,0,wx.EXPAND,5),(OpenMWconf_Sizer,0,wx.EXPAND,5)])
                OptionalPaths_Sizer.AddMany([(DataFiles_Sizer,0,wx.EXPAND,5),(TES3mpconf_Sizer,0,wx.EXPAND,5),(Mlox64_Sizer,0,wx.EXPAND,5)])
                Paths_Sizer.AddMany([(MainPaths_Sizer,0,wx.EXPAND|wx.ALL,5),(OptionalPaths_Sizer,0,wx.EXPAND|wx.ALL,5)])

        if True:  # About Panel
            self.about_panel = wx.Panel(self.settings_notebook, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            # Title/Version/Image Logo
            self.title = wx.StaticText(self.about_panel, wx.ID_ANY, self.name_po, dPos, dSize, wx.ALIGN_CENTRE)
            self.version = wx.StaticText(self.about_panel, wx.ID_ANY, self.version_po, dPos, dSize, wx.ALIGN_CENTRE)
            self.wrye_bad = wx.StaticBitmap(self.about_panel, wx.ID_ANY, wx.Bitmap('images/wrye_bad.jpg'), dPos, size=(140, 140))
            # Buttons
            self.license_button = wx.Button(self.about_panel, wx.ID_ANY, _(u'License'), dPos, size=(60, 22))
            self.credits_button = wx.Button(self.about_panel, wx.ID_ANY, _(u'Credits'), dPos, size=(60, 22))
            # Contents
            self.contents = rtc.RichTextCtrl(self.about_panel,wx.ID_ANY,u'',dPos,size=(-1,166),style=wx.TE_READONLY|wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS)
            self.contents.SetFocus()
            # URL
            self.home_url = wx.HyperlinkCtrl(self.about_panel,wx.ID_ANY,self.website_po[0],self.website_po[1],dPos,dSize,wx.HL_CONTEXTMENU|wx.HL_DEFAULT_STYLE)
            # Sizers ========================================= #
            AboutImageBtn_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            AboutImage_Sizer = wx.BoxSizer(wx.VERTICAL)
            AboutMain_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            AboutURL_Sizer = wx.BoxSizer(wx.HORIZONTAL)
            About_Sizer = wx.BoxSizer(wx.VERTICAL)
            AboutImageBtn_Sizer.AddMany([(self.license_button,0,wx.RIGHT|wx.LEFT,5),((11,0),0,0,5),(self.credits_button,0,wx.RIGHT|wx.LEFT,5)])
            AboutImage_Sizer.AddMany([(self.wrye_bad,0,wx.ALL,5),(AboutImageBtn_Sizer,0,wx.TOP,5)])
            AboutMain_Sizer.AddMany([(AboutImage_Sizer,0,wx.EXPAND,5),(self.contents,1,wx.ALL|wx.EXPAND,5)])
            AboutURL_Sizer.AddMany([((0,0),1,wx.EXPAND,5),(self.home_url,1,wx.RIGHT|wx.LEFT|wx.EXPAND,5),((0,0),1,wx.EXPAND,5)])
            About_Sizer.AddMany([(self.title,0,wx.EXPAND|wx.RIGHT|wx.LEFT,5),(self.version,0,wx.EXPAND|wx.RIGHT|wx.LEFT,5),
                                 (AboutMain_Sizer,1,wx.EXPAND,5),(AboutURL_Sizer,0,wx.EXPAND,5)])
            self.about_panel.SetSizer(About_Sizer)
            self.about_panel.Layout()
            About_Sizer.Fit(self.about_panel)

        if True:  # Footer
            # Error/Status Messages
            self.Settingstext = wx.StaticText(self, wx.ID_ANY, u'', dPos, dSize, 0)
            # OK/Cancel Buttons
            self.btnOK = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, size=(35, 22), name='btnOK')
            self.btnCancel = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, size=(60, 22), name='btnCancel')
            # Sizers ========================================= #
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
            # Sizers
            self.paths_panel.SetSizer(Paths_Sizer)
            self.paths_panel.Layout()
            Paths_Sizer.Fit(self.paths_panel)
            self.settings_notebook.AddPage(self.general_panel, _(u'General'), True)
            self.settings_notebook.AddPage(self.paths_panel, _(u'Paths'), False)
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
            self.Bind(wx.EVT_CLOSE, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_BUTTON(self, wx.ID_OPEN, self.OpenDialog)
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

    def pos_save(self):
        """Saves the Settings pos."""
        conf.settings['mash.settings.pos'] = self.GetPosition()

    def importThemeList(self):
        """Import theme list."""
        cwd = os.getcwd()
        themedir = os.path.join(cwd, 'themes')
        if not os.path.exists(themedir): os.makedirs(themedir)
        themeList = scandir.listdir(themedir)
        themeData = []*(len(themeList)+1)
        for theme in themeList:
            themePath = os.path.join(themedir, theme)
            with codecs.open(themePath, 'r', 'utf-8') as rawTheme:
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

    def OnCancel(self, event):
        """Cancel button handler."""
        self.pos_save()
        self.timer.Stop()
        self.Destroy()

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

    def chkSpecialPaths(self):
        """Check for changes in paths which need Wrye restart."""
        if not self.openmw:  # Polemos: Regular Morrowind Settings:
            if conf.settings['sInstallersDir'] != self.fldInst.GetValue(): return True
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
        mlox_changed_po = False

        if not self.openmw:  # Polemos: Regular Morrowind Settings:
            if conf.settings['mloxbit']:
                # Polemos: Mloxbit is set to True when auto detection is successful on Program run.
                conf.settings['mloxbit'] = False
            elif self.fldmlox.GetValue() != conf.settings['mloxpath']: mlox_changed_po = True

            conf.settings['mwDir'] = self.fldMw.GetValue()
            conf.settings['mloxpath'] = self.fldmlox.GetValue()
            conf.settings['sInstallersDir'] = self.fldInst.GetValue()

        if self.openmw:  # Polemos: OpenMW/Tes3MP Settings:
            if conf.settings['mlox64path'] != self.fldmlox64.GetValue(): mlox_changed_po = True

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
        self.set_settings()
        self.OnClose(None, mlox_changed_po)

    def OnClose(self, event, mlox_changed_po=False):
        """Notifications on settings close."""
        self.OnCancel(None)
        if mlox_changed_po: conf.settings['mash.toolbar.refresh'] = True
        if any([self.menu_config_po(),
                self.LrgFontEx != self.LrgFont.GetValue(),
                self.ShowErrEx != self.ShowErr.GetValue(),
                self.ThemeChoiceEx != self.ThemeChoiceNew,
                self.pathsRestart
               ]): gui.InfoMessage(self, _(u'Please restart Wrye Mash for changes to take effect.'))

    def InitCommon(self):
        """Init Common Settings."""
        self.Menubar_po.SetValue(conf.settings['mash.menubar.enabled'])
        self.Columns_Menu_po.SetValue(conf.settings['mash.col.menu.enabled'])
        self.HovHigh.SetValue(conf.settings['interface.lists.color'])
        self.LrgFont.SetValue(conf.settings['mash.large.fonts'])
        self.MinOnClose.SetValue(conf.settings['app.min.systray'])
        self.ShowErr.SetValue(conf.settings['show.debug.log'])
        self.ThemeChoice.SetSelection([num for num, x in enumerate(self.themeData) if x[0] == conf.settings['active.theme'][0]][0])
        self.Update_po.SetValue(conf.settings['enable.check'])
        self.fldUpdate.SetValue(conf.settings['timeframe.check'])
        # Items that need Wrye Mash to restart
        self.ShowErrEx = conf.settings['show.debug.log']
        self.LrgFontEx = conf.settings['mash.large.fonts']
        self.ThemeChoiceEx = conf.settings['active.theme']

    def InitSettings(self):
        """Init settings.."""
        self.InitCommon()
        if not self.openmw:  # Polemos: Regular Morrowind Settings:
            for x, y in zip((self.fldMw, self.fldmlox, self.fldInst),
                            (conf.settings['mwDir'], conf.settings['mloxpath'], conf.settings['sInstallersDir'])):
                try: x.SetValue(y)
                except: pass

        if self.openmw:  # Polemos: OpenMW/Tes3MP Settings
            for x, y in zip((self.fldOpenMWloc,self.flddatamods,self.fldDownloads,self.fldOpenMWConf,self.fldDataFiles,self.fldTES3mpConf,self.fldmlox64),
                            (conf.settings['openmwDir'],conf.settings['datamods'],conf.settings['downloads'],
                             os.path.join(conf.settings['openmwprofile'], 'openmw.cfg'),conf.settings['openmw.datafiles'],
                             conf.settings['TES3mpConf'],conf.settings['mlox64path'])):
                try: x.SetValue(y)
                except: pass


class TES3lint_Settings(wx.Dialog):  # Polemos: a new settings window for TES3lint (Maybe I should also create a standalone program out of this).
    """Class for the TES3lint settings window."""

    def __init__(self, parent, pos):
        """The settings mini window."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'TES3lint Settings'), pos=pos, size=(331, 494), style=wx.DEFAULT_DIALOG_STYLE)

        if True:  # Box Sizers
            perl_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Perl Directory:')), wx.HORIZONTAL)
            tesl3int_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'TES3lint Script Location:')), wx.HORIZONTAL)
            custom_flags_teslint_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Custom Flags:')), wx.VERTICAL)
            extras_teslint_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Extra Options (Can create program freezes):')), wx.VERTICAL)
            result_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Final Command:')), wx.HORIZONTAL)

        if True:  # Content
            # Perl Field/Button:
            self.perl_field = wx.TextCtrl(perl_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, wx.TE_NO_VSCROLL)
            self.browse_perl_btn = wx.Button(perl_sizer.GetStaticBox(), wx.ID_ANY, u'...', dPos, dSize, 0)
            # TES3lint Field/Button:
            self.tes3lint_field = wx.TextCtrl(tesl3int_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, wx.TE_NO_VSCROLL)
            self.browse_teslint_btn = wx.Button(tesl3int_sizer.GetStaticBox(), wx.ID_ANY, u'...', dPos, dSize, 0)
            # Recommended Flags:
            flags_radio_boxChoices = [_(u'-n  "normal" output flags on (fastest)'),
                                      _(u' -r  "recommended" output flags on (slow)'),
                                      _(u'-a  all output flags on. (slowest)'),
                                      _(u' -f "flags" specify flags below (separated by comma):')]
            self.flags_radio_box = wx.RadioBox(self, wx.ID_ANY, u'Recommended Lists of Flags:', dPos, dSize, flags_radio_boxChoices, 1, 0)
            self.flags_radio_box.SetSelection(0)
            # Custom Flags:
            self.custom_flags_text = wx.TextCtrl(custom_flags_teslint_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, 0)
            # Extra Options:
            self.debug_checkBox = wx.CheckBox(extras_teslint_sizer.GetStaticBox(), wx.ID_ANY, _(u'-D  "debug" output (vast)'), dPos, dSize, 0)
            self.verbose_checkBox = wx.CheckBox(extras_teslint_sizer.GetStaticBox(), wx.ID_ANY, _(u' -v  "verbose" (possibly more output)'), dPos, dSize, 0)
            # TES3lint result:
            self.final_static = wx.StaticText(result_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, 0)
            self.final_static.Wrap(-1)
            # Buttons
            self.ok_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, dSize, 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, dSize, 0)

        if True:  # Theming
            self.perl_field.SetForegroundColour(wx.Colour(0, 0, 0))
            self.perl_field.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.tes3lint_field.SetForegroundColour(wx.Colour(0, 0, 0))
            self.tes3lint_field.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.custom_flags_text.SetForegroundColour(wx.Colour(0, 0, 0))
            self.custom_flags_text.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.final_static.SetForegroundColour(wx.BLUE)
            self.final_static.SetBackgroundColour(wx.Colour(240, 240, 240))

        if True:  # Layout
            perl_sizer.AddMany([(self.perl_field,1,wx.ALL,5),(self.browse_perl_btn,0,wx.ALL,5)])
            tesl3int_sizer.AddMany([(self.tes3lint_field,1,wx.ALL,5),(self.browse_teslint_btn,0,wx.ALL,5)])
            custom_flags_teslint_sizer.Add(self.custom_flags_text, 0, wx.ALL|wx.EXPAND, 5)
            extras_teslint_sizer.AddMany([(self.debug_checkBox,0,wx.ALL,5),(self.verbose_checkBox,0,wx.ALL,5)])
            result_sizer.Add(self.final_static, 0, wx.ALL|wx.EXPAND, 5)
            buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
            buttons_sizer.AddMany([(self.ok_btn,0,wx.ALL,5),((0,0),1,wx.EXPAND,5),(self.cancel_btn,0,wx.ALL,5)])
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.AddMany([(perl_sizer,0,wx.EXPAND,5),(tesl3int_sizer,0,wx.EXPAND,5),(self.flags_radio_box,0,wx.ALL|wx.EXPAND,5),
                        (custom_flags_teslint_sizer,0,wx.EXPAND, 5),(extras_teslint_sizer,0,wx.EXPAND,5),(result_sizer,0,wx.EXPAND,5),(buttons_sizer,0,wx.EXPAND,5)])
            self.SetSizer(main_sizer)

        if True:  # Events
            self.timer_po()
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            self.ok_btn.Bind(wx.EVT_BUTTON, self.OnOK)
            self.cancel_btn.Bind(wx.EVT_BUTTON, self.OnClose)
            self.browse_perl_btn.Bind(wx.EVT_BUTTON, self.perl_dir)
            self.browse_teslint_btn.Bind(wx.EVT_BUTTON, self.tes3lint_dir)
            self.flags_radio_box.Bind(wx.EVT_RADIOBOX, self.refresh)
            self.Bind(wx.EVT_CHECKBOX, self.refresh)
            self.custom_flags_text.Bind(wx.EVT_TEXT, self.refresh)
            self.tes3lint_field.Bind(wx.EVT_TEXT, self.refresh)

        self.Layout()
        self.import_settings()
        self.ShowModal()

    def refresh(self, event):
        """Refresh command example on dialog."""
        conf.settings['tes3lint.refresh'] = True

    def timer_po(self):
        """A simple timer."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1)

    def import_settings(self):
        """Import settings from conf."""
        self.perl_field.SetValue(conf.settings['tes3lint.perl'])
        self.tes3lint_field.SetValue(conf.settings['tes3lint.location'])
        settings = conf.settings['tes3lint.last']
        self.flags_radio_box.SetSelection(settings[0])
        self.custom_flags_text.SetValue((','.join((unicode(x) for x in settings[1]))).strip('[ ]'))
        self.debug_checkBox.SetValue(settings[2])
        self.verbose_checkBox.SetValue(settings[3])

    def export_settings(self):
        """Export settings to conf."""
        conf.settings['tes3lint.perl'] = self.perl_field.GetValue()
        conf.settings['tes3lint.location'] = self.tes3lint_field.GetValue()
        conf.settings['tes3lint.command.result'] = self.final_static.GetLabelText()
        conf.settings['tes3lint.last'] = [self.flags_radio_box.GetSelection(),
                                          self.getFlags(),
                                          self.debug_checkBox.GetValue(),
                                          self.verbose_checkBox.GetValue()]

    def pos_save(self):
        """Saves the TES3lint Settings pos."""
        conf.settings['tes3lint.pos'] = self.GetPosition()

    def getFlags(self):
        """For better readability in export_settings."""
        return [x.strip() for x in self.custom_flags_text.GetValue().strip().split(u',')]

    def cmd_factory(self):
        """Construct the command status text."""
        conf.settings['tes3lint.refresh'] = False
        radio_box = [u'-n', u'-r', u'-a']
        path = os.path.basename(self.tes3lint_field.GetValue())
        if not path: path = u'tes3lint'
        if self.flags_radio_box.GetSelection() != 3: flags = u'%s' % radio_box[self.flags_radio_box.GetSelection()]
        else: flags = u'-f %s' %  u', '.join(self.getFlags())
        if self.debug_checkBox.GetValue(): extra0 = u'-D'
        else: extra0 = u''
        if self.verbose_checkBox.GetValue(): extra1 = u'-v'
        else: extra1 = u''
        return u' '.join([path, flags, extra0, extra1])

    def switch(self, state):
        """Color switch for flags field (ON/OFF)."""
        self.custom_flags_text.SetEditable(state)
        if not state: color = wx.Colour(240, 240, 240)
        else: color = wx.Colour(255, 255, 255)
        self.custom_flags_text.SetBackgroundColour(color)

    def onUpdate(self, event):
        """Safety check for settings."""
        if self.flags_radio_box.GetSelection() == 3: self.switch(True)
        else: self.switch(False)
        if conf.settings['tes3lint.refresh']: self.final_static.SetLabelText(u'%s %s' % (self.cmd_factory(), _(u'"target_file"')))

    def perl_dir(self, event):
        """..."""
        self.perl_field.SetValue(self.FileDialog(u'Perl', u'Executable files (*.exe)|*.exe', 'perl.exe'))

    def tes3lint_dir(self, event):
        """..."""
        self.tes3lint_field.SetValue(self.FileDialog(u'TES3lint', u'All files (*.*)|*.*', 'tes3lint'))

    def FileDialog(self, name, wildcard, defaultfile):
        """Filepaths for Perl and TES3lint."""
        message = _(u"%s directory selection") % name
        dialog = wx.FileDialog(self, message, '', defaultfile, wildcard, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return u''
        else:
            path = dialog.GetPath()
            dialog.Destroy()
            return path

    def OnClose(self, event):
        """Cancel/Close button handler."""
        self.pos_save()
        self.timer.Stop()
        conf.settings['tes3lint.refresh'] = True
        wx.Dialog.Destroy(self)

    def OnOK(self, event):
        """Ok button handler."""
        self.export_settings()
        self.OnClose('the door')
