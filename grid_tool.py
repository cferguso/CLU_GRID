#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Charles.Ferguson
#
# Created:     16/05/2016
# Copyright:   (c) Charles.Ferguson 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, os, math, arcpy

# 1 acre = 4046.86 sq. meters
# length of a side = 63.61 meters

arcpy.env.addOutputToMap = True
arcpy.env.overwriteOutput = True

# clu layer from paramater
pLyr = arcpy.GetParameterAsText(0)

# soil polygons
sLyr = arcpy.GetParameterAsText(1)


#acres parameter, length of side
cDim = arcpy.GetParameterAsText(2)
arcpy.AddMessage(cDim)
cSqM = float(cDim) * 4046.86
cDMet = math.sqrt(cSqM)



#create target layer from param
tLyr = arcpy.mapping.Layer(pLyr)
#sR = arcpy.Describe(tLyr).spatialReference
#arcpy.AddMessage(sR)


#get the extent of the target layer
xtnt = tLyr.getSelectedExtent()

xMin = xtnt.XMin
xMax = xtnt.XMax
yMin = xtnt.YMin
yMax = xtnt.YMax

ll = str(xMin) + " " + str(yMin)
oint = str(xMin) + " " + str(yMax)

xDist = xMax - xMin
yDist = yMax - yMin

xCells = int(math.ceil(xDist / cDMet))
yCells = int(math.ceil(yDist / cDMet))

upperX = xMin + (cDMet*xCells)
upperY = yMin + (cDMet*yCells)

oppCorner = '%f %f' %(upperX, upperY)

arcpy.AddMessage(xCells)
arcpy.AddMessage(yCells)

#arcpy.management.CreateFishnet(r"D:\Chad\GIS\PROJECT\GRID\fnet.shp", ll, oint, None, None, xCells, yCells, oppCorner, False, None, "POLYGON")
arcpy.management.CreateFishnet(r"D:\Chad\GIS\PROJECT\GRID\fnet.shp", ll, oint, cDMet, cDMet, None, None, oppCorner, False, None, "POLYGON")

arcpy.AddMessage("Created teh fnet successfully")
arcpy.management.DefineProjection(r'D:\Chad\GIS\PROJECT\GRID\fnet.shp', arcpy.Describe(tLyr).spatialReference)
arcpy.AddMessage("Added SR successfully")
arcpy.management.AddField(r"D:\Chad\GIS\PROJECT\GRID\fnet.shp", "acres", "DOUBLE")
arcpy.AddMessage("Added field successfully")
arcpy.management.CalculateField(r"D:\Chad\GIS\PROJECT\GRID\fnet.shp", "acres", "!SHAPE.area@ACRES!", "PYTHON")








