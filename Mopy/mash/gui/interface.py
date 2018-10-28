# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
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

# Extension for Wrye Mash Polemos fork ======================================================
#
# Interface, Copyright (C) 2018-, Polemos
#
# Polemos: Theming engine for Wrye Mash
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================


import wx, os, json
from ..mosh import _

# Default Style
style = {
    'mouse.hover': wx.RED,
    'lists.font.color': None
}

# Internal per setting styling
internalStyle = {
    'big.font':(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT),
    'list.background':(220,220,255)
}

def setIcon(parent, icon=None, text='', type=wx.wx.BITMAP_TYPE_ANY):
    """Set icon of caller window."""
    if icon is not None:
        try:
            parent.SetIcon(wx.Icon(icon, type), text)
            return
        except: pass  # If for a reason the image is missing.
    parent.SetIcon(wx.Icon(os.path.join('images', 'Wrye Mash.ico'), wx.BITMAP_TYPE_ICO), u'Wrye Mash')


class ThemeEngine:
    """Wrye Mash theme engine."""

    def __init__(self, theme):
        """Init."""
        self.checkThemeDir()
        if theme != ('Default theme', None): self.importTheme(theme[1])
        # Create dummy theme
        '''theme = {
            'theme.info': 'Black fonts for windows High Contrast theme, by Polemos',
            'lists.font.color': (255, 0, 0, 255)
        }
        self.exportTheme('Black_fonts_for_High_Contrast.mtf', theme)'''

    def checkThemeDir(self):
        """Check if it exists and recreate if needed the theme dir."""
        cwd = os.getcwd()
        self.themedir = os.path.join(cwd, 'themes')
        if not os.path.isdir(self.themedir): os.makedirs(self.themedir)

    def importTheme(self, theme):
        """Import theme."""
        themePath = os.path.join(self.themedir, theme)
        with open(themePath, 'r') as rawTheme: themeData = json.load(rawTheme)
        for x in themeData: style[x]=themeData[x]

    def exportTheme(self, theme, rawTheme):
        """Export theme."""
        themePath = os.path.join(self.themedir, theme)
        themeData = ('{\r\n\r\n', (',\r\n'.join(('"%s": %s' if type(rawTheme[x]) == tuple else '"%s": "%s"') %
            (x, list(rawTheme[x]) if type(rawTheme[x]) == tuple else rawTheme[x]) for x in rawTheme)), '\r\n\r\n}')
        with open(themePath, 'w') as themeFile: themeFile.writelines(themeData)


class SysTray(wx.TaskBarIcon):
    """Systray icon."""

    def __init__(self, mainFrame, mode):
        """Init."""
        wx.TaskBarIcon.__init__(self)
        mainFrame.Hide()
        self.mainFrame = mainFrame
        self.openmw = mode
        setIcon(self)
        # Event
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnSyTrayLeftClick)

    def OnSyTrayLeftClick(self, event):
        """Restore app window."""
        self.mainFrame.Show()
        self.mainFrame.Restore()
        self.onExit()

    def CreatePopupMenu(self):
        """Systray context menu."""
        # Menu items
        menu = wx.Menu()
        runGame = menu.AppendCheckItem(wx.NewId(), _(u'Launch %s') % (u'Morrowind' if not self.openmw else u'OpenMW'))
        menu.AppendSeparator()
        openApp = menu.Append(wx.NewId(), _(u'Open Wrye Mash'))
        exit = menu.Append(wx.NewId(), _(u'Exit'))
        # Menu actions
        def runGameDef(event): self.mainFrame.systrayRun(None)
        def OpenAppDef(event): self.OnSyTrayLeftClick(None)
        def ExitDef(event): self.mainFrame.OnCloseWindow(None)
        # Menu events
        self.Bind(wx.EVT_MENU, runGameDef, runGame)
        self.Bind(wx.EVT_MENU, OpenAppDef, openApp)
        self.Bind(wx.EVT_MENU, ExitDef, exit)
        # Show menu
        return menu

    def onExit(self):
        """On exiting Wrye Mash."""
        self.RemoveIcon()
        self.Destroy()
