# -*- coding: utf-8 -*-

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

# GPL License and Copyright Notice ============================================
#
#  Wrye Bolt is free software; you can redistribute it and/or
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
#  along with Wrye Bolt; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bolt copyright (C) 2005, 2006, 2007, 2008, 2009 Wrye
#
# =============================================================================


import cPickle
from unimash import _  # Polemos
import os
import re
import shutil
import struct
import sys
import time
from types import *
from zlib import crc32
import io, stat, scandir, ushlex, thread, xxhash  # Polemos
from subprocess import PIPE, check_call  # Polemos: KEEP => check_call <= !!
from sfix import Popen  # Polemos
import compat
# Exceptions
from merrors import mError as BoltError
from merrors import AbstractError as AbstractError, ArgumentError as ArgumentError, StateError as StateError
from merrors import UncodedError as UncodedError, ConfError as ConfError


# Constants
MashDir = os.path.dirname(sys.argv[0])
DETACHED_PROCESS = 0x00000008  # Polemos: No console window.
_gpaths = {}

# LowStrings

class LString(object):
    """Strings that compare as lower case strings."""
    __slots__ = ('_s', '_cs')

    def __init__(self,s):
        if isinstance(s,LString): s = s._s
        self._s = s
        self._cs = s.lower()

    def __getstate__(self):
        """Used by pickler. _cs is redundant,so don't include."""
        return self._s

    def __setstate__(self,s):
        """Used by unpickler. Reconstruct _cs."""
        self._s = s
        self._cs = s.lower()

    def __len__(self):
        return len(self._s)

    def __str__(self):
        return self._s

    def __repr__(self):
        return "bolt.LString(%s)" % repr(self._s)

    def __add__(self,other):
        return LString(self._s + other)

    def __hash__(self):
        """Hash"""
        return hash(self._cs)

    def __cmp__(self, other):
        """Compare"""
        if isinstance(other,LString): return cmp(self._cs, other._cs)
        else: return cmp(self._cs, other.lower())

# Paths ----------------------------------------------------------------------- #

def GPath(name):
    """Returns common path object for specified name/path."""
    if name is None: return None
    elif not name: norm = name
    elif isinstance(name,Path): norm = name._s
    else: norm = os.path.normpath(name)
    path = _gpaths.get(norm)
    if path is not None: return path
    else: return _gpaths.setdefault(norm,Path(norm))


class Path(object): # Polemos: Unicode fixes.
    """A file path. May be just a directory, filename or full path.
    Paths are immutable objects that represent file directory paths."""
    #--Class Vars/Methods
    norm_path = {} #--Dictionary of paths
    mtimeResets = [] #--Used by getmtime

    @staticmethod
    def get(name):
        """Returns path object for specified name/path."""
        name.encode('utf-8')
        if isinstance(name,Path): norm = name._s
        else: norm = os.path.normpath(name)
        return Path.norm_path.setdefault(norm,Path(norm))

    @staticmethod
    def getNorm(name):  # Sharlikran's commit for Python 2.7.8
        """Return the normpath for specified name/path object."""
        if isinstance(name,Path): return name._s
        elif not name: return name
        else: return os.path.normpath(name)

    @staticmethod
    def getCase(name):
        """Return the normpath+normcase for specified name/path object."""
        if not name: return name
        if isinstance(name,Path): return name._cs
        else: return os.path.normcase(os.path.normpath(name))

    @staticmethod
    def getcwd():
        return Path(os.getcwd().encode('utf-8'))

    def setcwd(self):
        """Set cwd. Works as either instance or class method."""
        if isinstance(self, Path): dir = self._s.encode('utf-8')
        else: dir = self
        os.chdir(dir)

    #--Instance stuff --------------------------------------------------
    #--Slots: _s is normalized path. All other slots are just pre-calced variations of it.
    __slots__ = ('_s', '_cs','_csroot','_sroot','_shead','_stail','_ext','_cext')

    def __init__(self, name):
        """Initialize."""
        if isinstance(name, Path): self.__setstate__(name._s)
        elif type(name) is unicode: self.__setstate__(name)
        else: self.__setstate__(str(name))

    def __getstate__(self):
        """Used by pickler. _cs is redundant,so don't include."""
        return self._s

    def __setstate__(self, norm):
        """Used by unpickler. Reconstruct _cs."""
        self._s = norm
        self._cs = os.path.normcase(norm)
        self._sroot,self._ext = os.path.splitext(norm)
        self._shead,self._stail = os.path.split(norm)
        self._cext = os.path.normcase(self._ext)
        self._csroot = os.path.normcase(self._sroot)

    def __len__(self):
        return len(self._s)

    def __repr__(self):
        return "bolt.Path(%s)" % `self._s`

    #--Properties--------------------------------------------------------
    #--String/unicode versions.
    @property
    def s(self):
        """Path as string."""
        return self._s

    @property
    def cs(self):
        """Path as string in normalized case."""
        return self._cs

    @property
    def csroot(self):
        """Root as string."""
        return self._csroot

    @property
    def sroot(self):
        """Root as string."""
        return self._sroot

    @property
    def shead(self):
        """Head as string."""
        return self._shead

    @property
    def stail(self):
        """Tail as string."""
        return self._stail

    #--Head, tail
    @property
    def headTail(self):
        """For alpha\beta.gamma returns (alpha,beta.gamma)"""
        return map(GPath,(self._shead,self._stail))

    @property
    def head(self):
        """For alpha\beta.gamma, returns alpha."""
        return GPath(self._shead)

    @property
    def tail(self):
        """For alpha\beta.gamma, returns beta.gamma."""
        return GPath(self._stail)

    #--Root, ext
    @property
    def rootExt(self):
        return (GPath(self._sroot),self._ext)

    @property
    def root(self):
        """For alpha\beta.gamma returns alpha\beta"""
        return GPath(self._sroot)

    @property
    def ext(self):
        """Extension (including leading period, e.g. '.txt')."""
        return self._ext

    @property
    def cext(self):
        """Extension in normalized case."""
        return self._cext

    @property
    def temp(self):
        """Temp file path.."""
        return self+'.tmp'

    @property
    def backup(self):
        """Backup file path."""
        return self+'.bak'

    #--size, atim, ctime
    @property
    def size(self): # Polemos: os.path.getsize -> os.stat().st_size
        """Size of file."""
        return os.stat(self._s).st_size

    @property
    def atime(self):
        return os.path.getatime(self._s)

    @property
    def ctime(self):
        return os.path.getctime(self._s)

    def getmtime(self):  #  Polemos: Does the Y2038 bug still exist in Python 2.7.15? Todo: Check for Y2038 bug.
        """Returns mtime for path. But if mtime is outside of epoch, then resets mtime to an in-epoch date and uses that."""
        mtime = int(os.path.getmtime(self._s))
        #--Y2038 bug? (os.path.getmtime() can't handle years over unix epoch)
        if mtime <= 0:
            import random
            #--Kludge mtime to a random time within 10 days of 1/1/2037
            mtime = time.mktime((2037,1,1,0,0,0,3,1,0))
            mtime += random.randint(0,10*24*60*60) #--10 days in seconds
            self.mtime = mtime
            Path.mtimeResets.append(self)
        return mtime
    def setmtime(self,mtime): os.utime(self._s,(self.atime,int(mtime)))
    mtime = property(getmtime,setmtime,doc="Time file was last modified.")

    @property
    def xxh(self):  # Polemos
        """Calculates and returns xxhash value for self."""
        xxhs = xxhash.xxh32()
        with self.open('rb', 65536) as ins:
            for x in xrange((self.size / 65536) + 1):
                xxhs.update(ins.read(65536))
        return xxhs.intdigest()

    @property
    def crc(self):  # Polemos: Optimized. It went from 23 sec to 6 sec in a 6700k system.
        """Calculates and returns crc value for self."""
        if conf.settings['advanced.7zipcrc32'] and self.size > 16777216:
            #  7z is faster on big files
            args = ushlex.split('7z.exe h "%s"' % self.s)
            ins = Popen(args, bufsize=-1, stdout=PIPE, creationflags=DETACHED_PROCESS)
            return int([x for x in ins.stdout][14].split(':')[1], 16)
        crc = 0L
        with self.open('rb', 65536) as ins:
            for x in xrange((self.size / 65536) + 1):
                crc = crc32(ins.read(65536), crc)
        return crc if crc > 0 else 4294967296L + crc

    #--Path stuff -------------------------------------------------------
    #--New Paths, subpaths
    def __add__(self,other):
        return GPath(self._s + Path.getNorm(other))

    def join(*args):
        norms = [Path.getNorm(x) for x in args]
        return GPath(os.path.join(*norms))

    def list(self):
        """For directory: Returns list of files."""
        if not os.path.exists(self._s): return []
        return [GPath(x) for x in scandir.listdir(self._s)]  # Pol: Seems better.

    def walk(self,topdown=True,onerror=None,relative=False):
        """Like os.walk."""
        if relative:
            start = len(self._s)
            return ((GPath(x[start:]),[GPath(u) for u in y],[GPath(u) for u in z])
                for x,y,z in scandir.walk(topdown,onerror))  # Polemos: replaced os.walk which is slow in Python 2.7 and below.
        else:
            return ((GPath(x),[GPath(u) for u in y],[GPath(u) for u in z])
                for x,y,z in scandir.walk(topdown,onerror))  # See above.

    #--File system info
    #--THESE REALLY OUGHT TO BE PROPERTIES.
    def exists(self): return os.path.exists(self._s)
    def isdir(self): return os.path.isdir(self._s)
    def isfile(self): return os.path.isfile(self._s)
    def isabs(self): return os.path.isabs(self._s)

    #--File system manipulation
    def open(self,*args):
        """Open a file function."""
        if self._shead and not os.path.exists(self._shead):
            os.makedirs(self._shead)
        return open(self._s,*args)

    def codecs_open(self,*args):  # Polemos: a new manipulation.
        """Open a unicode file function."""
        if self._shead and not os.path.exists(self._shead):
            os.makedirs(self._shead)
        return io.open(self._s, *args, encoding="utf-8")

    def makedirs(self):
        """Create dir function."""
        if not self.exists(): os.makedirs(self._s)

    def remove(self):  # Polemos fix
        """Remove function."""
        if self.exists():
            try: os.remove(self._s)
            except: self.undeny(self._s, action='os.remove')

    def removedirs(self):
        """Remove dir function."""
        if self.exists(): os.removedirs(self._s)

    def rmtree(self,safety='PART OF DIRECTORY NAME'): # Polemos fix: shutil.rmtree has a bug in 2.7. Delay to try to bypass.
        """Removes directory tree. As a safety factor, a part of the directory name must be supplied."""
        if self.isdir() and safety and safety.lower() in self._cs:
            for x in range(3):  # Drizzt tries.
                try:
                    shutil.rmtree(self._s, onerror=self.undeny_1err)
                    break
                except OSError: time.sleep(2)
            # if self.isdir(): self.message_po((u'Error: Access denied.\n\nCannot delete %s.' % (self._s))) #
            # Polemos: Looks nice to have, ain't it? Don't try it, seriously don't.                         #

    #--start, move, copy, touch, untemp
    def start(self):  # Polemos fix
        """Starts file as if it had been double clicked in file explorer."""
        try: os.startfile(self._s)
        except: pass  # Todo: Add a msg to inform user

    def copyTo(self, destName):  # Polemos fix
        """Copy function."""
        destName = GPath(destName)
        if self.isdir(): shutil.copytree(self._s, destName._s)
        else:
            if destName._shead and not os.path.exists(destName._shead):
                os.makedirs(destName._shead)
            try: shutil.copyfile(self._s, destName._s)
            except: pass
            destName.mtime = self.mtime

    def renameTo(self, destName):  # Polemos
        """Rename function."""
        destName = GPath(destName)
        try: os.rename(self._s, destName._s)
        except: return False
        if not self.isdir():
            try: destName.mtime = self.mtime
            except: pass
        return True

    def moveTo(self,destName):  # Polemos fix
        """Move function."""
        destPath = GPath(destName)
        if destPath._cs == self._cs: return
        if destPath._shead and not os.path.exists(destPath._shead):
            os.makedirs((destPath._shead))
        elif destPath.exists():
            try: os.remove(destPath._s)
            except: self.undeny(destPath._s, action='os.remove')
        try: shutil.move(self._s,destPath._s)
        except: pass

    def touch(self):
        """Like unix 'touch' command. Creates a file with current date/time."""
        if self.exists(): self.mtime = time.time()
        else:
            self.temp.open('w').close()
            self.untemp()

    def untemp(self,doBackup=False):  # Polemos fix
        """Replaces file with temp version, optionally making backup of file first."""
        if self.exists():
            if doBackup:
                self.backup.remove()
                shutil.move(self._s, self.backup._s)
            else:
                try: os.remove(self._s)
                except: self.undeny(self._s, action='os.remove')
        shutil.move(self.temp._s, self._s)

    def message_po(self, message=None):  # Polemos:  Not implemented.
        """Custom messaging."""
        import gui.dialog
        if message is None:
            message = _(u'Errors occurred during file operations.\nTry running Wrye Mash with Admin rights.')
        gui.dialog.ErrorMessage(None, _(message))
        return

    def undeny(self, path, destdir=None, action=None):  # Polemos.
        """Remove Read only attribute."""
        def write_on(path):
            try: os.chmod(path, stat.S_IWRITE)                # Part pythonic,
            except: check_call(ur'attrib -R %s /S' % (path))  # part hackish (Yeah I know).
        try:
            write_on(path)
            if action is None: return
            elif action == 'os.remove': os.remove(path)
            elif action == 'shutil.move': shutil.move(path, destdir)  # Not implemented.
        except:
            pass  # self.message_po(_(u'Error: Access denied.\nTry running Wrye Mash with Admin rights.')) #
                  # Polemos: Nope, nope... nope...                                                         #

    def undeny_1err(self, func, path, _): # Polemos
        """Remove readonly, and retry..."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

# Polemos: Special Methods Magic from Wrye Bash 307 Beta2.
# --Hash/Compare, based on the _cs attribute so case insensitive. NB: Paths
    # directly compare to basestring and Path and will blow for anything else
    def __hash__(self): return hash(self._cs)

    def __eq__(self, other):
        if isinstance(other, Path): return self._cs == other._cs
        else: return self._cs == Path.getCase(other)

    def __ne__(self, other):
        if isinstance(other, Path): return self._cs != other._cs
        else: return self._cs != Path.getCase(other)

    def __lt__(self, other):
        if isinstance(other, Path): return self._cs < other._cs
        else: return self._cs < Path.getCase(other)

    def __ge__(self, other):
        if isinstance(other, Path): return self._cs >= other._cs
        else: return self._cs >= Path.getCase(other)

    def __gt__(self, other):
        if isinstance(other, Path): return self._cs > other._cs
        else: return self._cs > Path.getCase(other)

    def __le__(self, other):
        if isinstance(other, Path): return self._cs <= other._cs
        else: return self._cs <= Path.getCase(other)


# Util Constants --------------------------------------------------------------
#--Unix new lines
reUnixNewLine = re.compile(r'(?<!\r)\n')

# Util Classes ----------------------------------------------------------------

class CsvReader:
    """For reading csv files. Handles both command tab separated (excel) formats."""
    def __init__(self,path):
        import csv
        self.ins = path.open('rb')
        format = ('excel','excel-tab')['\t' in self.ins.readline()]
        self.ins.seek(0)
        self.reader = csv.reader(self.ins,format)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next()

    def close(self):
        self.reader = None
        self.ins.close()

#------------------------------------------------------------------------------

class Flags(object):
    """Represents a flag field."""
    __slots__ = ['_names','_field']

    @staticmethod
    def getNames(*names):
        """Returns dictionary mapping names to indices.
        Names are either strings or (index,name) tuples.
        E.g., Flags.getNames('isQuest','isHidden',None,(4,'isDark'),(7,'hasWater'))"""
        namesDict = {}
        for index,name in enumerate(names):
            if type(name) is tuple:
                namesDict[name[1]] = name[0]
            elif name: #--skip if "name" is 0 or None
                namesDict[name] = index
        return namesDict

    #--Generation
    def __init__(self,value=0,names=None):
        """Initialize. Attrs, if present, is mapping of attribute names to indices. See getAttrs()"""
        object.__setattr__(self,'_field',int(value) | 0L)
        object.__setattr__(self,'_names',names or {})

    def __call__(self,newValue=None):
        """Retuns a clone of self, optionally with new value."""
        if newValue is not None:
            return Flags(int(newValue) | 0L,self._names)
        else: return Flags(self._field,self._names)

    def __deepcopy__(self, memo=None):
        if memo is None: memo = {}
        newFlags=Flags(self._field,self._names)
        memo[id(self)] = newFlags
        return newFlags

    #--As hex string
    def hex(self):
        """Returns hex string of value."""
        return '%08X' % (self._field,)
    def dump(self):
        """Returns value for packing"""
        return self._field

    #--As int
    def __int__(self):
        """Return as integer value for saving."""
        return self._field

    #--As list
    def __getitem__(self, index):
        """Get value by index. E.g., flags[3]"""
        return bool((self._field >> index) & 1)

    def __setitem__(self,index,value):
        """Set value by index. E.g., flags[3] = True"""
        value = ((value or 0L) and 1L) << index
        mask = 1L << index
        self._field = ((self._field & ~mask) | value)

    #--As class
    def __getattr__(self,name):
        """Get value by flag name. E.g. flags.isQuestItem"""
        try:
            names = object.__getattribute__(self,'_names')
            index = names[name]
            return (object.__getattribute__(self,'_field') >> index) & 1 == 1
        except KeyError: raise AttributeError(name)

    def __setattr__(self,name,value):
        """Set value by flag name. E.g., flags.isQuestItem = False"""
        if name in ('_field','_names'):
            object.__setattr__(self,name,value)
        else: self.__setitem__(self._names[name],value)

    #--Native operations
    def __eq__( self, other):
        """Logical equals."""
        if isinstance(other, Flags):
            return self._field == other._field
        else: return self._field == other

    def __ne__( self, other):
        """Logical not equals."""
        if isinstance(other, Flags):
            return self._field != other._field
        else: return self._field != other

    def __and__(self,other):
        """Bitwise and."""
        if isinstance(other, Flags): other = other._field
        return self(self._field & other)

    def __invert__(self):
        """Bitwise inversion."""
        return self(~self._field)

    def __or__(self,other):
        """Bitwise or."""
        if isinstance(other,Flags): other = other._field
        return self(self._field | other)

    def __xor__(self,other):
        """Bitwise exclusive or."""
        if isinstance(other, Flags): other = other._field
        return self(self._field ^ other)

    def getTrueAttrs(self):
        """Returns attributes that are true."""
        trueNames = [name for name in self._names if getattr(self,name)]
        trueNames.sort(key = lambda xxx: self._names[xxx])
        return tuple(trueNames)


class DataDict:
    """Mixin class that handles dictionary emulation, assuming that dictionary has the 'data' attribute."""

    def __contains__(self,key):
        return key in self.data
    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key] = value
    def __delitem__(self,key):
        del self.data[key]
    def __len__(self):
        return len(self.data)
    def setdefault(self,key,default): # Polemos fix
        return self.data.setdefault(key,default)
    def keys(self):
        return self.data.keys()
    def values(self):
        return self.data.values()
    def items(self):
        return self.data.items()
    def has_key(self,key):
        return self.data.has_key(key)
    def get(self,key,default=None):
        return self.data.get(key,default)
    def pop(self,key,default=None):
        return self.data.pop(key,default)
    def iteritems(self):
        return self.data.iteritems()
    def iterkeys(self):
        return self.data.iterkeys()
    def itervalues(self):
        return self.data.itervalues()

#------------------------------------------------------------------------------

class RemoveTree:  # Polemos
    """FileTree removal actions."""

    def __init__(self, tree):
        """Init."""
        if any([type(tree) is str, type(tree) is unicode]): tree = (tree,)
        self.rmTree(tree)

    def undeny(self, func, path, _):
        """Remove readonly, and retry..."""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except:  pass


    def rmTree(self, tree):
        """Remove Tree."""
        for branch in tree:
            if branch == '\\': break  # Polemos: You never know.
            if os.path.isdir(branch):
                for tries in range(3):
                    try:
                        shutil.rmtree(branch, onerror=self.undeny)
                        break
                    except: time.sleep(2)

#------------------------------------------------------------------------------

class MetaStamp:  # Polemos
    """Metafile creation."""

    def __init__(self, target_dir, package_name_data):
        """Init."""
        self.target_dir = target_dir
        self.metafile = os.path.join(target_dir, 'mashmeta.inf')
        self.Installer = package_name_data[2]
        self.Version = '' if not package_name_data[4] else package_name_data[4]
        self.Repo = 'Nexus' if package_name_data[3] else ''
        self.ID = package_name_data[3]
        self.MetaCreate()

    def MetaCreate(self):
        """Create mod metafile."""
        metatext = (u'[General]',
                    u'Installer=%s' % self.Installer,
                    u'Version=%s' % self.Version,
                    u'NoUpdateVer=',
                    u'NewVersion=',
                    u'Category=',
                    u'Repo=%s' % self.Repo,
                    u'ID=%s' % self.ID)
        tries = 0
        while tries != 3:
            if os.path.isfile(self.metafile): break
            try:
                with io.open(self.metafile, 'w', encoding='utf-8') as f:
                    f.write('\r\n'.join(metatext))
            except:
                tries += 1
                time.sleep(0.3)

#------------------------------------------------------------------------------

class MetaParse:  # Polemos
    """Metafile parsing."""
    Data = []

    def __init__(self, metadir):
        """Init."""
        metafile = os.path.join(metadir, 'mashmeta.inf')
        if not os.path.isfile(metafile): return
        self.Data = self.MetaRead(metafile)

    def metaScan(self, metafile):
        """Read metafile contents."""
        with io.open(metafile, 'r', encoding='utf-8') as f:
            return f.readlines()

    def MetaRead(self, metafile):
        """Parse mod metafile."""
        data = {u'Installer':'',
                  u'Version':'',
                  u'NoUpdateVer':'',
                  u'NewVersion':'',
                  u'Category':'',
                  u'Repo':'',
                  u'ID':''}
        reList = re.compile(u'(Installer|Version|NoUpdateVer|NewVersion|Category|Repo|ID)=(.+)')
        metadata = self.metaScan(metafile)[:]
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

#------------------------------------------------------------------------------

class ModInstall:  # Polemos
    """File tree manipulations."""

    def __init__(self, parent, mod_name, modsfolder, source_dir, target_dir, filesLen):
        """Init."""
        self.parent = parent
        self.mod_name = mod_name
        self.modsfolder = modsfolder
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.filesLen = filesLen
        self.chkStatus()

    def doAction(self):
        """Set action route."""
        if self.actionData[0]:  # Backup existing mod
            if not self.backup(): return
        if self.actionData[1] != self.mod_name:  # Rename mod
            if self.actionData[1] == '':
                self.error('rename')
                return
            self.mod_name = self.actionData[1]
            self.target_dir = os.path.join(self.modsfolder, self.mod_name)
            self.doAction()
            return
        if self.actionData[2] == 'rename': self.simpleInstall()
        if self.actionData[2] == 'overwrite': self.overwrite()
        if self.actionData[2] == 'replace': self.replace()

    def error(self, error):
        """Notify user of errors."""
        import gui.dialog as gui
        if error == 'backup':
            msg = _(u'Error: Unable to backup existing mod folder!!!\n\nInstallation was aborted, no actions were taken.')
        elif error == 'install':
            msg = _(u'Error: Could not finish installation!!!\n\nInstallation was aborted.')
        elif error == 'rename':
            msg = _(u'Error: An invalid mod name was supplied!!!\n\nInstallation was aborted, no actions were taken.')
        elif error == 'overwrite':
            msg = _(u'Error: Unable to merge mods!!!\n\nInstallation was aborted.')
        elif error == 'replace':
            msg = _(u'Error: Unable to delete existing mod folder!!!\n\nInstallation was aborted.')
        gui.ErrorMessage(self.parent, msg)

    def chkStatus(self):
        """Check folder conditions."""
        if os.path.isdir(self.target_dir):
            self.showgui()
            return
        self.simpleInstall()

    def simpleInstall(self):
        """Simple Installation."""
        try: self.copyMod()
        except: self.error('install')

    def copyMod(self, source_dir=None, target_dir=None):
        """Multithread Copy ops."""
        import gui.dialog as gui
        if source_dir is not None: self.source_dir = source_dir
        if target_dir is not None:  self.target_dir = target_dir
        self.dialog = gui.GaugeDialog(self.parent, title=_(u'Installing...'), max=self.filesLen)
        self.dialog.set_msg(_(u'Installing...'))
        self.progress()  # todo: make modal
        thread.start_new_thread(self.treeOp, ('treeOpThread',))

    def treeOp(self, id):
        """Files/Folders operations."""
        source_dir = self.source_dir
        target_dir = self.target_dir
        if not os.path.isdir(self.target_dir): os.makedirs(self.target_dir)
        num = 0
        for root, dirs, files in scandir.walk(source_dir, topdown=False):
            for fname in files:
                num += 1
                self.dialog.update(num)
                relsource = os.path.relpath(root, source_dir)
                if relsource == '.': relsource = ''
                source = os.path.join(root, fname)
                target = os.path.join(target_dir, relsource, fname)
                target_file_dir = os.path.join(target_dir, relsource)
                if not os.path.isdir(target_file_dir): os.makedirs(target_file_dir)
                buffer = min(10485760, os.path.getsize(source))
                if (buffer == 0): buffer = 1024
                with open(source, 'rb') as fsource:
                    with open(target, 'wb') as fdest:
                        shutil.copyfileobj(fsource, fdest, buffer)
                try: os.remove(source)
                except: pass
            try: os.rmdir(root)
            except: pass
        self.dialog.update(self.filesLen)
        self.dialog.set_msg(_(u'Finished...'))
        time.sleep(2)  # Give some time for system file caching.
        self.dialog.Destroy()

    def progress(self):
        """Progress indicator."""
        self.dialog.Show()

    def overwrite(self):
        """Merge folders."""
        try: self.copyMod()
        except: self.error('overwrite')

    def replace(self):
        """Replace folder."""
        def undeny(func, path, _):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except: os.system(r'attrib -R "%s" /S' % path)
        try: shutil.rmtree(self.target_dir, onerror=undeny)
        except: self.error('replace')
        self.simpleInstall()

    def backup(self):
        """Make a backup of old dir."""
        try:
            ID = 0
            while True:
                if ID == 0: ID = ''
                NewDirName = '%s%s%s' % (self.target_dir, 'backup', ID)
                if not os.path.isdir(NewDirName):
                    if self.actionData[2] == 'replace': os.rename(self.target_dir, NewDirName)
                    elif self.actionData[2] == 'overwrite': self.copyMod(self.target_dir, NewDirName)
                    break
                if not ID: ID = 0
                ID += 1
        except:
            self.error('backup')
            return False
        return True

    def showgui(self):
        """Dialog processor."""
        import gui.dialog as gui
        self.actionData = gui.ConflictDialog(self.parent, self.mod_name).GetData
        if not self.actionData: return
        if self.actionData[2] == 'rename':
            if os.path.isdir(os.path.join(self.modsfolder, self.actionData[1])):
                self.showgui()
                return
        self.doAction()

#------------------------------------------------------------------------------

class ModNameFactory:  # Polemos
    """Extract info from modname (if any) and return Mod Name data."""
    getModName = []

    def __init__(self, mod):
        """Init."""
        self.mod = mod
        self.factory()

    def cleanPath(self, mod):
        """Remove file path."""
        return os.path.basename(mod.lower().rstrip('\\'))

    def cleanExt(self, mod):
        """Remove extension."""
        exts = ['.7z', '.zip', '.rar']
        for num, ext in enumerate(exts):
            if mod.lower().endswith(ext):
                return mod.rstrip(ext)

    def getNexus(self, mod):
        """Get Nexus info from mod."""
        modparts = mod.split('-')
        modNexus, modName = False, False
        for part in modparts:
            if len(part) == 5:
                try: modNexus, modstr = int(part), part
                except: continue
        if modNexus:
            modtmp = mod.replace(modstr, '<;>').split('<;>')
            modName, modVer = modtmp[0], modtmp[1]
            if modVer.startswith('-'): modVer = modVer.lstrip('-').replace('-', '.')
            modVer = modVer.replace('-', '.').replace('_', '.')
            if modName.endswith('-'): modName = modName.rstrip('-')
        else: modVer = False
        return modName, modNexus, modVer

    def factory(self):
        """Modname analysis."""
        modNoPath = self.cleanPath(self.mod)
        modNoExt = self.cleanExt(modNoPath)
        modName, modNexus, modVer = self.getNexus(modNoExt)
        self.getModName = (modName, modNoExt, modNoPath, modNexus, modVer)

#------------------------------------------------------------------------------

class DataFilesDetect:  # Polemos
    """Detect Data Files root from package."""
    data_files = None
    common_folders = ['bookart', 'fonts', 'icons', 'meshes', 'music', 'shaders', 'sound', 'splash', 'textures', 'video', 'mwse', 'distantland']

    def __init__(self, package_paths, max_depth, mw_files):
        """Init."""
        self.package_paths = package_paths
        self.max_depth = max_depth
        self.mw_files = mw_files

    def TreeFactory(self, data_files):
        """Create path from data."""
        if not data_files: return ('',('root', '\\', -1))
        if data_files[0][2] == 0: return (data_files[0][1], ('\\', data_files[0][1], 0))
        result = [data_files[0][1]]
        for x in self.package_paths:
            if (x[1], x[2]) == (data_files[0][0], data_files[0][2]-1):
                result.append(x[1])
        result.reverse()
        return (os.path.join('', *result), data_files)

    def getDataFiles(self):
        """Return Data Files or None."""
        # No folders in Package root?
        root_folders = [x for x in self.package_paths if x[2] == 0]
        if len(root_folders) == 0:
            return self.TreeFactory(root_folders)
        # Is there a "Data Files" dir?
        data_files = [x for x in self.package_paths if x[1].lower() == 'Data Files'.lower()]
        if all([data_files, len(data_files) == 1]):
            return self.TreeFactory(data_files)
        # Single folder in Package root?
        if len(root_folders) == 1:
            if not root_folders[0][1] in self.common_folders:  # If subfolder is not a common Mw folder
                root_folders_contents = [x for x in self.package_paths if x[2] == 1]
                contents = [x for x in root_folders_contents if x[0] == root_folders[0][1]]
                if any((x for x in contents if x[1].lower() in self.common_folders)):
                    return self.TreeFactory(root_folders)
            else:  # If subfolder IS a common Mw folder
                return self.TreeFactory(root_folders)
        # Multiple folders in package root containing Mw common files/folders?
        if len(root_folders) > 1:
            if not all([True if x in self.common_folders else False for x in [x[1] for x in root_folders]]):
                root_fold_names = [x[1] for x in self.package_paths if x[2] == 0]
                sub_root = [x for x in self.package_paths if x[0] in root_fold_names and x[2] == 1]
                if len(set([x[0] for x in sub_root if x[1] in self.common_folders])) > 1: return None
                sub_root_files = [x for x in self.mw_files if x[0] in root_fold_names and x[2] == 1]
                if len(set([x[0] for x in sub_root_files if x[1] in [x[1] for x in self.mw_files]])) > 1: return None
        # Multiple folders in package root?
        if len(root_folders) > 1:
            if any((True for x in root_folders if x[1].lower() in self.common_folders)):  # Are they common Mw folders?
                return self.TreeFactory(root_folders)
        # Any single folder with Mw files?
        common = [x[1] for x in self.mw_files]
        common.extend(self.common_folders)
        if common:
            data_files = [x for x in self.package_paths if x[1] in common]
            return self.TreeFactory(data_files)
        return None

#------------------------------------------------------------------------------

class CleanJunkTemp:  # Polemos
    """Simple junk files cleaning."""
    junklist = ('thumbs.db', 'desktop.ini')
    try: tempdir = os.path.join(MashDir, u'Temp')
    except: tempdir = os.path.join(MashDir, 'Temp')
    junk_files = []

    def __init__(self):
        """Init..."""
        self.scan()
        self.clean()

    def scan(self):
        """Scan for junk files."""
        for root, dirs, files in scandir.walk(self.tempdir, topdown=True):
            for file in files:
                if file in self.junklist:
                    junk = os.path.join(root, file.lower())
                    self.junk_files.append(junk)

    def clean(self):
        """Clean junk files."""
        for x in self.junk_files:
            try:
                os.chmod(x, stat.S_IWRITE)
                os.remove(x)
            except: pass

#------------------------------------------------------------------------------

class ArchiveInfo:  # Polemos
    """Read archive contents."""
    getPackageData = []
    common_ext = ['.esp', '.esm', '.bsa', '.omwgame', '.omwaddon', '.ttf', '.fnt']

    def __init__(self, package_path):
        """Init."""
        self.package_path = package_path
        self.parseArchiveStructure()
        self.parseArchiveFiles()
        self.result()

    def archive(self, cmd):
        """Read Package contents."""
        args = ushlex.split(cmd)
        ins = Popen(args, stdout=PIPE, creationflags=DETACHED_PROCESS)
        return ins.stdout

    def parser(self, cmd):
        """Parse archive data."""
        parsed_data = []
        virgin = True
        for entry in self.archive(cmd):
            if virgin:
                if entry[:7] == u'Path = ':
                    virgin = False
                    continue
            if entry[:7] == u'Path = ':
                parsed_data.append(entry[7:].strip())
        return parsed_data

    def parseArchiveFiles(self):
        """Get Package special files data."""
        cmd = ur'7z.exe l -slt -sccUTF-8 "%s" *.esp *.esm *.bsa *.omwgame *.omwaddon *.ttf *.fnt -r' % self.package_path
        files_path = self.parser(cmd)
        self.mwfiles = self.dataFactory(files_path, tree=False)

    def parseArchiveStructure(self):
        """Get package structure data."""
        cmd = ur'7z.exe l -slt -sccUTF-8 "%s" -r *\\ -xr!*\\*.*' % self.package_path
        package_folders = self.parser(cmd)
        self.package_paths = self.dataFactory(package_folders)

    def dataFactory(self, data, tree=True):
        """Create file data."""
        objects = [tuple(x.split('\\')) for x in data]
        tmp_level = []
        max_depth = 0
        try: max_depth = max([len(x) for x in objects if len(x) > max_depth])
        except: pass
        for level in range(max_depth):
            for object in objects:
                if not tree:
                    try:  # For folders
                        if object[level][-4:].lower() not in self.common_ext: continue
                    except:  # For files
                        level = len(object)
                        if object[level - 1][-4:].lower() not in self.common_ext: continue
                try: parent = object[level-1] if level-1 >= 0 else '\\'
                except: parent = '\\'
                try:tmp_level.append((parent, object[level], level))
                except: continue
        if tree: self.max_depth = max_depth
        return tuple(sorted([x for x in set(tmp_level)]))

    def result(self):
        """Return Archive tree data."""
        self.getPackageData = (self.package_paths, self.max_depth, self.mwfiles)

#------------------------------------------------------------------------------

class MultiThreadGauge:  # Polemos
    """Provides a multithreaded gauge for archive packing/unpacking."""
    getInstallLen = 0

    def __init__(self, window, packData, mode='unpack'):
        """Init..."""
        self.mode = mode
        if mode == 'unpack':
            package_tempdir, package_path, data_files = packData
            title = _(u'Unpacking...')
            if data_files == '\\': data_files = ''
            else: data_files = '"%s*"' % data_files
            cmd = ur'7z.exe -bb -bsp1 x "%s" %s -o"%s" -aoa -scsUTF-8' % (package_path, data_files, package_tempdir)
            self.getmodlen(ur'7z.exe l "%s" %s' % (package_path, data_files))
        if mode == 'pack':
            pack_source, pack_target = packData
            if pack_target.endswith('.rar'): pack_target = '%s.7z' % pack_target[:-4]
            title = _(u'Packing...')
            cmd = ur'7z.exe -bb -bsp1 a "%s" "%s\*"' % (pack_target, pack_source)
            cmd = cmd.replace('\\','/')
        self.cmd = cmd
        import gui.dialog as gui
        self.dialog = gui.GaugeDialog(window, title=title)
        thread.start_new_thread(self.process, ('ProcThr',))
        self.dialog.ShowModal()

    def getmodlen(self, cmd):
        """Get quantity of files to be installed."""
        args = ushlex.split(cmd)
        ins = Popen(args, stdout=PIPE, creationflags=DETACHED_PROCESS)
        for entry in ins.stdout: lendata = entry
        lendata = lendata.split()
        self.getInstallLen = int(lendata[4]) if len(lendata) >= 5 else 0

    def process(self, id):
        """Main process thread."""
        args = ushlex.split(self.cmd)
        self.output = Popen(args, stdout=PIPE, creationflags=DETACHED_PROCESS)
        while self.output.poll() is None:
            line = self.output.stdout.readline()
            if '%' in line: self.update(int(line[0:3]), '%s%%' % int(line[0:3]))
        self.kill()

    def kill(self):
        """Quit functions."""
        self.output.stdout.close()
        if self.mode == 'unpack': msg0 , msg1 = _(u'Finishing Unpacking...'), _(u'Finished Unpacking.')
        else: msg0 , msg1 = _(u'Finishing Packing...'), _(u'Finished Packing.')
        self.update(99, msg0)
        self.update(100, msg1)
        time.sleep(1)
        self.dialog.Destroy()

    def update(self, num, msg=u''):
        """Update GaugeDialog."""
        self.dialog.set_msg(msg)
        self.dialog.update(num)

#------------------------------------------------------------------------------

class MainFunctions:
    """Encapsulates a set of functions and/or object instances so that they can
    be called from the command line with normal command line syntax.

    Functions are called with their arguments. Object instances are called
    with their method and method arguments. E.g.:
    * bish bar arg1 arg2 arg3
    * bish foo.bar arg1 arg2 arg3"""

    def __init__(self):
        """Initialization."""
        self.funcs = {}

    def add(self,func,key=None):
        """Add a callable object.
        func - A function or class instance.
        key - Command line invocation for object (defaults to name of func).
        """
        key = key or func.__name__
        self.funcs[key] = func
        return func

    def main(self):
        """Main function. Call this in __main__ handler."""
        #--Get func
        args = sys.argv[1:]
        attrs = args.pop(0).split('.')
        key = attrs.pop(0)
        func = self.funcs.get(key)
        if not func:
            print _(u'Unknown function/object:'), key
            return
        for attr in attrs: func = getattr(func,attr)
        #--Separate out keywords args
        keywords = {}
        argDex = 0
        reKeyArg  = re.compile(r'^\-(\D\w+)')
        reKeyBool = re.compile(r'^\+(\D\w+)')
        while argDex < len(args):
            arg = args[argDex]
            if reKeyArg.match(arg):
                keyword = reKeyArg.match(arg).group(1)
                value   = args[argDex+1]
                keywords[keyword] = value
                del args[argDex:argDex+2]
            elif reKeyBool.match(arg):
                keyword = reKeyBool.match(arg).group(1)
                keywords[keyword] = True
                del args[argDex]
            else: argDex = argDex + 1
        #--Apply
        func(*args, **keywords)

#--Commands Singleton
_mainFunctions = MainFunctions()

def mainfunc(func):
    """A function for adding funcs to _mainFunctions. Used as a function decorator ("@mainfunc")."""
    _mainFunctions.add(func)
    return func


class PickleDict:
    """Dictionary saved in a pickle file.
    Note: self.vdata and self.data are not reassigned! (Useful for some clients.)"""

    def __init__(self,path,readOnly=False):
        """Initialize."""
        self.path = path
        self.backup = path.backup
        self.readOnly = readOnly
        self.vdata = {}
        self.data = {}

    def exists(self):
        return self.path.exists() or self.backup.exists()

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
        self.vdata.clear()
        self.data.clear()
        for path in (self.path,self.backup):
            if path.exists():
                ins = None
                try:
                    ins = path.open('rb')
                    header = compat.uncpickle(ins)
                    if header == 'VDATA':
                        self.vdata.update(compat.uncpickle(ins))
                        self.data.update(compat.uncpickle(ins))
                    else: self.data.update(header)
                    ins.close()
                    return 1 + (path == self.backup)
                except EOFError:
                    if ins: ins.close()
        #--No files and/or files are corrupt
        return 0

    def save(self):
        """Save to pickle file."""
        if self.readOnly: return False
        #--Pickle it
        out = self.path.temp.open('wb')
        for data in ('VDATA',self.vdata,self.data):
            cPickle.dump(data,out,-1)
        out.close()
        self.path.untemp(True)
        return True

#------------------------------------------------------------------------------

class Settings(DataDict):
    """Settings/configuration dictionary with persistent storage.

    Default setting for configurations are either set in bulk (by the
    loadDefaults function) or are set as needed in the code (e.g., various
    auto-continue settings for mash. Only settings that have been changed from
    the default values are saved in persistent storage.

    Directly setting a value in the dictionary will mark it as changed (and thus
    to be archived). However, an indirect change (e.g., to a value that is a
    list) must be manually marked as changed by using the setChanged method."""

    def __init__(self,dictFile):
        """Initialize. Read settings from dictFile."""
        self.dictFile = dictFile
        if self.dictFile:
            dictFile.load()
            self.vdata = dictFile.vdata.copy()
            self.data = dictFile.data.copy()
        else:
            self.vdata = {}
            self.data = {}
        self.changed = []
        self.deleted = []

    def loadDefaults(self,defaults):
        """Add default settings to dictionary. Will not replace values that are already set."""
        for key in defaults.keys():
            if key not in self.data:
                self.data[key] = defaults[key]

    def setDefault(self,key,default):
        """Sets a single value to a default value if it has not yet been set."""
        pass

    def save(self):
        """Save to pickle file. Only key/values marked as changed are saved."""
        dictFile = self.dictFile
        if not dictFile or dictFile.readOnly: return
        dictFile.load()
        dictFile.vdata = self.vdata.copy()
        for key in self.deleted:
            dictFile.data.pop(key,None)
        for key in self.changed:
            dictFile.data[key] = self.data[key]
        dictFile.save()

    def setChanged(self,key):
        """Marks given key as having been changed. Use if value is a dictionary, list or other object."""
        if key not in self.data:
            raise ArgumentError(_(u'No settings data for %s' % key))
        if key not in self.changed:
            self.changed.append(key)

    def getChanged(self,key,default=None):
        """Gets and marks as changed."""
        if default is not None and key not in self.data:
            self.data[key] = default
        self.setChanged(key)
        return self.data.get(key)

    #--Dictionary Emulation
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

    def setdefault(self,key,value):
        """Dictionary emulation. Will not mark as changed."""
        if key in self.data:
            return self.data[key]
        if key in self.deleted: self.deleted.remove(key)
        self.data[key] = value
        return value

    def pop(self,key,default=None):
        """Dictionary emulation: extract value and delete from dictionary."""
        if key in self.changed: self.changed.remove(key)
        if key not in self.deleted: self.deleted.append(key)
        return self.data.pop(key,default)


class StructFile(file):
    """File reader/writer with extra functions for handling structured data."""

    def unpack(self,format,size):
        """Reads and unpacks according to format."""
        return struct.unpack(format,self.read(size))

    def pack(self,format,*data):
        """Packs data according to format."""
        self.write(struct.pack(format,*data))


class TableColumn:
    """Table accessor that presents table column as a dictionary."""

    def __init__(self,table,column):
        self.table = table
        self.column = column

    def __iter__(self):
        """Dictionary emulation."""
        tableData = self.table.data
        column = self.column
        return (key for key in tableData.keys() if (column in tableData[key]))

    def keys(self):
        return list(self.__iter__())

    def items(self):
        """Dictionary emulation."""
        tableData = self.table.data
        column = self.column
        return [(key,tableData[key][column]) for key in tableData.keys()
            if (column in tableData[key])]

    def has_key(self,key):
        """Dictionary emulation."""
        return self.__contains__(key)

    def clear(self):
        """Dictionary emulation."""
        self.table.delColumn(self.column)

    def get(self,key,default=None):
        """Dictionary emulation."""
        return self.table.getItem(key,self.column,default)

    #--Overloaded
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


class Table(DataDict):
    """Simple data table of rows and columns, saved in a pickle file. It is
    currently used by modInfos to represent properties associated with modfiles,
    where each modfile is a row, and each property (e.g. modified date or
    'mtime') is a column.

    The "table" is actually a dictionary of dictionaries. E.g.
        propValue = table['fileName']['propName']
    Rows are the first index ('fileName') and columns are the second index
    ('propName')."""

    def __init__(self,dictFile):
        """Intialize and read data from dictFile, if available."""
        self.dictFile = dictFile
        dictFile.load()
        self.vdata = dictFile.vdata
        self.data = dictFile.data
        self.hasChanged = False

    def save(self):
        """Saves to pickle file."""
        dictFile = self.dictFile
        if self.hasChanged and not dictFile.readOnly:
            self.hasChanged = not dictFile.save()

    def getItem(self,row,column,default=None):
        """Get item from row, column. Return default if row,column doesn't exist."""
        data = self.data
        if row in data and column in data[row]:
            return data[row][column]
        else:
            return default

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

    def setItemDefault(self,row,column,value):
        """Set value for row, column."""
        data = self.data
        if row not in data:
            data[row] = {}
        self.hasChanged = True
        return data[row].setdefault(column,value)

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

    #--Dictionary emulation
    def __setitem__(self,key,value):
        self.data[key] = value
        self.hasChanged = True

    def __delitem__(self,key):
        del self.data[key]
        self.hasChanged = True

    def setdefault(self,key,default):
        if key not in self.data: self.hasChanged = True
        return self.data.setdefault(key,default)  # fix

    def pop(self,key,default=None):
        self.hasChanged = True
        return self.data.pop(key,default)


class TankData:
    """Data source for a Tank table."""

    def __init__(self,params):
        """Initialize."""
        self.tankParams = params
        #--Default settings. Subclasses should define these.
        self.tankKey = self.__class__.__name__
        self.tankColumns = [] #--Full possible set of columns.
        self.title = self.__class__.__name__
        self.hasChanged = False

    def getParam(self,key,default=None):  #--Parameter access
        """Get a GUI parameter.
        Typical Parameters:
        * columns: list of current columns.
        * colNames: column_name dict
        * colWidths: column_width dict
        * colAligns: column_align dict
        * colReverse: column_reverse dict (colReverse[column] = True/False)
        * colSort: current column being sorted on
        """
        return self.tankParams.get(self.tankKey+'.'+key,default)

    def defaultParam(self,key,value):
        """Works like setdefault for dictionaries."""
        return self.tankParams.setdefault(self.tankKey+'.'+key,value)

    def updateParam(self,key,default=None):
        """Get a param, but also mark it as changed.
        Used for deep params like lists and dictionaries."""
        return self.tankParams.getChanged(self.tankKey+'.'+key,default)

    def setParam(self,key,value):
        """Set a GUI parameter."""
        self.tankParams['%s.%s' % (self.tankKey, key)] = value

    #--Collection
    def setChanged(self,hasChanged=True):
        """Mark as having changed."""
        pass

    def refresh(self):
        """Refreshes underlying data as needed."""
        pass

    def getRefreshReport(self):
        """Returns a (string) report on the refresh operation."""
        return None

    def getSorted(self,column,reverse):
        """Returns items sorted according to column and reverse."""
        raise AbstractError

    #--Item Info
    def getColumns(self,item=None):
        """Returns text labels for item or for row header if item == None."""
        columns = self.getParam('columns',self.tankColumns)
        if item is None: return columns[:]
        raise AbstractError

    def getName(self,item):
        """Returns a string name of item for use in dialogs, etc."""
        return item

    def getGuiKeys(self,item):
        """Returns keys for icon and text and background colors."""
        iconKey = textKey = backKey = None
        return (iconKey,textKey,backKey)

# Util Functions --------------------------------------------------------------

def copyattrs(source,dest,attrs):
    """Copies specified attrbutes from source object to dest object."""
    for attr in attrs: setattr(dest,attr,getattr(source,attr))


def cstrip(inString):
    """Convert c-string (null-terminated string) to python string."""
    zeroDex = inString.find('\x00')
    if zeroDex == -1: return inString
    else: return inString[:zeroDex]


def csvFormat(format):
    """Returns csv format for specified structure format."""
    csvFormat = ''
    for char in format:
        if char in 'bBhHiIlLqQ': csvFormat += ',%d'
        elif char in 'fd': csvFormat += ',%f'
        elif char in 's': csvFormat += ',"%s"'
    return csvFormat[1:] #--Chop leading comma


deprintOn = False
def deprint(*args,**keyargs):
    """Prints message along with file and line location."""
    if not deprintOn and not keyargs.get('on'): return
    import inspect
    stack = inspect.stack()
    file,line,function = stack[1][1:4]
    print '%s %4d %s: %s' % (GPath(file).tail.s,line,function,' '.join(map(str,args)))


def delist(header,items,on=False):
    """Prints list as header plus items."""
    if not deprintOn and not on: return
    import inspect
    stack = inspect.stack()
    file,line,function = stack[1][1:4]
    print '%s %4d %s: %s' % (GPath(file).tail.s,line,function,str(header))
    if items is None: print '> None'
    else:
        for indexItem in enumerate(items): print '>%2d: %s' % indexItem


def dictFromLines(lines,sep=None):  # Polemos: Is this used anywhere...?
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


def intArg(arg,default=None):
    """Returns argument as an integer. If argument is a string, then it converts it using int(arg,0)."""
    if arg is None: return default
    elif isinstance(arg,StringType): return int(arg,0)
    else: return int(arg)


def invertDict(indict):
    """Invert a dictionary."""
    return dict((y,x) for x,y in indict.iteritems())


def listFromLines(lines): # ???
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


def listJoin(*inLists):
    """Joins multiple lists into a single list."""
    outList = []
    for inList in inLists:
        outList.extend(inList)
    return outList


def listGroup(items):
    """Joins items into a list for use in a regular expression.
    E.g., a list of ('alpha','beta') becomes '(alpha|beta)'"""
    return '('+('|'.join(items))+')'


def rgbString(red,green,blue):
    """Converts red, green blue ints to rgb string."""
    return chr(red)+chr(green)+chr(blue)


def rgbTuple(rgb):
    """Converts red, green, blue string to tuple."""
    return struct.unpack('BBB',rgb)


def unQuote(inString):
    """Removes surrounding quotes from string."""
    if len(inString) >= 2 and inString[0] == '"' and inString[-1] == '"':
        return inString[1:-1]
    else: return inString


def winNewLines(inString):
    """Converts unix newlines to windows newlines."""
    return reUnixNewLine.sub('\r\n',inString)

# Log/Progress ----------------------------------------------------------------

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

    def setHeader(self,header,writeNow=False,doFooter=True):
        """Sets the header."""
        self.header = header
        if self.prevHeader:
            self.prevHeader += 'x'
        self.doFooter = doFooter
        if writeNow: self()

    def __call__(self,message=None):
        """Callable. Writes message, and if necessary, header and footer."""
        if self.header != self.prevHeader:
            if self.prevHeader and self.doFooter:
                self.writeFooter()
            if self.header:
                self.writeHeader(self.header)
            self.prevHeader = self.header
        if message: self.writeMessage(message)

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


class LogFile(Log):
    """Log that writes messages to file."""

    def __init__(self,out):
        self.out = out
        Log.__init__(self)

    def writeHeader(self,header):
        self.out.write(header+'\n')

    def writeFooter(self):
        self.out.write('\n')

    def writeMessage(self,message):
        self.out.write(message+'\n')


class Progress:
    """Progress Callable: Shows progress when called."""

    def __init__(self,full=1.0):
        if (1.0*full) == 0: raise ArgumentError(_(u'Full must be non-zero!'))
        self.message = ''
        self.full = full
        self.state = 0
        self.debug = False

    def setFull(self,full):
        """Set's full and for convenience, returns self."""
        if (1.0*full) == 0: raise ArgumentError(_(u'Full must be non-zero!'))
        self.full = full
        return self

    def plus(self,increment=1):
        """Increments progress by 1."""
        self.__call__(self.state+increment)

    def __call__(self,state,message=''):
        """Update progress with current state. Progress is state/full."""
        if (1.0*self.full) == 0: raise ArgumentError(_(u'Full must be non-zero!'))
        if message: self.message = message
        if self.debug: deprint('%0.3f %s' % (1.0*state/self.full, self.message))
        self.doProgress(1.0*state/self.full, self.message)
        self.state = state

    def doProgress(self,progress,message):
        """Default doProgress does nothing."""
        pass


class SubProgress(Progress):
    """Sub progress goes from base to ceiling."""

    def __init__(self,parent,baseFrom=0.0,baseTo='+1',full=1.0,silent=False):
        """For creating a subprogress of another progress meter.
        progress: parent (base) progress meter
        baseFrom: Base progress when this progress == 0.
        baseTo: Base progress when this progress == full
          Usually a number. But string '+1' sets it to baseFrom + 1
        full: Full meter by this progress' scale."""
        Progress.__init__(self,full)
        if baseTo == '+1': baseTo = baseFrom + 1
        if (baseFrom < 0 or baseFrom >= baseTo):
            raise ArgumentError(_(u'BaseFrom must be >= 0 and BaseTo must be > BaseFrom'))
        self.parent = parent
        self.baseFrom = baseFrom
        self.scale = 1.0*(baseTo-baseFrom)
        self.silent = silent

    def __call__(self,state,message=''):
        """Update progress with current state. Progress is state/full."""
        if self.silent: message = ''
        self.parent(self.baseFrom+self.scale*state/self.full,message)
        self.state = state


class ProgressFile(Progress):
    """Prints progress to file (stdout by default)."""

    def __init__(self,full=1.0,out=None):
        Progress.__init__(self,full)
        self.out = out or sys.stdout

    def doProgress(self,progress,message):
        self.out.write('%0.2f %s\n' % (progress,message))


class WryeText:
    """This class provides a function for converting wtxt text files to html
    files.

    Headings:
    = XXXX >> H1 "XXX"
    == XXXX >> H2 "XXX"
    === XXXX >> H3 "XXX"
    ==== XXXX >> H4 "XXX"
    Notes:
    * These must start at first character of line.
    * The XXX text is compressed to form an anchor. E.g == Foo Bar gets anchored as" FooBar".
    * If the line has trailing ='s, they are discarded. This is useful for making
      text version of level 1 and 2 headings more readable.

    Bullet Lists:
    * Level 1
      * Level 2
        * Level 3
    Notes:
    * These must start at first character of line.
    * Recognized bullet characters are: - ! ? . + * o The dot (.) produces an invisible
      bullet, and the * produces a bullet character.

    Styles:
      __Text__
      ~~Italic~~
      **BoldItalic**
    Notes:
    * These can be anywhere on line, and effects can continue across lines.

    Links:
     [[file]] produces <a href=file>file</a>
     [[file|text]] produces <a href=file>text</a>

    Contents
    {{CONTENTS=NN}} Where NN is the desired depth of contents (1 for single level,
    2 for two levels, etc.).
    """

    # Data ------------------------------------------------------------------------
    htmlHead = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
    <HTML>
    <HEAD>
    <META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=iso-8859-1">
    <TITLE>%s</TITLE>
    <STYLE>%s</STYLE>
    </HEAD>
    <BODY>
    """
    defaultCss = """
    H1 { margin-top: 0in; margin-bottom: 0in; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: none; border-right: none; padding: 0.02in 0in; background: #c6c63c; font-family: "Arial", serif; font-size: 12pt; page-break-before: auto; page-break-after: auto }
    H2 { margin-top: 0in; margin-bottom: 0in; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: none; border-right: none; padding: 0.02in 0in; background: #e6e64c; font-family: "Arial", serif; font-size: 10pt; page-break-before: auto; page-break-after: auto }
    H3 { margin-top: 0in; margin-bottom: 0in; font-family: "Arial", serif; font-size: 10pt; font-style: normal; page-break-before: auto; page-break-after: auto }
    H4 { margin-top: 0in; margin-bottom: 0in; font-family: "Arial", serif; font-style: italic; page-break-before: auto; page-break-after: auto }
    P { margin-top: 0.01in; margin-bottom: 0.01in; font-family: "Arial", serif; font-size: 10pt; page-break-before: auto; page-break-after: auto }
    P.empty {}
    P.list-1 { margin-left: 0.15in; text-indent: -0.15in }
    P.list-2 { margin-left: 0.3in; text-indent: -0.15in }
    P.list-3 { margin-left: 0.45in; text-indent: -0.15in }
    P.list-4 { margin-left: 0.6in; text-indent: -0.15in }
    P.list-5 { margin-left: 0.75in; text-indent: -0.15in }
    P.list-6 { margin-left: 1.00in; text-indent: -0.15in }
    PRE { border: 1px solid; background: #FDF5E6; padding: 0.5em; margin-top: 0in; margin-bottom: 0in; margin-left: 0.25in}
    CODE { background-color: #FDF5E6;}
    BODY { background-color: #ffffcc; }
    """

    @staticmethod
    def genHtml(ins,out=None,*cssDirs):
        """Reads a wtxt input stream and writes an html output stream."""
        # Path or Stream? ----------------------------------------------- #
        if isinstance(ins,(Path,str,unicode)):
            srcPath = GPath(ins)
            outPath = GPath(out) or srcPath.root+'.html'
            cssDirs = (srcPath.head,) + cssDirs
            ins = srcPath.open()
            out = outPath.open('w')
        else:
            srcPath = outPath = None
        cssDirs = map(GPath,cssDirs)
        # Setup --------------------------------------------------------- #
        #--Headers
        reHead = re.compile(r'(=+) *(.+)')
        headFormat = "<h%d><a name='%s'>%s</a></h%d>\n"
        headFormatNA = "<h%d>%s</h%d>\n"
        #--List
        reList = re.compile(r'( *)([-x!?\.\+\*o]) (.*)')
        #--Misc. text
        reHr = re.compile('^------+$')
        reEmpty = re.compile(r'\s+$')
        reMDash = re.compile(r'--')
        rePreBegin = re.compile('<pre>',re.I)
        rePreEnd = re.compile('</pre>',re.I)
        def subAnchor(match):
            text = match.group(1)
            anchor = reWd.sub('',text)
            return "<a name='%s'>%s</a>" % (anchor,text)
        #--Bold, Italic, BoldItalic
        reBold = re.compile(r'__')
        reItalic = re.compile(r'~~')
        reBoldItalic = re.compile(r'\*\*')
        states = {'bold':False,'italic':False,'boldItalic':False}
        def subBold(match):
            state = states['bold'] = not states['bold']
            return ('</B>','<B>')[state]
        def subItalic(match):
            state = states['italic'] = not states['italic']
            return ('</I>','<I>')[state]
        def subBoldItalic(match):
            state = states['boldItalic'] = not states['boldItalic']
            return ('</I></B>','<B><I>')[state]
        #--Preformatting
        #--Links
        reLink = re.compile(r'\[\[(.*?)\]\]')
        reHttp = re.compile(r' (http://[_~a-zA-Z0-9\./%-]+)')
        reWww = re.compile(r' (www\.[_~a-zA-Z0-9\./%-]+)')
        reWd = re.compile(r'(<[^>]+>|\[[^\]]+\]|\W+)')
        rePar = re.compile(r'^([a-zA-Z]|\*\*|~~|__)')
        reFullLink = re.compile(r'(:|#|\.[a-zA-Z0-9]{2,4}$)')
        def subLink(match):
            address = text = match.group(1).strip()
            if '|' in text:
                (address,text) = [chunk.strip() for chunk in text.split('|',1)]
                if address == '#': address += reWd.sub('',text)
            if not reFullLink.search(address):
                address = address+'.html'
            return '<a href="%s">%s</a>' % (address,text)
        #--Tags
        reAnchorTag = re.compile('{{A:(.+?)}}')
        reContentsTag = re.compile(r'\s*{{CONTENTS=?(\d+)}}\s*$')
        reAnchorHeadersTag = re.compile(r'\s*{{ANCHORHEADERS=(\d+)}}\s*$')
        reCssTag = re.compile('\s*{{CSS:(.+?)}}\s*$')
        #--Defaults ---------------------------------------------------------- #
        title = ''
        level = 1
        spaces = ''
        cssName = None
        #--Init
        outLines = []
        contents = []
        addContents = 0
        inPre = False
        isInParagraph = False
        anchorHeaders = True
        #--Read source file -------------------------------------------------- #
        for line in ins:
            isInParagraph,wasInParagraph = False,isInParagraph
            #--Preformatted? ----------------------------- #
            maPreBegin = rePreBegin.search(line)
            maPreEnd = rePreEnd.search(line)
            if inPre or maPreBegin or maPreEnd:
                inPre = maPreBegin or (inPre and not maPreEnd)
                outLines.append(line)
                continue
            #--Re Matches ------------------------------- #
            maContents = reContentsTag.match(line)
            maAnchorHeaders = reAnchorHeadersTag.match(line)
            maCss = reCssTag.match(line)
            maHead = reHead.match(line)
            maList  = reList.match(line)
            maPar   = rePar.match(line)
            maEmpty = reEmpty.match(line)
            #--Contents ---------------------------------- #
            if maContents:
                if maContents.group(1):
                    addContents = int(maContents.group(1))
                else: addContents = 100
                inPar = False
            elif maAnchorHeaders:
                anchorHeaders = maAnchorHeaders.group(1) != '0'
                continue
            #--CSS
            elif maCss:
                #--Directory spec is not allowed, so use tail.
                cssName = GPath(maCss.group(1).strip()).tail
                continue
            #--Headers
            elif maHead:
                lead,text = maHead.group(1,2)
                text = re.sub(' *=*#?$','',text.strip())
                anchor = reWd.sub('',text)
                level = len(lead)
                if anchorHeaders:
                    line = (headFormatNA,headFormat)[anchorHeaders] % (level,anchor,text,level)
                    if addContents: contents.append((level,anchor,text))
                else: line = headFormatNA % (level,text,level)
                #--Title?
                if not title and level <= 2: title = text
            #--List item
            elif maList:
                spaces = maList.group(1)
                bullet = maList.group(2)
                text = maList.group(3)
                if bullet == '.': bullet = '&nbsp;'
                elif bullet == '*': bullet = '&bull;'
                level = len(spaces)/2 + 1
                line = spaces+'<p class=list-'+`level`+'>'+bullet+'&nbsp; '
                line = line + text + '\n'
            #--Paragraph
            elif maPar:
                if not wasInParagraph: line = '<p>'+line
                isInParagraph = True
            #--Empty line
            elif maEmpty:
                line = spaces+'<p class=empty>&nbsp;</p>\n'
            #--Misc. Text changes -------------------- #
            line = reHr.sub('<hr>',line)
            line = reMDash.sub('&#150',line)
            line = reMDash.sub('&#150',line)
            #--Bold/Italic subs
            line = reBold.sub(subBold,line)
            line = reItalic.sub(subItalic,line)
            line = reBoldItalic.sub(subBoldItalic,line)
            #--Wtxt Tags
            line = reAnchorTag.sub(subAnchor,line)
            #--Hyperlinks
            line = reLink.sub(subLink,line)
            line = reHttp.sub(r' <a href="\1">\1</a>',line)
            line = reWww.sub(r' <a href="http://\1">\1</a>',line)
            #--Save line ------------------ #
            #print line,
            outLines.append(line)
        #--Get Css ----------------------------------------------------------- #
        if not cssName: css = WryeText.defaultCss
        else:
            if cssName.ext != '.css': raise u"Invalid Css file: %dsS" % cssName.s
            for dir in cssDirs:
                cssPath = GPath(dir).join(cssName)
                if cssPath.exists(): break
            else: raise u'Css file not found: %s' % cssName.s
            css = ''.join(cssPath.open().readlines())
            if '<' in css: raise u"Non css tag in %s" % cssPath.s
        #--Write Output ------------------------------------------------------ #
        out.write(WryeText.htmlHead % (title,css))
        didContents = False
        for line in outLines:
            if reContentsTag.match(line):
                if contents and not didContents:
                    baseLevel = min([level for (level,name,text) in contents])
                    for (level,name,text) in contents:
                        level = level - baseLevel + 1
                        if level <= addContents:
                            out.write('<p class=list-%d>&bull;&nbsp; <a href="#%s">%s</a></p>\n' % (level,name,text))
                    didContents = True
            else: out.write(line)
        out.write('</body>\n</html>\n')
        #--Close files?
        if srcPath:
            ins.close()
            out.close()

import conf  # Polemos: Hackish approach for importing settings into the module.

# Main ------------------------------------------------------------------------- #
if __name__ == '__main__' and len(sys.argv) > 1:
    #--Commands
    @mainfunc
    def genHtml(*args,**keywords):
        """Wtxt to html. Just pass through to WryeText.genHtml."""
        WryeText.genHtml(*args,**keywords)

    #--Command Handler
    _mainFunctions.main()
