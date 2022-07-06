# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 15:54:49 2022

@author: jelisaveta.m
"""
import pandas as pd
import pyreadstat
import os
import re
import urllib.request, json
from functools import reduce

#####################################################
##### TEMPORARY #####
projectNumber = 2022103
##### TEMPORARY END #####

#stimuliLogics = [1] #if there are multiple stimuli logics, just add to a list, for istance [6,5,2]
#####################################################

dataset = st.container()
	
with dataset:
    originalSurvey = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    
    if originalSurvey is None:
        st.error("Please upload the files!")
    else:
        with open('temp.sav', "wb") as buffer:
            shutil.copyfileobj(originalSurvey, buffer)


    #pokupi klikove iz SPSS baze
        os.chdir('C:\\Users\\jelisaveta.m\\Desktop\\Decipher dashboards')
        originalSurvey, meta = pyreadstat.read_sav(os.getcwd() + '\\Raw data\\ETL\\Survey\\220613.sav', user_missing=False)
        
        clickVariables = [col for col in originalSurvey.columns if re.search('AllDataBackupNoRemoved', col) ]
        
        clickVariablesSL = {'AllDataBackupNoRemoved1' : 2, 'AllDataBackupNoRemoved2' : 2}
        
        """
        click/zone detection function
        """    
        def clickFunction (cell, sl, xAxis, yAxis, comment, time):
            inZone = [] 
            comments = []
            times = []
            try:
                def inside (dots, z, comment, time):
                    dot = dots
                    x = dot[0]
                    y = dot[1]
                    inside = False;
                    for i, j in zip((0,1,2,3), (3,0,1,2)):
                        xi = z[i]['x'] / 10
                        yi = z[i]['y'] / 10
                        xj = z[j]['x'] / 10
                        yj = z[j]['y'] / 10            
                        res = yj - yi
                        if res == 0:
                            res = 0.00000000000000000000000000000000000000001
                    
                        intersect = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (res) + xi)
                        if intersect:
                            inside = not inside
                    return inside
                
                zones = dataSL[str(cell).split('.')[0]][str(sl)]['p']
                
                if len(zones) == 0:
                    raise Exception("Zones are not defined. Check SDT or send data to AWS")
                else:
                    for idx, z in enumerate(zones):
                        if inside ([float(xAxis), float(yAxis)], z, comment, float(time)):
                            inZone.append(1)
                            comments.append(comment)
                            times.append(time)
                        else:
                            inZone.append(0)
                            comments.append("")
                            times.append(0)
            except:
                inZone.append(0)
                comments.append("")
                times.append(0)
            return ([inZone, comments, times])
         
        """
        extract coordinates and comments from the raw variable
        """
        
        def extractCoord (x, coord):
            try:
                if coord == 'x' or 'y':
                    result = re.findall(str(coord) + ' :([+-]?[0-9]+\.[0-9]+)', str(x))
                if coord == 'comm':
                    result = re.findall('explanation :(.*?)\}', str(x)) 
                if coord == 'time':
                    result = re.findall('time :(.*?)\}', str(x))
            except:
                result = [0]
            return result
        
        
        """
        functions END
        """
        clickVariablesCell = clickVariables + ['uuid', 'CELL']
        clickData = originalSurvey[clickVariablesCell]
        
        finalRes = pd.DataFrame()
        for clickVar in clickVariables: 
            clickData['X_extract'] = clickData[clickVar].apply(lambda x: extractCoord(x, 'x'))
            clickData['Y_extract'] = clickData[clickVar].apply(lambda x: extractCoord(x, 'y'))
            clickData['explanation_extract'] = clickData[clickVar].apply(lambda x: extractCoord(x, 'comm'))
            clickData['time_extract'] = clickData[clickVar].apply(lambda x: extractCoord(x, 'time'))
        	
            info = clickData[['uuid', 'CELL']]
            x_devided = pd.DataFrame(clickData["X_extract"].to_list()).add_prefix('xDevided_').reset_index(drop=True)
            y_devided = pd.DataFrame(clickData["Y_extract"].to_list()).add_prefix('yDevided_').reset_index(drop=True)
            comm_devided = pd.DataFrame(clickData["explanation_extract"].to_list()).add_prefix('commDevided_').reset_index(drop=True)
            time_devided = pd.DataFrame(clickData["time_extract"].to_list()).add_prefix('timeDevided_').reset_index(drop=True)
        	
            finalData = pd.concat([info, x_devided, y_devided, comm_devided, time_devided], axis=1)
            finalData = finalData.fillna(0)
        	
            finalDataLong = pd.wide_to_long(finalData, stubnames=['xDevided_','yDevided_','commDevided_','timeDevided_'], i='uuid', j='clickNo').reset_index()
            finalDataLongVar = finalDataLong[['uuid','CELL','clickNo','xDevided_','yDevided_','commDevided_','timeDevided_']]
            # finalDataLongVar['xDevided_'].astype(bool)
            # finalDataLongVar = finalDataLongVar[finalDataLongVar['xDevided_'].astype(bool)] 
        	
        	
        	#LINK FOR ZONES ON AWS - EXAMPLE: https://eyesee-sdt.com/get_info?project=2022031, if we ever need to transfer this from AWS to SDT
        	#awsZones = 'https://eyesee-sdt.com/get_info?project=' + str(projectNumber)
            awsStimuliLogics = 'https://eyesee-raw-stimuli-storage.s3-eu-west-1.amazonaws.com/' + str(projectNumber) + '/utils/out.json'
        	
            with urllib.request.urlopen(awsStimuliLogics) as url:
                dataSL = json.loads(url.read().decode())
        	
            structure = {}
            for key, value in dataSL.items():
                structure[key] = dataSL[key][str(clickVariablesSL[clickVar])]['s'].split('/')[5].split('_')[1].split('.')[0]
        	
            
            ######################### TEST #########################
            
            awsZones = 'https://eyesee-sdt.com/get_info?project=' + str(projectNumber)
            
            
            with urllib.request.urlopen(awsZones) as url:
                dataSL_proba = json.loads(url.read().decode())
             
            zoneLabelsCell = {}
            for key, value in structure.items():  
                zoneLabelsCell[str(key)] = {}
                for indx, zone in enumerate(json.loads(dataSL_proba[int(value) - 1]['zones_ck'])['polys']):
                    zoneLabelsCell[str(key)][indx] = zone['client']
         
            allZonesLen = []
            for x in zoneLabelsCell:
                allZonesLen.append(len(zoneLabelsCell[x]))
                
            finalClickLabels = {}
            for k, v in zoneLabelsCell[list(structure.keys())[allZonesLen.index(max(allZonesLen))]].items():
                if v == 'Dummy':
                    v = zoneLabelsCell[list(structure.keys())[allZonesLen.index(max(allZonesLen)) - 1]][k]
                finalClickLabels[k] = v
                
            binaryClick = finalDataLongVar.apply(lambda row : clickFunction(row['CELL'], clickVariablesSL[clickVar], row['xDevided_'], row['yDevided_'], row['commDevided_'], row['timeDevided_']), axis = 1)
            finalDataLongVarFin = finalDataLongVar.assign(Result = binaryClick)
            
            finalDataLongVarFin[['Clicks','Comments','Times']] = pd.DataFrame(finalDataLongVarFin["Result"].to_list())
            # resultDevided = pd.DataFrame(finalDataLongVarFin["Result"].to_list()).add_prefix('Type_')
            # resultDevided['uuid'] = finalDataLongVarFin['uuid']
            
            finalDataLongVarFin[list('ClickZone_' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Clicks'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Clicks'].to_list())
            # resultDevided_click = pd.DataFrame(resultDevided["Type_0"].to_list())
            # resultDevided_click.columns = ['ClickZone_' + str(x+1) for x in list(resultDevided_click.columns)]
            finalDataLongVarFin[list('ClickComment_' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Comments'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Comments'].to_list())
            
            # resultDevided_zones = pd.DataFrame(resultDevided["Type_1"].to_list())
            # resultDevided_zones.columns = ['ClickComment_' + str(x+1) for x in list(resultDevided_zones.columns)]
            finalDataLongVarFin[list('ClickTime_' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Times'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Times'].to_list())
            
            # resultDevided_times = pd.DataFrame(resultDevided["Type_2"].to_list())
            # resultDevided_times.columns = ['ClickTime_' + str(x+1) for x in list(resultDevided_times.columns)]
            finalDataLongVarFinal = finalDataLongVarFin
            
        	
        	
            # finalDataLongVarFinal = pd.concat([finalDataLongVarFin, resultDevided_click, resultDevided_zones, resultDevided_times], axis=1)   
        	
            clickOnly = [col for col in finalDataLongVarFin if col.startswith('ClickZone')]
            clicksFinal = finalDataLongVarFin.groupby('uuid')[clickOnly].max().reset_index(drop=False)
            clicksFinal = clicksFinal.fillna(0)
            
            commentOnly = [col for col in finalDataLongVarFinal if col.startswith('ClickComment')]
            commentsFinal = finalDataLongVarFin.groupby('uuid')[commentOnly].sum().reset_index(drop=False)
            commentsFinal = commentsFinal.replace(0, "")
            
            timeOnly = [col for col in finalDataLongVarFinal if col.startswith('ClickTime')]
            timeFinal = finalDataLongVarFin.groupby('uuid')[timeOnly].sum().reset_index(drop=False)
            timeFinal = timeFinal.replace(0, "")
            
            allAggDatabases = [clicksFinal, commentsFinal, timeFinal]   
            finalDataLongVarFinal = reduce(lambda  left,right: pd.merge(left,right,on=['uuid'], how='outer'), allAggDatabases)
            
            
            if finalRes.empty:
                finalRes = originalSurvey.merge(finalDataLongVarFinal,on='uuid')
            else:
                finalRes = finalRes.merge(finalDataLongVarFinal,on='uuid')
	
	
finalClickDatabase = clickData.merge(finalRes,on='uuid')

finalDataLongVarFinal.to_csv('C:/Users/jelisaveta.m/Desktop/' + str(projectNumber) + 'proba_jellu_final.csv')
