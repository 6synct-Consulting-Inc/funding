import pandas as pd
import numpy as np
import DateTime as dt

#import dash
#import dash_core_components as dcc
#import dash_design_kit as ddk
#import dash_html_components as html
#import plotly.express as px
#import plotly.graph_objects as go

"""
THIS FILE IMPORTS THE RAW DATA, CLEANS IT, AND GENERATES A NICE 
DATAFRAME THAT IS IMPORTED TO THE APP.PY FILE FOR MANIPULATION
"""

# for testing print outputs, reformat default output settings for pandas
# (unnecessary for production code)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('max_colwidth', None)

# read in annual data files to dataframes
Funding_2018_19 = pd.read_csv("assets/2018-19 Grants and Contributions.csv", low_memory=False)
Funding_2019_20 = pd.read_csv("assets/2019-20 Grants and Contributions.csv", low_memory=False)

"""
SHOULD WE BE REMOVING DUPLICATES LIKE THIS? 
# remove duplicates of grants
df.drop_duplicates(subset='agreemen_1', keep='first', inplace=True)
"""
# FUNCTION: clean up headings, descriptions & remove duplicates
def clean_data(df):
    return df[['recipient_', 
               'recipient1', 
               'recipien_1', 
               'recipien_2', 
               'recipien_4', 
               'agreement_', 
               'agreement1', 
               'agreemen_2', 
               'descriptio', 
               'agreemen_3', 
               'naics_sect', 
               'program_na',
               'projected_',
               'federal__1',
               'latitude',
               'longitude'
              ]].rename(columns={"recipient_": "Prov_Abbreviation", 
                                 "recipient1": "Province",
                                 "recipien_1": "City",
                                 "recipien_2": "Company_Name",
                                 "recipien_4": "Company_ID", 
                                 "agreement_": "Type_of_Contribution",
                                 "agreement1": "Project",
                                 "agreemen_2": "$_Amount",
                                 "descriptio": "Detailed_Description",
                                 "agreemen_3": "Start_Date", 
                                 "program_na": "Funding_Program_Name",
                                 "projected_": "Spend_Date",
                                 "federal__1": "Electoral_District",
                                 "latitude":   "Latitude",
                                 "longitude":  "Longitude"
                                }
                       ).drop_duplicates(keep='first')

# combine dataframes
# Find unique instanstances from data:(Left_only = 2019_20,Right_only = 2018_19)
Dataset_comparison_companies = clean_data(Funding_2019_20)[['Company_ID']].merge(
    clean_data(Funding_2018_19)[['Company_ID']], indicator=True, how='outer')

Dataset_comparison_companies.groupby(['_merge'])
Dataset_comparison_companies["_merge"] = Dataset_comparison_companies["_merge"].replace("right_only", "2018_19 Only")
Dataset_comparison_companies["_merge"] = Dataset_comparison_companies["_merge"].replace("left_only", "2019_20 Only")
Dataset_comparison_companies["_merge"] = Dataset_comparison_companies["_merge"].replace("both", "Multi-Year Projects")
Dataset_comparison_companies.drop_duplicates(keep='first').set_index('Company_ID').reset_index()

# drop companies with missing datapoints
Dataset_comparison_companies.dropna(inplace=True) #subset=['Company_ID']

# drop any row with a NaN value
Dataset_comparison_companies.replace('',0.0)
Dataset_comparison_companies.replace(np.nan,0.0)

# create a nice and clean database for use with Plotly
df = clean_data(Funding_2019_20).merge(clean_data(Funding_2018_19), how='outer').merge(Dataset_comparison_companies, how='outer', on='Company_ID').drop_duplicates(keep='first')

# replace nan $ amounts with 0
#df['$_Amount'] = df['$_Amount'].fillna(0.0)

# shorten/condense Funding_Program_Name text:
df.loc[(df.Funding_Program_Name == 'Industrial Research Assistance Program – Contributions to Organizations'),'Funding_Program_Name']='IRAP - Contributions to Organizations'
df.loc[(df.Funding_Program_Name == 'Industrial Research Assistance Program – Contributions to Firms'),'Funding_Program_Name']='IRAP - Contributions to Firms'
df.loc[(df.Funding_Program_Name == 'Industrial Research Assistance Program – Green Youth Employment Program'),'Funding_Program_Name']='IRAP - Green Youth Employment'
df.loc[(df.Funding_Program_Name == 'Industrial Research Assistance Program – Youth Employment Program'),'Funding_Program_Name']='IRAP - Youth Employment'

# clean naics_sect text:
df.loc[(df.naics_sect == 'Administrative and support, waste management and remediation services'),'naics_sect']='Admin. support, waste manag. & remed.'
df.loc[(df.naics_sect == 'Information and cultural industries'),'naics_sect']='Info & cultural industries'
df.loc[(df.naics_sect == 'Professional, scientific and technical services'),'naics_sect']='Prof., scientific & technical services'
df.loc[(df.naics_sect == 'Mining, quarrying, and oil and gas extraction'),'naics_sect']='Mining, quarrying, oil, gas extract.'

"""
#ataset_comparison_companies.drop_duplicates(keep='first').set_index('Company_ID').reset_index()
#df = df.drop_duplicates(keep='first',)
"""

# removes duplicated start date grants (some grants are duplicated, with only altered 'Spend_Date' values)
# df = df.loc[~df.Start_Date.duplicated(keep='first')]
df = df.drop_duplicates(subset=['Start_Date', 'Project'], keep="last")

# Add column for Year and Quarter
df.insert(loc=0, column='Year_Quarter', value=df['Start_Date'])
df['Year_Quarter'] = pd.to_datetime(df['Year_Quarter'])
df['Year_Quarter'] = df['Year_Quarter'].dt.to_period("Q")
df['Year_Quarter'] = df['Year_Quarter'].astype(str)

# Clean upper / lower case
df['Project'] = df['Project'].str.lower()
df['Detailed_Description'] = df['Detailed_Description'].str.lower()
#df = df.applymap(lambda s:s.lower() if type(s) == str else s)



# drop those pesky duplicates one more time
#df = df.drop_duplicates(subset=['Start_Date','$_Amount'],keep='first',inplace=True)
df = df.dropna()

"""
ODDS AND ENDS

df.sort_values(by=['naics_sect'])
print(df.head(50))

corp_df = df[['Prov_Abbreviation','Project','Company_Name', 'naics_sect', '$_Amount', 'Funding_Program_Name','Latitude', 'Longitude']]


# example of how to remove useless columns
df = df.drop(df.columns[[0,2,7,12,13,14,31]], axis=1)
"""
















############################ NOT USED ############################################

"""
previous iteration of dataframe creation 
(specific columns of data extracted to a different dataframe)
no YoY analysis here, so much of this code is not compatible with above 

# create dataframe with relevant info [ corp name, corp id, grant $, longitude, latitude, NAICS sect, Program 'supplier' ]
corp_dff = df[['recipien_2','recipien_4','agreemen_2','longitude','latitude','naics_sect','program_na']]

# add all grants for each company
corp_df = corp_dff.groupby(['recipien_2','latitude','longitude','naics_sect','program_na'])[['agreemen_2']].sum().reset_index()
"""
#different version of same solution
#corp_df_2 = corp_df.groupby(by=['recipien_2', 'longitude','latitude']).apply(sum, axis=1)
#corp_df_2 = corp_df_2.reset_index()
"""

# conditional cell replacement example
#df.loc[df['Population(B)'] < 1] = 0

# finally, let's rename the columns because they are ugly
corp_df = corp_df.rename({'recipien_2':'Company_Name', 'recipien_4':'Corp ID', 
    'agreemen_2':'Grant_Total', 'longitude':'Longitude', 'latitude':'Latitude',
    'naics_sect':'NAICS_Sector','program_na':'Program'}, axis=1)
"""

########################### NOT USED #############################################

"""
CODE FROM A PREVIOUS JUPYTER NOTEBOOK FOR MORE GENERAL ANALYSIS
(ON A PROVINCIAL SCALE)

    if corp not in corp_df:
        corp_df.update({corp:df[['recipien_2','']})
    else:
# lists of province abbreviations
all_provinces = ["ON","QC","BC","AB","NS","MB","NB","SK","NL","PE","NT","YT","NU"]
big_4 = ["ON","QC","BC","AB"]

# create each province's dataframe
prov_df = { }
for province in all_provinces:
    prov_df[province] = df[df["recipient_"] == province]

# grants per province
grants_per_prov = df['recipient_'].value_counts()

# (normalized)
grants_per_prov_norm = df['recipient_'].value_counts(normalize=True)

# average grant per province
prov_mean = [ ]
for province in all_provinces:
    prov_mean.append(round(prov_df[province]["agreemen_2"].mean()))

# total grant per province
prov_tot = [ ]
for province in all_provinces:
    prov_tot.append(round(prov_df[province]["agreemen_2"].sum()))

##### ONTARIO #####
# total grant dollars
on_grant_dollars = prov_df["ON"]["agreemen_2"].sum(axis=0)

##### QUEBEC #####
# total grant dollars
qc_grant_dollars = prov_df["QC"]["agreemen_2"].sum(axis=0)

##### BRITISH COLUMBIA #####
# total grant dollars
bc_grant_dollars = prov_df["BC"]["agreemen_2"].sum(axis=0)

##### ALBERTA #####
# total grant dollars
ab_grant_dollars = prov_df["AB"]["agreemen_2"].sum(axis=0)

if __name__ == '__main__':
    app.run_server(debug=True)
"""
