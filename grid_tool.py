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


arcpy.env.overwriteOutput = True


# clu layer from paramater
pLyr = arcpy.GetParameterAsText(0)

# soil polygons from parameter
sLyr = arcpy.GetParameterAsText(1)


# acres parameter
cDim = arcpy.GetParameterAsText(2)
arcpy.AddMessage(cDim)

# length of a side from acres to sq. meters
cSqM = float(cDim) * 4046.86

#sq meters to meters
cDMet = math.sqrt(cSqM)

# get user output workspace and figure out what it is
# need to add a raise exception if it is an remote db
ws = arcpy.GetParameterAsText(3)
wsType = arcpy.Describe(ws).workspaceType



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

# get the origin of the grid
ll = '%f %f' %(xMin, yMin) #str(xMin) + " " + str(yMin)

# orient the grid N/S
ornAxs = '%f %f' %(xMin, yMax) #str(xMin) + " " + str(yMax)

#find the opposite corner
xDist = xMax - xMin
yDist = yMax - yMin

xCells = int(math.ceil(xDist / cDMet))
yCells = int(math.ceil(yDist / cDMet))

upperX = xMin + (cDMet*xCells)
upperY = yMin + (cDMet*yCells)

oppCorner = '%f %f' %(upperX, upperY)

arcpy.AddMessage(xCells)
arcpy.AddMessage(yCells)

##legacy
##xDist = xMax - xMin
##yDist = yMax - yMin
##
##xCells = int(math.ceil(xDist / cDMet))
##yCells = int(math.ceil(yDist / cDMet))
##
##arcpy.management.CreateFishnet(fullGrid, ll, ornAxs, None, None, xCells, yCells, oppCorner, False, None, "POLYGON")

try:
    arcpy.management.Delete("in_memory")
except:
    pass

netMemory = "in_memory" + os.sep + "netMemory"

if wsType == 'FileSystem':
    fullGrid = ws + os.sep + 'full_grid.shp'
    cluxssurgo = ws + os.sep + 'clu_x_ssurgo.shp'
else:
    fullGrid = ws + os.sep + 'full_grid'
    cluxssurgo = ws + os.sep + 'clu_x_ssurgo'



arcpy.management.CreateFishnet(fullGrid, ll, ornAxs, cDMet, cDMet, None, None, oppCorner, False, None, "POLYGON")

arcpy.AddMessage("Created teh fnet successfully")
arcpy.management.DefineProjection(fullGrid, arcpy.Describe(tLyr).spatialReference)
arcpy.AddMessage("Added SR successfully")
arcpy.management.AddField(fullGrid, "acres", "DOUBLE")
arcpy.AddMessage("Added field successfully")
arcpy.management.CalculateField(fullGrid, "acres", "!SHAPE.area@ACRES!", "PYTHON")

# do the intersect

infFeats = [tLyr, sLyr, fullGrid]
arcpy.analysis.Intersect(infFeats, cluxssurgo)
arcpy.management.CalculateField(cluxssurgo, "acres", "!SHAPE.area@ACRES!", "PYTHON")
arcpy.env.addOutputsToMap = True





