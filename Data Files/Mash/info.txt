Mod Name Aliasing
If you make a practice of renaming your installed espm files, then Mash will not be able to match the mod in the package to the installed file. So to adjust for that, you can define a mod aliasing database.

==Setup==
After installing Mash, look for Data Files\Mash\Official_Local_default.csv, and copy it to "Official_Local.csv" in the same directory.
Updating
Open Official_Local.csv in your favorite spreadsheet program. Note that the file format is csv (comma separated values). When making changes be sure to save it in the same CSV format (with comma separators)!
You'll see that the file has two columns.
On the left is "Official" which is the "official" name of the mod, i.e. the name of the mod that you'll find in the archive package that you downloaded.
On the right is "Local", which is the "local" name of the mod, i.e. the name you prefer for the mod.
The way this works is simple -- when mash encounters a mod with a specified official name, it will map it to the local name. All install, uninstall, etc. commands will then act as if the file in the mod actually had the local name.
So to define entries, the easiest thing to do is:
Open Mash and go to the Installers tab. Find a mod for which you have changed the name.
Go to the Missing tab, select and copy the name of the missing mod, then paste that into the Official column.
Go to the Mods Tab, select the mod and copy it's name from the detail view on the right and paste that into the Local column next to the official name.
Save changes to the csv file. (Be sure to save in CSV format!)
Return to Mash Installers tab. Mash should immediately recognize the updated file and adjust for its changes.
Of course, you don't have to change mods one at a time. You can do a bunch at once and then save the file, then return to Mash.