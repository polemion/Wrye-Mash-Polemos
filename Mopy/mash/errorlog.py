# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
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
#  This file is part of Wrye Mash.
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
# ======================================================================================


"""
WxPython contains code for logging output to a file, or logging output to a window. I really want to do both.

The startup code redirects stdin/stderr to a file, so this class allows provides a wrapper around stdin/stderr
"""

import sys, wx, os, io
from .unimash import _, uniChk as uniChk
from . import conf, singletons
from .gui import dialog as gui
from . import appinfo

dPos = wx.DefaultPosition
dSize = wx.DefaultSize


class WxOutputRedirect(object):
    """Redirect output."""

    def __init__(self, std, frame, log):
        """Init."""
        self.std = std
        self.frame = frame
        self.log = log

    def write(self, message):
        """Return error msgs."""
        wx.CallAfter(self.frame.Show)
        wx.CallAfter(self.frame.Raise)
        try:
            wx.CallAfter(self.log.WriteText, message)  # Polemos: Korean fix (possibly more)
        except UnicodeDecodeError:
            wx.CallAfter(self.log.WriteText, uniChk(message))
        wx.CallAfter(self.std.write, message)


class ErrorLog(wx.Dialog):  # Polemos
    """A class to display errors."""

    def __init__(self, parent,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.STAY_ON_TOP):
        """Init."""
        self.parent = parent
        if not conf.settings['show.debug.log']: return
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'Debug Log'), pos=dPos, size=(415, 249), style=style)
        # Contents
        self.text_log = wx.TextCtrl(self, wx.ID_ANY, '', dPos, dSize, wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.saveBtn = wx.Button(self, wx.ID_ANY, _(u'Save Log'), dPos, (-1, 22), 0)
        self.fcloseBtn = wx.Button(self, wx.ID_ANY, _(u'Force Close Wrye Mash...'), dPos, (-1, 22), 0)
        # Theming
        self.SetForegroundColour(wx.Colour(255, 255, 255))
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        # Events
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.saveBtn.Bind(wx.EVT_BUTTON, self.savelog)
        self.fcloseBtn.Bind(wx.EVT_BUTTON, self.forceClose)
        # Functions
        sys.stdout = WxOutputRedirect(sys.stdout, self, self.text_log)
        sys.stderr = WxOutputRedirect(sys.stderr, self, self.text_log)
        # Layout
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddMany([(self.saveBtn, 1, wx.EXPAND | wx.RIGHT, 5), (self.fcloseBtn, 0, wx.EXPAND, 5)])
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.AddMany([(self.text_log, 1, wx.EXPAND, 5), (btnSizer, 0, wx.EXPAND, 5)])
        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)

    def forceClose(self, event):
        """Force close Wrye Mash."""
        warning = _(
            u'Really force Wrye Mash to quit?\n\nDo this only if Wrye Mash is stuck ad infinitum in the debug log!!!')
        if gui.WarningQuery(self, warning, _(u'Are you sure?')) == wx.ID_NO: return
        self.Destroy()
        try:
            if self.parent.IsIconized(): self.parent.sysTray.onExit()
        except:
            pass
        self.parent.Destroy()
        appinfo.app.ExitMainLoop()
        sys.exit(0)

    def savelog(self, event):
        """Save the log."""
        dialog = wx.FileDialog(self, _(u'Save log'), singletons.MashDir, "Debug", '*.log',
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            fileName = os.path.join(dialog.GetDirectory(), dialog.GetFilename())
            with io.open(fileName, 'w', encoding='utf-8', errors='replace') as fl:
                fl.write(self.text_log.GetValue())

    def OnClose(self, event):
        """On close event."""
        self.Hide()
