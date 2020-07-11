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


from unimash import _  # Polemos

# The Exception

class mError(Exception):
    """Generic Error"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


# Coding Errors

class AbstractError(mError):
    """Coding Error: Abstract code section called."""

    def __init__(self,message=_(u'Abstract section called.')):
        mError.__init__(self, message)

class ArgumentError(mError):
    """Coding Error: Argument out of allowed range of values."""

    def __init__(self, message=_(u'Argument is out of allowed ranged of values.')):
        mError.__init__(self, message)

class StateError(mError):
    """Error: Object is corrupted."""

    def __init__(self, message=_(u'Object is in a bad state.')):
        mError.__init__(self, message)

class UncodedError(mError):
    """Coding Error: Call to section of code that hasn't been written."""

    def __init__(self,message=_(u'Section is not coded yet.')):
        mError.__init__(self, message)

class ConfError(mError):  # Polemos
    """Config file errors. Same as abstract."""

    def __init__(self, message):
        mError.__init__(self, message)


# TES3 File Errors

class Tes3Error(mError):
    """TES3 Error: File is corrupted."""
    def __init__(self, inName, message):
        mError.__init__(self, message)
        self.inName = inName

    def __str__(self):
        if self.inName: return self.inName+': '+self.message
        else: return _(u'Unknown File: ')+self.message

class Tes3ReadError(Tes3Error):
    """TES3 Error: Attempt to read outside of buffer."""
    def __init__(self, inName, recType, tryPos, maxPos):
        self.recType = recType
        self.tryPos = tryPos
        self.maxPos = maxPos
        if tryPos < 0: message = (_(u'%s: Attempted to read before (%d) beginning of file/buffer.') % (recType, tryPos))
        else: message = (_(u'%s: Attempted to read past (%d) end (%d) of file/buffer.') % (recType, tryPos, maxPos))
        Tes3Error.__init__(self, inName, message)

class Tes3RefError(Tes3Error):
    """TES3 Error: Reference is corrupted."""
    def __init__(self, inName, cellId, objId, iObj, iMod, masterName=''):
        self.cellId = cellId
        self.iMod = iMod
        self.iObj = iObj
        self.objId = objId
        self.masterName = masterName
        message = (_(u'%s: Bad Ref: %s: objId: %s iObj: %d') % (inName, cellId, objId, iObj))
        if iMod: message += u' iMod: %d [%s]' % (iMod, masterName)
        Tes3Error.__init__(self, inName, message)

class Tes3SizeError(Tes3Error):
    """TES3 Error: Record/subrecord has wrong size."""
    def __init__(self, inName, recName, readSize, maxSize, exactSize=True):
        self.recName = recName
        self.readSize = readSize
        self.maxSize = maxSize
        self.exactSize = exactSize
        if exactSize: messageForm = _(u'%s: Expected size == %d, but got: %d ')
        else: messageForm = _(u'%s: Expected size <= %d, but got: %d ')
        Tes3Error.__init__(self, inName, messageForm % (recName, readSize, maxSize))

class Tes3UnknownSubRecord(Tes3Error):
    """TES3 Error: Unknown subrecord."""
    def __init__(self,inName,subName,recName):
        Tes3Error.__init__(self,inName,_(u'Extraneous subrecord (%s) in %s record.')
            % (subName,recName))


# Usage Errors

class MaxLoadedError(mError):
    """Usage Error: Attempt to add a mod to load list when load list is full."""
    def __init__(self, message=_(u'Load list is full.')):
        mError.__init__(self, message)

class SortKeyError(mError):
    """Unknown Error: Unrecognized sort key."""
    def __init__(self, message=_(u'Unrecognized sort key.')):
        mError.__init__(self, message)

# Various Errors
class MashError(mError):
    """Mash Error: Unrecognized sort key."""
    def __init__(self, col=u'', message=_(u'Unrecognized sort key')):
        if col is None: col=u''
        mError.__init__(self, u'%s%s%s' % (message, u': ' if col or col is None else u'.', col))

class InterfaceError(mError):
    """Interface Error."""
    pass
