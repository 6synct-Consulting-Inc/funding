import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
#import plotly.io as pio
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import dash_design_kit as ddk

from grantData import *
from mapbox_token import *

# REQUIRED FOR DEPLOYMENT
app = dash.Dash(__name__)
server = app.server  # expose server variable for Procfile

#province_list = ['ON','BC','QC','AB','MB','SK','NL','NB','NS','PE','NU','NT','YT']
# create series for dropdown menus, and remove NaN [ cannot use .drop() on a list ]
province_series = df['Prov_Abbreviation']
province_series.dropna(inplace=True)
donor_series = df['Funding_Program_Name']
donor_series.dropna(inplace=True)
naics_sect_series = df['naics_sect']
naics_sect_series.dropna(inplace=True)
fed_jurisdiction_series = df['Federal_Electoral_District']
fed_jurisdiction_series.dropna(inplace=True)
year_series = df['_merge']
year_series.dropna(inplace=True)

# lists of unique values for use in dropdown menus
province_list = province_series.unique().tolist()
donor_list = donor_series.unique().tolist()
year_list = year_series.unique().tolist()
naics_sect_list = naics_sect_series.unique().tolist()
fed_jurisdiction_list = fed_jurisdiction_series.unique().tolist()

app.layout = ddk.App([

    ddk.Header([
        ddk.Logo('6synctLogo.png'), ### WHY IS THE LOGO NOT LOADING???? it is saved to folder..
        ddk.Title('Available Corporate Funding in Canada'),
    ]),

    ddk.Card(width=100,children=[
        'Description of data and what this baby can do for ya'
    ]),

    ddk.ControlCard(width=20,id = 'map-controls',
        children=[
            ddk.ControlItem(
                dcc.Dropdown(
                    id = 'donor-dropdown',
                    options=[
                        {'label':i,'value':i}
                        for i in donor_list
                    ],
                    multi=True, #allow for multiple selections
                    value=['IRAP - Contributions to Firms'], #default value on app load
                    clearable = False,
                ),
                label='Donor Program'   
            ),
            ddk.ControlItem(
                dcc.Dropdown(
                    id = 'naics-dropdown',
                    options=[
                        {'label':i,'value':i}
                        for i in naics_sect_list
                    ],
                    multi=True, 
                    value=['Manufacturing'], 
                    clearable = False,
                ),
                label='NAICS Sector'   
            ),
            ddk.ControlItem(
                dcc.Dropdown(
                    id = 'year-dropdown',
                    options=[
                        {'label':i,'value':i}
                        for i in year_list
                    ],
                    multi=False,  
                    clearable = False,
                    value='both' 
                ),               
                label='Year'
            ),
            ddk.ControlItem(
                dcc.Dropdown(
                    id = 'province-dropdown',
                    options=[
                        {'label':i,'value':i}
                        for i in province_list
                    ],
                    multi=True, 
                    clearable = False, 
                    value=province_list 
                ),
                label='Province'   
            ),
        ]
    ),

    ddk.Card(width = 80, children=[
        ddk.CardHeader(title='Geographic Representation of Funding'),
        dcc.Graph(id='map-graph')
    ]),

    ddk.Card(width = 40, children=[
        ddk.CardHeader(title='Provincial Treemap'),
        dcc.Graph(id='treemap')
    ]),

    ddk.Card(width = 60, children=[
        ddk.CardHeader(title='Funding Timeline'),
        dcc.Graph(id='timeline-graph')
    ]),

    ddk.Card(width = 50, children=[
        ddk.CardHeader(title='Donor Distribution of Funding'),
        dcc.Graph(id='donor-graph')
    ]), 

]) # end of app.layout

@app.callback(
    [Output('map-graph','figure'),
    Output('timeline-graph','figure'),
    Output('treemap','figure')],
    #Output('donor-graph','figure')],
    [Input(component_id='donor-dropdown',component_property='value'),
    Input('naics-dropdown','value'),
    Input('year-dropdown','value'),
    Input('province-dropdown','value')]
) # NO BLANK LINES ALLOWED B.W. CALLBACK & 'update' METHOD
def update_app(input_donor,input_naics,input_year,input_province):
    """
    Note that it is now impossible to have a 'None' selection for any 
    of the dropdown menus, this simplifies callback possibilities.
    Parameter is set in control cards in app.layout
    """
    def print_mapbox(dataframe1):
        figure = px.scatter_mapbox(dataframe1, 
        title='Location & Corporation of IRAP Grant',
        hover_name='Company_Name', 
        hover_data={'Funding_Program_Name':True,'Latitude':False,'Longitude':False},  
        lat="Latitude", lon="Longitude",
        #template='plotly_dark',
        #color ='naics_sect', #color_continuous_scale=px.colors.sequential.Darkmint,
        #color ='NAICS_Sector', color_continuous_scale=px.colors.sequential.Darkmint,
        mapbox_style='dark',
        size_max=45, opacity=.8, zoom=4, size='$_Amount'
        )

        figure.update_layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            #center=dict(lat=50.44,lon=-91.009), #as data is altered, will refresh to same 'center'
            pitch=0,
            zoom=2.9
        ),
        )
        return figure
    
    def print_timeline(dataframe1):
        timetable = pd.pivot_table(dataframe1, 
            values='$_Amount', 
            index=['Company_ID', 'Funding_Program_Name'], 
            columns=['Start_Date'], 
            aggfunc=np.sum
        ).sum()

        figure = px.scatter(timetable.reset_index().rename(columns={0: "Total_Funding_$"}), 
            x='Start_Date', 
            y='Total_Funding_$', 
            range_x=['2016-07-01','2020-12-31']
        )
        return figure

    def print_treemap(dataframe1):
        figure = px.treemap(dataframe1.dropna(), 
            path=['Province', 'naics_sect', 'Funding_Program_Name'], 
            values='$_Amount',
            hover_data={'$_Amount':True} #cannot turn off values not in dataframe (ex. id, labels,
            # perhaps can turn off hover in general, and display $_Amount as text instead
            #width=400,
        )
        return figure

    """
    def print_donor_graph(dataframe1):
        table_fundingtype = pd.pivot_table(dataframe1, 
            values='$_Amount', 
            index=['Company_ID'],# 'Start_Date'],
            columns=['Funding_Program_Name'], aggfunc=np.sum),
    
        figure = go.Figure()

        for donor in dataframe1['Funding_Program_Name'].unique().tolist():
            figure.add_trace(go.Box(x=table_fundingtype[donor], name = donor))

        return figure
    """

    print("Swedish")
    dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df.naics_sect.isin(input_naics)) & (df._merge == input_year) & (df.Prov_Abbreviation.isin(input_province))]
    print("Finnish")

    return print_mapbox(dff), print_timeline(dff), print_treemap(dff)#, print_donor_graph(dff)





"""

    def print_donor_graph(dataframe1):
        dataframe2 = dataframe1

        figure = px.box(dataframe2,x='$_Amount',y='Funding_Program_Name')   

        #figure.update_traces()

        return figure

"""









#######################################################################################
#######################################################################################
#######################################################################################
#######################################################################################

"""
        figure.add_trace(go.Box(x=table_fundingtype['CanExport'], 
                                                name='CanExport')),
        figure.add_trace(go.Box(x=table_fundingtype['CanExport SMEs'], 
                                                name='CanExport SMEs')),
        figure.add_trace(go.Box(x=table_fundingtype['Canada Accelerator and Incubator Program'], 
                                                name='Can. Accelerator Program')),
        figure.add_trace(go.Box(x=table_fundingtype['Canadian International Innovation Program'], 
                                                name='Canadian International Innovation Program')),
        figure.add_trace(go.Box(x=table_fundingtype['Eureka/Eurostar'], 
                                                name='Eureka/Eurostar')),
        figure.add_trace(go.Box(x=table_fundingtype['IRAP - Contributions to Firms'], 
                                                name='IRAP – Contributions to Firms')),
        figure.add_trace(go.Box(x=table_fundingtype['IRAP - Contributions to Organizations'], 
                                                name='IRAP – Contributions to Organizations')),
        figure.add_trace(go.Box(x=table_fundingtype['IRAP - Green Youth Employment'], 
                                                name='IRAP – Green Youth Employment Program')),
        figure.add_trace(go.Box(x=table_fundingtype['IRAP - Youth Employment'], 
                                                name='IRAP – Youth Employment Program')),
        figure.add_trace(go.Box(x=table_fundingtype['Innovative Solutions Canada'], 
                                                name='Innovative Solutions Canada')), 
"""



if __name__ == '__main__':
    app.run_server(debug=True)



"""
    TO USE THIS, CHANGE MULTI ATTR. TO TRUE FOR DONOR-DROPDOWN

    if input_donor == None and input_year == None and input_province == None:
        print("1")
        dff = df
    elif input_donor == None and input_year == None:
        print("2a")
        dff = df[(df.Prov_Abbreviation == input_province)]
        print("2b")
    elif input_donor == None and input_province == None:
        print("3a")
        dff = df[(df._merge == input_year)] 
        print("3b")
    elif input_year == None and input_province == None: 
        print("4a")
        dff = df[(df.Funding_Program_Name.isin(input_donor))]
        print("4b")
    elif input_donor == None:
        print("5a")
        dff = df[(df.Prov_Abbreviation == input_province) & (df._merge == input_year)] 
        print("5b")
    elif input_year == None:
        print("6a")
        dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df.Prov_Abbreviation == input_province)]  
        print("6b")  
    elif input_province == None:
        print("7a")
        dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df._merge == input_year)]
        print("7b")
    elif input_donor != None and input_year != None and input_province != None:
        print("8a")
        dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df._merge == input_year) & (df.Prov_Abbreviation.isin(input_province))]
        print("8b")
    elif input_donor == None and input_year == None and input_province == None:
        print("1-2")
        dff = df

    return print_mapbox(dff)#, print_timeline(dff)
"""





#dff = df[(df._merge == input_year) & (df.Prov_Abbreviation == input_province)]
#dff = df[(df.Funding_Program_Name == input_donor) & (df._merge == input_year)] 
#dff = df[(df.Funding_Program_Name == input_donor) & (df.Prov_Abbreviation == input_province)]
#dff = df[(df.Funding_Program_Name == input_donor) & (df._merge == input_year) & (df.Prov_Abbreviation == input_province)] 






"""
TABBSSS

tab_style = {"fontWeight": "bold"}

tabs = dcc.Tabs(
        id="tabs",
        value="tab-1",
        children=[
            dcc.Tab(
                label="Text Tab",
                value="tab-1",
                style=tab_style,
                selected_style=tab_style,
            ),
            dcc.Tab(
                label="Table Tab",
                value="tab-2",
                style=tab_style,
                selected_style=tab_style,
            ),
        ],
    )


# APP LAYOUT #
app.layout = ddk.App(
    [
        ddk.Header( # for all tabs
            [
                ############# LOGO DOESN'T LOAD for some reason (comment or as is)  ##################
                ddk.Logo(src="6synctLogo.png"),#ddk.Logo(src=app.get_asset_url("6synctLogo.png")),
                ddk.Title("Government Funding in Canada"),
            ]
        ),
        ddk.Card(children=tabs),
        ddk.Card(id="update-tab"),
    ]
)

@app.callback(Output("update-tab", "children"), [Input("tabs", "value")])
def render_tabs(tab):
    if tab == "tab-1":
        return tab1_control
    elif tab == "tab-2":
        return tab2_content
"""
