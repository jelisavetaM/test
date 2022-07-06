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

dataset = st.container()
	
with dataset:
    originalSurvey = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    
    if originalSurvey is None:
        st.error("Please upload the files!")
    else:
        with open('temp.sav', "wb") as buffer:
            shutil.copyfileobj(originalSurvey, buffer)
