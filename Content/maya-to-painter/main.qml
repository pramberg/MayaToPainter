import QtQuick 2.2
import Painter 1.0

PainterPlugin {
	
		tickIntervalMS: 1000
		
		onProjectOpened: {
			// Checks whether the current project is started from command line arguments.
			if (alg.project.isOpen() && alg.project.name() == "Untitled") {
				// Boolean used to enable setting the common baking parameters.
				// Setting them here doesn't work for some reason.
				// The current solution is ugly, but it works...
				alg.settings.setValue("meshFromMaya", true)
				
				var pathToLow = alg.fileIO.urlToLocalFile(alg.project.lastImportedMeshUrl())
				var pathToHigh = [pathToLow.replace("_low", "_high")]

				alg.project.settings.setValue("highpoly", pathToHigh)
			}
		}

		onComputationStatusChanged: function(isComputing)
		{
			// Try to find a highpoly if a mesh comes from Maya.
			if (alg.settings.contains("meshFromMaya")) 
			{
				if (alg.settings.value("meshFromMaya")) 
				{
					// Check if the highpoly actually exists.
					if (alg.fileIO.exists(alg.project.settings.value("highpoly")) && 
					  alg.project.settings.value("highpoly") != 
					  alg.fileIO.urlToLocalFile(alg.project.lastImportedMeshUrl())) 
				    {
						// Create the parameters that contain the highpoly meshes.
						var params = alg.baking.commonBakingParameters()
						params.detailParameters.High_Definition_Meshes = alg.project.settings.value("highpoly")
						alg.baking.setCommonBakingParameters(params)
					} 
					else 
					{
						alg.log.info("No highpoly found.")
					}
					alg.settings.remove("meshFromMaya")
				}
			}
			
			// Set the baking parameters in Maya.
			var file = alg.fileIO.open(alg.plugin_root_directory +  "bakingParameters.json", "r")
			var str = file.readAll()
			var bakingParameters = JSON.parse(str)
			file.close()
			var params = alg.baking.commonBakingParameters()
			
			bakingParameters.Output_Size = params.commonParameters.Output_Size
			bakingParameters.Antialiasing = params.detailParameters.Antialiasing
			bakingParameters.Average_Normals = params.detailParameters.Average_Normals
			bakingParameters.Match = params.detailParameters.Match
			
			str = JSON.stringify(bakingParameters)
			file = alg.fileIO.open(alg.plugin_root_directory +  "bakingParameters.json", "w")
			file.write(str)
			file.close()
			alg.settings.setValue("updateBakingParams", false)
        }
		
		onTick: {
			// Executes every second, waiting for a change in shouldBake.json. Not a pretty solution, but it works.
			var file = alg.fileIO.open(alg.plugin_root_directory +  "shouldBake.json", "r")
			var str = file.readAll()
			var shouldBakeObject = JSON.parse(str)
			file.close()
			
			// I need to do this through a separate file, because SP settings don't update when they are updated externally,
			// say, from a Python script in Maya...
			if ( !shouldBakeObject.shouldBake && alg.settings.value("updateBakingParams") )
			{
				alg.settings.setValue("updateBakingParams", false)
				// Get the desired baking parameters from Maya.
				file = alg.fileIO.open(alg.plugin_root_directory +  "bakingParameters.json", "r")
				str = file.readAll()
				var bakingParameters = JSON.parse(str)
				file.close()
				try
				{
					var params = alg.baking.commonBakingParameters()
				} 
				catch (e)
				{
					return
				}
				
				bakingParameters.Output_Size = params.commonParameters.Output_Size
				bakingParameters.Antialiasing = params.detailParameters.Antialiasing
				bakingParameters.Average_Normals = params.detailParameters.Average_Normals
				bakingParameters.Match = params.detailParameters.Match
				
				str = JSON.stringify(bakingParameters)
				file = alg.fileIO.open(alg.plugin_root_directory +  "bakingParameters.json", "w")
				file.write(str)
				file.close()

			}
			if ( shouldBakeObject.shouldBake )
			{
				file = alg.fileIO.open(alg.plugin_root_directory +  "bakingParameters.json", "r")
				str = file.readAll()
				var bakingParameters = JSON.parse(str)
				file.close()
				var params = alg.baking.commonBakingParameters()
				
				params.commonParameters.Output_Size = bakingParameters.Output_Size
				params.detailParameters.Antialiasing = bakingParameters.Antialiasing
				params.detailParameters.Average_Normals = bakingParameters.Average_Normals
				params.detailParameters.Match = bakingParameters.Match
				
				alg.baking.setCommonBakingParameters(params)
				
				// Bake all maps on each texture set of the document
				alg.mapexport.documentStructure().materials.forEach(function(material) {
					alg.baking.bake(material.name);
				});
				
				shouldBakeObject.shouldBake = 0
				str = JSON.stringify(shouldBakeObject)
				file = alg.fileIO.open(alg.plugin_root_directory +  "shouldBake.json", "w")
				file.write(str)
				file.close()
				alg.settings.setValue("updateBakingParams", true)
			}
		}
}

