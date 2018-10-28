# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# Wrye Mash 2018 Polemos fork Copyright (C) 2017-2018 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher
#
#  Copyright on the original code 2005-2009 Wrye
#  Copyright on any non trivial modifications or substantial additions 2009-2011 Melchor
#  Copyright on any non trivial modifications or substantial additions 2011-2016 Yacoby
#  Copyright on any non trivial modifications or substantial additions 2017-2018 Polemos
#
# ======================================================================================

# Extension for Wrye Mash Polemos fork ======================================================
#
# Interface, Copyright (C) 2018-, Polemos
#
# Polemos: Basis for a unicode engine for Wrye Mash
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================

import os, time

# Enrich these...
usualEncodings = (
    ('utf-8', 'Strict'),    # The Messiah
    ('cp1251', 'replace'),  # Windows Slavic
    ('cp1252', 'replace'),  # Western Europe
    None,                   # Default
)

def uniChk(value):
    """UniGate for values check."""
    for enc in usualEncodings:
        try: return value if enc is None else value.decode(enc[0], enc[1])
        except: continue

def binary(data):
    """Convert safely to binary."""
    cwd = os.getcwd()
    os.chdir(data)
    result = os.getcwd()
    os.chdir(cwd)
    return result

def norm_path_po(path): # Normalize bolt paths. Goofy but it works.
    """Returns a normalized unicode filename."""
    return unicode(path).replace("bolt.Path(u'", "").replace("')", "")

def uniformatDate(value):
    """Convert time to string formatted to neutral locale's default date/time."""
    return time.strftime('%x %H:%M:%S', time.localtime(value))
