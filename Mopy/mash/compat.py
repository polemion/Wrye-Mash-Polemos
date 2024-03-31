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

import sys, pickle, traceback
from datetime import datetime
from io import open
from . import appinfo


class MashUnpickler(pickle.Unpickler):
    """The same as pickle.Unpickler.find_class but translates module names."""

    def findClass(self, module, name):
        """Find class implementation."""
        try:
            if module in ('bolt', 'masher', 'balt', 'mash', 'mosh', 'mush'):
                module = 'mash.' + module
            __import__(module)
            mod = sys.modules[module]
            klass = getattr(mod, name)
            return klass
        except ImportError as e:
            print('%s: [Error] %s:\n%s' % (datetime.now(), e, traceback.format_exc()), end='')
        except AttributeError as e:
            print('%s: [Error] %s:\n%s' % (datetime.now(), e, traceback.format_exc()), end='')


def uncpickle(fPath):
    """Same as cPickle.loads(f) but does module name translation"""
    try:
        if isinstance(fPath, str):
            with open(fPath, 'rb') as f:
                pickleObj = MashUnpickler(f)
                return pickleObj.load()
        else:
            pickleObj = MashUnpickler(fPath)
            return pickleObj.load()
    except UnicodeDecodeError as e:  # Python3 pickle has changed dramatically from Python2
        print('%s: [Error] This is the Python3 version of %s, and you '
              'are trying to load configuration taken with a Python2 version. Will exit.' % (
              datetime.now(), appinfo.appName))
        return None
    except pickle.UnpicklingError as e:  # Ditto
        print('%s: [Error] This is the Python3 version of %s, and you '
              'are trying to load installers/table data taken with a Python2 version. Data will need to be refreshed.' % (
                  datetime.now(), appinfo.appName))
        return None
