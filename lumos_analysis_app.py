import streamlit as st
import pandas as pd
import plotly.express as px

# App title and intro
st.title('Eli Research & Development Lumos Analysis App')
st.write('This app is currently under development stage.')

# --- Form for file upload and variable input ---
with st.form('data input'):
    st.header('Data Upload & Input Processing')
    uploaded_file = st.file_uploader("Upload your data here to analyze:", type='csv')
    delim = st.radio(
        'What is your variable separation delimiter?',
        ['hyphen (-)', 'underscore (_)'],
        index=None
    )
    variables = st.text_input(
        "Enter the variables, separated by delimiter specified above",
        "variable 1-variable 2-variable 3"
    )
    button = st.form_submit_button('Initiate Analysis')

# --- Form processing ---
if button:
    if uploaded_file is None:
        st.warning("Please upload a CSV file.")
        st.stop()
    if delim is None:
        st.warning("Please select a delimiter.")
        st.stop()

    try:
        # Parse delimiter and variable names
        delim = '-' if delim == 'hyphen (-)' else '_'
        variables = variables.split(delim)

        # Read and clean data
        df = pd.read_csv(uploaded_file)
        df_tidy = (
            df[['strip name', 'line_peak_above_background_1', 'line_peak_above_background_2', 'line_area_1', 'line_area_2']]
            .rename(columns={
                'line_peak_above_background_1': 'TLH',
                'line_peak_above_background_2': 'CLH',
                'line_area_1': 'TLA',
                'line_area_2': 'CLA'
            })
            .assign(
                TLH_normalized=lambda x: x.TLH / (x.TLH + x.CLH),
                CLH_normalized=lambda x: x.CLH / (x.TLH + x.CLH),
                TLA_normalized=lambda x: x.TLA / (x.TLA + x.CLA),
                CLA_normalized=lambda x: x.CLA / (x.TLA + x.CLA)
            )
        )

        # Split strip name into custom columns
        split_cols = df['strip name'].str.split(delim, expand=True)
        split_cols.columns = variables[:split_cols.shape[1]]
        df_tidy = pd.concat([df_tidy, split_cols], axis=1).drop(columns=['strip name'])

        # Add additional ratios
        df_tidy["T-C_normalized"] = df_tidy["TLH_normalized"] - df_tidy["CLH_normalized"]
        df_tidy["T/C_normalized"] = df_tidy["TLH_normalized"] / df_tidy["CLH_normalized"]
        df_tidy["C/T_normalized"] = df_tidy["CLH_normalized"] / df_tidy["TLH_normalized"]

        # Descriptive statistics
        stat = (
            df_tidy[variables + [
                'TLH_normalized', 'CLH_normalized',
                'T-C_normalized', 'T/C_normalized', 'C/T_normalized'
            ]]
            .groupby(variables)
            .describe()
        )

        # Store results in session state
        st.session_state.df = df
        st.session_state.df_tidy = df_tidy
        st.session_state.stat = stat
        st.session_state.variables = variables

    except Exception as e:
        st.error(f"Error during data processing: {e}")
        st.stop()

# --- If session state exists, render analysis and graphs ---
if 'df_tidy' in st.session_state:
    df = st.session_state.df
    df_tidy = st.session_state.df_tidy
    stat = st.session_state.stat
    variables = st.session_state.variables

    # Output tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        'Raw Data', 'Normalized Raw Data', 'Descriptive Statistics', '2D Graphs'
    ])

    # Tab 1: Raw Data
    tab1.header('Raw Data')
    tab1.write(df)

    # Tab 2: Normalized Data
    tab2.header('Normalized Raw Data')
    tab2.write(df_tidy)

    # Tab 3: Descriptive Stats
    tab3.header('Descriptive Statistics')
    tab3.write(stat)

    # Tab 4: Graphs
    tab4.header('2D Graphs')

    # Graph settings
    x = tab4.selectbox('Choose your x-axis:', options=variables)
    x_type = tab4.selectbox(
        'Is your x-axis variable continuous or categorical?',
        options=['continuous', 'categorical']
    )
    color = tab4.selectbox('Choose color grouping (optional):', ['None'] + variables)
    facet = tab4.selectbox('Choose faceting variable (optional):', ['None'] + variables)
    log_x = tab4.radio('Log scale for x-axis?', ['yes', 'no'])

    if color == 'None': color = None
    if facet == 'None': facet = None
    if color == facet and color is not None:
        tab4.warning("Color and facet variables should not be the same.")

    y_vars = [
        'TLH_normalized', 'CLH_normalized', 'T-C_normalized',
        'T/C_normalized', 'C/T_normalized',
        'TLA_normalized', 'CLA_normalized',
        'TLH', 'CLH', 'TLA', 'CLA'
    ]

    for y in y_vars:
        try:
            if x_type == 'continuous':
                df_tidy[x] = pd.to_numeric(df_tidy[x], errors='coerce')
                fig = px.scatter(
                    df_tidy,
                    x=x, y=y,
                    color=color,
                    facet_col=facet,
                    trendline='lowess',
                    log_x=(log_x == 'yes'),
                    title=f"{y} vs {x}"
                )
            else:
                df_tidy[x] = df_tidy[x].astype(str)
                fig = px.box(
                    df_tidy,
                    x=x, y=y,
                    color=color,
                    facet_col=facet,
                    log_x=(log_x == 'yes'),
                    title=f"{y} by {x}"
                )
            tab4.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            tab4.error(f"Could not plot {y}: {e}")
