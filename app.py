import dash
import dash_core_components as dcc
import plotly.express as px
from dash.dependencies import Input, Output
import dash_design_kit as ddk
import dash_html_components as html
import plotly.graph_objects as go
import dash_table

from grantData import *
from mapbox_token import *

# theme.js supplies some additional styling, but orange is hard-coded

# REQUIRED FOR DEPLOYMENT
app = dash.Dash(__name__)
server = app.server  # expose server variable for Procfile

#province_list = ['ON','BC','QC','AB','MB','SK','NL','NB','NS','PE','NU','NT','YT']
# create series for dropdown menus, and remove NaN [ cannot use .drop() on a list ]
province_series = df['Prov_Abbreviation']
province_series.dropna(inplace=True)
district_series = df['Electoral_District']
district_series.dropna(inplace=True)
donor_series = df['Funding_Program_Name']
donor_series.dropna(inplace=True)
naics_sect_series = df['naics_sect']
naics_sect_series.dropna(inplace=True)
fed_jurisdiction_series = df['Electoral_District']
fed_jurisdiction_series.dropna(inplace=True)
year_series = df['_merge']
year_series.dropna(inplace=True)

# lists of unique values for use in dropdown menus
province_list = province_series.unique().tolist()
district_list = district_series.unique().tolist()
donor_list = donor_series.unique().tolist()
year_list = year_series.unique().tolist()
naics_sect_list = naics_sect_series.unique().tolist()
fed_jurisdiction_list = fed_jurisdiction_series.unique().tolist()


def print_mapbox(dataframe):
    figure = px.scatter_mapbox(dataframe,
                               title='Location & Corporation of IRAP Grant',
                               hover_name='Company_Name',
                               hover_data=['Funding_Program_Name'],#: True, 'Latitude': False, 'Longitude': False}, # This statement doesnt work -DFL
                               lat="Latitude", lon="Longitude",
                               # template='plotly_dark',
                               # color ='naics_sect', #color_continuous_scale=px.colors.sequential.Darkmint,
                               # color ='NAICS_Sector', color_continuous_scale=px.colors.sequential.Darkmint,
                               mapbox_style='dark',
                               size_max=45,
                               opacity=.8,
                               zoom=4,
                               size='$_Amount',
                               color_discrete_sequence=['#FF8827']
                               )
    figure.update_layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            # center=dict(lat=50.44,lon=-91.009), #as data is altered, will refresh to same 'center'
            pitch=0,
            zoom=2.8
        ),
    )

    return figure

def print_timeline(dataframe):
    timetable = pd.pivot_table(dataframe,
                               values='$_Amount',
                               index=['Company_ID', 'Funding_Program_Name'],
                               columns=['Year_Quarter'],
                               aggfunc=np.sum
                               ).sum()

    figure = px.bar(timetable.reset_index().rename(columns={0: "Total_Funding_$"}),
                        x='Year_Quarter',
                        y='Total_Funding_$',
                        color_discrete_sequence=['#FF8827'], # automatic if theme.js is used (ddk feature)
                        #range_x=['2018-04-01', '2020-12-31']
                        )
    return figure

def print_treemap(dataframe):
    figure = px.treemap(dataframe.dropna(),
                        path=['Province', 'naics_sect', 'Funding_Program_Name'],
                        values='$_Amount',
                        color='$_Amount',
                        color_continuous_scale='Oranges',
                        #hover_data={'$_Amount': True}  # This statement doesnt work -DFL
                        # perhaps can turn off hover in general, and display $_Amount as text instead
                        # width=400,
                        )
    return figure

def print_donor_graph(dataframe):
    figure = go.Figure()
    figure.update_layout(showlegend=False,
                      height=500,
                      # title_text='Descriptives',
                      xaxis_title='Funding Amount ($CAD)',
                      )
    columns = list(dataframe)
    for i in columns:
        figure.add_trace(go.Box(x=dataframe[i], name=i, marker_color='#ffad33'))

    return figure

app.layout = ddk.App(show_editor=False,
    children=[
    ddk.Header([
        ddk.Logo("assets/6synctLogoBlack.png",
            style={
                "height": "30px",
                "margin-right":"0px",
                "width": "auto",
            },
        ),
        
        ddk.Title('NRC IRAP - Corporate Funding in Canada from 2018-2020'),
    ]), # end of ddk.Header

    ddk.Block( # left-hand column
        width=20,
        children=[
            ddk.Card(id='Description',
                     children=[
                        ddk.CardHeader(title='How can this data be used and what questions can it answer?'),
                        dcc.Markdown(
                        '''
                        1. How many companies have received federal funding (how many are new in 2019_20)?
                        2. What is the total annual federal budget for IRAP funding?
                        3. What is the National/Local budget for funding? What are the trends from year to year?
                        4. How is the funding distributed? (Is it based on populations? Industry type? other factors?)
                        5. How novel is my grant request compared to already funded projects?
                        6. Which federal program should I apply to?
                        7. How much funding should I apply for (compared to other similarly sized companies, research opportunities, jurisdictional budget limits)?
                        '''
                        ),
                    ]
            ),

            ddk.ControlCard(id='map-controls',
                children=[
                    ddk.CardHeader(title='Search for Funding'),
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
                            multi=True,
                            clearable=False,
                            value=['2019_20 Only']
                        ),
                        label='Year'
                    ),
                    ddk.ControlItem(
                        dcc.Dropdown(
                            id = 'donor-dropdown',
                            options=[
                                {'label': i, 'value': i}
                                for i in donor_list
                            ],
                            multi=True, # allow for multiple selections
                            value=donor_list, # default value on app load
                            clearable = False,
                        ),
                        label='Donor Program'
                    ),
                    ddk.ControlItem(
                        dcc.Input(
                        id = 'project-input',
                        maxLength=20,
                        multiple=False,
                        placeholder="enter keyword",
                        type="text",
                        disabled=True # DISABLED... for now!
                        ),
                        label='Project Search'
                    )

                ]
            ), # end of map-controls ControlCard

        ] # end of left-hand column - children
    ), # end of left-hand column

    ddk.Block( # right-hand column
        width=80,
        children=[
            ddk.Card( # map of canada
                padding=0,
                children=[
                    ddk.CardHeader(title='Geographic Representation of Funding'),
                    ddk.Graph(id='map-graph'),
                ]
            ),

            ddk.Card( # funding treemap
                children=[
                    ddk.CardHeader(title='Total Funding'),
                    ddk.Graph(id='treemap')
                    ]
            ),

            ddk.Card( # donor graph
                children=[
                    ddk.CardHeader(title='Funding by donor'),
                    ddk.Graph(id='donor-graph')
                ]
            ),

            ddk.Card( # bar graph
                children=[
                    ddk.CardHeader(title='Funding Commitments - by Start Date (YR/Q)'),
                    ddk.Graph(id='timeline-graph'),
                ]
            ),

            ddk.Card( # Companies Dataframe Table
                children=[
                    ddk.CardHeader(title='Search by Company or Project Keyword'),
                    ddk.DataTable(id='companies-table',
                        columns=[{"name": i, "id": i} for i in df[['Company_Name', 'Project', '$_Amount', 'Start_Date', 'Spend_Date']].columns],
                        fill_width=False,
                        filter_action='native',
                        #filter_query=''
                        sort_action='native',
                        page_size=7,
                        sort_mode='multi',
                        style_header={"fontWeight": "bold", "textTransform": "capitalize"},
                        style_cell_conditional=[
                            {'if': {'column_id': '$_Amount'},
                            'width': '10%'},
                            {'if': {'column_id': 'Start_Date'},
                            'width': '10%'},
                            {'if': {'column_id': 'Spend_Date'},
                            'width': '10%'},
                            {'if': {'column_id': 'Company_Name'},
                            'width': '20%'},
                            {'if': {'column_id': 'Project'},
                            'width': '50%'},
                        ],
                        style_cell={
                            'whiteSpace': 'normal',
                            #'height': 'auto',
                        },
                        style_data_conditional=[
                                {
                                    "if": {"row_index": "even"},
                                    "backgroundColor": "var(--report_background_page)",
                                }
                            ],
                    ),
                ]
            ),

            ddk.Card( # footer and references
                children=[
                    ddk.CardFooter("Source Information:"),
                    dcc.Link('Data Source: https://open.canada.ca/',
                             href='https://open.canada.ca/',
                    ),

                    html.Br(),
                    dcc.Link('Available under open government license: http://open.canada.ca/en/open-government-licence-canada',
                             href='http://open.canada.ca/en/open-government-licence-canada',
                    ),
                ]
            ),
        ] # end of right-hand column - children
    ), # end of right-hand column

    ] # end app.layout - children
) # end of app.layout

@app.callback(
    [Output('treemap', 'figure'),  Output('map-graph', 'figure'), Output('timeline-graph', 'figure')],
    [Input('donor-dropdown', 'value'), Input('naics-dropdown', 'value'), Input('year-dropdown', 'value'), Input('province-dropdown', 'value')]
)
def update_treemap_mapbox_timeline(input_donor, input_naics, input_year, input_province):
    dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df.naics_sect.isin(input_naics)) & (df._merge.isin(input_year)) & (df.Prov_Abbreviation.isin(input_province))]
    return print_treemap(dff), print_mapbox(dff), print_timeline(dff)

@app.callback(
    Output('donor-graph','figure'),#, Output('donor-table', 'children')],
    [Input('donor-dropdown', 'value'), Input('naics-dropdown', 'value'), Input('year-dropdown', 'value'), Input('province-dropdown', 'value')]
)
def update_donorgraph(input_donor, input_naics, input_year, input_province):
    dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df.naics_sect.isin(input_naics)) & (df._merge.isin(input_year)) & (df.Prov_Abbreviation.isin(input_province))]

    table_fundingtype = pd.pivot_table(dff, values='$_Amount',
                                       index=['Company_ID', 'Start_Date'],
                                       # ,'naics_sect', 'City', 'Province', 'Start Date', 'Projected Spend Date'
                                       columns=['Funding_Program_Name'], aggfunc=np.sum)
    return print_donor_graph(table_fundingtype)#, print_donor_table(table_fundingtype)

@app.callback(
    Output('companies-table', 'data'),
    [Input('donor-dropdown', 'value'), Input('naics-dropdown', 'value'), Input('year-dropdown', 'value'), Input('province-dropdown', 'value')]
)
def update_table(input_donor, input_naics, input_year, input_province):
    dff = df[(df.Funding_Program_Name.isin(input_donor)) & (df.naics_sect.isin(input_naics)) & (df._merge.isin(input_year)) & (df.Prov_Abbreviation.isin(input_province))]
    return dff.to_dict("rows")

################################# MANDATORY SERVER CODE ##################################
if __name__ == '__main__':
    app.run_server(debug=True)
