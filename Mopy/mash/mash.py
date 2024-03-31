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

import sys, io, os, traceback, wx, locale
from datetime import datetime
from stat import S_IWUSR, S_IREAD
from io import open
from . import appinfo

maxLogEntries = 20  # Polemos: Max number of sessions stored in the log.
logStart = '# ===================== Wrye Mash started. ===================== #'
logEnd = '# ===================== Wrye Mash exited. ====================== #'
log_file = 'WryeMash.log'


def logChk():
    """Check and limit log size."""
    try:
        os.chmod(log_file, S_IWUSR | S_IREAD)
        with io.open(log_file, 'r') as fl:
            rawLog = fl.readlines()
            index = [n for n, x in enumerate(rawLog) if logStart in x]
        if len(index) >= maxLogEntries:
            with io.open(log_file, 'w') as fl:
                index.reverse()
                fl.write(''.join(rawLog[index[maxLogEntries - 1]:]))
    except:  # Unable to access the log file. C'est La Vie.
        pass


class ErrorLogger(object):
    """Custom stream error logger."""

    def __init__(self, log_file):
        """Init."""
        self.log = open(log_file, 'a')

    def write(self, message):
        """Write message to the log."""
        self.log.write(message)
        self.flush()

    def flush(self):
        """Flush the log."""
        self.log.flush()

    def close(self):
        """Close the log."""
        self.log.close()


class MyApp(wx.App):
    """Bootstrap wxPython."""

    def InitLocale(self):
        """Init locale."""
        locale.setlocale(locale.LC_ALL, 'C')

    def OnInit(self):
        """OnInit."""
        wx.Locale(wx.LANGUAGE_ENGLISH_US)
        self.SetAppName(appinfo.appName)
        return True


# Main
logChk()
sys.stdout = ErrorLogger(log_file)
sys.stderr = sys.stdout
excode = 0
print('%s: %s' % (datetime.now(), logStart))
try:
    from . import masher
    app = MyApp(False)
    main = masher.MashApp()
    if main.OnInit():
        app.MainLoop()
    else:
        print('%s: [Error] %s failed to initialise. Exiting...' % (datetime.now(), appinfo.appName))
        excode = 1
except Exception as e:
    print('%s: [Error] %s:\n%s' % (datetime.now(), e, traceback.format_exc()), end='')
    excode = 1
finally:
    print('%s: %s\n' % (datetime.now(), logEnd))
    sys.exit(excode)
