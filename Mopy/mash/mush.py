# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# This file is part of Wrye Mash Polemos fork.
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

# File Structure ==============================================================
# Record Types/Order
# - Used for record sorting.
# - Order increment flags:
#   + increment order by 1 
#   . don't increment order

recordTypes = """
TES3 +
GMST +
GLOB +
CLAS +
FACT +
RACE +
SOUN +
SKIL +
MGEF +
SCPT +
SSCR +
REGN +
BSGN +
LTEX +
SPEL +

ACTI +
ALCH +
APPA +
ARMO +
BODY +
BOOK +
CLOT +
CONT +
CREA +
DOOR +
ENCH +
INGR +
LEVC +
LEVI +
LIGH +
LOCK +
MISC +
NPC_ +
PROB +
REPA +
STAT +
WEAP +

CNTC +
CREC +
NPCC +

CELL +
LAND .
PGRD .
SNDG +
REFR +
DIAL +
INFO .

QUES +
JOUR +
KLST +
FMAP +
PCDT +
STLN +
GAME +
SPLM +
"""

# Installer
bethDataFiles = {'morrowind.esm', 'tribunal.esm', 'bloodmoon.esm', 'morrowind.bsa', 'tribunal.bsa', 'bloodmoon.bsa'}

# Game Info ===================================================================
# Skill Related

primaryAttributes = (
"Agility",
"Endurance",
"Intelligence",
"Personality",
"Speed",
"Strength",
"Willpower",
"Luck",
)

combatSkills = (
"Armorer",
"Athletics",
"Axe",
"Block",
"Blunt Weapon",
"Heavy Armor",
"Long Blade",
"Medium Armor",
"Spear",
)

magicSkills = (
"Alchemy",
"Alteration",
"Conjuration",
"Destruction",
"Enchant",
"Illusion",
"Mysticism",
"Restoration",
"Unarmored",
)

stealthSkills = (
"Acrobatics",
"Hand To Hand",
"Light Armor",
"Marksman",
"Mercantile",
"Security",
"Short Blade",
"Sneak",
"Speechcraft",
)

# Wrye Level Set ==============================================================
charSet0 = \
"""begin wr_lev${className}GS
short action
short stemp
short level

if ( menuMode )
  return

elseif ( action == 0 ) ;--Initialize
  set level to wr_lev${className}
  set action to 10
  return

elseif ( action == 10 ) ;--Option Menu
  messagebox "Choose the Way of the ${className} [level %g]?" level "Yes" "+5" "+1" "-1" "-5" "No"
  set action to 20
  return

elseif ( action == 20 ) ;--Option selected
  set stemp to getButtonPressed
  if ( stemp == -1 ) ;--Not pressed yet
  elseif ( stemp == 0 ) ; Do it
     set action to 30
  elseif ( stemp == 1 ) ; +5
    if ( level < 96 )
      set level to level + 5
      set action to 10
    endif
  elseif ( stemp == 2 ) ;+1
    if ( level < 100 )
      set level to level + 1
      set action to 10
    endif
  elseif ( stemp == 3 ) ;-1
    if ( level > 1 )
      set level to level - 1
      set action to 10
    endif
  elseif ( stemp == 4 ) ;-5
    if ( level > 5 )
      set level to level - 5
      set action to 10
    endif
  elseif ( stemp == 5 ) ;--Cancel
    set action to 100
  endif
  return

elseif ( action == 30 ) ;--Do it
  ;--Fall through

elseif ( action == 100 ) ;--Terminate
  set action to 0
  stopScript wr_lev${className}GS
  return
endif

;--Levels
set wr_lev${className} to level
set wr_levSetLevelGS.level to level
startScript wr_levSetLevelGS

;--Cap stats at level 30
if ( level > 30 )
  set level to 30
endif
"""

charSet1 = \
"""messagebox "You now follow the Way of the ${className}, level %g." level
playSound skillraise
set action to 100
end"""

# Library Generator ===========================================================
# Templates
libGenMain = (
"""begin ${libId}LS
short disabled
short action

if ( onActivate )
    if ( menuMode == 0 )
        activate
    endif
    return  
elseif ( action != lib_action )
    ;pass
elseif ( disabled != ${libId}G )
    return
elseif ( ${libId}G )
    set disabled to 0
    enable
    return
else
    set disabled to 1
    disable
    return
endif

;--Action changed...
if ( lib_action != 1 )
elseif ( ${libId}G )
elseif ( player->getItemCount "${srcId}" )
    set lib_actionCount to lib_actionCount + 1
    set ${libId}G to 1
${ifAltId}endif
set action to lib_action

end""")

libGenIfAltId = (
"""elseif ( player->getItemCount "${altId}" )
    set lib_actionCount to lib_actionCount + 1
    set ${libId}G to 1
""")

# Scheduling ==================================================================
# Templates

#--Master
scheduleMaster = (
"""begin SC_${town}_Master
dontSaveObject
if ( menuMode )
	return
elseif ( cellChanged )
	set SC_offScheduleG to 0
elseif ( SC_${town}_State == 0 )
	return
elseif ( SC_Reschedule )
	set SC_${town}_State to -1
	set SC_Reschedule to 0
elseif ( gamehour < 7 )
	if ( SC_${town}_State != 4 )
    	set SC_Reschedule to 0
		set SC_${town}_State to 4
		startScript SC_${town}_4
	endif
	${c4}startScript SC_${town}_C4
	return
elseif ( gamehour < 12 )
	if ( SC_${town}_State != 1 )
    	set SC_Reschedule to 0
		set SC_${town}_State to 1
		startScript SC_${town}_1
	endif
	return
elseif ( gamehour < 19 )
	if ( SC_${town}_State != 2 )
    	set SC_Reschedule to 0
		set SC_${town}_State to 2
		startScript SC_${town}_2
	endif
	return
else
	if ( SC_${town}_State != 3 )
    	set SC_Reschedule to 0
		set SC_${town}_State to 3
		startScript SC_${town}_3
	endif
	${c3}startScript SC_${town}_C3
	return
endif
end
""")

#--Cycle
scheduleCycle1 = (
"""begin SC_${town}_${cycle}
short action
float timer
if ( action == 0 ) ;--First pass
elseif ( action == 20 ) ;--Terminate
	set action to 0
	set timer to 0
	stopScript SC_${town}_${cycle}
	return
;--Action == 10
elseif ( SC_${town}_State != ${cycle} )
	set action to 20
	return
elseif ( getInterior )
	return
elseif ( timer < 0.5 )
	set timer to timer + getSecondsPassed
	return
else ;--Second Pass
	set action to 20
endif

if ( action == 0 )
	;messagebox "Starting SC_${town}_${cycle}"
	if ( SC_PlayBells )
		 playSound "SC_ScheduleSND"
	endif
${cycleCode}endif

""")

#--Sleep
scheduleSleep0 = (
"""begin SC_${town}_C${cycle}
;--Null sleep script. Should never be run, but just in case...
if ( cellChanged )
	set SC_Sleep to 0
	stopScript SC_${town}_C${cycle}
endif
end
""")

scheduleSleep1 = (
"""begin SC_${town}_C${cycle}
short prevState

if ( prevState != SC_${town}_State )
	set prevState to SC_${town}_State
	;Fall through
elseif ( cellChanged == 0 )
	return
endif

if ( SC_${town}_State != ${cycle} )
	set SC_Sleep to 0
	stopScript SC_${town}_C${cycle}
""")

scheduleSleep2 = (
"""else
	set SC_Sleep to 0
	stopScript SC_${town}_C${cycle}
endif
end
""")

#--Reset
scheduleReset0 = (
"""begin SC_${project}_ResetGS
;--Resets schedules to morning schedule for all towns.
float timer
short playBells
set playBells to SC_PlayBells
set SC_PlayBells to 0
if ( timer < 0 )
    set timer to timer + getSecondsPassed
    return
endif
""")

scheduleReset1 = (
"""if ( SC_${town}_State > 0 )
    messagebox "Resetting $town..."
    startScript SC_${town}_1
    set timer to -2.0
endif
""")

scheduleReset2 = (
"""messagebox "All towns reset."
set SC_PlayBells to playBells
stopScript SC_${project}_ResetGS
end""")

# Defs
scheduleDefs = """
#--Misc
stand: wander 0

#--Idles
#     stand still
#     0  shift legs
#     0  0  look behind
#     0  0  0  scratch head
#     0  0  0  0  shift clothes; hf: hands on hip
#     0  0  0  0  0  yawn
#     0  0  0  0  0  0  fingers, look around
#     0  0  0  0  0  0  0  hands to chest
#     0  0  0  0  0  0  0  0  weapon, touch head; kf: scratch head
#     0  0  0  0  0  0  0  0  0
s01:  0  5 20 40 15 60  0 10
s02:  0 15 15 20 10 40  0 25

i00:  0  5  5  5 10 10
i10:  0 10 60 20 10 10 
i30:  0 30 10 10 
i31:  0 30 20 30 30  0 15 15 # fidget/heartburn
i40:  0 40 20 10 10
i40a: 0 40 20 10 10  0 20 # fidget
i41:  0 40 20 10 10 10
i42:  0 40 20 20 10
i43:  0 40 20 20 10 10
i43a: 0 40 20 10 10  0 40 # heartburn
i44:  0 40 30 30 10
i45:  0 40 40 40 10
i46:  0 40 40 40 10 10  0 10
i50:  0 50 20 20 10
i50a: 0 50 20 10 10  0  0 10
i51:  0 50 20 20 20 10
i52:  0 50 30 30 20 10
i53:  0 50 50 10 10

i60:  0 60 20 10
i61:  0 60 20 10  0 10
i62:  0 60 20 10 10
i62a: 0 60 20 10 10  0 10
i63:  0 60 20 10 10  0  0 10 
i63a: 0 60 20 10 10  0  0 10 10 #heart/weaps
i63b: 0 60 20 10 10  0  0  0 10 #weap
i64:  0 60 20 10 10 10 
i65:  0 60 20 20 10
i65a: 0 60 20 20 20
i66:  0 60 20 20 10 10
i67:  0 60 20 20 10 10 10
i68:  0 60 20 20 20 10
i69:  0 60 20 20 20 10 10 10

i70:  0 60 30 10 10
i71:  0 60 30 30 10
i72:  0 60 30 30 10 10
i74:  0 60 30 30 10 10 10

i80:  0 60 40 30 20 10 10
i81:  0 60 40 40 10 10
i82:  0 60 40 40 20 10 10

i90:  0 60 60 10 10
i91:  0 60 60 100 10
"""
