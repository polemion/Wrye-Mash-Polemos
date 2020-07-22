# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
#
# Wrye Mash, Polemos fork Copyright (C) 2017-2020 Polemos
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

# Polemos: Tried to make it more efficient, hope I succeeded.

# Imports
from distutils.core import setup
from mash.gui.credits import Current_Version as raw
import scandir, py2exe, os, sys, imp, glob

# Info
verraw = [x.strip() for x in raw()[2].replace('-',',').replace('/',',').split(',')]
version = '0.%s.%s.%s' % (raw()[0], verraw[1], verraw[2])
company_name = "Polemos"
copyright = "Polemos 2017-%s (see 'license.txt' for full credits)" % verraw[2]
mashname = "Wrye Mash v%s %s" % (raw()[0], raw()[3])

# Retrieving wx install dir for getting gdiplus.dll
wxDlls = ["gdiplus.dll"]
import wx
wxDir = os.path.split(wx.__file__)[0]
del wx
wxDlls = [os.path.join(wxDir, a) for a in wxDlls]

# Paths
msvcppath = os.path.join(os.path.expandvars('%WINDIR%'), 'winsxs', '*', 'msvcp90.dll')
msvcrpath = os.path.join(os.path.expandvars('%WINDIR%'), 'winsxs', '*', 'msvcr90.dll')
msvcDlls = glob.glob(msvcppath) + glob.glob(msvcrpath)
dest_folder = '..\\bin\\Mopy'

# If you are building this you may need to change the public key for the dll files.
# It can be found in the manifest files in %windir%\winsxs\
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
<dependency>
    <dependentAssembly>
    <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''
RT_MANIFEST = 24

[sys.argv.remove(a) for a in sys.argv[1:] if a not in ['-q', 'py2exe']]
if "-q" not in sys.argv: sys.argv.append("-q")
if "py2exe" not in sys.argv: sys.argv.append("py2exe")

# Files/Folders Includes (supply 7z dir in here)
help_f = 'Wrye Mash.dat'
if os.path.exists('openmw.dat'): help_f = 'openmw.dat'
prog_resources = ['.\\7zip\\x86\\7z.exe',
                  '.\\7zip\\x86\\7z.dll',
                   help_f,
                  'Credits.txt',
                  'License.txt',
                  'cacert.pem',
                  ] + wxDlls + msvcDlls

# Remove old 'build' folder
if os.access('.\\build', os.F_OK):
    print 'Deleting old build folder...'
    for root, dirs, files in scandir.walk('.\\build', topdown=False):
        [os.remove(os.path.join(root, name)) for name in files]
        [os.rmdir(os.path.join(root, name)) for name in dirs]
    os.rmdir('.\\build')

# File Information
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.version = version
        self.company_name = company_name
        self.copyright = copyright
        self.name = mashname

# Includes for py2exe
includes = ["wx", "encodings.*"]
# Excludes for py2exe
excludes = ["Tkconstants", "Tkinter", "tcl", "doctest", "pdb", "unittest",
            "difflib", '_gtkagg', '_tkagg', 'bsddb', 'curses', #'email',
            'pywin.debugger', 'pywin.debugger.dbgcon', 'pywin.dialogs']
# dll Excludes
dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll', 'tk84.dll', 'msvcp90.dll',
                'UxTheme.dll', 'msvcr71.dll', 'IPHLPAPI.DLL', 'NSI.dll', 'WINNSI.DLL', 'WTSAPI32.dll']

# py2exe options
opts = {'py2exe': {'includes': includes,
                   'excludes': excludes,
                   "packages": ['wx.lib.pubsub', 'gzip'],
                   'dll_excludes': dll_excludes,
                   "compressed": 1,
                   "optimize": 2,
                   "ascii": 1,
                   "bundle_files": 1,
                   "dist_dir": dest_folder}}

# File Information
prog = Target(
    description='Morrowind mod organizer and tools.',
    author="Wrye, D.C.G, Yacoby, Polemos (see 'readme.txt' for full credits)",
    script='mash.py',
    icon_resources=[(0, ".\\images\\Wrye Mash.ico")],
    other_resources=[(RT_MANIFEST, 1, manifest_template % dict(prog="WryeMash"))],
)

# Py2exe stuff
setup(
    data_files=[('.', prog_resources)],
    zipfile=None,
    windows=[prog],
    options=opts,
    console=[prog]
)
from distutils import dir_util
dir_util.copy_tree('..\\Data Files', '..\\bin\\Data Files')
folds = ['Data', 'Extras', 'images', 'locale', 'snapshots', 'themes']
[dir_util.copy_tree(fold, '%s\\%s' % (dest_folder, fold)) for fold in folds]

# Delete unheeded files in bin dir.
toDel = ('w9xpopen.exe', 'gdiplus.dll', 'msvcp90.dll', 'msvcr90.dll')
for x in toDel:
    targ = os.path.join(dest_folder, x)
    if os.path.exists(targ):
        os.remove(targ)

# Compress with UPX (Antivirus programs often don't like that).
# Put upx executable in the same dir as the source.
if os.path.exists('upx.exe'):
    files = ( glob.glob(os.path.join(dest_folder, '*.dll'))
            + glob.glob(os.path.join(dest_folder, '*.exe')) )
    #note, --ultra-brute takes ages.
    #If you want a fast build change it to --best
    args = ['upx.exe', '--best'] + files
    os.spawnv(os.P_WAIT, 'upx.exe', args)
