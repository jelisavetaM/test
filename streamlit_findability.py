import streamlit as st
import pandas as pd
import numpy as np
import time

dataset = st.container()

def get_findability_data(allFilenames, valid_id_import, tested_product):
    find_raw = pd.concat([pd.read_csv(f, sep=',', keep_default_na=False) for f in allFilenames])
    find_raw = find_raw[find_raw['USER ID'] != '']

    valid_id = pd.read_excel(valid_id_import)


    find_merge = pd.merge(find_raw, valid_id, how='right', left_on='USER ID', right_on='sguid')

    #sredjivanje qty kolone u no purchase, purchase#
    dozvoljene_vrednosti_1 = ['1']
    find_merge.loc[~find_merge['QUANTITY'].isin(dozvoljene_vrednosti_1), 'QUANTITY'] = 'No purchase'
    find_merge['QUANTITY'] = np.where(find_merge['QUANTITY'] == '1', 'Purchase', find_merge['QUANTITY'])

    #sredjivanje client kolone u no purchase, purchase#
    find_merge['CLIENT'] = np.where( 
        ( (find_merge['SKU'] == tested_product) & (find_merge['QUANTITY'] == 'Purchase' ) ),'Test product1', 'none')

    #sredjivanje splitova#
    find_merge['cell_split'] = 'cell_' + find_merge['cell'].astype(str) 

    #######CISCENJE######
    #ciscenje empty#
    nedozvoljene_vrednosti = ['Empty', 'No Buy']
    find_merge.loc[find_merge['TIME BEFORE FIRST BUY'].isin(nedozvoljene_vrednosti), 'TIME BEFORE FIRST BUY'] = ''

    #za uzimanje dela DF-a#
    find_TIME_cleaning_temp = find_merge[['USER ID', 'Vrid', 'SKU', 'CLIENT', 'QUANTITY', 'TIME BEFORE FIRST BUY', 'cell_split', 'users']]

    find_TIME_purchase = find_TIME_cleaning_temp.query("QUANTITY == 'Purchase'")


    find_TIME_purchase_client = find_TIME_cleaning_temp.query("QUANTITY == 'Purchase'& CLIENT == 'Test product1'")

    find_TIME_purchase_client = find_TIME_purchase_client.astype({'TIME BEFORE FIRST BUY': 'int32'})

    cells = find_TIME_purchase_client['cell_split'].unique().tolist()


    #ciscenje cellova od outliera, gore/dole i mean + 2.5 stdev, TOTAL VREME#

    find_cells =[]

    for cells, find_TIME_temp in find_TIME_purchase_client.groupby('cell_split'):
        sorted_data = find_TIME_temp.sort_values('TIME BEFORE FIRST BUY')
        n = len(find_TIME_temp)
        outliers = round(n*4/100)
        find_TIME_temp = sorted_data[outliers: n-outliers]
        
        mean = np.mean(find_TIME_temp['TIME BEFORE FIRST BUY'])
        stdev = np.std(find_TIME_temp['TIME BEFORE FIRST BUY'])
        st.write("Mean: {:.2f}".format(mean))
        st.write("Standard Deviation: {:.2f}".format(stdev))

        lower_range = mean-(2.5*stdev)
        upper_range = mean+(2.5*stdev)
        st.write("Good data should lie between {:.2f} and {:.2f}".format(lower_range, upper_range))

        outliers = [i for i in find_TIME_temp['TIME BEFORE FIRST BUY'] if i<lower_range or i>upper_range]
        st.write("Number of outliers:",len(outliers))
        st.write("Outliers:", outliers)

        find_TIME_temp.drop(find_TIME_temp[(find_TIME_temp['TIME BEFORE FIRST BUY']<lower_range) | (find_TIME_temp['TIME BEFORE FIRST BUY']>upper_range)].index, inplace=True)  
        
        find_TIME_temp = find_TIME_temp.rename(columns={'TIME BEFORE FIRST BUY': 'time_total_cell'})
        find_TIME_temp = find_TIME_temp.astype({'time_total_cell': 'int32'})
        
        find_cells.append(find_TIME_temp)
        
    find_cells_clean = pd.concat(find_cells)

    list_find_cells_25 =[]

    for cells, find_cells_25_temp in find_cells_clean.groupby('cell_split'):
        list_values = find_cells_25_temp['time_total_cell'].to_list()
        n_ispitanika = len(list_values)
        najbrzih_25_temp = n_ispitanika/100*25
        najbrzih_25 = int(najbrzih_25_temp)

        find_cells_25_temp = find_cells_25_temp.nsmallest(najbrzih_25, ['time_total_cell'])

        find_cells_25_temp = find_cells_25_temp.rename(columns={'time_total_cell': 'time_total_cell_25'})
        find_cells_25_temp = find_cells_25_temp.astype({'time_total_cell_25': 'int32'})
        
        list_find_cells_25.append(find_cells_25_temp)
        
    find_cells_25 = pd.concat(list_find_cells_25)

    list_find_cells_50 =[]

    for cells, find_cells_50_temp in find_cells_clean.groupby('cell_split'):


        list_values = find_cells_50_temp['time_total_cell'].to_list()
        n_ispitanika = len(list_values)
        najbrzih_50_temp = n_ispitanika/100*50
        najbrzih_50 = int(najbrzih_50_temp)

        find_cells_50_temp = find_cells_50_temp.nsmallest(najbrzih_50, ['time_total_cell'])

        find_cells_50_temp = find_cells_50_temp.rename(columns={'time_total_cell': 'time_total_cell_50'})
        find_cells_50_temp = find_cells_50_temp.astype({'time_total_cell_50': 'int32'})
        
        list_find_cells_50.append(find_cells_50_temp)
        
    find_cells_50 = pd.concat(list_find_cells_50)

    cells = find_TIME_purchase_client['cell_split'].unique().tolist()
    users = find_TIME_purchase_client['users'].unique().tolist()

    list_find_cells_users_25 =[]
    list_find_cells_users_50 =[]
    for cell in cells :
        for user in users :
            #users 25%#
            find_user_cell_25_temp = find_cells_clean[(find_cells_clean.cell_split == cell ) & (find_cells_clean.users == user)]
            
            list_values = find_user_cell_25_temp['time_total_cell'].to_list()
            n_ispitanika = len(list_values)
            najbrzih_25_temp = n_ispitanika/100*25
            najbrzih_25 = int(najbrzih_25_temp)

            find_user_cell_25_temp = find_user_cell_25_temp.nsmallest(najbrzih_25, ['time_total_cell'])

            find_user_cell_25_temp = find_user_cell_25_temp.rename(columns={'time_total_cell': 'time_total_users_25'})
            find_user_cell_25_temp = find_user_cell_25_temp.astype({'time_total_users_25': 'int32'})
            
            list_find_cells_users_25.append(find_user_cell_25_temp)
        

            #users 50%#
            find_user_cell_50_temp = find_cells_clean[(find_cells_clean.cell_split == cell ) & (find_cells_clean.users == user)]
            
            list_values = find_user_cell_50_temp['time_total_cell'].to_list()
            n_ispitanika = len(list_values)
            najbrzih_50_temp = n_ispitanika/100*50
            najbrzih_50 = int(najbrzih_50_temp)

            find_user_cell_50_temp = find_user_cell_50_temp.nsmallest(najbrzih_50, ['time_total_cell'])

            find_user_cell_50_temp = find_user_cell_50_temp.rename(columns={'time_total_cell': 'time_total_users_50'})
            find_user_cell_50_temp = find_user_cell_50_temp.astype({'time_total_users_50': 'int32'})
            
            list_find_cells_users_50.append(find_user_cell_50_temp)

    find_user_cell_25 = pd.concat(list_find_cells_users_25) 
    find_user_cell_50 = pd.concat(list_find_cells_users_50) 

    #SPAJANJE BAZA#

    final_find = find_TIME_purchase.merge(
                 find_cells_clean[['USER ID', 'time_total_cell']], on='USER ID', how='left').merge(
                 find_cells_25[['USER ID', 'time_total_cell_25']], on='USER ID', how='left').merge(
                 find_cells_50[['USER ID', 'time_total_cell_50']], on='USER ID', how='left').merge(
                 find_user_cell_25[['USER ID', 'time_total_users_25']], on='USER ID', how='left').merge(
                 find_user_cell_50[['USER ID', 'time_total_users_50']], on='USER ID', how='left')

    #spajanje sa svim ispitanicima

    respondents_unique_temp = find_merge[['USER ID', 'Vrid']]
    respondents_unique = respondents_unique_temp.drop_duplicates()

    final_find_all_temp = respondents_unique.merge(final_find, on='USER ID', how='left')
    final_find_all_temp = final_find_all_temp.rename(columns={'Vrid_x': 'Vrid'})
    final_find_all_temp = final_find_all_temp.drop('Vrid_y', 1)

    cols1 = ['SKU','CLIENT','QUANTITY']
    final_find_all = final_find_all_temp
    for col in cols1:
        final_find_all[col] = final_find_all_temp[col].replace(np.nan,'none')

    #excel export

    with pd.ExcelWriter("final.xlsx") as writer:
        final_find_all.to_excel(writer, sheet_name='sheet1', index=False)
    
    with open('final.xlsx', mode = "rb") as f:
        st.download_button('Findability Data', f, file_name='final.xlsx')


with dataset:
    allFilenames = st.file_uploader('Upload Databases from Virtual Shelf Platform:', type=None, accept_multiple_files=True, key=None, help=None, on_change=None, args=None, kwargs=None,disabled=False)

    valid_id_import = st.file_uploader('Upload Database with Final IDs:', type=None, accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False)

    tested_product  = st.text_input('Insert tested product for example tested LIQUID FENCE DEER & RABBIT REPELLENT')

    if len(allFilenames)==0 or valid_id_import is None:
        st.error("Please upload the files!")
    elif tested_product == '':
        st.error("Please insert tested product")
    else:
        get_findability_data(allFilenames, valid_id_import, tested_product)
