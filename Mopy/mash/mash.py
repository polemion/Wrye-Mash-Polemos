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

import sys, io, os
from datetime import datetime
from stat import S_IWUSR, S_IREAD

maxLogEntries = 20  # Polemos: Max number of sessions stored in the log.


def logChk():
    """Check and limit log size."""
    try:
        os.chmod('WryeMash.log', S_IWUSR|S_IREAD)
        with io.open('WryeMash.log', 'r') as fl:
            rawLog = fl.readlines()
            index = [n for n, x in enumerate(rawLog) if '=== Wrye Mash started. ===' in x]
        if len(index) >= maxLogEntries:
            with io.open('WryeMash.log', 'w') as fl:
                index.reverse()
                fl.write(''.join(rawLog[index[maxLogEntries-1]:]))
    except: pass  # Unable to access the log file. C'est La Vie.


class ErrorLogger:
    """Class can be used for a writer to write to multiple streams. Duplicated
    in both possible startup files so log can be created without external
    dependencies"""

    def __init__(self, outStream):
        """Init."""
        self.outStream = outStream

    def write(self, message):
        """Write to out-stream."""
        try: [stream.write(message) for stream in self.outStream]
        except: pass


# Logger start
logChk()
fl = file('WryeMash.log', 'a+')
sys.stdout, sys.stderr = ErrorLogger((fl, sys.__stdout__)), ErrorLogger((fl, sys.__stderr__))
fl.write('\n%s: # ===================== Wrye Mash started. ===================== #\n' % datetime.now())

# Main
import masher
stdOutCode = int(sys.argv[1]) if len(sys.argv) > 1 else -1
app = masher.MashApp(stdOutCode) if stdOutCode >= 0 else masher.MashApp()
app.MainLoop()
fl.close()
