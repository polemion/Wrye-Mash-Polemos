# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# Wrye Mash 2018 Polemos fork Copyright (C) 2017-2019 Polemos
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
# Universal Mash, Copyright (C) 2018-, Polemos
#
# Polemos: Basis for a unicode engine for Wrye Mash
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================

import os, time, chardet, singletons

# Enrich these...
usualEncodings = (
    ('utf-8', 'Strict'),    # The Messiah
    ('cp1251', 'replace'),  # Windows Slavic
    ('cp1252', 'replace'),  # Western Europe
    ('cp1250', 'replace'),  # Central Europe
    None,                   # Default
)

def encChk(value):
    """Return value encoding."""
    if type(value) is unicode: value = value.encode('utf-8')
    enc = chardet.detect(value)
    return enc['encoding']

def uniChk(value):
    """UniGate for values check."""
    try: return value.decode(encChk(value))
    except:
        for enc in usualEncodings:
            try: return value if enc is None else value.decode(enc[0], enc[1])
            except: continue

def fChk(data):
    """Safety check."""
    cwd = singletons.MashDir
    os.chdir(data)
    result = os.getcwd()
    os.chdir(cwd)
    return result

def n_path(path):  # Goofy but it works.
    """Returns a normalized bolt path."""
    return unicode(path).replace("bolt.Path(u'", "").replace("')", "")

def uniformatDate(value):
    """Convert time to string formatted to a locale neutral date/time."""
    return time.strftime('%x %H:%M:%S', time.localtime(value))

