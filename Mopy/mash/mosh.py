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

# Modified by D.C.-G. < 16:35 2010-06-11 > for UtilsPanel extension.
# Modified by Polemos :) in 2,000,000 places, 2018~.


import locale
import time
from threading import Thread as Thread # Polemos
from subprocess import PIPE, check_call  # Polemos
from sfix import Popen  # Polemos
import io, ushlex, scandir  # Polemos
from unimash import uniChk, encChk, _  # Polemos
import array, cPickle, cStringIO, copy, math, os, re, shutil, string
import struct, sys, stat,bolt
from bolt import LString, GPath, DataDict, SubProgress
import compat, mush
# Exceptions
from merrors import mError as MoshError, Tes3Error as Tes3Error
from merrors import AbstractError as AbstractError, ArgumentError as ArgumentError, StateError as StateError
from merrors import UncodedError as UncodedError, ConfError as ConfError
from merrors import Tes3ReadError as Tes3ReadError, Tes3RefError as Tes3RefError, Tes3SizeError as Tes3SizeError
from merrors import MaxLoadedError as MaxLoadedError, SortKeyError as SortKeyError, Tes3UnknownSubRecord as Tes3UnknownSubRecord


# Singletons, Constants
MashDir = os.path.dirname(sys.argv[0])  # Polemos
DETACHED_PROCESS = 0x00000008  # Polemos
#--File Singletons
mwIniFile = None    #--MWIniFile singleton
modInfos  = None    #--ModInfos singleton
saveInfos = None    #--SaveInfos singleton
#--Settings
dirs = {}
settings = None
#--Default settings
settingDefaults = {
    'mosh.modInfos.resetMTimes': 0,
    'mosh.modInfos.objectMaps': r'Mash\ObjectMaps.pkl',
    'mosh.fileInfo.backupDir': r'Mash\Backups',
    'mosh.fileInfo.hiddenDir': r'Mash\Hidden',
    'mosh.fileInfo.snapshotDir': r'Mash\Snapshots',
    }


def formatInteger(value):
    """Convert integer to string formatted to locale."""
    return locale.format('%d', int(value), 1)


def formatDate(value):   # Polemos
    """Convert time to string formatted to locale's default date/time."""
    form = '%x, %H:%M:%S'
    try: return time.strftime(form, time.localtime(value))
    except:  # Needed when installers are outside Unix Epoch
        return time.strftime(form, time.localtime(0))


def megethos(num):  # Polemos
        """Convert byte sizes to KBs, MBs or GBs."""
        digits = len(str(num))
        if digits <= 3: return '%dB' % (num)
        elif 4 <= digits <= 6: return '%dKB' % (num / 1024)
        elif 7 <= digits <= 9: return '%dMB' % (num / 1024 ** 2)
        elif digits >= 10: return '%dGB' % (num / 1024 ** 3)


# Data Dictionaries -----------------------------------------------------------

class Settings:  # Polemos: Added revert to backup configuration.
    """Settings dictionary. Changes are saved to pickle file."""

    def __init__(self, path='settings.pkl'):
        """Initialize. Read settings from pickle file."""
        self.path = path.encode('utf-8')
        self.changed = []
        self.deleted = []
        self.data = {}
        # Check if the settings file is missing and if there is an available backup to restore.
        if not os.path.exists(self.path) and os.path.exists(self.path + '.bak'):
            shutil.copyfile(os.path.join(MashDir, self.path + '.bak'), os.path.join(MashDir, self.path))
        # --Load
        if os.path.exists(self.path):
            inData = compat.uncpickle(self.path.encode('utf-8'))
            self.data.update(inData)

    def loadDefaults(self,defaults):
        """Add default settings to dictionary. Will not replace values that are already set."""
        for key in defaults.keys():
            if key not in self.data:
                self.data[key] = defaults[key]

    def save(self):
        """Save to pickle file. Only key/values marked as changed are saved."""
        #--Data file exists?
        filePath = self.path.encode('utf-8')
        if os.path.exists(filePath):
            outData = compat.uncpickle(filePath)
            #--Delete some data?
            for key in self.deleted:
                if key in outData: del outData[key]
        else: outData = {}
        #--Write touched data
        for key in self.changed: outData[key] = self.data[key]
        #--Pickle it
        tempPath = ('%s.tmp' % filePath).encode('utf-8')
        cPickle.dump(outData,open(tempPath.encode('utf-8'),'wb'), -1)
        renameFile(tempPath.encode('utf-8'),filePath.encode('utf-8'),True)

    def setChanged(self,key):
        """Marks given key as having been changed. Use if value is a dictionary, list or other object."""
        if key not in self.data: raise ArgumentError(_(u"No settings data for %s" % key))
        if key not in self.changed: self.changed.append(key)

    def getChanged(self,key,default=None):
        """Gets and marks as changed."""
        if default is not None and key not in self.data: self.data[key] = default
        self.setChanged(key)
        return self.data.get(key)

    #--Dictionary Emulation
    def has_key(self,key):
        """Dictionary emulation."""
        return self.data.has_key(key)
    def get(self,key,default=None):
        """Dictionary emulation."""
        return self.data.get(key.encode('utf-8'),default)
    def setdefault(self,key,default):
        """Dictionary emulation."""
        return self.data.setdefault(key.encode('utf-8'),default)
    def __contains__(self,key):
        """Dictionary emulation."""
        return self.data.has_key(key.encode('utf-8'))
    def __getitem__(self,key):
        """Dictionary emulation."""
        return self.data[key.encode('utf-8')]
    def __setitem__(self,key,value):
        """Dictionary emulation. Marks key as changed."""
        if key in self.deleted: self.deleted.remove(key)
        if key not in self.changed: self.changed.append(key)
        self.data[key] = value
    def __delitem__(self,key):
        """Dictionary emulation. Marks key as deleted."""
        if key in self.changed: self.changed.remove(key)
        if key not in self.deleted: self.deleted.append(key)
        del self.data[key]


class TableColumn:
    """Table accessor that presents table column as a dictionary."""
    def __init__(self,table,column):
        self.table = table
        self.column = column
    #--Dictionary Emulation
    def keys(self):
        """Dictionary emulation."""
        table = self.table
        column = self.column
        return [key for key in table.data.keys() if (column in table.data[key])]
    def has_key(self,key):
        """Dictionary emulation."""
        return self.__contains__(key)
    def clear(self):
        """Dictionary emulation."""
        self.table.delColumn(self.column)
    def get(self,key,default=None):
        """Dictionary emulation."""
        return self.table.getItem(key,self.column,default)
    def __contains__(self,key):
        """Dictionary emulation."""
        tableData = self.table.data
        return tableData.has_key(key) and tableData[key].has_key(self.column)
    def __getitem__(self,key):
        """Dictionary emulation."""
        return self.table.data[key][self.column]
    def __setitem__(self,key,value):
        """Dictionary emulation. Marks key as changed."""
        self.table.setItem(key,self.column,value)
    def __delitem__(self,key):
        """Dictionary emulation. Marks key as deleted."""
        self.table.delItem(key,self.column)


class Table:
    """Simple data table of rows and columns, saved in a pickle file."""
    def __init__(self,path):
        """Intialize and read data from file, if available."""
        self.path = path
        self.data = {}
        self.hasChanged = False
        #--Load
        if os.path.exists(self.path):
            inData = compat.uncpickle(self.path)
            self.data.update(inData)

    def save(self):  # Polemos: Unicode fix. Strange one. Was it mine? Questions, questions, questions... (a)
        """Saves to pickle file."""
        if self.hasChanged:
            filePath = self.path#.encode('utf-8')
            tempPath = '%s.tmp' % filePath
            fileDir = os.path.split(filePath)[0]
            if not os.path.exists(fileDir): os.makedirs(fileDir)
            cPickle.dump(self.data,open(tempPath,'wb'), -1)
            renameFile(tempPath,filePath,True)
            self.hasChanged = False

    def getItem(self,row,column,default=None):
        """Get item from row, column. Return default if row, column doesn't exist."""
        data = self.data
        if row in data and column in data[row]:
            return data[row][column]
        else: return default

    def getColumn(self,column):
        """Returns a data accessor for column."""
        return TableColumn(self,column)

    def setItem(self,row,column,value):
        """Set value for row, column."""
        data = self.data
        if row not in data:
            data[row] = {}
        data[row][column] = value
        self.hasChanged = True

    def delItem(self,row,column):
        """Deletes item in row, column."""
        data = self.data
        if row in data and column in data[row]:
            del data[row][column]
            self.hasChanged = True

    def delRow(self,row):
        """Deletes row."""
        data = self.data
        if row in data:
            del data[row]
            self.hasChanged = True

    def delColumn(self,column):
        """Deletes column of data."""
        data = self.data
        for rowData in data.values():
            if column in rowData:
                del rowData[column]
                self.hasChanged = True

    def moveRow(self,oldRow,newRow):
        """Renames a row of data."""
        data = self.data
        if oldRow in data:
            data[newRow] = data[oldRow]
            del data[oldRow]
            self.hasChanged = True

    def copyRow(self,oldRow,newRow):
        """Copies a row of data."""
        data = self.data
        if oldRow in data:
            data[newRow] = data[oldRow].copy()
            self.hasChanged = True

#------------------------------------------------------------------------------

class PickleDict(bolt.PickleDict):
    """Dictionary saved in a pickle file. Supports older mash pickle file formats."""
    def __init__(self,path,oldPath=None,readOnly=False):
        """Initialize."""
        bolt.PickleDict.__init__(self,path,readOnly)
        self.oldPath = oldPath or GPath('')

    def exists(self):
        """See if pickle file exists."""
        return (bolt.PickleDict.exists(self) or self.oldPath.exists())

    def load(self):
        """Loads vdata and data from file or backup file.

        If file does not exist, or is corrupt, then reads from backup file. If
        backup file also does not exist or is corrupt, then no data is read. If
        no data is read, then self.data is cleared.

        If file exists and has a vdata header, then that will be recorded in
        self.vdata. Otherwise, self.vdata will be empty.

        Returns:
        0: No data read (files don't exist and/or are corrupt)
        1: Data read from file
        2: Data read from backup file
        """
        result = bolt.PickleDict.load(self)
        if not result and self.oldPath.exists():
            self.data.update(compat.uncpickle(self.oldPath.parsePath()))
            result = 1
        #--Done
        return result

    def save(self):
        """Save to pickle file."""
        saved = bolt.PickleDict.save(self)
        if saved:
            self.oldPath.remove()
            self.oldPath.backup.remove()
        return saved


# Util Functions --------------------------------------------------------------


# Common re's, Unix new lines
reUnixNewLine = re.compile(r'(?<!\r)\n')
reSaveFile = re.compile('\.ess$',re.I)
reModExt  = re.compile(r'\.es[mp](.ghost)?$',re.I)

#--Version number in tes3.hedr
reVersion = re.compile(r'^(Version:?) *([-0-9\.]*\+?) *\r?$',re.M)

#--Misc
reExGroup = re.compile('(.*?),')


def cstrip(inString):
    """Convert c-string (null-terminated string) to python string."""
    zeroDex = inString.find('\x00')
    if zeroDex == -1: return inString
    else: return inString[:zeroDex]

def dictFromLines(lines,sep=None):
    """Generate a dictionary from a string with lines, stripping comments and skipping empty strings."""
    reComment = re.compile('#.*')
    temp = [reComment.sub('',x).strip() for x in lines.split('\n')]
    if sep is None or type(sep) == type(''):
        temp = dict([x.split(sep,1) for x in temp if x])
    else: #--Assume re object.
        temp = dict([sep.split(x,1) for x in temp if x])
    return temp

def getMatch(reMatch,group=0):
    """Returns the match or an empty string."""
    if reMatch: return reMatch.group(group)
    else: return ''

y2038Resets = []
def getmtime(path):
    """Returns mtime for path. But if mtime is outside of epoch, then resets mtime to an in-epoch date and uses that."""
    import random
    mtime = os.path.getmtime(path)
    #--Y2038 bug? (os.path.getmtime() can't handle years over unix epoch)
    if mtime <= 0:
        #--Kludge mtime to a random time within 10 days of 1/1/2037
        mtime = time.mktime((2037,1,1,0,0,0,3,1,0))
        mtime += random.randint(0,10*24*60*60) #--10 days in seconds
        os.utime(path,(time.time(),mtime))
        y2038Resets.append(os.path.basename(path))
    return mtime

def iff(bool,trueValue,falseValue):
    """Return true or false value depending on a boolean test."""
    if bool: return trueValue
    else: return falseValue

def invertDict(indict):
    """Invert a dictionary."""
    return {y: x for x, y in indict.items()}

def listFromLines(lines):
    """Generate a list from a string with lines, stripping comments and skipping empty strings."""
    reComment = re.compile('#.*')
    temp = [reComment.sub('',x).strip() for x in lines.split('\n')]
    temp = [x for x in temp if x]
    return temp

def listSubtract(alist,blist):
    """Return a copy of first list minus items in second list."""
    result = []
    for item in alist:
        if item not in blist:
            result.append(item)
    return result

def renameFile(oldPath,newPath,makeBack=False):
    """Moves file from oldPath to newPath. If newPath already exists then it
    will either be moved to newPath.bak or deleted depending on makeBack."""
    if os.path.exists(newPath):
        if makeBack:
            backPath = '%s.bak' % newPath
            if os.path.exists(backPath): os.remove(backPath)
            os.rename(newPath,backPath)
        else: os.remove(newPath)
    os.rename(oldPath,newPath)

def rgbString(red,green,blue):
    """Converts red, green blue ints to rgb string."""
    return chr(red)+chr(green)+chr(blue)

def rgbTuple(rgb):
    """Converts red, green, blue string to tuple."""
    return struct.unpack('BBB',rgb)

def winNewLines(inString):
    """Converts unix newlines to windows newlines."""
    return reUnixNewLine.sub('\r\n',inString)

# IO Wrappers -----------------------------------------------------------------

class Log:
    """Log Callable. This is the abstract/null version. Useful version should
    override write functions.

    Log is divided into sections with headers. Header text is assigned (through
    setHeader), but isn't written until a message is written under it. I.e.,
    if no message are written under a given header, then the header itself is
    never written."""

    def __init__(self):
        """Initialize."""
        self.header = None
        self.prevHeader = None
        self.indent = ''

    def setHeader(self,header):
        """Sets the header."""
        self.header = header

    def __call__(self,message):
        """Callable. Writes message, and if necessary, header and footer."""
        if self.header != self.prevHeader:
            if self.prevHeader:
                self.writeFooter()
            if self.header:
                self.writeHeader(self.header)
            self.prevHeader = self.header
        self.writeMessage(message)

    #--Abstract/null writing functions...
    def writeHeader(self,header):
        """Write header. Abstract/null version."""
        pass
    def writeFooter(self):
        """Write mess. Abstract/null version."""
        pass
    def writeMessage(self,message):
        """Write message to log. Abstract/null version."""
        pass

#------------------------------------------------------------------------------

class LogFile(Log): # Polemos, just in case...
    """Log that writes messages to file."""
    def __init__(self,out):
        self.out = out
        Log.__init__(self)

    def writeHeader(self,header):
        self.out.write('%s%s\n' % (self.indent, header))

    def writeFooter(self):
        self.out.write('%s\n' % self.indent)

    def writeMessage(self,message): # Polemos fix
        try: self.out.write('%s%s\n' % (self.indent, message))
        except: self.out.write('%s%s\n' % (self.indent, message.encode('utf-8')))

#------------------------------------------------------------------------------

class Progress:
    """Progress Callable: Shows progress on message change and at regular intervals."""
    def __init__(self,interval=0.5):
        self.interval = interval
        self.message = None
        self.time = 0
        self.base = 0.0
        self.scale = 1.0
        self.max = 1.0

    def setBaseScale(self,base=0.0,scale=1.0):
        if scale == 0: raise ArgumentError(_(u'Scale must not equal zero!'))
        self.base = base
        self.scale = scale

    def setMax(self,max):
        self.max = 1.0*max or 1.0 #--Default to 1.0

    def __call__(self,rawProgress,message=None):
        if not message: message = self.message
        if ((message != self.message) or
            (time.time() > (self.time+self.interval))):
            self.doProgress(self.base+self.scale*rawProgress/self.max, message)
            self.message = message
            self.time = time.time()

    def doProgress(self,progress,message):
        """Default doProgress does nothing."""
        try: yield progress, message
        except: pass

#------------------------------------------------------------------------------

class ProgressFile(Progress):
    """Prints progress to file (stdout by default)."""
    def __init__(self,interval=0.5,out=None):
        Progress.__init__(self,interval)
        self.out = out

    def doProgress(self,progress,message):
        out = self.out or sys.stdout #--Defaults to stdout
        out.write('%0.2f %s\n' % (progress,message))

#------------------------------------------------------------------------------

class Tes3Reader:
    """Wrapper around an TES3 file in read mode.
    Will throw a Tes3ReadError if read operation fails to return correct size."""
    def __init__(self,inName,ins):
        """Initialize."""
        self.inName = inName
        self.ins = ins
        #--Get ins size
        curPos = ins.tell()
        ins.seek(0,2)
        self.size = ins.tell()
        ins.seek(curPos)

    #--IO Stream ------------------------------------------
    def seek(self,offset,whence=0,recType='----'):
        """File seek."""
        if whence == 1: newPos = self.ins.tell()+offset
        elif whence == 2: newPos = self.size + offset
        else: newPos = offset
        if newPos < 0 or newPos > self.size: raise Tes3ReadError(self.inName, recType, newPos, self.size)
        self.ins.seek(offset,whence)

    def tell(self):
        """File tell."""
        return self.ins.tell()

    def close(self):
        """Close file."""
        self.ins.close()

    def atEnd(self):
        """Return True if current read position is at EOF."""
        return (self.ins.tell() == self.size)

    #--Read/unpack ----------------------------------------
    def read(self,size,recType='----'):
        """Read from file."""
        endPos = self.ins.tell() + size
        if endPos > self.size:
            raise Tes3SizeError(self.inName, recType,endPos,self.size)
        return self.ins.read(size)

    def unpack(self,format,size,recType='-----'):
        """Read file and unpack according to struct format."""
        endPos = self.ins.tell() + size
        if endPos > self.size:
            raise Tes3ReadError(self.inName, recType,endPos,self.size)
        return struct.unpack(format,self.ins.read(size))

    def unpackRecHeader(self):
        """Unpack a record header."""
        return self.unpack('4s3i',16,'REC_HEAD')

    def unpackSubHeader(self,recType='----',expName=None,expSize=0):
        """Unpack a subrecord header. Optionally checks for match with expected name and size."""
        (name,size) = self.unpack('4si',8,recType+'.SUB_HEAD')
        #--Match expected name?
        if expName and expName != name:
            raise Tes3Error(self.inName,_(u'%s: Expected %s sub-record, but found %s instead.') % (recType,expName,name))
        #--Match expected size?
        if expSize and expSize != size:
            raise Tes3SizeError(self.inName,recType+'.'+name,size,expSize,True)
        return (name,size)

    #--Find data ------------------------------------------
    def findSubRecord(self,subName,recType='----'):
        """Finds subrecord with specified name."""
        while not self.atEnd():
            (name,size) = self.unpack('4si',8,recType+'.SUB_HEAD')
            if name == subName: return self.read(size,recType+'.'+subName)
            else: self.seek(size,1,recType+'.'+name)
        #--Didn't find it?
        else: return None

#------------------------------------------------------------------------------

class Tes3Writer:
    """Wrapper around an TES3 output stream. Adds utility functions."""
    def __init__(self,out):
        """Initialize."""
        self.out = out

    #--Stream Wrapping
    def write(self,data):
        self.out.write(data)

    def getvalue(self):
        return self.out.getvalue()

    def close(self):
        self.out.close()

    #--Additional functions.
    def pack(self,format,*data):
        self.out.write(struct.pack(format,*data))

    def packSub(self,type,data,*values):
        """Write subrecord header and data to output stream.
        Call using either packSub(type,data), or packSub(type,format,values)."""
        if values: data = struct.pack(data,*values)
        self.out.write(struct.pack('4si',type,len(data)))
        self.out.write(data)

    def packSub0(self,type,data): # Polemos: todo: Are unicode chars allowed in a saved game?
        """Write subrecord header and data + null terminator to output stream."""
        self.out.write(struct.pack('4si',type,len(data)+1))
        self.out.write(data)
        self.out.write('\x00')

# TES3 Abstract ---------------------------------------------------------------

class SubRecord:
    """Generic Subrecord."""
    def __init__(self,name,size,ins=None,unpack=False):
        self.changed = False
        self.name = name
        self.size = size
        self.data = None
        self.inName = ins and getattr(ins,'inName',None)
        if ins: self.load(ins,unpack)

    def load(self,ins,unpack=False):
        self.data = ins.read(self.size,'----.----')

    def setChanged(self,value=True):
        """Sets changed attribute to value. [Default = True.]"""
        self.changed = value

    def setData(self,data):
        """Sets data and size."""
        self.data = data
        self.size = len(data)

    def getSize(self):
        """Return size of self.data, after, if necessary, packing it."""
        if not self.changed: return self.size
        #--StringIO Object
        out = Tes3Writer(cStringIO.StringIO())
        self.dumpData(out)
        #--Done
        self.data = out.getvalue()
        self.data.close()
        self.size = len(self.data)
        self.setChanged(False)
        return self.size

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        raise AbstractError

    def dump(self,out):
        if self.changed: raise StateError(_(u'Data changed: ')+ self.name)
        if not self.data: raise StateError(_(u'Data undefined: ')+self.name)
        out.write(struct.pack('4si',self.name,len(self.data)))
        out.write(self.data)


class Record:
    """Generic Record."""
    def __init__(self,name,size,delFlag,recFlag,ins=None,unpack=False):
        self.changed = False
        self.name = name
        self.size = size
        self.delFlag = delFlag
        self.recFlag = recFlag
        self.data = None
        self.id = None
        self.inName = ins and getattr(ins,'inName',None)
        if ins: self.load(ins,unpack)

    def load(self,ins=None,unpack=False):
        """Load data from ins stream or internal data buffer."""
        name = self.name
        #--Read, but don't analyze.
        if not unpack:
            self.data = ins.read(self.size,name)
        #--Read and analyze ins.
        elif ins:
            inPos = ins.tell()
            self.loadData(ins)
            ins.seek(inPos,0,name+'_REWIND')
            self.data = ins.read(self.size,name)
        #--Analyze internal buffer.
        else:
            reader = Tes3Reader(self.inName,cStringIO.StringIO(self.data))
            self.loadData(reader)
            reader.close()

    def loadData(self,ins):
        """Loads data from input stream. Called by load()."""
        raise AbstractError

    def setChanged(self,value=True):
        """Sets changed attribute to value. [Default = True.]"""
        self.changed = value

    def setData(self,data):
        """Sets data and size."""
        self.data = data
        self.size = len(data)

    def getSize(self):  # Polemos: Removed duplicate.
        """Return size of self.data, after, if necessary, packing it."""
        if not self.changed: return self.size
        #--Pack data and return size.
        out = Tes3Writer(cStringIO.StringIO())
        self.dumpData(out)
        self.data = out.getvalue()
        out.close()
        self.size = len(self.data)
        self.setChanged(False)
        return self.size

    def dumpData(self,out):
        """Dumps state into data. Called by getSize()."""
        raise AbstractError

    def dump(self,out):
        """Dumps record header and data into output file stream."""
        if self.changed: raise StateError(_(u'Data changed: ')+ self.name)
        if not self.data: raise StateError(_(u'Data undefined: ')+self.name)
        out.write(struct.pack('4s3i',self.name,self.size,self.delFlag,self.recFlag))
        out.write(self.data)

    def getId(self):
        """Get id. Doesn't work for all record types."""
        if getattr(self,'id',None):
            return self.id
        name = self.name
        #--Singleton records
        if name in frozenset(('FMAP','GAME','JOUR','KLST','PCDT','REFR','SPLM','TES3')):
            return None
        #--Special records.
        elif name == 'CELL':
            reader = self.getReader()
            srName = reader.findSubRecord('NAME',name)
            srData = reader.findSubRecord('DATA',name)
            (flags,gridX,gridY) = struct.unpack('3i',self.data)
            if flags & 1: self.id = cstrip(srName)
            else: self.id = '[%d,%d]' % (gridX,gridY)
        elif name == 'INFO':
            srData = self.getReader().findSubRecord('INAM',name)
            self.id = cstrip(srData)
        elif name == 'LAND':
            srData = self.getReader().findSubRecord('INTV',name)
            self.id = '[%d,%d]' % struct.unpack('2i',srData)
        elif name == 'PGRD':
            reader = self.getReader()
            srData = reader.findSubRecord('DATA',name)
            srName = reader.findSubRecord('NAME',name)
            gridXY = struct.unpack('2i',srData[:8])
            if srData != (0,0) or not srName:
                self.id = '[%d,%d]' % gridXY
            else: self.id = cstrip(srName)
        elif name == 'SCPT':
            srData = self.getReader().findSubRecord('SCHD',name)
            self.id = cstrip(srData[:32])
        #--Most records: id in NAME record.
        else:
            srData = self.getReader().findSubRecord('NAME',name)
            self.id = srData and cstrip(srData)
        #--Done
        return self.id

    def getReader(self):
        """Returns a Tes3Reader wrapped around self.data."""
        return Tes3Reader(self.inName,cStringIO.StringIO(self.data))


class ContentRecord(Record):
    """Content record. Abstract parent for CREC, CNTC, NPCC record classes."""
    def getId(self):
        """Returns base + index id. E.g. crate_mine00000001"""
        return '%s%08X' % (self.id,self.index)


class ListRecord(Record):
    """Leveled item or creature list. Does all the work of Levc and Levi classes."""
    def __init__(self,name,size,delFlag,recFlag,ins=None,unpack=False):
        """Initialize."""
        #--Record type.
        if name not in ('LEVC','LEVI'):
            raise ArgumentError(_(u'Type must be either LEVC or LEVI.'))
        #--Data
        self.id = None
        self.calcFromAllLevels = False
        self.calcForEachItem = False
        self.chanceNone = 0
        self.count = 0
        self.entries = []
        self.isDeleted = False
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        """Load data from stream or own data."""
        #--Read subrecords
        bytesRead = 0
        objectId = None
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader(self.name)
            bytesRead += 8+size
            subData = ins.read(size, self.name+'.'+name)
            #--Id?
            if name == 'NAME': self.id = cstrip(subData)
            #--Flags
            elif name == 'DATA':
                flags = struct.unpack('i',subData)[0]
                if self.name == 'LEVC':
                    self.calcFromAllLevels = (flags & 1) == 1
                else:
                    self.calcForEachItem = (flags & 1) == 1
                    self.calcFromAllLevels = (flags & 2) == 2
            #--Chance None
            elif name == 'NNAM':
                self.chanceNone = struct.unpack('B',subData)[0]
            #--Count
            elif name == 'INDX':
                self.count = struct.unpack('i',subData)[0]
            #--Creature/Item Id?
            elif name == 'CNAM' or name == 'INAM':
                objectId = cstrip(subData)
            #--PC Level
            elif name == 'INTV':
                pcLevel = struct.unpack('h',subData)[0]
                self.entries.append((pcLevel,objectId))
                objectId = None
            #--Deleted?
            elif name == 'DELE': self.isDeleted = True
            #--Else
            else: raise Tes3UnknownSubRecord(self.inName,name,self.name)
        #--No id?
        if not self.id:
            raise Tes3Error(self.inName,_(u'No id for %s record.') % (self.name,))
        #--Bad count?
        if self.count != len(self.entries):
            self.count = len(self.entries)
            self.setChanged()

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Header
        out.packSub0('NAME',self.id)
        if getattr(self,'isDeleted',False):
            out.packSub('DELE','i',0)
            return
        if self.name == 'LEVC':
            flags = 1*self.calcFromAllLevels
            etype = 'CNAM'
        else:
            flags = 1*self.calcForEachItem + 2*self.calcFromAllLevels
            etype = 'INAM'
        out.packSub('DATA','i',flags)
        out.packSub('NNAM','B',self.chanceNone)
        out.packSub('INDX','i',len(self.entries))
        #--Entries
        for pcLevel, objectId in self.entries:
            out.packSub0(etype,objectId)
            out.packSub('INTV','h',pcLevel)

    def mergeWith(self,newLevl):
        """Merges newLevl settings and entries with self."""
        #--Clear
        self.data = None
        self.setChanged()
        #--Merge settings
        self.isDeleted = newLevl.isDeleted
        self.chanceNone = newLevl.chanceNone
        self.calcFromAllLevels = self.calcFromAllLevels or newLevl.calcFromAllLevels
        self.calcForEachItem = self.calcForEachItem or newLevl.calcForEachItem
        #--Merge entries
        entries = self.entries
        oldEntries = set(entries)
        for entry in newLevl.entries:
            if entry not in oldEntries:
                entries.append(entry)
        #--Sort entries by pcLevel
        self.entries.sort(key=lambda a: a[0])


# TES3 Data --------------------------------------------------------------------


class Book(Record):
    """BOOK record."""
    def __init__(self,name='BOOK',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialization."""
        self.model = 'Add Art File'
        self.teaches = -1
        self.weight = self.value = self.isScroll = self.enchantPoints = 0
        self.title = self.script = self.icon = self.text = self.enchant = None
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        """Loads from ins/internal data."""
        self.isDeleted = False
        #--Read subrecords
        bytesRead = 0
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('BOOK')
            srData = ins.read(size,'BOOK.'+name)
            bytesRead += 8+size
            if   name == 'NAME': self.id = cstrip(srData)
            elif name == 'MODL': self.model = cstrip(srData)
            elif name == 'FNAM': self.title = cstrip(srData)
            elif name == 'BKDT':
                (self.weight,self.value,self.isScroll,self.teaches,self.enchantPoints
                    ) = struct.unpack('f4i',srData)
            elif name == 'SCRI': self.script = cstrip(srData)
            elif name == 'ITEX': self.icon = cstrip(srData)
            elif name == 'TEXT': self.text = cstrip(srData)
            elif name == 'ENAM': self.enchant = cstrip(srData)
            #--Deleted?
            elif name == 'DELE': self.isDeleted = True
            #--Bad record?
            else:
                raise Tes3Error(self.inName,_(u'Extraneous subrecord (%s) in %s record.')
                    % (name,self.name))

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        out.packSub0('NAME',self.id)
        if getattr(self,'isDeleted',False):
            out.packSub('DELE','i',0)
            return
        out.packSub0('MODL',self.model)
        if self.title:   out.packSub0('FNAM',self.title)
        out.packSub('BKDT','f4i',
            self.weight, self.value, self.isScroll, self.teaches, self.enchantPoints)
        if self.script:  out.packSub0('SCRI',self.script)
        if self.icon:    out.packSub0('ITEX',self.icon)
        if self.text:    out.packSub0('TEXT',self.text)
        if self.enchant: out.packSub0('TEXT',self.enchant)

#------------------------------------------------------------------------------

class Cell_Acdt(SubRecord):
    """In-game character attributes sub-record."""
    pass


class Cell_Chrd(SubRecord):
    """In-game character skill sub-record."""
    pass


class Cell_Frmr:
    """Proxy for FRMR/NAME record combo. Exists only to keep other functions from getting confused."""
    def __init__(self):
        self.name = 'FRMR_PROXY'


class Cell_Objects:
    """Objects in cell. Combines both early and temp objects."""
    def __init__(self,cell):
        self.cell = cell

    def list(self):
        """Return combined list of early and temp objects."""
        return self.cell.objects+self.cell.tempObjects

    def remove(self,object):
        """Remove specified object from appropriate list."""
        if object in self.cell.objects:
            self.cell.objects.remove(object)
        else:
            self.cell.tempObjects.remove(object)
        self.cell.setChanged()

    def replace(self,object,newObject):
        """Replace old object with new object."""
        if object in self.cell.objects:
            objIndex = self.cell.objects.index(object)
            self.cell.objects[objIndex] = newObject
        else:
            objIndex = self.cell.tempObjects.index(object)
            self.cell.tempObjects[objIndex] = newObject
        self.cell.setChanged()

    def isTemp(self,object):
        """Return True if object is a temp object."""
        return (object in self.tempObjects)

#------------------------------------------------------------------------------

class Cell(Record):
    """Cell record. Name, region, objects in cell, etc."""
    def __init__(self,name='CELL',size=0,delFlag=0,recFlag=0,ins=None,unpack=False,skipObjRecords=False):
        #--Arrays
        self.skipObjRecords = skipObjRecords
        self.records = [] #--Initial records
        self.objects = []
        self.tempObjects = []
        self.endRecords = [] #--End records (map notes)
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        skipObjRecords = self.skipObjRecords
        #--Name
        (name,size) = ins.unpackSubHeader('CELL','NAME')
        self.cellName = cstrip(ins.read(size,'CELL.NAME'))
        bytesRead = 8+size
        #--Other Records
        subGroup = 0 #--0:(start) records; 10: (early) objects; 20: temp objects; 30:end records
        nam0 = 0 #--Temp record count from file
        printCell = 0
        objRecords = None
        isMoved = False
        isSpawned = False
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('CELL')
            #--New reference?
            if name == 'FRMR':
                if not subGroup: subGroup = 10
                #--Spawned? Then just another subrecord.
                if isSpawned:
                    isSpawned = False
                    if skipObjRecords:
                        ins.seek(size,1,'CELL.FRMR')
                    else:
                        objRecords.append(SubRecord(name,size,ins))
                    bytesRead += 8 + size
                #--New Record?
                else:
                    if size != 4: raise Tes3SizeError(self.inName,'CELL.FRMR',size,4,True)
                    rawData = ins.read(4,'CELL.FRMR')
                    iMod = struct.unpack('3xB',rawData)[0]
                    iObj = struct.unpack('i',rawData[:3]+'\x00')[0]
                    bytesRead  += 12
                    (name,size) = ins.unpackSubHeader('CELL','NAME')
                    objId = cstrip(ins.read(size,'CELL.NAME_NEXT'))
                    bytesRead += 8 + size
                    if skipObjRecords:
                        pass
                    elif isMoved:
                        isMoved = False
                        objRecords.append(Cell_Frmr())
                    else:
                        objRecords = [Cell_Frmr()]
                    #--Save Object
                    object = (iMod,iObj,objId,objRecords)
                    if subGroup == 10:
                        self.objects.append(object)
                    else:
                        self.tempObjects.append(object)
            #--Leveled Creature? (Ninja Monkey)
            elif name == 'LVCR':
                isSpawned = True
                if skipObjRecords:
                    ins.seek(size,1,'CELL.LVCR')
                else:
                    objRecords.append(SubRecord(name,size,ins))
                bytesRead += 8 + size
            #--Map Note?
            elif name == 'MPCD':
                subGroup = 30
                self.endRecords.append(SubRecord(name,size,ins))
                bytesRead += 8 + size
            #--Move Ref?
            elif name == 'MVRF' and not isSpawned:
                if not subGroup: subGroup = 10
                isMoved = True
                if skipObjRecords:
                    ins.seek(size,1,'CELL.MVRF')
                else:
                    objRecords = [SubRecord(name,size,ins)]
                bytesRead += 8 + size
            #--Map Note?
            elif name == 'NAM0':
                if subGroup >= 20:
                    raise Tes3Error(self.ins, self.getId()+_(u': Second NAM0 subrecord.'))
                subGroup = 20
                if size != 4: raise Tes3SizeError(self.inName,'CELL.NAM0',size,4,True)
                if size != 4: raise Tes3SizeError(self.inName,'CELL.NAM0',size,4,True)
                nam0 = ins.unpack('i',4,'CELL.NAM0')[0]
                bytesRead += 8 + size
            #--Start subrecord?
            elif not subGroup:
                record = SubRecord(name,size,ins)
                self.records.append(record)
                if name == 'DATA':
                    (self.flags,self.gridX,self.gridY) = struct.unpack('3i',record.data)
                bytesRead += 8 + size
            #--Object sub-record?
            elif subGroup < 30:
                #if isSpawned:
                if skipObjRecords:
                    ins.seek(size,1,'CELL.SubRecord')
                else:
                    objRecords.append(SubRecord(name,size,ins))
                bytesRead += 8 + size
            #--End subrecord?
            elif subGroup == 30:
                self.endRecords.append(SubRecord(name,size,ins))
                bytesRead += 8 + size
        #--Nam0 miscount?
        if nam0 != len(self.tempObjects):
            self.setChanged()

    def getObjects(self):
        """Return a Cell_Objects instance."""
        return Cell_Objects(self)

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Get sizes and dump into dataIO
        out.packSub0('NAME',self.cellName)
        #--Hack: Insert data record if necessary
        for record in self.records:
            if record.name == 'DATA': break
        else:
            self.records.insert(0,SubRecord('DATA',0))
        #--Top Records
        for record in self.records:
            if record.name == 'DATA':
                record.setData(struct.pack('3i',self.flags,self.gridX,self.gridY))
            record.getSize()
            record.dump(out)
        #--Objects
        inTempObjects = False
        for object in self.getObjects().list():
            #--Begin temp objects?
            if not inTempObjects and (object in self.tempObjects):
                out.packSub('NAM0','i',len(self.tempObjects))
                inTempObjects = True
            (iMod,iObj,objId,objRecords) = object
            for record in objRecords:
                #--FRMR/NAME placeholder?
                if isinstance(record, Cell_Frmr):
                    out.pack('4si','FRMR',4)
                    out.write(struct.pack('i',iObj)[:3])
                    out.pack('B',iMod)
                    out.packSub0('NAME',objId)
                else:
                    record.getSize()
                    record.dump(out)
        #--End Records
        for endRecord in self.endRecords:
            endRecord.getSize()
            endRecord.dump(out)

    def getId(self):
        #--Interior Cell?
        if (self.flags & 1):
            return self.cellName
        else:
            return ('[%d,%d]' % (self.gridX,self.gridY))

    def cmpId(self,other):
        """Return cmp value compared to other cell for sorting."""
        selfIsInterior = self.flags & 1
        otherIsInterior = other.flags & 1
        #--Compare exterior/interior. (Exterior cells sort to top.)
        if selfIsInterior != otherIsInterior:
            #--Return -1 if self is exterior
            return (-1 + 2*(selfIsInterior))
        #--Interior cells?
        elif selfIsInterior:
            return cmp(self.cellName,other.cellName)
        #--Exterior cells?
        elif self.gridX != other.gridX:
            return cmp(self.gridX,other.gridX)
        else:
            return cmp(self.gridY,other.gridY)

#------------------------------------------------------------------------------

class Crec(ContentRecord):
    """CREC record. Creature contents."""
    def __init__(self,name='CREC',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.index = 0
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Name
        (name,size) = ins.unpackSubHeader('CREC','NAME')
        self.id = cstrip(ins.read(size,'CREC.NAME'))
        #--Index
        (name,size) = ins.unpackSubHeader('CELL','INDX')
        self.index = ins.unpack('i',size,'CREC.INDX')[0]

#------------------------------------------------------------------------------

class Cntc(ContentRecord):
    """CNTC record. Container contents."""
    def __init__(self,name='CNTC',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.index = 0
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Name
        (name,size) = ins.unpackSubHeader('CNTC','NAME')
        self.id = cstrip(ins.read(size,'CNTC.NAME'))
        #--Index
        (name,size) = ins.unpackSubHeader('CNTC','INDX')
        self.index = ins.unpack('i',size,'CTNC.INDX')[0]

#------------------------------------------------------------------------------

class Dial(Record):
    """DIAL record. Name of dialog topic/greeting/journal name, etc."""
    def __init__(self,name='DIAL',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.type = 0
        self.unknown1 = None
        self.dele = None
        self.data = None
        self.infos = []
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Id
        (name,size) = ins.unpackSubHeader('DIAL','NAME')
        self.id = cstrip(ins.read(size,'DIAL.NAME'))
        bytesRead = 8+size
        #--Type
        (name,size) = ins.unpackSubHeader('DIAL','DATA')
        if size == 1:
            self.type = ins.unpack('B',size,'DIAL.DATA')[0]
        elif size == 4:
            (self.type,self.unknown1) = ins.unpack('B3s',size,'DIAL.DATA')
        else:
            raise Tes3SizeError(self.inName,'DIAL.DATA',size,4,False)
        bytesRead += 8+size
        #--Dele?
        if size == 4:
            (name,size) = ins.unpackSubHeader('DIAL','DELE')
            self.dele = ins.read(size,'DIAL.DELE')
            bytesRead += 8+size
        if bytesRead != self.size:
            raise Tes3Error(self.inName,_(u'DIAL %d %s: Unexpected subrecords') % (self.type,self.id))

    def sortInfos(self):
        """Sorts infos by link order."""
        #--Build infosById
        infosById = {}
        for info in self.infos:
            if info.id is None: raise Tes3Error(self.inName, _(u'Dialog %s: info with missing id.') % (self.id,))
            infosById[info.id] = info
        #--Heads
        heads = []
        for info in self.infos:
            if info.prevId not in infosById:
                heads.append(info)
        #--Heads plus their next chains
        newInfos = []
        for head in heads:
            nextInfo = head
            while nextInfo:
                newInfos.append(nextInfo)
                nextInfo = infosById.get(nextInfo.nextId)
        #--Anything left?
        for info in self.infos:
            if info not in newInfos:
                newInfos.append(info)
        #--Replace existing list
        self.infos = newInfos

#------------------------------------------------------------------------------

class Fmap(Record):
    """FMAP record. Worldmap for savegame."""
    #--Class data
    DEEP    = rgbString(25,36,33)
    SHALLOW = rgbString(37,55,50)
    LAND    = rgbString(62,45,31)
    GRID    = rgbString(27,40,37)
    BORDER  = SHALLOW
    MARKED  = rgbString(202,165,96)

    def __init__(self,name='FMAP',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialize."""
        self.mapd = None #--Array of 3 byte strings when expanded (512x512)
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Header
        out.packSub('MAPH','ii',512,9)
        #--Data
        out.pack('4si','MAPD',512*512*3)
        out.write(''.join(self.mapd))

    def edit(self):
        """Prepare data for editing."""
        wmap = 512
        if not self.mapd:
            data = self.data[24:]
            mapd = self.mapd = []
            for index in xrange(0,3*wmap*wmap,3):
                mapd.append(data[index:index+3])
        self.setChanged()

    def drawRect(self,color,x1,y1,x2,y2):
        """Draw rectangle of specified color."""
        if not self.changed: self.edit()
        wmap = 512
        mapd = self.mapd
        for y in xrange(y1,y2):
            ymoff = wmap*y
            for x in xrange(x1,x2):
                mapd[x+ymoff] = color

    def drawBorder(self,color,x1,y1,x2,y2,thick):
        """Draw's a border rectangle of specified thickness."""
        self.drawRect(color,x1,y1,x2,y1+thick)
        self.drawRect(color,x1,y1,x1+thick,y2)
        self.drawRect(color,x2-thick,y1,x2,y2)
        self.drawRect(color,x1,y2-thick,x2,y2)

    def drawGrid(self,gridLines=True):
        """Draw grid for visible map."""
        if not self.changed: self.edit()
        cGrid = Fmap.GRID
        cBorder = Fmap.BORDER
        if gridLines: #--Some fools don't want the grid!
            #--Grid
            for uv in xrange(-25,26,5):
                xy = 512/2 - 9*uv + 4
                self.drawRect(cGrid,0,xy,512,xy+1)
                self.drawRect(cGrid,xy,0,xy+1,512)
            #--Grid axes
            xy = 512/2 + 4
            self.drawRect(cBorder,0,xy,512,xy+1)
            self.drawRect(cBorder,xy,0,xy+1,512)
        #--Border
        self.drawBorder(cBorder,0,0,512,512,4)

    def drawCell(self,land,uland,vland,marked):
        """Draw a cell from landscape record."""
        from math import sqrt, pow
        #--Tranlate grid point (u,v) to pixel point
        if not self.changed: self.edit()
        #--u/v max/min are grid range of visible map.
        #--wcell is bit width of cell. 512 is bit width of visible map.
        (umin,umax,vmin,vmax,wcell,wmap) = (-28,27,-27,28,9,512)
        if not ((umin <= uland <= umax) and (vmin <= vland <= vmax)):
            return
        #--x0,y0 is bitmap coordinates of top left of cell in visible map.
        (x0,y0) = (4 + wcell*(uland-umin), 4 + wcell*(vmax-vland))
        #--Default to deep
        mapc = [Fmap.DEEP]*(9*9)
        heights = land and land.getHeights()
        if heights:
            #--Land heights are in 65*65 array, starting from bottom left.
            #--Coordinate conversion. Subtract one extra from height array because it's edge to edge.
            converter = [(65-2)*px/(wcell-1) for px in range(wcell)]
            for yc in xrange(wcell):
                ycoff = wcell*yc
                yhoff = (65-1-converter[yc])*65
                for xc in xrange(wcell):
                    height = heights[converter[xc]+yhoff]
                    if height >= 0: #--Land
                        (r0,g0,b0,r1,g1,b1,scale) = (66,48,33,32,23,16,sqrt(height/3000.0))
                        scale = int(scale*10)/10.0 #--Make boundaries sharper.
                        r = chr(max(0,int(r0 - r1*scale)) & ~1)
                    else: #--Sea
                        #--Scale color from shallow to deep color.
                        (r0,g0,b0,r1,g1,b1,scale) = (37,55,50,12,19,17,-height/2048.0)
                        r = chr(max(0,int(r0 - r1*scale)) | 1)
                    g = chr(max(0,int(g0 - g1*scale)))
                    b = chr(max(0,int(b0 - b1*scale)))
                    mapc[xc+ycoff] = r+g+b
        #--Draw it
        mapd = self.mapd
        for yc in xrange(wcell):
            ycoff = wcell*yc
            ymoff = wmap*(y0+yc)
            for xc in xrange(wcell):
                cOld = mapd[x0+xc+ymoff]
                cNew = mapc[xc+ycoff]
                rOld = ord(cOld[0])
                #--New or old is sea.
                if (ord(cNew[0]) & 1) or ((rOld & 1) and
                    (-2 < (1.467742*rOld - ord(cOld[1])) < 2) and
                    (-2 < (1.338710*rOld - ord(cOld[2])) < 2)):
                    mapd[x0+xc+ymoff] = cNew
        if marked:
            self.drawBorder(Fmap.MARKED,x0+2,y0+2,x0+7,y0+7,1)
            pass

#------------------------------------------------------------------------------

class Glob(Record):
    """Global record. Note that global values are stored as floats regardless of type."""
    def __init__(self,name='GLOB',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialization."""
        self.type = 'l'
        self.value = 0
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        """Loads from ins/internal data."""
        #--Read subrecords
        bytesRead = 0
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('GLOB')
            srData = ins.read(size,'GLOB.'+name)
            bytesRead += 8+size
            if   name == 'NAME': self.id = cstrip(srData)
            elif name == 'FNAM': self.type = srData
            elif name == 'FLTV': self.value = struct.unpack('f',srData)
            #--Deleted?
            elif name == 'DELE': self.isDeleted = True
            #--Bad record?
            else: raise Tes3UnknownSubRecord(self.inName,name,self.name)

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        out.packSub0('NAME',self.id)
        if getattr(self,'isDeleted',False):
            out.packSub('DELE','i',0)
            return
        out.packSub('FNAM',self.type)
        out.packSub('FLTV','f',self.value)

#------------------------------------------------------------------------------

class Info_Test:
    """INFO function/variable test. Equates to SCVR + INTV/FLTV."""
    def __init__(self,type,func,oper,text='',value=0):
        """Initialization."""
        self.type = type
        self.func = func
        self.oper = oper
        self.text = text
        self.value = value

    def dumpData(self,out,index):
        """Dumps self into specified out stream with specified SCVR index value."""
        #--SCVR
        out.pack('4siBB2sB', 'SCVR', 5+len(self.text), index+48, self.type, self.func, self.oper)
        if self.text: out.write(self.text)
        #--Value
        if type(self.value) is int:
            out.packSub('INTV','i', self.value)
        else: out.packSub('FLTV','f', self.value)

#------------------------------------------------------------------------------

class Info(Record):
    """INFO record. Dialog/journal entry. This version is complete."""
    def __init__(self,name='INFO',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialization."""
        #--Info Id
        self.id = ''
        self.nextId = ''
        self.prevId = ''
        #--Text/Script
        self.text = None
        self.script = None
        self.speak = None
        self.qflag = 0 # 0 nothing, 1 name, 2 finished, 3 restart.
        #--Unknown
        self.type = 0 #--Same as for dial.
        self.unk02 = 0
        #--Speaker Tests
        self.spDisp = 0
        self.spSex = -1
        self.spRank = -1
        self.spId = None
        self.spRace = None
        self.spClass = None
        self.spFaction = None
        #--Cell, PC
        self.cell = None
        self.pcRank = -1
        self.pcFaction = None
        #--Other Tests
        self.tests = [0,0,0,0,0,0]
        #--Deleted?
        self.isDeleted = False
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        """Loads from ins/internal data."""
        #--Read subrecords
        bytesRead = 0
        curTest = None
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('INFO')
            srData = ins.read(size,'INFO.'+name)
            bytesRead += 8+size
            #--Ids
            if   name == 'INAM': self.id = cstrip(srData)
            elif name == 'PNAM': self.prevId = cstrip(srData)
            elif name == 'NNAM': self.nextId = cstrip(srData)
            #--Text/Script
            elif name == 'NAME': self.text = srData
            elif name == 'BNAM': self.script = srData
            elif name == 'SNAM': self.speak = srData
            #--Quest flags
            elif name == 'QSTN': self.qflag = 1
            elif name == 'QSTF': self.qflag = 2
            elif name == 'QSTR': self.qflag = 3
            #--String/Value Tests
            elif name == 'DATA':
                (self.type, self.spDisp, self.spRank, self.spSex, self.pcRank, self.unk02
                    ) = struct.unpack('2i4B',srData)
            elif name == 'ONAM': self.spId = cstrip(srData)
            elif name == 'RNAM': self.spRace = cstrip(srData)
            elif name == 'CNAM': self.spClass = cstrip(srData)
            elif name == 'FNAM': self.spFaction = cstrip(srData)
            elif name == 'ANAM': self.cell = cstrip(srData)
            elif name == 'DNAM': self.pcFaction = cstrip(srData)
            #--Function/Value Tests
            elif name == 'SCVR':
                (index,type,func,oper) = struct.unpack('BB2sB',srData[:5])
                text = srData[5:]
                curTest = Info_Test(type,func,oper,text)
                self.tests[index-48] = curTest
            elif name == 'INTV':
                (curTest.value,) = struct.unpack('i',srData)
            elif name == 'FLTV':
                (curTest.value,) = struct.unpack('f',srData)
            #--Deleted?
            elif name == 'DELE': self.isDeleted = True
            #--Bad record?
            else: raise Tes3UnknownSubRecord(self.inName,name,self.name)

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        out.packSub0('INAM',self.id)
        out.packSub0('PNAM',self.prevId)
        out.packSub0('NNAM',self.nextId)
        if not self.isDeleted:
            out.packSub('DATA','2i4B',
                self.type, self.spDisp, self.spRank, self.spSex, self.pcRank, self.unk02)
        if self.spId:       out.packSub0('ONAM',self.spId)
        if self.spRace:     out.packSub0('RNAM',self.spRace)
        if self.spClass:    out.packSub0('CNAM',self.spClass)
        if self.spFaction:  out.packSub0('FNAM',self.spFaction)
        if self.cell:       out.packSub0('ANAM',self.cell)
        if self.pcFaction:  out.packSub0('DNAM',self.pcFaction)
        if self.speak:      out.packSub0('SNAM',self.speak)
        if self.text:       out.packSub('NAME',self.text)
        if self.qflag == 0:
            pass
        if self.qflag == 1: out.packSub('QSTN','\x01')
        if self.qflag == 2: out.packSub('QSTF','\x01')
        if self.qflag == 3: out.packSub('QSTR','\x01')
        for index,test in enumerate(self.tests):
            if test: test.dumpData(out,index)
        if self.script:     out.packSub('BNAM',self.script)
        if self.isDeleted:  out.pack('DELE','i',0)

    def compactTests(self,mode='TOP'):
        """Compacts test array. I.e., moves test up into any empty slots if present.
        mode: 'TOP' Eliminate only leading empty tests. [0,0,1,0,1] >> [1,0,1]
        mode: 'ALL' Eliminat all empty tests. [0,0,1,0,1] >> [1,1]"""
        if tuple(self.tests) == (0,0,0,0,0,0): return False
        if mode == 'TOP':
            newTests = self.tests[:]
            while newTests and not newTests[0]:
                del newTests[0]
        else:
            newTests = [test for test in self.tests if test]
        while len(newTests) < 6: newTests.append(0)
        if tuple(self.tests) != tuple(newTests):
            self.tests = newTests
            self.setChanged()
            return True

#------------------------------------------------------------------------------

class InfoS(Record):
    """INFO record. Dialog/journal entry.
    This is a simpler version of the info record. It expands just enough for
    dialog import/export."""
    def __init__(self,name='INFO',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.nextId = None
        self.prevId = None
        self.spId = None
        self.text = None
        self.records = [] #--Subrecords, of course
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Read subrecords
        bytesRead = 0
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('INFO')
            bytesRead += 8+size
            record = SubRecord(name,size,ins)
            self.records.append(record)
            #--Info Id?
            if name == 'INAM':
                self.id = cstrip(record.data)
            elif name == 'PNAM':
                self.prevId = cstrip(record.data)
            elif name == 'NNAM':
                self.nextId = cstrip(record.data)
            #--Speaker?
            elif name == 'ONAM':
                self.spId = cstrip(record.data)
            #--Text?
            elif name == 'NAME':
                self.text = record.data

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Get sizes
        for record in self.records:
            #--Text
            if record.name == 'NAME':
                #--Truncate text?
                if len(self.text) > 511:
                    self.text = self.text[:511]
                record.data = self.text
                record.size = len(self.text)
            #--Speaker
            elif record.name == 'ONAM':
                record.data = self.spId+'\x00'
                record.size = len(self.spId) + 1
            record.getSize()
            record.dump(out)

#------------------------------------------------------------------------------

class Land(Record):
    """LAND record. Landscape: heights, vertices, texture references, etc."""
    def __init__(self,name='LAND',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialize."""
        self.id = None
        #self.gridX = 0
        #self.gridY = 0
        self.heights = None
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def getId(self):
        """Return id. Also, extract gridX and gridY."""
        if self.id: return self.id
        reader = self.getReader()
        subData = reader.findSubRecord('INTV','LAND')
        (self.gridX,self.gridY) = struct.unpack('ii',subData)
        self.id = '[%d,%d]' % (self.gridX,self.gridY)
        return self.id

    def getHeights(self):
        """Returns len(65x65) array of vertex heights."""
        if self.heights: return self.heights
        reader = self.getReader()
        subData = reader.findSubRecord('VHGT','LAND')
        if not subData: return None
        height0 = struct.unpack('f',subData[:4])[0]
        import array
        deltas = array.array('b',subData[4:4+65*65])
        iheights = array.array('i')
        iheights.append(0)
        for index in xrange(1,65*65):
            if index % 65: iheights.append(iheights[-1] + deltas[index])
            else: iheights.append(iheights[-65] + deltas[index])
        heights = self.heights = array.array('f')
        for index in xrange(65*65):
            heights.append(8*(height0 + iheights[index]))
        return self.heights

#------------------------------------------------------------------------------

class Levc(ListRecord):
    """LEVC record. Leveled list for creatures."""
    pass


class Levi(ListRecord):
    """LEVI record. Leveled list for items."""
    pass

#------------------------------------------------------------------------------

class Npcc(ContentRecord):
    """NPCC record. NPC contents/change."""
    def __init__(self,name='NPCC',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.index = 0
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Name
        (name,size) = ins.unpackSubHeader('NPCC','NAME')
        self.id = cstrip(ins.read(size,'CELL.NAME'))
        #--Index
        (name,size) = ins.unpackSubHeader('NPCC','NPDT',8)
        (unknown,self.index) = ins.unpack('ii',size,'CELL.NPDT')

#------------------------------------------------------------------------------

class Scpt(Record):
    """SCPT record. Script."""
    #--Class Data
    subRecordNames = ['SCVR','SCDT','SCTX','SLCS','SLSD','SLFD','SLLD','RNAM']

    def __init__(self,name='SCPT',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        #--Arrays
        self.id = None
        self.numShorts = 0
        self.numLongs = 0
        self.numFloats = 0
        self.dataSize = 0
        self.varSize = 0
        #--Mod data
        self.scvr = None
        self.scdt = None
        self.sctx = None
        #--Save data
        self.slcs = None
        self.slsd = None
        self.slfd = None
        self.slld = None
        self.rnam = None
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        #--Subrecords
        bytesRead = 0
        srNameSet = set(Scpt.subRecordNames)
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('SCPT')
            #--Header
            if name == 'SCHD':
                (self.id, self.numShorts, self.numLongs, self.numFloats, self.dataSize, self.varSize
                    ) = ins.unpack('32s5i',size,'SCPT.SCHD')
                self.id = cstrip(self.id)
            #--Other subrecords
            elif name in srNameSet:
                setattr(self,name.lower(),SubRecord(name,size,ins))
            else: raise Tes3Error(self.inName,_(u'Unknown SCPT record: ')+name)
            bytesRead += 8+size
        if bytesRead != self.size:
            raise Tes3Error(self.inName,_(u'SCPT %s: Unexpected subrecords') % (self.id))

    def getRef(self):
        """Returns reference data for a global script."""
        rnam = self.rnam
        if not rnam or rnam.data == chr(255)*4: return None
        if rnam.size != 4: raise Tes3Error(self.inName,(_(u'SCPT.RNAM'),rnam.size,4,True))
        iMod = struct.unpack('3xB',rnam.data)[0]
        iObj = struct.unpack('i',rnam.data[:3]+'\x00')[0]
        return (iMod,iObj)

    def setRef(self,reference):
        """Set reference data for a global script."""
        (iMod,iObj) = reference
        self.rnam.setData(struct.pack('i',iObj)[:3] + struct.pack('B',iMod))
        self.setChanged()

    def setCode(self,code):
        #--SCHD
        self.dataSize = 2
        #--SCDT
        if not self.scdt: self.scdt = SubRecord('SCDT',0)
        self.scdt.setData(struct.pack('BB',1,1)) #--Uncompiled
        #--SCVR
        #self.scvr = None
        #--SCTX (Code)
        if not self.sctx: self.sctx = SubRecord('SCTX',0)
        self.sctx.setData(winNewLines(code))
        #--Done
        self.setChanged()
        self.getSize()

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Header
        out.packSub('SCHD','32s5i',
            self.id,
            self.numShorts, self.numLongs, self.numFloats,
            self.dataSize, self.varSize)
        #--Others
        for record in [getattr(self,srName.lower(),None) for srName in Scpt.subRecordNames]:
            if not record: continue
            record.size = len(record.data)
            record.dump(out)

#------------------------------------------------------------------------------

class Tes3_Hedr(SubRecord):
    """TES3 HEDR subrecord. File header."""
    def __init__(self,name,size,ins=None,unpack=False):
        """Initialize."""
        self.version = 1.3
        self.fileType = 0 #--0: esp; 1: esm; 32: ess
        self.author = ''
        self.description = ''
        self.numRecords = 0
        SubRecord.__init__(self,name,size,ins,unpack)

    def load(self,ins,unpack=False):
        self.data = ins.read(self.size,'TES3.HEDR')
        if not unpack: return
        data = struct.unpack('fi32s256si',self.data)
        self.version = data[0]
        self.fileType = data[1]
        self.author = cstrip(data[2])
        self.description = cstrip(data[3])
        self.numRecords = data[4]

    def getSize(self): # Polemos: Fixed a struct bug here.
        if not self.data and not self.changed: raise StateError(_(u'Data undefined: %s' % self.name))
        if not self.changed: return self.size
        self.description = winNewLines(self.description)

        try:
            self.data = struct.pack('fi32s256si',
                                    self.version,
                                    self.fileType,
                                    self.author,
                                    self.description,
                                    self.numRecords)
        except:
            try:
                author_po = str(self.author)
                self.data = struct.pack('fi32s256si',
                                        self.version,
                                        self.fileType,
                                        author_po,
                                        self.description,
                                        self.numRecords)
            except:
                try:
                    description_po = str(self.description)
                    self.data = struct.pack('fi32s256si',
                                            self.version,
                                            self.fileType,
                                            self.author,
                                            description_po,
                                            self.numRecords)
                except: pass
        self.size = len(self.data)
        self.setChanged(False)
        return self.size

#------------------------------------------------------------------------------

class Tes3_Gmdt(SubRecord):
    """TES3 GMDT subrecord. Savegame data. PC name, health, cell, etc."""

    def load(self,ins,unpack=False):
        self.data = ins.read(self.size,'TES3.GMDT')
        if not unpack: return
        data = struct.unpack('3f12s64s4s32s',self.data)
        self.curHealth = data[0]
        self.maxHealth = data[1]
        self.day = data[2]
        self.unknown1 = data[3]
        self.curCell = cstrip(data[4])
        self.unknown2 = data[5]
        self.playerName = cstrip(data[6])

    def getSize(self):
        if not self.data: raise StateError(_(u'Data undefined: ')+self.name)
        if not self.changed: return self.size
        self.data = struct.pack('3f12s64s4s32s',
            self.curHealth,
            self.maxHealth,
            self.day,
            self.unknown1,
            self.curCell,
            self.unknown2,
            self.playerName,
            )
        self.size = len(self.data)
        self.setChanged(False)
        return self.size

#------------------------------------------------------------------------------

class Tes3(Record):
    """TES3 Record. File header."""
    def __init__(self,name='TES3',size=0,delFlag=0,recFlag=0,ins=None,unpack=False):
        """Initialize."""
        self.hedr = None
        self.masters = [] #--(fileName,fileSize)
        self.gmdt = None
        self.others = [] #--SCRD, SCRS (Screen snapshot?)
        Record.__init__(self,name,size,delFlag,recFlag,ins,unpack)

    def loadData(self,ins):
        MAX_SUB_SIZE = 100*1024
        #--Header
        (name,size) = ins.unpackSubHeader('TES3','HEDR')
        self.hedr = Tes3_Hedr(name,size,ins,True)
        bytesRead = 8+size
        #--Read Records
        while bytesRead < self.size:
            (name,size) = ins.unpackSubHeader('TES3')
            if size > MAX_SUB_SIZE: raise Tes3SizeError(self.inName,name,size,-MAX_SUB_SIZE,True)
            #--Masters
            if name == 'MAST':
                #--FileName
                fileName = cstrip(ins.read(size,'TES3.MAST'))
                bytesRead += 8 + size
                #--FileSize
                (name,size) = ins.unpackSubHeader('TES3','DATA',8)
                fileSize = ins.unpack('Q',8,'TES3.DATA')[0]
                self.masters.append((fileName,fileSize))
                bytesRead += 16
            #--Game Data
            elif name == 'GMDT':
                self.gmdt = Tes3_Gmdt(name,size,ins,True)
                bytesRead += 8 + size
            #--Screen snapshot?
            else:
                self.others.append(SubRecord(name,size,ins))
                bytesRead += 8 + size

    def dumpData(self,out):
        """Dumps state into out. Called by getSize()."""
        #--Get sizes and dump into dataIO
        self.hedr.getSize()
        self.hedr.dump(out)
        for (name,size) in self.masters:
            out.packSub0('MAST',name)
            out.packSub('DATA','Q',size)
        if self.gmdt:
            self.gmdt.getSize()
            self.gmdt.dump(out)
        for other in self.others:
            other.getSize()
            other.dump(out)

# File System -----------------------------------------------------------------

class MWIniFile:  # Polemos: OpenMW/TES3mp support
    """Morrowind.ini/OpenMW.cfg file."""

    def __init__(self, dr):
        """Init."""
        self.dir = dr
        self.openmw = settings['openmw']
        self.encod = settings['profile.encoding']
        if not self.openmw:  # Morrowind
            self.path = os.path.join(self.dir, 'Morrowind.ini')
        elif self.openmw:  # OpenMW/TES3mp
            self.path = os.path.join(self.dir, 'openmw.cfg')
        self.datafiles_po = []
        self.confLoadLines = []
        self.DataMods = []
        self.DataModsDirs = []
        self.ConfCache = []
        self.activeFileExts = set()
        self.openmwPathDict = {}
        self.PluginSection = ''
        self.ArchiveSection = ''
        self.loadFiles = []
        self.bsaFiles = []
        self.loadFilesBad = []
        self.loadFilesExtra = []
        self.loadFilesDups = False
        self.mtime = 0
        self.size = 0
        self.doubleTime = {}
        self.exOverLoaded = set()
        self.loadOrder = tuple()
        self.filesRisk = []
        self.skip = True

    def criticalMsg(self, msg, dtype='', modal=True):
        """Show critical messages to user."""
        import gui.dialog as gui
        gui.ErrorMessage(None, msg, dtype=dtype, modal=modal)

    def getSetting(self, section, key, default=None):
        """Gets a single setting from the file."""
        section, key = map(bolt.LString, (section, key))
        settings = self.getSettings()
        if section in settings: return settings[section].get(key,default)
        else: return default

    def getSettings(self):
        """Gets settings for self."""
        reComment = re.compile(';.*')
        reSection = re.compile(r'^\[\s*(.+?)\s*\]$')
        reSetting = re.compile(r'(.+?)\s*=(.*)')
        #--Read ini file
        iniFile = GPath(self.path).codecs_open('r')
        settings = {}
        sectionSettings = None
        for line in iniFile:
            stripped = reComment.sub('', line).strip()
            maSection = reSection.match(stripped)
            maSetting = reSetting.match(stripped)
            if maSection:
                sectionSettings = settings[LString(maSection.group(1))] = {}
            elif maSetting:
                if sectionSettings is None:
                    sectionSettings = settings.setdefault(LString('General'), {})
                    self.isCorrupted = True
                sectionSettings[LString(maSetting.group(1))] = maSetting.group(2).strip()
        iniFile.close()
        return settings

    def saveSetting(self, section, key, value):
        """Changes a single setting in the file."""
        settings = {section: {key: value}}
        self.saveSettings(settings)

    def saveSettings(self,settings):
        """Applies dictionary of settings to ini file. Values in settings dictionary can be
        either actual values or full key=value line ending in newline char."""
        settings = {LString(x): {LString(u): v for u, v in y.iteritems()} for x, y in settings.iteritems()}
        reComment = re.compile(';.*')
        reSection = re.compile(r'^\[\s*(.+?)\s*\]$')
        reSetting = re.compile(r'(.+?)\s*=')
        #--Read init, write temp
        path = GPath(self.path)
        iniFile = path.codecs_open('r')
        tmpFile = path.temp.codecs_open('w')
        section = sectionSettings = None
        for line in iniFile:
            stripped = reComment.sub('',line).strip()
            maSection = reSection.match(stripped)
            maSetting = reSetting.match(stripped)
            if maSection:
                section = LString(maSection.group(1))
                sectionSettings = settings.get(section, {})
            elif maSetting and LString(maSetting.group(1)) in sectionSettings:
                key = LString(maSetting.group(1))
                value = sectionSettings[key]
                if type(value) is str and value[-1] == '\n':
                    line = value
                else: line = '%s=%s\n' % (key, value)
            tmpFile.write(line)
        tmpFile.close()
        iniFile.close()
        #--Done
        path.untemp()

    def applyMit(self,mitPath): # Polemos fixes
        """Read MIT file and apply its settings to morrowind.ini. Note: Will ONLY apply settings that already exist."""
        reComment = re.compile(';.*')
        reSection = re.compile(r'^\[\s*(.+?)\s*\]$')
        reSetting = re.compile(r'(.+?)\s*=')
        #--Read MIT file
        with io.open(mitPath, 'r', encoding=self.encod, errors='replace') as mitFile:
            sectionSettings = None
            settings = {}
            for line in mitFile:
                stripped = reComment.sub('',line).strip()
                maSection = reSection.match(stripped)
                maSetting = reSetting.match(stripped)
                if maSection: sectionSettings = settings[maSection.group(1)] = {}
                elif maSetting: sectionSettings[maSetting.group(1).lower()] = line
        #--Discard Games Files (Loaded mods list) from settings
        for section in settings.keys():
            if section.lower() in ('game files', 'archives', 'mit'): del settings[section]
        #--Apply it
        tmpPath = '%s.tmp' % self.path
        with io.open(self.path, 'r', encoding=self.encod, errors='replace') as iniFile:
            with io.open(tmpPath, 'w', encoding=self.encod, errors='replace') as tmpFile:
                section = None
                sectionSettings = {}
                for line in iniFile:
                    stripped = reComment.sub('', line).strip()
                    maSection = reSection.match(stripped)
                    maSetting = reSetting.match(stripped)
                    if maSection:
                        section = maSection.group(1)
                        sectionSettings = settings.get(section, {})
                    elif maSetting and maSetting.group(1).lower() in sectionSettings:
                        line = sectionSettings[maSetting.group(1).lower()]
                    tmpFile.write(line)
        #--Done
        renameFile(tmpPath,self.path, True)
        self.mtime = getmtime(self.path)

    def itmDeDup(self, itms):  # Polemos
        """Item de-duplication."""
        the_set = set()
        the_set_add = the_set.add
        return [x for x in itms if not (x in the_set or the_set_add(x))]

    def checkActiveState(self, DataDir):  # Polemos
        """True if DataDir is in load list (OpenMW/TES3mp)."""
        return DataDir in self.sanitizeDatamods(self.openmw_datamods()[:], False)

    def unloadDatamod(self, DataDir):  # Polemos
        """Remove DataDir from OpenMW."""
        DataDirF = [u'data="%s"' % os.path.realpath(x).rstrip() for x in DataDir]
        [self.DataMods.remove(x) for x in DataDirF if x in self.DataMods]
        self.SaveDatamods(self.DataMods)

    def loadDatamod(self, DataDir, DataOrder):  # Polemos
        """Add DataDir to OpenMW."""
        [self.DataMods.append(u'data="%s"' % os.path.realpath(x)) for x in DataDir]
        DataOrderF = [u'data="%s"' % x for x in DataOrder]
        datamodsListExport = [x for x in DataOrderF if x in self.DataMods]
        self.SaveDatamods(datamodsListExport)

    def updateDatamods(self, DataOrder):  # Polemos
        """Update DataDirs order (active or not - OpenMW)."""
        DataOrderF = [u'data="%s"' % os.path.realpath(x[1]) for x in DataOrder]
        datamodsListExport = [x for x in DataOrderF if x in self.DataMods]
        self.DataMods = datamodsListExport
        self.SaveDatamods(datamodsListExport)

    def filterDataMod(self, data):  # Polemos
        """Returns DataMod path from openmw.cfg config entry."""
        if not data: return data
        if type(data) is list: return [x.split('"')[1] for x in data]
        else: return type(data)([x.split('"')[1] for x in data][0])

    def sanitizeDatamods(self, data, repack=True):  # Polemos
        """Sanitize DataDirs entries (openmw.cfg)."""
        filterPaths = self.filterDataMod(data)
        filterDups = self.itmDeDup(filterPaths)
        filterMissing = [x for x in filterDups if os.path.isdir(x)]
        return [u'data="%s"'%os.path.realpath(x).rstrip() for x in filterMissing
            ] if repack else [os.path.realpath(x).rstrip() for x in filterMissing]

    def SaveDatamods(self, rawdata):  # Polemos
        """Export DataDirs to openmw.cfg."""
        data = self.sanitizeDatamods(rawdata)
        reLoadFile = re.compile(ur'data=(.*)$', re.UNICODE)
        datamodsMark = True
        DataMods_empty = True
        conf_tmp = []
        # Check for no entries
        for line in self.confLoadLines[:]:
            maLoadFile = reLoadFile.match(line)
            if maLoadFile:
                DataMods_empty = False
                if datamodsMark:
                    datamodsMark = False
                    conf_tmp.extend(data)
            else: conf_tmp.append(line.rstrip())
        # If no entries
        if DataMods_empty:
            if conf_tmp[-1] == 'PluginMark' and data:
                del conf_tmp[-1]
                conf_tmp.extend(data)
                conf_tmp.append('PluginMark')
            else: conf_tmp.extend(data)
        # No DataMods dirs yet
        if conf_tmp and not self.DataModsDirs:
            self.safeSave('\n'.join([
                x for x in conf_tmp if not any(['PluginMark' in x, 'ArchiveMark' in x])]))
        #self.StructureChk(datafiles_po) todo: check for cfg abnormalities...
        else:
            self.confLoadLines = conf_tmp
            self.DataModsDirs = self.filterDataMod(data)
            self.safeSave()

    def StructureChk(self, cfg):  # Polemos: Not enabled. todo: enable openmw.cfg check
        """Last check before saving OpenMW cfg file."""
        chkpoints = ''
        archive = False
        data = False
        content = False
        for x in cfg:
            if not archive:
                if x.startswith('fallback-archive='):
                    chkpoints = '%s1' % chkpoints
                    archive = True
            if not data:
                if x.startswith('data="'):
                    chkpoints = '%s2' % chkpoints
                    data = True
            if not content:
                if x.startswith('content='):
                    chkpoints = '%s3' % chkpoints
                    content = True
        if not chkpoints == '123': return False
        else: return True

    def FullRefresh(self):
        """For OpenMW/TES3mp."""
        folders = [x for x in self.openmw_data_files() if not os.path.isdir(x)]
        self.unloadDatamod(folders)

    def openmw_datamods(self):  # Polemos
        """Gets data entries from OpenMW.cfg file."""
        reLoadFile = re.compile(ur'data=(.*)$', re.UNICODE)
        del self.DataMods[:]
        del self.ConfCache[:]
        for line in self.open_conf_file():
            maLoadFile = reLoadFile.match(line)
            if maLoadFile:
                self.DataMods.append(line.rstrip())
            self.ConfCache.append(line)
        if not self.DataMods: return []
        return self.DataMods

    def openmw_data_files(self):  # Polemos
        """Return data file directories (OpenMW)."""
        if self.hasChanged():
            self.DataModsDirs = self.sanitizeDatamods(self.openmw_datamods()[:], False)
        return self.DataModsDirs

    def open_conf_file(self):  # Polemos
        """Return Morrowind.ini or OpenMW.cfg file."""
        try:
            with io.open(self.path, 'r', encoding=self.encod, errors='strict') as conf_file:
                return conf_file.readlines()
        except ValueError:  # Override errors when changing encodings.
            with io.open(self.path, 'r', encoding=self.encod, errors='ignore') as conf_file:
                return conf_file.readlines()

    def loadConf(self):  # Polemos
        """Redirect to read data from either morrowind.ini or OpenMW.cfg."""
        if not self.openmw:  # Morrowind
            self.load_Morrowind_INI()
        elif self.openmw:  # OpenMW/TES3mp
            self.load_OpenMW_cfg()

    def flush_conf(self, full=True):  # Polemos.
        """Flush old data."""
        if full:
            self.PluginSection = ''
            self.ArchiveSection = ''
            del self.confLoadLines[:]
            del self.loadFiles[:]
            del self.bsaFiles[:]
        self.loadFilesDups = False
        del self.loadFilesBad[:]
        del self.loadFilesExtra[:]

    def getExt(self, itmPath):
        """Return itm extension."""
        ext = os.path.splitext(itmPath)[-1].lower()
        self.activeFileExts.add(ext)
        return ext

    def chkCase(self, itms):  # Polemos
        """Check for duplicates and remove them if they are not in path. Fix case if unique."""
        if not any([itms is not None, not itms]): return itms  # Unforeseen events
        if not self.openmw:  # Morrowind
            origin = os.path.join(self.dir, 'Data Files')
            inItms = {x.lower() for x in itms}
            if len(inItms) < len(itms):
                itmsR = [x for x in os.listdir(
                    origin) if [e for e in self.activeFileExts if x.lower().endswith(e)]]
                self.loadFilesDups = True
                return list({x for x in itms if x in itmsR})
        elif self.openmw:  # OpenMW self.openmwPathDict
            inItms = {x.lower() for x in itms}
            if len(inItms) < len(itms):
                itmsR = [x for x in self.openmwPathDict if x in [
                    fl for fl in os.listdir(os.path.dirname(self.openmwPathDict[x])) if x.lower() == fl.lower()]]
                self.loadFilesDups = True
                return list({x for x in itms if x in itmsR})
        return itms  # All OK

    def getSrcFilePathInfo(self, itm):  # Polemos
        """Acquire mod/plugin path info."""
        if not self.openmw:  # Morrowind
            modDir = [os.path.join(self.dir, 'Data Files')]
        elif self.openmw:  # OpenMW
            modDir = self.DataModsDirs[:]
        for dr in modDir:
            itmPath = os.path.join(dr, itm)
            if os.path.isfile(itmPath):
                return itmPath
        return False

    def load_Morrowind_INI(self):  # Polemos.
        """Read Plugin and Archive data from morrowind.ini"""
        reLoadPluginSection = re.compile(ur'^\[Game Files\](.*)', re.UNICODE)
        reLoadPluginFiles = re.compile(ur'GameFile[0-9]+=(.*)$', re.UNICODE)
        reLoadArchiveSection = re.compile(ur'^\[Archives\](.*)', re.UNICODE)
        reLoadArchiveFiles = re.compile(ur'Archive [0-9]+=(.*)$', re.UNICODE)
        self.mtime = getmtime(self.path)
        self.size = os.path.getsize(self.path)
        self.flush_conf()
        PluginSection, ArchiveSection = False, False

        try:
            for line in self.open_conf_file():
                maLoadPluginSection = reLoadPluginSection.match(line)
                maLoadArchiveSection = reLoadArchiveSection.match(line)
                maLoadPluginFiles = reLoadPluginFiles.match(line)
                maLoadArchiveFiles = reLoadArchiveFiles.match(line)

                if maLoadArchiveSection:
                    ArchiveSection = True
                    self.ArchiveSection = line.rstrip()

                if maLoadPluginSection:
                    PluginSection = True
                    self.PluginSection = line.rstrip()

                if maLoadArchiveFiles:
                    archive = maLoadArchiveFiles.group(1).rstrip()
                    loadArchivePath, loadArchiveExt = self.getSrcFilePathInfo(archive), self.getExt(archive)
                    if loadArchivePath and re.match('^\.bsa$', loadArchiveExt): self.bsaFiles.append(archive)
                    else: self.loadFilesBad.append(archive)

                if maLoadPluginFiles:
                    plugin = maLoadPluginFiles.group(1).rstrip()
                    loadPluginPath, loadPluginExt = self.getSrcFilePathInfo(plugin), self.getExt(plugin)
                    if len(self.loadFiles) == 1023: self.loadFilesExtra.append(plugin)
                    elif loadPluginPath and re.match('^\.es[pm]$', loadPluginExt): self.loadFiles.append(plugin)
                    else: self.loadFilesBad.append(plugin)

                if not maLoadArchiveFiles and not maLoadPluginFiles: self.confLoadLines.append(line.rstrip())
                if not line:
                    if not PluginSection: raise Tes3Error('Morrowind.ini', _(u'Morrowind.ini: [Game Files] section not found.'))
                    if not ArchiveSection: raise Tes3Error('Morrowind.ini', _(u'Morrowind.ini: [Archives] section not found.'))

            self.bsaFiles = self.chkCase(self.bsaFiles)
            self.loadFiles = self.chkCase(self.loadFiles)
        except Exception as err:  # Last resort to avoid conf file corruption Todo: err debug
            self.flush_conf()

    def load_OpenMW_cfg(self):  # Polemos
        """Read plugin data from openmw.cfg"""
        self.datafiles_po = self.openmw_data_files()
        reLoadArchiveFiles = re.compile(ur'fallback-archive=(.*)$', re.UNICODE)
        reLoadPluginFiles = re.compile(ur'content=(.*)$', re.UNICODE)
        self.mtime = getmtime(self.path)
        self.size = os.path.getsize(self.path)
        self.flush_conf()
        conf_tmp = []
        ArchivesMark = None
        PluginsMark = None
        Archives_empty = True
        Plugins_empty = True
        no_sound_mark = False

        try:
            for line in self.ConfCache[:]:  # Check for no entries
                maLoadArchiveFiles = reLoadArchiveFiles.match(line)
                maLoadPluginFiles = reLoadPluginFiles.match(line)
                if maLoadArchiveFiles: Archives_empty = False
                if 'no-sound=' in line: no_sound_mark = True
                if maLoadPluginFiles: Plugins_empty = False
                conf_tmp.append(line.rstrip())

            for line in conf_tmp:  # Parse OpenMW.cfg
                maLoadArchiveFiles = reLoadArchiveFiles.match(line)
                maLoadPluginFiles = reLoadPluginFiles.match(line)

                if maLoadArchiveFiles:  # Archives
                    if ArchivesMark is None: ArchivesMark = True
                    archiveFile = maLoadArchiveFiles.group(1)
                    self.getExt(archiveFile)
                    archivePath = self.getSrcFilePathInfo(archiveFile)
                    if archivePath:
                        self.bsaFiles.append(archiveFile)
                        self.openmwPathDict[archiveFile] = archivePath
                    else: self.loadFilesBad.append(archiveFile)

                if maLoadPluginFiles:  # Plugins
                    if PluginsMark is None: PluginsMark = True
                    PluginFile = maLoadPluginFiles.group(1)
                    self.getExt(PluginFile)
                    PluginPath = self.getSrcFilePathInfo(PluginFile)
                    if PluginPath:
                        self.loadFiles.append(PluginFile)
                        self.openmwPathDict[PluginFile] = PluginPath
                    else: self.loadFilesBad.append(PluginFile)

                if Archives_empty:  # If no Archive entries
                    if 'no-sound=' in line:
                        self.confLoadLines.append(line)
                        line = 'ArchiveMark'

                if ArchivesMark:  # Mark Archives pos in conf
                    ArchivesMark = False
                    self.confLoadLines.append('ArchiveMark')

                if PluginsMark:  # Mark Plugins pos in conf
                    PluginsMark = False
                    self.confLoadLines.append('PluginMark')

                if not maLoadArchiveFiles and not maLoadPluginFiles: self.confLoadLines.append(line)

            if Plugins_empty: self.confLoadLines.append('PluginMark')  # If no Plugin entries
            if not no_sound_mark: self.confLoadLines.insert(0, 'ArchiveMark')
            self.bsaFiles = self.chkCase(self.bsaFiles)
            self.loadFiles = self.chkCase(self.loadFiles)
            if self.bsaFiles: self.openmw_apply_order(self.bsaFiles, self.datafiles_po)
            if self.loadFiles: self.openmw_apply_order(self.loadFiles, self.datafiles_po)
        except Exception as err:  # Last resort to avoid conf file corruption Todo: err debug
            self.flush_conf()

    def get_active_bsa(self):  # Polemos
        """Called to return BSA entries from conf files."""
        if self.hasChanged(): self.loadConf()
        return self.bsaFiles

    def data_files_factory(self, filenames):  # Polemos: OpenMW/TES3mp
        """Constructs the data file paths for OpenMW"""
        paths = self.DataModsDirs
        order_po = []
        real = os.path.realpath
        exists = os.path.exists
        join = os.path.join
        # Polemos: Having the folders first in the loop, counts for the DataMods folder order override.
        # Also, when searching for mods in a DataMods folder we cannot Break to speed things up. If we
        # do, we risk to omit DataMods with multiple plugins...
        for mod_dir in paths:
            for filename in filenames:
                fpath = real(join(mod_dir, filename))
                if exists(fpath):
                    order_po.append(fpath)
        return order_po

    def openmw_apply_order(self, order, paths):  # Polemos: OpenMW/TES3mp
        """Handle OpenMW mod ordering when reading openmw.cfg to display on mods panel."""
        if not order or not paths: return
        order_po = self.data_files_factory(order)
        # Polemos: For mods and bsas we use mtime to set/get order. Thus we keep compatibility with
        # regular Morrowind mod/bsa ordering and just hijack Wrye Mash system to use with OpenMW.
        if len(order_po) <= 1: return
        mtime_first = 1026943162
        mtime_last = int(time.time())
        if mtime_last < 1228683562: mtime_last = 1228683562
        loadorder_mtime_increment = (mtime_last - mtime_first) / len(order_po)
        mtime = mtime_first
        for filepath in order_po:
            os.utime(filepath, (-1, mtime))
            mtime += loadorder_mtime_increment

    def save_openmw_plugin_factory(self):  # Polemos: OpenMW/TES3mp
        """Prepare plugin file entries for insertion to OpenMW.cfg."""
        plugins_order = self.data_files_factory(self.loadFiles)
        plugins_order.sort(key=lambda x: os.path.getmtime(x))
        plugins_order = [os.path.basename(x) for x in plugins_order]
        plugins_order = self.itmDeDup(plugins_order)
        esm_order = [x for x in plugins_order if x.lower().endswith('.esm') or x.lower().endswith('.omwgame')]
        esp_order = [x for x in plugins_order if x.lower().endswith('.esp') or x.lower().endswith('.omwaddon')]
        return esm_order + esp_order

    def save_openmw_archive_factory(self):  # Polemos: OpenMW/TES3mp
        """Prepare archive file entries for insertion to OpenMW.cfg."""
        archives_order = self.data_files_factory(self.bsaFiles)
        archives_order.sort(key=lambda x: os.path.getmtime(x))
        archives_order = [os.path.basename(x) for x in archives_order]
        archives_order = self.itmDeDup(archives_order)
        return [x for x in archives_order if x.lower().endswith('.bsa')]

    def saveS(self, simpleData):  # Polemos
        """Simple no rules storage."""
        with io.open(self.path, 'w', encoding=self.encod, errors='strict') as conf_File:
            conf_File.write(simpleData)

    def save(self):  # Polemos fixes, optimizations, OpenMW/TES3mp support, BSA support, speed up massive lists.
        """Prepare data to write to morrowind.ini or openmw.cfg file."""
        if not self.confLoadLines:
            self.flush_conf()
            msg = _(  # We need this dialog to be modeless to avoid file datetime corruption.
                u'Unable to parse or modify %s. No changes can be made.'
                u'\n\nPlease try selecting a different encoding from the settings menu and restart Wrye Mash.'
            ) % ('morrowind.ini' if not self.openmw else 'openmw.cfg')
            self.criticalMsg(msg, 'error', False)
            raise StateError(msg)
        writeCache, failed = [], {}

        if self.hasChanged():  # Has the config file changed?
            if not self.openmw: error_ini_po = _(u'Morrowind.ini has changed externally! Aborting...')
            elif self.openmw: error_ini_po = _(u'Openmw.cfg has changed externally! Aborting...')
            raise StateError(error_ini_po)

        with io.open(self.path, 'w', encoding=self.encod, errors='strict') as conf_File:
            if not self.openmw:  # Morrowind
                # Check for irregular file namings.
                if not settings['query.file.risk']:
                    self.filesRisk = self.fileNamChk(self.loadFiles+self.bsaFiles)
                # Create output entries.
                for line in self.confLoadLines:
                    if line == self.ArchiveSection:
                        writeCache.append('%s' % self.ArchiveSection)
                        for aNum in xrange(len(self.bsaFiles)):
                            Archive = self.bsaFiles[aNum]
                            writeCache.append('Archive %d=%s' % (aNum, Archive))
                    elif line == self.PluginSection:
                        writeCache.append('%s' % self.PluginSection)
                        for pNum in xrange(len(self.loadFiles)):
                            Plugin = self.loadFiles[pNum]
                            writeCache.append('GameFile%d=%s' % (pNum, Plugin))
                    else: writeCache.append('%s' % line)

            elif self.openmw:  # OpenMW/TES3mp
                # Call file factories.
                archives_order = self.save_openmw_archive_factory()
                plugins_order = self.save_openmw_plugin_factory()
                # Check for irregular file namings.
                if not settings['query.file.risk']:
                    self.filesRisk = self.fileNamChk(archives_order+plugins_order)
                # Create output entries.
                for line in self.confLoadLines:
                    if line == 'ArchiveMark':
                        for Archive in archives_order:
                            writeCache.append('fallback-archive=%s' % Archive)
                    elif line == 'PluginMark':
                        for Plugin in plugins_order:
                            writeCache.append('content=%s' % Plugin)
                    else: writeCache.append('%s' % line)

            try:  # Try to join all and save once.
                tmpwriteCache = '\n'.join(writeCache)
                conf_File.write(tmpwriteCache)
            except:  # On fail, save by line.
                for num, x in enumerate(writeCache):
                    x = '%s\n' % x
                    try: conf_File.write(x)
                    except:
                        try: conf_File.write(x.encode(encChk(x)))
                        except: failed[num] = x.rstrip()

        self.mtime = getmtime(self.path)
        self.size = os.path.getsize(self.path)
        self.flush_conf(False)
        # Notify user for any errors.
        if failed: self.charFailed(failed)

    def fRisk(self):  # Polemos
        """Show filenames that may cause problems to the user."""
        if settings['query.file.risk'] or self.openmw: return  # Todo: Enable for OpenMW
        import gui.dialog as gui, wx
        engine = u'Morrowind' if not self.openmw else u'OpenMW'
        # Notify user
        tmessage = _(u'Some of your mod filenames seem to have problematic encodings.')
        message = _(u'There is a possibility that they might cause problems/bugs with Wrye Mash or %s functionality.\n'
                    u'Please consider renaming them.\n\nWould you like to see a list of the affected filenames?') % engine
        if gui.ContinueQuery(None, tmessage, message, 'query.file.risk', _(u'Problematic Filenames Detected')) != wx.ID_OK: return
        else:
            riskItms = '\n'.join(self.filesRisk)
            gui.WarningMessage(None, _(u'The affected filenames are:\n\n%s' % riskItms), _(u'Affected Filenames List'))
        del self.filesRisk[:]

    def fileNamChk(self, flist):
        """Check for irregular file namings."""
        probs = []
        for x in flist:
            try: x.decode(encChk(x))
            except: probs.append(x)
        return probs

    def charFailed(self, items):  # Polemos
        """Show failed entries to the user."""
        # Set data
        conf = u'Morrowind.ini' if not self.openmw else u'Openmw.cfg'
        confItms = ('Archive', 'GameFile') if not self.openmw else ('fallback-archive=', 'content')
        l = _(u'Line')
        # Extract mod errors
        mods = [(u'%s %s: %s'%(l, x, items[x])) for x in items if any([y in items[x] for y in confItms])]
        # Reload the config file
        self.loadConf()
        # If the errors are only for mod entries, skip them, keep the changes in the configuration file and notify user
        if len(items) == len(mods):
            errors = '\n'.join(mods)
            self.criticalMsg(_(u'Problems encountered while updating %s. The following entries were not added:\n\n%s' % (conf, errors)))
        # If there are also errors on lines without mod entries, notify user and raise error to revert to backup
        if len(items) > len(mods):
            errors = '\n'.join([(u'%s %s: %s...'%(l, x, items[x][:35])) if len(items[x]) > 35 else (u'%s %s: %s'%(l, x, items[x])) for x in items])
            self.criticalMsg(_(u'Problems encountered while updating %s. Will revert to backup, no changes will be saved:\n\n%s' % (conf, errors)))
            self.restoreBackup()

    def restoreBackup(self):  # Polemos: Good to have a safety switch.
        """Restores the latest morrowind.ini/openmw.cfg backup file on save failure."""
        # Does the last backup file exist?
        if os.path.isfile('%s.bak' % self.path): conf_bck = '%s.bak' % self.path
        # If missing, does the first backup ever taken exist?
        elif os.path.isfile('%s.baf' % self.path): conf_bck = '%s.baf' % self.path
        # Shit happens. Notify user and abort.
        else: return u'Fatal: No backup file was found to restore configuration!'
        # Restore ops
        shutil.copy(conf_bck, self.path)
        self.loadConf()

    def makeBackup(self):
        """Create backup copy/copies of morrowind.ini/openmw.cfg file."""
        #--File Path
        original = self.path
        #--Backup
        backup = '%s.bak' % self.path
        shutil.copy(original, backup)
        #--First backup
        firstBackup = '%s.baf' % self.path
        if not os.path.exists(firstBackup):
            shutil.copy(original, firstBackup)

    def safeSave(self, simpleData=False):  # Polemos
        """Safe save conf file."""
        self.makeBackup()
        try:
            if not simpleData: self.save()
            else: self.saveS(simpleData)
        except ConfError as err:
            import gui.dialog as gui
            gui.ErrorMessage(None, err.message)
            self.restoreBackup()
        except Exception as err:
            self.restoreBackup()
        # If allowed check filename risk
        if not self.skip and self.filesRisk: self.fRisk()
        self.skip = False  # Skip first check

    def hasChanged(self):
        """True if morrowind.ini/openmw.cfg file has changed."""
        return ((self.mtime != getmtime(self.path)) or
            (self.size != os.path.getsize(self.path)))

    def refresh(self):
        """Load only if morrowind.ini/openmw.cfg has changed."""
        hasChanged = self.hasChanged()
        if hasChanged: self.loadConf()
        if len(self.loadFiles) > 1023:
            del self.loadFiles[1023:]
            self.safeSave()
        return hasChanged

    def refreshDoubleTime(self):
        """Refresh arrays that keep track of doubletime mods."""
        doubleTime = self.doubleTime
        doubleTime.clear()
        for loadFile in self.loadFiles:
            try:  # Polemos: Black magic here, move along.
                mtime = modInfos[loadFile].mtime
                doubleTime[mtime] = doubleTime.has_key(mtime)
            except: pass
        #--Refresh overLoaded too..
        exGroups = set()
        self.exOverLoaded.clear()
        for selFile in self.loadFiles:
            maExGroup = reExGroup.match(selFile)
            if maExGroup:
                exGroup = maExGroup.group(1)
                if exGroup not in exGroups: exGroups.add(exGroup)
                else: self.exOverLoaded.add(exGroup)

    def isWellOrdered(self,loadFile=None):
        if loadFile and loadFile not in self.loadFiles: return True
        # Yakoby: An attempt at a fix for issue #27.I am not sure why
        # this is now needed and wasn't before.One posibility is that
        # when modInfos gets manipulated this isn't refreshed.
        elif loadFile:
            mtime = modInfos[loadFile].mtime
            if mtime not in self.doubleTime: self.refreshDoubleTime()
            return not self.doubleTime[mtime]
        else: return not (True in self.doubleTime.values())

    def getDoubleTimeFiles(self):
        dtLoadFiles = []
        for loadFile in self.loadFiles:
            try: # Polemos: It fails if restoring auto backup.
                if self.doubleTime[modInfos[loadFile].mtime]:
                    dtLoadFiles.append(loadFile)
            except: pass
        return dtLoadFiles

    def sortLoadFiles(self):
        """Sort load files into esm/esp, alphabetical order."""
        self.loadFiles.sort()
        self.loadFiles.sort(lambda a, b: cmp(a[-3:].lower(), b[-3:].lower()))

    def isMaxLoaded(self):
        """True if load list is full."""
        return len(self.loadFiles) >= 1023

    def isLoaded(self,modFile):
        """True if modFile is in load list."""
        return (modFile in self.loadFiles)

    def load(self, Files, doSave=True, action='Plugins'):  # Polemos: Speed up
        """Add modFile/archive to load list."""
        if action == 'Plugins':
            for x in Files:
                if x not in self.loadFiles:
                    if self.isMaxLoaded(): raise MaxLoadedError
                    self.loadFiles.append(x)
            if doSave:
                self.sortLoadFiles()
                self.safeSave()
            self.refreshDoubleTime()
            self.loadOrder = modInfos.getLoadOrder(self.loadFiles)
        elif action == 'Archives':  # Polemos bsa support
            bsaSet = set(self.bsaFiles)
            self.bsaFiles.extend([x for x in Files if x not in bsaSet])
            self.safeSave()

    def unload(self, Files, doSave=True, action='Plugins'):  # Polemos: Speed up
        """Remove modFile/archive from load list."""
        if action == 'Plugins':
            [self.loadFiles.remove(x) for x in Files if x in self.loadFiles]
            if doSave: self.safeSave()
            self.refreshDoubleTime()
            self.loadOrder = modInfos.getLoadOrder(self.loadFiles)
        if action == 'Archives':  # Polemos bsa support
            [self.bsaFiles.remove(x) for x in Files]
            self.safeSave()

#------------------------------------------------------------------------------

class MasterInfo:
    """Return info about masters."""

    def __init__(self,name,size):
        """Init."""
        self.oldName = self.name = name
        self.oldSize = self.size = size
        self.modInfo = modInfos.get(self.name,None)
        if self.modInfo:
            self.mtime = self.modInfo.mtime
            self.author = self.modInfo.tes3.hedr.author
            self.masterNames = self.modInfo.masterNames
        else:
            self.mtime = 0
            self.author = ''
            self.masterNames = tuple()
        self.isLoaded = True
        self.isNew = False #--Master has been added

    def setName(self,name):
        self.name = name
        self.modInfo = modInfos.get(self.name,None)
        if self.modInfo:
            self.mtime = self.modInfo.mtime
            self.size = self.modInfo.size
            self.author = self.modInfo.tes3.hedr.author
            self.masterNames = self.modInfo.masterNames
        else:
            self.mtime = 0
            self.size = 0
            self.author = ''
            self.masterNames = tuple()

    def hasChanged(self):
        return (
            (self.name != self.oldName) or
            (self.size != self.oldSize) or
            (not self.isLoaded) or self.isNew)

    def isWellOrdered(self):
        if self.modInfo: return self.modInfo.isWellOrdered()
        else: return 1

    def getStatus(self):
        if not self.modInfo: return 30
        elif self.size != self.modInfo.size: return 10
        else: return 0

    def isExOverLoaded(self):
        """True if belongs to an exclusion group that is overloaded."""
        maExGroup = reExGroup.match(self.name)
        if not (mwIniFile.isLoaded(self.name) and maExGroup): return False
        else: return (maExGroup.group(1) in mwIniFile.exOverLoaded)

    def getObjectMap(self):
        """Object maps."""
        if self.name == self.oldName: return None
        else: return modInfos.getObjectMap(self.oldName,self.name)

#------------------------------------------------------------------------------

class FileInfo: # Polemos: OpenMW/TES3mp support
    """Abstract TES3 File."""

    def __init__(self, directory, name):
        """Init."""
        self.openMW = settings['openmw']
        if not self.openMW:  # Morrowind support
            path = os.path.join(directory, name)
        if self.openMW:  # OpenMW/TES3mp support
            directory = [x for x in MWIniFile.openmw_data_files(
                MWIniFile(settings['openmwprofile']))[:] if os.path.isfile(os.path.join(x, name))][0]
            path = os.path.join(directory, name)
        self.name = name
        self.dir = directory
        if os.path.exists(path):
            self.ctime = os.path.getctime(path)
            self.mtime = getmtime(path)
            self.size = os.path.getsize(path)
        else:
            self.ctime = time.time()
            self.mtime = time.time()
            self.size = 0
        self.tes3 = 0
        self.masterNames = tuple()
        self.masterOrder = tuple()
        self.masterSizes = {}
        self.madeBackup = False
        #--Ancillary storage
        self.extras = {}

    #--File type tests
    def isMod(self):
        if not self.openMW: return self.isEsp() or self.isEsm()
        else: return self.isEsp() or self.isEsm() or self.isOmwgame() or self.isOmwaddon()
    def isEsp(self):
        return self.name[-3:].lower() == 'esp'
    def isEsm(self):
        return self.name[-3:].lower() == 'esm'
    def isEss(self):
        return self.name[-3:].lower() == 'ess'
    def isOmwgame(self):
        return self.name[-3:].lower() == 'omwgame'
    def isOmwaddon(self):
        return self.name[-3:].lower() == 'omwaddon'
    def isOmwsave(self):
        return self.name[-3:].lower() == 'omwsave'


    def sameAs(self,fileInfo):
        return (
            (self.size == fileInfo.size) and
            (self.mtime == fileInfo.mtime) and
            (self.ctime == fileInfo.ctime) and
            (self.name == fileInfo.name) )

    def refresh(self):
        path = os.path.join(self.dir,self.name)
        self.ctime = os.path.getctime(path)
        self.mtime = getmtime(path)
        self.size = os.path.getsize(path)
        if self.tes3: self.getHeader()

    def setType(self,type):
        self.getHeader()
        if type == 'esm':
            self.tes3.hedr.fileType = 1
        elif type == 'esp':
            self.tes3.hedr.fileType = 0
        elif type == 'ess':
            self.tes3.hedr.fileType = 32
        self.tes3.hedr.setChanged()
        self.writeHedr()

    def getHeader(self):
        path = os.path.join(self.dir,self.name)
        try:
            ins = Tes3Reader(self.name,file(path,'rb'))
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            if name != 'TES3': raise Tes3Error(self.name,_(u'Expected TES3, but got ')+name)
            self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        except struct.error, rex:
            ins.close()
            raise Tes3Error(self.name,u'Struct.error: '+`rex`)
        except Tes3Error, error:
            ins.close()
            error.inName = self.name
            raise
        #--Master sizes (for getMasterStatus)
        masterNames = []
        self.masterSizes.clear()
        for (master,size) in self.tes3.masters:
            self.masterSizes[master] = size
            masterNames.append(master)
        self.masterNames = tuple(masterNames)
        self.masterOrder = tuple() #--Reset to empty for now
        #--Free some memory
        self.tes3.data = None
        self.tes3.others = None
        #--Done
        ins.close()

    def getMasterStatus(self,masterName):
        #--Exists?
        if not modInfos.has_key(masterName): return 30
        #--Sizes differ?
        elif ((masterName in self.masterSizes) and
            (self.masterSizes[masterName] != modInfos[masterName].size)):
            return 10
        #--Okay?
        else: return 0

    def getStatus(self):
        status = 0
        #--Worst status from masters
        for masterName in self.masterSizes.keys():
            status = max(status,self.getMasterStatus(masterName))
        #--Missing files?
        if status == 30: return status
        #--Natural misordering?
        self.masterOrder = modInfos.getLoadOrder(self.masterNames)
        if self.masterOrder != self.masterNames: return 20
        else: return status

    #--New File
    def writeNew(self,masters=[],mtime=0):
        """Creates a new file with the given name, masters and mtime."""
        tes3 = Tes3()
        tes3.hedr = Tes3_Hedr('HEDR',0)
        if   self.isEsp(): tes3.hedr.fileType = 0
        elif self.isEsm(): tes3.hedr.fileType = 1
        elif self.isEss(): tes3.hedr.fileType = 32
        for master in masters:
            tes3.masters.append((master,modInfos[master].size))
        tes3.hedr.setChanged()
        tes3.setChanged()
        #--Write it
        path = os.path.join(self.dir,self.name)
        out = file(path,'wb')
        tes3.getSize()
        tes3.dump(out)
        out.close()
        self.setMTime(mtime)

    def writeHedr(self):
        """Writes hedr subrecord to file, overwriting old hedr."""
        path = os.path.join(self.dir,self.name)
        out = file(path,'r+b')
        out.seek(16) #--Skip to Hedr record data
        self.tes3.hedr.getSize()
        self.tes3.hedr.dump(out)
        out.close()
        #--Done
        self.getHeader()
        self.setMTime()

    def writeDescription(self,description):
        """Sets description to specified text and then writes hedr."""
        description = description[:min(255,len(description))]
        self.tes3.hedr.description = description
        self.tes3.hedr.setChanged()
        self.writeHedr()

    def writeAuthor(self,author):
        """Sets author to specified text and then writes hedr."""
        author = author[:min(32,len(author))]
        self.tes3.hedr.author = author
        self.tes3.hedr.setChanged()
        self.writeHedr()

    def writeAuthorWM(self):
        """Marks author field with " [wm]" to indicate Mash modification."""
        author = self.tes3.hedr.author
        if '[wm]' not in author and len(author) <= 27:
            self.writeAuthor(author+' [wm]')

    def setMTime(self,mtime=0):
        """Sets mtime. Defaults to current value (i.e. reset)."""
        mtime = mtime or self.mtime
        path = os.path.join(self.dir,self.name)
        os.utime(path,(time.time(),mtime))
        self.mtime = getmtime(path)

    def makeBackup(self, forceBackup=False):
        if self.madeBackup and not forceBackup: return
        #--Backup Directory
        backupDir = os.path.join(self.dir,settings['mosh.fileInfo.backupDir'])
        if not os.path.exists(backupDir): os.makedirs(backupDir)
        #--File Path
        original = os.path.join(self.dir,self.name)
        #--Backup
        backup = os.path.join(backupDir,self.name)
        shutil.copy(original,backup)
        #--First backup
        firstBackup = backup+'f'
        if not os.path.exists(firstBackup):
            shutil.copy(original,firstBackup)
        #--Done
        self.madeBackup = True

    def getStats(self):
        stats = self.stats = {}
        path = os.path.join(self.dir,self.name)
        ins = Tes3Reader(self.name,file(path,'rb'))
        while not ins.atEnd():
            #--Get record info and handle it
            (type,size,delFlag,recFlag) = ins.unpackRecHeader()
            if type not in stats:
                stats[type] = (1,size)
            else:
                count, cumSize = stats[type]
                stats[type] = (count+1, cumSize+size+16) #--16B in header
            #--Seek to next record
            ins.seek(size,1,'Record')
        #--Done
        ins.close()

    #--Snapshot Parameters
    def getNextSnapshot(self):  # Polemos: Unicode fix. Strange one. Was it mine? Questions, questions, questions... (b)
        destDir = (os.path.join(self.dir,settings['mosh.fileInfo.snapshotDir']))#.encode('utf8')
        if not os.path.exists(destDir): os.makedirs(destDir)
        (root,ext) = os.path.splitext(self.name)
        destName = root+'-00'+ext
        separator = '-'
        snapLast = ['00']
        #--Look for old snapshots.
        reSnap = re.compile('^'+root+'-([0-9\.]*[0-9]+)'+ext+'$')
        for fileName in scandir.listdir(destDir):
            maSnap = reSnap.match(fileName)
            if not maSnap: continue
            snapNew = maSnap.group(1).split('.')
            #--Compare shared version numbers
            sharedNums = min(len(snapNew),len(snapLast))
            for index in xrange(sharedNums):
                (numNew,numLast) = (int(snapNew[index]),int(snapLast[index]))
                if numNew > numLast:
                    snapLast = snapNew
                    continue
            #--Compare length of numbers
            if len(snapNew) > len(snapLast):
                snapLast = snapNew
                continue
        #--New
        snapLast[-1] = ('%0'+`len(snapLast[-1])`+'d') % (int(snapLast[-1])+1,)
        destName = root+separator+('.'.join(snapLast))+ext
        wildcard = root+'*'+ext
        wildcard = _(u'%s Snapshots|%s|All Snapshots|*.esp;*.esm;*.ess') % (root,wildcard)
        return (destDir,destName,wildcard)

#------------------------------------------------------------------------------

class FileInfos: # + OpenMW/TES3mp support

    def __init__(self,dir,factory=FileInfo):
        """Init with specified directory and specified factory type."""
        self.OpenMW = settings['openmw']
        self.dir = dir
        self.factory=factory
        self.data = {}
        if not self.OpenMW: # Morrowind support
            self.table = Table(os.path.join(self.dir,'Mash','Table.pkl'))
        if self.OpenMW: # OpenMW/TES3mp support
            self.table = Table(os.path.join(MashDir, 'openmw', 'Table.pkl'))
        self.corrupted = {} #--errorMessage = corrupted[fileName]

    #--Dictionary Emulation
    def __contains__(self,key):
        """Dictionary emulation."""
        return key in self.data
    def __getitem__(self,key):
        """Dictionary emulation."""
        try:  return self.data[key]  # Polemos: Hack' a doro, In case the file where
        except: pass                 # the key is pointing is missing.Be Exceptional!
    def __setitem__(self,key,value):
        """Dictionary emulation."""
        self.data[key] = value
    def __delitem__(self,key):
        """Dictionary emulation."""
        del self.data[key]
    def keys(self):
        """Dictionary emulation."""
        return self.data.keys()
    def has_key(self,key):
        """Dictionary emulation."""
        return self.data.has_key(key)
    def get(self,key,default):
        """Dictionary emulation."""
        return self.data.get(key,default)

    #--Refresh File
    def refreshFile(self,fileName):
        try:
            fileInfo = self.factory(self.dir,fileName)
            fileInfo.getHeader()
            self.data[fileName] = fileInfo
        except Tes3Error, error:
            self.corrupted[fileName] = error.message
            if fileName in self.data: del self.data[fileName]
            raise

    def refresh(self):
        """Morrowind - OpenMW/TES3mp junction."""
        if not self.OpenMW:  # Morrowind support
            return self.refresh_Morrowind()
        if self.OpenMW:  # OpenMW/TES3mp support
            return self.refresh_OpenMW()

    def refresh_OpenMW(self):
        data = self.data
        oldList = data.keys()
        newList = []
        added = []
        updated = []
        deleted = []
        if self.dir == os.path.join(settings['openmwprofile'], 'Saves'):
            if not os.path.exists(self.dir): os.makedirs(self.dir)
            contents = scandir.listdir(self.dir)
            type_po = 'saves'
        else:
            contents = MWIniFile(settings['openmwprofile']).openmw_data_files()
            type_po = 'mods'
        for dir in contents:  #--Loop over files in directory
            if type_po == 'mods':
                if os.path.exists(dir): self.dir = dir
            for fileName in scandir.listdir(self.dir):
                fileName = fileName
                #--Right file type?
                filePath = os.path.join(self.dir,fileName)
                if not os.path.isfile(filePath) or not self.rightFileType(fileName): continue
                fileInfo = self.factory(self.dir,fileName)
                if fileName not in oldList:  #--New file?
                    try: fileInfo.getHeader()
                    except Tes3Error, error:  #--Bad header?
                        self.corrupted[fileName] = error.message
                        continue
                    else:  #--Good header?
                        if fileName in self.corrupted: del self.corrupted[fileName]
                        added.append(fileName)
                        data[fileName] = fileInfo
                elif not fileInfo.sameAs(data[fileName]):  #--Updated file?
                    try:
                        fileInfo.getHeader()
                        data[fileName] = fileInfo
                    except Tes3Error, error:  #--Bad header?
                        self.corrupted[fileName] = error.message
                        del self.data[fileName]
                        continue
                    else:  #--Good header?
                        if fileName in self.corrupted: del self.corrupted[fileName]
                        updated.append(fileName)
                #--No change?
                newList.append(fileName)
        for fileName in oldList:  #--Any files deleted?
            if fileName not in newList:
                deleted.append(fileName)
                del self.data[fileName]
        return (len(added) or len(updated) or len(deleted))

    def refresh_Morrowind(self):
        data = self.data
        oldList = data.keys()
        newList = []
        added = []
        updated = []
        deleted = []
        if not os.path.exists(self.dir): os.makedirs(self.dir)
        for fileName in scandir.listdir(self.dir):  #--Loop over files in directory
            fileName = fileName
            # --Right file type?
            filePath = os.path.join(self.dir, fileName)
            if not os.path.isfile(filePath) or not self.rightFileType(fileName): continue
            fileInfo = self.factory(self.dir, fileName)
            if fileName not in oldList:  # --New file?
                try: fileInfo.getHeader()
                except Tes3Error, error:  # --Bad header?
                    self.corrupted[fileName] = error.message
                    continue
                else:  # --Good header?
                    if fileName in self.corrupted: del self.corrupted[fileName]
                    added.append(fileName)
                    data[fileName] = fileInfo
            elif not fileInfo.sameAs(data[fileName]):  # --Updated file?
                try:
                    fileInfo.getHeader()
                    data[fileName] = fileInfo
                except Tes3Error, error:  # --Bad header?
                    self.corrupted[fileName] = error.message
                    del self.data[fileName]
                    continue
                else:  # --Good header?
                    if fileName in self.corrupted: del self.corrupted[fileName]
                    updated.append(fileName)
            # --No change?
            newList.append(fileName)
        for fileName in oldList: #--Any files deleted?
            if fileName not in newList:
                deleted.append(fileName)
                del self.data[fileName]
        return (len(added) or len(updated) or len(deleted))

    def rightFileType(self,fileName):  #--Right File Type? [ABSTRACT]
        """Bool: filetype (extension) is correct for subclass. [ABSTRACT]"""
        raise AbstractError

    def rename(self,oldName,newName):  #--Rename
        """Renames member file from oldName to newName."""
        #--Update references
        fileInfo = self[oldName]
        self[newName] = self[oldName]
        del self[oldName]
        self.table.moveRow(oldName,newName)
        #--FileInfo
        fileInfo.name = newName
        #--File system
        newPath = os.path.join(fileInfo.dir,newName)
        oldPath = os.path.join(fileInfo.dir,oldName)
        renameFile(oldPath,newPath)
        #--Done
        fileInfo.madeBackup = False

    def delete(self,fileName):  #--Delete
        """Deletes member file."""
        fileInfo = self[fileName]
        #--File
        filePath = os.path.join(fileInfo.dir,fileInfo.name)
        os.remove(filePath)
        #--Table
        self.table.delRow(fileName)
        #--Misc. Editor backups
        for ext in ('.bak','.tmp','.old'):
            backPath = filePath + ext
            if os.path.exists(backPath): os.remove(backPath)
        #--Backups
        backRoot = os.path.join(fileInfo.dir,settings['mosh.fileInfo.backupDir'],fileInfo.name)
        for backPath in (backRoot,backRoot+'f'):
            if os.path.exists(backPath): os.remove(backPath)
        self.refresh()

    def moveIsSafe(self,fileName,destDir):  #--Move Exists
        """Bool: Safe to move file to destDir."""
        return not os.path.exists(os.path.join(destDir,fileName))

    def move(self,fileName,destDir):  #--Move
        """Moves member file to destDir. Will overwrite!"""
        if not os.path.exists(destDir):
            os.makedirs(destDir)
        srcPath = os.path.join(self.dir,fileName)
        destPath = os.path.join(destDir,fileName)
        renameFile(srcPath,destPath)
        self.refresh()

    def copy(self,fileName,destDir,destName=None,setMTime=False):  #--Copy
        """Copies member file to destDir. Will overwrite!"""
        if not os.path.exists(destDir):
            os.makedirs(destDir)
        if not destName: destName = fileName
        srcPath = os.path.join(self.dir,fileName)
        destPath = os.path.join(destDir,destName)
        if os.path.exists(destPath):
            os.remove(destPath)
        shutil.copyfile(srcPath,destPath)
        if setMTime:
            mtime = getmtime(srcPath)
            os.utime(destPath,(time.time(),mtime))
        self.refresh()

#------------------------------------------------------------------------------

class ModInfo(FileInfo):
    """Return mod status."""

    def isWellOrdered(self):
        """True if it is ordered correctly by datetime."""
        try: return not modInfos.doubleTime[self.mtime]  # Happens...
        except: pass

    def isExOverLoaded(self):
        """True if it belongs to an exclusion group that is overloaded."""
        maExGroup = reExGroup.match(self.name)
        if not (mwIniFile.isLoaded(self.name) and maExGroup): return False
        else: return (maExGroup.group(1) in mwIniFile.exOverLoaded)

    def setMTime(self,mtime=0):
        """Sets mtime. Defaults to current value (i.e. reset)."""
        mtime = mtime or self.mtime
        FileInfo.setMTime(self,mtime)
        modInfos.mtimes[self.name] = mtime

#------------------------------------------------------------------------------

class ResourceReplacer:
    """Resource Replacer. Used to apply and remove a set of resource (texture, etc.) replacement files."""
    #--Class data
    textureExts = {'.dds', '.tga', '.bmp'}
    dirExts = {
        'bookart':  textureExts,
        'fonts': {'.fnt', '.tex'},
        'icons':    textureExts,
        'meshes': {'.nif', '.kf'},
        'music': {'.mp3'},
        'sound': {'.wav'},
        'splash':   textureExts,
        'textures': textureExts,
        }

    def __init__(self,replacerDir,file):
        """Initialize"""
        self.replacerDir = replacerDir
        self.file = file
        self.progress = None
        self.cumSize = 0

    def isApplied(self):
        """Returns True if has been applied."""
        return self.file in settings['mosh.resourceReplacer.applied']

    def apply(self,progress=None):
        """Copy files to appropriate resource directories (Textures, etc.)."""
        if progress:
            self.progress = progress
            self.cumSize = 0
            self.totSize = 0
            self.doRoot(self.sizeDir)
            self.progress.setMax(self.totSize)
        self.doRoot(self.applyDir)
        settings.getChanged('mosh.resourceReplacer.applied').append(self.file)
        self.progress = None

    def remove(self):
        """Uncopy files from appropriate resource directories (Textures, etc.)."""
        self.doRoot(self.removeDir)
        settings.getChanged('mosh.resourceReplacer.applied').remove(self.file)

    def doRoot(self,action):
        """Copy/uncopy files to/from appropriate resource directories."""
        #--Root directory is Textures directory?
        dirExts = ResourceReplacer.dirExts
        textureExts = ResourceReplacer.textureExts
        srcDir = os.path.join(self.replacerDir,self.file)
        destDir = modInfos.dir
        isTexturesDir = True #--Assume true for now.
        for srcFile in scandir.listdir(srcDir):
            srcPath  = os.path.join(srcDir,srcFile)
            if os.path.isdir(srcPath) and srcFile.lower() in dirExts:
                isTexturesDir = False
                destPath = os.path.join(destDir,srcFile)
                action(srcPath,destPath,dirExts[srcFile.lower()])
        if isTexturesDir:
            destPath = os.path.join(destDir,'Textures')
            action(srcDir,destPath,textureExts)

    def sizeDir(self,srcDir,destDir,exts):
        """Determine cumulative size of files to copy."""
        for srcFile in scandir.listdir(srcDir):
            srcExt = os.path.splitext(srcFile)[-1].lower()
            srcPath  = os.path.join(srcDir,srcFile)
            destPath = os.path.join(destDir,srcFile)
            if srcExt in exts:
                self.totSize += os.path.getsize(srcPath)
            elif os.path.isdir(srcPath):
                self.sizeDir(srcPath,destPath,exts)

    def applyDir(self,srcDir,destDir,exts):
        """Copy files to appropriate resource directories (Textures, etc.)."""
        for srcFile in scandir.listdir(srcDir):
            srcExt = os.path.splitext(srcFile)[-1].lower()
            srcPath  = os.path.join(srcDir,srcFile)
            destPath = os.path.join(destDir,srcFile)
            if srcExt in exts:
                if not os.path.exists(destDir):
                    os.makedirs(destDir)
                shutil.copyfile(srcPath,destPath)
                if self.progress:
                    self.cumSize += os.path.getsize(srcPath)
                    self.progress(self.cumSize,_(u'Copying Files...'))
            elif os.path.isdir(srcPath):
                self.applyDir(srcPath,destPath,exts)

    def removeDir(self,srcDir,destDir,exts):
        """Uncopy files from appropriate resource directories (Textures, etc.)."""
        for srcFile in scandir.listdir(srcDir):
            srcExt = os.path.splitext(srcFile)[-1].lower()
            srcPath  = os.path.join(srcDir,srcFile)
            destPath = os.path.join(destDir,srcFile)
            if os.path.exists(destPath):
                if srcExt in exts:
                    os.remove(destPath)
                elif os.path.isdir(srcPath):
                    self.removeDir(srcPath,destPath,exts)

#------------------------------------------------------------------------------

class ModInfos(FileInfos):

    def __init__(self,dir,factory=ModInfo):
        """Init."""
        FileInfos.__init__(self,dir,factory)
        self.OpenMW = settings['openmw']
        self.resetMTimes = settings['mosh.modInfos.resetMTimes']
        self.mtimes = self.table.getColumn('mtime')
        self.mtimesReset = [] #--Files whose mtimes have been reset.
        self.doubleTime = {}
        self.objectMaps = None

    def refreshFile(self,fileName):
        """Refresh File."""
        try: FileInfos.refreshFile(self,fileName)
        finally: self.refreshDoubleTime()

    def refresh(self):
        """Refresh."""
        hasChanged = FileInfos.refresh(self)
        if hasChanged:
            #--Reset MTimes?
            if self.resetMTimes:
                self.refreshMTimes()
            #--Any load files disappeared?
            for loadFile in mwIniFile.loadFiles[:]:
                if loadFile not in self.data:
                    self.unload(loadFile)
            self.refreshDoubleTime()
        #--Update mwIniLoadOrder
        mwIniFile.loadOrder = modInfos.getLoadOrder(mwIniFile.loadFiles)
        if self.OpenMW: mwIniFile.safeSave()
        return hasChanged

    def refreshMTimes(self):
        """Remember/reset mtimes of member files."""
        del self.mtimesReset[:]
        for fileName, fileInfo in self.data.items():
            oldMTime = self.mtimes.get(fileName,fileInfo.mtime)
            self.mtimes[fileName] = oldMTime
            #--Reset mtime?
            if fileInfo.mtime != oldMTime and oldMTime != -1:
                fileInfo.setMTime(oldMTime)
                self.mtimesReset.append(fileName)

    def refreshDoubleTime(self):
        """Refresh doubletime dictionary."""
        doubleTime = self.doubleTime
        doubleTime.clear()
        for modInfo in self.data.values():
            mtime = modInfo.mtime
            doubleTime[mtime] = doubleTime.has_key(mtime)
        #--Refresh MWIni File too
        mwIniFile.refreshDoubleTime()

    def rightFileType(self,fileName):
        """Bool: File is a mod."""
        if not self.OpenMW:
            fileExt = fileName[-4:].lower()
            return (fileExt == '.esp' or fileExt == '.esm')
        else:
            fileExt0 = fileName[-4:].lower()
            fileExt1 = fileName[-9:].lower()
            fileExt2 = fileName[-8:].lower()
            return (fileExt0 == '.esp' or fileExt0 == '.esm' or fileExt1 == '.omwaddon' or fileExt2 == '.omwgame')

    def getVersion(self,fileName):
        """Extracts and returns version number for fileName from tes3.hedr.description."""
        if not fileName in self.data or not self.data[fileName].tes3:
            return ''
        maVersion = reVersion.search(self.data[fileName].tes3.hedr.description)
        return (maVersion and maVersion.group(2)) or ''

    def circularMasters(self,stack,masters=None):
        """Circular Masters."""
        stackTop = stack[-1]
        masters = masters or (stackTop in self.data and self.data[stackTop].masterNames)
        if not masters: return False
        for master in masters:
            if master in stack: return True
            if self.circularMasters(stack+[master]): return True
        return False

    def getLoadOrder(self, modNames, asTuple=True): #--Get load order
        """Sort list of mod names into their load order. ASSUMES MODNAMES ARE UNIQUE!!!"""
        data = self.data
        modNames = list(modNames) #--Don't do an in-place sort.
        modNames.sort()
        modNames.sort(key=lambda a: (a in data) and data[a].mtime) #--Sort on modified
        if not self.OpenMW:
            # Polemos: Not really needed for OpenMW implementation. Even though the Timsort algorithm (used in
            # Python) is efficient with pre-sorted lists, we lose the advantage due to the added complexity.
            modNames.sort(key=lambda a: a[-1].lower()) #--Sort on esm/esp
        #--Match Bethesda's esm sort order
        #  - Start with masters in chronological order.
        #  - For each master, if it's masters (mm's) are not already in list,
        #    then place them ahead of master... but in REVERSE order. E.g., last
        #    grandmaster will be first to be added.
        def preMaster(modName, modDex):
            """If necessary, move grandmasters in front of master -- but in reverse order."""
            if self.data.has_key(modName):
                mmNames = list(self.data[modName].masterNames[:])
                mmNames.reverse()
                for mmName in mmNames:
                    if mmName in modNames:
                        mmDex = modNames.index(mmName)
                        #--Move master in front and pre-master it too.
                        if mmDex > modDex:
                            del modNames[mmDex]
                            modNames.insert(modDex, mmName)
                            modDex = 1 + preMaster(mmName, modDex)
            return modDex
        #--Read through modNames.
        modDex = 1
        while modDex < len(modNames):
            modName = modNames[modDex]
            if modName[-1].lower() != 'm': break
            if self.circularMasters([modName]): modDex += 1
            else: modDex = 1 + preMaster(modName, modDex)
        #--Convert? and return
        if asTuple: return tuple(modNames)
        else: return modNames

    def isLoaded(self, fileName): #--Loading
        """True if fileName is in the the load list."""
        return mwIniFile.isLoaded(fileName)

    def load(self, fileNames, doSave=True):  # Polemos: Speed up
        """Adds file to load list."""
        if type(fileNames) in [str, unicode]: fileNames = [fileNames]
        #--Load masters
        modFileNames = self.keys()
        for x in fileNames:
            if x not in self.data: continue  # Polemos fix: In case a mod is missing
            for master, size in self[x].tes3.masters:
                if master in modFileNames and master != x:
                    self.load(master, False)
        #--Load self
        mwIniFile.load(fileNames, doSave)

    def unload(self, fileNames, doSave=True):  # Polemos: Speed up
        """Removes file from load list."""
        if type(fileNames) in [str, unicode]: fileNames = [fileNames]
        #--Unload fileName
        mwIniFile.unload(fileNames, False)
        #--Unload fileName's children
        loadFiles = mwIniFile.loadFiles[:]
        for loadFile in loadFiles:
            #--Already unloaded? (E.g., grandchild)
            if not mwIniFile.isLoaded(loadFile): continue
            # --Can happen if user does an external delete.
            if loadFile not in self.data: continue
            for x in fileNames: #--One of loadFile's masters?
                for master in self[loadFile].tes3.masters:
                    if master[0] == x:
                        self.unload(loadFile,False)
                        break
        #--Save
        if doSave: mwIniFile.safeSave()

    def rename(self,oldName,newName):
        """Renames member file from oldName to newName."""
        isLoaded = self.isLoaded(oldName)
        if isLoaded: self.unload(oldName)
        FileInfos.rename(self,oldName,newName)
        self.refreshDoubleTime()
        if isLoaded: self.load(newName)

    def delete(self,fileName):
        """Deletes member file."""
        self.unload(fileName)
        FileInfos.delete(self,fileName)

    def move(self,fileName,destDir):
        """Moves member file to destDir."""
        self.unload(fileName)
        FileInfos.move(self,fileName,destDir)

    def getResourceReplacers(self):
        """Returns list of ResourceReplacer objects for subdirectories of Replacers directory."""
        replacers = {}
        replacerDir = os.path.join(self.dir,'Replacers')
        if not os.path.exists(replacerDir):
            return replacers
        if 'mosh.resourceReplacer.applied' not in settings:
            settings['mosh.resourceReplacer.applied'] = []
        for name in scandir.listdir(replacerDir):
            path = os.path.join(replacerDir,name)
            if os.path.isdir(path):
                replacers[name] = ResourceReplacer(replacerDir,name)
        return replacers

    def addObjectMap(self,fromMod,toMod,objectMap):
        """Add an objectMap with key(fromMod,toMod)."""
        if self.objectMaps is None: self.loadObjectMaps()
        self.objectMaps[(fromMod,toMod)] = objectMap

    def removeObjectMap(self,fromMod,toMod):
        """Deletes objectMap with key(fromMod,toMod)."""
        if self.objectMaps is None: self.loadObjectMaps()
        del self.objectMaps[(fromMod,toMod)]

    def getObjectMap(self,fromMod,toMod):
        """Returns objectMap with key(fromMod,toMod)."""
        if self.objectMaps is None: self.loadObjectMaps()
        return self.objectMaps.get((fromMod,toMod),None)

    def getObjectMaps(self,toMod):
        """Return a dictionary of ObjectMaps with fromMod key for toMod."""
        if self.objectMaps is None: self.loadObjectMaps()
        subset = {}
        for key in self.objectMaps.keys():
            if key[1] == toMod:
                subset[key[0]] = self.objectMaps[key]
        return subset

    def loadObjectMaps(self):
        """Load ObjectMaps from file."""
        path = os.path.join(self.dir, settings['mosh.modInfos.objectMaps'])
        try:
            if os.path.exists(path):
                self.objectMaps = compat.uncpickle(path)
            else: self.objectMaps = {}
        except EOFError:  # Polemos: Fix for corrupted Updaters pkl
            import gui.dialog, wx
            if gui.dialog.ErrorQuery(None, _(u'Updaters data has been corrupted and needs to be reset.\n\nClick '
                u'Yes to automatically delete the updaters data file.\n(This will make Wrye Mash forget which mods it has updated '
                    u'but it will not affect your updated saves - an inconvenience really).\n\nClick No if you wish to do it '
                        u'manually by deleting the following file:\n%s') % path) == wx.ID_YES:
                try: os.remove(path)
                except: gui.dialog.ErrorMessage(None, _(u'Wrye Mash was unable to delete the file which '
                    u'holds the Updaters data. You need to manually delete the following file:\n\n"%s"' % path))

    def saveObjectMaps(self):
        """Save ObjectMaps to file."""
        if self.objectMaps is None: return
        path = os.path.join(self.dir,settings['mosh.modInfos.objectMaps'])
        outDir = os.path.split(path)[0]
        if not os.path.exists(outDir): os.makedirs(outDir)
        cPickle.dump(self.objectMaps,open(path,'wb'),-1)

#------------------------------------------------------------------------------

class ReplJournalDate:
    """Callable: Adds <hr>before journal date."""
    def __init__(self):
        self.prevDate = None

    def __call__(self,mo):
        prevDate = self.prevDate
        newDate = mo.group(1)
        if newDate != prevDate:
            hr = prevDate and '<hr>' or ''
            self.prevDate = newDate
            return '%s<FONT COLOR="9F0000"><B>%s</B></FONT><BR>' % (hr,newDate)
        else: return ''

#------------------------------------------------------------------------------

class SaveInfo(FileInfo):  # Polemos: Fixed a small (ancient again) bug with the journal.
    """Representation of a savegame file."""

    def getStatus(self):
        """Returns the status, i.e., "health" level of the savegame. Based on
        status/health of masters, plus synchronization with current load list."""
        status = FileInfo.getStatus(self)
        masterOrder = self.masterOrder
        #--File size?
        if status > 0 or len(masterOrder) > len(mwIniFile.loadOrder): return status
        #--Current ordering?
        if masterOrder != mwIniFile.loadOrder[:len(masterOrder)]: return status
        elif masterOrder == mwIniFile.loadOrder: return -20
        else: return -10

    def getJournal(self):
        """Returns the text of the journal from the savegame in slightly
        modified html format."""
        if 'journal' in self.extras: return self.extras['journal']
        #--Default
        self.extras['journal'] = _(u'[No Journal Record Found.]')
        #--Open save file and look for journal entry
        inPath = os.path.join(self.dir,self.name)
        ins = Tes3Reader(self.name, file(inPath, 'rb'))
        #--Raw data read
        while not ins.atEnd():
            #--Get record info and handle it
            (name, size, delFlag, recFlag) = ins.unpackRecHeader()
            if name != 'JOUR': ins.seek(size, 1, name)
            #--Journal
            else:
                (subName,subSize) = ins.unpackSubHeader('JOUR')
                if subName != 'NAME': self.extras['journal'] = _(u'[Error reading file.]')  # Polemos fix: removed double '='
                else:
                    reDate = re.compile(r'<FONT COLOR="9F0000">(.+?)</FONT><BR>')
                    reTopic = re.compile(r'@(.*?)#')
                    data = ins.read(subSize)
                    data = reDate.sub(ReplJournalDate(),data)
                    data = reTopic.sub(r'\1',data)
                    self.extras['journal'] = cstrip(data)
                break
        #--Done
        ins.close()
        # print self.extras['journal']  <== Polemos: the journal bug (easy to happen),
        # it was present at least since Melchior's version up to Yakoby's.
        return self.extras['journal']

    def getScreenshot(self):  # Polemos fixes
        """Returns screenshot data with alpha info stripped out. If screenshot data isn't available, returns None."""
        #--Used cached screenshot, if have it.
        if 'screenshot' in self.extras: return self.extras['screenshot']
        #--Gets tes3 header
        path = os.path.join(self.dir, self.name)
        try:
            ins = Tes3Reader(self.name,file(path,'rb'))
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            if name != 'TES3': raise Tes3Error(self.name,_(u'Expected TES3, but got %s' % name))
            self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        except struct.error, rex:
            ins.close()
            raise Tes3Error(self.name,_(u'Struct.error: %s' % rex))
        except Tes3Error, error:
            ins.close()
            error.inName = self.name
            raise
        ins.close()
        #--Get screenshot data subrecord
        for subrecord in self.tes3.others:
            if subrecord.name == 'SCRS':
                #--Convert bgra array to rgb array
                buff = cStringIO.StringIO()
                for num in xrange(len(subrecord.data)/4):
                    bb,gg,rr = struct.unpack('3B',subrecord.data[num*4:num*4+3])
                    buff.write(struct.pack('3B',rr,gg,bb))
                rgbString = buff.getvalue()
                try: #--Image processing (brighten, increase range)
                    rgbArray = array.array('B',rgbString)
                    rgbAvg   = float(sum(rgbArray))/len(rgbArray)
                    rgbSqAvg = float(sum(xx*xx for xx in rgbArray))/len(rgbArray)
                    rgbSigma = math.sqrt(rgbSqAvg - rgbAvg*rgbAvg)
                    rgbScale = max(1.0,80/rgbSigma)
                    def remap(color):
                        color = color - rgbAvg
                        color = color * rgbScale
                        return max(0,min(255,int(color+128)))
                except: pass
                buff.seek(0)
                try: [buff.write(struct.pack('B',remap(ord(char)))) for num,char in enumerate(rgbString)]
                except: pass
                screenshot = buff.getvalue()
                buff.close()
                break
        else: #--No SCRS data
            screenshot = None
        #--Cache and return
        self.extras['screenshot'] = screenshot
        return screenshot

#------------------------------------------------------------------------------

class SaveInfos(FileInfos):
    """Collection of saveInfos for savefiles in the saves directory."""
    #--Init
    def __init__(self,dir,factory=SaveInfo):
        FileInfos.__init__(self,dir,factory)

    #--Right File Type (Used by Refresh)
    def rightFileType(self,fileName):
        return (fileName[-4:].lower() == '.ess')

#------------------------------------------------------------------------------

class ResPack:
    """Resource package (BSA or resource replacer). This is the abstract supertype."""

    def getOrder(self):
        """Returns load order number or None if not loaded."""
        raise AbstractError
    def rename(self,newName):
        """Renames respack."""
        raise AbstractError
    def duplicate(self,newName):
        """Duplicates self with newName."""
        raise AbstractError
    def select(self):
        """Selects package."""
        raise AbstractError
    def unselect(self):
        """Unselects package."""
        raise AbstractError
    def isSelected(self):
        """Returns True if is currently selected."""
        raise AbstractError

#------------------------------------------------------------------------------

class BSAPack(ResPack):
    """BSA file resource package."""
    pass

#------------------------------------------------------------------------------

class ResReplacerPack(ResPack):
    """Resource replacer directory."""
    pass

#------------------------------------------------------------------------------

class ResPacks:
    """Collection of Res Packs (BSAs and Resource Replacers)."""
    def __init__(self):
        """Initialize. Get BSA and resource replacers."""
        self.data = {}
        self.refresh()

    def refresh(self):
        """Refreshes BSA and resource replacers."""
        raise UncodedError

#------------------------------------------------------------------------------

utilsCommands = ("mish",)
class UtilsData(DataDict): # Polemos: Many changes here.
    """UtilsData #-# D.C.-G for UtilsPanel extension."""
    def __init__(self):
        """Initialize."""
        self.dir = dirs['app']
        self.data = {}
        self.badata = []
        if not os.path.isfile('utils.dcg'): self.rebuilt_config()

    def refresh(self):
        """Refresh list of utilities."""
        self.dir = dirs['app']
        #-# Since there is only one utils file, its name is hardcoded.
        utilsFile = "utils.dcg"
        newData = {}
        if os.path.isfile(utilsFile) and os.access(utilsFile, os.R_OK):
            with io.open(utilsFile, "r", encoding='utf-8', errors='replace') as file:
                lines = file.readlines()
            for line in lines:
                line = line.rstrip()
                if not line.startswith(";") and line != "":
                    try:
                        ID, commandLine, arguments, description = line.split(";", 3)
                        newData[ID] = (commandLine, arguments, description.strip())
                        check = int(ID)
                    except: continue
        changed = (str(self.data) != str(newData))
        self.data = newData
        return changed

    def rebuilt_config(self):
        default_text = (u'; utils.dcg\r\n'
                        u'; File containing the mash utils data\r\n'
                        u';\r\n'
                        u'; Format of a Utility entry:\r\n'
                        u';\r\n'
                        u'; ID of the utility; Filename; Parameters; Description of the utility; Name of the Utility\r\n\r\n')
        with io.open('utils.dcg', "w", encoding='utf-8') as file:
            file.write(default_text)

    def delete(self,fileName):
        """Deletes member file."""
        filePath = self.dir.join(fileName)
        filePath.remove()
        del self.data[fileName]

    def save(self):  # Polemos: fixes
        """Writes the file on the disk."""
        utilsFile = "utils.dcg"
        orgData = {}
        self.badata = []
        if os.path.isfile(utilsFile) and os.access(utilsFile, os.R_OK):
            with io.open(utilsFile, 'r', encoding='utf-8', errors='replace') as file:
                lines = file.readlines()
            lines = [line.rstrip() for line in lines]
            for line in lines:
                if not line.startswith(";") and line != "":
                    try:
                        ID, commandLine, arguments, description = line.split(";", 3)
                        orgData[ID] = (commandLine, arguments, description.strip())
                        check = int(ID)
                    except:
                        self.badata.append(line)
                        continue
        changed = (str(self.data) != str(orgData))

        if changed: # Items removed
            [lines.remove(line) for key in orgData.keys() if key not in self.data.keys() for line in lines if line.startswith(key)]

            # Items added or modified
            for key, value in self.data.iteritems():
                if key not in orgData.keys():
                    try: lines.append(u"%s;%s;%s;%s".encode('utf-8').decode('utf-8') % ((key,) + value))
                    except: lines.append(u"%s;%s;%s;%s".decode('utf-8') % ((key,) + value))
                elif key in orgData.keys():
                    for line in lines:
                        try:
                            if line.startswith(key):
                                idx = lines.index(line)
                                lines[idx] = u"%s;%s;%s;%s" % ((key,) + value)
                        except: pass
            with io.open(utilsFile, "w", encoding='utf-8', errors='replace') as file:
                lines = '\r\n'.join([line for line in lines if line not in self.badata])
                try: file.write(lines.encode('utf-8'))
                except: file.write(lines)

#------------------------------------------------------------------------------

class CommandsData:
    """Create Custom Commands."""
    def __init__(self, window):
        self.config_file_path = os.path.join(MashDir, 'custom.dcg')
        import gui.dialog as gui
        self.gui = gui
        self.window = window
        self.data = {}

    def execute(self):
        self.load_commands()
        self.DoConfig()

    def Get(self):
        self.load_commands()
        return self.data

    def load_commands(self):
        if not os.path.isfile(self.config_file_path): self.save_commands(save_default=True)
        try:
            if os.path.isfile(self.config_file_path) and os.access(self.config_file_path, os.R_OK):
                with io.open(self.config_file_path, 'r', encoding='utf-8', errors='replace') as file:
                    config_file = file.readlines()
                commands = {}
                for line in config_file:
                    line = line.strip()
                    if not line.startswith(u';') and line != u'':
                        try:
                            name = line.split(u';')[0]
                            args = u';'.join(line.split(u';')[1:])
                            commands[name] = args
                        except: pass
                self.data = commands
        except: pass #self.gui.ErrorMessage(None, _(u'A problem has occurred while loading "custom.dcg" to import your custom commands.\n'))

    def save_commands(self, save_default=False):
        try:
            with io.open(self.config_file_path, 'w', encoding='utf-8', errors='replace') as file:
                file.write(self.default_config_file())
                if not save_default:
                    for key, value in self.data.iteritems():
                        try: file.write(u'%s;%s\n' % (key, value))
                        except: pass
        except: pass # self.gui.ErrorMessage(None, _(u'A problem has occurred while saving/creating "custom.dcg" to export your custom commands.\n'))

    def default_config_file(self):
        return (u'; custom.dcg\n'
                u'; File containing Custom Commands entries\n'
                u';\n'
                u'; Format of a Custom Command entry:\n'
                u';\n'
                u'; Name;Command parameters\n'
                u'; Hint: use %target% variable to represent the position of file target(s) in your commands.\n\n')

    def DoConfig(self):
        dialog = self.gui.ListDialog(self.window, _(u'Set Commands...'), dict(self.data))
        value = dialog.GetValue
        if value or value == {}: self.data = value
        else: return
        self.save_commands()

#------------------------------------------------------------------------------

class ScreensData(DataDict):  # Polemos: added png support
    def __init__(self):
        """Initialize."""
        self.dir = dirs['app']
        self.data = {}

    def refresh(self):
        """Refresh list of screenshots."""
        self.dir = dirs['app']
        ssBase = GPath(mwIniFile.getSetting('General','Screen Shot Base Name','ScreenShot'))
        if ssBase.head:
            self.dir = self.dir.join(ssBase.head)
        newData = {}
        reImageExt = re.compile(r'\.(bmp|jpg|png)$',re.I)
        #--Loop over files in directory
        for fileName in self.dir.list():
            filePath = self.dir.join(fileName)
            maImageExt = reImageExt.search(fileName.s)
            if maImageExt and filePath.isfile():
                newData[fileName] = (maImageExt.group(1).lower(),filePath.mtime,os.path.getsize(filePath._s)) # Polemos: Added size attr.
        changed = (self.data != newData)
        self.data = newData
        return changed

    def delete(self,fileName):
        """Deletes member file."""
        filePath = self.dir.join(fileName)
        filePath.remove()
        del self.data[fileName]

#------------------------------------------------------------------------------

class datamod_order:   # Polemos: OpenMW/TES3mp support
    """Create Datamods entries for OpenMW."""

    def __init__(self):
        """Initialize."""
        self.encod = settings['profile.encoding']
        self.mwfiles = settings['openmw.datafiles'] if os.path.isdir(settings['openmw.datafiles']) else None
        self.conf_file = settings['openmwprofile']
        self.mods = os.path.join(MashDir, 'Profiles', settings['profile.active'], 'mods.dat')
        self.modsorder_path = os.path.join(MashDir, 'Profiles', settings['profile.active'], 'modsorder.dat')
        self.order = []
        self.datafiles = []
        self.SetModOrder()

    def moveTo(self, mods):
        """Changes selected mod(s) order."""
        self.order = mods[:]
        self.create(self.mods, '\r\n'.join((x for x in self.order)))
        self.RefreshProfile()

    def mopydir(self):
        """Check or create Mashdir."""
        self.mashdir = settings['mashdir']
        if not os.path.isdir(self.mashdir):
            os.makedirs(self.mashdir)
            exists = False
        else: exists = True
        return exists

    def metainfo(self, mod):
        """Get data from mashmeta.inf file in mod directory."""
        data = {u'Installer':'',
                  u'Version':'',
                  u'NoUpdateVer':'',
                  u'NewVersion':'',
                  u'Category':'',
                  u'Repo':'',
                  u'ID':''}
        reList = re.compile(u'(Installer|Version|NoUpdateVer|NewVersion|Category|Repo|ID)=(.+)')
        # Special ModData
        if mod == self.mwfiles:
            data[u'Category'] = u'Main Files'
            metadata = data
        elif mod == self.mashdir:
            data[u'Category'] = u'Mash Files'
            metadata = data
        else: metadata = self.metaget(mod)[:]
        # Main
        for x in metadata:
            x = x.rstrip()
            maList = reList.match(x)
            if maList:
                key, value = maList.groups()
                if key == u'Installer': data[key] = value
                elif key == u'Version': data[key] = value
                elif key == u'NoUpdateVer': data[key] = value
                elif key == u'NewVersion': data[key] = value
                elif key == u'Category': data[key] = value
                elif key == u'Repo': data[key] = value
                elif key == u'ID': data[key] = value
        return data

    def metatext(self): # Todo: add dialog for setting repos, url, etc ...
        """Default content for mashmeta.inf (mod dir)."""
        metatext = (u'[General]',
                    u'Installer=',
                    u'Version=',
                    u'NoUpdateVer=',
                    u'NewVersion=',
                    u'Category=',
                    u'Repo=',
                    u'ID=')
        return '\r\n'.join(metatext)

    def metaget(self, mod):
        """Check if mashmeta.inf exist and create it if does not."""
        metafile = os.path.join(mod, 'mashmeta.inf')
        if not os.path.isfile(metafile): self.create(metafile, self.metatext())
        return self.read(metafile)

    def RefreshProfile(self):
        """Get Data from user profile."""
        self.ProfileDataMods = [x.rstrip() for x in self.read(self.mods) if os.path.isdir(x.rstrip())]
        if not self.check_mods_data(): self.SetModOrder()

    def check_mods_data(self):
        """Checks for problems in mods.dat file."""
        return len(set(self.order)) == len(self.order)

    def mod_order(self):
        """Establish a New Mod Order Government (o)."""
        isdir = os.path.isdir
        if os.path.isfile(self.mods):
            self.order = [x.rstrip() for x in self.read(self.mods) if isdir(x.rstrip())]
            if not self.check_mods_data(): self.order = []
            self.order.extend([x for x in self.datamods()[:] if x not in self.order])
            if all([self.mwfiles is not None, self.mwfiles not in self.order]): self.order.insert(0, self.mwfiles)
        self.create(self.mods, '\r\n'.join((x for x in self.order)))

    def SetModOrder(self):
        """Init User Profile Data."""
        self.mod_order()
        self.RefreshProfile()

    def modflags(self, Version, NoUpdateVer, NewVersion, mod):
        """Assign mod flags."""
        flags = []
        moddir = settings['datamods']
        if Version != NewVersion and NoUpdateVer != NewVersion: flags.append('(U)')
        if mod not in self.inmods: flags.append('!')
        if '!' in flags:  # Keep this.
            if moddir in mod:
                flags.remove('!')
        return flags if flags != [] else ''

    def get_mod_data(self):
        """Final mod data assembly and delivery."""
        self.RefreshProfile()
        result = {}
        basename = os.path.basename
        normpath = os.path.normpath
        chkActive = MWIniFile(self.conf_file).checkActiveState
        for num, mod in enumerate(self.ProfileDataMods):
            meta = self.metainfo(mod)
            Name = basename(normpath(mod))
            active_state = chkActive(mod)
            Version = meta[u'Version']
            NoUpdateVer = meta[u'NoUpdateVer']
            NewVersion = meta[u'NewVersion']
            flags = self.modflags(Version, NoUpdateVer, NewVersion, mod)
            Category = meta[u'Category']
            Inmods = True if mod in self.inmods else False
            data = [Name, num, flags, Version, Category, active_state, mod, Inmods]
            result[mod] = data
        return result

    def datamods(self):
        """Create Datamods data from openmw.cfg and Datamods dir."""
        # Init stuff
        isdir = os.path.isdir
        join = os.path.join
        # Openmw.cfg parsing
        self.datafiles = MWIniFile(settings['openmwprofile']).openmw_data_files()[:]
        datafiles = self.datafiles[:]
        # DataMods dir parsing
        moddir = settings['datamods']
        datamods = [join(moddir, dir) for dir in scandir.listdir(moddir)]
        # DataMods final list
        datafiles.extend((x for x in datamods if all([isdir(x), x not in datafiles])))
        if not self.mopydir(): datafiles.append(self.mashdir)
        # Mods in DataMods Modified List
        self.inmods = datamods[:]
        self.inmods.append(self.mashdir)
        if self.mwfiles is not None: self.inmods.append(self.mwfiles)
        return datafiles

    def create(self, file, text=u''):
        """Create a file and save text."""
        with io.open(file, 'w', encoding=self.encod) as f:
            f.write(text)

    def read(self, file):
        """Read file contents from a file in a chosen dir."""
        with io.open(file, 'r', encoding=self.encod) as f:
            return f.readlines()

#------------------------------------------------------------------------------

class DataModsInfo(DataDict, datamod_order):  # Polemos: OpenMW/TES3mp support
    """Returns a mods information."""
    data = {}
    def __init__(self):
        """Initialize."""
        datamod_order.__init__(self)

    def refresh(self):
        """Refresh list of Mods Directories."""
        newData = self.get_mod_data()
        changed = (self.data != newData)

        if settings['openmw'] and changed: self.data = {}

        # This is magic. Don't play with the dark arts. #
        for key, value in newData.iteritems():          #
            self.data[key] = value                      #
        return changed

#------------------------------------------------------------------------------

class BSA_order:  # Polemos
    """Create BSA entries."""

    def __init__(self):
        self.openmw = settings['openmw']
        self.conf = self.get_conf_dir()
        self.dir = self.bsa_dir()

    def get_conf_dir(self):
        if not self.openmw: return dirs['app'].s  # Morrowind
        if self.openmw: return settings['openmwprofile']  # OpenMW

    def bsa_dir(self):
        """Set the Data Files dir."""
        if not self.openmw: return dirs['mods'].s  # Morrowind
        if self.openmw: return MWIniFile(self.conf).openmw_data_files()  # OpenMW

    def bsa_files(self):
        """Return a list of bsa files."""
        if not self.openmw:
            bsas = [os.path.join(self.dir, bsafile) for bsafile in scandir.listdir(self.dir) if bsafile.endswith('.bsa')]
        if self.openmw:
            bsas = []
            bsadir = self.bsa_dir()[:]
            # The comprehension below is faster (timed) than the loop it is based on,
            # even though we are using append() inside the comprehension (which defeats
            # the purpose)... Be my guest and change it.
            [[bsas.append(os.path.join(moddir, bsafile)) for bsafile in scandir.listdir(moddir)
                    if bsafile.lower().endswith('.bsa')] for moddir in bsadir if os.path.exists(moddir)]
        return bsas

    def bsa_active(self):
        """Check which mods are active from conf files."""
        active = MWIniFile.get_active_bsa(MWIniFile(self.conf))
        return active

    def bsa_size(self, bsa):
        """Get file size, return empty if file is inaccessible."""
        try: return os.path.getsize(bsa)/1024
        except: return ''

    def bsa_date(self, bsa):
        """Get file date, return empty if file is inaccessible."""
        try: return os.path.getmtime(bsa)
        except: return ''

    def get_bsa_data(self):
        """Final bsa info assembly and delivery."""
        bsa_files = self.bsa_files()[:]
        active = self.bsa_active()[:]
        result = {}
        for bsa_Path in bsa_files:
            Name = os.path.basename(bsa_Path)
            Active = True if Name in active else False
            Size = self.bsa_size(bsa_Path)
            Date = self.bsa_date(bsa_Path)
            entry = [Name, bsa_Path, Active, Size, Date]
            result[Name] = entry
        return result

#------------------------------------------------------------------------------

class BSAdata(DataDict, BSA_order):  # Polemos
    """BSAdata factory."""
    data = {}

    def __init__(self):
        """Initialize."""
        BSA_order.__init__(self)
        self.refresh()

    def refresh(self):
        """Refresh list of BSAs."""
        newData = self.get_bsa_data()
        changed = (self.data != newData)

        if settings['openmw'] and changed: self.data = {}

        # This is magic. Don't play with the dark arts. #
        for key, value in newData.iteritems():          #
            self.data[key] = value                      #
        return changed

#------------------------------------------------------------------------------

class Packages_Factory:  # Polemos
    """Create Package entries."""

    def __init__(self):
        self.dir = settings['downloads']

    def package_files(self):
        """Return a list of package files."""
        packages = [os.path.join(self.dir, package) for package in scandir.listdir(self.dir) if package.endswith(('.zip', 'rar', '7z'))]
        return packages

    def package_installed(self, package):  # Polemos, todo: maybe implement...
        """Check which packages are installed from metafiles."""
        return False #os.path.isfile('%s.meta' % package)

    def package_size(self, file):
        """Get file size, return empty if file is inaccessible."""
        try: return os.path.getsize(file)
        except: return ''

    def get_package_data(self):
        """Final package info assembly and delivery."""
        package_files = self.package_files()[:]
        result = {}
        for package in package_files:
            Name = os.path.basename(package)
            Installed = True if self.package_installed(package) else False
            Size = self.package_size(package)
            entry = [Name, package, Installed, Size]
            result[Name] = entry
        return result

#------------------------------------------------------------------------------

class PackagesData(DataDict, Packages_Factory):  # Polemos
    """PackageData factory."""
    data = {}

    def __init__(self):
        """Initialize."""
        Packages_Factory.__init__(self)
        self.refresh()

    def refresh(self):
        """Refresh list of BSAs."""
        newData = self.get_package_data()
        changed = (self.data != newData)

        if changed: self.data = {}

        # This is magic. Don't play with the dark arts. #
        for key, value in newData.iteritems():          #
            self.data[key] = value                      #
        return changed

# -----------------------------------------------------------------------------

class GetBckList:  # Polemos
    """Formulate backup files list."""
    bckList = []

    def __init__(self, fname=False):
        """Init."""
        self.bckList = []
        self.max = settings['backup.slots']
        self.snapdir = os.path.join(MashDir, 'snapshots')
        self.bckfiles = [os.path.join(self.snapdir, '%s%s.txt' % (fname, x)) for x in range(self.max)]
        self.listFactory()

    def dtFactory(self, DateTime):
        """Date/Time Factory."""
        return time.strftime('%m/%d/%Y - %H:%M:%S', time.localtime(DateTime))

    def listFactory(self):
        """List Factory."""
        for num, bckfile in enumerate(self.bckfiles):
            if os.path.isfile(bckfile):
                timestamp = os.path.getmtime(bckfile)
                self.bckList.append(_(u'%s. Backup dated: %s' % (num, self.dtFactory(timestamp))))

# -----------------------------------------------------------------------------

class LoadModOrder:  # Polemos
    """Restore Datamods order and status."""
    modData = []

    def __init__(self, num, fname):
        """Init."""
        self.mode = fname
        self.encod = settings['profile.encoding']
        bckfile = os.path.join(MashDir, 'snapshots', '%s%s.txt' % (fname, num))
        self.parseBck(bckfile)

    def dataFactory(self, rawData):
        """Restore data from container."""
        if self.mode == 'modsnap':
            self.modData = [x.rstrip().split('"') for x in rawData]
            for num, x in enumerate(self.modData):
                self.modData[num][0] = True if self.modData[num][0] == u'True' else False
        elif self.mode == 'datasnap':
            self.modData = [line.rstrip() for line in rawData]
            self.modData = filter(None, self.modData)  # Polemos: This may have problems in Python 3
        elif self.mode == 'paksnap':
            self.modData = [(int(x[0]), GPath(x[1].replace('"', '')), int(x[2])) for x in [y.split(':') for y in rawData]]

    def parseBck(self, bckFile):
        """Save backup file."""
        with io.open(bckFile, 'r', encoding=self.encod) as bck:
            self.dataFactory(bck.readlines())

# -----------------------------------------------------------------------------

class SaveModOrder:  # Polemos
    """Backup of items order and status."""
    status = False

    def __init__(self, modData, mode, fname):
        """Init."""
        self.encod = settings['profile.encoding']
        self.mode = mode
        self.modData = modData
        self.max = settings['backup.slots']
        self.snapdir = os.path.join(MashDir, 'snapshots')
        self.bckfiles = [os.path.join(self.snapdir, '%s%s.txt' % (fname, x)) for x in range(self.max)]
        if not os.path.isdir(self.snapdir):
            try: os.makedirs(self.snapdir)
            except IOError: return  # todo: add access denied error
            except: return
        self.initbck()

    def initbck(self):
        """Init backup actions."""
        # If only one slot
        if self.max == 1:
            self.saveBck(self.bckfiles[0])
            return
        # Save to first available slot
        for bckFile in self.bckfiles:
            if not os.path.isfile(bckFile):
                self.saveBck(bckFile)
                return
        # If all slots are filled, rotate
        os.remove(self.bckfiles[(self.max-1)])
        ids = range(self.max)
        ids.reverse()
        for item in ids:
            if item-1 == -1: break
            os.rename(self.bckfiles[item-1], self.bckfiles[item])
        try: self.saveBck(self.bckfiles[0])
        except IOError: return  # todo: add access denied error

    def saveBck(self, bckFile):
        """Save backup file."""
        with io.open(bckFile, 'w', encoding=self.encod) as bck:
            if self.mode == 'mods':
                for x in ['%s"%s\n' % (x[5], x[6]) for x in self.modData]: bck.write(x)
            elif self.mode == 'plugins':
                try: bck.write(self.modData.decode(self.encod))
                except: pass  # todo: add fail error
            elif self.mode == 'installers':
                for x in self.modData:
                    try: bck.write('%s:"%s":%s\n' % (x[0], x[1], x[2]))
                    except: pass  # todo: add fail error
        self.status = True

# -----------------------------------------------------------------------------

class CopyTree:  # Polemos
    """File tree copy (generic)."""
    accessErr = False

    def __init__(self, parent, source_dir, target_dir):
        """Init."""
        self.parent = parent
        self.source_dir = source_dir
        self.target_dir = target_dir
        if self.chkTarg(): return
        self.filesLen = self.cntItms()
        self.title = u'Overwriting...' if os.path.isdir(self.target_dir) else u'Copying...'
        self.copyAct()

    def chkTarg(self):
        """Check if copying to itself."""
        result = self.source_dir == self.target_dir
        if result:
            import gui.dialog as gui
            gui.ErrorMessage(self.parent, _(u'Operation aborted: Thou shall not copy a directory unto itself...'))
        return result

    def copyAct(self):
        """Thread Copy Tree."""
        import wx
        import gui.dialog as gui
        self.dialog = gui.GaugeDialog(self.parent, self.target_dir, self.title, self.filesLen)
        self.dialog.Show()
        thrTreeOp = Thread(target=self.treeOp)
        thrTreeOp.start()
        with wx.WindowDisabler():
            while thrTreeOp.isAlive(): wx.GetApp().Yield()
        if self.accessErr: gui.ErrorMessage(self.parent, _(u'Operation failed: Access denied. Unable to write on the destination.'))

    def cntItms(self):
        """Count directory contents for progress status."""
        itms = 0
        for root, dirsn, files in os.walk(self.source_dir):
            itms += len(files)  # We will use only the len of files for the progress status
        return itms

    def treeOp(self):  # Polemos: This is a very fast implementation. Todo: post it on stackoverflow?
        """Filetree operations."""
        source_dir = self.source_dir
        target_dir = self.target_dir
        if not os.path.isdir(self.target_dir): os.makedirs(self.target_dir)
        # Commence
        try:
            cnt = 0
            for root, dirsn, files in scandir.walk(source_dir, topdown=False):
                for status, fname in enumerate(files, 1):
                    if self.filesLen < 41: self.dialog.update(status)
                    else:
                        cnt += 1
                        if cnt >= 10:
                            self.dialog.update(status)
                            cnt = 0
                    relsource = os.path.relpath(root, source_dir)
                    if relsource == '.': relsource = ''
                    source = os.path.join(root, fname)
                    target = os.path.join(target_dir, relsource, fname)
                    target_file_dir = os.path.join(target_dir, relsource)
                    if not os.path.isdir(target_file_dir): os.makedirs(target_file_dir)
                    buffer = min(10485760, os.path.getsize(source))
                    if buffer == 0: buffer = 1024
                    with open(source, 'rb') as fsource:
                        with open(target, 'wb') as fdest:
                            shutil.copyfileobj(fsource, fdest, buffer)
        except IOError: self.accessErr = True
        finally:
            self.dialog.update(self.filesLen)
            self.dialog.set_msg(_(u'Finished...'))
            time.sleep(2)  # Give some time for system file caching.
            self.dialog.Destroy()


class ResetTempDir:  # Polemos
    """Reset/clear Mash Temp dir."""
    try: tempdir = (os.path.join(MashDir, 'Temp'))
    except: tempdir = os.path.join(MashDir, u'Temp')
    status = True

    def __init__(self, window):
        """Init."""
        import gui.dialog
        wait = gui.dialog.WaitDialog(window, _(u'Please wait, cleaning temp folder...'))
        if os.path.isdir(self.tempdir):
            if not self.safe(self.tempdir):  # Polemos: todo: Add GUI to inform user.
                self.status = False
                return
            bolt.RemoveTree(self.tempdir)
        self.RecreateTempdir()
        wait.exit()

    def safe(self, tempdir):
        """Ensure Temp is Mash Temp."""
        if tempdir == os.path.abspath(os.sep): return False
        if [x for x in scandir.listdir(tempdir) if x in ['7z.exe', 'mash.exe', 'mash.py']]: return False
        return True

    def RecreateTempdir(self):
        """Recreate tempdir."""
        try:
            if not os.path.isdir(self.tempdir):
                os.mkdir(self.tempdir)
        except: pass

# Installers ------------------------------------------------------------------

class Installer(object):  # Polemos: added MWSE compatibility, optimised, bug fixing, restored lost Bain func on many packages.
    """Object representing an installer archive, its user configuration, and its installation state."""
    #--Member data
    persistent = ('archive', 'order', 'group', 'modified', 'size', 'crc', 'fileSizeCrcs', 'type', 'isActive',
                  'subNames', 'subActives', 'dirty_sizeCrc', 'comments', 'readMe', 'packageDoc', 'packagePic',
                  'src_sizeCrcDate', 'hasExtraData', 'skipVoices', 'espmNots')
    volatile = ('data_sizeCrc', 'skipExtFiles', 'skipDirFiles', 'status', 'missingFiles', 'mismatchedFiles',
                'refreshed', 'mismatchedEspms', 'unSize', 'espms', 'underrides')
    __slots__ = persistent+volatile
    #--Package analysis/porting.
    docDirs = {'screenshots', 'docs'}
    dataDirs = {'bookart' , 'fonts', 'icons', 'meshes', 'music', 'shaders', 'sound', 'splash', 'textures',
                'video', 'mash plus', 'mits', 'mwse', 'animation'}
    dataDirsPlus = dataDirs | set()
    dataDirsMinus = {'mash', 'replacers', 'distantland', 'clean'}  #--Will be skipped even if hasExtraData == True.
    reDataFile = re.compile(r'\.(esp|esm|bsa)$',re.I)
    reReadMe = re.compile(r'^([^\\]*)(dontreadme|read[ _]?me|lisez[ _]?moi)([^\\]*)\.(txt|rtf|htm|html|doc|odt)$', re.I)
    skipExts = {'.dll', '.dlx', '.exe', '.py', '.pyc', '.7z', '.zip', '.rar', '.db'}
    docExts = {'.txt', '.rtf', '.htm', '.html', '.doc', '.odt', '.jpg', '.png', '.pdf', '.css', '.xls'}
    #--Temp Files/Dirs
    tempDir = GPath('Temp')
    tempList = GPath('TempList.txt')
    #--Aliases
    off_local = {}

    #--Class Methods ----------------------------------------------------------
    @staticmethod
    def getGhosted():
        """Returns map of real to ghosted files in mods directory."""
        dataDir = dirs['mods']
        ghosts = [x for x in dataDir.list() if x.cs[-6:] == '.ghost']
        return {x.root: x for x in ghosts if not dataDir.join(x).root.exists()}

    @staticmethod
    def clearTemp():
        """Clear temp install directory -- DO NOT SCREW THIS UP!!!"""
        Installer.tempDir.rmtree(safety='Temp')

    @staticmethod
    def sortFiles(files):
        """Utility function. Sorts files by directory, then file name."""
        def sortKey(file):
            dirFile = file.lower().rsplit('\\', 1)
            if len(dirFile) == 1: dirFile.insert(0, '')
            return dirFile
        sortKeys = {x: sortKey(x) for x in files}
        return sorted(files, key=lambda x: sortKeys[x])

    @staticmethod
    def refreshSizeCrcDate(apRoot, old_sizeCrcDate, progress=None, removeEmpties=False, fullRefresh=False):  # Polemos: fixed crc bug, +speed, more.
        """Update old_sizeCrcDate for root directory. This is used both by InstallerProject's and by InstallersData."""
        progress_info = settings['mash.installers.show.progress.info']
        rootIsMods = (apRoot == dirs['mods'])  #--Filtered scanning for mods directory.
        norm_ghost = (rootIsMods and Installer.getGhosted()) or {}
        ghost_norm = {y: x for x, y in norm_ghost.iteritems()}
        rootName = apRoot.stail
        progress = progress or bolt.Progress()
        new_sizeCrcDate = {}
        bethFiles = mush.bethDataFiles
        skipExts = Installer.skipExts
        asRoot = apRoot.s
        relPos = len(apRoot.s)+1
        pending = set()
        #--Scan for changed files
        progress(0, _(u'%s: Pre-Scanning...\n ') % rootName)
        progress.setFull(1)
        dirDirsFiles = []
        emptyDirs = set()
        for asDir, sDirs, sFiles in scandir.walk(asRoot): # Polemos: replaced os.walk which is slow in Python 2.7 and below.
            progress(0.05, _(u'%s: Pre-Scanning:\n%s') % (rootName, asDir[relPos:]))
            if rootIsMods and asDir == asRoot: sDirs[:] = [x for x in sDirs if x.lower() not in Installer.dataDirsMinus]
            dirDirsFiles.append((asDir,sDirs,sFiles))
            if not (sDirs or sFiles): emptyDirs.add(GPath(asDir))
        progress(0, _(u'%s: Scanning...\n ') % rootName)
        progress.setFull(1+len(dirDirsFiles))
        for index, (asDir, sDirs, sFiles) in enumerate(dirDirsFiles):
            progress(index)
            rsDir = asDir[relPos:]
            inModsRoot = rootIsMods and not rsDir
            apDir = GPath(asDir)
            rpDir = GPath(rsDir)
            for sFile in sFiles:
                ext = sFile[sFile.rfind('.'):].lower()
                rpFile = rpDir.join(sFile)
                if inModsRoot:
                    if ext in skipExts: continue
                    if not rsDir and sFile.lower() in bethFiles: continue
                    rpFile = ghost_norm.get(rpFile, rpFile)
                isEspm = not rsDir and (ext == '.esp' or ext == '.esm')
                apFile = apDir.join(sFile)
                size = apFile.size
                date = apFile.mtime
                oSize, oCrc, oDate = old_sizeCrcDate.get(rpFile, (0, 0, 0))
                if size == oSize and (date == oDate or isEspm): new_sizeCrcDate[rpFile] = (oSize, oCrc, oDate)
                else: pending.add(rpFile)
        #--Remove empty dirs?
        if settings['mash.installers.removeEmptyDirs']:
            for dir in emptyDirs:
                try: dir.removedirs()
                except OSError: pass
        #--Force update?
        if fullRefresh: pending |= set(new_sizeCrcDate)
        changed = bool(pending) or (len(new_sizeCrcDate) != len(old_sizeCrcDate))
        #--Update crcs?
        if pending:
            progress(0,_(u'%s: Calculating CRCs...\n ') % rootName)
            progress.setFull(3+len(pending))
            numndex = 0
            for index, rpFile in enumerate(sorted(pending)):  # Polemos: Bugfix and also added some extra info...
                if progress_info:
                    try: string = (_(u'%s: Calculating CRCs...\n%s\nCRC: %s\nSize:  %sKB') %
                            (rootName, unicode(rpFile.s, sys.getfilesystemencoding()), apFile.crc, (apFile.size/1024)))
                    except: string = (_(u'%s: Calculating CRCs...\n%s\nCRC:  %s\nSize:  %sKB') %
                            (rootName, rpFile.s, apFile.crc, (apFile.size/1024)))
                if progress_info: progress(index, string)
                # Polemos: Progress dialogs crawl if they have to show many items continuously. The same seems to
                # also happen on native windows progress dialogs (if you wonder why the "show more" is not ON by
                # default) and it is the main reason, in my opinion, of the extreme slowness in Windows 10 progress
                # dialogs. We mitigate this here by updating the progress dialog by steps of 10 until reaching the
                # final 9 items which are shown by steps of 1.
                elif numndex == 10: progress(index)
                numndex = numndex + 1 if numndex < 10 else 0
                apFile = apRoot.join(norm_ghost.get(rpFile, rpFile))
                crc = apFile.crc
                size = apFile.size
                date = apFile.mtime
                new_sizeCrcDate[rpFile] = (size, crc, date)
        old_sizeCrcDate.clear()
        old_sizeCrcDate.update(new_sizeCrcDate)
        #--Done
        return changed

    #--Initization, etc -------------------------------------------------------
    def initDefault(self):
        """Inits everything to default values."""
        #--Package Only
        self.archive = ''
        self.modified = 0 #--Modified date
        self.size = 0 #--size of archive file
        self.crc = 0 #--crc of archive
        self.type = 0 #--Package type: 0: unset/invalid; 1: simple; 2: complex
        self.fileSizeCrcs = []
        self.subNames = []
        self.src_sizeCrcDate = {} #--For InstallerProject's
        #--Dirty Update
        self.dirty_sizeCrc = {}
        #--Mixed
        self.subActives = []
        #--User Only
        self.skipVoices = False
        self.hasExtraData = False
        self.comments = ''
        self.group = '' #--Default from abstract. Else set by user.
        self.order = -1 #--Set by user/interface.
        self.isActive = False
        self.espmNots = set() #--Lowercase esp/m file names that user has decided not to install.
        #--Volatiles (unpickled values)
        #--Volatiles: directory specific
        self.refreshed = False
        #--Volatile: set by refreshDataSizeCrc
        self.readMe = self.packageDoc = self.packagePic = None
        self.data_sizeCrc = {}
        self.skipExtFiles = set()
        self.skipDirFiles = set()
        self.espms = set()
        self.unSize = 0
        #--Volatile: set by refreshStatus
        self.status = 0
        self.underrides = set()
        self.missingFiles = set()
        self.mismatchedFiles = set()
        self.mismatchedEspms = set()

    def __init__(self,archive):
        """Initialize."""
        self.initDefault()
        self.archive = archive.stail

    def __getstate__(self):
        """Used by pickler to save object state."""
        getter = object.__getattribute__
        return tuple(getter(self,x) for x in self.persistent)

    def __setstate__(self,values):
        """Used by unpickler to recreate object."""
        self.initDefault()
        setter = object.__setattr__
        for value,attr in zip(values, self.persistent):
            setter(self,attr,value)
        if self.dirty_sizeCrc is None:
            self.dirty_sizeCrc = {}  #--Use empty dict instead.
        self.refreshDataSizeCrc()

    def __copy__(self,iClass=None):
        """Create a copy of self -- works for subclasses too (assuming subclasses
        don't add new data members). iClass argument is to support Installers.updateDictFile"""
        iClass = iClass or self.__class__
        clone = iClass(GPath(self.archive))
        copier = copy.copy
        getter = object.__getattribute__
        setter = object.__setattr__
        for attr in Installer.__slots__: setter(clone, attr, copier(getter(self, attr)))
        return clone

    def refreshDataSizeCrc(self):
        """Updates self.data_sizeCr and related variables. Also, returns dest_src map for install operation."""
        if isinstance(self, InstallerArchive): archiveRoot = GPath(self.archive).sroot
        else: archiveRoot = self.archive
        reReadMe = self.reReadMe
        docExts = self.docExts
        docDirs = self.docDirs
        dataDirsPlus = self.dataDirsPlus
        dataDirsMinus = self.dataDirsMinus
        skipExts = self.skipExts
        bethFiles = mush.bethDataFiles
        packageFiles = {'package.txt', 'package.jpg'}
        unSize = 0
        espmNots = self.espmNots
        skipVoices = self.skipVoices
        off_local = self.off_local
        if espmNots and not skipVoices: skipEspmVoices = {x.cs for x in espmNots}
        else: skipEspmVoices = None
        skipDistantLOD = settings['mash.installers.skipDistantLOD']
        hasExtraData = self.hasExtraData
        type = self.type
        if type == 2:
            allSubs = set(self.subNames[1:])
            activeSubs = {x for x, y in zip(self.subNames[1:], self.subActives[1:]) if y}
        #--Init to empty
        self.readMe = self.packageDoc = self.packagePic = None
        for attr in ('skipExtFiles', 'skipDirFiles', 'espms'): object.__getattribute__(self, attr).clear()
        data_sizeCrc = {}
        skipExtFiles = self.skipExtFiles
        skipDirFiles = self.skipDirFiles
        espms = self.espms
        dest_src = {}
        #--Bad archive?
        if type not in (1, 2): return dest_src
        #--Scan over fileSizeCrcs
        for full, size, crc in self.fileSizeCrcs:
            file = full #--Default
            if type == 2: #--Complex archive
                subFile = full.split('\\', 1)
                if len(subFile) == 2:
                    sub, file = subFile
                    if sub not in activeSubs:
                        if sub not in allSubs: skipDirFiles.add(file)
                        continue
            rootPos = file.find('\\')
            extPos = file.rfind('.')
            fileLower = file.lower()
            # Polemos: The rootlower defines dirs in the root of the "selected
            # to be installed". This doesn't necessarily mean the package root.
            rootLower = (rootPos > 0 and fileLower[:rootPos]) or ''
            fileExt = (extPos > 0 and fileLower[extPos:]) or ''
            #--Skip file?
            if (rootLower == 'omod conversion data' or fileLower[-9:] == 'thumbs.db' or fileLower[-11:] == 'desktop.ini'):
                continue #--Silent skip
            elif skipDistantLOD and fileLower[:10] == 'distantlod': continue
            elif skipVoices and fileLower[:11] == 'sound\\voice': continue
            elif file in bethFiles:
                skipDirFiles.add(full)
                continue
            # Polemos: fix for installing "Docs" sub-folders, without breaking bain install packages.
            elif not hasExtraData and rootLower and rootLower not in dataDirsPlus and rootLower not in docDirs:
                skipDirFiles.add(full)
                continue
            elif hasExtraData and rootLower and rootLower in dataDirsMinus:
                skipDirFiles.add(full)
                continue
            elif fileExt in skipExts:
                skipExtFiles.add(full)
                continue
            #--Remap (and/or skip)
            dest = file #--Default. May be remapped below.
            #--Esps
            if not rootLower and reModExt.match(fileExt):
                pFile = pDest = GPath(file)
                if pFile in off_local:
                    pDest = off_local[pFile]
                    dest = pDest.s
                espms.add(pDest)
                if pDest in espmNots: continue
            #--Esp related voices (Oblivion?)
            elif skipEspmVoices and fileLower[:12] == 'sound\\voice\\':
                farPos = file.find('\\', 12)
                if farPos > 12 and fileLower[12:farPos] in skipEspmVoices: continue
            #--Docs
            elif rootLower in docDirs: dest = 'Docs\\'+file[rootPos+1:]
            elif not rootLower:
                maReadMe = reReadMe.match(file)
                if file.lower() == 'masterlist.txt': pass
                elif maReadMe:
                    if not (maReadMe.group(1) or maReadMe.group(3)): dest = 'Docs\\%s%s' % (archiveRoot,fileExt)
                    else: dest = 'Docs\\'+file
                    self.readMe = dest
                elif fileLower == 'package.txt': dest = self.packageDoc = 'Docs\\'+archiveRoot+'.package.txt'
                elif fileLower == 'package.jpg': dest = self.packagePic = 'Docs\\'+archiveRoot+'.package.jpg'
                elif fileExt in docExts: dest = 'Docs\\'+file
            #--Save
            key = GPath(dest)
            data_sizeCrc[key] = (size,crc)
            dest_src[key] = full
            unSize += size
        self.unSize = unSize
        (self.data_sizeCrc,old_sizeCrc) = (data_sizeCrc,self.data_sizeCrc)
        #--Update dirty?
        if self.isActive and data_sizeCrc != old_sizeCrc:
            dirty_sizeCrc = self.dirty_sizeCrc
            for file,sizeCrc in old_sizeCrc.iteritems():
                if file not in dirty_sizeCrc and sizeCrc != data_sizeCrc.get(file):
                    dirty_sizeCrc[file] = sizeCrc
        #--Done (return dest_src for install operation)
        return dest_src

    def refreshSource(self, archive,progress=None,fullRefresh=False):
        """Refreshes fileSizeCrcs, size, date and modified from source archive/directory."""
        raise AbstractError

    def refreshBasic(self, archive, progress=None, fullRefresh=False):
        """Extract file/size/crc info from archive."""
        self.refreshSource(archive, progress, fullRefresh)
        def fscSortKey(fsc):
            dirFile = fsc[0].lower().rsplit('\\', 1)
            if len(dirFile) == 1: dirFile.insert(0, '')
            return dirFile
        fileSizeCrcs = self.fileSizeCrcs
        sortKeys = {x: fscSortKey(x) for x in fileSizeCrcs}
        fileSizeCrcs.sort(key=lambda x: sortKeys[x])
        #--Type, subNames
        reDataFile = self.reDataFile
        dataDirs = self.dataDirs
        type = 0
        subNameSet = set()
        subNameSet.add('')
        for file,size,crc in fileSizeCrcs:
            fileLower = file.lower()
            if type != 1:
                frags = file.split('\\')
                nfrags = len(frags)
                #--Type 1?
                if (nfrags == 1 and reDataFile.search(frags[0]) or nfrags > 1 and frags[0].lower() in dataDirs):
                    type = 1
                    break
                #--Type 2?
                elif nfrags > 2 and frags[1].lower() in dataDirs:
                    subNameSet.add(frags[0])
                    type = 2
                elif nfrags == 2 and reDataFile.search(frags[1]):
                    subNameSet.add(frags[0])
                    type = 2
        self.type = type
        #--SubNames, SubActives
        if type == 2:
            actives = {x for x, y in zip(self.subNames, self.subActives) if (y or x == '')}
            self.subNames = sorted(subNameSet, key=string.lower)
            if len(self.subNames) == 2: #--If only one subinstall, then make it active.
                self.subActives = [True, True]
            else: self.subActives = [(x in actives) for x in self.subNames]
        else:
            self.subNames = []
            self.subActives = []
        #--Data Size Crc
        self.refreshDataSizeCrc()

    def refreshStatus(self,installers):
        """Updates missingFiles, mismatchedFiles and status.
        Status:
        20: installed (green)
        10: mismatches (yellow)
        0: unconfigured (white)
        -10: missing files (red)
        -20: bad type (grey)
        """
        data_sizeCrc = self.data_sizeCrc
        data_sizeCrcDate = installers.data_sizeCrcDate
        abnorm_sizeCrc = installers.abnorm_sizeCrc
        missing = self.missingFiles
        mismatched = self.mismatchedFiles
        misEspmed = self.mismatchedEspms
        underrides = set()
        status = 0
        missing.clear()
        mismatched.clear()
        misEspmed.clear()
        if self.type == 0: status = -20
        elif data_sizeCrc:
            for file,sizeCrc in data_sizeCrc.iteritems():
                sizeCrcDate = data_sizeCrcDate.get(file)
                if not sizeCrcDate: missing.add(file)
                elif sizeCrc != sizeCrcDate[:2]:
                    mismatched.add(file)
                    if not file.shead and reModExt.search(file.s): misEspmed.add(file)
                if sizeCrc == abnorm_sizeCrc.get(file): underrides.add(file)
            if missing: status = -10
            elif misEspmed: status = 10
            elif mismatched: status = 20
            else: status = 30
        #--Clean Dirty
        dirty_sizeCrc = self.dirty_sizeCrc
        for file,sizeCrc in dirty_sizeCrc.items():
            sizeCrcDate = data_sizeCrcDate.get(file)
            if (not sizeCrcDate or sizeCrc != sizeCrcDate[:2] or
                sizeCrc == data_sizeCrc.get(file)):
                del dirty_sizeCrc[file]
        #--Done
        (self.status, oldStatus) = (status, self.status)
        (self.underrides, oldUnderrides) = (underrides, self.underrides)
        return (self.status != oldStatus or self.underrides != oldUnderrides)

    def install(self,archive,destFiles,data_sizeCrcDate,progress=None):
        """Install specified files to Morrowind\Data files directory."""
        raise AbstractError


class InstallerMarker(Installer):
    """Represents a marker installer entry. Currently only used for the '==Last==' marker"""
    __slots__ = tuple()  #--No new slots

    def __init__(self, archive):
        """Initialize."""
        Installer.__init__(self, archive)
        self.modified = time.time()

    def refreshSource(self, archive, progress=None, fullRefresh=False):
        """Refreshes fileSizeCrcs, size, date and modified from source archive/directory."""
        pass

    def install(self, name, destFiles, data_sizeCrcDate, progress=None):
        """Install specified files to Morrowind\Data files directory."""
        pass


class InstallerArchiveError(bolt.BoltError):
    """Installer exception."""
    pass


class InstallerArchive(Installer):
    """Represents an archive installer entry."""
    __slots__ = tuple() #--No new slots

    #--File Operations --------------------------------------------------------
    def refreshSource(self,archive,progress=None,fullRefresh=False):  # Polemos fixes, speed improvements.
        """Refreshes fileSizeCrcs, size, date and modified from source archive/directory."""
        # Basic file info
        self.modified = archive.mtime
        self.size = archive.size
        self.crc = archive.xxh
        # Get fileSizeCrcs
        fileSizeCrcs = self.fileSizeCrcs = []
        reList = re.compile(u'(Path|Folder|Size|CRC) = (.+)')
        file = size = crc = isdir = 0
        command = ur'7z.exe l -slt -sccUTF-8 "%s"' % archive.s
        args = ushlex.split(command)
        ins = Popen(args, bufsize=32768, stdout=PIPE, creationflags=DETACHED_PROCESS)
        memload = [x for x in ins.stdout]
        for line in memload:
            maList = reList.match(line)
            if maList:
                key,value = maList.groups()
                if key == u'Path': file = (value.decode('utf-8')).strip()
                elif key == u'Folder': isdir = (value[0] == '+')
                elif key == u'Size': size = int(value)
                elif key == u'CRC':
                    try:
                        crc = int(value,16)
                        if file and not isdir: fileSizeCrcs.append((file, size, crc))
                    except: pass
                    file = size = crc = isdir = 0
        if not fileSizeCrcs:
            import gui.dialog
            gui.dialog.ErrorMessage(None, _(u'7z module is'
                u' unable to read archive %s.\nTry extracting it and then repacking it before trying again.' % (archive.s)))
            return

    def unpackToTemp(self, archive, fileNames, progress=None):  # Polemos fixes and addons.
        """Erases all files from self.tempDir and then extracts specified files from archive to self.tempDir.Note: fileNames = File names (not paths)."""
        # Not counting the unicode problems, there were some strange bugs here, wonder why. - Polemos
        try: check = fileNames
        except:
            import gui.dialog
            gui.dialog.ErrorMessage(None, _(u'No files to extract for selected archive.'))
            return
        progress = progress or bolt.Progress()
        progress.state,progress.full = 0,len(fileNames)
        #--Dump file list
        try:
            with io.open(self.tempList.s, 'w', encoding='utf-8') as out:
                out.write(u'\n'.join(fileNames))
        except:
            import gui.dialog
            gui.dialog.ErrorMessage(None, _(u'There was a problem installing your package.\nPlease do a "Full Refresh" from the menu and try again.'))
            self.clearTemp()
            return
        self.clearTemp()
        #--Extract files
        apath = dirs['installers'].join(archive)
        command = ur'7z.exe x "%s" -bb -y -o"%s" @%s -scsUTF-8' % (apath.s, self.tempDir.s, self.tempList.s)
        args = ushlex.split(command)
        ins = Popen(args, stdout=PIPE, creationflags=DETACHED_PROCESS)
        reExtracting = re.compile('-\s+(.+)')
        reAllOk = re.compile('Everything is Ok')
        extracted = []
        for line in ins.stdout:
            extract_ok = reAllOk.match(line)
            maExtracting = reExtracting.match(line)
            if extract_ok: result = True
            if maExtracting:
                extracted.append(maExtracting.group(1).strip())
                progress.plus()
        try: check = result  # Polemos: Excepting is fast sometimes.
        except:
            import gui.dialog  # Polemos: In case of errors.
            gui.dialog.ErrorMessage(None,_(u"Errors occurred during extraction and/or Extraction failed."))
        # Ensure that no file is read only:
        for thedir, subdirs, files in scandir.walk(self.tempDir.s):  # Polemos: replaced os.walk which is slow in Python 2.7 and below.
            for f in files:
                path_po = os.path.join(thedir, f)
                try: os.chmod(path_po, stat.S_IWRITE)
                except:  # Polemos: Yeah I know...
                    try: os.system(r'attrib -R "%s" /S' % (path_po))
                    except: pass
        self.tempList.remove()

    def install(self,archive,destFiles,data_sizeCrcDate,progress=None):  # Polemos fixes.
        """Install specified files to Morrowind directory."""
        # Note: Installs "directly" from the archive here.
        progress = progress or bolt.Progress()
        destDir = dirs['mods']
        destFiles = set(destFiles)
        data_sizeCrc = self.data_sizeCrc
        dest_src = {x: y for x, y in self.refreshDataSizeCrc().iteritems() if x in destFiles}
        if not dest_src: return 0
        #--Extract
        progress(0, _(u'%s\nExtracting files...') % archive.s)
        self.unpackToTemp(archive, dest_src.values(), SubProgress(progress, 0, 0.9))
        #--Move
        progress(0.9, _(u'%s\nMoving files...') % archive.s)
        progress.state, progress.full = 0, len(dest_src)
        count = 0
        norm_ghost = Installer.getGhosted()
        tempDir = self.tempDir
        for dest, src in dest_src.iteritems():
            size, crc = data_sizeCrc[dest]
            srcFull = tempDir.join(src)
            destFull = destDir.join(norm_ghost.get(dest, dest))
            if srcFull.exists():
                srcFull.moveTo(destFull)
                data_sizeCrcDate[dest] = (size, crc, destFull.mtime)
                progress.plus()
                count += 1
        self.clearTemp()
        return count

    def unpackToProject(self,archive,project,progress=None):  # Polemos fixes.
        """Unpacks archive to build directory."""
        progress = progress or bolt.Progress()
        files = self.sortFiles([x[0].strip() for x in self.fileSizeCrcs])
        if not files: return 0
        #--Clear Project
        destDir = dirs['installers'].join(project)
        if destDir.exists(): destDir.rmtree(safety='Installers')
        #--Extract
        progress(0,project.s+_(u"\nExtracting files..."))
        self.unpackToTemp(archive, files, SubProgress(progress, 0, 0.9))
        #--Move
        progress(0.9,project.s+_(u"\nMoving files..."))
        progress.state, progress.full = 0, len(files)
        count = 0
        tempDir = self.tempDir
        for file in files:
            srcFull = tempDir.join(file)
            destFull = destDir.join(file)
            if not destDir.exists():
                destDir.makedirs()
            if srcFull.exists():
                srcFull.moveTo(destFull)
                progress.plus()
                count += 1
        self.clearTemp()
        return count


class InstallerProject(Installer):
    """Represents a directory/build installer entry."""
    __slots__ = tuple() #--No new slots

    def removeEmpties(self,name):
        """Removes empty directories from project directory."""
        empties = set()
        projectDir = dirs['installers'].join(name)
        for asDir,sDirs,sFiles in scandir.walk(projectDir.s): # Polemos: replaced os.walk which is slow in Python 2.7 and below.
            if not (sDirs or sFiles): empties.add(GPath(asDir))
        for empty in empties: empty.removedirs()
        projectDir.makedirs() #--In case it just got wiped out.

    def refreshSource(self,archive,progress=None,fullRefresh=False):
        """Refreshes fileSizeCrcs, size, date and modified from source archive/directory."""
        fileSizeCrcs = self.fileSizeCrcs = []
        src_sizeCrcDate = self.src_sizeCrcDate
        apRoot = dirs['installers'].join(archive)
        Installer.refreshSizeCrcDate(apRoot, src_sizeCrcDate, progress, True, fullRefresh)
        cumDate = 0
        cumSize = 0
        for file in [x.s for x in self.src_sizeCrcDate]:
            size,crc,date = src_sizeCrcDate[GPath(file)]
            fileSizeCrcs.append((file,size,crc))
            cumSize += size
            cumDate = max(cumDate,date)
        self.size = cumSize
        self.modified = cumDate
        self.crc = 0
        self.refreshed = True

    def install(self, name, destFiles, data_sizeCrcDate, progress=None):
        """Install specified files to Morrowind Data directory."""
        # Note: Installs from the "extracted archive" here.
        destDir = dirs['mods']
        destFiles = set(destFiles)
        data_sizeCrc = self.data_sizeCrc
        dest_src = {x: y for x, y in self.refreshDataSizeCrc().iteritems() if x in destFiles}
        if not dest_src: return 0
        #--Copy Files
        count = 0
        norm_ghost = Installer.getGhosted()
        srcDir = dirs['installers'].join(name)
        progress.state, progress.full = 0, len(dest_src)
        for dest,src in dest_src.iteritems():
            size,crc = data_sizeCrc[dest]
            srcFull = srcDir.join(src)
            destFull = destDir.join(norm_ghost.get(dest, dest))
            if srcFull.exists():
                srcFull.copyTo(destFull)
                data_sizeCrcDate[dest] = (size, crc, destFull.mtime)
                progress.plus()
                count += 1
        return count

    def syncToData(self,package,projFiles):
        """Copies specified projFiles from Morrowind\Data files to project directory."""
        srcDir = dirs['mods']
        projFiles = set(projFiles)
        srcProj = tuple((x,y) for x, y in self.refreshDataSizeCrc().iteritems() if x in projFiles)
        if not srcProj: return (0, 0)
        #--Sync Files
        updated = removed = 0
        norm_ghost = Installer.getGhosted()
        projDir = dirs['installers'].join(package)
        for src,proj in srcProj:
            srcFull = srcDir.join(norm_ghost.get(src, src))
            projFull = projDir.join(proj)
            if not srcFull.exists():
                projFull.remove()
                removed += 1
            else:
                srcFull.copyTo(projFull)
                updated += 1
        self.removeEmpties(package)
        return (updated, removed)


class InstallersData(bolt.TankData, DataDict):  # Polemos fixes
    """Installers tank data. This is the data source for."""
    status_color = {-20: 'grey', -10: 'red', 0: 'white', 10: 'orange', 20: 'yellow', 30: 'green'}
    type_textKey = {1: 'BLACK', 2: 'NAVY'}

    def __init__(self):
        """Initialize."""
        self.openmw = settings['openmw']
        self.dir = dirs['installers']
        self.bashDir = self.dir.join('Bash')
        #--Tank Stuff
        bolt.TankData.__init__(self, settings)
        self.tankKey = 'mash.installers'
        self.tankColumns = settings['mash.installers.cols']
        self.title = _(u'Installers')
        #--Default Params
        self.defaultParam('columns', self.tankColumns)
        self.defaultParam('colWidths', settings['mash.installers.colWidths'])
        self.defaultParam('colAligns', settings['mash.installers.colAligns'])
        self.defaultParam('colSort', settings['mash.installers.sort'])
        #--Persistent data
        self.dictFile = PickleDict(self.bashDir.join('Installers.dat'))
        self.data = {}
        self.data_sizeCrcDate = {}
        #--Volatile
        self.abnorm_sizeCrc = {} #--Normative sizeCrc, according to order of active packages
        self.hasChanged = False
        self.loaded = False
        self.lastKey = GPath('==Last==')
        self.renamedSizeDate = (0, 0)

    def addMarker(self, name):
        path = GPath(name)
        self.data[path] = InstallerMarker(path)

    def setChanged(self, hasChanged=True):
        """Mark as having changed."""
        self.hasChanged = hasChanged

    def refresh(self,progress=None, what='DIONS', fullRefresh=False):  # D.C.-G. Modified to avoid system error if installers path is not reachable.
        """Refresh info."""
        if not os.access(dirs['installers'].s, os.W_OK): return "noDir"
        progress = progress or bolt.Progress()
        #--MakeDirs
        self.bashDir.makedirs()
        #--Refresh Data
        changed = False
        self.refreshRenamed()
        if not self.loaded:
            progress(0,_(u'Loading Data...\n'))
            self.dictFile.load()
            data = self.dictFile.data
            self.data = data.get('installers', {})
            self.data_sizeCrcDate = data.get('sizeCrcDate', {})
            self.updateDictFile()
            self.loaded = True
            changed = True
        #--Last marker
        if self.lastKey not in self.data:
            self.data[self.lastKey] = InstallerMarker(self.lastKey)
        #--Refresh Other
        if 'D' in what:
            changed |= Installer.refreshSizeCrcDate(
                dirs['mods'], self.data_sizeCrcDate, progress,
                settings['mash.installers.removeEmptyDirs'], fullRefresh)
        if 'I' in what: changed |= self.refreshRenamed()
        if 'I' in what: changed |= self.refreshInstallers(progress,fullRefresh)
        if 'O' in what or changed: changed |= self.refreshOrder()
        if 'N' in what or changed: changed |= self.refreshNorm()
        if 'S' in what or changed: changed |= self.refreshStatus()
        #--Done
        if changed: self.hasChanged = True
        return changed

    def updateDictFile(self):
        """Updates self.data to use new classes."""
        if self.dictFile.vdata.get('version',0): return
        #--Update to version 1
        for name in self.data.keys():
            installer = self.data[name]
            if isinstance(installer, Installer):
                self.data[name] = installer.__copy__(InstallerArchive)
        self.dictFile.vdata['version'] = 1

    def save(self):
        """Saves to pickle file."""
        if self.hasChanged:
            self.dictFile.data['installers'] = self.data
            self.dictFile.data['sizeCrcDate'] = self.data_sizeCrcDate
            self.dictFile.save()
            self.hasChanged = False

    def saveCfgFile(self):  #-# D.C.-G.,  Polemos: fixes, change mash.ini into an override.
        """Save the installers path to mash.ini."""
        mashini_loc = os.path.join(MashDir, 'mash.ini')
        if not os.path.exists(mashini_loc) or self.openmw: return
        import ConfigParser
        mash_ini = False
        if GPath('mash.ini').exists():
            mashIni = ConfigParser.ConfigParser()
            try:
                with io.open('mash.ini', 'r', encoding='utf-8') as f: mashIni.readfp(f)
                mash_ini = True
                instPath = GPath(mashIni.get('General', 'sInstallersDir').strip()).s
            except:
                mash_ini = False
                instPath = ""
        else: instPath = ""
        if instPath != dirs["installers"].s:
            if not mash_ini:
                if os.path.exists(os.path.join(MashDir, "mash_default.ini")):
                    with io.open('mash_default.ini', 'r', encoding='utf-8') as f: d = f.read()
                else: d = "[General]\n"
                with io.open('mash.ini', 'w', encoding='utf-8') as f: f.write(d)
                mashIni = ConfigParser.ConfigParser()
                try:
                    with io.open('mash.ini', 'r', encoding='utf-8') as f: mashIni.readfp(f)
                except: pass
            mashIni.set("General", "sInstallersDir", os.path.abspath(dirs["installers"].s))
            installers_po = u"[General]\nsInstallersDir=%s" % (str(GPath(mashIni.get('General', 'sInstallersDir').strip())
                                ).replace("bolt.Path(u'", '').replace("')", '')).decode('unicode_escape')
            with io.open('mash.ini', 'wb+', encoding='utf-8') as f: f.write(installers_po)

    def getSorted(self,column,reverse):
        """Returns items sorted according to column and reverse."""
        data = self.data
        items = data.keys()
        if column == 'Package': items.sort(reverse=reverse)
        elif column == 'Files': items.sort(key=lambda x: len(data[x].fileSizeCrcs),reverse=reverse)
        else:
            items.sort()
            attr = column.lower()
            if column in ('Package', 'Group'):
                getter = lambda x: object.__getattribute__(data[x],attr).lower()
                items.sort(key=getter,reverse=reverse)
            else:
                getter = lambda x: object.__getattribute__(data[x],attr)
                items.sort(key=getter,reverse=reverse)
        settings['mash.installers.sort'] = column
        #--Special sorters
        if settings['mash.installers.sortStructure']: items.sort(key=lambda x: data[x].type)
        if settings['mash.installers.sortActive']: items.sort(key=lambda x: not data[x].isActive)
        if settings['mash.installers.sortProjects']: items.sort(key=lambda x: not isinstance(data[x], InstallerProject))
        return items

    def getColumns(self, item=None): #--Item Info
        """Returns text labels for item or for row header if item is None."""
        columns = self.getParam('columns')
        if item is None: return columns[:]
        labels, installer = [],self.data[item]
        for column in columns:
            if column == 'Package': labels.append(item.s)
            elif column == 'Files': labels.append(formatInteger(len(installer.fileSizeCrcs)))
            else:
                value = object.__getattribute__(installer, column.lower())
                if column in ('Package', 'Group'): pass
                elif column == 'Order': value = `value`
                elif column == 'Modified': value = formatDate(value)
                elif column == 'Size':
                    try: value = megethos(value)
                    except: value = '%sKB' % formatInteger(value/1024)
                else: raise ArgumentError(column)
                labels.append(value)
        return labels

    def getGuiKeys(self,item):
        """Returns keys for icon and text and background colors."""
        installer = self.data[item]
        #--Text
        if installer.type == 2 and len(installer.subNames) == 2: textKey = self.type_textKey[1]
        else: textKey = self.type_textKey.get(installer.type,'GREY')
        #--Background
        backKey = (installer.skipDirFiles and 'mash.installers.skipped') or None
        if installer.dirty_sizeCrc: backKey = 'bash.installers.dirty'
        elif installer.underrides: backKey = 'mash.installers.outOfOrder'
        #--Icon
        iconKey = ('off','on')[installer.isActive]+'.'+self.status_color[installer.status]
        if installer.type < 0: iconKey = 'corrupt'
        elif isinstance(installer, InstallerProject): iconKey += '.dir'
        return (iconKey,textKey,backKey)

    def getName(self,item):
        """Returns a string name of item for use in dialogs, etc."""
        return item.s

    def getColumn(self,item,column):
        """Returns item data as a dictionary."""
        raise UncodedError

    def setColumn(self,item,column,value):
        """Sets item values from a dictionary."""
        raise UncodedError

    #--Dict Functions -----------------------------------------------------------
    def __delitem__(self,item):
        """Delete an installer. Delete entry AND archive file itself."""
        if item == self.lastKey: return
        installer = self.data[item]
        apath = self.dir.join(item)
        if isinstance(installer, InstallerProject):
            apath.rmtree(safety='Installers')
        else: apath.remove()
        del self.data[item]

    def copy(self,item,destName,destDir=None):
        """Copies archive to new location."""
        if item == self.lastKey: return
        destDir = destDir or self.dir
        apath = self.dir.join(item)
        apath.copyTo(destDir.join(destName))
        if destDir == self.dir:
            self.data[destName] = installer = copy.copy(self.data[item])
            installer.isActive = False
            self.refreshOrder()
            self.moveArchives([destName],self.data[item].order+1)

    def rename(self, item, destName, destDir=None):  # Polemos
        """Rename archive/folder."""
        if item == self.lastKey: return
        destDir = destDir or self.dir
        apath = self.dir.join(item)
        if not apath.renameTo(destDir.join(destName)): return False
        if destDir == self.dir:
            self.data[destName] = installer = copy.copy(self.data[item])
            installer.isActive = False
            self.refreshOrder()
            self.moveArchives([destName],self.data[item].order)
            del self.data[item]
            return True

    #--Refresh Functions --------------------------------------------------------
    def refreshRenamed(self):
        """Refreshes Installer.off_local from corresponding csv file."""
        changed = False
        pRenamed = dirs['mods'].join('Mash', 'Official_Local.csv')
        if not pRenamed.exists():
            changed = bool(Installer.off_local)
            self.renamedSizeDate = (0,0)
            Installer.off_local.clear()
        elif self.renamedSizeDate != (pRenamed.size,pRenamed.mtime):
            self.renamedSizeDate = (pRenamed.size,pRenamed.mtime)
            off_local = {}
            reader = bolt.CsvReader(pRenamed)
            for fields in reader:
                if len(fields) < 2 or not fields[0] or not fields[1]: continue
                off,local = map(string.strip,fields[:2])
                if not reModExt.search(off) or not reModExt.search(local): continue
                off,local = map(GPath,(off,local))
                if off != local: off_local[off] = local
            reader.close()
            changed = (off_local != Installer.off_local)
            Installer.off_local = off_local
        #--Refresh Installer mappings
        if changed:
            for installer in self.data.itervalues():
                installer.refreshDataSizeCrc()
        #--Done
        return changed

    def refreshInstallers(self,progress=None,fullRefresh=False):
        """Refresh installer data."""
        progress = progress or bolt.Progress()
        changed = False
        pending = set()
        projects = set()
        #--Current archives
        newData = {}
        if not self.openmw:  # Polemos: Regular Morrowind support
            for i in self.data.keys():
                if isinstance(self.data[i], InstallerMarker):
                    newData[i] = self.data[i]
        for archive in dirs['installers'].list():
            apath = dirs['installers'].join(archive)
            isdir = apath.isdir()
            if isdir: projects.add(archive)
            if (isdir and archive != 'Bash') or archive.cext in ('.7z','.zip','.rar'):
                installer = self.data.get(archive)
                if not installer:
                    pending.add(archive)
                elif (isdir and not installer.refreshed) or (
                    (installer.size,installer.modified) != (apath.size,apath.mtime)):
                    newData[archive] = installer
                    pending.add(archive)
                else: newData[archive] = installer
        if fullRefresh: pending |= set(newData)
        changed = bool(pending) or (len(newData) != len(self.data))
        if not self.openmw:  # Polemos: Regular Morrowind support
            #--New/update crcs?
            for subPending,iClass in zip((pending - projects, pending & projects), (InstallerArchive, InstallerProject)):
                if not subPending: continue
                progress(0,_(u"Scanning Packages..."))
                progress.setFull(len(subPending))
                for index,package in enumerate(sorted(subPending)):
                    progress(index,_(u"Scanning Packages...\n %s" % package.s))
                    installer = newData.get(package)
                    if not installer: installer = newData.setdefault(package,iClass(package))
                    apath = dirs['installers'].join(package)
                    try: installer.refreshBasic(apath,SubProgress(progress,index,index+1))
                    except InstallerArchiveError: installer.type = -1
        self.data = newData
        return changed

    def refreshRenamedNeeded(self):
        pRenamed = dirs['mods'].join('Mash','Official_Local.csv')
        if not pRenamed.exists(): return bool(Installer.off_local)
        else: return (self.renamedSizeDate != (pRenamed.size,pRenamed.mtime))

    def refreshInstallersNeeded(self):
        """Returns true if refreshInstallers is necessary. (Point is to skip use
        of progress dialog when possible."""
        for archive in dirs['installers'].list():
            apath = dirs['installers'].join(archive)
            if not apath.isfile() or not archive.cext in ('.7z','.zip','.rar'): continue
            installer = self.data.get(archive)
            if not installer or (installer.size,installer.modified) != (apath.size,apath.mtime): return True
        return False

    def refreshOrder(self):
        """Refresh installer status."""
        changed = False
        data = self.data
        ordered,pending = [],[]
        for archive,installer in self.data.iteritems():
            if installer.order >= 0: ordered.append(archive)
            else: pending.append(archive)
        pending.sort()
        ordered.sort()
        ordered.sort(key=lambda x: data[x].order)
        if self.lastKey in ordered:
            index = ordered.index(self.lastKey)
            ordered[index:index] = pending
        else: ordered += pending
        order = 0
        for archive in ordered:
            if data[archive].order != order:
                data[archive].order = order
                changed = True
            order += 1
        return changed

    def refreshNorm(self):
        """Refresh self.abnorm_sizeCrc."""
        data = self.data
        active = [x for x in data if data[x].isActive]
        active.sort(key=lambda x: data[x].order)
        #--norm
        norm_sizeCrc = {}
        for package in active:
            norm_sizeCrc.update(data[package].data_sizeCrc)
        #--Abnorm
        abnorm_sizeCrc = {}
        data_sizeCrcDate = self.data_sizeCrcDate
        for path,sizeCrc in norm_sizeCrc.iteritems():
            sizeCrcDate = data_sizeCrcDate.get(path)
            if sizeCrcDate and sizeCrc != sizeCrcDate[:2]: abnorm_sizeCrc[path] = sizeCrcDate[:2]
        (self.abnorm_sizeCrc,oldAbnorm_sizeCrc) = (abnorm_sizeCrc,self.abnorm_sizeCrc)
        return abnorm_sizeCrc != oldAbnorm_sizeCrc

    def refreshStatus(self):
        """Refresh installer status."""
        changed = False
        for installer in self.data.itervalues():
            changed |= installer.refreshStatus(self)
        return changed

    #--Operations -------------------------------------------------------------
    def moveArchives(self, moveList, newPos):
        """Move specified archives to specified position."""
        moveSet = set(moveList)
        data = self.data
        numItems = len(data)
        orderKey = lambda x: data[x].order
        oldList = sorted(data, key=orderKey)
        newList = [x for x in oldList if x not in moveSet]
        moveList.sort(key=orderKey)
        newList[newPos:newPos] = moveList
        for index, archive in enumerate(newList):
            data[archive].order = index
        self.setChanged()

    def install(self, archives, progress=None, last=False, override=True):
        """Install selected archives.
        what:
            'MISSING': only missing files.
            Otherwise: all (unmasked) files.
        """
        progress = progress or bolt.Progress()
        #--Mask and/or reorder to last
        mask = set()
        if last: self.moveArchives(archives, len(self.data))
        else:
            maxOrder = max(self[x].order for x in archives)
            for installer in self.data.itervalues():
                if installer.order > maxOrder and installer.isActive:
                    mask |= set(installer.data_sizeCrc)
        #--Install archives in turn
        progress.setFull(len(archives))
        archives.sort(key=lambda x: self[x].order,reverse=True)
        for index,archive in enumerate(archives):
            progress(index,archive.s)
            installer = self[archive]
            destFiles = set(installer.data_sizeCrc) - mask
            if not override: destFiles &= installer.missingFiles
            if destFiles: installer.install(archive,destFiles,self.data_sizeCrcDate,SubProgress(progress,index,index+1))
            installer.isActive = True
            mask |= set(installer.data_sizeCrc)
        self.refreshStatus()

    def uninstall(self,unArchives,progress=None):
        """Uninstall selected archives."""
        unArchives = set(unArchives)
        data = self.data
        data_sizeCrcDate = self.data_sizeCrcDate
        getArchiveOrder =  lambda x: self[x].order
        #--Determine files to remove and files to restore. Keep in mind that
        #  that multiple input archives may be interspersed with other archives
        #  that may block (mask) them from deleting files and/or may provide
        #  files that should be restored to make up for previous files. However,
        #  restore can be skipped, if existing files matches the file being
        #  removed.
        masked = set()
        removes = set()
        restores = {}
        #--March through archives in reverse order...
        for archive in sorted(data,key=getArchiveOrder,reverse=True):
            installer = data[archive]
            #--Uninstall archive?
            if archive in unArchives:
                for data_sizeCrc in (installer.data_sizeCrc,installer.dirty_sizeCrc):
                    for file,sizeCrc in data_sizeCrc.iteritems():
                        sizeCrcDate = data_sizeCrcDate.get(file)
                        if file not in masked and sizeCrcDate and sizeCrcDate[:2] == sizeCrc:
                            removes.add(file)
            #--Other active archive. May undo previous removes, or provide a restore file.
            #  And/or may block later uninstalls.
            elif installer.isActive:
                files = set(installer.data_sizeCrc)
                myRestores = (removes & files) - set(restores)
                for file in myRestores:
                    if installer.data_sizeCrc[file] != data_sizeCrcDate.get(file,(0,0,0))[:2]:
                        restores[file] = archive
                    removes.discard(file)
                masked |= files
        #--Remove files
        emptyDirs = set()
        modsDir = dirs['mods']
        progress.state, progress.full = 0, len(removes)
        for file in removes:
            progress.plus()
            path = modsDir.join(file)
            path.remove()
            (path+'.ghost').remove()
            del data_sizeCrcDate[file]
            emptyDirs.add(path.head)
        #--Remove empties
        for emptyDir in emptyDirs:
            if emptyDir.isdir() and not emptyDir.list(): emptyDir.removedirs()
        #--De-activate
        for archive in unArchives: data[archive].isActive = False
        #--Restore files
        restoreArchives = sorted(set(restores.itervalues()), key=getArchiveOrder, reverse=True)
        if ['mash.installers.autoAnneal'] and restoreArchives:
            progress.setFull(len(restoreArchives))
            for index,archive in enumerate(restoreArchives):
                progress(index,archive.s)
                installer = data[archive]
                destFiles = {x for x, y in restores.iteritems() if y == archive}
                if destFiles: installer.install(archive, destFiles, data_sizeCrcDate, SubProgress(progress, index, index + 1))
        #--Done
        progress.state = len(removes)
        self.refreshStatus()

    def anneal(self,anPackages=None,progress=None):
        """Anneal selected packages. If no packages are selected, anneal all.
        Anneal will:
        * Correct underrides in anPackages.
        * Install missing files from active anPackages."""
        data = self.data
        data_sizeCrcDate = self.data_sizeCrcDate
        anPackages = set(anPackages or data)
        getArchiveOrder =  lambda x: data[x].order
        #--Get remove/refresh files from anPackages
        removes = set()
        for package in anPackages:
            installer = data[package]
            removes |= installer.underrides
            if installer.isActive:
                removes |= installer.missingFiles
                removes |= set(installer.dirty_sizeCrc)
        #--March through packages in reverse order...
        restores = {}
        for package in sorted(data,key=getArchiveOrder,reverse=True):
            installer = data[package]
            #--Other active package. May provide a restore file.
            #  And/or may block later uninstalls.
            if installer.isActive:
                files = set(installer.data_sizeCrc)
                myRestores = (removes & files) - set(restores)
                for file in myRestores:
                    if installer.data_sizeCrc[file] != data_sizeCrcDate.get(file, (0, 0, 0))[:2]: restores[file] = package
                    removes.discard(file)
        #--Remove files
        emptyDirs = set()
        modsDir = dirs['mods']
        for file in removes:
            path = modsDir.join(file)
            path.remove()
            (path+'.ghost').remove()
            data_sizeCrcDate.pop(file, None)
            emptyDirs.add(path.head)
        #--Remove empties
        for emptyDir in emptyDirs:
            if emptyDir.isdir() and not emptyDir.list():
                emptyDir.removedirs()
        #--Restore files
        restoreArchives = sorted(set(restores.itervalues()), key=getArchiveOrder, reverse=True)
        if restoreArchives:
            progress.setFull(len(restoreArchives))
            for index, package in enumerate(restoreArchives):
                progress(index,package.s)
                installer = data[package]
                destFiles = {x for x, y in restores.iteritems() if y == package}
                if destFiles: installer.install(package, destFiles, data_sizeCrcDate, SubProgress(progress, index, index+1))

    def getConflictReport(self,srcInstaller,mode):
        """Returns report of overrides for specified package for display on conflicts tab.
        mode: O: Overrides; U: Underrides"""
        data = self.data
        srcOrder = srcInstaller.order
        conflictsMode = (mode == 'OVER')
        if conflictsMode: mismatched = set(srcInstaller.data_sizeCrc)
        else: mismatched = srcInstaller.underrides
        showInactive = conflictsMode and settings['mash.installers.conflictsReport.showInactive']
        showLower = conflictsMode and settings['mash.installers.conflictsReport.showLower']
        if not mismatched: return ''
        src_sizeCrc = srcInstaller.data_sizeCrc
        packConflicts = []
        getArchiveOrder =  lambda x: data[x].order
        for package in sorted(self.data,key=getArchiveOrder):
            installer = data[package]
            if installer.order == srcOrder: continue
            if not showInactive and not installer.isActive: continue
            if not showLower and installer.order < srcOrder: continue
            curConflicts = Installer.sortFiles([x.s for x,y in installer.data_sizeCrc.iteritems()
                if x in mismatched and y != src_sizeCrc[x]])
            if curConflicts: packConflicts.append((installer.order,package.s,curConflicts))
        #--Unknowns
        isHigher = -1
        buff = cStringIO.StringIO()
        for order,package,files in packConflicts:
            if showLower and (order > srcOrder) != isHigher:
                isHigher = (order > srcOrder)
                buff.write(u'= %s %s\n' % ((_(u'Lower'),_(u'Higher'))[isHigher],'='*40))
            buff.write(u'==%d== %s\n' % (order,package))
            for file in files:
                buff.write(file)
                buff.write('\n')
            buff.write('\n')
        report = buff.getvalue()
        if not conflictsMode and not report and not srcInstaller.isActive:
            report = _(u"No Underrides. Mod is not completely un-installed.")
        return report

# Data Extensions ------------------------------------------------------------

class RefReplacer:
    """Used by FileRefs to replace references."""

    def __init__(self,filePath=None):
        """Initialize."""
        self.srcModName = None #--Name of mod to import records from.
        self.srcDepends = {} #--Source mod object dependencies.
        self.newIds = {} #--newIds[oldId] = (newId1,newId2...)
        self.newIndex = {} #--newIndex[oldId] = Index of next newIds[oldId]
        self.usedIds = set() #--Records to import
        if filePath: self.loadText(filePath)

    def loadText(self,filePath):
        """Loads replacer information from file."""
        ins = file(filePath,'r')
        reComment = re.compile(r"#.*")
        reSection = re.compile(r'@ +(srcmod|replace)',re.M)
        reReplace = re.compile(r"(\w[-\w ']+)\s*:\s*(.+)")
        reNewIds  = re.compile(r",\s*")
        mode = None
        for line in ins:
            line = reComment.sub('',line.strip())
            maSection = reSection.match(line)
            if maSection:
                mode = maSection.group(1)
            elif not line: #--Empty/comment line
                pass
            elif mode == 'srcmod':
                self.srcModName = line
            elif mode == 'replace':
                maReplace = reReplace.match(line)
                if not maReplace: continue
                oldId = maReplace.group(1)
                self.newIds[oldId.lower()] = reNewIds.split(maReplace.group(2))
        ins.close()

    def getNewId(self,oldId):
        """Returns newId replacement for old id."""
        oldId = oldId.lower()
        newIds = self.newIds[oldId]
        if len(newIds) == 1:
            newId = newIds[0]
        else:
            index = self.newIndex.get(oldId,0)
            self.newIndex[oldId] = (index + 1) % len(newIds)
            newId = newIds[index]
        self.usedIds.add(newId.lower())
        return newId

    def getSrcRecords(self):
        """Returns list of records to insert into mod."""
        srcRecords = {}
        if self.srcModName and self.usedIds:
            #--Get FileRep
            srcInfo = modInfos[self.srcModName]
            fullRep = srcInfo.extras.get('FullRep')
            if not fullRep:
                fullRep = FileRep(srcInfo)
                fullRep.load()
                srcInfo.extras['FullRep'] = fullRep
            for record in fullRep.records:
                id = record.getId().lower()
                if id in self.usedIds:
                    srcRecords[id] = copy.copy(record)
        return srcRecords

    def clearUsage(self):
        """Clears usage state."""
        self.newIndex.clear()
        del self.usedIds[:]


class FileRep:
    """Abstract TES3 file representation."""
    def __init__(self, fileInfo,canSave=True,log=None,progress=None):
        """Initialize."""
        self.progress = progress or Progress()
        self.log = log or Log()
        self.fileInfo = fileInfo
        self.canSave = canSave
        self.tes3 = None
        self.records = []
        self.indexed = {} #--record = indexed[type][id]

    def load(self,keepTypes='ALL',factory={}):
        """Load file. If keepTypes, then only keep records of type in keepTypes or factory.
        factory: dictionary mapping record type to record class. For record types
        in factory, specified class will be used and data will be kept."""
        keepAll = (keepTypes == 'ALL')
        keepTypes = keepTypes or set() #--Turns None or 0 into an empty set.
        #--Header
        inPath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        ins = Tes3Reader(self.fileInfo.name,file(inPath,'rb'))
        (name,size,delFlag,recFlag) = ins.unpackRecHeader()
        self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        #--Raw data read
        while not ins.atEnd():
            #--Get record info and handle it
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            if name in factory:
                record = factory[name](name,size,delFlag,recFlag,ins)
                self.records.append(record)
            elif keepAll or name in keepTypes:
                record = Record(name,size,delFlag,recFlag,ins)
                self.records.append(record)
            else: ins.seek(size,1,name)
        #--Done Reading
        ins.close()

    def unpackRecords(self,unpackTypes):
        """Unpacks records of specified types"""
        for record in self.records:
            if record.name in unpackTypes:
                record.load(unpack=True)

    def indexRecords(self,indexTypes):
        """Indexes records of specified types."""
        indexed = self.indexed = {}
        for type in indexTypes:
            indexed[type] = {}
        for record in self.records:
            type = record.name
            if type in indexTypes:
                indexed[type][record.getId().lower()] = record

    def loadUI(self,factory={}):
        """Convenience function. Loads, then unpacks, then indexes."""
        keepTypes = self.canSave and 'ALL' or tuple()
        self.load(keepTypes=keepTypes,factory=factory)
        uiTypes = set(factory.keys())
        self.unpackRecords(uiTypes)
        self.indexRecords(uiTypes)

    def getRecord(self,type,id,Class=None):
        """Gets record with corresponding type and id.
        If record doesn't exist and Class is provided, then a new instance
        with given id is created, added to record list and indexed and then
        returned to the caller."""
        idLower = id.lower()
        typeIds = self.indexed[type]
        if idLower in typeIds:
            return typeIds[idLower]
        elif Class:
            record = Class()
            record.id = id
            self.records.append(record)
            typeIds[idLower] = record
            return record
        else: return None

    def setRecord(self,record):
        """Adds record to record list and indexed."""
        idLower = record.getId().lower()
        type = record.name
        typeIds = self.indexed[type]
        if idLower in typeIds:
            oldRecord = typeIds[idLower]
            index = self.records.index(oldRecord)
            self.records[index] = record
        else: self.records.append(record)
        typeIds[idLower] = record

    def safeSave(self):
        """Save data to file safely."""
        self.fileInfo.makeBackup()
        filePath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        tempPath = filePath+'.tmp'
        self.save(tempPath)
        renameFile(tempPath,filePath)
        self.fileInfo.setMTime()
        self.fileInfo.extras.clear()

    def save(self,outPath=None):
        """Save data to file.
        outPath -- Path of the output file to write to. Defaults to original file path."""
        if (not self.canSave): raise StateError(_(u"Insufficient data to write file."))
        if outPath is None:
            fileInfo = self.fileInfo
            outPath = os.path.join(fileInfo.dir,fileInfo.name)
        with file(outPath,'wb') as out:
            #--Tes3 Record
            self.tes3.setChanged()
            self.tes3.hedr.setChanged()
            self.tes3.hedr.numRecords = len(self.records) #--numRecords AFTER TES3 record
            self.tes3.getSize()
            self.tes3.dump(out)
            #--Other Records
            for record in self.records:
                record.getSize()
                record.dump(out)

    def sortRecords(self):
        #--Get record type order.
        import mush
        order = 0
        typeOrder = {}
        for typeIncrement in listFromLines(mush.recordTypes):
            (type,increment) = typeIncrement.split()
            if increment == '+': order += 1
            typeOrder[type] = order
        #--Get ids for records. (For subsorting.)
        ids = {}
        noSubSort = {'CELL', 'LAND', 'PGRD', 'DIAL', 'INFO'}
        for record in self.records:
            recData = record.data
            if record.name in noSubSort:
                ids[record] = 0
            else:
                id = record.getId()
                ids[record] = id and id.lower()
        #--Sort
        self.records.sort(cmp=lambda a,b:
            cmp(typeOrder[a.name],typeOrder[b.name]) or cmp(ids[a],ids[b]))


class FileRefs(FileRep):
    """TES3 file representation with primary focus on references, but also
    including other information used in file repair."""

    def __init__(self, fileInfo, skipNonCells=False, skipObjRecords=False,log=None,progress=None):
        canSave = not skipNonCells #~~Need to convert skipNonCells argument to this.
        FileRep.__init__(self, fileInfo, canSave, log ,progress)
        self.skipObjRecords = skipObjRecords
        self.tes3 = None
        self.fmap = None
        self.records = []
        self.cells = []
        self.lands = {} #--Landscapes indexed by Land.id.
        #--Save Debris Info
        self.debrisIds = {}
        #--Content records
        self.conts = [] #--Content records: CREC, CNTC, NPCC
        self.conts_id = {}
        self.cells_id = {}
        self.refs_scpt = {}
        self.scptRefs = set()
        self.isLoaded = False
        self.isDamaged = False

    #--File Handling---------------------------------------
    def setDebrisIds(self):
        """Setup to record ids to be used by WorldRefs.removeSaveDebris.
        Should be called before load or refresh."""
        for type in ['BOOK','CREA','GLOB','NPC_','LEVI','LEVC','FACT']:
            if type not in self.debrisIds:
                self.debrisIds[type] = []
        #--Built-In Globals (automatically added by game engine)
        for builtInGlobal in ('monthstorespawn','dayspassed'):
            if builtInGlobal not in self.debrisIds['GLOB']:
                self.debrisIds['GLOB'].append(builtInGlobal)

    def refreshSize(self):
        """Return file size if needs to be updated. Else return 0."""
        if self.isLoaded:
            return 0
        else:
            return self.fileInfo.size

    def refresh(self):
        """Load data if file has changed since last load."""
        if self.isDamaged:
            raise StateError(self.fileInfo.name+_(u': Attempted to access damaged file.'))
        if not self.isLoaded:
            try:
                self.load()
                self.isLoaded = True
            except Tes3ReadError, error:
                self.isDamaged = True
                if not error.inName:
                    error.inName = self.fileInfo.name
                raise

    def load(self):
        """Load reference data from file."""
        progress = self.progress
        filePath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        self.fileSize = os.path.getsize(filePath)
        #--Localize
        cells = self.cells
        records = self.records
        canSave = self.canSave
        skipObjRecords = self.skipObjRecords
        contTypes = {'CREC', 'CNTC', 'NPCC'}
        levTypes = {'LEVC', 'LEVI'}
        debrisIds = self.debrisIds
        debrisTypes = set(debrisIds.keys())
        #--Header
        inPath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        ins = Tes3Reader(self.fileInfo.name,file(inPath,'rb'))
        (name,size,delFlag,recFlag) = ins.unpackRecHeader()
        self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        if not canSave: del self.tes3.others[:]
        #--Progress info
        progress = self.progress
        progress(0.0,'Loading '+self.fileInfo.name)
        #--Raw data read
        while not ins.atEnd():
            #--Get record info and handle it
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            #--CELL?
            if name == 'CELL':
                record = Cell(name,size,delFlag,recFlag,ins,0,skipObjRecords)
                cells.append(record)
                if canSave: records.append(record)
            #--Contents
            elif canSave and name in contTypes:
                if name == 'CREC': record = Crec(name,size,delFlag,recFlag,ins,True)
                elif name == 'CNTC': record = Cntc(name,size,delFlag,recFlag,ins,True)
                else: record = Npcc(name,size,delFlag,recFlag,ins,True)
                self.conts.append(record)
                self.conts_id[record.getId()] = record
                records.append(record)
            #--File Map
            elif name == 'FMAP':
                record = Fmap(name,size,delFlag,recFlag,ins)
                self.fmap = record
                records.append(record)
            #--Landscapes
            elif name == 'LAND':
                record = Land(name,size,delFlag,recFlag,ins)
                self.lands[record.getId()] = record
                records.append(record)
            #--Scripts
            elif canSave and name == 'SCPT':
                record = Scpt(name,size,delFlag,recFlag,ins,True)
                records.append(record)
                if record.getRef(): self.refs_scpt[record] = record.getRef()
            #--Save debris info?
            elif name in debrisTypes:
                record = Record(name,size,delFlag,recFlag,ins)
                id = record.getId()
                if id: debrisIds[name].append(id.lower())
                if canSave: records.append(record)
            #--Skip Non-cell?
            elif not canSave: ins.seek(size,1,name)
            #--Keep non-cell?
            else: records.append(Record(name,size,delFlag,recFlag,ins))
        #--Done Reading
        ins.close()
        #--Analyze Cells
        cntCells = 0
        progress.setMax(len(self.cells))
        for cell in self.cells:
            cell.load(None,1)
            self.cells_id[cell.getId()] = cell
            if not canSave: cell.data = None #--Free some memory
            #--Progress
            cntCells += 1
            progress(cntCells)
        #--Scripts
        if self.refs_scpt: self.updateScptRefs()

    def save(self,outPath=None):
        """Save data to file.
        outPath -- Path of the output file to write to. Defaults to original file path."""
        if (not self.canSave or self.skipObjRecords): raise StateError(_(u"Insufficient data to write file."))
        if not outPath:
            fileInfo = self.fileInfo
            outPath = os.path.join(fileInfo.dir,fileInfo.name)
        out = file(outPath,'wb')
        #--Tes3 Record
        self.tes3.changed = 1
        self.tes3.hedr.changed = 1
        self.tes3.hedr.numRecords = len(self.records) #--numRecords AFTER TES3 record
        self.tes3.getSize()
        self.tes3.dump(out)
        #--Size Cell Records
        cntRecords = 0
        progress = self.progress
        progress.setMax(len(self.cells))
        progress(0.0,'Saving '+self.fileInfo.name)
        for record in self.cells:
            record.getSize()
            #--Progress
            cntRecords += 1
            progress(cntRecords)
        #--Other Records
        for record in self.records:
            record.getSize() #--Should already be done, but just in case.
            record.dump(out)
        out.close()

    #--Renumbering-------------------------------------------------------------
    def getFirstObjectIndex(self):
        """Returns first object index number. Assumes that references are in linear order."""
        if not self.fileInfo.isEsp(): raise StateError(_(u'FileRefs.renumberObjects is for esps only.'))
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                if object[0] == 0:
                    return object[1]
        return 0

    def renumberObjects(self,first):
        """Offsets all local object index numbers by specified amount. FOR ESPS ONLY!
        Returns number of objects changed."""
        if not self.fileInfo.isEsp(): raise StateError(_(u'FileRefs.renumberObjects is for esps only.'))
        if first <= 0: raise ArgumentError(_(u'First index should be a positive integer'))
        log = self.log
        next = int(first)
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                if object[0] == 0:
                    newObject = (0,next)+object[2:]
                    objects.replace(object,newObject)
                    next += 1
        return (next - first)

    #--Remapping---------------------------------------------------------------
    def remap(self,newMasters,modMap,objMaps=[]):
        """Remap masters and modIndexes.
        newMasters -- New master list. Same format as Cell.masters.
        modMap -- mapping dictionary so that newModIndex = modMap[oldModIndex]
        objMaps -- ObjectIndex mapping dictionaries"""
        #--Masters
        self.tes3.masters = newMasters
        #--File mapping
        modMapKeys = modMap.keys()
        #--Remap iObjs
        cells_id = self.cells_id
        reObjNum = re.compile('[0-9A-Z]{8}$')
        for (iMod,objMap) in objMaps:
            cellIds = objMap.keys()
            for cellId in cellIds:
                cellObjMap = objMap[cellId]
                #--Save
                cell = cells_id.get(cellId)
                if not cell: continue
                #--Objects
                objects = cell.getObjects()
                for object in objects.list():
                    #--Different mod?
                    if object[0] != iMod: pass
                    #--Cell deleted?
                    elif cellObjMap == -1: objects.remove(object)
                    #--Remapped object?
                    elif object[1] in cellObjMap:
                        (newIObj,objId) = cellObjMap[object[1]]
                        objIdBase = reObjNum.sub('',objId) #--Strip '00001234' id num from object
                        #--Mismatched object id?
                        if objId != objIdBase: pass
                        #--Deleted object?
                        elif newIObj == -1: objects.remove(object)
                        #--Remapped object?
                        else:
                            newObject = self.remapObject(object,iMod,newIObj)
                            objects.replace(object,newObject)
        self.updateScptRefs()
        #--Remap iMods
        if not modMapKeys: return
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                #--Remap IMod
                iMod = object[0]
                #--No change?
                if iMod not in modMapKeys: pass
                #--Object deleted?
                elif modMap[iMod] == -1: objects.remove(object)
                #--Object not deleted?
                else:
                    newObject = self.remapObject(object,modMap[iMod])
                    objects.replace(object,newObject)
        self.updateScptRefs()

    def remapObject(self,object,newIMod,newIObj=-1):
        """Returns an object mapped to a newMod."""
        (iMod,iObj,objId,objRecords) = object[:4]
        if newIObj == -1: newIObj = iObj
        newObject = (newIMod,newIObj)+object[2:]
        if objRecords and objRecords[0].name == 'MVRF':
            data = cStringIO.StringIO()
            data.write(struct.pack('i',newIObj)[:3])
            data.write(struct.pack('B',newIMod))
            objRecords[0].data = data.getvalue()
            objRecords[0].setChanged(False)
            data.close()
        #--Remap any script references
        oldRef = (iMod,iObj)
        if oldRef in self.scptRefs:
            newRef = (newIMod,newIObj)
            for scpt in self.refs_scpt.keys():
                if self.refs_scpt[scpt] == oldRef:
                    scpt.setRef(newRef)
                    self.refs_scpt[scpt] = newRef
                    #--Be sure to call updateScptRefs when finished remapping *all* objects.
        #--Done
        return newObject

    def updateScptRefs(self):
        """Updates refs_scpt and scptRefs data. Call after all objects have been remapped."""
        for scpt in self.refs_scpt.keys():
            self.refs_scpt[scpt] = scpt.getRef()
        self.scptRefs = set(self.refs_scpt.values())

    def listBadRefScripts(self):
        """Logs any scripts with bad refs."""
        if not self.log: return
        ids = []
        for record in self.records:
            if record.name != 'SCPT': continue
            rnam = record.rnam
            if rnam and rnam.data == chr(255)*4:
                ids.append(record.getId())
        if ids:
            self.log.setHeader(_(u'Detached Global Scripts'))
            for id in sorted(ids,key=string.lower):
                self.log(id)

    def getObjectMap(self,oldRefs):
        """Returns an iObj remapping from an old FileRefs to this FileRefs.

        This is used to update saved games from one version of a mod to a newer version."""
        objMap = {} #--objMap[cellId][oldIObj] = newIObj
        #--Old cells
        for oldCell in oldRefs.cells:
            cellId = oldCell.getId()
            newCell = self.cells_id.get(cellId)
            #--Cell deleted?
            if not newCell:
                objMap[cellId] = -1
                continue
            cellObjMap = {}
            newObjects = newCell.getObjects().list()
            nextObjectIndex = {}
            #--Old Objects
            for oldObject in oldCell.getObjects().list():
                (iMod,oldIObj,objId) = oldObject[:3]
                if iMod: continue #--Skip mods to masters
                #--New Objects
                objIndex = nextObjectIndex.get(objId,0)
                newIObj = -1 #--Delete by default
                while objIndex < len(newObjects):
                    newObject = newObjects[objIndex]
                    objIndex += 1
                    if newObject[0]: continue #--Skip mods to masters
                    if newObject[2] == objId:
                        newIObj = newObject[1]
                        break
                nextObjectIndex[objId] = objIndex
                #--Obj map has changed?
                if newIObj != oldIObj:
                    cellObjMap[oldIObj] = (newIObj,objId)
            #--Save mapping for this cell?
            if cellObjMap: objMap[cellId] = cellObjMap
        #--Done
        return objMap

    #--Removers ---------------------------------------------------------------
    def removeLvcrs(self):
        """Remove all LVCR refs.
        In save game, effect is to reset the spawn point."""
        count = 0
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                for objRecord in object[3]:
                    if objRecord.name == 'LVCR':
                        objects.remove(object)
                        count += 1
                        break
        return count

    def removeOrphanContents(self):
        """Remove orphaned content records."""
        reObjNum = re.compile('[0-9A-Z]{8}$')
        #--Determine which contIds are matched to a reference.
        contIds = set(self.conts_id.keys())
        matched = {id: False for id in contIds}
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                objId= object[2]
                #--LVCR? Get id of spawned creature instead.
                for objRecord in object[3]:
                    if objRecord.name == 'NAME':
                        objId = cstrip(objRecord.data)
                        break
                if reObjNum.search(objId):
                    if objId in contIds:
                        matched[objId] = True
        #--Special case: PlayerSaveGame
        matched['PlayerSaveGame00000000'] = True
        #--unmatched = container records that have not been matched.
        orphans = set([self.conts_id[id] for id in contIds if not matched[id]])
        for orphan in sorted(orphans, key=lambda a: a.getId().lower()):
            self.log('  '+orphan.getId())
        #--Delete Records
        self.records = [record for record in self.records if record not in orphans]
        self.conts   = [record for record in self.conts if record not in orphans]
        self.conts_id = {id: record for id, record in self.conts_id.iteritems() if matched[id] > 0}
        return len(orphans)

    def removeRefsById(self,objIds,safeCells=[]):
        """Remove refs with specified object ids, except in specified cells.
        objIds -- Set of object ids to re removed.
        skipCells -- Set of cell names to be skipped over."""
        reObjNum = re.compile('[0-9A-F]{8}$')
        delCount = {}
        reSafeCells = re.compile('('+('|'.join(safeCells))+')')
        cellsSkipped = []
        for cell in self.cells:
            if safeCells and reSafeCells.match(cell.getId()):
                cellsSkipped.append(cell.getId())
                continue
            objects = cell.getObjects()
            for object in objects.list():
                objId = object[2]
                #--If ref is a spawn point, then use id of spawned creature.
                for objRecord in object[3]:
                    if objRecord.name == 'NAME':
                        objId = cstrip(objRecord.data)
                        break
                objBase = reObjNum.sub('',objId) #--Strip '00001234' id num from object
                if objBase in objIds:
                    objects.remove(object)
                    delCount[objBase] = delCount.get(objBase,0) + 1
        #--Done
        log = self.log
        log.setHeader(_(u'Cells Skipped:'))
        for cell in sorted(cellsSkipped,key=lambda a: a.lower()):
            log('  '+cell)
        log.setHeader(_(u'References Deleted:'))
        for objId in sorted(delCount.keys(),key=lambda a: a.lower()):
            log('  %03d  %s' % (delCount[objId],objId))

    #--Replacers --------------------------------------------------------------
    def replaceRefsById(self,refReplacer):
        """Replace refs according to refReplacer."""
        log = self.log
        oldIds = set(refReplacer.newIds.keys())
        replCount = {}
        for cell in self.cells:
            objects = cell.getObjects()
            for object in objects.list():
                (iMod,iObj,oldId,objRecords) = object[:4]
                if oldId.lower() in oldIds:
                    newId = refReplacer.getNewId(oldId)
                    newObject = (iMod,iObj,newId,objRecords)
                    objects.replace(object,newObject)
                    replCount[oldId] = replCount.get(oldId,0) + 1
        #--Add Records?
        newRecords = refReplacer.getSrcRecords()
        if newRecords:
            selfIds = set([record.getId().lower() for record in self.records if record.getId()])
            log.setHeader(_(u'Records added:'))
            for newId in sorted(newRecords.keys()):
                if newId not in selfIds:
                    self.records.append(newRecords[newId])
                    log(newId)
        #--Log
        log.setHeader(_(u'References replaced:'))
        for oldId in sorted(replCount.keys(),key=lambda a: a.lower()):
            log('%03d %s' % (replCount[oldId], oldId))
        #--Return number of references replaced.
        return sum(replCount.values())


class WorldRefs:
    """World references as defined by a set of masters (esms and esps)."""
    def __init__(self,masterNames = [], progress=None, log=None):
        self.progress = progress or Progress()
        self.log = log or Log()
        self.levListMasters = {} #--Count of masters for each leveled list (LEVC or LEVI)
        self.masterNames = [] #--Names of masters, in order added
        self.extCellNames = set() #--Named exterior cells.
        self.cellRefIds = {}  #--objId = cellRefIds[cellId][(iMod,iObj)]
        self.cellRefAlts = {} #--(iModNew,iObj) = cellRefAlts[cellId][(iModOld,iObj)]
        self.debrisIds = {}
        self.lands = {} #--Landscape records indexed by landscape record id.
        if masterNames:
            self.addMasters(masterNames)

    def addMasters(self,masterNames):
        """Add a list of mods."""
        #--Load Masters
        #--Master FileRefs
        proItems = []
        totSize = 0
        for masterName in masterNames:
            #--Don't have fileRef? FileRef out of date?
            masterInfo = modInfos[masterName]
            fileRefs = masterInfo.extras.get('FileRefs')
            if not fileRefs:
                fileRefs = masterInfo.extras['FileRefs'] = FileRefs(masterInfo,True,True)
                fileRefs.setDebrisIds()
            refreshSize = fileRefs.refreshSize()
            if refreshSize:
                proItems.append((fileRefs,refreshSize))
                totSize += refreshSize
        #--Refresh masters
        cumSize = 0
        for (fileRefs,size) in proItems:
            self.progress.setBaseScale(1.0*cumSize/totSize, 1.0*size/totSize)
            fileRefs.progress = self.progress
            fileRefs.refresh()
            cumSize += size
        #--Do Mapping
        del proItems[:]
        totSize = 0
        for masterName in masterNames:
            size = len(modInfos[masterName].extras['FileRefs'].cells)
            proItems.append((masterName,size))
            totSize += size
        cumSize = 0
        for (masterName,size) in proItems:
            if size: self.progress.setBaseScale(1.0*cumSize/totSize, 1.0*size/totSize)
            self.addMaster(masterName)
            cumSize += size

    def addMaster(self,masterName):
        """Add a single mod."""
        masterInfo = modInfos[masterName]
        self.masterNames.append(masterName)
        #--Map info
        iMod = len(self.masterNames)
        #--Map masters
        masterMap = self.getMasterMap(masterInfo)
        masterRefs = masterInfo.extras['FileRefs']
        #--Get Refs types and alts
        cellRefIds = self.cellRefIds
        cellRefAlts = self.cellRefAlts
        #--Progress
        cntCells = 0
        progress = self.progress
        progress.setMax(len(masterRefs.cells))
        progress(0.0,_(u"Building ")+masterName)
        for cell,record in masterRefs.lands.items():
            self.lands[cell] = record
        for masterCell in masterRefs.cells:
            cellId = masterCell.getId()
            #--Named exterior cell?
            if not (masterCell.flags & 1) and masterCell.cellName:
                self.extCellNames.add(masterCell.cellName)
            #--New cell id?
            if cellId not in cellRefIds:
                refIds = cellRefIds[cellId] = {}
                refAlts = cellRefAlts[cellId] = {}
            #--Exiting cell id?
            else:
                refIds = cellRefIds[cellId]
                refAlts = cellRefAlts[cellId]
            #--Objects
            for object in masterCell.getObjects().list():
                (iMMod,iObj,objId) = object[:3]
                newIdKey = (iMod,iObj)
                #--Modifies a master reference?
                if iMMod:
                    if iMMod >= len(masterMap):
                        raise Tes3RefError(masterName,cellId,objId,iObj,iMMod,
                            _(u'NO SUCH MASTER'))
                    altKey = (masterMap[iMMod],iObj)
                    oldIdKey = altKey
                    #--Already modified?
                    if altKey in refAlts:
                        oldIdKey = refAlts[altKey]
                    if oldIdKey not in refIds:
                        raise Tes3RefError(masterName,cellId,objId,iObj,iMMod,
                            masterInfo.masterNames[iMMod-1])
                    del refIds[oldIdKey]
                    refAlts[altKey] = newIdKey
                #--Save it
                refIds[newIdKey] = objId
            #--Progress
            cntCells += 1
            progress(cntCells)
        #--Debris Ids
        for type, ids in masterRefs.debrisIds.items():
            if type not in self.debrisIds:
                self.debrisIds[type] = set()
            self.debrisIds[type].update(ids)
        #--List Masters
        levListMasters = self.levListMasters
        for levList in (masterRefs.debrisIds['LEVC'] + masterRefs.debrisIds['LEVI']):
            if levList not in levListMasters:
                levListMasters[levList] = []
            levListMasters[levList].append(masterName)

    def getMasterMap(self,masterInfo):
        """Return a map of a master's masters to the refworld's masters."""
        masterMap = [0]
        #--Map'em
        for mmName in masterInfo.masterNames:
            if mmName not in self.masterNames:
                raise MoshError(_(u"Misordered esm: %s should load before %s") % (mmName, masterInfo.name))
            masterMap.append(self.masterNames.index(mmName)+1)
        #--Done
        return masterMap

    #--Repair ---------------------------------------------
    def removeDebrisCells(self,fileRefs):
        """Removes debris cells -- cells that are not supported by any of the master files."""
        #--Make sure fileRefs for a save file!
        if not fileRefs.fileInfo.isEss():
            fileName = fileRefs.fileInfo.fileName
            raise ArgumentError(_(u'Cannot remove debris cells from a non-save game!')+fileName)
        log = self.log
        cntDebrisCells = 0
        log.setHeader("Debris Cells")
        for cell in fileRefs.cells:
            #--Cell Id
            cellId = cell.getId()
            if cellId not in self.cellRefIds:
                log(cellId)
                fileRefs.records.remove(cell)
                fileRefs.cells.remove(cell)
                del fileRefs.cells_id[cellId]
                cntDebrisCells += 1
        return cntDebrisCells

    def removeDebrisRecords(self,fileRefs):
        """Removes debris records (BOOK, CREA, GLOB, NPC_) that are not present
        in masters and that aren't constructed in game (custom enchantment scrolls)."""
        #--Make sure fileRefs for a save file!
        if not fileRefs.fileInfo.isEss():
            fileName = fileRefs.fileInfo.fileName
            raise ArgumentError(_(u'Cannot remove save debris from a non-save game!')+fileName)
        goodRecords = []
        debrisIds = self.debrisIds
        debrisTypes = set(debrisIds.keys())
        reCustomId = re.compile('^\d{10,}$')
        removedIds = {}
        for record in fileRefs.records:
            type = record.name
            if type in debrisTypes:
                id = record.getId()
                if id and id.lower() not in debrisIds[type] and not reCustomId.match(id):
                    if type not in removedIds:
                        removedIds[type] = []
                    removedIds[type].append(id)
                    continue #--Skip appending this record to good records.
            goodRecords.append(record)
        #--Save altered record list?
        cntDebrisIds = 0
        if removedIds:
            #--Save changes
            del fileRefs.records[:]
            fileRefs.records.extend(goodRecords)
            #--Log
            log = self.log
            for type in sorted(removedIds.keys()):
                log.setHeader(_(u"Debris %s:") % (type,))
                for id in sorted(removedIds[type],key=lambda a: a.lower()):
                    log('  '+id)
                cntDebrisIds += len(removedIds[type])
        return cntDebrisIds

    def removeOverLists(self,fileRefs):
        """Removes leveled lists when more than one loaded mod changes that
        same leveled list."""
        if not fileRefs.fileInfo.isEss():
            fileName = fileRefs.fileInfo.fileName
            raise ArgumentError(_(u'Cannot remove overriding lists from a non-save game!')+fileName)
        listTypes = {'LEVC', 'LEVI'}
        levListMasters = self.levListMasters
        log = self.log
        cntLists = 0
        log.setHeader(_(u"Overriding Lists"))
        #--Go through records and trim overriding lists.
        goodRecords = []
        for record in fileRefs.records:
            type = record.name
            if type in listTypes:
                id = record.getId()
                idl = id.lower()
                masters = levListMasters.get(idl,'')
                if len(masters) != 1:
                    log('  '+id)
                    for master in masters:
                        log('    '+master)
                    cntLists += 1
                    #del fileRefs.debrisIds[type][idl]
                    continue #--Skip appending this record to good records.
            goodRecords.append(record)
        del fileRefs.records[:]
        fileRefs.records.extend(goodRecords)
        return cntLists

    def repair(self,fileRefs):
        """Repair the references for a file."""
        #--Progress/Logging
        log = self.log
        logBDD = _('BAD DELETE>>DELETED %d %d %s')
        logBRR = _('BAD REF>>REMATCHED  %d %d %s %d')
        logBRN = _('BAD REF>>NO MASTER  %d %d %s')
        logBRD = _('BAD REF>>DOUBLED    %d %d %s')
        #----
        isMod = (fileRefs.fileInfo.isMod())
        reObjNum = re.compile('[0-9A-Z]{8}$')
        emptyDict = {}
        cellRefIds = self.cellRefIds
        cntRepaired = 0
        cntDeleted = 0
        cntUnnamed = 0
        for cell in fileRefs.cells:
            #--Data arrays
            usedKeys = []
            badDeletes = []
            badObjects = []
            doubleObjects = []
            refMods = {}
            #--Cell Id
            cellId = cell.getId()
            log.setHeader(cellId)
            #--Debris cell name?
            if not isMod:
                cellName = cell.cellName
                if not (cell.flags & 1) and cellName and (cellName not in self.extCellNames):
                    log(_(u"Debris Cell Name: ")+cellName)
                    cell.flags &= ~32
                    cell.cellName = ''
                    cell.setChanged()
                    cntUnnamed += 1
            refIds = cellRefIds.get(cellId,emptyDict) #--Empty if cell is new in fileRefs.
            objects = cell.getObjects()
            for object in objects.list():
                (iMod,iObj,objId,objRecords) = object[:4]
                refKey = (iMod,iObj)
                #--Used Key?
                if refKey in usedKeys:
                    log(logBRD % object[:3])
                    objects.remove(object)
                    doubleObjects.append(object)
                    cell.setChanged()
                #--Local object?
                elif not iMod:
                    #--Object Record
                    for objRecord in objRecords:
                        #--Orphan delete?
                        if objRecord.name == 'DELE':
                            log(logBDD % object[:3])
                            objects.remove(object)
                            badDeletes.append(object)
                            cntDeleted += 1
                            cell.setChanged()
                            break
                    #--Not Deleted?
                    else: #--Executes if break not called in preceding for loop.
                        usedKeys.append(refKey)
                #--Modified object?
                else:
                    refId = refIds.get(refKey,None)
                    objIdBase = reObjNum.sub('',objId) #--Strip '00001234' id num from object
                    #--Good reference?
                    if refId and (isMod or (refId == objIdBase)):
                        usedKeys.append(refKey)
                    #--Missing reference?
                    else:
                        badObjects.append(object)
                        cell.setChanged()
            #--Fix bad objects.
            if badObjects:
                #--Build rematching database where iMod = refMods[(iObj,objId)]
                refMods = {}
                repeatedKeys = []
                for refId in refIds.keys():
                    (iMod,iObj) = refId
                    objId = refIds[refId]
                    key = (iObj,objId)
                    #--Repeated Keys?
                    if key in refMods:
                        repeatedKeys.append(key)
                    else:
                        refMods[key] = iMod
                #--Remove remaps for any repeated keys
                for key in repeatedKeys:
                    if key in refMods: del refMods[key]
                #--Try to remap
                for object in badObjects:
                    (iMod,iObj,objId) = object[:3]
                    objIdBase = reObjNum.sub('',objId) #--Strip '00001234' id num from object
                    refModsKey = (iObj,objIdBase)
                    newMod = refMods.get(refModsKey,None)
                    #--Valid rematch?
                    if newMod and ((newMod,iObj) not in usedKeys):
                        log(logBRR % (iMod,iObj,objId,newMod))
                        usedKeys.append((newMod,iObj))
                        objects.replace(object,fileRefs.remapObject(object,newMod))
                        cntRepaired += 1
                    elif not newMod:
                        log(logBRN % tuple(object[:3]))
                        objects.remove(object)
                        cntDeleted += 1
                    else:
                        log(logBRD % tuple(object[:3]))
                        objects.remove(object)
                        cntDeleted += 1
        #--Done
        fileRefs.updateScptRefs()
        return (cntRepaired,cntDeleted,cntUnnamed)

    def repairWorldMap(self,fileRefs,gridLines=True):
        """Repair savegame's world map."""
        if not fileRefs.fmap: return 0
        progress = self.progress
        progress.setMax((28*2)**2)
        progress(0.0,_(u"Drawing Cells"))
        proCount = 0
        for gridx in xrange(-28,28,1):
            for gridy in xrange(28,-28,-1):
                id = '[%d,%d]' % (gridx,gridy)
                cell = fileRefs.cells_id.get(id,None)
                isMarked = cell and cell.flags & 32
                fileRefs.fmap.drawCell(self.lands.get(id),gridx,gridy,isMarked)
                proCount += 1
                progress(proCount)
        fileRefs.fmap.drawGrid(gridLines)
        return 1


class FileDials(FileRep):
    """TES3 file representation focusing on dialog.

    Only TES3 DIAL and INFO records are analyzed. All others are left in raw data
    form. """
    def __init__(self, fileInfo, canSave=True):
        FileRep.__init__(self,fileInfo,canSave)
        self.dials = []
        self.infos = {} #--info = self.infos[(dial.type,dial.id,info.id)]

    def load(self,factory={}):
        """Load dialogs from file."""
        canSave = self.canSave
        InfoClass = factory.get('INFO',InfoS) #--Info class from factory.
        #--Header
        inPath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        ins = Tes3Reader(self.fileInfo.name,file(inPath,'rb'))
        (name,size,delFlag,recFlag) = ins.unpackRecHeader()
        self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        #--Raw data read
        dial = None
        while not ins.atEnd():
            #--Get record info and handle it
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            #--DIAL?
            if name == 'DIAL':
                dial = Dial(name,size,delFlag,recFlag,ins,True)
                self.dials.append(dial)
                if canSave: self.records.append(dial)
            #--INFO?
            elif name == 'INFO':
                info = InfoClass(name,size,delFlag,recFlag,ins,True)
                self.records.append(info)
                dial.infos.append(info)
                self.infos[(dial.type,dial.id,info.id)] = info
            #--Non-dials?
            elif canSave:
                record = Record(name,size,delFlag,recFlag,ins)
                self.records.append(record)
            else:
                ins.seek(size,1,'Record')
        #--Done Reading
        ins.close()

    def save(self,outPath=None):
        """Save data to file.
        outPath -- Path of the output file to write to. Defaults to original file path."""
        if (not self.canSave): raise StateError(_(u"Insufficient data to write file."))
        FileRep.save(self,outPath)

    def loadText(self,textFileName):
        """Replaces dialog text with text read from file."""
        #--Text File
        infoKey = None
        text = None
        texts = {}
        reHeader = re.compile('^#')
        reInfo = re.compile('@ +(\d) +"(.+?)" +(\d+)')
        reSingleQuote = re.compile('[\x91\x92]')
        reDoubleQuote = re.compile('[\x93\x94]')
        reEllipsis = re.compile('\x85')
        reEolSpaces = re.compile(r' +\r\n')
        reExtraSpaces = re.compile(r'  +')
        reIllegalChars = re.compile(r'[@#]')
        #--Read file
        textFile = file(textFileName,'rb')
        for line in textFile:
            if reHeader.match(line): continue
            maInfo = reInfo.match(line)
            if maInfo:
                infoKey = (int(maInfo.group(1)),maInfo.group(2),maInfo.group(3))
                texts[infoKey] = text = []
            else:
                text.append(line)
        textFile.close()
        #--Strip and clean texts
        updated = []
        unmatched = []
        trimmed = {}
        for infoKey in texts.keys():
            if infoKey not in self.infos:
                unmatched.append(infoKey)
                continue
            text = ''.join(texts[infoKey])
            #--Required Subs
            text = text.strip(' \r\n')
            text = reSingleQuote.sub('\'',text)
            text = reDoubleQuote.sub('"',text)
            text = reEllipsis.sub('...',text)
            text = reIllegalChars.sub('',text)
            #--Optional subs
            text = reEolSpaces.sub('\r\n',text)
            text = reExtraSpaces.sub(' ',text)
            #--Trim?
            if len(text) > 511:
                trimmed[infoKey] = (text[:511],text[511:])
                text = text[:511]
            info = self.infos[infoKey]
            if text != info.text:
                info.text = text
                info.setChanged()
                updated.append(infoKey)
        #--Report
        buff = cStringIO.StringIO()
        for header,infoKeys in ((_('Updated'),updated),(_('Unmatched'),unmatched)):
            if infoKeys:
                buff.write('=== %s\n' % (header,))
            for infoKey in infoKeys:
                buff.write('* %s\n' % (infoKey,))
        if trimmed:
            buff.write('=== %s\n' % (_('Trimmed'),))
            for infoKey,(preTrim,postTrim) in trimmed.items():
                buff.write(`infoKey`+'\n'+preTrim+'<<<'+postTrim+'\n\n')
        return buff.getvalue()

    def dumpText(self,textFileName,groupBy='spId',spId=None):
        """Dumps dialogs to file."""
        newDials = self.dials[:]
        newDials.sort(key=lambda a: a.id.lower())
        newDials.sort(key=lambda a: a.type,reverse=True)
        infoKeys = []
        for dial in newDials:
            dial.sortInfos()
            for info in dial.infos:
                infoKeys.append((dial.type,dial.id,info.id))
        if groupBy == 'spId':
            infoKeys.sort(key=lambda a: self.infos[a].spId and self.infos[a].spId.lower())
        #--Text File
        with file(textFileName,'wb') as textFile:
            prevSpId = prevTopic = -1
            for infoKey in infoKeys:
                info = self.infos[infoKey]
                #--Filter by spId?
                if spId and info.spId != spId: continue
                #--Empty text?
                if not info.text: continue
                #--NPC Header?
                if groupBy == 'spId' and info.spId != prevSpId:
                    prevSpId = info.spId
                    header = prevSpId or ''
                    textFile.write('# "%s" %s\r\n' % (header,'-'*(75-len(header))))
                #--Topic header?
                elif groupBy == 'topic' and infoKey[1] != prevTopic:
                    prevTopic = infoKey[1]
                    header = prevTopic or ''
                    textFile.write('# "%s" %s\r\n' % (header,'-'*(75-len(header))))
                textFile.write('@ %d "%s" %s' % infoKey)
                if info.spId:
                    textFile.write(' "'+info.spId+'"')
                textFile.write('\r\n')
                textFile.write(info.text)
                textFile.write('\r\n')
                textFile.write('\r\n')


class FileLibrary(FileRep):
    """File representation for generating library books.
    Generates library books from input text file and current mod load list."""
    def __init__(self, fileInfo,canSave=True,log=None,progress=None):
        """Initialize."""
        self.srcBooks = {} #--srcBooks[srcId] = (bookRecord,modName)
        self.altBooks = {} #--altBooks[altId] = (bookRecord,modName)
        self.libList  = [] #--libId1, libId2, etc. in same order as in text file.
        self.libMap   = {} #--libMap[libId]  = (srcId,altId)
        FileRep.__init__(self,fileInfo,canSave,log,progress)

    def loadUI(self,factory={'GLOB':Glob,'BOOK':Book,'SCPT':Scpt,'CELL':Cell}):
        """Loads data from file."""
        FileRep.loadUI(self,factory)

    def loadText(self,inName):
        """Read library book list from specified text file."""
        reComment = re.compile(r'\s*\#.*')
        ins = file(inName)
        for line in ins:
            #--Strip spaces and comments
            line = reComment.sub('',line)
            line = line.rstrip()
            #--Skip empty/comment lines
            if not line: continue
            #--Parse line
            (libId,srcId,altId) = line.split('\t')[:3]
            self.libList.append(libId)
            self.libMap[libId] = (srcId,altId)
        #--Done
        ins.close()

    def getBooks(self):
        """Extracts source book data from currently loaded mods."""
        srcIds = set([srcId for srcId,altId in self.libMap.values()])
        altIds = set([altId for srcId,altId in self.libMap.values()])
        factory = {'BOOK':Book}
        for modName in mwIniFile.loadOrder:
            print modName
            fileRep = FileRep(modInfos[modName],False)
            fileRep.load(keepTypes=None,factory=factory)
            for record in fileRep.records:
                if record.name == 'BOOK':
                    bookId = record.getId()
                    if bookId in srcIds:
                        print '',bookId
                        self.srcBooks[bookId] = (record,modName)
                    elif bookId in altIds:
                        print '',bookId
                        self.altBooks[bookId] = (record,modName)

    def copyBooks(self):
        """Copies non-Morrowind books to self."""
        skipMods = {'Morrowind.esm', self.fileInfo.name}
        for id,(record,modName) in (self.srcBooks.items() + self.altBooks.items()):
            if modName not in skipMods:
                self.setRecord(copy.copy(record))

    def genLibData(self):
        """Creates new esp with placed refs for lib books. WILL OVERWRITE!"""
        import mush
        tsMain = string.Template(mush.libGenMain)
        tsIfAltId = string.Template(mush.libGenIfAltId)
        #--Data Records
        for id in ('lib_action','lib_actionCount'):
            glob = self.getRecord('GLOB',id,Glob)
            (glob.type, glob.value) = ('s',0)
            glob.setChanged()
        setAllCode  = 'begin lib_setAllGS\n'
        setNoneCode = 'begin lib_setNoneGS\n'
        for libId in self.libList:
            (srcId,altId) = self.libMap[libId]
            srcBook = self.srcBooks.get(srcId)[0]
            if not srcBook:
                print '%s: Missing source: %s' % (libId,srcId)
                continue
            #--Global
            glob = self.getRecord('GLOB',libId+'G',Glob)
            (glob.type, glob.value) = ('s',0)
            glob.setChanged()
            #--Script
            scriptId = libId+'LS'
            script = self.getRecord('SCPT',scriptId,Scpt)
            scriptCode = tsMain.substitute(
                libId=libId, srcId=srcId, ifAltId=(
                    (altId and tsIfAltId.substitute(libId=libId,altId=altId)) or ''))
            script.setCode(scriptCode)
            script.setChanged()
            #--Book
            srcBook.load(unpack=True)
            book = self.getRecord('BOOK',libId,Book)
            book.model = srcBook.model
            book.title = srcBook.title
            book.icon = srcBook.icon
            book.text = srcBook.text
            book.script = scriptId
            book.setChanged()
            #--Set Scripts
            setAllCode  += 'set %sG to 1\n' % (libId,)
            setNoneCode += 'set %sG to 0\n' % (libId,)
        #--Set scripts
        for id,code in (('lib_setAllGS',setAllCode),('lib_setNoneGS',setNoneCode)):
            code += ';--Done\nstopScript %s\nend\n' % (id,)
            script = self.getRecord('SCPT',id,Scpt)
            script.setCode(code)
            script.setChanged()

    def genLibCells(self):
        """Generates standard library """
        #--Cell Records
        objNum = 1
        cellParameters = (
            ('East',270,0,0,0,-6),
            ('North',180,270,90,6,0),
            ('South',0,90,90,-6,0),
            ('West',90,0,180,0,6),)
        for name,rx,ry,rz,dx,dy in cellParameters:
            #--Convert to radians.
            rx, ry, rz = [rot*math.pi/180.0 for rot in (rx,ry,rz)]
            #--Create cell
            cellName = 'BOOKS '+name
            cell = self.getRecord('CELL',cellName,Cell)
            cell.cellName = cellName
            (cell.flags,cell.gridX,cell.gridY) = (1,1,1)
            del cell.objects[:]
            del cell.tempObjects[:]
            tempObjects = cell.tempObjects = []
            for index,libId in enumerate(self.libList):
                srcId = self.libMap[libId][0]
                if srcId not in self.srcBooks: continue
                srData = SubRecord('DATA',24)
                srData.setData(struct.pack('6f',index*dx,index*dy,100,rx,ry,rz))
                tempObjects.append((0,objNum,libId,[Cell_Frmr(),srData]))
                objNum += 1
            cell.setChanged()

    def doImport(self,textFile):
        """Does all the import functions."""
        self.loadText(textFile)
        self.getBooks()
        #self.copyBooks()
        self.genLibData()
        self.genLibCells()
        self.sortRecords()


class FileLists(FileRep):
    """TES3 file representation focussing on levelled lists.

    Only TES3 LEVI and LEVC records are analyzed. All others are left in raw data
    form. """
    def __init__(self, fileInfo, canSave=True):
        FileRep.__init__(self,fileInfo,canSave)
        self.levcs = {}
        self.levis = {}
        self.srcMods = {} #--Used by merge functionality

    def load(self):
        """Load leveled lists from file."""
        canSave = self.canSave
        #--Header
        inPath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        ins = Tes3Reader(self.fileInfo.name,file(inPath,'rb'))
        (name,size,delFlag,recFlag) = ins.unpack('4s3i',16,'REC_HEAD')
        self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        #--Raw data read
        while not ins.atEnd():
            #--Get record info and handle it
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            #--LEVC?
            if name == 'LEVC':
                levc = Levc(name,size,delFlag,recFlag,ins,True)
                self.levcs[levc.id] = levc
                if canSave: self.records.append(levc)
            elif name == 'LEVI':
                levi = Levi(name,size,delFlag,recFlag,ins,True)
                self.levis[levi.id] = levi
                if canSave: self.records.append(levi)
            #--Other
            elif canSave:
                record = Record(name,size,delFlag,recFlag,ins)
                self.records.append(record)
            else: ins.seek(size,1,'Record')
        #--Done Reading
        ins.close()

    def beginMerge(self):
        """Begins merge process. """
        #--Delete existing lists.
        listTypes = {'LEVC', 'LEVI'}
        self.records = [record for record in self.records if record.name not in listTypes]
        self.levcs.clear()
        self.levis.clear()

    def mergeWith(self, newFL):
        """Add lists from another FileLists object."""
        srcMods = self.srcMods
        for levls, newLevls in ((self.levcs,newFL.levcs),(self.levis,newFL.levis)):
            for listId, newLevl in newLevls.items():
                if listId not in srcMods:
                    srcMods[listId] = [newFL.fileInfo.name]
                    levl = levls[listId] = copy.deepcopy(newLevl)
                    self.records.append(levl)
                else:
                    srcMods[listId].append(newFL.fileInfo.name)
                    levls[listId].mergeWith(newLevl)

    def completeMerge(self):
        """Completes merge process. Use this when finished using mergeWith."""
        #--Remove lists that aren't the sum of at least two esps.
        srcMods = self.srcMods
        for levls in (self.levcs,self.levis):
            for listId in levls.keys():
                if len(srcMods[listId]) < 2 or levls[listId].isDeleted:
                    self.records.remove(levls[listId])
                    del levls[listId]
                    del srcMods[listId]
        #--Log
        log = self.log
        for label, levls in (('Creature',self.levcs), ('Item',self.levis)):
            if not len(levls): continue
            log.setHeader(_(u'Merged %s Lists:') % (label,))
            for listId in sorted(levls.keys(),key=lambda a: a.lower()):
                log(listId)
                for mod in srcMods[listId]: log('  '+mod)


class FileScripts(FileRep):
    """TES3 file representation focussing on scripts. Only scripts are analyzed. All other recods are left in raw data form."""

    def __init__(self, fileInfo, canSave=True):
        FileRep.__init__(self,fileInfo,canSave)
        self.scripts = []

    def load(self,factory={}):
        """Load dialogs from file."""
        canSave = self.canSave
        #--Header
        inPath = os.path.join(self.fileInfo.dir,self.fileInfo.name)
        ins = Tes3Reader(self.fileInfo.name,file(inPath,'rb'))
        (name,size,delFlag,recFlag) = ins.unpackRecHeader()
        self.tes3 = Tes3(name,size,delFlag,recFlag,ins,True)
        #--Raw data read
        dial = None
        while not ins.atEnd():
            #--Get record info and handle it
            (name,size,delFlag,recFlag) = ins.unpackRecHeader()
            #--SCPT?
            if name == 'SCPT':
                record = Scpt(name,size,delFlag,recFlag,ins,True)
                self.scripts.append(record)
                if canSave: self.records.append(record)
            #--Non-dials?
            elif canSave:
                record = Record(name,size,delFlag,recFlag,ins)
                self.records.append(record)
            else: ins.seek(size,1,'Record')
        #--Done Reading
        ins.close()

    def save(self,outPath=None):
        """Save data to file.
        outPath -- Path of the output file to write to. Defaults to original file path."""
        if not self.canSave: raise StateError(_(u'Insufficient data to write file.'))
        FileRep.save(self,outPath)

    def loadText(self, textFileName):
        """Replaces dialog text with text read from file."""
        with file(textFileName,'rb') as textFile:
            reHeader = re.compile('^# ([a-zA-Z_0-9]+)')
            id, lines, changed = None, [], []
            id_records = {record.id.lower(): record for record in self.scripts}
            def unBuffer():
                record = id and id_records.get(id.lower())
                if record:
                    code = (''.join(lines)).strip()
                    if code.lower() != record.sctx.data.strip().lower():  # ?
                        record.setCode(code)  # ?x2
                        changed.append(id)
            for line in textFile:
                maHeader = reHeader.match(line)
                if maHeader:
                    unBuffer()
                    id, lines = maHeader.group(1), []
                elif id: lines.append(line)
        unBuffer()
        return sorted(changed, key=string.lower)

    def dumpText(self,textFileName):
        """Dumps dialogs to file."""
        with file(textFileName,'wb') as textFile:
            for script in sorted(self.scripts, key=lambda a: a.id.lower()):
                textFile.write('# %s %s\r\n' % (script.id,'='*(76 - len(script.id))))
                textFile.write(script.sctx.data.strip())
                textFile.write('\r\n\r\n')

# Processing Functions, Classes -----------------------------------------------

class CharSetImporter:
    """Imports CharSets from text file to mod."""
    def __init__(self):
        self.log = Log()
        self.classStats = {}

    def loadText(self,fileName):
        """TextMunch: Reads in 0/30 level settings and spits out a level setting script."""
        #--Constants
        reComment = re.compile(';.*')
        reClassName = re.compile(r'@\s*([a-zA-Z0-9_]+)')
        reStats = re.compile(r'\s*(\d+)\s+(\d+)')
        statNames = ('Agility', 'Block', 'Light Armor', 'Marksman', 'Sneak', 'Endurance', 'Heavy Armor', 'Medium Armor', 'Spear',
                     'Intelligence', 'Alchemy', 'Conjuration', 'Enchant', 'Security', 'Personality', 'Illusion', 'Mercantile',
                     'Speechcraft', 'Speed', 'Athletics', 'Hand To Hand', 'Short Blade', 'Unarmored', 'Strength', 'Acrobatics',
                     'Armorer', 'Axe', 'Blunt Weapon', 'Long Blade', 'Willpower', 'Alteration', 'Destruction', 'Mysticism',
                     'Restoration', 'Luck',)
        #--Read file
        with open(fileName) as inn:
            curStats = className = None
            for line in inn:
                stripped = reComment.sub('',line).strip()
                maClassName = reClassName.match(stripped)
                maStats = reStats.match(stripped)
                if not stripped: pass
                elif maClassName:
                    className = maClassName.group(1)
                    curStats = self.classStats[className] = []
                elif maStats:
                    v00,v30 = [int(stat) for stat in maStats.groups()]
                    curStats.append((v00,v30))
                else: raise MoshError(_(u'Bad line in CharSet class file.') + line.strip() + ' >> ' + stripped)
        #--Post Parse
        for className,stats in self.classStats.items():
            if len(stats) != 35: raise MoshError(_(u'Bad number of stats for class ') + className)
            stats = self.classStats[className] = dict(zip(statNames, stats))
            #--Health
            str00,str30 = stats['Strength']
            end00,end30 = stats['Endurance']
            hea00 = (str00 + end00)/2
            hea30 = (str30 + end30)/2 + end30*29/10
            stats['Health'] = (hea00,hea30)

    def printMajors(self):
        """Print major and minor skills for each class."""
        import mush
        skills = mush.combatSkills+mush.magicSkills+mush.stealthSkills
        for className, stats in sorted(self.classStats.items()):
            print className,'-------------------------------'
            skillStats = [(key,value) for key,value in stats.items() if key in skills]
            skillStats.sort(key=lambda a: a[1][1],reverse=True)
            for low,high in ((0,5),(5,10)):
                for skill,stat in sorted(skillStats[low:high]):
                    print '%-13s  %3d' % (skill,stat[1])
                print

    def save(self,fileInfo):
        """Add charset scripts to esp."""
        fileRep = FileRep(fileInfo)
        fileRep.load(factory={'SCPT':Scpt})
        fileRep.unpackRecords({'SCPT'})
        fileRep.indexRecords({'SCPT'})
        #--Add scripts
        for className in self.classStats.keys():
            print className
            id = 'wr_lev%sGS' % (className,)
            script = fileRep.getRecord('SCPT',id,Scpt)
            script.setCode(self.getScript(className))
        #--Done
        fileRep.sortRecords()
        fileRep.safeSave()

    def getScript(self,className):
        """Get stat setting script for classname."""
        #--Constants
        import mush
        charSet0 = string.Template(mush.charSet0)
        charSet1 = string.Template(mush.charSet1)
        reSpace = re.compile(r'\s+')
        statGroups = (
            ('Primary',mush.primaryAttributes),
            ('Secondary',('Health',)),
            ('Combat Skills',mush.combatSkills),
            ('Magic Skills',mush.magicSkills),
            ('Stealth Skills',mush.stealthSkills))
        #--Dump Script
        stats = self.classStats[className]
        out = cStringIO.StringIO()
        out.write(charSet0.substitute(className=className))
        for group,statNames in statGroups:
            out.write(';--'+group+'\n')
            for statName in statNames:
                shortName = reSpace.sub('',statName)
                v00,v30 = stats[statName]
                if v00 == v30: out.write('set%s %d\n' % (shortName,v00,))
                else:
                    out.write('  set stemp to %d + ((%d - %d)*level/30)\n' % (v00,v30,v00))
                    out.write('set%s stemp\n' % (shortName,))
            out.write('\n')
        out.write(charSet1.substitute(className=className))
        return out.getvalue()


class ScheduleGenerator:
    """Generates schedules from input text files."""
    def __init__(self):
        import mush
        self.log = Log()
        #--Project
        self.project = None
        #--Definitions
        #  defs[key] = string
        self.defs = {}
        self.defs.update(dictFromLines(mush.scheduleDefs,re.compile(r':\s+')))
        #--Code
        #  code[town] = [[lines0],[lines1],[lines2]...]
        #  lines0 used for all cycles
        self.code = {}
        #--Sleep (sleep, lighting, etc.)
        #  sleep[town][cycle] = [(cell1,state1),(cell2,state2),...]
        #  state = '-' (not sleeping), '+' (sleeping)
        self.sleep = {}
        #--Schedule
        #  schedule[town][npc] = [(condition1,[act1,act2,act3,act4]),(condition2,[...])]
        #  actN = (posString,aiString)
        self.schedule = {}
        #--New towns. I.e., towns that just imported.
        self.newTowns = set()
        #--Template Strings
        self.tsMaster = string.Template(mush.scheduleMaster)
        self.tsCycle1 = string.Template(mush.scheduleCycle1)
        self.tsSleep0 = string.Template(mush.scheduleSleep0)
        self.tsSleep1 = string.Template(mush.scheduleSleep1)
        self.tsSleep2 = string.Template(mush.scheduleSleep2)
        self.tsReset0 = string.Template(mush.scheduleReset0)
        self.tsReset1 = string.Template(mush.scheduleReset1)
        self.tsReset2 = string.Template(mush.scheduleReset2)

    #--Schedule
    def loadText(self,fileName,pickScheduleFile=None,imported=None):
        """Read schedule from file."""
        #--Localizing
        defs = self.defs
        log = self.log
        #--Re's
        reCell = re.compile("\s*(\".*?\")")
        reCodeCycle = re.compile("\s*([1-4][ ,1-4]*)")
        reComment = re.compile(r'\s*\#.*')
        reDef = re.compile(r'\.([a-zA-Z]\w+)')
        rePos = re.compile("-?\d+\s+-?\d+\s+-?\d+\s+-?\d+")
        reRepeat = re.compile('= (\d)')
        reSleep = re.compile(r'([=+\-\*\^~x])\s+(.+)$')
        reWander = re.compile('wander +(\d+)')
        reIsMember = re.compile('isMember +(".+")')
        #--Functions/Translators
        replDef = lambda a: defs[a.group(1)]
        #--0: awake, 1: sleep+trespass, 2: sleep 3: dim trespass
        sleepStates = {'=':None,'-':0,'+':1,'*':2,'^':3,'~':4,'x':5}
        #--Log
        header = os.path.split(fileName)[-1]
        if len(header) < 70: header += '='*(70-len(header))
        log.setHeader(header)
        #--Imported
        isTopFile = (imported is None)
        if isTopFile: imported = []
        #--Input variables
        section = None
        town = None
        townNpcs = set()
        townSchedule = None
        npcSchedule = None
        codeCycles = [0]
        #--Parse input file
        with file(fileName) as ins:
            for line in ins:
                #--Strip spaces and comments
                line = reComment.sub('',line)
                line = line.rstrip()
                #--Skip empty/comment lines
                if not line: continue
                #--Section header?
                if line[0] == '@':
                    # (town|defs|night|code|npcName)[: npcCondition]
                    parsed = line[1:].split(':',1)
                    id = parsed[0].strip()
                    #--Non-npc?
                    if id in {'town', 'defs', 'night', 'evening', 'code', 'import', 'project'}:
                        section = id
                        if section in ('evening','night'): townSleep = self.sleep[town]
                        elif section == 'code':
                            cycles = [0]
                            townCode = self.code[town] = [[],[],[],[],[]]
                    else:
                        section = 'npc'
                        npc = id
                        #--Any town,npc combination will overwrite any town,npc
                        #  combination from an imported file.
                        if (town,npc) not in townNpcs:
                            townNpcs.add((town,npc))
                            townSchedule[npc] = []
                        npcSchedule = [0,0,0,0]
                        condition = (len(parsed) == 2 and parsed[1].strip())
                        townSchedule[npc].append((condition,npcSchedule))
                    if section not in {'town', 'import', 'project'}: log('  '+line[1:])
                #--Data
                else:
                    #--Import
                    if section == 'import':
                        newPath = line.strip()
                        log(_(u'IMPORT: ')+newPath)
                        if not os.path.exists(newPath) and pickScheduleFile:
                            caption = "Find sub-import file %s:" % (newPath,)
                            newPath = pickScheduleFile(caption,newPath)
                        if not (newPath and os.path.exists(newPath)):
                            raise StateError(u"Unable to import schedule file: "+line.strip())
                        if newPath.lower() in [dir.lower() for dir in imported]:
                            log(_(u'  [%s already imported.]') % (newPath,))
                        else:
                            log.indent += '> '
                            imported.append(newPath)
                            self.loadText(newPath,pickScheduleFile,imported)
                            log.indent = log.indent[:-2]
                    #--Project
                    elif section == 'project' and isTopFile:
                        self.project = line.strip()
                        log(_('PROJECT: ')+self.project)
                    #--Defs
                    elif section == 'defs':
                        (key,value) = line.strip().split(':',1)
                        defs[key] = value.strip()
                    #--Town
                    elif section == 'town':
                        town = line.strip()
                        log.setHeader(town)
                        if isTopFile: self.newTowns.add(town)
                        if town not in self.schedule:
                            self.schedule[town] = {}
                            self.sleep[town] =  {3:{},4:{}}
                        townSchedule = self.schedule[town]
                        npcSchedule = None
                        codeCycles = []
                    #--Code
                    elif section == 'code':
                        line = reDef.sub(replDef,line)
                        maCodeCycle = reCodeCycle.match(line)
                        if maCodeCycle:
                            codeCycles = [int(x) for x in maCodeCycle.group(1).split(',')]
                            continue
                        for cycle in codeCycles: townCode[cycle].append(line)
                    #--Evening/Night
                    elif section in ('evening','night'):
                        cycle = {'evening':3,'night':4}[section]
                        line = reDef.sub(replDef,line)
                        chunks = [chunk.strip() for chunk in line.split(';')]
                        maSleep = reSleep.match(chunks[0])
                        if not maSleep: continue
                        (cell,defaultState) = (maSleep.group(2), sleepStates[maSleep.group(1)])
                        cellStates = (defaultState,)
                        for chunk in chunks[1:]:
                            chunk = chunk.strip()
                            maSleep = reSleep.match(chunk)
                            if not maSleep or maSleep.group(1) == '=':
                                raise MoshError(_(u'Bad sleep condition state for %s in %s: %s') % (section, town, line))
                            condition,state = maSleep.group(2), sleepStates[maSleep.group(1)]
                            condition = reIsMember.sub(r'getPCRank \1 >= 0',condition)
                            cellStates += ((condition,state),)
                        townSleep[cycle][cell] = cellStates
                    #--NPC
                    elif section == 'npc':
                        #--Get Cycle
                        cycle = int(line[0])
                        rem = line[2:]
                        #--Repeater?
                        maRepeat = reRepeat.match(rem)
                        if maRepeat:
                            oldCycle = int(maRepeat.group(1))
                            npcSchedule[cycle-1] = npcSchedule[oldCycle-1]
                            continue
                        #--Replace defs
                        rem = reDef.sub(replDef,rem)
                        #--Cell
                        maCell = reCell.match(rem)
                        if not maCell: raise MoshError(_(u'Pos cell not defined for %s %s %d') % (town, npc, cycle))
                        cell = maCell.group(1)
                        rem = rem[len(cell):].strip()
                        #--Pos
                        maPos = rePos.match(rem)
                        coords = maPos.group(0).strip().split()
                        coords[-1] = `int(coords[-1])*57` #--Workaround interior rotation bug
                        pos = 'positionCell %s %s' % (' '.join(coords),cell)
                        rem = rem[len(maPos.group(0)):].strip()
                        #--Wander/Travel
                        ai = reWander.sub(r'wander \1 5 10  ',rem)
                        #--Save
                        npcSchedule[cycle-1] = (pos,ai)

    def dumpText(self,fileName):
        """Write schedule to file."""
        with file(fileName,'w') as out:
            for town in sorted(self.towns):
                #--Header
                out.write('; '+town+' '+'='*(76-len(town))+'\n')
                #--Cycle Scripts
                for cycle in [1,2,3,4]:
                    out.write(self.getCycleScript(town,cycle))
                    out.write('\n')
                #--Master, cells scripts
                out.write(self.getSleepScript(town,3))
                out.write('\n')
                out.write(self.getSleepScript(town,4))
                out.write('\n')
                out.write(self.getMasterScript(town))
                out.write('\n')

    def save(self,fileInfo):
        """Add schedule scripts to esp."""
        fileRep = FileRep(fileInfo)
        fileRep.load(factory={'SCPT':Scpt,'DIAL':Dial,'INFO':Info})
        fileRep.unpackRecords({'SCPT'})
        fileRep.indexRecords({'SCPT'})
        #--Add scripts
        def setScript(id,code):
            script = fileRep.getRecord('SCPT',id,Scpt)
            script.setCode(code)
        for town in sorted(self.newTowns):
            #--Cycle Scripts
            for cycle in (1,2,3,4): setScript('SC_%s_%d' % (town,cycle), self.getCycleScript(town,cycle))
            #--Master, sleep scripts
            for cycle in (3,4): setScript('SC_%s_C%d' % (town,cycle), self.getSleepScript(town,cycle))
            setScript('SC_%s_Master' % (town,), self.getMasterScript(town))
        #--Reset Scripts
        if self.project:
            setScript('SC_%s_ResetGS' % (self.project,), self.getResetScript())
            setScript('SC_%s_ResetStatesGS' % (self.project,), self.getResetStatesScript())
        #--Add dialog scripts
        #--Find Hello entries
        recIndex = 0
        records = fileRep.records
        while recIndex < len(records):
            record = records[recIndex]
            recIndex += 1
            if isinstance(record, Dial):
                record.load(unpack=True)
                if record.type == 1 and record.id == 'Hello': break
        #--Sub scripts into hello entries
        reSCInit = re.compile(r'^;--SC_INIT: +(\w+)',re.M)
        while recIndex < len(records):
            record = records[recIndex]
            recIndex += 1
            if record.name != 'INFO': break
            record.load(unpack=True)
            script = record.script
            if not script: continue
            maSCInit = reSCInit.search(script)
            #--No SCInit marker in script?
            if not maSCInit: continue
            town = maSCInit.group(1)
            #--SCInit for uncovered town?
            if town not in self.newTowns: continue
            #--Truncate script and add npc initializers
            script = script[:maSCInit.end()]
            for npc in sorted(self.schedule[town].keys()):
                script += '\r\nset SC_temp to "%s".nolore' % (npc,)
            script += '\r\nset SC_%s_State to -1' % (town,)
            script += '\r\n;messagebox "Initialized %s"' % (town,)
            #--Save changes
            record.script = winNewLines(script)
            record.setChanged()
        #--Done
        fileRep.sortRecords()
        fileRep.safeSave()

    def getResetScript(self):
        """Return SC_[Project]_ResetGS script."""
        if not self.project: raise StateError(_(u'No project has been defined!'))
        text = self.tsReset0.substitute(project=self.project)
        for town in sorted(self.schedule.keys()): text += self.tsReset1.substitute(town=town)
        text += self.tsReset2.substitute(project=self.project)
        return text

    def getResetStatesScript(self):
        """Return SC_[Project]_ResetStatesGS script."""
        if not self.project: raise StateError(_(u'No project has been defined!'))
        text = "begin SC_%s_ResetStatesGS\n" % (self.project,)
        text += ';--Sets state variables for %s project to zero.\n' % (self.project,)
        for town in sorted(self.schedule.keys()):
            text += 'set SC_%s_State to 0\n' % (town,)
        text += "stopScript SC_%s_ResetStatesGS\nend\n" % (self.project,)
        return text

    def getMasterScript(self,town):
        """Return master script for town."""
        c3 = iff(self.sleep[town][3],'',';')
        c4 = iff(self.sleep[town][4],'',';')
        return self.tsMaster.substitute(town=town,c3=c3,c4=c4)

    def getSleepScript(self,town,cycle):
        """Return cells ("C") script for town, cycle."""
        out = cStringIO.StringIO()
        tcSleep = self.sleep[town][cycle]
        #--No cells defined?
        if len(tcSleep) == 0: out.write(self.tsSleep0.substitute(town=town,cycle=cycle))
        else:
            out.write(self.tsSleep1.substitute(town=town,cycle=cycle))
            #--Want to sort so that generic names are last. (E.g. "Vos" after "Vos, Chapel")
            #  But sort also needs to ignore leading and trailing quotes in cell string.
            #  So, compare trimmed cell string, and then reverse sort.
            for cell in sorted(tcSleep.keys(),key=lambda a: a[1:-1],reverse=True):
                cellStates = tcSleep[cell]
                defaultState = cellStates[0]
                out.write('elseif ( getPCCell %s )\n' % (cell,))
                if defaultState is None: continue
                for count,(condition,state) in enumerate(cellStates[1:]):
                    ifString = ['if','elseif'][count > 0]
                    out.write('\t%s ( %s )\n\t\tset SC_Sleep to %s\n' % (ifString,condition,state))
                if len(cellStates) > 1: out.write('\telse\n\t\tset SC_Sleep to %s\n\tendif\n' % (defaultState,))
                else: out.write('\tset SC_Sleep to %s\n' % (defaultState,))
            out.write(self.tsSleep2.substitute(town=town,cycle=cycle))

        return out.getvalue()

    def getCycleScript(self,town,cycle):
        """Return cycle script for town, cycle."""
        #--Schedules
        reWanderCell = re.compile('wander[, ]+(\d+)',re.I)
        rePosCell = re.compile('positionCell +(\-?\d+) +(\-?\d+) +(\-?\d+).+"(.+)"')
        townCode = self.code.get(town,0)
        townSchedule = self.schedule[town]
        npcs = sorted(townSchedule.keys())
        out = cStringIO.StringIO()
        cycleCode = ''
        if townCode:
            for line in townCode[0]+townCode[cycle]: cycleCode += '\t'+line+'\n'
        out.write(self.tsCycle1.substitute(town=town,cycle=`cycle`,cycleCode=cycleCode))
        for npc in npcs:
            out.write('if ( "%s"->getDisabled )\n' % (npc,))
            out.write('elseif ( "%s"->getItemCount SC_offSchedule != 0 )\n' % (npc,))
            for (condition,npcSchedule) in townSchedule[npc]:
                if not condition: out.write('else\n')
                else: out.write('elseif ( %s )\n' % (condition,))
                (pos,ai) = npcSchedule[cycle-1]
                out.write('\tif ( action < 20 )\n')
                out.write('\t\t"%s"->%s\n' % (npc,pos))
                if ai != 'NOAI':
                    #--Wandering in exterior cell?
                    maWanderCell = reWanderCell.match(ai)
                    maPosCell = rePosCell.match(pos)
                    if maWanderCell and (int(maWanderCell.group(1)) > 0) and (maPosCell.group(4).find(',') == -1):
                        xx,yy,zz,cell = maPosCell.groups()
                        out.write('\t\t"%s"->aiTravel %s %s %s\n' % (npc,xx,yy,zz))
                        out.write('\t\tset action to 10\n\telse\n')
                    out.write('\t\t"%s"->ai%s\n' % (npc,ai))
                out.write('\tendif\n')
            out.write('endif\n')
        out.write("if ( action != 10 )\n\tset action to 20\nendif\n")
        out.write('end\n')
        return out.getvalue()

# Initialization ------------------------------------------------------------------------ #
#-# First modified by D.C.-G. - Changed by Polemos to be an override.
#-#
#-# Avoiding error return on installers path creation not allowed.
#-# D.C.-G.: I implemented this because my installers directory is on a remote drive ;-)
#-# ==>> ONLY FOR WINDOWS
#-# Errors skipped:
#-#   * path not accessible physically (missing drive or unacceptable URL);
#-#   * the user does not have the rights to write in the destination folder.
# --------------------------------------------------------------------------------------- #

def defaultini():  # Polemos: The default ini.
    """Create mash_default.ini if none exists."""
    default_ini = (u';--This is the generic version of Mash.ini. If you want to set values here,\n'
                   u';  then copy this to "mash.ini" and edit as desired.\n'
                   u';Use mash.ini as an override when you need the Installers dir in a remote or relative location.\n'
                   u'[General]\n'
                   u';--sInstallersDir is the Alternate root directory for installers, etc. You can\n'
                   u';  use absolute path (c:\Games\Morrowind Mods) or relative path where the path\n'
                   u';  is relative to Morrowind install directory.\n'
                   u'sInstallersDir=Installers ;--Default\n'
                   u';sInstallersDir=..\Morrowind Mods\Installers ;--Alternate')
    try:
        with io.open('mash_default.ini', 'w', encoding='utf-8') as f:
            f.write(default_ini)
    except: pass

def DCGremote():  # Polemos just optimised to avoid code repeats.
    """Remote drive error skipping."""
    if sys.platform.lower().startswith("win"):
        drv, pth = os.path.splitdrive(dirs['installers'].s)
        if os.access(drv, os.R_OK):
            dirs['installers'].makedirs()

def initDirs():  # Polemos fixes, changes + OpenMW/TES3mp support
    """Init directories. Assume that settings has already been initialized."""
    if not settings['openmw']:  # Regular Morrowind
        dirs['app'] = GPath(settings['mwDir'])
        dirs['mods'] = dirs['app'].join('Data Files')

        dirs['installers'] = GPath(settings['sInstallersDir'])
        DCGremote()
        # Polemos: Mash.ini produces more problems than benefits. Removed for now.
        '''if GPath('mash.ini').exists():  # Mash.ini override
            mashini_read()
        else:
            dirs['installers'] = GPath(settings['sInstallersDir'])
            DCGremote()'''

    if settings['openmw']:  # OpenMW/TES3mp support
        dirs['app'] = GPath(settings['openmwDir'])
        dirs['mods'] = GPath(settings['datamods'])
        dirs['installers'] = GPath(settings['downloads'])
        DCGremote()

def mashini_read():  # Polemos: Make mash.ini an override.
    """Read Mash.ini and get installers loc. It overrides settings.pkl"""
    # Polemos: Mash.ini produces more problems than benefits. Deactivated for now.
    defaultini()

    installers_set = settings['sInstallersDir']
    mashIni = None

    if os.path.exists(os.path.join(MashDir, 'mash.ini')):
        import ConfigParser
        mashIni = ConfigParser.ConfigParser()
        try:
            with io.open('mash.ini', 'r', encoding='utf-8') as f:
                mashIni.readfp(f)
        except: pass

    if mashIni:
        if mashIni.has_option('General', 'sInstallersDir'):
            installers = GPath(mashIni.get('General', 'sInstallersDir').strip())
    else: installers = GPath(installers_set)

    if installers.isabs(): dirs['installers'] = installers
    else: dirs['installers'] = dirs['app'].join(installers)

    DCGremote()

def initSettings(path='settings.pkl'):
    global settings
    settings = Settings(path)
    reWryeMash = re.compile('^wrye\.mash')
    for key in settings.data.keys():
        newKey = reWryeMash.sub('mash',key)
        if newKey != key:
            settings[newKey] = settings[key]
            del settings[key]
    settings.loadDefaults(settingDefaults)

# Main ------------------------------------------------------------------------ #
if __name__ == '__main__': print 'Compiled'
