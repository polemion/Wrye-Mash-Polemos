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
# Universal Mash, Copyright (C) 2018-, Polemos
#
# Unicode/Locale functions
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================

import os, time, chardet, singletons, locale, re, cPickle


# Enrich these...
usualEncodings = (
    ('utf-8', 'Strict'),    # The Messiah
    ('cp1251', 'replace'),  # Windows Slavic
    ('cp1252', 'replace'),  # Western Europe
    ('cp1250', 'replace'),  # Central Europe
    None,                   # Default
)

profileEncodings = {
        'cp1250': 'Central European Latin (Polish)',
        'cp1251': 'Cyrillic alphabets (Slavic)',
        'utf-8': 'Experimental (Write On)'
}

defaultEncoding = 'cp1252'
if not defaultEncoding in profileEncodings:
    profileEncodings[defaultEncoding] = 'Western Latin (Morrowind default)'

def compileTranslator(txtPath, pklPath):
    """Compiles specified txtFile into pklFile."""
    reSource = re.compile(r'^=== ')
    reValue = re.compile(r'^>>>>\s*$')
    reBlank = re.compile(r'^\s*$')
    reNewLine = re.compile(r'\\n')
    #--Scan text file
    translator = {}
    def addTranslation(key, value):
        key   = reNewLine.sub('\n', key[:-1])
        value = reNewLine.sub('\n', value[:-1])
        if key and value: translator[key] = value
    key, value, mode = '', '', 0
    with open(txtPath) as textFile:
        for line in textFile:
            #--Blank line. Terminates key, value pair
            if reBlank.match(line):
                addTranslation(key, value)
                key, value, mode = '', '', 0
            #--Begin key input?
            elif reSource.match(line):
                addTranslation(key, value)
                key, value, mode = '', '', 1
            #--Begin value input?
            elif reValue.match(line): mode = 2
            elif mode == 1: key += line
            elif mode == 2: value += line
        addTranslation(key, value) #--In case missed last pair
    #--Write translator to pickle
    filePath = pklPath
    tempPath = filePath+'.tmp'
    cPickle.dump(translator, open(tempPath, 'w'))
    if os.path.exists(filePath): os.remove(filePath)
    os.rename(tempPath, filePath)


# Do translator test and set
currentLocale = locale.getlocale()
if locale.getlocale() == (None, None):  # Todo: Pos for Phoenix
    try: locale.setlocale(locale.LC_ALL, '')  # Polemos: Possible fix for "locale.Error: unsupported locale setting"
    except: locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # Statistics...
language = locale.getlocale()[0].split('_', 1)[0]
if language.lower() == 'german': language = 'de' #--Hack for German speakers who aren't 'DE'.
languagePkl, languageTxt = (os.path.join('locale', language+ext) for ext in ('.pkl', '.txt'))

#--Recompile pkl file?
if os.path.exists(languageTxt) and (not os.path.exists(languagePkl) or (os.path.getmtime(languageTxt) > os.path.getmtime(languagePkl))):
    compileTranslator(languageTxt, languagePkl)

#--Use dictionary from pickle as translator
if os.path.exists(languagePkl):
    with open(languagePkl) as pklFile:
        _translator = cPickle.load(pklFile)
    def _(text): return _translator.get(text, text)
else:
    def _(text): return text


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
