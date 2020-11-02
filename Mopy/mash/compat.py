# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
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
Mash uses cPickle to store data. This means that whenever the code changes
much then it breaks backwards compatibility. The sane solution would be to
convert everything to use json. However for my sanity, this file
provides a workaround to enable the renaming of files


(This is not a nice solution)
"""

import sys
import cPickle

def findClass(module, name):
    """Find class implementation. The same as pickle.Unpickler.find_class but translates module names"""
    if module in ('bolt', 'masher', 'balt', 'mash', 'mosh', 'mush'):
        module = 'mash.' + module

    __import__(module)
    mod = sys.modules[module]
    klass = getattr(mod, name)
    return klass

def uncpickle(fPath):  # Polemos: Compatibility fix
    """Same as cPickle.loads(f) but does module name translation"""
    if type(fPath) is unicode or type(fPath) is str:
        try:
            with open(fPath, 'rb') as f:
                pickleObj = cPickle.Unpickler(f)
                pickleObj.find_global = findClass
                return pickleObj.load()
        except:
            with open(fPath, 'r') as f:
                # Polemos: The Python 2.x version of pickle has a
                # bug when in binary (slightly more efficient but
                # also needed for newer protocols), thus besides
                # compatibility with older saved Wrye Mash settings
                # it is needed as a failover. More info:
                # https://bugs.python.org/issue11564
                pickleObj = cPickle.Unpickler(f)
                pickleObj.find_global = findClass
                return pickleObj.load()
    else:
        pickleObj = cPickle.Unpickler(fPath)
        pickleObj.find_global = findClass
        return pickleObj.load()
