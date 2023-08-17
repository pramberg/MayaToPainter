"""
The MIT License (MIT)

Copyright (c) 2018 Viktor Pramberg <hi@viktorpramberg.com>
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import webbrowser
import pymel.core as pm
import maya.OpenMayaMPx as OpenMayaMPx

cmdName = 'mayaToPainter'
version = "1.0.0"

# ---------------------------------------------------------------------- #
# Create environment variables for everything if they don't already exist.
# ---------------------------------------------------------------------- #

# The export directory, which is set to a folder named "mayaToPainter" in the
# user's temp folder.
if "mayaToPainterExportDirectory" not in pm.env.optionVars:
    pm.optionVar["mayaToPainterExportDirectory"] = os.path.join(
        tempfile.gettempdir(), "mayaToPainter")

defaultPainterPath = ("C:\Program Files\Allegorithmic\\"
                      "Substance Painter\substance painter.exe")

# Get the path to the Substance Painter executable.
if ("mayaToPainterSPDirectory" not in pm.env.optionVars and
        not os.path.isfile(defaultPainterPath)):
    # Bring up a file dialog if the user doesn't have a normal installation
    # of Painter.
    ret = pm.fileDialog2(dir="C:\\",
                         cap="Select path to Substance Painter",
                         fileMode=1)[0]
    pm.optionVar(sv=("mayaToPainterSPDirectory", ret))

elif ("mayaToPainterSPDirectory" not in pm.env.optionVars and
        os.path.isfile(defaultPainterPath)):
    pm.optionVar["mayaToPainterSPDirectory"] = defaultPainterPath

# Initialize the list that all exported files are added to.
if "mayaToPainterExportedFiles" not in pm.env.optionVars:
    pm.optionVar(sva=("mayaToPainterExportedFiles", ""))
    pm.optionVar(ca="mayaToPainterExportedFiles")

# Holds the settings for Split by UDIMs
if "mayaToPainterSplitByUDIMs" not in pm.env.optionVars:
    pm.optionVar(iv=("mayaToPainterSplitByUDIMs", 0))

# When this is true Substance Painter will bake the current project
if "mayaToPainterShouldBake" not in pm.env.optionVars:
    pm.optionVar(iv=("mayaToPainterShouldBake", 0))

# When this is true Substance Painter will bake the current project
if "mayaToPainterSameWidthHeight" not in pm.env.optionVars:
    pm.optionVar(iv=("mayaToPainterSameWidthHeight", True))


# Function for adding files that are exported to a variable, so
# they can be deleted later, if the user wants to.
def addObjectToList(aObj):
    for obj in pm.optionVar["mayaToPainterExportedFiles"]:
        if aObj in obj:
            return
    pm.optionVar(sva=("mayaToPainterExportedFiles", aObj))


# Export multiple objects in a single selection. Used when multiple
# objects are selected that aren't named "_high" and "_low"
# or the length of the selection is greater than 2.
def exportMutliple(aSelection):
    exportName = pm.promptDialog(title='Object Name',
                                 message=('Enter the name of '
                                          'the exported fbx:'),
                                 button=['OK', 'Cancel'],
                                 defaultButton='OK',
                                 cancelButton='Cancel',
                                 dismissString='Cancel')
    if exportName == 'OK':
        text = pm.promptDialog(query=True, text=True)
        if text != '':
            if '.fbx' in text:
                text = text
            elif '.FBX' in text:
                text = text
            else:
                text = text + '.fbx'
        else:
            pm.warning(('No object sent to Substance Painter: '
                        'No export name specified'))
            return
    else:
        pm.warning(('No object sent to Substance Painter: '
                    'No export name specified'))
        return

    filename = os.path.join(pm.optionVar["mayaToPainterExportDirectory"],
                            "%s" % text)
    shouldUpdateMesh = os.path.exists(filename)
    nodes = pm.ls(sl=1, dag=1)
    inConnections = list(set(pm.listConnections(nodes[1],
                                                type="shadingEngine")))
    for sg in inConnections:
        if ("initialShadingGroup" in sg.name() and
                len(inConnections) == 1):
            mat = pm.shadingNode('blinn', asShader=True, name=text[0:-4])
            shadingGroup = pm.sets(renderable=True,
                                   noSurfaceShader=True,
                                   empty=True,
                                   name=mat + '_SG')
            pm.connectAttr('%s.outColor' % mat,
                           '%s.surfaceShader' % shadingGroup)
            for obj in aSelection:
                pm.sets(shadingGroup, forceElement=obj)

    pm.mel.FBXResetExport()
    pm.select(aSelection)
    pm.mel.FBXExport(s=True, f=filename)
    addObjectToList(filename)
    painterObj = filename

    for sg in inConnections:
        if ("initialShadingGroup" in sg.name() and
                len(inConnections) == 1):
            # Remove material
            materials = pm.ls(mat=True)
            for mat in materials:
                if text[0:-4] in mat.name():
                    pm.delete(mat)

            fileNodes = pm.ls(typ='shadingEngine')
            for node in fileNodes:
                if (aSelection[0] + '_TS' in node.name() and
                        '_SG' in node.name()):
                    pm.delete(node)

            pm.sets('initialShadingGroup', forceElement=aSelection)
    return [painterObj, shouldUpdateMesh]


# THANK YOU to "ewerybody" on StackOverflow for this function that checks
# if a process exists!
# Link: https://stackoverflow.com/a/29275361
def processExists(aProcessname):
    tlcall = 'TASKLIST', '/FI', 'imagename eq %s' % aProcessname
    # shell=True hides the shell window, stdout to PIPE enables
    # communicate() to get the tasklist command result
    tlproc = subprocess.Popen(tlcall, shell=True, stdout=subprocess.PIPE)
    # trimming it to the actual lines with information
    tlout = tlproc.communicate()[0].strip().split('\r\n')
    # if TASKLIST returns single line without processname: it's not running
    if len(tlout) > 1 and aProcessname in tlout[-1]:
        return True
    else:
        return False


# Verify that the path to Substance Painter is valid. Is run before every
# export and when opening and closing the options.
def verifyPaths():
    spDir = pm.optionVar["mayaToPainterSPDirectory"]
    if not os.path.isdir(pm.optionVar["mayaToPainterExportDirectory"]):
        pm.error(pm.optionVar["mayaToPainterExportDirectory"] +
                 ' is not a path.')
    if ("substance painter.exe" not in spDir or
            "Substance Painter.exe" not in spDir):
        painterExe = False
    else:
        painterExe = True

    if not os.path.isfile(spDir):
        pm.error('Substance Painter executable not found: ' + spDir +
                 (' is not a file. You need to change path '
                  'inside the option-box.'))
    elif os.path.isfile(spDir) and painterExe:
        pm.error('Substance Painter executable not found: ' + spDir +
                 (' is not a Substance Painter executable.'
                  'You need to change path inside the option-box.'))


# Main export function that determines what type of selection the user has
# made, and handles it appropriately.
def sendToPainter():
    verifyPaths()
    painterObj = ''
    selection = pm.ls(sl=True)
    exportDir = pm.optionVar["mayaToPainterExportDirectory"]

    try:
        tempPath = os.path.join(tempfile.gettempdir(), "mayaToPainter")
        if exportDir == tempPath:
            os.makedirs(tempPath)
    except:
        pass

    shouldUpdateMesh = False
    if len(selection) == 0:
        pm.warning("No object selected: Can't send to Substance Painter")
        return

    if len(selection) == 2:
        # Need to check if the selection is one high and one low before the
        # actual function. Exit this block and do the fallback export
        # otherwise.
        for obj in selection:
            if "_low" in obj.name():
                filename = os.path.join(exportDir, "%s.fbx" % obj)
                shouldUpdateMesh = os.path.exists(filename)

                nodes = pm.ls(sl=1, dag=1)
                inConnections = pm.listConnections(nodes[1],
                                                   type="shadingEngine")
                inConnections = list(set(inConnections))
                for sg in inConnections:
                    if ("initialShadingGroup" in sg.name() and
                            len(inConnections) == 1):
                        mat = pm.shadingNode('blinn',
                                             asShader=True,
                                             name=obj[0:-4])
                        shadingGroup = pm.sets(renderable=True,
                                               noSurfaceShader=True,
                                               empty=True,
                                               name=mat + '_SG')
                        pm.connectAttr('%s.outColor' % mat,
                                       '%s.surfaceShader' % shadingGroup)
                        pm.sets(shadingGroup, forceElement=obj)

                pm.mel.FBXResetExport()
                pm.select(obj)
                pm.mel.FBXExport(s=True, f=filename)
                addObjectToList(filename)
                painterObj = filename

                for sg in inConnections:
                    if ("initialShadingGroup" in sg.name() and
                            len(inConnections) == 1):
                        # Remove material
                        materials = pm.ls(mat=True)
                        for mat in materials:
                            if obj[0:-4] in mat.name():
                                pm.delete(mat)

                        fileNodes = pm.ls(typ='shadingEngine')
                        for node in fileNodes:
                            if (obj + '_TS' in node.name() and
                                    '_SG' in node.name()):
                                pm.delete(node)

                        pm.sets('initialShadingGroup', forceElement=obj)

            elif "_high" in obj.name():
                filename = os.path.join(exportDir, "%s.fbx" % obj)
                shouldUpdateMesh = os.path.exists(filename)
                pm.mel.FBXResetExport()
                pm.select(obj)
                pm.mel.FBXExport(s=True, f=filename)
                addObjectToList(filename)
            else:
                # If one of the objects isn't specified as a high or lowpoly,
                # export it as a multi-export.
                output = exportMutliple(selection)
                painterObj = output[0]
                shouldUpdateMesh = output[1]
                break

    elif len(selection) == 1:
        filename = os.path.join(exportDir, "%s.fbx" % selection[0])
        shouldUpdateMesh = os.path.exists(filename)
        nodes = pm.ls(sl=1, dag=1)
        inConnections = pm.listConnections(nodes[1], type="shadingEngine")
        inConnections = list(set(inConnections))
        for sg in inConnections:
            if ("initialShadingGroup" in sg.name() and
                    len(inConnections) == 1):
                mat = pm.shadingNode('blinn',
                                     asShader=True,
                                     name=selection[0] + '_TS')
                shadingGroup = pm.sets(renderable=True,
                                       noSurfaceShader=True,
                                       empty=True,
                                       name=mat + '_SG')
                pm.connectAttr('%s.outColor' % mat,
                               '%s.surfaceShader' % shadingGroup)
                pm.sets(shadingGroup, forceElement=selection[0])

        pm.mel.FBXResetExport()
        pm.select(selection)
        pm.mel.FBXExport(s=True, f=filename)
        addObjectToList(filename)
        painterObj = filename
        for sg in inConnections:
            if ("initialShadingGroup" in sg.name() and
                    len(inConnections) == 1):
                # Remove material
                materials = pm.ls(mat=True)
                for mat in materials:
                    if selection[0] + '_TS' in mat.name():
                        pm.delete(mat)

                fileNodes = pm.ls(typ='shadingEngine')
                for node in fileNodes:
                    if (selection[0] + '_TS' in node.name() and
                            '_SG' in node.name()):
                        pm.delete(node)

                pm.sets('initialShadingGroup', forceElement=selection[0])

    else:
        output = exportMutliple(selection)
        painterObj = output[0]
        shouldUpdateMesh = output[1]

    # Only update the JSON-file if the user has exported.
    # This prevents Painter from baking when the toggle is pressed, only when
    # the user expects the plugin to start baking.
    updateAutoBakeJSON()

    if processExists('Substance Painter.exe') and shouldUpdateMesh:
        print('Meshes updated!')
        return

    # Split by UDIM is only applicable on project creation.
    splitByUDIM = pm.optionVar["mayaToPainterSplitByUDIMs"]

    # Used when creating a detached process. If it isn't used,
    # Substance Painter needs to be closed before Maya can be
    # closed.
    DETACHED_PROCESS = 0x00000008
    if (splitByUDIM):
        arguments = [
            pm.optionVar["mayaToPainterSPDirectory"],
            "--mesh",
            painterObj,
            "--split-by-udim"
        ]
        subprocess.Popen(arguments,
                         close_fds=True,
                         creationflags=DETACHED_PROCESS)
    else:
        # Create a completely detached process, so Maya can be closed while
        # Painter is still running.
        arguments = [
            pm.optionVar["mayaToPainterSPDirectory"],
            "--mesh",
            painterObj
        ]
        subprocess.Popen(arguments,
                         close_fds=True,
                         creationflags=DETACHED_PROCESS)


def changeExportPath():
    # Change export path
    try:
        exportDir = pm.optionVar["mayaToPainterExportDirectory"]
        ret = pm.fileDialog2(dir=exportDir,
                             cap="Select export path",
                             fileMode=2)[0]
    except KeyError:
        ret = pm.fileDialog2(cap="Select export path",
                             fileMode=2)[0]
    except TypeError:
        return
    if (os.path.isdir(ret)):
        pm.optionVar["mayaToPainterExportDirectory"] = ret
    else:
        print("Selected path isn\'t a directory: %s" % ret)
    pm.textField("exportPath0", e=True,
                 tx=pm.optionVar["mayaToPainterExportDirectory"])
    pm.textField("exportPath1", e=True,
                 tx=pm.optionVar["mayaToPainterExportDirectory"])


def changePainterPath():
    try:
        ret = pm.fileDialog2(dir=pm.optionVar["mayaToPainterSPDirectory"],
                             cap="Select path to Substance Painter",
                             fileMode=1)[0]
    except KeyError:
        ret = pm.fileDialog2(cap="Select path to Substance Painter",
                             fileMode=1)[0]
    except TypeError:
        return
    if (os.path.isfile(ret)):
        pm.optionVar["mayaToPainterSPDirectory"] = ret
    else:
        print("Selected file doesn\'t exist: %s" % ret)
    pm.textField("painterPath", e=True,
                 tx=pm.optionVar["mayaToPainterSPDirectory"])


def resetExportPath():
    pm.optionVar["mayaToPainterExportDirectory"] = os.path.join(
        tempfile.gettempdir(),
        "mayaToPainter")
    pm.textField("exportPath0", e=True,
                 tx=pm.optionVar["mayaToPainterExportDirectory"])
    pm.textField("exportPath1", e=True,
                 tx=pm.optionVar["mayaToPainterExportDirectory"])


def resetPainterPath():
    pm.optionVar["mayaToPainterSPDirectory"] = defaultPainterPath
    pm.textField("painterPath", e=True,
                 tx=pm.optionVar["mayaToPainterSPDirectory"])


# Remove the temp-folder that was created initially, and used as the default
# export path.
def removeTempFolder():
    temp = os.path.join(tempfile.gettempdir(), "mayaToPainter")
    if os.listdir(temp) != 0:
        msg = ('Do you want to remove the temp folder '
               'that was created by this plugin, and all files in it?')
        rd = pm.confirmDialog(title='Clean up',
                              message=msg,
                              button=['Yes', 'No'],
                              defaultButton='No',
                              cancelButton='No',
                              dismissString='No',
                              ma='center')
        if rd == 'Yes':
            shutil.rmtree(temp)
            print('Removed ' + temp)
        else:
            print('Your temporary files are safe!')


# Functions for handling the removal of exported fbx-files.
def removeAllTempFiles():
    for index, file in enumerate(pm.optionVar["mayaToPainterExportedFiles"]):
        if os.path.isfile(file):
            os.remove(file)
            pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
            print(file + " removed")
        else:
            # Remove from optionVar
            pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
        assbin = file[0:-3] + "assbin"
        if os.path.isfile(assbin):
            os.remove(assbin)
            print(assbin + " removed")


def removeLowTempFiles():
    for index, file in enumerate(pm.optionVar["mayaToPainterExportedFiles"]):
        if "_low" in file:
            if os.path.isfile(file):
                os.remove(file)
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
                print(file + " removed")
            else:
                # Remove from optionVar
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
            assbin = file[0:-3] + "assbin"
            if os.path.isfile(assbin):
                os.remove(assbin)
                print(assbin + " removed")


def removeHighTempFiles():
    for index, file in enumerate(pm.optionVar["mayaToPainterExportedFiles"]):
        if "_high" in file:
            if os.path.isfile(file):
                os.remove(file)
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
                print(file + " removed")
            else:
                # Remove from optionVar
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
            assbin = file[0:-3] + "assbin"
            if os.path.isfile(assbin):
                os.remove(assbin)
                print(assbin + " removed")


def removeNotLowHighTempFiles():
    for index, file in enumerate(pm.optionVar["mayaToPainterExportedFiles"]):
        if "_high" not in file and "_low" not in file:
            if os.path.isfile(file):
                os.remove(file)
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
                print(file + " removed")
            else:
                # Remove from optionVar
                pm.optionVar(rfa=("mayaToPainterExportedFiles", index))
            assbin = file[0:-3] + "assbin"
            if os.path.isfile(assbin):
                os.remove(assbin)
                print(assbin + " removed")


def openCurrentTempFolder():
    webbrowser.open(pm.optionVar["mayaToPainterExportDirectory"])


def updateExportPath(aField):
    pm.optionVar["mayaToPainterExportDirectory"] = pm.textField('exportPath' +
                                                                str(aField),
                                                                q=True,
                                                                tx=True)
    exportDir = pm.optionVar["mayaToPainterExportDirectory"]
    pm.textField('exportPath0', e=True,
                 tx=exportDir)
    pm.textField('exportPath1', e=True,
                 tx=exportDir)
    if not os.path.isdir(exportDir):
        os.mkdir(exportDir)
    print('New export path is: ' + exportDir)


def updatePainterPath():
    pm.optionVar["mayaToPainterSPDirectory"] = pm.textField('painterPath',
                                                            q=True,
                                                            tx=True)
    painterDir = pm.optionVar["mayaToPainterSPDirectory"]
    if not os.path.isfile(painterDir):
        pm.error('Substance Painter executable not found: ' + painterDir +
                 (' is not a file. You need to change path '
                  'inside the option-box.'))
    elif (os.path.isfile(painterDir) and
            "substance painter.exe" not in painterDir):
        pm.error('Substance Painter executable not found: ' + painterDir +
                 (' is not a Substance Painter executable. '
                  'You need to change path inside the option-box.'))
    else:
        print('Substance Painter executable found!')


def updateSplitByUDIMs():
    pm.optionVar["mayaToPainterSplitByUDIMs"] = pm.checkBox("UDIMToggle",
                                                            q=True,
                                                            v=True)


def updateAutoBake():
    pm.optionVar["mayaToPainterShouldBake"] = pm.checkBox("AutoBakeToggle",
                                                          q=True,
                                                          v=True)
    updateBakingParametersJSON()


# Made this a function because it may need to change to support users who
# have moved their Documents folder.
# Haven't tested if this solution works for that case.
def getPathToPainterPlugin():
    path = '~/Allegorithmic/Substance Painter/plugins/maya-to-painter/'
    return os.path.expanduser(path)


# Update the shouldBake.json that is in the Painter plugin path with the
# current value in the options.
def updateAutoBakeJSON():
    pathToPainterPlugin = getPathToPainterPlugin()
    with open(pathToPainterPlugin + 'shouldBake.json', 'r') as shouldBakeJSON:
        obj = json.loads(shouldBakeJSON.read())
        obj['shouldBake'] = pm.optionVar["mayaToPainterShouldBake"]
    with open(pathToPainterPlugin + 'shouldBake.json', 'w') as shouldBakeJSON:
        json.dump(obj, shouldBakeJSON)


def sendToPainterOptionsButton(aWindow):
    sendToPainter()
    pm.deleteUI(aWindow, window=True)


# Update desired baking parameters.
def updateBakingParametersJSON():
    pathToPainterPlugin = getPathToPainterPlugin()
    jsonFile = pathToPainterPlugin + 'bakingParameters.json'
    with open(jsonFile, 'r') as shouldBakeJSON:
        obj = json.loads(shouldBakeJSON.read())


# This is what Painter expects in their baking parameters.
resolutions = {
    '32': 5,
    '64': 6,
    '128': 7,
    '256': 8,
    '512': 9,
    '1024': 10,
    '2048': 11,
    '4096': 12,
    '8192': 13,
}

# This is what I need to display them in Maya.
read_resolutions = {
    5: '32',
    6: '64',
    7: '128',
    8: '256',
    9: '512',
    10: '1024',
    11: '2048',
    12: '4096',
    13: '8192',
}


def updateXResolution(aMenuItem):
    pathToPainterPlugin = getPathToPainterPlugin()
    jsonFile = pathToPainterPlugin + 'bakingParameters.json'
    with open(jsonFile, 'r') as shouldBakeJSON:
        obj = json.loads(shouldBakeJSON.read())
        obj["Output_Size"][0] = resolutions[aMenuItem]
    with open(jsonFile, 'w') as shouldBakeJSON:
        json.dump(obj, shouldBakeJSON)
    if (pm.optionVar["mayaToPainterSameWidthHeight"]):
        pm.optionMenu("YResolution", e=True,
                      v=pm.optionMenu("XResolution",
                                      q=True,
                                      v=True))
        updateYResolution(aMenuItem)


def updateYResolution(aMenuItem):
    pathToPainterPlugin = getPathToPainterPlugin()
    jsonFile = pathToPainterPlugin + 'bakingParameters.json'
    with open(jsonFile, 'r') as shouldBakeJSON:
        obj = json.loads(shouldBakeJSON.read())
        obj["Output_Size"][1] = resolutions[aMenuItem]
    with open(jsonFile, 'w') as shouldBakeJSON:
        json.dump(obj, shouldBakeJSON)


def createResolutionDropdown(aLayout):
    horz = pm.horizontalLayout(ratios=[1], parent=aLayout)
    pm.text("ResolutionLabel", label="Resolution", parent=horz,
            al="left", fn="smallPlainLabelFont")
    pm.checkBox("ResolutionToggle", label="Same Width/Height", parent=horz,
                al="left", v=pm.optionVar["mayaToPainterSameWidthHeight"],
                cc=pm.Callback(updateSameWidthHeight))

    horz2 = pm.horizontalLayout(ratios=[1], parent=aLayout)
    pm.optionMenu("XResolution", cc=updateXResolution, parent=horz2)
    pm.menuItem(label='32')
    pm.menuItem(label='64')
    pm.menuItem(label='128')
    pm.menuItem(label='256')
    pm.menuItem(label='512')
    pm.menuItem(label='1024')
    pm.menuItem(label='2048')
    pm.menuItem(label='4096')
    pm.menuItem(label='8192')

    pm.optionMenu("YResolution",
                  cc=updateYResolution,
                  parent=horz2,
                  en=not pm.optionVar["mayaToPainterSameWidthHeight"])
    pm.menuItem(label='32')
    pm.menuItem(label='64')
    pm.menuItem(label='128')
    pm.menuItem(label='256')
    pm.menuItem(label='512')
    pm.menuItem(label='1024')
    pm.menuItem(label='2048')
    pm.menuItem(label='4096')
    pm.menuItem(label='8192')
    horz.redistribute()
    horz2.redistribute()


def updateOptionsFromJSON():
    pathToPainterPlugin = getPathToPainterPlugin()
    jsonFile = pathToPainterPlugin + 'bakingParameters.json'
    shouldReset = False
    with open(jsonFile, 'r') as shouldBakeJSON:
        obj = json.loads(shouldBakeJSON.read())
        try:
            pm.optionMenu("XResolution",
                          e=True,
                          v=read_resolutions[obj["Output_Size"][0]])
            pm.optionMenu("YResolution",
                          e=True,
                          v=read_resolutions[obj["Output_Size"][1]])
        except KeyError:
            pm.warning("Json file is empty. Resetting it.")
            shouldReset = True
    if shouldReset:
        with open(jsonFile, 'w') as shouldBakeJSON:
            newJson = {"Antialiasing": "None",
                       "Output_Size": [7, 11],
                       "Match": "Always",
                       "Average_Normals": True}
            json.dump(newJson, shouldBakeJSON)
        updateOptionsFromJSON()


def updateSameWidthHeight():
    checkbox = pm.checkBox("ResolutionToggle", q=True, v=True)
    pm.optionVar["mayaToPainterSameWidthHeight"] = checkbox
    pm.optionMenu("YResolution", e=True,
                  en=not pm.optionVar["mayaToPainterSameWidthHeight"])
    if (pm.optionVar["mayaToPainterSameWidthHeight"]):
        pm.optionMenu("YResolution",
                      e=True,
                      v=pm.optionMenu("XResolution", q=True, v=True))


# Create options window.
def openOptions():
    window = pm.window(title="Maya To Painter Options",
                       w=330,
                       h=380,
                       cc=pm.Callback(verifyPaths))

    tabLayout = pm.tabLayout()

    ratios = [
        1, 0.25, 1,
        0.25, 1, 1,
        0.5, 0.5, 1,
        1, 1, 0.5,
        1, 1, 1.0,
        0.5, 0.5, 2
    ]
    layout = pm.verticalLayout("General Settings",
                               ratios=ratios,
                               spacing=15,
                               parent=tabLayout)

    ratios = [
        1, 0.25, 1,
        0.25, 1, 1,
        0.5, 0.5, 1,
        1, 1, 0.5,
        1, 1, 1.0,
        0.5, 0.5, 2
    ]
    pathLayout = pm.verticalLayout('Advanced Settings',
                                   ratios=ratios,
                                   spacing=15,
                                   parent=tabLayout)

    # ###################
    # Export path general
    # ###################

    pm.text("exportPathTitle1",
            label="Export path",
            parent=layout,
            al="left",
            fn="smallPlainLabelFont")
    pm.textField("exportPath1",
                 pht='Select export path',
                 tx=pm.optionVar["mayaToPainterExportDirectory"],
                 parent=layout,
                 en=True,
                 ip=0,
                 cc=pm.Callback(updateExportPath, 1))
    pathHorzLayout = pm.horizontalLayout(ratios=[1],
                                         parent=layout)
    pm.button("exportPathBtn1",
              label="Change Path",
              parent=pathHorzLayout,
              en=True,
              command=pm.Callback(changeExportPath))
    pm.button("resetExportPath1",
              label="Reset export path",
              parent=pathHorzLayout,
              command=pm.Callback(resetExportPath))
    pathHorzLayout.redistribute()
    pm.separator(parent=layout)

    # ######
    # Baking
    # ######

    bakeHorzLayout = pm.horizontalLayout(ratios=[1],
                                         parent=layout)
    pm.text("AutoBakeTitle",
            label="Auto Bake",
            parent=bakeHorzLayout,
            al="left",
            fn="smallPlainLabelFont")
    pm.checkBox("AutoBakeToggle",
                label="Auto Bake",
                parent=bakeHorzLayout,
                al="left",
                v=pm.optionVar["mayaToPainterShouldBake"],
                cc=pm.Callback(updateAutoBake))
    bakeHorzLayout.redistribute()

    pm.separator("AutoBakeSeparator",  parent=layout)

    # ##########
    # Resolution
    # ##########

    createResolutionDropdown(layout)

    pm.separator("ResolutionSeparator",  parent=layout)

    # ####
    # UDIM
    # ####

    udimHorzLayout = pm.horizontalLayout(ratios=[1],
                                         parent=layout)
    pm.text("UDIMTitle",
            label="UDIMs",
            parent=udimHorzLayout,
            al="left",
            fn="smallPlainLabelFont")
    pm.checkBox("UDIMToggle",
                label="Split by UDIM",
                parent=udimHorzLayout,
                al="left",
                v=pm.optionVar["mayaToPainterSplitByUDIMs"],
                cc=pm.Callback(updateSplitByUDIMs))
    udimHorzLayout.redistribute()
    pm.separator("UDIMSeparator",  parent=layout)

    # ####################
    # Export path advanced
    # ####################

    pm.text("exportPathTitle",
            label="Export path",
            parent=pathLayout,
            al="left",
            fn="smallPlainLabelFont")
    pm.textField("exportPath0",
                 pht='Select export path',
                 tx=pm.optionVar["mayaToPainterExportDirectory"],
                 parent=pathLayout,
                 en=True,
                 ip=0,
                 cc=pm.Callback(updateExportPath, 0))
    pathHorzLayout = pm.horizontalLayout(ratios=[1],
                                         parent=pathLayout)
    pm.button("exportPathBtn",
              label="Change Path",
              parent=pathHorzLayout,
              en=True,
              command=pm.Callback(changeExportPath))
    pm.button("resetExportPath",
              label="Reset export path",
              parent=pathHorzLayout,
              command=pm.Callback(resetExportPath))
    pathHorzLayout.redistribute()
    pm.button("exportPathExplorerBtn",
              label="Open folder in Explorer",
              parent=pathLayout,
              en=True,
              command=pm.Callback(openCurrentTempFolder))
    pm.separator(parent=pathLayout)

    # ############
    # Painter path
    # ############

    pm.text("painterPathTitle",
            label="Path to Substance Painter",
            parent=pathLayout,
            al="left",
            fn="smallPlainLabelFont")
    pm.textField("painterPath",
                 pht='Select path to Substance Painter',
                 tx=pm.optionVar["mayaToPainterSPDirectory"],
                 parent=pathLayout,
                 en=True,
                 ip=0,
                 cc=pm.Callback(updatePainterPath))
    sppathHorzLayout = pm.horizontalLayout(ratios=[1],
                                           parent=pathLayout)
    pm.button("painterPathBtn",
              label="Change Path",
              parent=sppathHorzLayout,
              en=True,
              command=pm.Callback(changePainterPath))
    pm.button("resetPainterPathBtn",
              label="Reset Painter path",
              parent=sppathHorzLayout,
              command=pm.Callback(resetPainterPath))
    sppathHorzLayout.redistribute()

    pm.separator(parent=pathLayout)

    # #######
    # Cleanup
    # #######

    pm.text("cleanupTitle",
            label="Cleanup exported files (and assbins)",
            parent=pathLayout,
            al="left",
            fn="smallPlainLabelFont")

    cleanupHorzLayout1 = pm.horizontalLayout(ratios=[1],
                                             parent=pathLayout)
    cleanupHorzLayout2 = pm.horizontalLayout(ratios=[1],
                                             parent=pathLayout)

    pm.button("cleanupAllBtn",
              label="Remove all",
              parent=cleanupHorzLayout1,
              command=pm.Callback(removeAllTempFiles))
    pm.button("cleanupAllExceptBtn",
              label="Remove all except high/low",
              parent=cleanupHorzLayout1,
              command=pm.Callback(removeNotLowHighTempFiles))

    pm.button("cleanupLowBtn",
              label="Remove low",
              parent=cleanupHorzLayout2,
              command=pm.Callback(removeLowTempFiles))
    pm.button("cleanupHighBtn",
              label="Remove high",
              parent=cleanupHorzLayout2,
              command=pm.Callback(removeHighTempFiles))

    cleanupHorzLayout1.redistribute()
    cleanupHorzLayout2.redistribute()

    # ################
    # Send to Painter!
    # ################

    pm.button("SendToPainterBtn",
              label="Send To Painter",
              parent=layout,
              command=pm.Callback(sendToPainterOptionsButton, window),
              h=50)

    layout.redistribute()
    pathLayout.redistribute()
    updateOptionsFromJSON()
    window.show()


# Do plugin stuff... This is for the main button.
class MayaToPainter(OpenMayaMPx.MPxCommand):

    def __init__(self):
        ''' Constructor. '''
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, args):
        ''' Do stuff '''
        sendToPainter()

    @staticmethod
    def cmdCreator():
        ''' Create an instance of our command. '''
        return OpenMayaMPx.asMPxPtr(MayaToPainter())


# This is for the option box.
class MayaToPainterOptions(OpenMayaMPx.MPxCommand):

    def __init__(self):
        ''' Constructor. '''
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, args):
        ''' Do stuff '''
        openOptions()

    @staticmethod
    def cmdCreator():
        ''' Create an instance of our command. '''
        return OpenMayaMPx.asMPxPtr(MayaToPainterOptions())


# These two functions are required for any plugin.
def initializePlugin(mobject):
    ''' Initialize the plug-in when Maya loads it. '''
    mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Viktor Pramberg', version)
    try:
        mplugin.registerCommand(cmdName,
                                MayaToPainter.cmdCreator)
        mplugin.registerCommand(cmdName + 'Options',
                                MayaToPainterOptions.cmdCreator)
        mplugin.addMenuItem("Send To Painter",
                            "MayaWindow|mainMeshMenu",
                            cmdName,
                            "",
                            True,
                            "mayaToPainterOptions")
        # Set the icon on the menu item.
        pm.menuItem("Send_To_Painter",
                    e=True,
                    i="mayaToPainter.png")
        try:
            os.makedirs(os.path.join(tempfile.gettempdir(), "mayaToPainter"))
            print('Created ' + os.path.join(tempfile.gettempdir(),
                                            "mayaToPainter"))
        except:
            pass
    except:
        sys.stderr.write('Failed to register command: ' + cmdName)


def uninitializePlugin(mobject):
    ''' Uninitialize the plug-in when Maya un-loads it. '''
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(cmdName)
        mplugin.deregisterCommand(cmdName + "Options")
        mplugin.removeMenuItem(["Send_To_Painter"])
        removeTempFolder()
    except:
        sys.stderr.write('Failed to unregister command: ' + cmdName)
