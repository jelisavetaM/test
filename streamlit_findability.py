# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 14:51:18 2022

@author: jelisaveta.m
"""

import pandas as pd
import os
import pyreadstat
import re
import numpy as np
from functools import reduce
import urllib.request, json
import streamlit as st
import shutil
import xlsxwriter
import base64



dataset = st.container()
	
with dataset:
    originalSurvey = st.file_uploader('Upload survey database:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    rtm_upload = st.file_uploader('Upload RTM database:', type=['csv'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    
    if originalSurvey is None or rtm_upload is None:
        st.error("Please upload the files!")
    else:
        with open('temp.sav', "wb") as buffer:
            shutil.copyfileobj(originalSurvey, buffer)
        projectNumber = 2022103
        
        version = "dapresy"
        
        # Rename record and date variables; add Weight variable
        originalSurvey, meta = pyreadstat.read_sav('temp.sav', user_missing=False)
        # for the date variable not no stay transformed to integer
        # it is necessary  to rescale the integer from SPSS with the number 12219379200 i.e. the number of seconds existing between "1582-10-14" and "1970-01-01" (the origin used by to_datetime)
        originalSurvey['date'] = pd.to_datetime(originalSurvey['date']-12219379200, unit="s")
        
        
        originalSurvey = originalSurvey.rename(columns = {"record" : "RespondentID", "date" : "ResponseDate"})
        originalSurvey['Weight'] = 1
        originalSurvey['Total'] = 1
        first_column = originalSurvey.pop('Weight')
        originalSurvey.insert(0, 'Weight', first_column)
        second_column = originalSurvey.pop('Total')
        originalSurvey.insert(0, 'Total', second_column)
        
        cols =  originalSurvey.columns.tolist() 
        
        #recode metadata
        meta.column_labels.insert(0, "Total: Total")
        meta.column_labels.insert(1, "Weight: Weight")
        
        originalSurvey = originalSurvey[cols]
        
        
        
        
        chosen_columns = []
        for i in meta.variable_value_labels:
          if len(meta.variable_value_labels[i]) == 2 and any("NO TO:" in string for string in meta.variable_value_labels[i].values()):
              chosen_columns.append(i)
        
        #chage delimiters in variable names from Deciphers default 'r' to '#' 
        def change_delimiter (var_list, delimiter):
            if var_list in chosen_columns or version == "data":
                pattern_row = re.search(r"r(\d+)", var_list)
                pattern_col = re.search(r"c(\d+)", var_list)
            
                if pattern_row:
                    changed = re.sub(pattern_row.group(), delimiter + re.findall(r'\d+', pattern_row.group())[0], var_list)
                elif pattern_col:
                    changed = re.sub(pattern_col.group(),  "c" +    delimiter + re.findall(r'\d+', pattern_col.group())[0], var_list) 
                else:
                    changed = var_list
            else:
                changed = var_list
            
            return changed
        
        new_cols = [change_delimiter(i, '#') for i in cols]
        # update columns (variable) names
        originalSurvey.columns = new_cols
        
        def change_metadata (key, delimiter):
            if key in chosen_columns or version == "data":
                pattern_row = re.search(r"r(\d+)", key)
                pattern_col = re.search(r"c(\d+)", key)
            
                if pattern_row:
                    key_new = re.sub(pattern_row.group(), delimiter + re.findall(r'\d+', pattern_row.group())[0], key)
                elif pattern_col:
                    key_new = re.sub(pattern_col.group(),  "c" + delimiter + re.findall(r'\d+', pattern_col.group())[0], key) 
                else:
                    key_new = key
            else:
             key_new = key   
            return key_new
        
        
        new_dict = {change_metadata(k, '#'): v for k, v in meta.variable_value_labels.items()}
        
        
        #recode multiple response variables
        multipleQ_cols = [col for col in originalSurvey.columns if '#' in col and 'oe' not in col]
        
        
        if version == "data":
            for var in multipleQ_cols:
                if "dec_vars" not in var:
                    if len(new_dict[var].keys()) == 2 and any("NO TO:" in string for string in new_dict[var].values()):
                        # new_dict[var][0] = new_dict[var][0].split(': ')[1]
                        new_dict[var][0] = "Not selected"
                        new_dict[var][1] = new_dict[var][list(new_dict[var].keys())[1]]
                        new_dict[var][1] = "Selected"
                        if list(new_dict[var].keys())[1] > 1:
                            del new_dict[var][list(new_dict[var].keys())[1]]
                        originalSurvey[var] = np.where(originalSurvey[var] > 1, 1, originalSurvey[var])               
        elif version == "dapresy":
            for var in multipleQ_cols:
                if "dec_vars" not in var:
                    if len(new_dict[var].keys()) == 2 and any("NO TO:" in string for string in new_dict[var].values()):
                        # new_dict[var][0] = new_dict[var][0].split(': ')[1]
                        # new_dict[var][0] = "Not selected"
                        new_dict[var][1] = new_dict[var][list(new_dict[var].keys())[1]]
                        # new_dict[var][1] = "Selected"
                        if list(new_dict[var].keys())[1] > 1:
                            del new_dict[var][list(new_dict[var].keys())[1]]
                        originalSurvey[var] = np.where(originalSurvey[var] > 1, 1, originalSurvey[var])
                
        
        
        
        if version == "data":
            new_labels = []
            for label in meta.column_labels:
                new_label = label.split(": ")[1]
                if "-" in new_label:
                    new_label = new_label.split("- ")[0]
                new_labels.append(new_label)   
                    
        elif version == "dapresy":
            new_labels = []
            for label in meta.column_labels:
                new_label = label.split(": ")[1]
                if "-" in new_label:
                    new_label = new_label.split("- ")[1]
                new_labels.append(new_label)
        
        #change CELL variable settings 
        meta.variable_measure['CELL'] = 'nominal'
        meta.variable_measure['Weight'] = 'scale'
        
        cell_val_labels = {} 
        for i in originalSurvey.CELL.unique():
            cell_val_labels[int(i)] = "CELL " + str(i).split('.')[0]
            
        new_dict['CELL'] = cell_val_labels
        new_dict['Total'] = {1.0: 'Total'}
        
        ############################################### RTM PART ###############################################
        RTM_Qtext = "Does the attribute match the display you can see below?"
        
        df_RTM_original = pd.read_csv(rtm_upload)
        df_RTM = df_RTM_original.loc[:, df_RTM_original.columns.str.startswith('EXP') | df_RTM_original.columns.str.startswith('HIYES') | df_RTM_original.columns.str.startswith('userid')]
        
        #delete dupicates in the RTM (bug)
        df_RTM = df_RTM.drop_duplicates(subset=['userid'], keep='first')
        
        all_attributes = set([col.split('#')[3] for col in df_RTM.columns if "userid" not in col])
        
        # RTMsols = list(df_RTM.columns)
        # RTMsols.remove('userid')
        
        # df_RTM[RTMsols] = df_RTM[RTMsols].replace({-1:np.nan, 0:np.nan})
        
        # merge columns with same attributes
        # create value labels dictionary, example {0.0: 'NO TO: Bushmills', 8.0: 'Bushmills'}
        df_RTM_merged = pd.DataFrame()
        RTM_val_labels = {}
        RTM_labels = []
        RTM_measure = {}
        
        kpis = ['EXP','HIYES']
        for kpi in kpis:
            for idx, attribute in enumerate(all_attributes):
                col_temp = [col for col in df_RTM.columns if ("userid" not in col) and (str(col.split('#')[3]) == str(attribute)) and kpi in col]
                if not df_RTM_merged.isin(['userid']).any().any():
                    df_RTM_merged['userid'] = df_RTM['userid']
                col_name = kpi + "attribute#" + str(idx + 1)
                df_RTM_merged[col_name] = df_RTM.groupby({x:'sum' for x in col_temp}, axis=1).sum()
                RTM_val_labels[col_name] = {1.0: attribute.replace("_", " ")}
                RTM_labels.append(RTM_Qtext)
                RTM_measure[col_name] = 'nominal'
        
        RTMsols = list(df_RTM_merged.columns)
        RTMsols.remove('userid')
        
        df_RTM_merged[RTMsols] = df_RTM_merged[RTMsols].replace({-1.0:np.nan, 0.0:np.nan})
        
        # MERGING RTN & SURVEY
        survey_and_RTM = pd.merge(originalSurvey, df_RTM_merged, how = 'left', left_on='uuid', right_on = 'userid')
        survey_and_RTM.drop(['userid'], axis = 1, inplace=True)
        new_dict.update(RTM_val_labels)
        new_labels = new_labels + RTM_labels
        meta.variable_measure.update(RTM_measure)
        
        
        
        #CLICKS
        
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
        finalClickLabelsAll = {}
        
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
             
            finalClickLabelsAll[re.search(r'\d+', clickVar).group()[0]] = finalClickLabels
            
            binaryClick = finalDataLongVar.apply(lambda row : clickFunction(row['CELL'], clickVariablesSL[clickVar], row['xDevided_'], row['yDevided_'], row['commDevided_'], row['timeDevided_']), axis = 1)
            finalDataLongVarFin = finalDataLongVar.assign(Result = binaryClick)
            
            finalDataLongVarFin[['Clicks','Comments','Times']] = pd.DataFrame(finalDataLongVarFin["Result"].to_list())
            # resultDevided = pd.DataFrame(finalDataLongVarFin["Result"].to_list()).add_prefix('Type_')
            # resultDevided['uuid'] = finalDataLongVarFin['uuid']
            
            finalDataLongVarFin[list('ClickZone_' + str(re.search(r'\d+', clickVar).group()[0]) + '#' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Clicks'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Clicks'].to_list())
            # resultDevided_click = pd.DataFrame(resultDevided["Type_0"].to_list())
            # resultDevided_click.columns = ['ClickZone_' + str(x+1) for x in list(resultDevided_click.columns)]
            finalDataLongVarFin[list('ClickComment_' + str(re.search(r'\d+', clickVar).group()[0]) + '#' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Comments'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Comments'].to_list())
            
            # resultDevided_zones = pd.DataFrame(resultDevided["Type_1"].to_list())
            # resultDevided_zones.columns = ['ClickComment_' + str(x+1) for x in list(resultDevided_zones.columns)]
            finalDataLongVarFin[list('ClickTime_' + str(re.search(r'\d+', clickVar).group()[0]) + '#' + str(x+1) for x in list(pd.DataFrame(finalDataLongVarFin['Times'].to_list()).columns))] = pd.DataFrame(finalDataLongVarFin['Times'].to_list())
            
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
                # finalDataLongVarFinal = finalDataLongVarFinal.rename(columns={col: col+'#' + re.search(r'\d+', clickVar).group()[0] for col in finalDataLongVarFinal.columns if col not in ['uuid']})
                finalRes = finalDataLongVarFinal
            else:
                # finalDataLongVarFinal = finalDataLongVarFinal.rename(columns={col: col+'#' + re.search(r'\d+', clickVar).group()[0] for col in finalDataLongVarFinal.columns if col not in ['uuid']})
                finalRes = finalRes.merge(finalDataLongVarFinal, on='uuid')
                
        # MERGING CLICKS & SURVEY
        finalAllMerged = survey_and_RTM.merge(finalRes, on='uuid')
        
        # ADJUST METADATA
        
        
        click_val_labels = {}
        for var in list(finalRes.columns):
            if "Zone" in var:
                click_val_labels[var] = {1.0 : finalClickLabelsAll[re.findall('[0-9]+', var)[0]][int(re.findall('[0-9]+', var)[1]) - 1]}
        
        new_dict.update(click_val_labels)
        
        click_labels = []
        click_measure = {}
        for var in list(finalRes.columns):
            if "uuid" not in var:
                if "Zone" in var:
                    click_labels.append("Click task - zones")
                    click_measure[var] = "nominal"
                elif "Comment" in var:
                    click_labels.append("Click task - comments")
                    click_measure[var] = "nominal"
                elif "Time" in var:
                    click_labels.append("Click task - times")
                    click_measure[var] = "scale"
                
        new_labels = new_labels + click_labels
        meta.variable_measure.update(click_measure)
        
        def get_table_download_link(df):
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
            href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
        

        st.markdown(get_table_download_link(finalAllMerged), unsafe_allow_html=True)
        #pyreadstat.write_sav(finalAllMerged, os.getcwd() + '\\Outputs\\ETL\\Survey\\test_dapresy_final.sav',  variable_value_labels = new_dict, column_labels = new_labels, variable_measure = meta.variable_measure)
