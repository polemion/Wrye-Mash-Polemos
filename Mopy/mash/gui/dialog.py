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


import wx, os, io
import time
from time import strftime as timestamp
from .. import conf, singletons, mosh
from shutil import copyfile
from ..unimash import _  # Polemos
from ..mprofile import profilePaths as profilePaths
import wx.lib.dialogs as wx_dialogs_po  # Polemos
import wx.html  # Polemos
import interface  # Polemos


dPos = wx.DefaultPosition
dSize = wx.DefaultSize
Size = wx.Size


def chkChars(text_val, strict=False):
    """Check for illegal characters and replace."""
    nope = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for x in nope:
        if not strict: text_val = text_val.replace(x, '_')
        else: text_val = text_val.replace(x, '')
    return text_val.strip(' ')


def setIcon(parent, imgPath=None):
    """Set icon of caller window."""
    if imgPath is None:
        appICO = wx.Icon(os.path.join('images', 'Wrye Mash.ico'))
    else: appICO = wx.Icon(imgPath)
    parent.SetIcon(appICO)


class ProgressDialog(mosh.Progress):  # Polemos: fix for newer wxpythons.
    """Prints progress to file (stdout by default)."""

    def __init__(self,title=_(u'Progress'),message='',parent=None, interval=0.1):
        """Init."""
        style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.STAY_ON_TOP
        self.dialog = wx.ProgressDialog(title,message,100,parent,style)
        mosh.Progress.__init__(self,interval)
        self.isDestroyed = False

    def doProgress(self, progress, message):
        """Progress bar."""
        if self.dialog:
            self.dialog.Update(int(progress*100), message)
            wx.Yield()
        else: pass

    def Destroy(self):
        """On exit."""
        if self.dialog:
            self.dialog.Destroy()
            self.dialog = None


class WaitDialog(wx.BusyInfo, wx.BusyCursor):
    """A busy dialog."""

    def __init__(self, window, message):
        """Init."""
        disableAll = wx.WindowDisabler()
        wx.BusyInfo.__init__(self, message, window)
        wx.BusyCursor.__init__(self)

    def exit(self):
        """On exit."""
        del self


class GaugeDialog(wx.Dialog):  # Polemos
    """A custom progress dialog."""

    def __init__(self, parent, message=_(u'Please wait...'), title=_(u'Progress...'), max=100):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=(382, 96), style=wx.CAPTION|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        self.max = max

        if True: # Contents
            self.mainPanel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.message = wx.StaticText(self.mainPanel, wx.ID_ANY, message, dPos, dSize, 0)
            self.gauge = wx.Gauge(self.mainPanel, wx.ID_ANY, max, dPos, dSize, wx.GA_HORIZONTAL|wx.GA_SMOOTH)
            self.gauge.SetValue(0)

        if True: # Theme
            self.mainPanel.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.message.Wrap(-1)

        if True: # Layout
            contentsSizer = wx.BoxSizer(wx.VERTICAL)
            contentsSizer.AddMany([(self.message,0,wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT,10),
                ((0,0),1,wx.EXPAND,5),(self.gauge,0,wx.EXPAND|wx.ALL,10)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.Add(self.mainPanel, 1, wx.EXPAND, 5)
            self.mainPanel.SetSizer(contentsSizer)
            self.mainPanel.Layout()
            contentsSizer.Fit(self.mainPanel)
            self.SetSizer(mainSizer)
            self.Layout()

        if True: # Event
            wx.EVT_CLOSE(self, self.OnClose)

    def OnClose(self, event):
        """On close."""
        pass

    def set_msg(self, msg):
        """Set custom message."""
        self.message.SetLabel(msg)

    def update(self, num):
        """Update gauge."""
        self.gauge.SetValue(num) if self.max else self.gauge.Pulse()


class netProgressDialog:  # Polemos
    """Progress dialog for Nash (internet module) update."""

    def __init__(self, caption=_(u'Please wait...'), message=_(u'Checking for new version...'), maximum=5, parent=None):
        """Init."""
        self.dialog = wx.ProgressDialog(caption, message, maximum, parent, style=wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE)

    def doProgress(self, progress, message):
        """Show progress dialog."""
        self.dialog.Update(progress, message)
        wx.Yield()

    def update(self, counter=1):
        """Update dialog, on 5th step destroy."""
        self.doProgress(counter, _(u'Checking for new version...'))
        if counter == 5: self.Destroy()

    def Destroy(self):
        self.doProgress(5, _(u'Finished...'))
        self.dialog.Destroy()


class ConflictDialog(wx.Dialog):  # Polemos
    """A file-tree copy resolution dialog."""
    GetData = False

    def __init__(self, parent, modName, title=_(u'Target folder already exists...')):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=Size(507, 129), style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        self.modName = modName

        if True:  # Contents
            self.panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.warn_bmp = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap('images/warning.png', wx.BITMAP_TYPE_ANY), dPos, dSize, 0)
            self.textQ = wx.StaticText(self.panel, wx.ID_ANY,
                                _(u'A mod folder with the same name already exists. How do you wish to proceed?'), dPos, Size(-1, -1), 0)
            self.textMod = wx.TextCtrl(self.panel, wx.ID_ANY, modName, dPos, Size(-1, 20), 0|wx.SIMPLE_BORDER|wx.TE_PROCESS_ENTER)
            self.chkBox = wx.CheckBox(self, wx.ID_ANY, _(u'Backup existing mod...'), dPos, dSize, 0)
            # Buttons
            self.rename_btn = wx.Button(self.panel, wx.ID_ANY, _(u'Rename mod:'), dPos, Size(95, 22), 0)
            self.overwrite_btn = wx.Button(self, wx.ID_ANY, _(u'Overwrite...'), dPos, Size(85, 22), 0)
            self.replace_btn = wx.Button(self, wx.ID_ANY, _(u'Replace...'), dPos, Size(75, 22), 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, Size(55, 22), 0)

        if True:  # Theming
            self.panel.SetForegroundColour(wx.Colour(0, 0, 0))
            self.panel.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.textMod.SetForegroundColour(wx.Colour(0, 0, 0))
            self.textMod.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True:  # Layout
            self.textQ.Wrap(-1)
            self.overwrite_btn.SetDefault()
            modSizer = wx.BoxSizer(wx.HORIZONTAL)
            modSizer.AddMany([(self.rename_btn, 0, wx.ALL, 5), (self.textMod, 1, wx.ALL|wx.ALIGN_CENTER, 5)])
            textSizer = wx.BoxSizer(wx.VERTICAL)
            textSizer.AddMany([(self.textQ, 1, wx.ALL, 5),(modSizer, 0, wx.EXPAND, 5)])
            contentSizer = wx.BoxSizer(wx.HORIZONTAL)
            contentSizer.AddMany([(self.warn_bmp,1,wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND,5),(textSizer,1,wx.EXPAND|wx.ALL,5)])
            self.panel.SetSizer(contentSizer)
            self.panel.Layout()
            contentSizer.Fit(self.panel)
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.chkBox,0,wx.ALIGN_CENTER_VERTICAL|wx.ALL,5),
                              ((0,0),1,wx.EXPAND,5), (self.overwrite_btn, 0, wx.ALL, 5), (self.replace_btn, 0, wx.ALL, 5), (self.cancel_btn, 0, wx.ALL, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(self.panel, 1, wx.EXPAND, 5),(btnSizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True:  # Events
            self.rename_btn.Bind(wx.EVT_BUTTON, self.renameMod)
            self.overwrite_btn.Bind(wx.EVT_BUTTON, self.overwriteMod)
            self.replace_btn.Bind(wx.EVT_BUTTON, self.replaceMod)
            self.textMod.Bind(wx.EVT_TEXT_ENTER, self.renameMod)

        self.ShowModal()

    def SetData(self, action):
        """Set data to return and exit dialog."""
        modName = chkChars(self.textMod.GetValue())
        self.GetData = (self.chkBox.GetValue(), modName, action)
        self.Destroy()

    def renameMod(self, event):
        """Set Rename."""
        self.SetData('rename')

    def overwriteMod(self, event):
        """Set Merge."""
        self.SetData('overwrite')

    def replaceMod(self, event):
        """Set Replace."""
        self.SetData('replace')


def TextEntry(parent, message, default=''):
    """Shows a text entry dialog and returns result or None if canceled."""
    dialog = wx.TextEntryDialog(parent, message, default)
    if dialog.ShowModal() != wx.ID_OK:
        dialog.Destroy()
        return None
    else:
        value = dialog.GetValue()
        dialog.Destroy()
        return value


def askdialog(parent, question, caption, cnl=False):  # Polemos
    """Shows a modal yes/no dialog and return the resulting answer (True/False)."""
    style = wx.YES_NO|wx.ICON_QUESTION|wx.STAY_ON_TOP
    if cnl: style = style|wx.CANCEL
    dialog = wx.MessageDialog(parent, question, caption, style=style).ShowModal()
    return dialog


def DirDialog(parent, message=_(u'Choose a directory.'), defaultPath=''):  # Polemos
    """Shows a modal directory dialog and return the resulting path, or None if canceled."""
    with wx.DirDialog(parent, message, defaultPath, style=wx.DD_NEW_DIR_BUTTON) as dialog:
        dialog.ShowModal()
        path = dialog.GetPath()
    return None if not path else path


def FileDialog(parent, message=_(u'Choose a file.'), defaultPath='', defaultfile='', wildcard=_(u'Executable files (*.exe)|*.exe')):  # Polemos
    """Shows a modal find file dialog and returns the resulting file path and filename or None if canceled."""
    with wx.FileDialog(parent, message, defaultPath, defaultfile, wildcard, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dialog:
        dialog.ShowModal()
        path, filename = dialog.GetPath(), dialog.GetFilename()
    return None if not path else (path, filename)


def ContinueQuery(parent, tmessage, message, continueKey, title=_(u'Warning'), nBtn=True):  # Polemos
    """Shows a modal continue query if value of continueKey is false. Returns True to continue.
        Also provides checkbox "Don't show this in future." to set continueKey to true."""
    # Init actions
    if conf.settings.get(continueKey): return wx.ID_OK
    # Init Dialog
    style = wx.CAPTION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.STAY_ON_TOP
    dialog = wx.Dialog(parent, id=wx.ID_ANY, title=title, pos=dPos, size=wx.Size(-1, -1), style=style)
    dialog.SetSizeHints(-1, -1)
    # Content
    cntBox = wx.StaticBox(dialog, wx.ID_ANY, '')
    title = wx.StaticText(cntBox, wx.ID_ANY, tmessage, dPos, dSize, 0)
    main = wx.StaticText(cntBox, wx.ID_ANY, message, dPos, dSize, 0)
    okBtn = wx.Button(dialog, wx.ID_OK, _(u'OK' if not nBtn else u'Yes'), dPos, dSize, 0)
    show = wx.CheckBox(dialog, wx.ID_ANY, _(u' Don\'t show this in the future.'), dPos, dSize, 0)
    cnlBtn = wx.Button(dialog, wx.ID_CANCEL, _(u'No'), dPos, dSize, 0)
    # Theming
    dialog.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
    dialog.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
    bold = wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, '')
    title.SetFont(bold)
    # Layout
    if not nBtn: cnlBtn.Hide()
    main.SetMinSize(wx.Size(-1, 100))
    [x.SetMaxSize(wx.Size(380, -1)) for x in (title, main)]
    [x.Wrap(-1) for x in (title, main)]
    cntSizer = wx.StaticBoxSizer(cntBox, wx.VERTICAL)
    cntSizer.AddMany([(title,0,wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL,5),(main,1,wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.RIGHT|wx.LEFT,5)])
    btnSizer = wx.BoxSizer(wx.HORIZONTAL)
    btnSizer.AddMany([(okBtn, 0, wx.ALL, 5), (show, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5), (cnlBtn, 0, wx.ALL, 5)])
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.AddMany([(cntSizer, 1, wx.EXPAND|wx.RIGHT|wx.LEFT, 5),(btnSizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)])
    dialog.SetSizer(mainSizer)
    dialog.Layout()
    mainSizer.Fit(dialog)
    # --Get continue key setting and return
    result = dialog.ShowModal()
    if result: conf.settings[continueKey] = show.GetValue()
    return result


def LogMessage(parent, message, logText,title=u'', style=0, asDialog=True):
    """Query Dialog."""
    pos = conf.settings.get('mash.message.log.pos', dPos)
    size = conf.settings.get('mash.message.log.size', (400, 400))
    if asDialog: window = wx.Dialog(parent,-1,title, pos=pos,size=size,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
    else:
        window = wx.Frame(parent,-1,title,pos=pos,size=(200,300), style=wx.RESIZE_BORDER|wx.CAPTION|wx.SYSTEM_MENU|wx.CLOSE_BOX|wx.CLIP_CHILDREN)
        window.SetIcons(singletons.images['mash.main.ico'].GetIconBundle())
    window.SetSizeHints(200,200)
    sizer = wx.BoxSizer(wx.VERTICAL)
    if message: sizer.Add(wx.StaticText(window,-1,message),0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP,6)
    textCtrl = wx.TextCtrl(window,-1,logText,style=wx.TE_READONLY|wx.TE_MULTILINE)
    sizer.Add(textCtrl,1,wx.EXPAND)
    window.SetSizer(sizer)
    if asDialog:
        window.ShowModal()
        #--Done
        conf.settings['mash.message.log.pos'] = window.GetPosition()
        conf.settings['mash.message.log.size'] = window.GetSizeTuple()
        window.Destroy()
    else: window.Show()


class WelcomeDialog(wx.Dialog):  # Polemos
    """Shows a welcome message."""

    def __init__(self, parent, headtext, detailstext, title=_(u'Welcome!!!')):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=(389,141),style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)

        if True:  # Contents
            bad_wrye = wx.StaticBitmap(panel, wx.ID_ANY, wx.Bitmap('images/wr_b_mini.png', wx.BITMAP_TYPE_ANY), dPos, dSize, 0)
            headline = wx.StaticText(panel, wx.ID_ANY, headtext, dPos, dSize, 0)
            details = wx.StaticText(panel, wx.ID_ANY, detailstext, dPos, dSize, 0)
            okBtn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, Size(65, 23), 0)

        if True:  # Theming
            panel.SetBackgroundColour(wx.Colour(255, 255, 255))
            headline.SetForegroundColour(wx.Colour(0, 0, 160))
            headline.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, u''))

        if True:  # Layout
            textSizer = wx.BoxSizer(wx.VERTICAL)
            textSizer.AddMany([(headline, 0, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, 10),(details, 0, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, 10)])
            panelSizer = wx.BoxSizer(wx.HORIZONTAL)
            panelSizer.AddMany([(bad_wrye, 0, wx.EXPAND|wx.LEFT, 5),(textSizer, 1, wx.EXPAND|wx.RIGHT|wx.LEFT, 5)])
            buttonSizer = wx.BoxSizer(wx.VERTICAL)
            buttonSizer.Add(okBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 8)
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.AddMany([(panel, 1, wx.EXPAND, 5), (buttonSizer, 0, wx.EXPAND, 5)])
            panel.SetSizer(panelSizer)
            panel.Layout()
            panelSizer.Fit(panel)
            self.SetSizer(main_sizer)
            self.Layout()
            self.Centre(wx.BOTH)

        if True:  # Events
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_CLOSE(self, self.OnCancel)

    def OnCancel(self, event):
        """On cancel."""
        self.Destroy()

    def OnOk(self, event):
        """On OK."""
        self.EndModal(True)
        self.Destroy()


class ModInstallDialog(wx.Dialog):  # Polemos
    """Mod Installation dialog."""
    GetModData = None, None
    data_files = ''

    def __init__(self, parent, modname, data_files, package_data, package_name_data, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'Mod Installation...'), pos=dPos, size=Size(419, 85), style=style)
        self.package_data = package_data
        self.data_files = data_files
        self.package_name_data = package_name_data

        if True:  # Contents
            # Main
            self.text = wx.StaticText(self, wx.ID_ANY, _(u'Mod Name:     '), dPos, Size(-1, -1), 0)
            self.mod_name = wx.TextCtrl(self, wx.ID_ANY, u'', dPos, Size(-1, 20), 0|wx.SIMPLE_BORDER)
            self.mod_name.SetLabel(modname)
            # Buttons
            self.advanced_btn = wx.Button(self, wx.ID_ANY, _(u'Advanced'), dPos, Size(75, 21), 0)
            self.ok_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, Size(35, 21), 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, Size(60, 21), 0)

        if True:  # Theming
            self.SetForegroundColour(wx.Colour(0, 0, 0))
            self.SetBackgroundColour(wx.Colour(224, 224, 224))
            self.text.SetForegroundColour(wx.Colour(0, 0, 0))
            self.text.SetBackgroundColour(wx.Colour(224, 224, 224))
            self.mod_name.SetForegroundColour(wx.Colour(0, 0, 0))
            self.mod_name.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True:  # Layout
            self.SetSizeHints(-1, -1)
            self.text.Wrap(-1)
            contentSizer = wx.BoxSizer(wx.HORIZONTAL)
            contentSizer.AddMany([(self.text, 0, wx.ALIGN_CENTER, 5),(self.mod_name, 1, 0, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([((0,0),1,0,5),(self.advanced_btn,0,wx.RIGHT,5),(self.ok_btn,0,wx.RIGHT,5),(self.cancel_btn,0,wx.RIGHT,5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(contentSizer, 0, wx.ALL|wx.EXPAND, 5),(btnSizer, 0, wx.EXPAND, 5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True:  # Events
            self.advanced_btn.Bind(wx.EVT_BUTTON, self.advanced)
            self.mod_name.Bind(wx.EVT_TEXT_ENTER, self.OnOk)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_CLOSE(self, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.ShowModal()

    def advanced(self, event):
        """Call Package Explorer"""
        explorer = ArchiveExplorer(self.package_data, self.data_files)
        data_files = explorer.GetTreeValue
        if data_files is None: return
        else: self.data_files = data_files

    def OnCancel(self, event):
        self.Destroy()

    def OnOk(self, event):
        if isinstance(self.data_files, basestring): self.data_files = [self.data_files]
        self.mod_name.SetValue(chkChars(self.mod_name.GetValue()))
        self.GetModData = self.data_files[0],  self.mod_name.GetValue()
        self.Destroy()


class RenameDialog(wx.Dialog):  # Polemos
    """Rename target."""
    GetModName = False

    def __init__(self, parent, oldName, title=_(u'Rename mod...'), style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=Size(450, 107), style=style)
        self.SetSizeHints(-1, -1)
        self.oldName = oldName
        if True: # Contents
            self.text = wx.StaticText(self, wx.ID_ANY, _(u'Please select a new mod name:'), dPos, dSize, 0)
            self.field = wx.TextCtrl(self, wx.ID_ANY, u'', dPos, Size(-1, 20), 0|wx.SIMPLE_BORDER)
            self.rename_btn = wx.Button(self, wx.ID_ANY, _(u'Rename'), dPos, Size(65, 22), 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, Size(60, 22), 0)
        if True: # Theming
            self.field.SetForegroundColour(wx.Colour(0, 0, 0))
            self.field.SetBackgroundColour(wx.Colour(255, 255, 255))
        if True: # Layout
            self.text.Wrap(-1)
            self.cancel_btn.SetDefault()
            contentSizer = wx.BoxSizer(wx.VERTICAL)
            contentSizer.AddMany([(self.text, 0, wx.EXPAND|wx.ALL, 5),(self.field, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.rename_btn, 0, wx.ALL, 5), (self.cancel_btn, 0, wx.ALL, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(contentSizer, 1, wx.EXPAND, 5),(btnSizer, 0, wx.ALIGN_RIGHT, 5)])
            self.SetSizer(mainSizer)
            self.Layout()
        if True: # Actions
            self.rename_btn.Bind(wx.EVT_BUTTON, self.OnRename)
            self.field.SetLabel(oldName)
            self.timer_po()
            self.ShowModal()

    def timer_po(self):
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        if self.field.GetValue() == u'' or self.field.GetValue().lower() == self.oldName.lower(): self.rename_btn.Disable()
        else: self.rename_btn.Enable()

    def OnCancel(self, event):
        self.timer.Stop()
        self.Destroy()

    def OnRename(self, event):
        self.GetModName = chkChars(self.field.GetValue(), True)
        self.timer.Stop()
        self.Destroy()


def InfoMessage(parent, message, title=_(u'Information'), style=(wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP)):
    """Shows a modal information message."""
    return Message(parent, message, title, style)


def ManualDetectDialog(parent, message, title=u'', style=wx.YES_NO|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP|wx.CANCEL):  # Polemos
    """Manually or autodetect dialog."""
    with wx.MessageDialog(parent, message, title, style) as dialog:
        dialog.SetYesNoLabels(_(u'Try to autodetect'), _(u'Manual search'))
        result = dialog.ShowModal()
    return result


def WarningQuery(parent, message, title=u'', style=(wx.YES_NO|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP)):
    """Shows a modal warning message."""
    return Message(parent, message, title, style)


def WarningMessage(parent, message, title=_(u'Warning'), style=(wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP)):
    """Shows a modal warning message."""
    return Message(parent, message, title, style)


def ErrorQuery(parent, message, title=u'', style=(wx.YES_NO|wx.ICON_HAND|wx.STAY_ON_TOP)):  # Polemos
    """Shows a modal warning/error message."""
    return Message(parent, message, title, style)


def ErrorMessage(parent, message, title=_(u'Error'), style=(wx.OK|wx.ICON_HAND|wx.STAY_ON_TOP), dtype='error', modal=True):
    """Shows a modal error message."""
    return Message(parent, message, title, style) if modal else MessageU(parent, message, dtype, title, modal)


def Message(parent, message, title=u'', style=wx.OK|wx.STAY_ON_TOP):
    """Shows a modal MessageDialog. Use ErrorMessage, WarningMessage or InfoMessage."""
    with wx.MessageDialog(parent, message, title, style) as dialog:
        result = dialog.ShowModal()
    return result


class MessageU(wx.Dialog):
    """An experimental modal/nonmodal themable message dialog."""
    count = 6

    def __init__(self, parent, message, dtype, title=u'', modal=True, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):  # Polemos
        """Init."""
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=title, pos=dPos, size=Size(526, 140), style=style)
        self.SetSizeHints(-1, -1)
        message = message.split('\n\n')
        if len(message) > 1: hmsg, msg = message[0], '\n\n'.join(message[1:])
        else: hmsg, msg = message[0], ''
        mode = {'error': (wx.ART_ERROR, wx.ART_MESSAGE_BOX)}

        if True:  # Content
            panel = wx.Panel(self, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            sign = wx.StaticBitmap(panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(mode[dtype][0], mode[dtype][1]), dPos, dSize, 0)
            headTxt = wx.StaticText(panel, wx.ID_ANY, hmsg, dPos, dSize, 0)
            mainTxt = wx.StaticText(panel, wx.ID_ANY, msg, dPos, dSize, 0)
            self.okBtn = wx.Button(self, wx.ID_OK, _(u'OK (%s)'%self.count), dPos, dSize, 0)

        if True:  # Theming
            self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            panel.SetBackgroundColour(wx.Colour(255, 255, 255))
            sign.SetBackgroundColour(wx.Colour(255, 255, 255))
            headTxt.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, ''))
            headTxt.SetForegroundColour(wx.Colour(0, 0, 170))

        if True:  # Layout
            [x.Wrap(-1) for x in (headTxt, mainTxt)]
            txtSizer = wx.BoxSizer(wx.VERTICAL)
            txtSizer.AddMany([(headTxt, 1, wx.EXPAND|wx.ALL, 5),(mainTxt, 1, wx.EXPAND|wx.ALL, 5)])
            cntSizer = wx.BoxSizer(wx.HORIZONTAL)
            cntSizer.AddMany([(sign, 0, wx.ALL, 5), (txtSizer, 1, wx.EXPAND, 5)])
            panel.SetSizer(cntSizer)
            panel.Layout()
            cntSizer.Fit(panel)
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(panel, 1, wx.EXPAND|wx.BOTTOM, 5), (self.okBtn, 0, wx.ALL|wx.ALIGN_RIGHT, 5)])
            self.SetSizer(mainSizer)
            self.Layout()
            self.ShowModal() if modal else self.Show()

        if not modal:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
            self.timer.Start(1000)

    def onUpdate(self, event):
        """Timer events."""
        if self.count == 0:
            self.timer.Destroy()
            self.Destroy()
        else:
            self.count -= 1
            self.okBtn.SetLabel(_(u'OK (%s)'%self.count))


class ScrolledtextMessage(wx.Dialog):  # Polemos
    """Shows a non modal or modal MessageDialog with a scrollbar and an OK button."""

    def __init__(self, window, msg, caption, modal):
        """Init."""
        wx.Dialog.__init__(self, window)
        self.dialog = wx_dialogs_po.ScrolledMessageDialog(window, msg, caption)
        if modal: self.dialog.ShowModal()
        if not modal: self.dialog.Show()

    def Destroy(self):
        """On exit."""
        self.dialog.Destroy()


class MaxCharDialog(wx.Dialog):  # Polemos
    """A modal dialog with max characters check."""
    init = True

    def __init__(self, title, maxchar, current, caption, parent=None, size=(400, 200), pos=dPos, style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE):
        """Init."""
        wx.Dialog.__init__(self, parent=parent, id=wx.ID_ANY, size=size, pos=pos, style=style)

        self.maxchar = maxchar
        self.SetTitle(title)
        self.current = current

        if True:  # Contents
            captionBox = wx.StaticBox(self, wx.ID_ANY, caption)
            self.fld_po = wx.TextCtrl(captionBox, wx.ID_ANY, current, dPos, dSize, wx.TE_MULTILINE)
            self.fldchars = wx.TextCtrl(captionBox, wx.ID_ANY, self.char_remain(), dPos, dSize, wx.TE_READONLY)
            self.btnOK = wx.Button(captionBox, wx.ID_OK, _(u'OK'), dPos, (-1,22), 0)
            btnCancel = wx.Button(captionBox, wx.ID_CANCEL, _(u'Cancel'), dPos, (-1,22), 0)
        if True:  # Layout
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.btnOK, 0, 0, 5),((0, 0), 1, 0, 5),(self.fldchars, 0, 0, 5),((0, 0), 1, 0, 5),(btnCancel, 0, 0, 5)])
            mainSizer = wx.StaticBoxSizer(captionBox, wx.VERTICAL)
            mainSizer.AddMany([(self.fld_po, 1, wx.EXPAND, 5),(btnSizer, 0, wx.EXPAND|wx.TOP, 5)])
            self.SetSizer(mainSizer)
            self.Layout()
        if True:  # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            self.fld_po.Bind(wx.EVT_TEXT, self.char_update)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_SIZE(self, self.OnSize)

        self.timer_po()
        self.ShowModal()

    def timer_po(self):
        """Timer."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def char_remain(self):
        """Show remaining chars."""
        current = _(u'Chars: %s of %s' % (len(self.fld_po.GetValue()), self.maxchar))
        return current

    def char_update(self, event):
        """On char change events."""
        self.fldchars.ChangeValue(self.char_remain())

    def onUpdate(self, event):
        """Timer events."""
        if len(self.fld_po.GetValue()) > self.maxchar: self.btnOK.Disable()
        else: self.btnOK.Enable()

    def OnSize(self, event):
        """Change size events."""
        self.Layout()
        if self.init:
            self.SetSizeHints(*self.GetSize())
            self.init = False

    def OnCancel(self, event):
        """On clicking Cancel events."""
        self.fin_val_po = self.current
        self.timer.Stop()
        self.Destroy()

    def OnOk(self, event):
        """On clicking OK events."""
        self.fin_val_po = self.fld_po.GetValue()
        self.timer.Stop()
        self.Destroy()

    def GetValue(self):
        """Return final value."""
        return self.fin_val_po


class date_time_dialog(wx.Dialog):  # Polemos
    """Shows a Date/Time multi field spinner Dialog."""

    def __init__(self, parent, title, caption, datetime, id=wx.ID_ANY, size=(418, 258), pos=dPos):
        """Init."""
        wx.Dialog.__init__(self, parent=parent, id=id, title=title, pos=pos, size=size, style=wx.CAPTION|wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.datetime = datetime
        year, month, day, hour, min, sec = time.strptime(datetime, '%m-%d-%Y %H:%M:%S')[0:6]
        self.curDT = '%s/%s/%s, %s:%s:%s' % (month, day, year, hour, min, sec)
        self.timer_po()

        if True:  # Contents
            # Title
            self.info = wx.StaticText(self, wx.ID_ANY, caption, dPos, dSize, 0)
            # Date
            dateBox = wx.StaticBox(self, wx.ID_ANY, _(u'Date:'))
            self.month_static = wx.StaticText(dateBox, wx.ID_ANY, _(u'Month:'), dPos, dSize, 0)
            self.month = wx.SpinCtrl(dateBox,wx.ID_ANY,u'',dPos,Size(65,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,1,12,month)
            self.day_static = wx.StaticText(dateBox,wx.ID_ANY,_(u'Day:'),dPos,dSize,0)
            self.day = wx.SpinCtrl(dateBox,wx.ID_ANY,u'',dPos,Size(65,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,1,31,day)
            self.year_static = wx.StaticText(dateBox,wx.ID_ANY,_(u'Year:'),dPos, dSize,0)
            self.year = wx.SpinCtrl(dateBox,wx.ID_ANY,u'',dPos,Size(85,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,1970,2038,year)
            # Time
            timeBox = wx.StaticBox(self, wx.ID_ANY, _(u'Time:'))
            self.hour_static = wx.StaticText(timeBox,wx.ID_ANY,_(u'Hour:'),dPos,dSize,0)
            self.hour = wx.SpinCtrl(timeBox,wx.ID_ANY,u'',dPos,Size(65,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,0,23,hour)
            self.min_static = wx.StaticText(timeBox,wx.ID_ANY, _(u'Min:'),dPos,dSize,0)
            self.min = wx.SpinCtrl(timeBox,wx.ID_ANY,u'',dPos,Size(65,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,0,59,min)
            self.sec_static = wx.StaticText(timeBox,wx.ID_ANY, _(u'Sec:'),dPos,dSize,0)
            self.sec = wx.SpinCtrl(timeBox,wx.ID_ANY,u'',dPos,Size(65,-1),wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.ALIGN_CENTER_HORIZONTAL,0,59,sec)
            # Manual insert
            mnlBox = wx.StaticBox(self, wx.ID_ANY, _(u'Insert Date/Time Manually (mm/dd/YYYY, hh:mm:ss):'))
            self.mnlTxtCtrl = wx.TextCtrl(mnlBox, wx.ID_ANY, '', dPos, dSize, 0)
            # Buttons area
            self.ok_button = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, (-1, 22), 0)
            self.smplTextCtrl = wx.TextCtrl(self, wx.ID_ANY, self.curDT, dPos, dSize, wx.TE_CENTRE|wx.TE_READONLY|wx.SIMPLE_BORDER)
            self.cancel_button = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, (-1, 22), 0)

        if True:  # Theming
            self.SetForegroundColour(wx.Colour(255, 255, 255))
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.month_static.SetForegroundColour(wx.Colour(0, 0, 0))
            self.month_static.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.month.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_CAPTIONTEXT))
            self.smplTextCtrl.SetForegroundColour(wx.Colour(0, 0, 0))
            self.smplTextCtrl.SetBackgroundColour(wx.Colour(224, 224, 224))

        if True:  # Layout
            # Date
            dateSizer = wx.StaticBoxSizer(dateBox, wx.HORIZONTAL)
            dateSizer.AddMany([(self.month_static,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT,5),(self.month,0,wx.RIGHT|wx.LEFT,5),
                    ((0,0),1,wx.EXPAND,5),(self.day_static,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT,5),(self.day,0,wx.RIGHT|wx.LEFT,5),
                    ((0,0),1,wx.EXPAND,5),(self.year_static,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT,5),(self.year,0,wx.RIGHT|wx.LEFT,5)])
            # Time
            timeSizer = wx.StaticBoxSizer(timeBox, wx.HORIZONTAL)
            timeSizer.AddMany([(self.hour_static,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT,5),(self.hour,0,wx.RIGHT|wx.LEFT,5),
                    ((0,0),1,wx.EXPAND,5),(self.min_static,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT,5),(self.min,0,wx.RIGHT|wx.LEFT,5),
                    ((0,0),1,wx.EXPAND,5),(self.sec_static,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT,5),(self.sec,0,wx.RIGHT|wx.LEFT,5)])
            # Manual
            mnlSizer = wx.StaticBoxSizer(mnlBox, wx.HORIZONTAL)
            mnlSizer.Add(self.mnlTxtCtrl, 1, wx.ALL, 5)
            # Buttons
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.ok_button,0,wx.ALL,5),
                (self.smplTextCtrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5), (self.cancel_button,0,wx.ALL,5)])
            # Main
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(self.info,0,wx.ALL|wx.EXPAND,5), (dateSizer,-1,wx.EXPAND,5),
                    (timeSizer,-1,wx.EXPAND,5), (mnlSizer, 0, wx.EXPAND, 5), (btnSizer,0,wx.EXPAND,5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True:  # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
            wx.EVT_SPINCTRL(self, wx.ID_ANY, self.rstMnl)


        self.cancel_button.SetFocus()
        self.ShowModal()

    def export_date(self):
        user_date = '%s-%s-%s %s:%s:%s'%(
                        self.month.GetValue(),
                        self.day.GetValue(),
                        self.year.GetValue(),
                        self.hour.GetValue(),
                        self.min.GetValue(),
                        self.sec.GetValue())
        return user_date

    def GetValue(self):
        return self.fin_val_po

    def timer_po(self):
        """Timer for buttons."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(350)

    def onUpdate(self, event):
        """Timer actions."""
        self.smplTextCtrl.SetValue(self.export_date().replace(' ', ', ').replace('-', '/'))
        modTR = self.mnlTxtCtrl.GetValue()
        try:
            modT = modTR.replace(',', '').replace('/', ' ').replace(':', ' ').split(' ')
            if len(modT) == 6:
                [x.SetValue(int(y)) for x, y in zip((self.month, self.day, self.year, self.hour, self.min, self.sec), modT)]
        except: pass

    def rstMnl(self, event):
        """Reset manual field."""
        self.mnlTxtCtrl.SetValue('')

    def OnCancel(self, event):
        self.fin_val_po = self.datetime
        self.Destroy()

    def OnOk(self, event):
        self.fin_val_po = self.export_date()
        self.Destroy()


class SimpleListDialog(wx.Dialog):  # Polemos
    """A simple modal list dialog."""
    Selection = None

    def __init__(self, parent, choices, msg=_(u'Choose an item:'), title=_(u'Select item'), size=Size(350, 190)):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        if not type(choices) is list: choices = [choices]
        self.choices = choices

        if True: # Content
            self.intro = wx.StaticText(self, wx.ID_ANY, msg, dPos, dSize, 0)
            self.wxlist = wx.ListBox(self, wx.ID_ANY, dPos, dSize, self.choices, wx.LB_ALWAYS_SB)
            self.ok_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, Size(40, 22), 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, Size(55, 22), 0)

        if True: # Theming
            self.intro.Wrap(-1)
            self.wxlist.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, u''))
            self.wxlist.SetForegroundColour(wx.Colour(0, 0, 0))
            self.wxlist.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True: # Layout
            contentSizer = wx.BoxSizer(wx.VERTICAL)
            contentSizer.AddMany([(self.intro, 0, wx.TOP|wx.RIGHT|wx.LEFT, 5),(self.wxlist, 1, wx.EXPAND|wx.ALL, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.ok_btn, 0, wx.RIGHT|wx.LEFT|wx.DOWN, 5),(self.cancel_btn, 0, wx.RIGHT|wx.LEFT|wx.DOWN, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(contentSizer, 1, wx.EXPAND, 5),(btnSizer, 0, wx.ALIGN_RIGHT, 5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True: # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
            self.wxlist.Bind(wx.EVT_LISTBOX_DCLICK, self.OnOK)

        self.timer_po()
        self.ShowModal()

    def timer_po(self):
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        if self.wxlist.GetSelection() == -1:
            if self.ok_btn.IsEnabled(): self.ok_btn.Disable()
        else:
            if not self.ok_btn.IsEnabled(): self.ok_btn.Enable()

    def OnOK(self, event):
        try: self.Selection = self.wxlist.GetSelection()
        except: pass
        finally: self.OnCancel(None)

    def OnCancel(self, event):
        self.timer.Stop()
        self.Destroy()


class ListDialog(wx.Dialog):  # Polemos
    """Show an advanced modal list dialog with add/remove/delete functions for entries."""

    def __init__(self, parent, title, data):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=Size(417, 234), style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE)
        if data != {}: self.data = data
        else: self.data = {}

        if True:  # Contents
            self.contents_list = wx.ListBox(self, wx.ID_ANY, dPos, dSize, u'', wx.LB_ALWAYS_SB|wx.LB_SORT)

        if True:  # Buttons
            self.add_button = wx.Button(self, wx.ID_ANY, _(u'Add'), dPos, (60,26), 0)
            self.edit_button = wx.Button(self, wx.ID_ANY, _(u'Edit'), dPos, (60,26), 0)
            self.remove_button = wx.Button(self, wx.ID_ANY, _(u'Remove'), dPos, (60,26), 0)
            self.ok_button = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, (60,26), 0)
            self.cancel_button = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, (60,26), 0)

        if True:  # Theming
            self.contents_list.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, ''))
            self.contents_list.SetForegroundColour(wx.Colour(0, 0, 0))
            self.contents_list.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True:  # Layout
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.AddMany([(self.add_button,0,wx.ALL,5),(self.edit_button,0,wx.ALL,5),(self.remove_button,0,wx.ALL,5),
                                  ((0,0),1,wx.EXPAND, 5),(self.ok_button,0,wx.ALL,5),(self.cancel_button,0,wx.ALL,5)])
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.AddMany([(self.contents_list,1,wx.ALL|wx.EXPAND,2),(button_sizer,0,wx.EXPAND,3)])
            self.SetSizer(main_sizer)

        if True:  # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            self.add_button.Bind(wx.EVT_BUTTON, self.add)
            self.edit_button.Bind(wx.EVT_BUTTON, self.edit)
            self.remove_button.Bind(wx.EVT_BUTTON, self.remove)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.Layout()
        self.Centre(wx.BOTH)
        self.OnScreen()
        self.ShowModal()

    def OnCancel(self, event):
        """On cancel."""
        self.GetValue = False
        self.data = {}
        self.Destroy()

    def OnScreen(self):
        """Show list."""
        try:
            self.screen_data = [u'[%s] : [%s]' % (x, self.data[x]) for x in self.data]
            self.contents_list.SetItems(self.screen_data)
        except: pass

    def add(self, event):
        """Add item."""
        dialog = ItemDialog(self, _(u'Add Command'), {u'': u''})
        value = dialog.GetValue
        if value == {u'': u''}: return
        elif value:
            self.data.update(value)
            self.OnScreen()

    def CurrentItem(self):
        """On item select actions."""
        try:
            command = self.contents_list.GetString(self.contents_list.GetSelection())
            name, args = command.split(u' : ')
            name, args = name.strip(u'[] '), args.strip(u'[] ')
            return name, args, {name:args}
        except: pass  # In a way we propagate the exception to the caller.

    def edit(self, event):
        """Edit selected."""
        try: name, args, result = self.CurrentItem()
        except: return
        dialog = ItemDialog(self, _(u'Edit Command'), result)
        value = dialog.GetValue
        if value == {u'': u''}: return
        elif value:
            if name in self.data.keys(): del self.data[name]
            self.data.update(value)
            self.OnScreen()

    def remove(self, event):
        """Remove selected"""
        try:
            del self.data[self.CurrentItem()[0]]
            self.OnScreen()
        except: pass

    def OnOK(self, event):
        """On OK."""
        self.GetValue = self.data
        self.data = {}
        self.Destroy()


class ItemDialog(wx.Dialog):  # Polemos
    """Modal helper of ListDialog."""

    def __init__(self, parent, title, item):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=Size(356, 162), style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE)
        for x in item: name, command = x, item[x]

        if True:  # Contents
            boxName = wx.StaticBox(self, -1, _(u'Name'))
            boxCommand = wx.StaticBox(self, -1, _(u'Command (add %target% variable for target file)'))
            self.name = wx.TextCtrl(self, wx.ID_ANY, name, dPos, dSize, wx.TE_NO_VSCROLL)
            self.command = wx.TextCtrl(self, wx.ID_ANY, command, dPos, dSize, 0)
            self.status_text = wx.StaticText(self, wx.ID_ANY, u'', dPos, dSize, wx.ALIGN_CENTRE) # Polemos Todo: Show errors.
            self.status_text.Wrap(-1)
            self.ok_button = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, dSize, 0)
            self.cancel_button = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, dSize, 0)

        if True:  # Theming
            self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.name.SetForegroundColour(wx.Colour(0, 0, 0))
            self.name.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.command.SetForegroundColour(wx.Colour(0, 0, 0))
            self.command.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.status_text.SetForegroundColour(wx.Colour(255, 0, 0))
            self.status_text.SetBackgroundColour(wx.Colour(235, 235, 235))

        if True:  # Layout
            name_field_sizer = wx.StaticBoxSizer(boxName, wx.VERTICAL)
            name_field_sizer.Add(self.name,0,wx.RIGHT|wx.LEFT|wx.EXPAND,5)
            command_field_sizer = wx.StaticBoxSizer(boxCommand,wx.VERTICAL)
            command_field_sizer.Add(self.command,0,wx.RIGHT|wx.LEFT|wx.DOWN|wx.EXPAND,5)
            buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
            buttons_sizer.AddMany([(self.ok_button,0,wx.ALL,5),(self.status_text,1,wx.ALL,7),(self.cancel_button,0,wx.ALL,5)])
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.AddMany([(name_field_sizer,0,wx.EXPAND,5),(command_field_sizer,0,wx.EXPAND,5),(buttons_sizer,0,wx.EXPAND,5)])
            self.SetSizer(main_sizer)

        if True:  # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.Layout()
        self.Centre(wx.BOTH)
        self.ShowModal()

    def dechar(self, text):
        return text.replace(';', ':')

    def OnOK(self, event):
        key = self.dechar(self.name.GetValue())
        value = self.command.GetValue()
        self.GetValue = {key:value}
        self.Destroy()

    def OnCancel(self, event):
        self.GetValue = False
        self.Destroy()


class RunDialog(wx.Dialog):  # Polemos
    """A dialog for running customs commands."""

    def __init__(self, parent, style=wx.CAPTION|wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'Run...'), pos=dPos, size=Size(398, 116), style=style)

        if True:  # Content
            boxCommand = wx.StaticBox(self, -1, _(u'Command (add %target% variable for target file)'))
            self.input_text = wx.TextCtrl(self, wx.ID_ANY, u'', dPos, dSize, wx.TE_NO_VSCROLL)
            self.run_button = wx.Button(self, wx.ID_ANY, _(u'Execute Command'), dPos, dSize, 0)
            self.cancel_button = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, dSize, 0)

        if True:  # Theming
            self.SetForegroundColour(wx.Colour(0, 0, 0))
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.input_text.SetForegroundColour(wx.Colour(0, 0, 0))
            self.input_text.SetBackgroundColour(wx.Colour(255, 255, 255))

        if True:  # Layout
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.AddMany([(self.run_button,0,wx.ALL,3),((0,0),1,0,3),(self.cancel_button,0,wx.ALL,3)])
            main_sizer = wx.StaticBoxSizer(boxCommand, wx.VERTICAL)
            main_sizer.AddMany([(self.input_text,0,wx.EXPAND|wx.ALL,5),(button_sizer,0,wx.EXPAND,3)])
            self.SetSizer(main_sizer)

        if True: # Events
            wx.EVT_CLOSE(self, self.OnCancel)
            self.run_button.Bind(wx.EVT_BUTTON, self.OnRun)
            self.cancel_button.Bind(wx.EVT_BUTTON, self.OnCancel)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        if conf.settings['last.custom.cmd']: self.input_text.SetValue(conf.settings['last.custom.cmd'])
        self.Layout()
        self.Centre(wx.BOTH)
        self.timer_po()
        self.ShowModal()

    def OnRun(self, event):
        self.GetValue = conf.settings['last.custom.cmd'] = self.input_text.GetValue().strip()
        self.Destroy()

    def timer_po(self):
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        if not self.input_text.GetValue().strip():
            if self.run_button.IsEnabled(): self.run_button.Disable()
        else:
            if not self.run_button.IsEnabled(): self.run_button.Enable()

    def OnCancel(self, event):
        self.GetValue = False
        self.timer.Stop()
        self.Destroy()


class UtilsDialog(wx.Dialog):  # Polemos: so many things here... also moved from Utils.py
    """Dialog for creating/modifying utilities."""
    result = None

    def __init__(self, parent, pos=dPos, size=(400, 300), new=True, data = ('','','','')):
        """Utilities Dialog."""
        wx.Dialog.__init__(self, parent, pos=pos, size=size, style=wx.CAPTION|wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)

        from ..balt import button
        self.Panel = wx.Panel(self)
        self.SetMinSize(size)

        if True:  # components
            txtProg = wx.StaticText(self.Panel, -1, _(u'Program'))
            self.fldProg = wx.TextCtrl(self.Panel, -1, value=data[1], style=wx.TE_READONLY)
            btnBrowse = button(self.Panel, id=-1, label=_('...'), name='btnBrowse', onClick=self.OpenFile, tip=_(u'Browse for a program.'))

            txtArguments = wx.StaticText(self.Panel, -1, _(u'Arguments'))
            self.fldArguments = wx.TextCtrl(self.Panel, -1, value=data[2])

            txtDesc = wx.StaticText(self.Panel, -1, _(u'Description'))
            self.fldDesc = wx.TextCtrl(self.Panel, -1, style=wx.TE_MULTILINE, value=data[3])
            self.fldDesc.SetBackgroundColour((255, 255, 255))
            self.fldDesc.SetMinSize(Size(-1, 100))

            btnOk = button(self.Panel, id=wx.ID_OK, label=_(u'OK'), name='btnOk', onClick=self.SaveUtility)
            btnCancel = button(self.Panel, id=wx.ID_CANCEL, label=_(u'Cancel'), name='btnCancel', onClick=self.Cancel)

        if True:  # Layout
            sizerProg = wx.BoxSizer(wx.HORIZONTAL)
            sizerProg.SetMinSize(Size(400, -1))
            sizerProg.AddMany([(self.fldProg,1,wx.EXPAND),((2,0)),(btnBrowse)])
            sizerBtn = wx.BoxSizer(wx.HORIZONTAL)
            sizerBtn.AddMany([(btnOk,0,wx.EXPAND),((0,0),1,wx.EXPAND,5),(btnCancel,0,wx.EXPAND)])
            sizerWin = wx.BoxSizer(wx.VERTICAL)
            sizerWin.AddMany([(txtProg),(sizerProg,0,wx.EXPAND),(txtArguments),(self.fldArguments,0,wx.EXPAND),
                              (txtDesc),(self.fldDesc,2,wx.EXPAND),(sizerBtn,0,wx.EXPAND)])
            sizerWin.Fit(self)
            self.Panel.SetSizer(sizerWin)
            self.Panel.Layout()

        if True:  # events
            wx.EVT_BUTTON(self, wx.ID_OK, self.SaveUtility)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.Cancel)

    def Cancel(self, event):
        """Cancels the utility creation/modification."""
        self.result = False
        event.Skip()

    def OpenFile(self, event):  # Polemos fix
        """Opens the file dialog to set the utility program."""
        dialog = wx.FileDialog(self,_(u'Choose the new utility.'), '', '', '*.*', wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return
        path = dialog.GetPath()
        dialog.Destroy()
        self.fldProg.SetValue(path)

    def SaveUtility(self, event):  # Polemos: No more key problems here...
        """Saves the new/modified utility."""
        import random
        ID = str(random.randint(100, 999))
        prog = self.fldProg.GetValue()
        arguments = self.fldArguments.GetValue()
        desc = self.fldDesc.GetValue()
        self.result = (ID, prog, arguments, desc)
        event.Skip()


class AdvLog(wx.Dialog):  # Polemos
    """A log dialog with a save button."""
    lineok = ''
    log_done = False

    def __init__(self, parent, title, logname='Output.log', ruleset='Default'):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=dSize, style=wx.CAPTION|wx.STAY_ON_TOP)
        self.logname = logname
        self.title = title
        self.ruleset = ruleset

        if True:  # Content
            # Polemos: TE_RICH mainly for stdout of > 64k
            self.text_log = wx.TextCtrl(self, wx.ID_ANY, u'', dPos, dSize, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
            self.text_log.SetBackgroundColour((255, 255, 255))
            self.OK_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, dSize, 0)
            self.savelog_btn = wx.Button(self, wx.ID_ANY, _(u'Save Log'), dPos, dSize, 0)

        if True:  # Layout
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            btn_sizer.AddMany([(self.OK_btn,0,wx.ALIGN_LEFT|wx.ALL,5),((0,0),1,wx.EXPAND,5),(self.savelog_btn,0,wx.ALIGN_RIGHT|wx.ALL,5)])
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.SetMinSize(Size(650, 300))
            main_sizer.AddMany([(self.text_log,1,wx.EXPAND|wx.ALL,5),(btn_sizer,0,wx.EXPAND,5)])
            self.SetSizer(main_sizer)
            main_sizer.Fit(self)

        if True:  # Events
            self.Bind(wx.EVT_CLOSE, self.close)
            self.savelog_btn.Bind(wx.EVT_BUTTON, self.savelog)
            wx.EVT_BUTTON(self, wx.ID_OK, self.close)

        self.Layout()
        self.Centre(wx.BOTH)
        self.timer_po()
        self.start()

    def start(self):
        """Cosmetic stuff."""
        self.SetTitle(_(u'Please Wait...'))
        self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLUE))
        self.text_log.WriteText(_(u'\nProcedure is being initialized. Please wait.'
                                u'\n--------------------------------------------\n'))

    def write(self, data, color='BLACK'):
        """Combines letter into words and display."""
        if not data.endswith('\n'): self.lineok = '%s%s' % (self.lineok, data)
        else:
            self.lineok = '%s%s' % (self.lineok, data)
            self.chkRules(self.lineok, color)
            self.text_log.WriteText(self.lineok)
            self.lineok = ''

    def chkRules(self, line, color):
        """Apply ruleset on line."""
        if self.ruleset == 'TES3lint':
            if line.lstrip().startswith('['): color = 'BROWN'
        elif self.ruleset == 'MultiPatch':
            if line.lstrip().startswith('No patching necessary.'): color = 'RED'
            elif line.lstrip().startswith('Multipatch: Scanning'): color = 'BROWN'
            elif line.lstrip().startswith('A multipatch has been conjured'): color = 'BROWN'
            elif line.lstrip().startswith('tes3cmd multipatch skipping'): color = 'RED'
        elif self.ruleset == 'Fixit':
            if line.lstrip().startswith('No patching necessary.'): color = 'RED'
            elif line.lstrip().startswith('Multipatch: Scanning Active Plugins...'): color = 'BROWN'
            elif line.lstrip().startswith('CLEANING:'): color = 'RED'
            elif line.lstrip().startswith('Cleaning Stats for'): color = 'BROWN'
            elif line.lstrip().startswith('A multipatch has been conjured'): color = 'BROWN'
            elif line.lstrip().startswith('tes3cmd multipatch skipping'): color = 'RED'
        self.color(color)

    def color(self, clr):
        """Color selection."""
        if clr == 'RED': self.text_log.SetDefaultStyle(wx.TextAttr(wx.RED))
        elif clr == 'BLACK': self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        elif clr == 'BLUE': self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLUE))
        elif clr == 'BROWN': self.text_log.SetDefaultStyle(wx.TextAttr(wx.Colour(153, 0, 0)))

    def finished(self):
        """Cosmetic finish."""
        self.SetTitle(self.title)
        self.text_log.SetDefaultStyle(wx.TextAttr(wx.BLUE))
        self.text_log.WriteText(_(u'\n\nFinished.\n\n'))
        self.log_done = True

    def winlog(self):
        """Makes log line endings compatible with older versions of windows."""
        return '\r\n'.join(self.text_log.GetValue().split('\n'))

    def savelog(self, event):
        """Option to save log."""
        dialog = wx.FileDialog(self, _(u'Save log'), singletons.MashDir, self.logname, '*.log', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            fileName = os.path.join(dialog.GetDirectory(), dialog.GetFilename())
            with io.open(fileName, 'w', encoding='utf-8', errors='replace') as file:
                file.write(self.winlog())

    def close(self, event):
        """Exit actions."""
        self.timer.Stop()
        self.Destroy()

    def timer_po(self):
        """Timer for buttons."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        """Timer actions."""
        if not self.log_done:
            if self.OK_btn.IsEnabled: self.OK_btn.Disable()
            if self.savelog_btn.IsEnabled: self.savelog_btn.Disable()
        else:
            self.OK_btn.Enable()
            self.savelog_btn.Enable()


class ArchiveExplorer(wx.Dialog):  # Polemos
    """Content explorer for mod archives."""
    checklvl = []
    dataSet = False
    dataItem = ''
    selectedItem = ''
    GetTreeValue = None

    def __init__(self, package_data, advData=None, title=_(u'Install Plugin...')):
        """Init."""
        parent, archive, archiveData = package_data
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=(-1,-1), size=(400, 350), style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        self.folders, self.max_depth = archiveData
        self.advData = advData
        self.timer_po()

        if True:  # Contents
            self.archiveText = wx.StaticText(self, wx.ID_ANY, _(u'Contents of: %s' % archive), dPos, dSize, wx.ALIGN_CENTRE)
            archBoxTitle = wx.StaticBox(self, wx.ID_ANY, _(u'Right click on a folder for options:'))
            self.archiveTree = wx.TreeCtrl(archBoxTitle, wx.ID_ANY, dPos, dSize, wx.TR_DEFAULT_STYLE)
            self.statusText = wx.StaticText(self,wx.ID_ANY,_(u'Please select the mod\'s root folder.'),dPos,dSize,wx.ALIGN_CENTRE|wx.STATIC_BORDER)
            self.ok_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, dSize, 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, dSize, 0)

        if True:  # Content Settings
            self.ok_btn.SetDefault()
            self.statusText.SetMinSize(Size(-1, 24))
            self.ok_btn.SetMinSize(Size(35, 22))
            self.cancel_btn.SetMinSize(Size(60, 22))
            self.setRootdata()
            self.archiveTree.Expand(self.root)
            self.ok_btn.SetFocus()

        if True:  # Fonts
            self.archiveText.SetFont(wx.Font(10,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False,u''))
            self.statusText.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, u''))
            self.archiveText.Wrap(-1)
            self.statusText.Wrap(-1)

        if True:  # Theming
            self.TreeForeColor = wx.Colour(0, 0, 0)
            self.statusText.SetForegroundColour(wx.Colour(255, 0, 0))
            self.archiveTree.SetForegroundColour(self.TreeForeColor)
            self.archiveTree.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.SetForegroundColour(wx.Colour(0, 0, 0))
            self.SetBackgroundColour(wx.Colour(224, 224, 224))

        if True:  # Layout
            archBoxSizer = wx.StaticBoxSizer(archBoxTitle, wx.VERTICAL)
            archBoxSizer.Add(self.archiveTree, 1, wx.EXPAND, 5)
            buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
            buttonSizer.AddMany([(self.statusText,1,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT,5),(self.ok_btn,0,wx.ALL,5),(self.cancel_btn,0,wx.ALL,5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(self.archiveText,0,wx.EXPAND|wx.UP|wx.RIGHT|wx.LEFT,5),(archBoxSizer,1,wx.EXPAND|wx.ALL,5),(buttonSizer,0,wx.EXPAND,5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True:  # Events
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.onClose)
            self.Bind(wx.EVT_CLOSE, self.onClose)
            self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.showLevel)
            self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onMouseR)

        self.ShowModal()

    def timer_po(self):
        """Timer for buttons."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        """Timer actions."""
        if self.GetTreeValue is None:
            if self.ok_btn.IsEnabled(): self.ok_btn.Disable()
        else:
            if not self.ok_btn.IsEnabled(): self.ok_btn.Enable()

    def conv_path(self, advData):  # Polemos => Todo: Implement this.
        """Converts imported path to a Package Explorer entry."""
        return

    def treeFactory(self, item):
        """Assemble selected folder path to return to the Package Explorer."""
        treeItems = []
        treeItems.append(self.archiveTree.GetItemText(item))
        for x in range(self.max_depth):
            try:
                treeItems.append(self.archiveTree.GetItemText(self.archiveTree.GetItemParent(item)))
                item = self.archiveTree.GetItemParent(item)
            except: break
        treeItems.reverse()
        del treeItems[0]
        self.GetTreeValue = os.path.join('', *treeItems)

    def onMouseR(self, event=None):
        """Show Menu."""
        if event is not None: self.selectedItem = event.GetItem()
        else: self.selectedItem = self.archiveTree.GetSelection()
        # Menu Options
        def setData(event):
            self.dataSet = True
            if self.dataItem: unsetOld()
            self.dataItem = self.selectedItem
            self.archiveTree.SetItemTextColour(self.dataItem, wx.BLUE)
            self.archiveTree.SetItemBold(self.dataItem)
            self.statusText.SetLabel(_(u'Mod\'s root folder set.'))
            self.statusText.SetForegroundColour(wx.BLUE)
            self.Layout()
            self.treeFactory(self.dataItem)
        def unsetData(event):
            self.dataSet = False
            unsetOld()
            self.dataItem = ''
            self.statusText.SetLabel(_(u'Please select the mod\'s root folder.'))
            self.statusText.SetForegroundColour(wx.Colour(255, 0, 0))
            self.GetTreeValue = None
            self.Layout()
        def unsetOld():
            self.archiveTree.SetItemTextColour(self.dataItem, self.TreeForeColor)
            self.archiveTree.SetItemBold(self.dataItem, False)
        # Menu items
        context = wx.Menu()
        setmenu = context.Append(-1, _(u'Set as the Mod\'s root.'))
        unsetmenu = context.Append(-1, _(u'Unset folder.'))
        # Rules
        if not self.dataSet:
            if unsetmenu.IsEnabled():unsetmenu.Enable(False)
        else:
            if not unsetmenu.IsEnabled(): unsetmenu.Enable()
        try:
            if self.selectedItem == self.dataItem:
                if setmenu.IsEnabled():setmenu.Enable(False)
            elif self.selectedItem != self.dataItem:
                if not setmenu.IsEnabled(): setmenu.Enable(True)
        except: pass
        # Events
        self.Bind(wx.EVT_MENU, setData, setmenu)
        self.Bind(wx.EVT_MENU, unsetData, unsetmenu)
        # Show menu
        self.PopupMenu(context, event.GetPoint())

    def setRootdata(self):
        """Package root level data."""
        # Set max depth fo the tree
        self.depth_levels = ['lvl%s' % x for x in range(self.max_depth)]
        # Make root name user friendly
        self.root = self.archiveTree.AddRoot(_(u'Archive root'))
        # Append root children
        for folder in self.folders:
            if folder[2] == 0:
                setattr(self, '%s%s' % (folder[1], 0), self.archiveTree.AppendItem(self.root, folder[1]))
                if self.max_depth - 1 != folder[2]:
                    self.archiveTree.SetItemHasChildren(getattr(self, '%s%s' % (folder[1], 0)))
        # Sort root level
        self.archiveTree.SortChildren(self.root)

    def showLevel(self, event):
        """Package deeper levels data."""
        item = self.archiveTree.GetItemText(event.GetItem())
        # Avoid tree recreation
        childs = self.archiveTree.GetChildrenCount(event.GetItem())
        if childs != 0: return
        # Loop only on items children
        children = [folder for folder in self.folders if folder[0] == item]
        for child in children:
            # Append new children
            try: setattr(self, '%s%s' % (child[1], child[2]), self.archiveTree.AppendItem(getattr(self, '%s%s' % (child[0], child[2]-1)), child[1]))
            except: pass # Catch problematic attrs
            # Show if there are any children to the current level and cache all remaining levels
            if self.max_depth-1 != child[2]:
                try: self.archiveTree.SetItemHasChildren(getattr(self, '%s%s' % (child[1], child[2])))
                except: continue
                self.archiveTree.Expand(getattr(self, '%s%s' % (child[1], child[2])))
                if not self.archiveTree.IsExpanded(getattr(self, '%s%s' % (child[1], child[2]))):
                    self.archiveTree.SetItemHasChildren(getattr(self, '%s%s' % (child[1], child[2])), False)
                self.archiveTree.Collapse(getattr(self, '%s%s' % (child[1], child[2])))
                # Sort children
                self.archiveTree.SortChildren(getattr(self, '%s%s' % (child[1], child[2])))

    def onClose(self, event):
        """Exit..."""
        self.GetTreeValue = None
        self.Destroy()


class HelpDialog(wx.Dialog):  # Polemos
    """Help browser."""

    def __init__(self, parent, images, pos, size, style=wx.DEFAULT_DIALOG_STYLE|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.STAY_ON_TOP):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'Wrye Mash Help.'), pos=pos, size=size, style=style)
        self.openmw = conf.settings['openmw']
        singletons.helpBrowser = self
        self.SetIcons(images['mash.main.ico'].GetIconBundle())
        self.SetSizeHints(-1, -1)
        if True: # Content
            # Panels
            self.main = wx.SplitterWindow(self, wx.ID_ANY, dPos, dSize, wx.SP_3D|wx.SP_LIVE_UPDATE)
            self.indexPanel = wx.Panel(self.main, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            self.contentPanel = wx.Panel(self.main, wx.ID_ANY, dPos, dSize, wx.TAB_TRAVERSAL)
            # Content
            self.conText = wx.StaticText(self.indexPanel, wx.ID_ANY, _(u'Contents:'), dPos, dSize, 0)
            self.search = wx.SearchCtrl(self.indexPanel, wx.ID_ANY, '', dPos, dSize, 0)
            self.search.Hide()
            self.index = wx.TreeCtrl(self.indexPanel, wx.ID_ANY, dPos, dSize, wx.TR_HIDE_ROOT|wx.TR_NO_LINES)
            self.help = wx.html.HtmlWindow(self.contentPanel, wx.ID_ANY, dPos, dSize, wx.html.HW_SCROLLBAR_AUTO)
        if True: # Theme
            self.SetBackgroundColour(wx.Colour(192, 192, 192))
            self.main.SetBackgroundColour(wx.Colour(192, 192, 192))
            self.indexPanel.SetBackgroundColour(wx.Colour(192, 192, 192))
            self.search.SetBackgroundColour(wx.Colour(192, 192, 192))
            self.index.SetBackgroundColour(wx.Colour(224, 224, 224))
            if interface.style['lists.font.color'] is not None:  # Todo: Theme
                self.index.SetForegroundColour(interface.style['lists.font.color'])
            self.contentPanel.SetBackgroundColour(wx.Colour(192, 192, 192))
            self.help.SetBackgroundColour(wx.Colour(255, 255, 255))
        if True: # Layout
            self.main.SetMinimumPaneSize(178)
            self.conText.Wrap(-1)
            indexSizer = wx.BoxSizer(wx.VERTICAL)
            indexSizer.AddMany([(self.conText,0,wx.ALL|wx.EXPAND,5),
                (self.search,0,wx.EXPAND|wx.RIGHT|wx.LEFT,5),(self.index,1,wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT,5)])
            contentSizer = wx.BoxSizer(wx.VERTICAL)
            contentSizer.Add(self.help, 1, wx.EXPAND, 5)
            self.indexPanel.SetSizer(indexSizer)
            self.contentPanel.SetSizer(contentSizer)
            self.indexPanel.Layout()
            self.contentPanel.Layout()
            indexSizer.Fit(self.indexPanel)
            contentSizer.Fit(self.contentPanel)
            self.main.SplitVertically(self.indexPanel, self.contentPanel, 178)
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.Add(self.main, 1, wx.EXPAND|wx.ALL, 5)
            self.SetSizer(mainSizer)
            self.Layout()
        if True: # Events
            self.help.Bind(wx.EVT_KEY_DOWN, self.onChar)
            self.help.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.onLink)
            self.help.Bind(wx.EVT_ENTER_WINDOW, self.onHelp)
            self.help.Bind(wx.EVT_RIGHT_UP, self.onMouseR)
            self.index.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onIndex)
            self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.initSettings()

    def initSettings(self):
        """Init settings."""
        self.main.SetSashPosition(conf.settings['mash.help.sash'])
        self.loadHelp()
        self.setIndex()

    def onChar(self, event):
        """Keyboard shortcuts."""
        chars = {
            'a': 65
        }
        if event.GetUnicodeKey() in chars.values() and event.ControlDown():
            if event.GetUnicodeKey() == 65: self.help.SelectAll()
        else: event.Skip()

    def onMouseR(self, event):
        """On right clicking the help ctrl."""
        # Menu actions
        def copyAct(event):
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(self.help.SelectionToText()))
                wx.TheClipboard.Close()
        def SelectAllAct(event): self.help.SelectAll()
        # Menu items
        context = wx.Menu()
        CopyItm = context.Append(-1, _(u'Copy'))
        SelectAll = context.Append(-1, _(u'Select All'))
        # Events
        self.Bind(wx.EVT_MENU, copyAct, CopyItm)
        self.Bind(wx.EVT_MENU, SelectAllAct, SelectAll)
        # Conditions
        if self.help.SelectionToText() == '': CopyItm.Enable(False)
        # Show menu todo: optimize by overriding base method
        self.PopupMenu(context, [x/3 for x in self.help.GetSizeTuple()])

    def onHelp(self, event):
        """On hovering help panel."""
        if not self.help.HasFocus():
            self.help.SetFocus()

    def onIndex(self, event):
        """On selecting index entry."""
        try: self.help.ScrollToAnchor(self.index.GetItemText(event.GetItem())[:3].replace('.','').strip())
        except: pass

    def setIndex(self):
        """Create help index."""
        # Parse headings
        indexRaw = []
        tmp = []
        hold = last = False
        # Polemos: This is quite a brutal parsing. It will convert any <h2>...</h2> html tag
        # into a list entry for the help contents. It will grab the numeric part from the html
        # heading and create a link to a same num named (pre-placed) anchor in the html source.
        for x in self.helpData.splitlines():
            if 'h2>' in x:
                hold = False
                last = True
                tmp.append(x.strip())
            if hold: tmp.append(x.strip())
            if '<h2' in x:
                tmp.append(x)
                hold = True
            if last:
                result = ((' '.join(tmp)
                ).replace('><','')).partition(
                '>')[2].partition('<')[0].rstrip()
                if result: indexRaw.append(result)
                last = False
                tmp = []
        # Add to index
        self.root = self.index.AddRoot(_(u'Contents:'))
        for x in indexRaw: self.index.AppendItem(self.root, x)

    def loadHelp(self):
        """Load help file."""
        # Morrowind - OpenMW/TES3mp support
        helpFile ='Wrye Mash.dat' if not self.openmw else 'openmw.dat'
        path = os.path.join(singletons.MashDir, helpFile)
        with io.open(path, 'r') as hlpData:
            self.helpData = hlpData.read()
        self.help.SetPage(self.helpData)

    def onLink(self, event):
        """Handle internal and external links."""
        href = event.GetLinkInfo().GetHref()
        anchor = href[1:]
        if not href.startswith('#'): wx.LaunchDefaultBrowser(href)
        elif self.help.HasAnchor(anchor): self.help.ScrollToAnchor(anchor)

    def OnClose(self, event):
        """Exit..."""
        conf.settings['mash.help.show'] = False
        if not self.IsIconized() and not self.IsMaximized():
            conf.settings['mash.help.sash'] = self.main.GetSashPosition()
            conf.settings['mash.help.pos'] = self.GetPosition()
            conf.settings['mash.help.size'] = self.GetSizeTuple()
        self.Destroy()


class ConfBackup(wx.Dialog):
    """A dialog for performing manual backups of Morrowind/OpenMW configuration files."""

    def __init__(self, parent=None):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'Backup/Restore Configuration'), pos=dPos,
                           size=wx.Size(602, 300), style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP)
        self.SetSizeHints(-1, -1)
        self.confFileNamesTemplate = ('morrowind.ini', 'openmw.cfg', 'pluginlist.json')
        self.confInit()
        self.timer_po()
        cnfListChoices = self.setConfList()

        if True:  # Content
            # Main
            self.intro = wx.StaticText(self, wx.ID_ANY, _(u'Use [Ctrl] + [Left Mouse Click] to select/unselect multiple items:'), dPos, dSize,0)
            self.cnfList = wx.ListBox(self, wx.ID_ANY, dPos, dSize, cnfListChoices, wx.LB_ALWAYS_SB|wx.LB_EXTENDED)
            # Buttons
            self.res_btn = wx.Button(self, wx.ID_ANY, _(u'Restore Selected'), dPos, wx.Size(160, 22), 0)
            self.del_btn = wx.Button(self, wx.ID_ANY, _(u'Delete Selected'), dPos, wx.Size(160, 22), 0)
            self.bck_btn = wx.Button(self, wx.ID_ANY, _(u'Backup Current Configuration'), dPos, wx.Size(180, 22), 0)
            self.cnl_btn = wx.Button(self, wx.ID_CANCEL, _(u'Exit'), dPos, wx.Size(55, 22), 0)

        if True:  # Theming
            self.intro.Wrap(-1)
            self.cnfList.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, ''))
            '''self.SetForegroundColour(wx.Colour(240, 240, 240))
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.intro.SetForegroundColour(wx.Colour(0, 0, 0))
            self.intro.SetBackgroundColour(wx.Colour(240, 240, 240))'''
            self.cnfList.SetForegroundColour(wx.Colour(0, 0, 0))
            self.cnfList.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.del_btn.SetForegroundColour(wx.RED)

        if True:  # Layout
            contentSizer = wx.BoxSizer(wx.VERTICAL)
            contentSizer.AddMany([(self.intro, 0, wx.TOP|wx.RIGHT|wx.LEFT, 5), (self.cnfList, 1, wx.EXPAND|wx.ALL, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.res_btn, 0, wx.LEFT|wx.RIGHT, 5), ((0,0),1,0,5), (self.del_btn, 0, wx.LEFT|wx.RIGHT, 5), ((0,0),1,0,5),
                (self.bck_btn, 0, wx.RIGHT|wx.LEFT, 5), (self.cnl_btn, 0, wx.LEFT|wx.RIGHT|wx.DOWN, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(contentSizer, 1, wx.EXPAND, 5), (btnSizer, 0, wx.ALIGN_RIGHT|wx.EXPAND, 5)])
            self.SetSizer(mainSizer)
            self.Layout()

        if True:  # Events
            wx.EVT_CLOSE(self, self.OnExit)
            self.res_btn.Bind(wx.EVT_BUTTON, self.restore)
            self.del_btn.Bind(wx.EVT_BUTTON, self.delete)
            self.bck_btn.Bind(wx.EVT_BUTTON, self.backup)
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnExit)

        self.ShowModal()

    def timer_po(self):
        """Timer for buttons."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(100)

    def onUpdate(self, event):
        """Timer actions."""
        if len(self.cnfList.GetSelections()) > 1 or not self.cnfList.GetSelections():
            if self.res_btn.IsEnabled(): self.res_btn.Disable()
        else:
            if not self.res_btn.IsEnabled(): self.res_btn.Enable()
        if not self.cnfList.GetSelections():
            if self.del_btn.IsEnabled(): self.del_btn.Disable()
        else:
            if not self.del_btn.IsEnabled(): self.del_btn.Enable()

    def chkBckDir(self):
        """Check for confBckDir existence."""
        if not os.path.isdir(self.confBckDir):  # One final check...
            os.makedirs(self.confBckDir)
            if not os.path.isdir(self.confBckDir):  # Failed.
                ErrorMessage(None, _(u'Access Denied: Unable to create a folder storage for backups!!\n\n'
                                     u'To proceed you neeed to manually create the following folder first:\n%s' % self.confBckDir))
                self.OnExit(None)

    def confInit(self):
        """Set conf path info."""
        self.confBckDir = profilePaths()['confBcks']
        self.chkBckDir()
        self.openmw = conf.settings['openmw']
        if not self.openmw:
            self.confFiles = {'Morrowind.ini': os.path.join(conf.settings['mwDir'], 'Morrowind.ini')}
        elif self.openmw:
            self.confFiles = {'OpenMW.cfg': os.path.join(conf.settings['openmwprofile'], 'OpenMW.cfg')}
            if conf.settings['tes3mp']: self.confFiles['pluginlist.json'] = conf.settings['TES3mpConf']

    def setConfList(self):
        """Creates configuration files list."""
        self.chkBckDir()
        rawConfList = {x: os.path.join(self.confBckDir, x) for x in os.listdir(
            self.confBckDir) if not os.path.isdir(os.path.join(self.confBckDir, x))}
        rawConfIndex = sorted([rawConfList[x] for x in rawConfList], key=os.path.getmtime, reverse=True)
        sortedRawConfList = [x.replace(self.confBckDir, '').replace('\\', '') for x in rawConfIndex]
        if not self.openmw:  # Morrowind
            ConfList = [x for x in sortedRawConfList if x.endswith('.ini')]
        elif self.openmw:  # OpenMW/TES3mp
            ConfList = [x for x in sortedRawConfList if x.endswith('.cfg') or x.endswith('.json')]
        return [x for x in ConfList if x.split(']')[1].lower() in self.confFileNamesTemplate]  # One last check.

    def restore(self, event):
        """Restore actions"""
        self.chkBckDir()
        fnameS = self.cnfList.GetString(self.cnfList.GetSelections()[0])
        fname = fnameS.split(']')[1]  # Brutal, but efficient
        if fname.lower() == 'morrowind.ini':  # Morrowind
            if conf.settings['mwDir']:  # Not really needed though...
                src = os.path.join(self.confBckDir, fnameS)
                dst = os.path.join(conf.settings['mwDir'], fname)
            else:
                WarningMessage(self, _(u'Unable to Restore:\n\nMorrowind is not set correctly in settings.\n'
                                     u'Please open the settings window and check the configuration.'))
                return
        elif fname.lower() == 'openmw.cfg':  # OpenMW
            if conf.settings['openmwprofile']:
                src = os.path.join(self.confBckDir, fnameS)
                dst = os.path.join(conf.settings['openmwprofile'], fname)
            else:
                WarningMessage(self, _(u'Unable to Restore:\n\nOpenMW is not set in settings.\n'
                                     u'Please open the settings window and set the configuration of OpenMW.'))
                return
        elif fname.lower() == 'pluginlist.json':  # TES3mp
            if conf.settings['TES3mpConf']:
                src = os.path.join(self.confBckDir, fnameS)
                dst = os.path.join(conf.settings['TES3mpConf'], fname)
            else:
                WarningMessage(self, _(u'Unable to Restore:\n\nTES3mp is not set in settings.\n'
                                     u'Please open the settings window and set the configuration of TES3mp.'))
                return
        # File actions.
        try: copyfile(src, dst)
        except IOError as err:  # Access Denied.
            ErrorMessage(self, _(u'Access Denied, unable to overwrite destination:\n\n%s') % err, _(u'Access Denied'))
        except Exception as err:  # Who knows.
            ErrorMessage(self, _(u'An error occurred while trying to restore:\n\n%s' % err))

    def backup(self, event):
        """Backup actions"""
        self.chkBckDir()
        timeStr = timestamp("%Y-%m-%d_%H-%M-%S")
        for fl in self.confFiles:
            src = self.confFiles[fl]
            dst = os.path.join(self.confBckDir, '[%s]%s' % (timeStr, fl))
            try: copyfile(src, dst)
            except Exception as err:
                ErrorMessage(self, _(u'An error occurred while trying to backup configuration:\n\n%s' % err))
        self.cnfList.SetItems(self.setConfList())

    def delete(self, event):
        """Delete actions"""
        self.chkBckDir()
        for fl in self.cnfList.GetSelections():
            target = os.path.join(self.confBckDir, self.cnfList.GetString(fl))
            try: os.remove(target)
            except Exception as err:
                ErrorMessage(self, _(u'An error occurred while trying to delete the selected item(s):\n\n%s' % err))
        self.cnfList.SetItems(self.setConfList())

    def OnExit(self, event):
        """Exit dialog."""
        self.timer.Destroy()
        self.Destroy()
