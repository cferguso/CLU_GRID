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
class ForceExit(Exception):
    pass

def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:

        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                #arcpy.AddMessage("    ")
                arcpy.AddError(string)

    except:
        pass


def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
        AddMsgAndPrint(theMsg, 2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

def keyCollector(grid):

    try:

        mkLst =[]
        with arcpy.da.SearchCursor(grid, "MUKEY") as rows:
            for row in rows:
                mKey = str(row[0])
                if not mKey in mkLst:
                    mkLst.append(mKey)
        #arcpy.AddMessage(mLst)
        return True, mkLst

    except:
        errorMsg()
        return False, 'Error in collecting mukeys'




def sdaInfo(mukeys):

    import socket
    import xml.etree.cElementTree as ET

    mukeys = ','.join(mukeys)

    try:

        ordLst = ['AREASYMBOL', 'MUSYM', 'MUNAME', 'MUKEY', 'OM_WTA']
        strFlds = ['AREASYMBOL', 'MUSYM', 'MUNAME', 'MUKEY']
        fltFlds = ['OM_WTA']

        funcDict = {}

        sdaQry = " SELECT AREASYMBOL, MUSYM, MUNAME, MUKEY\n"\
        " INTO #kitchensink\n"\
        " FROM legend  AS lks\n"\
        " INNER JOIN  mapunit AS muks ON muks.lkey = lks.lkey AND muks.mukey IN (" + mukeys + ")\n"\
        " \n"\
        " SELECT mu1.mukey, cokey, comppct_r, \n"\
        " SUM (comppct_r) over(partition by mu1.mukey ) AS SUM_COMP_PCT\n"\
        " \n"\
        "  \n"\
        " INTO #comp_temp\n"\
        " FROM legend  AS l1\n"\
        " INNER JOIN  mapunit AS mu1 ON mu1.lkey = l1.lkey AND mu1.MUKEY IN (" + mukeys + ")\n"\
        " INNER JOIN  component AS c1 ON c1.mukey = mu1.mukey AND majcompflag = 'Yes'\n"\
        " \n"\
        " \n"\
        " SELECT cokey, SUM_COMP_PCT, \n"\
        " CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST (CAST (comppct_r AS  decimal (5,2)) / CAST (SUM_COMP_PCT AS decimal (5,2)) AS decimal (5,2)) END AS WEIGHTED_COMP_PCT \n"\
        " INTO #comp_temp3\n"\
        " FROM #comp_temp\n"\
        " \n"\
        " \n"\
        " \n"\
        " SELECT \n"\
        "  areasymbol, musym, muname, mu.mukey/1  AS MUKEY, c.cokey AS COKEY, chorizon.chkey/1 AS CHKEY, compname, hzname, hzdept_r, hzdepb_r, \n"\
        " \n"\
        " comppct_r, \n"\
        " \n"\
        " CAST (ISNULL (om_r, 0) AS decimal (5,2))AS om_r\n"\
        " INTO #main\n"\
        " FROM legend  AS l\n"\
        " INNER JOIN  mapunit AS mu ON mu.lkey = l.lkey AND mu.mukey IN (" + mukeys + ")\n"\
        " INNER JOIN  component AS c ON c.mukey = mu.mukey  \n"\
        " INNER JOIN(chorizon INNER JOIN chtexturegrp ON chorizon.chkey = chtexturegrp.chkey) ON c.cokey = chorizon.cokey\n"\
        " AND (((chorizon.hzdept_r)=(SELECT Min(chorizon.hzdept_r) AS MinOfhzdept_r\n"\
        " FROM chorizon INNER JOIN chtexturegrp ON chorizon.chkey = chtexturegrp.chkey\n"\
        " AND chtexturegrp.texture Not In ('SPM','HPM', 'MPM') AND chtexturegrp.rvindicator='Yes' AND c.cokey = chorizon.cokey ))AND ((chtexturegrp.rvindicator)='Yes'))\n"\
        " ORDER BY areasymbol, musym, muname, mu.mukey, comppct_r DESC, cokey,  hzdept_r, hzdepb_r\n"\
        " \n"\
        " \n"\
        " \n"\
        " SELECT #main.areasymbol, #main.musym, #main.muname, #main.MUKEY, \n"\
        " #main.COKEY, #main.CHKEY, #main.compname, hzname, hzdept_r, hzdepb_r, \n"\
        " \n"\
        " om_r, \n"\
        " comppct_r, SUM_COMP_PCT, WEIGHTED_COMP_PCT ,\n"\
        " \n"\
        " SUM(om_r)over(partition by #main.COKEY)AS COMP_WEIGHTED_AVERAGE\n"\
        " \n"\
        " INTO #comp_temp2\n"\
        " FROM #main\n"\
        " INNER JOIN #comp_temp3 ON #comp_temp3.cokey=#main.cokey\n"\
        " ORDER BY #main.areasymbol, #main.musym, #main.muname, #main.MUKEY, comppct_r DESC,  #main.COKEY,  hzdept_r, hzdepb_r\n"\
        " \n"\
        " SELECT #comp_temp2.MUKEY,#comp_temp2.COKEY, WEIGHTED_COMP_PCT * COMP_WEIGHTED_AVERAGE AS COMP_WEIGHTED_AVERAGE1\n"\
        " INTO #last_step\n"\
        " FROM #comp_temp2 \n"\
        " GROUP BY  #comp_temp2.MUKEY,#comp_temp2.COKEY, WEIGHTED_COMP_PCT, COMP_WEIGHTED_AVERAGE\n"\
        " \n"\
        " SELECT areasymbol, musym, muname, \n"\
        " #kitchensink.mukey, #last_step.COKEY, \n"\
        " CAST (SUM (COMP_WEIGHTED_AVERAGE1) over(partition by #kitchensink.mukey) as decimal(5,2))AS OM_WTA\n"\
        " INTO #last_step2\n"\
        " FROM #last_step\n"\
        " RIGHT OUTER JOIN #kitchensink ON #kitchensink.mukey=#last_step.mukey \n"\
        " GROUP BY #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname, #kitchensink.mukey, COMP_WEIGHTED_AVERAGE1, #last_step.COKEY\n"\
        " ORDER BY #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname, #kitchensink.mukey\n"\
        " \n"\
        " \n"\
        " SELECT #last_step2.AREASYMBOL, #last_step2.MUSYM, #last_step2.MUNAME, \n"\
        " #last_step2.MUKEY, #last_step2.OM_WTA \n"\
        " \n"\
        " FROM #last_step2\n"\
        " LEFT OUTER JOIN #last_step ON #last_step.mukey=#last_step2.mukey \n"\
        " GROUP BY #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, #last_step2.OM_WTA\n"\
        " ORDER BY #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, #last_step2.OM_WTA\n"

        #arcpy.AddMessage(sdaQry)
        #PrintMsg(propQry.replace("&gt;", ">").replace("&lt;", "<"))

        # Send XML query to SDM Access service
        sXML = """<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
        <RunQuery xmlns="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
          <Query>""" + sdaQry + """</Query>
        </RunQuery>
        </soap12:Body>
        </soap12:Envelope>"""

        dHeaders = dict()
        dHeaders["Host"      ] = "sdmdataaccess.nrcs.usda.gov"
        #dHeaders["User-Agent"] = "NuSOAP/0.7.3 (1.114)"
        #dHeaders["Content-Type"] = "application/soap+xml; charset=utf-8"
        dHeaders["Content-Type"] = "text/xml; charset=utf-8"
        dHeaders["SOAPAction"] = "http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx/RunQuery"
        dHeaders["Content-Length"] = len(sXML)
        sURL = "SDMDataAccess.nrcs.usda.gov"

        # Create SDM connection to service using HTTP
        conn = httplib.HTTPConnection(sURL, 80)

        # Send request in XML-Soap
        conn.request("POST", "/Tabular/SDMTabularService.asmx", sXML, dHeaders)

        # Get back XML response
        response = conn.getresponse()

        cStatus = response.status
        cResponse = response.reason

        #PrintMsg(str(cStatus) + ": " + cResponse)

        xmlString = response.read()

        # Close connection to SDM
        conn.close()

        # Convert XML to tree format
        root = ET.fromstring(xmlString)

        # Iterate through XML tree, finding required elements...
        for child in root.iter('Table'):

            #create a list to accumulate values for each mapunit
            hldrLst = list()

            #loop thru the ordered list and get corresponding value from xml
            #and add it to list
            for eFld in ordLst:
                eRes = child.find(eFld).text

                #test and  convert values to appropriate data type
                #convert to None type if no value returned
                if eFld in strFlds:
                    if str(eRes):
                        eRes = eRes
                    else:
                        eRes = None

                if eFld in fltFlds:
                    try:
                        eRes = float(eRes)
                    except:
                        eRes = None

                hldrLst.append(eRes)

            #put the list for each mapunit into a dictionary.  dict keys are mukeys.
            funcDict[hldrLst[-2]]= hldrLst

        #arcpy.AddMessage(funcDict)

        return True, funcDict

    except socket.timeout as e:
        Msg = 'Soil Data Access timeout error'
        return False, Msg

    except socket.error as e:
        Msg = 'Socket error: ' + str(e)
        return False, Msg

    except:
        errorMsg()
        Msg = 'Unknown error collecting data from Soil Data Access'
        return False, Msg

#===============================================================================

import sys, os, math, httplib, traceback, collections, arcpy

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
# need to add a raise exception if it's a remote db
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


##try:
##    arcpy.management.Delete("in_memory")
##except:
##    pass
##
##netMemory = "in_memory" + os.sep + "netMemory"

if wsType == 'FileSystem':
    fullGrid = ws + os.sep + 'grid.shp'
    cluxssurgo = ws + os.sep + 'clu_x_ssurgo.shp'
else:
    fullGrid = ws + os.sep + 'grid'
    cluxssurgo = ws + os.sep + 'clu_x_ssurgo'



arcpy.management.CreateFishnet(fullGrid, ll, ornAxs, cDMet, cDMet, None, None, oppCorner, False , None, "POLYGON")


arcpy.management.DefineProjection(fullGrid, arcpy.Describe(tLyr).spatialReference)

arcpy.management.AddField(fullGrid, "acres", "FLOAT")

arcpy.management.AddField(fullGrid, "OM_WTA", "FLOAT", field_is_nullable = "NULLABLE")
arcpy.management.AddField(fullGrid, "OM_PP", "FLOAT")
arcpy.management.AddField(fullGrid, "OM_SUM", "FLOAT")

arcpy.AddMessage("Added field successfully")
arcpy.management.CalculateField(fullGrid, "acres", "!SHAPE.area@ACRES!", "PYTHON")

# do the intersect

infFeats = [tLyr, sLyr, fullGrid]
arcpy.env.addOutputsToMap = True
arcpy.analysis.Intersect(infFeats, cluxssurgo)
arcpy.management.CalculateField(cluxssurgo, "acres", "!SHAPE.area@ACRES!", "PYTHON")

#clean up the attribute table a little, must keep mukey for SDA query
delFlds = ['Id', 'STATECD', 'COUNTYCD', 'COMMENTS', 'CALCACRES', 'FSA_ACRES', 'ADMNSTATE', 'ADMNCOUNTY', 'AREASYMBOL', 'SPATIALVER']

##descFlds = [x.name for x in arcpy.Describe(cluxssurgo).fields]
##for fld in descFlds:
##    if fld in delFlds:
arcpy.management.DeleteField(cluxssurgo, delFlds)



#collect and return the mukeys from the intersect layer
kC1, kC2 = keyCollector(cluxssurgo)

#pass the mukeys to query
if kC1:

    #calling SDA, are you home?
    sI1, sI2 = sdaInfo(kC2)

    if sI1:

        #collectively these cursors are probably better off in a function
        #but we'll leave them here for now...


        with arcpy.da.Editor(ws) as edit:
            #edit.startEditing(False, True)
            with arcpy.da.UpdateCursor(cluxssurgo, ["MUKEY", "OM_WTA"]) as rows:
                for row in rows:
                    # funcDict collected lists, OM_WTA is the 5th item
                    theWTA = sI2.get(row[0])
                    theVal = theWTA[4]
                    if theVal == None:
                        theVal = 0
                    #arcpy.AddMessage(theVal)
                    row[1] = theVal
                    rows.updateRow(row)
            del theVal
            del row, rows

            #sum the total acreage of each grid - not all grids will total the user acre parameter
            soilGrdAc = dict()
            with arcpy.da.SearchCursor(cluxssurgo, ['FID_grid', 'acres']) as rows:
                for row in rows:
                    fid = str(row[0])
                    if not fid in soilGrdAc:
                        soilGrdAc[fid] = row[1]
                    else:
                        hldrVal = soilGrdAc.get(fid)
                        soilGrdAc[fid] = hldrVal + row[1]
            del row, rows, hldrVal

        #edit.stopEditing(True)
        #del edit

        #with arcpy.da.Editor(ws) as edit:
            #edit.startEditing(False, True)

            sDict = collections.OrderedDict(sorted(soilGrdAc.items()))
            for k,v in sDict.iteritems():
                arcpy.AddMessage(k + "::" + str(v))

        with arcpy.da.UpdateCursor(cluxssurgo, ["FID_grid", "acres", "OM_WTA", "OM_PP"]) as rows:
            for row in rows:
                #had to cast FID_grid to str, an hour lost -- argh!
                totalAc = soilGrdAc.get(str(row[0]))
                rowAc = row[1]
                if rowAc == None:
                    rowAc = 0
                omWTA = row[2]
                #thePrint = str(omWTA) + "* (" + str(rowAc) + "/" + str(totalAc) + ")"
                theVal = omWTA * (rowAc /totalAc)
                row[3] = theVal
                rows.updateRow(row)
            del row, rows

##        totalOM = dict()
##        with arcpy.da.UpdateCursor(cluxssurgo, ['FID_grid', 'OM_PP']) as rows:
##            for row in rows:
##                fid = str(row[0])
##                if not fid in totalOM:
##                    totalOM[fid] = row[1]
##                else:
##                    hldrVal = totalOM.get(fid)
##                    totalOM[fid] = hldrVal + row[1]
##
##        del row, rows, fid, hldrVal

        sumOM =dict()
        with arcpy.da.UpdateCursor(cluxssurgo, ['FID_grid', 'OM_PP', 'OM_SUM']) as rows:
            for row in rows:
                fid = str(row[0])
                if not fid in sumOM:
                    sumOM[fid] = row[1]
                else:
                    hldrVal = sumOM.get(fid)
                    sumOM = hldrVal + row[1]
                row[3] = sumOM






    else:
        arcpy.AddMessage(sI2)

else:
    arcpy.AddMessage(kC2)

try:
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, None)[0]
    arcpy.mapping.AddLayer(df, cluxssurgo)

except:
    pass










