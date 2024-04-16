# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# Wrye Mash, Polemos fork Copyright (C) 2017-2021 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http: //www.gnu.org/licenses/gpl.html GPL version 2 or higher
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

import wx
from .unimash import _, defaultEncoding as defaultEncoding  # Polemos

settings = None

dataMap = {

    # Morrowind
    'Inst': 'installers',
    'Mw': 'Morrowind',
    'mlox': 'mlox.exe',
    'MGEXE': 'MGEXegui.exe',

    # OpenMW/TES3MP
    'OpenMWloc': 'OpenMW/TES3mp',
    'OpenMWConf': 'OpenMW.cfg',
    'datamods': 'mods',
    'Downloads': 'downloads',
    'mlox64': 'mlox64.exe',
    'DataFiles': 'Data Files',
    'TES3mpConf': 'pluginlist.json'
}

settingDefaults = {

    # -# SettingsWindow
    'mash.settings.pos': wx.DefaultPosition,

    # -# Wizard
    'wizard.first.openmw': True,
    'wizard.first.mw': True,

    # --Morrowind settings
    'mwDir': '',
    'sInstallersDir': None,
    # -Polemos: MGE XE
    'mgexe.detected': False,
    'mgexe.dir': '',
    # -Polemos: mlox dir
    'mloxpath': '',

    # -Polemos: OpenMW/TES3mp settings
    'openmw': False,
    'tes3mp': False,
    'openmwDir': None,
    'openmwprofile': None,
    'TES3mpConf': '',
    'datamods': None,
    'downloads': None,
    'mlox64path': '',
    'openmw.datafiles': '',
    'mashdir': None,

    # Dialog Queries
    'query.masters.update2': False,
    'query.fixit.order': False,
    'query.file.risk': False,
    'query.masters.update': False,
    'query.hideFiles.continue': False,
    'query.sortMods.continue': False,
    'query.refRemovers.continue': False,
    'query.refReplacers.continue': False,
    'query.sortRecords.continue': False,
    'query.iniTweaks.continue': False,
    'query.schedules.import.continue': False,
    'query.renumberRefs.continue': False,
    'query.removeDebrisCells.continue': False,
    'query.tes3cmd.multipatch': False,
    'query.redate.curtime.continue': False,
    'query.redate.fltime.continue': False,
    'query.linear.file.list': False,
    'query.tes3cmd.sync': False,
    'query.tes3cmd.merge': False,
    'query.mwse.max.plugins': False,
    'query.mcp.extended.map': False,

    # --Wrye Mash
    'all.ok': True,
    'mash.version': 0,  # Set later in MashApp()
    'mash.virgin': True,
    'mash.menubar.enabled': True,
    'mash.col.menu.enabled': True,
    'mash.framePos': wx.DefaultPosition,
    'mash.frameSize': (885, 550),
    'mash.frameSize.min': (400, 560),
    'mash.page': 2,
    'mash.window.sizes': {},
    'mash.bit.ver': '',

    # -Polemos: Profile
    'profile.active': 'Default',
    'profile.encoding': defaultEncoding,

    # -Polemos: Interface Settings
    'active.theme': ('Default theme', None),
    'backup.slots': 3,
    'interface.lists.color': True,
    'last.custom.cmd': False,
    'mash.large.fonts': False,
    'app.min.systray': False,
    'show.debug.log': True,

    # -Polemos: Advanced Settings
    'advanced.7zipcrc32b': False,
    'advanced.redate.interval': 60,
    'mash.extend.plugins': False,
    'mash.mcp.extend.map': False,

    # -Polemos: Date scheme for version checking (Web)
    'last.check': None,
    'timeframe.check': 15,
    'enable.check': True,
    'asked.check': False,

    # -Polemos: Common Sash Settings (Mod, Plugins, Saves Tabs)
    'mash.max.sash': 400,
    'mash.sash.window.size': (867, 395),

    # --Wrye Mash: Load Lists
    'mash.loadLists.data': {
        'Bethesda ESMs': [
            'Morrowind.esm',
            'Tribunal.esm',
            'Bloodmoon.esm',
        ],
    },

    # --Polemos: Load Lists refresh toggle.
    'mash.loadLists.need.refresh': False,

    # --Wrye Mash: Statistics
    'mash.fileStats.cols': ['Type', 'Count', 'Size'],
    'mash.fileStats.sort': 'Type',
    'mash.fileStats.colReverse': {
        'Count': 1,
        'Size': 1,
    },
    'mash.fileStats.colWidths': {
        'Type': 50,
        'Count': 50,
        'Size': 75,
    },
    'mash.fileStats.colAligns': {
        'Count': 1,
        'Size': 1,
    },

    # --Polemos: TESlint implementation.
    'tes3lint.pos': wx.DefaultPosition,
    'tes3lint.location': '',
    'tes3lint.perl': '',
    'tes3lint.last': [1, [], False, False],
    'tes3lint.command.result': u'',
    'tes3lint.refresh': True,

    # --Polemos: Added for Utilities page.
    'mash.utils.page': 0,
    'mash.utils.cols': ['ID', 'File'],  # , 'Flag'],  # Polemos: Leave the 'ID' alone.
    'mash.utils.colWidths': {
        'File': 150,
        'ID': 35,
        'Flag': 50,
    },
    'mash.utils.colAligns': {},
    'mash.utils.colReverse': {
        'File': 1,
    },
    'mash.utils.sort': 'File',
    'mash.utils.sashPos': 237,

    # --Installers
    'mash.installers.cols': ['Package', 'Order', 'Modified', 'Size', 'Files'],
    'mash.installers.page': 1,
    'mash.installers.isFirstRun': True,
    'mash.installers.enabled': True,
    'mash.installers.autoAnneal': True,
    'mash.installers.fastStart': True,
    'mash.installers.removeEmptyDirs': True,
    'mash.installers.skipDistantLOD': False,
    'mash.installers.sortProjects': False,
    'mash.installers.sortActive': False,
    'mash.installers.sortStructure': False,
    'mash.installers.conflictsReport.showLower': True,
    'mash.installers.conflictsReport.showInactive': False,
    'mash.installers.show.progress.info': False,
    'mash.installers.markers': [],
    'mash.installers.sort': 'Order',
    'mash.installers.colReverse': {},
    'mash.installers.colWidths': {
        'Package': 142,
        'Order': 43,
        'Group': 60,
        'Modified': 60,
        'Size': 60,
        'Files': 45
    },
    'mash.installers.colAligns': {
        'Order': 'RIGHT',
        'Size': 'RIGHT',
        'Files': 'RIGHT',
        'Modified': 'RIGHT'
    },

    # --Wrye Mash: Screenshots
    'mash.screens.cols': ['Image', 'Size'],
    'mash.screens.sort': 'Image',
    'mash.screens.colReverse': {
        'Image': 1,
    },
    'mash.screens.colWidths': {
        'Image': 150,
        'Size': 55,
    },
    'mash.screens.colAligns': {},
    'mash.screens.sashPos': 212,

    # --Wrye Mash: Group and Rating
    'mash.mods.groups': ['Body',
                         'Bethesda',
                         'Clothes',
                         'Creature',
                         'Fix',
                         'Last',
                         'Test',
                         'Game',
                         'GFX',
                         'Location',
                         'Misc.',
                         'NPC',
                         'Quest',
                         'Race',
                         'Resource',
                         'Sound',
                         'MWSE'],
    'mash.mods.ratings': ['+', '1', '2', '3', '4', '5', '=', '~'],

    # --Wrye Mash: RefRemovers
    'mash.refRemovers.data': {
    },
    'mash.refRemovers.safeCells': [
        _("Balmora, Caius Cosades' House"),
        _("Indarys Manor"),
        _("Raven Rock, Factor's Estate"),
        _("Rethan Manor"),
        _("Skaal Village, The Blodskaal's House"),
        _("Solstheim, Thirsk"),
        _("Tel Uvirith, Tower Lower"),
        _("Tel Uvirith, Tower Upper"),
    ],

    # --Wrye Mash: RefReplacers
    'mash.refReplacers.data': {
    },

    # --Wrye Mash: Col (Sort) Names
    # Polemos: the '    File' fixes a wx glitch, kinda.   <===#
    'mash.colNames': {
        '#': _('#'),
        'Author': _('Author'),
        'Cell': _('Cell'),
        'Count': _('Count'),
        'Day': _('Day'),
        'File': _('    File'),
        'Rating': _('Rating'),
        'Group': _('Group'),
        'Category': _('Category'),
        'Load Order': _('Load Order'),
        'Modified': _('Modified'),
        'Master': _('Master'),
        'Num': _('Num'),
        'Player': _('Player'),
        'Save Name': _('Save Name'),
        'Size': _('Size'),
        'Status': _('Status'),
        'Type': _('Type'),
        'Version': _('Version'),
        'Mod Name': _('Mod Name'),
        'Flags': _('Flags'),
        'Image': _('Image'),
        'Package': _('Package'),
        'Files': _('Files'),
        'Order': _('Order'),
        'Archive': _('Archive')
    },

    # --Polemos: ModPackages
    'mash.Packages.cols': ['Package', 'Size'],
    'mash.Packages.sort': 'Package',
    'mash.Packages.colReverse': {},
    'mash.Packages.colWidths': {
        'Package': 200,
        'Size': 37,
    },
    'mash.Packages.colAligns': {
        '#': 1,
    },

    # --Polemos: BSArchives
    'mash.Archives.cols': ['Archive', '#', 'Size'],
    'mash.Archives.sort': '#',
    'mash.Archives.colReverse': {},
    'mash.Archives.colWidths': {
        'Archive': 113,
        '#': 30,
        'Size': 27,
    },
    'mash.Archives.colAligns': {
        '#': 1,
    },

    # --Wrye Mash: Masters
    'mash.masters.cols': ['Master', '#'],
    'mash.masters.esmsFirst': 1,
    'mash.masters.selectedFirst': 0,
    'mash.masters.sort': 'Load Order',
    'mash.masters.colReverse': {},
    'mash.masters.colWidths': {
        'Master': 150,
        '#': 35,
    },
    'mash.masters.colAligns': {
        '#': 1,
    },

    # --Wrye Mash: Help Browser
    'mash.help.show': False,
    'mash.help.pos': (-1, -1),
    'mash.help.size': (1036, 600),
    'mash.help.sash': 178,

    # --Wrye Mash: Mod Notes
    'mash.modNotes.show': False,
    'mash.modNotes.size': (200, 300),
    'mash.modNotes.pos': wx.DefaultPosition,

    # --Wrye Mash: Mod Docs
    'mash.modDocs.show': False,
    'openmw.modDocs.show': False,
    'mash.modDocs.size': (700, 400),
    'mash.modDocs.pos': wx.DefaultPosition,
    'mash.modDocs.dir': None,

    # --Wrye Mash: Mods (Morrowind)
    'mash.mods.cols': ['File', '#', 'Rating', 'Group', 'Modified', 'Size', 'Author'],
    'mash.mods.esmsFirst': 1,
    'mash.mods.selectedFirst': 0,
    'mash.mods.sort': 'Modified',
    'mash.mods.colReverse': {},
    'mash.mods.colWidths': {
        '#': 30,
        'File': 200,
        'Group': 20,
        'Rating': 20,
        'Modified': 140,
        'Size': 75,
        'Author': 140,
    },
    'mash.mods.colAligns': {
        'Size': 1,
    },
    'mash.mods.renames': {},
    'mash.mods.sashPos': 655,

    # --Polemos: Plugins (OpenMW)
    'openmw.mods.cols': ['File', '#', 'Rating', 'Group', 'Size', 'Author'],
    'openmw.mods.esmsFirst': 1,
    'openmw.mods.selectedFirst': 0,
    'openmw.mods.sort': '#',
    'openmw.mods.colReverse': {},
    'openmw.mods.colWidths': {
        '#': 30,
        'File': 340,
        'Group': 20,
        'Rating': 20,
        'Size': 75,
        'Author': 140,
    },
    'openmw.mods.colAligns': {
        'Size': 1,
    },
    'openmw.mods.renames': {},

    # Polemos: OpenMW DataMods
    'mash.DataMods.packages.showHidden': False,
    'mash.datamods.cols': ['Mod Name', '#', 'Flags', 'Version', 'Category'],
    'mash.datamods.esmsFirst': 0,
    'mash.datamods.selectedFirst': 0,
    'mash.datamods.sort': '#',
    'mash.datamods.colReverse': {},
    'mash.datamods.colWidths': {
        'Mod Name': 360,
        '#': 30,
        'Flags': 40,
        'Version': 60,
        'Category': 90,
    },
    'mash.datamods.colAligns': {
        'Size': 1,
    },
    'mash.datamods.renames': {},

    # --Wrye Mash: Journal
    'mash.journal.show': False,
    'mash.journal.size': (300, 400),
    'mash.journal.pos': wx.DefaultPosition,

    # --Wrye Mash: Saves
    'mash.saves.sets': [],
    'mash.saves.cols': ['File', 'Modified', 'Size', 'Save Name', 'Player', 'Cell'],
    'mash.saves.sort': 'Modified',
    'mash.saves.colReverse': {
        'Modified': 1,
    },
    'mash.saves.colWidths': {
        'File': 128,
        'Modified': 133,
        'Size': 65,
        'Save Name': 110,
        'Player': 80,
        'Cell': 111,
        'Day': 30,
    },
    'mash.saves.colAligns': {
        'Size': 1,
    },
    'mash.saves.sashPos': 655,

    # --Polemos Mash: OpenMW Saves
    'OpenMW.saves.cols': ['File', 'Modified', 'Size', 'Save Name', 'Player'],
    'mash.worldMap.gridLines': True,
    'OpenMW.saves.sort': 'Modified',
    'OpenMW.saves.colReverse': {
        'Modified': 1,
    },
    'OpenMW.saves.colWidths': {
        'File': 189,
        'Modified': 133,
        'Size': 65,
        'Save Name': 160,
        'Player': 80,
        'Day': 30,
    },
    'OpenMW.saves.colAligns': {
        'Size': 1,
    }

}

settingsOrig = settingDefaults.copy()
