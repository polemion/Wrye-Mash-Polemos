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


# Extension for Wrye Mash Polemos fork =======================================================
#
# Wrye Nash, Copyright (C) 2018-, Polemos
#
# Polemos: I created this as a basis for Nexus site compatibility. It gives Internet abilities
# to Wrye Mash. I hope the next guy who works on Wrye Mash will find it useful and build on it.
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ============================================================================================


from lxml import html
from lxml import _elementpath as _dummy  # Polemos: Needed for py2exe to work.
import requests
from .gui import dialog as guidialog
import os, wx

os.environ["REQUESTS_CA_BUNDLE"] = "cacert.pem"


def wrye_download_site(url, mode):
    """Mirrors and download site of Wrye Mash."""
    if url == 'home':
        if not mode:  # Regular Morrowind
            return 'https://www.nexusmods.com/morrowind/mods/45439'
        else:  # OpenMW/TES3mp
            return 'https://www.nexusmods.com/morrowind/mods/46935'
    if url == 'download':
        if not mode:  # Regular Morrowind
            return 'https://www.nexusmods.com/morrowind/mods/45439?tab=files'
        else:  # OpenMW/TES3mp
            return 'https://www.nexusmods.com/morrowind/mods/46935?tab=files'


class WryeWeb(object):
    """Wrye Mash version checker for Nexus."""

    def __init__(self, mode):
        """Init."""
        self.openmw = mode
        self.mash_net = wrye_download_site('home', self.openmw)

    def get_mash_ver(self):
        """Parse Nexus page."""
        progress = guidialog.netProgressDialog()
        try:
            progress.update(4)
            page = requests.get(self.mash_net)
            tree = html.fromstring(page.content)
            get_ver = tree.xpath('//*[@id="pagetitle"]/ul[2]/li[5]/div/div[2]')
            self.mash_net_ver = int(('%s' % (get_ver[0].text.strip().replace('v', ''))))
            progress.update()
            result = self.mash_net_ver
        except:
            result = 'error'
        finally:
            progress.Destroy()
            return result


class VisitWeb(object):
    """Visit a mod's webpage."""

    def __init__(self, webData):
        """Init."""
        repo, ID = webData
        if repo == 'Nexus':
            self.Nexus(ID)
        # elif repo ==...
        else:
            return

    def Nexus(self, ID):
        """Nexus site implementation."""
        nexusWeb = 'https://www.nexusmods.com/morrowind/mods/%s' % ID
        self.visit(nexusWeb)

    def visit(self, website):
        """Open mod website on user's default system browser."""
        wx.LaunchDefaultBrowser(website)
