# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 00:49:50 2022

@author: jelisaveta.m
"""
import streamlit as st

import pandas as pd
import os
import pyreadstat
import re
import numpy as np
from functools import reduce
import urllib.request, json

dataset = st.container()

with dataset:
    originalSurvey = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    
    if originalSurvey is None:
        st.error("Please upload the files!")
    else:
        bytes_data = originalSurvey.getvalue()
        originalSurvey, meta = pyreadstat.read_sav(bytes_data, user_missing=False)
        st.write(originalSurvey)
