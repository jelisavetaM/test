# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 00:49:50 2022

@author: jelisaveta.m
"""
import streamlit as st

dataset = st.container()

with dataset:
    originalSurvey = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
    
    if originalSurvey is not None:
        st.error("Please upload the files!")
    else:
        originalSurvey, meta = pyreadstat.read_sav(originalSurvey, user_missing=False)
        st.write(originalSurvey)
