# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 00:49:50 2022

@author: jelisaveta.m
"""
import streamlit as st

dataset = st.container()

with dataset:
    originalSurvey = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=['sav'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)
