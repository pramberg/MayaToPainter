# Maya To Painter
A plugin that vastly improves the experience of using Maya and Substance Painter together. It has features for easily working with high- and lowpoly meshes, making the process of baking much faster. It detects whether Painter is running, and updates the mesh instead of starting a new instance of Painter if the mesh already exists. 
Check out the option-box for cleaning up the temp-folder, and changing directories.
Currently, it doesn't have support for UDIMs, but if there is demand, it can be added.

## Installation
If you have a normal installation of both Maya and Painter, AND you trust this project's batch files, you can use the installer to quickly place everything where it should go. Then you just need to load the plugin in Maya's plugin manager.

Otherwise, you can follow these steps:
* Go to the `Content` folder.
* Place the `mayaToPainter.py` file in `Documents/maya/plug-ins` folder. If that folder isn't there, create it.
* If you want an item in the mesh context marking menu, also add the `scripts` folder to `Documents/maya` and add `prefs` to `Documents/maya/20##`.
* Place the `maya-to-painter` folder in `Documents/Allegorithmic/Substance Painter/plugins`
* In Maya, go to `Windows` → `Settings/Preferences` → `Plug-in Manager`
* Check the *Loaded* and *Auto load* checkboxes for `mayaToPainter.py`
* You should now have a new menu button under Maya's `Mesh` menu called `Send To Painter`. 
* If you installed to marking menu, the mesh context marking menu will have a new `Send To Painter` button at the bottom.

## Features
* Easy export of selected object(s), and open a new project in Substance Painter with that object.
* Update meshes if Painter is open, and exported file already exist.
* Auto naming of texture sets on objects with only lambert1 assigned.
* Options for user set export path, Painter path and cleanup tools.
* Optional addition: new item in context sensitive marking menu.
* For full functionality, install the Substance Painter part of the plugin.
    - Add the `maya-to-painter` folder to `Documents/Allegorithmic/Substance Painter/plugins`
    - Doing this will allow Painter to automatically add a highpoly you export using this plugin to the baking parameters.

## How to use
### Export Behavior
* No mesh selected:
    - You will get a warning telling you to select a mesh.
* One mesh selected:
    - Plugin will export to your export path, and then start Substance Painter with the selected mesh as a startup mesh.
* Two or more meshes selected:
    - Plugin will ask you for a name. This will be the name of the FBX, and also the name of the texture set, if the objects don't have any material other than lambert1. They will be exported as the same object.
* Exactly two objects selected, with "_low" AND "_high" in the end of their name:
    - Plugin will export **two** meshes, assuming you want to bake your lowpoly in Painter. If you have the Painter plugin installed, the highpoly will automatically be added to your baking parameters. **Important note**: you can also use groups here, so you can still use this when baking by mesh name.
* If you've already exported a mesh:
    - The plugin checks if there is a process called `Substance Painter.exe` running, and if there already is an object with the same export name in the export path. If both are true, it will update the mesh(es) instead of starting a new instance of Painter. To update your mesh in Painter, go to `Edit` → `Project Configuration` → `Select`. In the prompt, just press `Open` immediately, you don't need to select the mesh. Then press "OK".
    Highpoly meshes will auto-update, so all you need to do is press bake again.

### Intended use:
Create "objectName_high" and "objectName_low" groups, and put all sub-objects in those folders. When you are ready to export, select the both groups and press export. If you named your meshes inside the groups correctly, you will be able to bake in Painter using `By mesh name`. When you have a project set up, you will easily be able to iterate by sending the group(s) to Painter again.

### Settings
* Open the option-box by going to the `Modeling` menu set, open the `Mesh` menu and pressing the square button on the `Send To Painter` button.
* The `Export Path` field is where the plugin will store the temp files needed to send meshes to Painter. The default is a folder inside your temp directory.
* If you want to see what is in your temp folder, you can click the `Open folder in Explorer` button. This will open a new window of the currently selected Export path.
* The `Path to Substance Painter` field will normally not need to be changed. It will automatically add the default Painter install path. If it can't find the executable, you will get prompted to find it yourself when the plugin is first loaded.
* The `Cleanup` section handles the removal of temp files created by the plugin. **IMPORTANT**: these buttons will ONLY remove files created by this plugin, not files you've placed there yourself. It will, however remove any `.assbin` files that Painter creates when baking. 
You can choose four different options:
  * `Remove all`: Removes all exported files.
  * `Remove all except high/low`: Removes all files that don't have "_high" or "_low" in their name.
  * `Remove high`: Removes all files with "_high" in their name.

### Material / Texture Set behavior
* If all selected objects only have lambert1 shader, the plugin will create a new material during export to give you a nicer texture set name in Painter.
* If it detects ANY other shader, it will not do anything, and keep everything as it is in Maya.

## Known bugs:
* You can't exit Maya properly if an instance of Painter is running that was started from this plugin.
* Recent Maya versions aren't supported.
* This version is incompatible with recent versions of Substance Painter (since Adobe took over).