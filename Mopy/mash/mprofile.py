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
# Profile System, Copyright (C) 2019-, Polemos
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================


import os, codecs, conf, singletons


class user_profile:  # Polemos
    """Wrye Mash User profile."""

    def __init__(self):
        """Initialize."""
        if not self.checkactive(): self.createdefault()
        self.version_updates()
        singletons.Profile = self

    def version_updates(self):
        """Update old profile if needed."""
        for line in self.getdata('profile'):
            if '#   Wrye Mash v' in line:  # Versions before v99
                self.create(self.profile, text=self.defaultini())
                for x in ['active.dat','bsa.dat','plugins.dat']:
                    target = os.path.join(self.profiledir, x)
                    if os.path.isfile(target):
                        try: os.remove(target)
                        except: pass

    def getdata(self, data='profile'):
        """Method for easy data retrieval"""
        if data == 'profile': return self.read(self.profile)
        elif data == 'mods': return self.read(self.mods)

    def checkactive(self):
        """Check if active profile files exist and act."""
        try: profile = self.setprofile()
        except:
            self.createdefault() # todo: add dialog to inform user
            profile = self.setprofile()
        for x in profile:
            if not os.path.exists(x): return False  # todo: add dialog to inform user
        return True

    def setprofile(self):
        """Set profile default paths"""
        self.profiledir = os.path.join(singletons.MashDir, 'Profiles', conf.settings['profile.active'])
        self.profile = os.path.join(self.profiledir, 'profile.ini')
        self.mods = os.path.join(self.profiledir, 'mods.dat')
        return self.profiledir, self.profile, self.mods

    def createdefault(self):
        """Create default files/dirs."""
        try: self.setprofile()
        except: pass # todo: add dialog to inform user
        try:
            if not os.path.exists(self.profiledir): os.makedirs(self.profiledir)
            if not os.path.isfile(self.profile): self.create(self.profile, text=self.defaultini())
            if not os.path.isfile(self.mods): self.create(self.mods)
        except: pass # todo: add dialog to inform user

    def create(self, data, text=''):
        """Create method."""
        with codecs.open(data, 'w', 'utf-8') as f:
            f.write(text)

    def read(self, data):
        """Read method."""
        with codecs.open(data, 'r', 'utf-8') as f:
            data = f.readlines()
        return data

    def defaultini(self):
        """Return default.ini text."""
        version = conf.settings['mash.version']
        openmw = conf.settings['openmw']
        tes3mp = conf.settings['tes3mp']
        if not openmw: engine = 'Morrowind'
        elif openmw and not tes3mp: engine = 'openmw'
        elif openmw and tes3mp: engine = 'openmw_tes3mp'
        text = ('#   Wrye Mash Profile Data    #\r\n',
                '[General]',
                'profver=%s' % (version[0]),
                'engine=%s' % (engine))
        return '\r\n'.join(text)
