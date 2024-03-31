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


import os
import subprocess
from subprocess import Popen
import threading
import time
import six.moves.queue as queue
from ... import conf, singletons


class HelperMixin(object):  # Polemos fixes.

    def getSubprocess(self, args):
        if os.name == 'nt':
            # Hide the command prompt on NT systems
            info = subprocess.STARTUPINFO()
            info.dwFlags |= 0x00000001
        cmd_po = 'tes3cmd.exe'
        args_po = ''
        try:
            for x in args:
                if x.lower().endswith('.esp') or x.lower().endswith('.esm') or x.lower().endswith(
                    '.ess'): x = '"%s"' % x
                if x != 'tes3cmd.exe': args_po = '%s %s' % (args_po, x)
        except:
            args_po = ''
        # Polemos: Tired trying to work with Mary Popens buggy attitude. Be my guest.
        command = 'cd /D "%s" & %s%s' % (getDataDir(), cmd_po, args_po)
        return Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    def buildFixitArgs(self, hideBackups, backupDir):
        args = ['tes3cmd.exe', 'fixit']
        if hideBackups: args.append('--hide-backups')
        if backupDir: args += ['--backup-dir', backupDir]
        return args

    def buildMultipatchArgs(self):  # Polemos: Added Multipatch ability.
        """Args factory"""
        args = ['tes3cmd.exe', 'multipatch ']
        return args

    def syncHeadMastArgs(self, files):  # Polemos: Added Sync Headers/Master ability by Abot.
        """Args factory"""
        args = ['tes3cmd.exe', 'header', '--synchronize', '--debug', '--hide-backups', '--backup-dir',
                'tes3cmdbck'] + files
        return args

    def mergeArgs(self, files):  # Polemos: Added Merge records by Abot.
        """Args factory"""
        args = ['tes3cmd.exe', 'dumb', '--debug', '--raw-with-header'] + files
        return args

    def buildCleanArgs(self, files, replace, hideBackups, backupDir, cells, dups, gmsts, instances, junk):
        """Args factory"""
        if not (cells or dups or gmsts or instances or junk): raise Exception(u'No options selected')
        args = ['tes3cmd.exe', 'clean']
        if replace: args.append('--replace')
        if hideBackups: args.append('--hide-backups')
        if backupDir: args += ['--backup-dir', backupDir]
        # if everything is true then we don't need to set any of the options
        if cells and dups and gmsts and instances and junk:
            args += files
            return args
        if cells: args.append('--cell-params')
        if dups: args.append('--dups')
        if gmsts: args.append('--gmsts')
        if instances: args.append('--instances')
        if junk: args.append('--junk-cells')
        args += files
        return args

    def buildHeaderArgs(self, file, hideBackups, backupDir, sync, updateMasters, updateRecordCount):
        args = ['tes3cmd.exe', 'header']
        if hideBackups: args.append('--hide-backups')
        if backupDir: args += ['--backup-dir', backupDir]

        if sync: args.append('--synchronize')
        if updateMasters: args.append('--update-masters')
        if updateRecordCount: args.append('--update-record-count')
        args.append(file)
        return args


class Basic(HelperMixin):  # Polemos fixes.
    """Basic."""

    def fixit(self, hideBackups=True, backupDir='tes3cmdbck'):
        """Fixit."""
        args = self.buildFixitArgs(hideBackups, backupDir)
        self.out, self.err = self.getSubprocess(args).communicate()

    def multipatch(self):  # Polemos
        """Multipatch."""
        args = self.buildMultipatchArgs()
        self.out, self.err = self.getSubprocess(args).communicate()

    def syncMasters(self, files):  # Polemos
        """Header sync masters."""
        args = self.syncHeadMastArgs(files)
        self.out, self.err = self.getSubprocess(args).communicate()

    def merge(self, files):  # Polemos
        """Header sync masters."""
        args = self.mergeArgs(files)
        self.out, self.err = self.getSubprocess(args).communicate()


class Threaded(threading.Thread, HelperMixin):
    """A class that manages a Threaded process in another thread."""

    def __init__(self, callback=None):
        """
        The callback should be a function that sends the done event to your
        application. It should be constructed with care as it is called in this
        thread not the main one.
        """
        threading.Thread.__init__(self)
        self.msg = queue.Queue()
        self.callback = callback
        self.err = self.out = ''

    def stop(self):
        """
        Stops the execution of the thread. You must join the thread after
        calling this as it isn't instant. This is safe to call from another thread
        """
        self.msg.put('STOP')

    def fixit(self, hideBackups=True, backupDir='tes3cmdbck'):
        self.args = self.buildFixitArgs(hideBackups, backupDir)
        self.start()

    def clean(self, files, replace=False, hideBackups=True, backupDir='tes3cmdbck', cells=True, dups=True, gmsts=True,
              instances=True, junk=True):
        self.files = files
        self.args = self.buildCleanArgs(files, replace, hideBackups, backupDir, cells, dups, gmsts, instances, junk)
        self.start()

    def header(self, file, hideBackups=True, backupDir='tes3cmdbck', sync=True, updateMasters=False,
               updateRecordCount=False):
        self.files = [file]
        self.args = self.buildHeaderArgs(file, hideBackups, backupDir, sync, updateMasters, updateRecordCount)
        self.start()

    def run(self):  # Polemos: hackish bugfix (happens for queue to return nothing)
        """This shouldn't be called directly, use a function like clean that correctly sets the state."""
        p = self.getSubprocess(self.args)
        unfreeze = 0
        while p.poll() is None:
            unfreeze += 1
            if unfreeze == 500: break  # 5 sec breaker
            if not self.msg.empty():
                msg = self.msg.get()
                if msg == 'STOP':
                    p.terminate()
                    return
            time.sleep(0.01)

        for line in iter(p.stdout.readline, ''): self.out += line.strip() + '\n'
        for line in iter(p.stderr.readline, ''): self.err += line.strip() + '\n'
        if self.callback: self.callback()


def getDataDir():  # Polemos fix
    data_files_dir = os.path.join(conf.settings['mwDir'], 'Data Files')
    return data_files_dir


def getLocation():  # Polemos: Returns path only if TES3cmd is in "Data Files" dir
    path = os.path.join(conf.settings['mwDir'], 'Data Files', 'tes3cmd.exe')
    return path if os.path.exists(path) else None
