import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


st.title('Eli Research & Development Lumos Analysis App')

st.write('This app is currently under development stage.')

with st.form('data input'):   
    st.header('Data Upload & Input Processing')
    uploaded_file=st.file_uploader("Upload your data here to analyze: ",type='csv')
    delim=st.radio('What is your variable separation delimiter?',['hyphen (-)','underscore (_)'],index=None)
    variables=st.text_input("Enter the variables, separated by delimiter specified above","variable 1-variable 2-variable-3")
    st.form_submit_button('Initiate Analysis')


# Input Processing
df=pd.read_csv(uploaded_file)
if delim == 'hyphen (-)':
    delim='-'
else:
    delim='_'
variables=variables.split(delim)
# Data Processing
df_tidy = (
    df[['strip name', 'line_peak_above_background_1', 'line_peak_above_background_2', 'line_area_1', 'line_area_2']]
    .rename(
        columns={
            'line_peak_above_background_1': 'TLH',
            'line_peak_above_background_2': 'CLH',
            'line_area_1': 'TLA',
            'line_area_2': 'CLA'
        }
    )
    .assign(
        TLH_normalized=lambda x: x.TLH / (x.TLH + x.CLH),
        CLH_normalized=lambda x: x.CLH / (x.TLH + x.CLH),
        TLA_normalized=lambda x: x.TLA / (x.TLA + x.CLA),
        CLA_normalized=lambda x: x.CLA / (x.TLA + x.CLA)
    )
    .assign(
        **df['strip name'].str.split(delim, expand=True)
        .rename(
            columns=dict(zip(range(len(variables)), variables)) #Dynamically rename based on input.
        )
    )
    .drop(columns=['strip name'])
)
df["T-C_normalized"] = df["TLH_normalized"] - df["CLH_normalized"]
df["T/C_normalized"] = df["TLH_normalized"] / df["CLH_normalized"]
df["C/T_normalized"] = df["CLH_normalized"] / df["TLH_normalized"]

# Descriptie Statistics
stat=(
    df_tidy[variables+['TLH_normalized','CLH_normalized','T-C_normalized','T/C_normalized','C/T_normalized']]
    .groupby(variables)
    .describe()
)

# Tabs generation
tab1,tab2,tab3,tab4=st.tabs(
    ['Raw Data','Normalized Raw Data','Descriptive Statistics','2D Graphs'
    ]
)

tab1.header('Raw Data')
tab1.write(df)

tab2.header('Normalized Raw Data')
tab2.write(df_tidy)

tab3.header('Descriptive Statistics')
tab3.write(stat)

tab4.header("2D Graphs")

x=tab4.selectbox(
    'Choose your x-axis: ',
    options=variables
    )
x_cont_or_cat=tab4.selectbox(
    'Is your x-axis variable continuous or categorical?: ',
    options=['continuous','categorical']
    )

color=tab4.pills(
    'If you want a coloured grouping, choose the variable group for colour: ',
    options=variables,
    key='color'
    )
facet=tab4.pills(
    'If you want to facet the graphs per variable, select one from the following:',
    options=variables,
    key='facet'
)
log_x=tab4.radio(
    "Do you prefer the x-axis to be scaled logarithmically?: ",
    options=['yes','no'],
    key='log_x'
)
for y in ['TLH_normalized','CLH_normalized','T-C_normalized','T/C_normalized','C/T_normalized','TLA_normalized','CLA_normalized','TLH','CLH','TLA','CLA']:
    if x_cont_or_cat=='continuous':
        df_tidy[x].astype(float)
        fig=px.scatter(
            df_tidy,
            x=x,
            y=y,
            color=color,
            title=f"The effect of {x} on {y}",
            trendline='lowess',
            facet_col=facet if facet else None,
            log_x=True if log_x=='yes' else None
        )
        tab4.plotly_chart(fig)
    else: 
        df_tidy[x].astype(object)
        fig=px.box(
            df_tidy,
            x=x,
            y=y,
            color=color,
            title=f"The effect of {x} on {y}",
            facet_col=facet if facet else None,
            log_x=True if log_x=='yes' else None
        )
        tab4.plotly_chart(fig)
