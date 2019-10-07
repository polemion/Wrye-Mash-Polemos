# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
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
# Credits, Copyright (C) 2018-, Polemos
#
# Polemos: Write your Mash Legacy here guys...
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================


import os, sys
from ..nash import wrye_download_site
from .. import bitver

# Determine if mash is x64 or x86 bit ver.
bit = bitver.wryeMashBitVer if hasattr(bitver, 'wryeMashBitVer') else ''
# OpenMW/TES3mp or Morrowind functionality.
openmw = os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'openmw.dat'))

# Version details
ver = 100
extraVerInfo = u'Beta4' if not openmw else u'Alpha for OpenMW'
date = u'10/2019'
author = u'Polemos fork'

def Current_Version():
    """The Data here feeds all of Wrye Mash."""
    extraVerInf = u' ' + extraVerInfo
    # Setup.py or setupx64.py imports version info (for compiling) from the line below. It is brutal so keep the formatting.
    return (ver, u'%sv%s%s - %s - %s' % (bit, ver, extraVerInf, author, date), u'%s - %s'%(ver, date), u'%s'%date[-4:], u'%s'%author)

class About:  # Polemos: a much needed "About".
    """About Data. It is called by Settings Dialog (About Tab)."""

    def __init__(self, mode):
        """Init."""
        self.name = u'Wrye Mash %s %s' % (Current_Version()[4], u'for OpenMW' if openmw else u'')
        self.version = u'Version: %s' % (Current_Version()[2])
        self.website = (u'Nexus Homepage', wrye_download_site('home', mode))

    def getData(self):
        """Return the credits data to the caller."""
        return self.name, self.version, self.website, self.developers(), self.license()

    # Note:
    # 'b' => bold,
    # 'i' => italic and
    # '' => None

    def developers(self):
        """Dev factory."""
        source = [(u'"Every modder and utility developer in the Morrowind community stands on the collective'
                   u' shoulders of everyone who preceded them, contributing time, talent, and inspiration.\r\n'
                   u'So, thanks to all the past developers and folks in the forums!", Wrye.\r\n', 'b'), ('\r\n','')]

        source.extend(((u'Wrye: ', 'b'),
                       (u'the original creator of Wrye everything,\r\n', 'i'),
                       (u'Melchor: ', 'b'),
                       (u'New help interface, Utilities tab and settings window,\r\n', 'i'),
                       (u'Yacoby: ', 'b'),
                       (u'drag and drop functionality, mlox - TES3cmd support, fixes, refactoring and more,\r\n', 'i'),
                       (u'Polemos: ', 'b'),
                       (u'Toolbar menu, mod order snapshots, better Unicode support, fixes, BSA Archives implementation, OpenMW/TES3mp compability,'
                        u' TES3lint support, Custom Commands support, new dialogs, theming options, store/restore mod order buttons, interface'
                        u' modernization and streamlining, speed improvements, update notifications, support for people with weak vision, higher'
                        u' icon res for the status bar, extra functionalities and more.\r\n', 'i'),
                       (u'\r\n', '')))

        source.extend(((u'ManaUser: ', 'b'),
                       (u'Coding (a lot).\r\n', 'i'),
                       (u'Argent: ', 'b'),
                       (u'Java code and technical insights into Morrowind files.\r\n', 'i'),
                       (u'FallenWizard: ', 'b'),
                       (u'Key shortcut for deletion in mods and saves tabs from Mash.\r\n', 'i'),
                       (u'\r\n', '')))

        source.extend(((u'Beryllium: ', 'b'),
                       (u'EE templates, bug reports and feedback.\r\n', 'i'),
                       (u'Abot: ', 'b'),
                       (u'Translations.\r\n', 'i'),
                       (u'Dragon32, Shasta Thorne: ', 'b'),
                       (u'Ref Removers.\r\n', 'i'),
                       (u'Oooiii, Stahpk, Abot, calemcc, Zikerocks, Valascon, KarmicKid and Pherim: ', 'b'),
                       (u'Vital bug reports and ideas.\r\n', 'i'),
                       (u'StaticNation: ', 'b'),
                       (u'The Wrye Mash bug finder champion.\r\n', 'i'),
                       (u'KOYK_GR: ', 'b'),
                       (u'New icon and Bug testing.', 'i')))
        return source

    def license(self):
        """License factory."""
        return (
                (u'Wrye Mash Polemos fork\r\n', 'b'),
                (u'Copyright (C) 2017-2019 Polemos\r\n', 'b'),
                (u'* based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version\r\n', 'i'),
                (u'* based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA\r\n', 'i'),
                (u'* based on code by Wrye copyright (C) 2005-2009 Wrye Mash\r\n', 'i'),

                (u'License: GPL version 2 or higher\r\n', 'b'),
                (u'GPL: http://www.gnu.org/licenses/gpl.html\r\n', 'b'),
                (u'\r\n', ''),

                (u'Copyright on the original code:\r\n', 'b'),
                (u'2005-2009 Wrye\r\n', 'i'),
                (u'Copyright on any non trivial code modifications or substantial code additions:\r\n', 'b'),
                (u'2009-2011 Melchor\r\n', 'i'),
                (u'2011-2016 Yacoby\r\n', 'i'),
                (u'2017-2019 Polemos\r\n', 'i'),
                (u'\r\n', ''),

                (u'Original Wrye Mash License and Copyright:\r\n', 'b'),
                (u'Wrye Mash is free software; you can redistribute it and/or ', ''),
                (u'modify it under the terms of the GNU General Public License ', ''),
                (u'as published by the Free Software Foundation; either version 2 ', ''),
                (u'of the License, or (at your option) any later version.\r\n', ''),
                (u'Wrye Bolt is distributed in the hope that it will be useful,\r\n', 'b'),
                (u'but WITHOUT ANY WARRANTY; without even the implied warranty of ', ''),
                (u'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the ', ''),
                (u'GNU General Public License for more details.\r\n', ''),
                (u'You should have received a copy of the GNU General Public License ', ''),
                (u'along with Wrye Mash; if not, write to the Free Software Foundation, ', ''),
                (u'Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA. ', 'i'),
                (u'Wrye Mash copyright (C) 2005, 2006, 2007, 2008, 2009 Wrye\r\n\r\n', ''),
                (u'\r\n', ''),

                (u'This software contains other softwares which fall under different Licenses:\r\n', 'b'),
                (u'7zip ', 'b'),

                (u'is licenced under LGPL\r\n', 'i'),
                (u'Python License:\r\n', 'b'),
                (u'https://www.python.org/download/releases/2.7/license/\r\n', 'i'),
                (u'wxPython License:\r\n', 'b'),
                (u'https://wxpython.org/pages/license/\r\n', 'i'),
                (u'Cole Bemis for icon Pack Feather:\r\n', 'b'),
                (u'CC BY 3.0, https://creativecommons.org/licenses/by/3.0/\r\n', 'i'),
                (u'Rafiqul Hassan for Blogger Iconset:\r\n', 'b'),
                (u'Freeware, http://www.iconarchive.com/show/blogger-icons-by-rafiqul-hassan.html\r\n', 'i'),
                (u'bobsobol for TES3 - Morrowind icon on DeviantArt:\r\n', 'b'),
                (u'CC Share Alike 3.0 License, https://www.deviantart.com/bobsobol/art/TES3-Morrowind-209901409\r\n', 'i')
        )
