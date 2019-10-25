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


# Extension for Wrye Mash Polemos fork ======================================================
#
# Wrye Wizard, Copyright (C) 2018-, Polemos
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================


import codecs
import json
import os
import scandir
import sys
import wx
import dialog as gui
from ..plugins.mlox.loader import Mlox_The_Path
from .. import conf
from ..unimash import _

# Constants
MashDir = os.path.dirname(sys.argv[0])
dPos = wx.DefaultPosition
dSize = wx.DefaultSize
Size = wx.Size
TOP = wx.TOP
BOT = wx.BOTTOM
EXP = wx.EXPAND
LEF = wx.LEFT
RIG = wx.RIGHT
CEN = wx.ALIGN_CENTRE


class WizardDialog(wx.Dialog):
    """Wizard Class."""
    PanelID = 0
    disabled = []

    def __init__(self, title=u'Wrye Mash Polemos fork', pos=dPos, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, parent=None, id=wx.ID_ANY, title=title, pos=pos, size=Size(415, 500), style=style)
        self.Interface_Themes = [x[0] for x in self.importThemeList()]
        self.Encoding_Ch = [('%s, %s' % (x, conf.settings['mash.encodings'][x])) for x in conf.settings['mash.encodings']]
        self.MashDate = conf.settings['mash.version']
        self.SetSizeHints(-1, -1)
        self.WMPF_sword = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(u'images/daggerfall.png',wx.BITMAP_TYPE_ANY), dPos, dSize, 0)

        if True:  # Intro Panel
            # Contents
            self.intro_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.welcome_Text = wx.StaticText(self.intro_panel,wx.ID_ANY,u'',dPos,Size(-1, 60),CEN)
            self.introText1 = wx.StaticText(self.intro_panel, wx.ID_ANY,u'', dPos, Size(-1, 55), CEN)
            self.line_1 = wx.StaticLine(self.intro_panel, wx.ID_ANY, dPos, dSize, wx.LI_HORIZONTAL)
            self.introText2 = wx.StaticText(self.intro_panel, wx.ID_ANY, u'', dPos, Size(-1, 30), CEN)
            self.line_2 = wx.StaticLine(self.intro_panel, wx.ID_ANY, dPos, dSize, wx.LI_HORIZONTAL)
            self.introText3 = wx.StaticText(self.intro_panel, wx.ID_ANY, u'', dPos, Size(-1, 65), CEN)
            self.introText4 = wx.StaticText(self.intro_panel, wx.ID_ANY, u'Wrye Mash %s Polemos fork is under the GPL 2 '
                            u'license or higher. For more information read the included license.' % self.MashDate[3], dPos, Size(-1, 50),CEN)
            self.introText5 = wx.StaticText(self.intro_panel, wx.ID_ANY, _(u'Click Next if you wish to proceed.'), dPos, Size(-1, 30),CEN)
            # Sizers ========================================= #
            introPanSizer = wx.BoxSizer(wx.VERTICAL)
            introPanSizer.AddMany([(self.welcome_Text,0,EXP|wx.ALL,5),(self.introText1,0,EXP|wx.ALL,5),
                (self.line_1,0,EXP,5), (self.introText2,0,wx.ALL,5), (self.line_2,0,EXP|BOT,5), (self.introText3,0,EXP|wx.ALL,5),
                        ((0,0),1,EXP,5),(self.introText4,0,EXP|wx.ALL,5), (self.introText5,0,wx.ALL|EXP,5)])
            self.intro_panel.SetSizer(introPanSizer)
            self.intro_panel.Layout()
            introPanSizer.Fit(self.intro_panel)

        if not conf.settings['openmw']:  # Regular Morrowind support: Main and Optional Paths Panel
            self.mw_1_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.mw1_Text1 = wx.StaticText(self.mw_1_panel, wx.ID_ANY, _(u'Please fill the entries below:'), dPos, Size(-1, 30), CEN)
            # Morrowind directory
            mw_box = wx.StaticBox(self.mw_1_panel, wx.ID_ANY, _(u'1) Morrowind directory:'))
            mw_Sizer = wx.StaticBoxSizer(mw_box, wx.VERTICAL)
            self.fldMw = wx.TextCtrl(mw_box, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldMw')
            self.btnBrowseMw = wx.Button(mw_box, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseMw')
            self.mw_Text = wx.StaticText(mw_box,wx.ID_ANY,_(u'Define  the  directory  of  Morrowind\'s installation.'), dPos, Size(-1,30), 0)
            # Installers directory
            Instbox = wx.StaticBox(self.mw_1_panel, wx.ID_ANY, _(u'2) Mods Installers directory:'))
            InstSizer = wx.StaticBoxSizer(Instbox, wx.VERTICAL)
            self.fldInst = wx.TextCtrl(Instbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldInst')
            self.btnBrowseInst = wx.Button(Instbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseInst')
            self.InstText = wx.StaticText(Instbox, wx.ID_ANY,_(u'Select a folder '
                        u'where your packed mod archives will be stored (zip, rar and 7z).'), dPos, Size(-1, 30), 0)
            # Mlox directory
            Mloxbox = wx.StaticBox(self.mw_1_panel, wx.ID_ANY, _(u'3) Mlox directory (Optional):'))
            Mlox_Sizer = wx.StaticBoxSizer(Mloxbox, wx.VERTICAL)
            self.fldmlox = wx.TextCtrl(Mloxbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldmlox')
            self.btnBrowsemlox = wx.Button(Mloxbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowsemlox')
            self.MloxText1 = wx.StaticText(Mloxbox, wx.ID_ANY, _(u'If you are using Mlox '
                        u'standalone (exe) you may define it\'s location here.'), dPos, Size(-1, 30), 0)
            self.MloxText2 = wx.StaticText(Mloxbox, wx.ID_ANY,_(u'If Mlox\'s folder '
                        u'is inside Morrowind\'s you may try to autodetect it below.'), dPos, Size(-1, 30), 0)
            self.detect_Mlox_button = wx.Button(Mloxbox, wx.ID_ANY, u'Try to Detect Mlox Location', dPos, dSize, 0)
            # Sizers ========================================= #
            mw_te3mp_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Downloads_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Mods_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            mw_1_Sizer = wx.BoxSizer(wx.VERTICAL)
            mw_te3mp_BrwSizer.AddMany([(self.fldMw, 1, 0, 5), (self.btnBrowseMw, 0, 0, 5)])
            mw_Sizer.AddMany([(mw_te3mp_BrwSizer, 0, EXP, 5), (self.mw_Text, 0, TOP|BOT, 5)])
            Downloads_BrwSizer.AddMany([(self.fldInst, 1, 0, 5), (self.btnBrowseInst, 0, 0, 5)])
            InstSizer.AddMany([(Downloads_BrwSizer, 0, EXP, 5), (self.InstText, 0, TOP|BOT, 5)])
            Mods_BrwSizer.AddMany([(self.fldmlox, 1, 0, 5), (self.btnBrowsemlox, 0, 0, 5)])
            Mlox_Sizer.AddMany([(Mods_BrwSizer,0,EXP,5),(self.MloxText1,0,TOP|BOT,5),(self.MloxText2,0,TOP|BOT,5),
                        (self.detect_Mlox_button,0,EXP|TOP|BOT,5)])
            mw_1_Sizer.AddMany([(self.mw1_Text1,0,EXP|LEF|RIG,5),(mw_Sizer,0,EXP|LEF|RIG,5),((0,0),1,0,5),
                        (InstSizer,0,EXP|LEF|RIG,5),((0,0),1,0,5),(Mlox_Sizer, 0,EXP|LEF|RIG,5),((0,0),1,0,5)])
            self.mw_1_panel.SetSizer(mw_1_Sizer)
            self.mw_1_panel.Layout()
            mw_1_Sizer.Fit(self.mw_1_panel)

        if conf.settings['openmw']:  # OpenMW/TES3mp support: Main Paths Panel
            self.openmw_1_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.openmw1_Text1 = wx.StaticText(self.openmw_1_panel, wx.ID_ANY, _(u'Please fill the entries below:'), dPos, Size(-1, 30), CEN)
            # OpenMW/TES3mp directory
            openmw_te3mpbox = wx.StaticBox(self.openmw_1_panel, wx.ID_ANY, _(u'1) OpenMW/TES3mp directory:'))
            openmw_te3mpSizer = wx.StaticBoxSizer(openmw_te3mpbox, wx.VERTICAL)
            self.fldOpenMWloc = wx.TextCtrl(openmw_te3mpbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldOpenMWloc')
            self.btnBrowseOpenMWloc = wx.Button(openmw_te3mpbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseOpenMWloc')
            self.Openmw_te3mpText = wx.StaticText(openmw_te3mpbox, wx.ID_ANY,_(u'Select '
                        u'the location of OpenMW and/or TES3mp installation.'),dPos,Size(-1,30),0)
            # Downloads directory
            Downloadsbox = wx.StaticBox(self.openmw_1_panel, wx.ID_ANY, _(u'2) Downloads directory:'))
            DownloadsSizer = wx.StaticBoxSizer(Downloadsbox, wx.VERTICAL)
            self.fldDownloads = wx.TextCtrl(Downloadsbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldDownloads')
            self.btnBrowseDownloads = wx.Button(Downloadsbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseDownloads')
            self.DownloadsText = wx.StaticText(Downloadsbox, wx.ID_ANY,_(u'Select '
                        u'the folder where your packed mod archives will be stored (zip, rar and 7z).'), dPos, Size(-1, 30), 0)
            # Mods directory
            Modsbox = wx.StaticBox(self.openmw_1_panel, wx.ID_ANY, _(u'3) Mods directory:'))
            ModsSizer = wx.StaticBoxSizer(Modsbox, wx.VERTICAL)
            self.flddatamods = wx.TextCtrl(Modsbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='flddatamods')
            self.btnBrowsedatamods = wx.Button(Modsbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowsedatamods')
            self.ModsText = wx.StaticText(Modsbox,wx.ID_ANY,_(u'Select a '
                        u'folder where your activated (and unpacked) mod (Data) folders will reside.'),dPos, Size(-1, 30), 0)
            # Sizers ========================================= #
            Openmw_te3mp_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Downloads_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Mods_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            openmw_1_Sizer = wx.BoxSizer(wx.VERTICAL)
            Openmw_te3mp_BrwSizer.AddMany([(self.fldOpenMWloc, 1, 0, 5), (self.btnBrowseOpenMWloc, 0, 0, 5)])
            openmw_te3mpSizer.AddMany([(Openmw_te3mp_BrwSizer, 0, EXP, 5),(self.Openmw_te3mpText, 0, TOP|BOT, 5)])
            Downloads_BrwSizer.AddMany([(self.fldDownloads, 1, 0, 5),(self.btnBrowseDownloads, 0, 0, 5)])
            DownloadsSizer.AddMany([(Downloads_BrwSizer, 0, EXP, 5),(self.DownloadsText, 0, TOP|BOT, 5)])
            Mods_BrwSizer.AddMany([(self.flddatamods, 1, 0, 5), (self.btnBrowsedatamods, 0, 0, 5)])
            ModsSizer.AddMany([(Mods_BrwSizer, 0, EXP, 5),(self.ModsText, 0, TOP|BOT, 5)])
            openmw_1_Sizer.AddMany([(self.openmw1_Text1,0,EXP|wx.ALL,5),(openmw_te3mpSizer,0,EXP|wx.ALL,5),((0,0),1,0,5),(DownloadsSizer,0,EXP|wx.ALL,5),
                                    ((0,0),1,0,5),(ModsSizer, 0,EXP|wx.ALL,5),((0,0),1,0,5)])
            self.openmw_1_panel.SetSizer(openmw_1_Sizer)
            self.openmw_1_panel.Layout()
            openmw_1_Sizer.Fit(self.openmw_1_panel)

        if conf.settings['openmw']:  # OpenMW/TES3mp support: Openmw.cfg Error Panel
            self.openmw_2_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.openmw2_Text1 = wx.StaticText(self.openmw_2_panel, wx.ID_ANY,_(u'Please define OpenMW Profile Location:'), dPos,Size(-1, 35), CEN)
            # openmw.cfg location
            Openmwcfgbox = wx.StaticBox(self.openmw_2_panel, wx.ID_ANY, _(u'openmw.cfg file location:'))
            OpenmwcfgSizer = wx.StaticBoxSizer(Openmwcfgbox, wx.VERTICAL)
            self.fldOpenMWConf = wx.TextCtrl(Openmwcfgbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldOpenMWConf')
            self.btnBrowseOpenMWConf = wx.Button(Openmwcfgbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseOpenMWConf')
            # Info
            self.openmw2_Text2 = wx.StaticText(Openmwcfgbox, wx.ID_ANY,_(u'You need to define openmw.cfg location to proceed.'), dPos,Size(-1, 30), 0)
            self.openmw2_Text3 = wx.StaticText(Openmwcfgbox, wx.ID_ANY,_(u'Note: You need to have run OpenMW '
                        u'atleast once in the past for OpenMW to create it\'s configuration files (openmw.cfg in our case).'),dPos, Size(-1, 60), 0)
            self.openmw2_Text4 = wx.StaticText(Openmwcfgbox,wx.ID_ANY,_(u'If you haven\'t run OpenMW before, '
                    u'you may try the following:'),dPos,Size(-1,30),0)
            self.openmw2_Text5 = wx.StaticText(Openmwcfgbox, wx.ID_ANY, _(u'1) Run OpenMW Launcher\n2) Configure it\n3) Click the button '
                    u'below for Wrye Mash to retry locating openmw.cfg.'),dPos, Size(-1, 60), 0)
            self.detect_openmwcfg_button = wx.Button(Openmwcfgbox, wx.ID_ANY, _(u'Try to Detect openmw.cfg'),dPos, dSize, 0)
            # Sizers ========================================= #
            Openmwcfg_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            openmw_2_Sizer = wx.BoxSizer(wx.VERTICAL)
            Openmwcfg_BrwSizer.AddMany([(self.fldOpenMWConf, 1, 0, 5), (self.btnBrowseOpenMWConf, 0, 0, 5)])
            OpenmwcfgSizer.AddMany([(Openmwcfg_BrwSizer,1,EXP,5),(self.openmw2_Text2,0,TOP|BOT,5),(self.openmw2_Text3,0,TOP|BOT,5),
                    (self.openmw2_Text4,0,TOP|BOT,5),(self.openmw2_Text5,0,TOP|BOT,5),((0,0),1,EXP,5),(self.detect_openmwcfg_button,0,EXP,5)])
            openmw_2_Sizer.AddMany([(self.openmw2_Text1, 0, EXP|wx.ALL, 5),(OpenmwcfgSizer, 1, EXP|wx.ALL, 5)])
            self.openmw_2_panel.SetSizer(openmw_2_Sizer)
            self.openmw_2_panel.Layout()
            openmw_2_Sizer.Fit(self.openmw_2_panel)

        if conf.settings['openmw']:  # OpenMW/TES3mp support: Optional Settings Panel
            self.openmw_3_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.openmw3_Text = wx.StaticText(self.openmw_3_panel, wx.ID_ANY, _(u'Optional Settings:'), dPos,Size(-1, 28), CEN)
            # Morrowind Data Files
            OpenDataFilesbox = wx.StaticBox(self.openmw_3_panel, wx.ID_ANY, _(u'Morrowind Data Files:'))
            OpenDataFilesSizer = wx.StaticBoxSizer(OpenDataFilesbox,wx.VERTICAL)
            self.fldDataFiles = wx.TextCtrl(OpenDataFilesbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldDataFiles')
            self.btnBrowseDataFiles = wx.Button(OpenDataFilesbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseDataFiles')
            self.OpenDataFilesSizerText = wx.StaticText(OpenDataFilesbox, wx.ID_ANY, _(u'For better integration with Wrye Mash '
                    u'it is recommended to define here the location of Morrowind\'s "Data Files".'),dPos, Size(-1, 43), 0)
            # TES3mp
            Tes3mpbox = wx.StaticBox(self.openmw_3_panel, wx.ID_ANY, _(u'TES3mp: (Not Ready Yet)'))
            Tes3mpSizer = wx.StaticBoxSizer(Tes3mpbox, wx.VERTICAL)
            self.Tes3mp_checkBox = wx.CheckBox(Tes3mpbox, wx.ID_ANY, _(u'Enable TES3mp.'), dPos, dSize, 0)
            self.fldTES3mpConf = wx.TextCtrl(Tes3mpbox, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldTES3mpConf')
            self.btnBrowseTES3mpConf = wx.Button(Tes3mpbox, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowseTES3mpConf')
            self.Tes3mpText = wx.StaticText(Tes3mpbox, wx.ID_ANY,_(u'Define pluginlist.json location or click the button below.'),dPos, Size(-1, 30), 0)
            self.detect_Tes3mp_button = wx.Button(Tes3mpbox, wx.ID_ANY, _(u'Try to Detect pluginlist.json'),dPos, dSize, 0)
            # Mlox64
            Mlox64box = wx.StaticBox(self.openmw_3_panel, wx.ID_ANY, _(u'Mlox64: (Not Ready Yet)'))
            Mlox64_Sizer = wx.StaticBoxSizer(Mlox64box ,wx.VERTICAL)
            self.fldmlox64 = wx.TextCtrl(Mlox64box, wx.ID_ANY, u'', dPos, Size(-1, 21), wx.TE_READONLY, name='fldmlox64')
            self.btnBrowsemlox64 = wx.Button(Mlox64box, wx.ID_OPEN, u'...', dPos, Size(-1, 21), wx.BU_EXACTFIT, name='btnBrowsemlox64')
            self.Mlox64Text = wx.StaticText(Mlox64box, wx.ID_ANY,_(u'If you are using Mlox64 you may define it\'s location here.'),dPos, Size(-1, 30), 0)
            self.detect_Mlox64_button = wx.Button(Mlox64box, wx.ID_ANY, _(u'Try to Detect Mlox64 Location'), dPos, dSize, 0)
            # Sizers ========================================= #
            OpenDataFiles_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Tes3mp_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            Mlox64_BrwSizer = wx.BoxSizer(wx.HORIZONTAL)
            openmw_3_Sizer = wx.BoxSizer(wx.VERTICAL)
            OpenDataFiles_BrwSizer.AddMany([(self.fldDataFiles, 1, 0, 5), (self.btnBrowseDataFiles, 0, 0, 5)])
            OpenDataFilesSizer.AddMany([(OpenDataFiles_BrwSizer, 0, EXP, 5),(self.OpenDataFilesSizerText, 0, wx.ALL, 5)])
            Tes3mp_BrwSizer.AddMany([(self.fldTES3mpConf, 1, 0, 5), (self.btnBrowseTES3mpConf, 0, 0, 5)])
            Tes3mpSizer.AddMany([(self.Tes3mp_checkBox,0,BOT|RIG|LEF,5),(Tes3mp_BrwSizer,0,EXP,5),
                                                    (self.Tes3mpText,0,wx.ALL,5),(self.detect_Tes3mp_button,0,EXP,5)])
            Mlox64_BrwSizer.AddMany([(self.fldmlox64, 1, 0, 5), (self.btnBrowsemlox64, 0, 0, 5)])
            Mlox64_Sizer.AddMany([(Mlox64_BrwSizer, 0, EXP, 5),(self.Mlox64Text, 0, wx.ALL, 5),(self.detect_Mlox64_button, 0, EXP, 5)])
            openmw_3_Sizer.AddMany([(self.openmw3_Text,0,EXP,5),(OpenDataFilesSizer,0,EXP|RIG|LEF,5),((0,0),1,EXP,5),
                                            (Tes3mpSizer,0,EXP|RIG|LEF,5),((0,0),1,EXP,5),(Mlox64_Sizer,0,EXP|RIG|LEF,5)])
            self.openmw_3_panel.SetSizer(openmw_3_Sizer)
            self.openmw_3_panel.Layout()
            openmw_3_Sizer.Fit(self.openmw_3_panel)

        if True: # Last Panel
            self.end_panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.EndText1 = wx.StaticText(self.end_panel, wx.ID_ANY, _(u'Misc Settings:'), dPos, Size(-1, 28),CEN)
            # Update Settings
            Updatebox = wx.StaticBox(self.end_panel, wx.ID_ANY, _(u'Update Settings:'))
            UpdateSizer = wx.StaticBoxSizer(Updatebox, wx.VERTICAL)
            self.UpdateText1 = wx.StaticText(Updatebox, wx.ID_ANY,_(u'Would you like to be notified when '
                        u'the next Wrye Mash version is released?'),dPos, Size(-1, 30), 0)
            self.Update_checkBox = wx.CheckBox(Updatebox, wx.ID_ANY, _(u'Enable Notifications:'+(' '*62)),dPos, dSize, wx.ALIGN_RIGHT)
            self.UpdateSpnText = wx.StaticText(Updatebox, wx.ID_ANY, _(u'Frequency in Days (0=Everyday):'),dPos, dSize, 0)
            self.Update_spinCtrl = wx.SpinCtrl(Updatebox, wx.ID_ANY, u'', dPos,Size(45, -1), wx.SP_ARROW_KEYS|wx.SP_WRAP, 0, 365, 15)
            # Interface Settings
            Interfacebox = wx.StaticBox(self.end_panel, wx.ID_ANY, _(u'Interface Settings:'))
            InterfaceSizer = wx.StaticBoxSizer(Interfacebox, wx.VERTICAL)
            self.InterfaceText = wx.StaticText(Interfacebox, wx.ID_ANY, _(u'Choose a Theme for Wrye Mash:'),dPos, Size(-1, 20), 0)
            self.Interface_choices = wx.Choice(Interfacebox, wx.ID_ANY, dPos, dSize, self.Interface_Themes, 0)
            # Encoding Settings
            Encodingbox = wx.StaticBox(self.end_panel, wx.ID_ANY, _(u'Encoding Settings:'))
            EncodingSizer = wx.StaticBoxSizer(Encodingbox, wx.VERTICAL)
            self.EncodingText = wx.StaticText(Encodingbox,wx.ID_ANY,_(u'Choose '
                        u'an Encoding (Useful for Translated Versions of Morrowind):'),dPos,Size(-1, 30),0)
            self.Encoding_choices = wx.Choice(Encodingbox, wx.ID_ANY, dPos, dSize, self.Encoding_Ch, 0)
            # Info
            self.EndText2 = wx.StaticText(self.end_panel, wx.ID_ANY,_(u'Click Finish to save your settings and launch Wrye Mash.'),dPos, Size(-1, 30), CEN)
            self.EndText3 = wx.StaticText(self.end_panel, wx.ID_ANY, _(u'(You can always change your settings later).'),dPos, Size(-1, 30), CEN)
            # Sizers ========================================= #
            Update_SpnSizer = wx.BoxSizer(wx.HORIZONTAL)
            EndSizer = wx.BoxSizer(wx.VERTICAL)
            Update_SpnSizer.AddMany([(self.UpdateSpnText, 1, TOP, 5),(self.Update_spinCtrl, 0, 0, 5)])
            UpdateSizer.AddMany([(self.UpdateText1,0,wx.ALL,5),(self.Update_checkBox,0,BOT,5),(Update_SpnSizer,0,EXP|TOP,5)])
            InterfaceSizer.AddMany([(self.InterfaceText, 0, wx.ALL, 5),(self.Interface_choices, 0, EXP|BOT, 5)])
            EncodingSizer.AddMany([(self.EncodingText, 0, wx.ALL, 5),(self.Encoding_choices, 0, EXP|BOT, 5)])
            EndSizer.AddMany([(self.EndText1,0,EXP,5),(UpdateSizer,0,EXP|wx.ALL,5),((0,0),1,0,5),(EncodingSizer,0,EXP|wx.ALL,5),((0,0),1,0,5),
                (InterfaceSizer,0,EXP|wx.ALL,5),((0,0),1,EXP,5),(self.EndText2,0,wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,5),
                        (self.EndText3,0,wx.UP|BOT|wx.ALIGN_CENTER_HORIZONTAL,5)])
            self.end_panel.SetSizer(EndSizer)
            self.end_panel.Layout()
            EndSizer.Fit(self.end_panel)

        if True:  # Footer
            # Contents
            self.mainLine = wx.StaticLine(self, wx.ID_ANY, dPos, dSize, wx.LI_HORIZONTAL)
            self.back_button = wx.Button(self, wx.ID_BACKWARD, u'<Back', dPos, Size(75, -1), 0)
            self.next_Fin_button = wx.Button(self, wx.ID_FORWARD, u'Next>', dPos, Size(75, -1), 0)
            self.cancel_Quit__button = wx.Button(self, wx.ID_CANCEL, u'Quit', dPos, Size(75, -1), 0)
            # Sizers ========================================= #
            footerSizer = wx.BoxSizer(wx.HORIZONTAL)
            footerSizer.AddMany([(self.back_button,0,wx.ALL,5),(self.next_Fin_button,0,wx.ALL,5),((0,0),1,EXP,5),(self.cancel_Quit__button,0,wx.ALL,5)])

        if True:  # Themes
            # Common
            self.introText2.SetForegroundColour(wx.Colour(255, 0, 0))
            self.EndText2.SetForegroundColour(wx.BLUE)
            if not conf.settings['openmw']:  # Regular Morrowind support
                self.fldMw.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldMw.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.fldInst.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldInst.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.fldmlox.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldmlox.SetBackgroundColour(wx.Colour(255, 255, 255))
            if conf.settings['openmw']:  # OpenMW/TES3mp support
                self.fldOpenMWloc.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldOpenMWloc.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.fldDownloads.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldDownloads.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.flddatamods.SetForegroundColour(wx.Colour(0, 0, 0))
                self.flddatamods.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.fldOpenMWConf.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldOpenMWConf.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.openmw2_Text4.SetForegroundColour(wx.Colour(0, 0, 255))
                self.fldDataFiles.SetForegroundColour(wx.Colour(0, 0, 0))
                self.fldDataFiles.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True: # =================== Disabled Items ====================== #
            # Common
            if conf.settings['openmw']:  # OpenMW/TES3mp support
                # TES3mp
                Tes3mpbox.SetForegroundColour(wx.Colour(160, 160, 160))
                Tes3mpbox.Disable()
                # Mlox64
                Mlox64box.SetForegroundColour(wx.Colour(160, 160, 160))
                Mlox64box.Disable()
                # =================== Disabled Items ====================== #

        if True:  # Sizers
            panelsSizer = wx.BoxSizer(wx.VERTICAL)
            panelsSizer.Add(self.intro_panel, 1, EXP|TOP|BOT|RIG, 5)
            if not conf.settings['openmw']:  # Regular Morrowind support
                panelsSizer.AddMany([(self.mw_1_panel,1,EXP|TOP,5)])  # If in need of more panels.
            if conf.settings['openmw']:  # OpenMW/TES3mp support
                panelsSizer.AddMany([(self.openmw_1_panel,1,EXP|TOP,5),(self.openmw_2_panel,1,EXP,5),(self.openmw_3_panel,1,EXP|TOP|BOT,5)])
            panelsSizer.Add(self.end_panel, 1, EXP|TOP|BOT, 5)
            contentsSizer = wx.BoxSizer(wx.HORIZONTAL)
            contentsSizer.AddMany([(self.WMPF_sword, 0, TOP|BOT, 5),(panelsSizer, 1, EXP, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(contentsSizer,1,EXP,5),(self.mainLine,0,EXP|RIG|LEF,5),(footerSizer,0,EXP,5)])
            self.SetSizer(mainSizer)
            self.Layout()
            self.SetMinSize(Size(340, 500))
            self.Centre(wx.BOTH)

        if True:  # Wizard Panel Data
            if not conf.settings['openmw']:  # Regular Morrowind support
                self.wizard_fields = (self.fldMw, self.fldInst)
                self.PanelData = {0: [self.intro_panel, None, None],
                                  1: [self.mw_1_panel, _(u'Please fill the entries below:'), self.mw1_Text1],
                                  2: [self.end_panel , None, None]}

            if conf.settings['openmw']:      # OpenMW/TES3mp support
                self.wizard_fields = (self.fldOpenMWloc, self.flddatamods, self.fldDownloads, self.fldDataFiles)
                self.PanelData = {0: [self.intro_panel, None, None],
                                  1: [self.openmw_1_panel, _(u'Please fill the entries below:'), self.openmw1_Text1],
                                  2: [self.openmw_2_panel, _(u'Please define OpenMW Profile Location:'), self.openmw2_Text1],
                                  3: [self.openmw_3_panel, _(u'Optional Settings:'), self.openmw3_Text ],
                                  4: [self.end_panel , _(u'Misc Settings:'), self.EndText1]}

        if True:  # Init Conditions
            self.LastPanel = len(self.PanelData) - 1
            self.allows = False
            self.openmwcfg_detect = None
            self.setFonts()
            self.txtwraps()
            self.InitSettings()
            self.init_content()
            self.end_panel.Hide()
            self.back_button.Disable()
            # Panels
            if not conf.settings['openmw']:  # Regular Morrowind support
                self.mw_1_panel.Hide()
            if conf.settings['openmw']:  # OpenMW/TES3mp support
                self.openmw_1_panel.Hide()
                self.openmw_2_panel.Hide()
                self.openmw_3_panel.Hide()

        if True: # Events
            self.timer_po()
            self.Bind(wx.EVT_CLOSE, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_BACKWARD, self.OnBack)
            wx.EVT_BUTTON(self, wx.ID_FORWARD, self.OnNextFin)
            wx.EVT_BUTTON(self, wx.ID_OPEN, self.OpenDialog)
            wx.EVT_TEXT(self, wx.ID_ANY, self.ColorSwitch)
            if not conf.settings['openmw']:  # Morrowind support
                self.detect_Mlox_button.Bind(wx.EVT_BUTTON, self.detect_mlox)
            if conf.settings['openmw']:  # OpenMW/TES3mp support
                self.detect_openmwcfg_button.Bind(wx.EVT_BUTTON, self.detect_openmwcfg)

    def init_content(self):
        """Variable Text Data."""
        if not conf.settings['openmw']:  # Regular Morrowind
            t1 = _(u'Welcome to Wrye Mash %s Configuration Wizard.' % self.MashDate[3])
            t2 = _(u'This wizard will help you configure all the settings needed to use Wrye Mash with Morrowind. ')
            t3 = _(u"")
            t4 = _(u"")
            self.line_1.Hide()
            self.line_2.Hide()
            self.detect_Mlox_button.Disable()
        if conf.settings['openmw']:  # OpenMW/TES3mp
            t1 = _(u'Welcome to Wrye Mash %s OpenMW/TES3mp Configuration Wizard.' % self.MashDate[3])
            t2 = _(u'This wizard will help you configure all the settings needed to use Wrye Mash with OpenMW and/or TES3mp. ')
            t3 = _(u'NOTE: This an Alpha/"Work in progress" version.')
            t4 = _(u'Since this is an Alpha/"Work in Progress" many features are not implemented and bugs may roam in every corner.  Use at your own risk.')
        #  Display
        self.welcome_Text.SetLabel(t1)
        self.introText1.SetLabel(t2)
        self.introText2.SetLabel(t3)
        self.introText3.SetLabel(t4)
        self.RefPan()

    def importThemeList(self):
        """Import theme list."""
        themedir = os.path.join(MashDir, 'themes')
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

    def timer_po(self):
        """A simple timer to check for problems in the Wizard."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1)

    def RefPan(self):
        """Refresh selected Panel's layout."""
        Panel = self.PanelData[self.PanelID][0]
        Panel.Layout()
        Panel.Refresh()

    def chkdisabled(self):
        """Enabled/Disabled check switch."""
        if self.PanelID in set(self.disabled):
            if self.next_Fin_button.IsEnabled():
                self.next_Fin_button.Disable()
        else:
            if not self.next_Fin_button.IsEnabled():
                self.next_Fin_button.Enable()

    def onUpdate(self, event):
        """Safety check for settings."""
        # Check for Errors
        self.chkdisabled()
        if not conf.settings['openmw']:  # Regular Morrowind Rules
            # Panel 1: Empty fields check
            if all([self.check_empty(),1 not in self.disabled]): self.disabled.append(1)
            elif all([not self.check_empty(),1 in self.disabled, self.check_conflicts()]): self.disabled.remove(1)
            if all([self.check_empty(), self.detect_Mlox_button.IsEnabled()]): self.detect_Mlox_button.Disable()
            elif all([not self.check_empty(), not self.detect_Mlox_button.IsEnabled()]): self.detect_Mlox_button.Enable()
            # Panel 1: Dir conflict check
            if self.allows:
                for x, y in zip(self.PanelData, (1,)):
                    if not self.check_conflicts():
                        self.PanelData[y][2].SetLabel(_(u'Conflicts in folder paths.'))
                        self.PanelData[y][2].SetForegroundColour(wx.RED)
                        if 1 not in self.disabled: self.disabled.append(1)
                    else:
                        self.PanelData[y][2].SetLabel(self.PanelData[y][1])
                        self.PanelData[y][2].SetForegroundColour(wx.BLACK)
                        if 1 in self.disabled: self.disabled.remove(1)
        if conf.settings['openmw']:  # OpenMW/TES3mp Rules
            # Panel 1: Empty fields check
            if all([self.check_empty(), 1 not in self.disabled]): self.disabled.append(1)
            elif all([not self.check_empty(), 1 in self.disabled]): self.disabled.remove(1)
            # Panel 2: Empty field check
            if all([self.check_empty(self.fldOpenMWConf), 2 not in self.disabled]): self.disabled.append(2)
            elif all([not self.check_empty(self.fldOpenMWConf), 2 in self.disabled]): self.disabled.remove(2)
            # Panel 2: openmw.cfg field check
            if self.PanelID == 2:
                if all([self.openmwcfg_detect is not None, self.allows]):
                    self.PanelData[self.PanelID][2].SetLabel(_(u'Success!') if self.openmwcfg_detect else _(u'Failed to detect OpenMW Profile.'))
                    self.detect_openmwcfg_button.SetLabel(_(u'Success!') if self.openmwcfg_detect else _(u'Failed to detect OpenMW Profile.'))
                    self.PanelData[self.PanelID][2].SetForegroundColour(wx.BLUE if self.openmwcfg_detect else wx.RED)
                    self.detect_openmwcfg_button.SetForegroundColour(wx.BLUE if self.openmwcfg_detect else wx.RED)
            # Panel 1, 3: Dir conflict check
            if self.allows:
                for x, y in zip(self.PanelData, (1, 3)):
                    if not self.check_conflicts():
                        self.PanelData[y][2].SetLabel(_(u'Conflicts in folder paths.'))
                        self.PanelData[y][2].SetForegroundColour(wx.RED)
                        if 3 not in self.disabled: self.disabled.append(3)
                    else:
                        self.PanelData[y][2].SetLabel(self.PanelData[y][1])
                        self.PanelData[y][2].SetForegroundColour(wx.BLACK)
                        if 3 in self.disabled: self.disabled.remove(3)
        # Common
        [x.Disable() if not self.Update_checkBox.IsChecked() else x.Enable() for x in (self.UpdateSpnText, self.Update_spinCtrl)]
        # Refresh Panel
        if self.allows:
            self.RefPan()
            self.allows = False

    def ColorSwitch(self, event):
        self.check_conflicts('color')
        self.allows = True

    def check_conflicts(self, mode='check'):
        """Check for conflicts in path fields or check and colorize their fields.."""
        values = [x.GetValue().rstrip('\\ ').lower() for x in self.wizard_fields if x.GetValue().rstrip('\\ ')]
        if mode == 'check': return len(set(values)) == len(values)
        conflicts = {x for x in values if values.count(x) > 1}
        [x.SetForegroundColour(wx.RED) if x.GetValue().rstrip('\\ ').lower() in conflicts else x.SetForegroundColour(wx.BLACK) for x in self.wizard_fields]
        self.RefPan()

    def check_empty(self, field=None):
        """Check for empty path fields."""
        if not conf.settings['openmw'] and field is None:  # Morrowind
            check = [x.GetValue().rstrip(' ') for x in self.wizard_fields]
            return False if all(check) else True
        elif conf.settings['openmw'] and field is None:  # OpenMW/Tes3MP
            check = [x.GetValue().rstrip(' ') for x in self.wizard_fields if x is not self.fldDataFiles]
            return False if all(check) else True
        else:  # Specific field check
            return False if field.GetValue() else True

    def check_folders(self, folder, showmsg=False):
        """Check if declared folder is a valid Morrowind or OpenMW/TES3mp folder (when possible)."""
        def show(data):
            if not showmsg: return data[3]
            data[0].SetLabel(data[2])
            data[0].SetForegroundColour(data[1])
            return data[3]
        # Rules
        if folder == 'fldMw':  # Morrowind Path Check
            try:
                if all([os.path.isfile(os.path.join(self.fldMw.GetValue(), 'Morrowind.ini')),
                        os.path.isdir(os.path.join(self.fldMw.GetValue(), 'Data files'))]):
                    return show([self.mw_Text, wx.BLUE, _(u'Success: morrowind.ini and "Data files" folder found.'), True])
            except: pass
            return show([self.mw_Text, wx.RED, _(u'Are you sure this is Morrowind\'s directory? (Ignore if you are sure).'), False])
        if folder == 'fldOpenMWloc':  # OpenMW Path Check
            try:
                if all([os.path.isfile(os.path.join(self.fldOpenMWloc.GetValue(), 'openmw-launcher.exe'))]):
                    return show([self.Openmw_te3mpText, wx.BLUE, _(u'Success: OpenMW Launcher found (openmw-launcher.exe).'), True])
            except: pass
            return show([self.Openmw_te3mpText, wx.RED, _(u'Are you sure this is OpeMW/TES3mp directory? (Ignore if you are sure).'), False])
        if folder == 'fldOpenMWConf':  # OpenMW Path Check
            try:
                chk_ok = False
                if os.path.basename((self.fldOpenMWConf.GetValue()).rstrip('\\')) == 'openmw.cfg': return True
                if os.path.isfile(os.path.join(os.path.dirname(self.fldOpenMWConf.GetValue()).rstrip('\\'), 'openmw.cfg')): chk_ok = True
            except: pass
            self.fldOpenMWConf.SetValue(u'')
            if chk_ok: return show([self.openmw2_Text2, wx.RED, _(u'Error: OpenMW Profile path MUST contain "openmw.cfg"!'), False])
            return show([self.openmw2_Text2, wx.RED, _(u'Invalid path: OpenMW Profile folder MUST contain "openmw.cfg" file!'), False])

    def detect_openmwcfg(self, event):
        """Detect OpenMW profile directory."""
        try:
            user = os.environ['USERPROFILE']
            openmwcfg = os.path.join(user, 'Documents', 'my games', 'openmw', 'openmw.cfg')
            if os.path.exists(openmwcfg):
                self.fldOpenMWConf.SetValue(openmwcfg)
                self.openmwcfg_detect = True
                self.openmw2_Text2.SetLabel(u"")
            else: self.openmwcfg_detect = False
        except: self.openmwcfg_detect = False
        self.ColorSwitch(None)

    def detect_mlox(self, event):
        """Try to detect mlox dir."""
        def fail():
            self.detect_Mlox_button.SetLabel(_(u'Failed to detect Mlox.exe'))
            self.detect_Mlox_button.SetForegroundColour(wx.RED)
        if self.check_folders('fldMw'): MWdir = self.fldMw.GetValue()
        else: fail()
        avoid = [x for x in
                [self.fldInst.GetValue() if os.path.isdir(self.fldInst.GetValue()) else None,
                 MashDir, os.path.join(self.fldMw.GetValue(), 'Data files')]
                 if x is not None]
        try:
            result = Mlox_The_Path('mlox.exe', avoid, MWdir)
            if os.path.isfile(result):
                self.fldmlox.SetValue(result)
                self.detect_Mlox_button.SetLabel(_(u'Success!'))
                self.detect_Mlox_button.SetForegroundColour(wx.BLUE)
            else: fail()
        except: fail()

    def OpenDialog(self, event):
        """Choosing files or directories."""
        name = event.EventObject.Name[9:]
        if any((conf.dataMap[name].endswith(x) for x in ['.exe','.cfg','.py','.json','.ini','pl'])):
            for x in ['.exe','.cfg','.py','.json','.ini','pl']:
                if conf.dataMap[name].endswith(x): ext = x
            dialog = wx.FileDialog(self, _(u'Select %s file location:') % conf.dataMap[name].capitalize(),
                                   '', '%s' % conf.dataMap[name], u'Files (*%s)|*%s' % (ext,ext), style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                return
            else:
                path = dialog.GetPath()
                dialog.Destroy()
        else:
            dialog = wx.DirDialog(self, _(u'%s directory selection') % conf.dataMap[name].capitalize())
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                return
            path = dialog.GetPath()
            dialog.Destroy()
        getattr(self, 'fld%s' % name).SetValue(path)
        self.check_folders('fld%s' % name, True)

    def OnBack(self, event):
        """Back button handler."""
        if self.PanelID != 0: self.PanelID -= 1
        CurPanel = self.PanelData[self.PanelID][0]
        NextPanel = self.PanelData[self.PanelID + 1][0]
        if self.PanelID == 0:
            self.back_button.Disable()
            self.cancel_Quit__button.SetLabel(u'Quit')
        if self.next_Fin_button.GetLabel() != u'Next>': self.next_Fin_button.SetLabel(u'Next>')
        NextPanel.Hide()
        CurPanel.Show()
        self.Layout()

    def OnNextFin(self, event):
        """Next/Finish button handler."""
        maxPanel = self.LastPanel
        if self.PanelID < maxPanel:
            self.PanelID += 1
            CurPanel = self.PanelData[self.PanelID][0]
            PrevPanel = self.PanelData[self.PanelID - 1][0]
            if self.PanelID == maxPanel: self.next_Fin_button.SetLabel(u'Finish')
            if not self.back_button.IsEnabled(): self.back_button.Enable()
            if self.cancel_Quit__button.GetLabel() != u'Cancel': self.cancel_Quit__button.SetLabel(u'Cancel')
            PrevPanel.Hide()
            CurPanel.Show()
            self.Layout()
        else: self.SaveSettings()

    def SaveSettings(self):
        """Save user settings."""
        conf.settings['enable.check'] = self.Update_checkBox.GetValue()
        conf.settings['timeframe.check'] = self.Update_spinCtrl.GetValue()
        conf.settings['asked.check'] = True
        conf.settings['active.theme'] = [x for num, x in enumerate(self.themeData) if num == self.Interface_choices.GetSelection()][0]
        conf.settings['profile.encoding'] = [enc for enc in conf.settings['mash.encodings'] if enc in
                    [x for num, x in enumerate(self.Encoding_Ch) if num == self.Encoding_choices.GetSelection()][0]][0]

        if not conf.settings['openmw']:  # Regular Morrowind
            conf.settings['mwDir'] = self.fldMw.GetValue()
            conf.settings['mloxpath'] = self.fldmlox.GetValue()
            conf.settings['sInstallersDir'] = self.fldInst.GetValue()

        if conf.settings['openmw']:  # OpenMW/Tes3MP
            conf.settings['openmwDir'] = self.fldOpenMWloc.GetValue()
            conf.settings['datamods'] = self.flddatamods.GetValue()
            conf.settings['downloads'] = self.fldDownloads.GetValue()
            conf.settings['openmwprofile'] = os.path.dirname(self.fldOpenMWConf.GetValue())
            conf.settings['openmw.datafiles'] = self.fldDataFiles.GetValue()
            conf.settings['TES3mpConf'] = self.fldTES3mpConf.GetValue()
            conf.settings['mlox64path'] = self.fldmlox64.GetValue()

        self.OnClose(True)

    def OnClose(self, result):
        """Close actions."""
        self.timer.Stop()
        self.Destroy()
        self.EndModal(result)

    def OnCancel(self, event):
        warning = _(u'Are you sure you wish to Quit?\n\nAll your changes will be lost!!!')
        if gui.WarningQuery(self, warning, _(u'Are you sure?')) == wx.ID_YES: self.OnClose(False)
        else: return

    def InitSettings(self):
        """Init settings.."""
        self.Update_checkBox.SetValue(conf.settings['enable.check'])
        self.Update_spinCtrl.SetValue(conf.settings['timeframe.check'])
        self.Interface_choices.SetSelection([num for num, x in enumerate(self.themeData) if x[0] == conf.settings['active.theme'][0]][0])
        self.Encoding_choices.SetSelection([num for num, x in enumerate(self.Encoding_Ch) if conf.settings['profile.encoding'] in x][0])

        if not conf.settings['openmw']:  # Regular Morrowind
            try: self.fldMw.SetValue(conf.settings['mwDir'])
            except: pass
            try: self.fldmlox.SetValue(conf.settings['mloxpath'])
            except: pass
            try: self.fldInst.SetValue(conf.settings['sInstallersDir'])
            except: pass

        if conf.settings['openmw']:  # OpenMW/Tes3MP
            try: self.fldOpenMWloc.SetValue(conf.settings['openmwDir'])
            except: pass
            try: self.flddatamods.SetValue(conf.settings['datamods'])
            except: pass
            try: self.fldDownloads.SetValue(conf.settings['downloads'])
            except: pass
            try: self.fldOpenMWConf.SetValue(os.path.join(conf.settings['openmwprofile'], 'openmw.cfg'))
            except: pass
            try: self.fldDataFiles.SetValue(conf.settings['openmw.datafiles'])
            except: pass
            try: self.fldTES3mpConf.SetValue(conf.settings['TES3mpConf'])
            except: pass
            try: self.fldmlox64.SetValue(conf.settings['mlox64path'])
            except: pass

    def txtwraps(self):
        """Text form."""
        # Common
        [x.Wrap(-1) for x in (self.welcome_Text,self.introText1,self.introText2,self.introText3,self.introText4,self.introText5,
                              self.EndText1,self.UpdateText1,self.UpdateSpnText,self.InterfaceText,self.EndText2,self.EndText3)]
        if not conf.settings['openmw']:  # Regular Morrowind support
            [x.Wrap(-1) for x in (self.mw1_Text1,self.mw_Text,self.InstText,self.MloxText1)]
        if conf.settings['openmw']:  # OpenMW/TES3mp support
            [x.Wrap(-1) for x in (self.openmw1_Text1,self.Openmw_te3mpText,self.DownloadsText,self.ModsText,self.openmw2_Text1,
                                  self.openmw2_Text2,self.openmw2_Text3,self.openmw2_Text4,self.openmw2_Text5,self.openmw3_Text,
                                  self.OpenDataFilesSizerText,self.Tes3mpText,self.Mlox64Text)]

    def setFonts(self):
        # Types
        BigFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, '@Arial Unicode MS')
        RegBoldFont = wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, u'')
        RegFont = wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False, u'')
        # Common
        self.welcome_Text.SetFont(BigFont)
        self.introText2.SetFont(RegBoldFont)
        self.introText4.SetFont(RegFont)
        self.introText5.SetFont(RegBoldFont)
        self.EndText1.SetFont(BigFont)
        self.EndText2.SetFont(RegBoldFont)
        if not conf.settings['openmw']:  # Regular Morrowind support
            self.mw1_Text1.SetFont(BigFont)
            self.btnBrowseMw.SetFont(RegFont)
            self.btnBrowseInst.SetFont(RegFont)
            self.btnBrowsemlox.SetFont(RegFont)
        if conf.settings['openmw']:  # OpenMW/TES3mp support
            # Panel 1
            self.openmw1_Text1.SetFont(BigFont)
            self.btnBrowseOpenMWloc.SetFont(RegFont)
            self.btnBrowseDownloads.SetFont(RegFont)
            self.btnBrowsedatamods.SetFont(RegFont)
            # Panel 2
            self.openmw2_Text1.SetFont(BigFont)
            self.btnBrowseOpenMWConf.SetFont(RegFont)
            self.openmw2_Text3.SetFont(RegBoldFont)
            self.openmw2_Text4.SetFont(RegBoldFont)
            # Panel 3
            self.openmw3_Text.SetFont(BigFont)
            self.btnBrowseDataFiles.SetFont(RegFont)
            self.btnBrowseTES3mpConf.SetFont(RegFont)
            self.btnBrowsemlox64.SetFont(RegFont)
