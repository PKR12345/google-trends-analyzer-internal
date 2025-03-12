import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import plotly.graph_objs as go
from langchain_community.utilities import GoogleSerperAPIWrapper
import os
import ast
from google import genai
from datetime import datetime

os.environ["SERPER_API_KEY"] = "8ab032d2b62c29259a0e0bf4eaf65fc2be8feb75"

# Initialize session state variables
if 'economic_data' not in st.session_state:
    st.session_state.economic_data = None
if 'google_trends_data' not in st.session_state:
    st.session_state.google_trends_data = {}
if 'prev_params' not in st.session_state:
    st.session_state.prev_params = {}
if 'keyword_suggestions' not in st.session_state:
    st.session_state.keyword_suggestions = {}
if 'news_summaries' not in st.session_state:
    st.session_state.news_summaries = {}
if 'pg_news_summaries' not in st.session_state:
    st.session_state.pg_news_summaries = {}
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False

# Sidebar - Global parameters for pytrends
st.sidebar.title("Pytrends Configuration")
keywords_input = st.sidebar.text_input(
    "Enter keywords (comma separated):", 
    "Inflation",
    help="""**kw_list**: Keywords to analyze (max 5). 
    - Example: For ['Inflation', 'DEI'], enter Inflation, DEI
    - Use pytrends.suggestions() for topic IDs
    - Advanced: Use '/m/025rw19' format for specific topics"""
)
keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

# Timeframe Help
timeframe = st.sidebar.selectbox(
    "Timeframe (e.g., 'today 12-m'):", 
    ["today 12-m", "today 3-m", "today 5-y", "now 7-d", "now 1-H"],
    help="""**timeframe**: Date range for analysis
    - Default: 'today 5-y' (last 5 years)
    - Specific: '2016-12-14 2017-01-25'
    - Patterns: 
      - 'today 3-m' (3 months)
      - 'now 7-d' (7 days)
      - 'now 1-H' (1 hour)
      - 'today 12-m' (12 months)
    - UTC time used"""
)

# Geo Help
geo = st.sidebar.selectbox(
    "Region (Geo code, e.g., 'US'):", 
    ["US", "GB", "IN", "CN"],
    help="""**geo**: Geographic target
    - Country codes: 'US', 'CN' 
    - States: 'US-AL', 'GB-ENG'
    - Multiple regions: ['US-CA', 'US-TX']
    - Default: Worldwide"""
)

# Gprop Help
gprop = st.sidebar.selectbox(
    "Google Property:", 
    ["news", "web search", "youtube", "google shopping"],
    help="""**gprop**: Google property filter
    - Options: 'images', 'news', 'youtube', 'froogle'
    - Default: Web search"""
)

if gprop == "web search":
    gprop = ""
elif gprop == "google shopping":
    gprop = "froogle"

# Tz Help
tz = 360

# Category Help (if you have a category input)
retries = st.sidebar.number_input("Number of Retries:", min_value=0, value=10,
                                 help="""*retries***: Number of retries
                                 - No of times the agent can retry requesting the api
                                 - Increase this incase of 'Max Retries Error'
                                 - Defaults to 10""")
backoff_factor = 0.10

tabs_overall = st.tabs(['Google Trends'])

# # Economic Factors Tab
# with tabs_overall[1]:
#     if st.session_state.economic_data is None:
#         df = pd.read_excel(r"C:\Users\pranav.reddy\Downloads\Nielsen home care.xlsx")
#         df.sort_values(by=['Month'], inplace=True)
        
#         agg_dict = {
#             '$ Sales': 'sum',
#             'VOL Sales': 'sum',
#             'Inflation Rate': 'mean',
#             'Unemplayment Rate': 'mean',
#             'Savings Rate': 'mean',
        #     'Wage Growth': 'mean',
        #     'Housing Starts % growth 1MA': 'mean'
        # }
        
        # df_grouped = df.groupby(['PG SUBSECTOR', 'PG MANUFACTURER', 'Month']).agg(agg_dict).reset_index()
        # df_total = df_grouped[(df_grouped['PG SUBSECTOR'] == 'HOME CARE SUBSECTOR') & 
        #                       (df_grouped['PG MANUFACTURER'] == 'Total')]
        # df_pg = df_grouped[(df_grouped['PG SUBSECTOR'] == 'HOME CARE SUBSECTOR') & 
        #                    (df_grouped['PG MANUFACTURER'] == 'PROCTER & GAMBLE')]
        
        # st.session_state.economic_data = {
        #     'df_total': df_total,
        #     'df_pg': df_pg,
        #     'sales_options': ['$ Sales', 'VOL Sales'],
        #     'indicator_options': ['Inflation Rate', 'Unemplayment Rate', 'Savings Rate', 
        #                           'Wage Growth', 'Housing Starts % growth 1MA']
        # }
    
    # economic_data = st.session_state.economic_data
    # selected_sales = st.selectbox("Select Sales Type", economic_data['sales_options'])
    # selected_indicator = st.selectbox("Select Economic Indicator", economic_data['indicator_options'])

    # def create_dual_axis_plot(data, title):
    #     fig = go.Figure()
    #     fig.add_trace(go.Scatter(
    #         x=data['Month'],
    #         y=data[selected_sales],
    #         name=selected_sales,
    #         mode='lines+markers',
    #         line=dict(color='blue'),
    #         yaxis='y1'
    #     ))
    #     fig.add_trace(go.Scatter(
    #         x=data['Month'],
    #         y=data[selected_indicator],
    #         name=selected_indicator,
            # mode='lines+markers',
    #         line=dict(color='red'),
    #         yaxis='y2'
    #     ))
    #     fig.update_layout(
    #         title=title,
    #         xaxis=dict(title="Month"),
    #         yaxis=dict(title=dict(text=selected_sales, font=dict(color='blue'))),
    #         yaxis2=dict(title=dict(text=selected_indicator, font=dict(color='red')), 
    #                   overlaying='y', side='right'),
    #         legend=dict(orientation='h')
    #     )
    #     return fig

    # fig_total = create_dual_axis_plot(economic_data['df_total'], "Trend Plot for TOTAL HOME CARE")
    # fig_pg = create_dual_axis_plot(economic_data['df_pg'], "Trend Plot for PROCTER & GAMBLE HOME CARE")
    
    # corr_total = economic_data['df_total'][selected_sales].corr(economic_data['df_total'][selected_indicator])
    # corr_pg = economic_data['df_pg'][selected_sales].corr(economic_data['df_pg'][selected_indicator])
    
    # st.plotly_chart(fig_total, use_container_width=True)
    # st.write(f"**Correlation (Total):** {corr_total:.2f}")
    # st.plotly_chart(fig_pg, use_container_width=True)
    # st.write(f"**Correlation (PROCTER & GAMBLE):** {corr_pg:.2f}")

# Google Trends Tab
with tabs_overall[0]:
    if st.sidebar.button("Run Analysis") or st.session_state.get('analysis_run', False):
        with st.spinner("Fetching Data from Google Trends API, it may take 2-3 minutes..."):
            st.session_state.analysis_run = True
            with st.expander("User Manual 📘 - Click to Expand", expanded=False):
                st.markdown("""
                ## Google Trends Analysis Guide
                
                ### Overview
                This tab helps analyze Google search trends and related news. It contains 4 sections:
                1. Interest Over Time
                2. Interest by Region
                3. Keyword Suggestions
                4. News Summaries
                
                ---
                
                ### 1. Interest Over Time 📈
                **What it does:**  
                - Shows search interest for your keywords over selected timeframe  
                - Displays trends as interactive line chart  
                - Shows raw data table below
                
                **How to use:**  
                - Enter keywords in sidebar (comma-separated)  
                - Adjust timeframe/region in sidebar  
                - Hover over chart points for exact values  
                - Scroll table to see historical data
                
                ---
                
                ### 2. Interest by Region 🌍  
                **What it does:**  
                - Shows regional interest distribution  
                - Displays data in sortable table format  
                - Higher values = more relative interest
                
                **Note:**  
                - Works best with country-level regions (US, CN, etc.)  
                - Blank results mean low search volume
                
                ---
                
                ### 3. Keyword Suggestions 💡  
                **What it does:**  
                - Provides related search terms  
                - Helps discover new keywords  
                - Shows Google's auto-suggestions
                
                **How to use:**  
                1. Enter a seed keyword  
                2. See suggestions in table  
                3. Click interesting terms to copy
                
                ---
                
                ### 4. News Summaries 📰  
                **What it does:**  
                - Finds latest news for your keywords  
                - Lets you select articles for AI analysis  
                - Provides CPG industry impact assessment
                
                **Workflow:**  
                1. See news results table  
                2. Select article from dropdown  
                3. Click "Generate Summary"  
                4. Get:  
                   - Article summary  
                   - CPG industry impact analysis
                
                **Note:**  
                - Summaries powered by Gemini AI  
                - First generation may take 10-15 seconds
                
                ---
                
                ### General Tips 🔧
                - Use sidebar for all configuration  
                - Change parameters > click outside to refresh  
                - Cached results speed up repeat use  
                - API errors usually fix with retry  
                - Hover over ❔ icons for help  
                """)
        
            current_params = {
                'keywords': keywords,
                'timeframe': timeframe,
                'geo': geo,
                'gprop': gprop,
                'tz': tz,
                'retries': retries,
                'backoff_factor': backoff_factor
            }
            
            if current_params != st.session_state.prev_params:
                pytrends = TrendReq(hl='en-US', tz=tz, retries=retries, backoff_factor=backoff_factor)
                if keywords:
                    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop=gprop)
                    try:
                        st.session_state.google_trends_data['data_iot'] = pytrends.interest_over_time()
                    except Exception as e:
                        st.error(f"Error retrieving Interest Over Time data: {e}")
                        st.session_state.google_trends_data['data_iot'] = pd.DataFrame()
                    try:
                        st.session_state.google_trends_data['data_ibr'] = pytrends.interest_by_region()
                    except Exception as e:
                        st.error(f"Error retrieving Interest by Region data: {e}")
                        st.session_state.google_trends_data['data_ibr'] = pd.DataFrame()
                st.session_state.prev_params = current_params
            
            tabs = st.tabs(["Interest Over Time", "Interest by Region", "Summary", "P&G Product Summary","Keyword Suggestions"])
            
            with tabs[0]:
                st.header("Interest Over Time")
                data_iot = st.session_state.google_trends_data.get('data_iot', pd.DataFrame())
                if not data_iot.empty:
                    st.line_chart(data_iot.drop(columns = ['isPartial'], axis =1))
                    st.dataframe(data_iot.drop(columns = ['isPartial'], axis =1))
                else:
                    st.write("No data available for the given parameters.")
            
            with tabs[1]:
                st.header("Interest by Region")
                data_ibr = st.session_state.google_trends_data.get('data_ibr', pd.DataFrame())
                if not data_ibr.empty:
                    st.dataframe(data_ibr.sort_values([keywords[0]],ascending=False))
                else:
                    st.write("No data available for the selected region.")
            
            with tabs[4]:
                st.header("Keyword Suggestions")
                suggestion_keyword = st.text_input("Enter a keyword for suggestions:", "Trump", key="suggestions")
                if suggestion_keyword:
                    if suggestion_keyword in st.session_state.keyword_suggestions:
                        suggestions = st.session_state.keyword_suggestions[suggestion_keyword]
                    else:
                        try:
                            pytrends = TrendReq(hl='en-US', tz=tz, retries=retries, backoff_factor=backoff_factor)
                            suggestions = pytrends.suggestions(suggestion_keyword)
                            st.session_state.keyword_suggestions[suggestion_keyword] = suggestions
                        except Exception as e:
                            st.error(f"Error retrieving Keyword Suggestions: {e}")
                            suggestions = []
                    if suggestions:
                        st.dataframe(pd.DataFrame(suggestions))
                    else:
                        st.write("No suggestions found for the given keyword.")
            
            # with tabs[3]:
            #     try:
            #         def extract_news_summary(topic, time_posted):
            #               utc_time = datetime.utcnow()
            #               # create client
            #               client = genai.Client(api_key=os.getenv("GEMINI_API_KEY","AIzaSyCJeqV2cNBq2m-ozeoaOw5JO88FhBfNhwc"))
                        
            #               prompt = f"""You are an experienced journalist, who has 30 plus year of experience in providing enriching and true news 
            #               to viewers around the world. Given an article topic provided by the user, your task to fetch all the information regarding
            #               the article and summerize it crisp and clear for the user. Also understand the information in detailed and provide your view
            #               on whether the information has any potential impact on the CPG Industry. You must return the response in the output format.
                        
            #               Output Format:
            #               <summary>
            #               [The summary goes here]
            #               <\summary>
            #               <impact_on_cpg_industry>
            #               [Your view on the impact on the CPG industry goes here]
            #               <\impact_on_cpg_industry>
                        
            #               Instructions:
            #               1. Make sure to provide the response in the output format.
            #               2. Think step by step and approach the problem intelligently to come with the final response.
            #               3. If you think that the information does not have any relation or does not impact the CPG industry, then mention your view as 'Not Applicable'. 
                        
            #               Conversation Date: Today is {utc_time}
            #               Time when article was posted: {time_posted}
            #               User Article Topic: {topic}
                        
            #               Response:
            #               """
            #               # Generate a list of cookie recipes
            #               response = client.models.generate_content(
            #                   model='gemini-2.0-flash',
            #                   contents=prompt,
            #                   config={"tools": [{"google_search": {}}]},
            #               )
                        
            #               return response.text
                        
            #         if keywords != st.session_state.get('news_keywords', []):
            #             summary_dict = {}
            #             for keyword in keywords:
            #                 search = GoogleSerperAPIWrapper(type="news")
            #                 results = search.results(keyword)
            #                 news_data = {
            #                     'Title': [n.get('title', '') for n in results.get('news', [])],
            #                     'Link': [n.get('link', '') for n in results.get('news', [])],
            #                     'Date': [n.get('date', '') for n in results.get('news', [])],
            #                     'Source': [n.get('source', '') for n in results.get('news', [])]
            #                 }
            #                 summary_dict[keyword] = pd.DataFrame(news_data)
            #             st.session_state.news_summaries = summary_dict
            #             st.session_state.news_keywords = keywords.copy()
                    
            #         # Initialize summary cache if not exists
            #         if 'summary_cache' not in st.session_state:
            #             st.session_state.summary_cache = {}
                    
            #         for keyword in keywords:
            #             st.subheader(keyword)
            #             if keyword in st.session_state.news_summaries:
            #                 df_news = st.session_state.news_summaries[keyword]
            #                 st.dataframe(df_news)
                            
            #                 # Article selection
            #                 titles = df_news['Title'].tolist()
            #                 selected_title = st.selectbox(
            #                     f"Select article to summarize ({keyword})", 
            #                     titles,
            #                     key=f"select_{keyword}"
            #                 )
                            
            #                 # Get selected article details
            #                 selected_article = df_news[df_news['Title'] == selected_title].iloc[0]
            #                 time_posted = selected_article['Date']
            #                 article_topic = selected_article['Title']
                            
            #                 # Check cache or generate summary
            #                 cache_key = f"{keyword}|{selected_title}"
            #                 if cache_key not in st.session_state.summary_cache:
            #                     if st.button(f"Generate Summary for '{selected_title}'", key=f"btn_{cache_key}"):
            #                         with st.spinner("Generating summary..."):
            #                             try:
            #                                 summary_response = extract_news_summary(article_topic, time_posted)
            #                                 st.write(summary_response)
            #                                 # Parse the response
            #                                 summary = summary_response.split("<summary>")[1].split("</summary>")[0].strip()
            #                                 impact = summary_response.split("<impact_on_cpg_industry>")[1].split("</impact_on_cpg_industry>")[0].strip()
                                            
            #                                 st.session_state.summary_cache[cache_key] = {
            #                                     'summary': summary,
            #                                     'impact': impact
            #                                 }
            #                             except Exception as e:
            #                                 st.error(f"Error generating summary: {e}")
            #                 else:
            #                     # Display cached summary
            #                     cached = st.session_state.summary_cache[cache_key]
            #                     st.subheader("Summary")
            #                     st.write(cached['summary'])
                                
            #                     st.subheader("Potential Impact on CPG Industry")
            #                     st.write(cached['impact'])
                            
            #                 st.markdown("---")
                            
            #     except Exception as e:
            #         st.error(f"Error retrieving Summaries: {e}")
        
                with tabs[2]:
                    try:
                        # Initialize summary cache in session state
                        if 'summary_cache' not in st.session_state:
                            st.session_state.summary_cache = {}
                
                        # Initialize Gemini client
                        def get_gemini_client():
                            return genai.Client(api_key=os.getenv("GEMINI_API_KEY","AIzaSyCJeqV2cNBq2m-ozeoaOw5JO88FhBfNhwc"))
                
                        # Modified summary extraction function
                        def extract_news_summary(topic, time_posted):
                            utc_time = datetime.utcnow()
                            client = get_gemini_client()
                            
                            prompt = f"""You are an experienced journalist, who has 30 plus year of experience in providing enriching and true news 
                                  to viewers around the world. Given an article topic provided by the user, your task to fetch all the information regarding
                                  the article and summerize it crisp and clear for the user. Also understand the information in detailed and provide your view
                                  on whether the information has any potential impact on the CPG Industry. You must return the response in the output format.
                                
                                  Output Format:
                                  <summary>
                                  [The summary goes here]
                                  </summary>
                                  <impact_on_cpg_industry>
                                  [Your view on the impact on the CPG industry goes here]
                                  </impact_on_cpg_industry>
                                
                                  Instructions:
                                  1. Make sure to provide the response in the output format.
                                  2. Think step by step and approach the problem intelligently to come with the final response.
                                  3. If you think that the information does not have any relation or does not impact the CPG industry, then mention your view as 'Not Applicable'. 
                                
                                  Conversation Date: Today is {utc_time}
                                  Time when article was posted: {time_posted}
                                  User Article Topic: {topic}
                                
                                  Response:
                                  """
                            
                            response = client.models.generate_content(
                                 model='gemini-2.0-flash',
                                 contents=prompt,
                                 config={"tools": [{"google_search": {}}]},
                            )
                            return response.text
                
                        # Check if we need to refresh news data
                        if keywords != st.session_state.get('news_keywords', []):
                            summary_dict = {}
                            for keyword in keywords:
                                search = GoogleSerperAPIWrapper(type="news")
                                results = search.results(keyword)
                                news_data = {
                                    'Title': [n.get('title', '') for n in results.get('news', [])],
                                    'Link': [n.get('link', '') for n in results.get('news', [])],
                                    'Date': [n.get('date', '') for n in results.get('news', [])],
                                    'Source': [n.get('source', '') for n in results.get('news', [])]
                                }
                                summary_dict[keyword] = pd.DataFrame(news_data)
                            st.session_state.news_summaries = summary_dict
                            st.session_state.news_keywords = keywords.copy()
                
                        # Display news and handle summaries
                        for keyword in keywords:
                            st.subheader(f"News for: {keyword}")
                            if keyword in st.session_state.news_summaries:
                                df_news = st.session_state.news_summaries[keyword]
                                
                                # Display news dataframe
                                st.dataframe(df_news)
                                
                                # Article selection
                                titles = df_news['Title'].tolist()
                                selected_title = st.selectbox(
                                    f"Select article to summarize ({keyword})", 
                                    titles,
                                    key=f"select_{hash(keyword)}"  # Unique key per keyword
                                )
                                
                                # Get selected article details
                                selected_article = df_news[df_news['Title'] == selected_title].iloc[0]
                                cache_key = f"{keyword}|{selected_title}"
                                if cache_key in st.session_state.summary_cache:
                                    if st.button("Clear Summary", key=f"clear_{hash(cache_key)}"):
                                        del st.session_state.summary_cache[cache_key]
                                        temp_button = st.button(f"Generate Summary for '{selected_title}'", 
                                           key=f"btn_{hash(cache_key)}")
                                        break
                                    # del st.session_state.active_article
                                
                                # Generate summary button
                                if st.button(f"Generate Summary for '{selected_title}'", 
                                           key=f"btn_{hash(cache_key)}"):
                                    # Clear previous summary if any
                                    # if cache_key in st.session_state.summary_cache:
                                    #     del st.session_state.summary_cache[cache_key]
                                    
                                    # Store in session state to persist across reruns
                                    st.session_state.active_article = {
                                        'key': cache_key,
                                        'title': selected_title,
                                        'time': selected_article['Date'],
                                        'topic': selected_article['Title']
                                    }
                
                                # Check if we have an active article to process
                                if 'active_article' in st.session_state:
                                    active = st.session_state.active_article
                                    
                                    # Only process if it matches current keyword/article
                                    if active['key'] == cache_key:
                                        # if st.button("Clear Summary", key=f"clear_{hash(cache_key)}"):
                                        #         del st.session_state.summary_cache[cache_key]
                                        #         del st.session_state.active_article
                                            
                                        if cache_key not in st.session_state.summary_cache:
                                            with st.spinner("Generating summary (this may take 10-15 seconds)..."):
                                                try:
                                                    st.write(active['topic'])
                                                    raw_response = extract_news_summary(
                                                        active['topic'], 
                                                        active['time']
                                                    )
                                                    # Parse response
                                                    summary = raw_response.split("<summary>")[1].split("</summary>")[0].strip()
                                                    impact = raw_response.split("<impact_on_cpg_industry>")[1].split("</impact_on_cpg_industry>")[0].strip()
                                                    
                                                    # Store in cache
                                                    st.session_state.summary_cache[cache_key] = {
                                                        'summary': summary,
                                                        'impact': impact
                                                    }
                                                except Exception as e:
                                                    st.error(f"Error generating summary: {str(e)}")
                                                    st.session_state.summary_cache[cache_key] = {
                                                        'summary': "Error generating summary",
                                                        'impact': "Error analyzing impact"
                                                    }
                                        
                                        # Display cached results
                                        if cache_key in st.session_state.summary_cache:
                                            cached = st.session_state.summary_cache[cache_key]
                                            
                                            st.subheader("Summary")
                                            st.write(cached['summary'])
                                            
                                            st.subheader("Potential Impact on CPG Industry")
                                            st.write(cached['impact'])
                                            
                                            # Add clear button
                                            # if st.button("Clear Summary", key=f"clear_{hash(cache_key)}"):
                                            #     del st.session_state.summary_cache[cache_key]
                                            #     del st.session_state.active_article
                
                                st.markdown("---")
                
                    except Exception as e:
                        st.error(f"Error in news summary section: {str(e)}")
                        
                with tabs[3]:
                    st.header("P&G keyword summary analysis")
                    try:
                        # Initialize Gemini client
                        def get_gemini_client():
                            return genai.Client(api_key=os.getenv("GEMINI_API_KEY","AIzaSyCJeqV2cNBq2m-ozeoaOw5JO88FhBfNhwc"))
                        
                        # Modified summary extraction function
                        def extract_top_keywords(brand):
                            utc_time = datetime.utcnow()
                            client = get_gemini_client()
                            
                            prompt = f"""You are an experience Consultant who works for P&G, who has 30 plus year of experience with the company and has in-depth knowledge about the different brand in P&G. 
                                  Given an P&G brand provided by the user, your task to give me the list of top 10 searched keywords related to the brand on google in the US region in the last 1 month. You must return the response as a python list of keywords in the output format.
                                
                                  Output Format:
                                  ```python
                                  [
                                  \"keyword 1\",
                                  \"keyword 2\",
                                  .
                                  .
                                  \"keyword 10\"
                                  ]
                                  ```
                                
                                  Instructions:
                                  1. Make sure to provide the response in the output format.
                                  2. Think step by step and approach the problem intelligently to come with the final response.
                                  3. If you think that the information does not have any relation or does not impact the CPG industry, then mention your view as 'Not Applicable'. 
                                
                                  Conversation Date: Today is {utc_time}
                                  P&G Brand: {brand}
                                
                                  Response:
                                  """
                            response = client.models.generate_content(
                                 model='gemini-2.0-flash',
                                 contents=prompt,
                                 config={"tools": [{"google_search": {}}]},
                            )
                            return response.text
                            
                        if 'pg_brand_selection' not in st.session_state:
                            st.session_state.pg_brand_selection = None
                        if 'pg_brand_keyword_trend'not in st.session_state:
                            st.session_state.pg_brand_keyword_trend = {}
                        if 'top_keywords_by_brand' not in st.session_state:
                            st.session_state.top_keywords_by_brand = {}
                        if 'brand_keyword_selection' not in st.session_state:
                            st.session_state.brand_keyword_selection = None
                        if 'add_keyword' not in st.session_state:
                            st.session_state.add_keyword = None
                        if 'searh_type' not in st.session_state:
                            st.session_state.searh_type = None
                        brand_selection = st.selectbox(
                                    f"Select the P&G Brand",
                                    ['Dawn', 'Cascade', 'Febreze', 'Swiffer', 'Mr. Clean']
                        )
                        st.session_state.pg_brand_selection = brand_selection
                        if st.session_state.pg_brand_selection not in st.session_state.top_keywords_by_brand:
                            top_keywords_response = extract_top_keywords(st.session_state.pg_brand_selection)
                            top_keywords_str =  top_keywords_response.split("```python")[1].split("```")[0].strip()
                            top_keywords = ast.literal_eval(top_keywords_str)
                            st.session_state.top_keywords_by_brand[st.session_state.pg_brand_selection] = top_keywords
                        brand_keyword_selection = st.selectbox(
                                    f"Select the P&G keyword",
                                    st.session_state.top_keywords_by_brand[st.session_state.pg_brand_selection]
                        )
                        search_type = st.selectbox(
                                    f"Select the search type for analysis",
                                    ['news', 'web', 'shopping']
                        )
                        st.session_state.searh_type = search_type
                        st.session_state.brand_keyword_selection = brand_keyword_selection
                        add_keyword = st.text_input("Add any additional keyword:", st.session_state.pg_brand_selection)
                        if add_keyword!="" and add_keyword not in st.session_state.top_keywords_by_brand[st.session_state.pg_brand_selection]:
                            st.session_state.top_keywords_by_brand[st.session_state.pg_brand_selection].append(add_keyword)
                        if f"{st.session_state.brand_keyword_selection}-{st.session_state.searh_type}" not in st.session_state.pg_brand_keyword_trend:
                            if search_type=='web':
                                search_type = ''
                            elif search_type=='shopping':
                                search_type = 'froogle'
                            pytrends_1 = TrendReq(hl='en-US', tz=tz, retries=retries, backoff_factor=backoff_factor)
                            pytrends_1.build_payload([st.session_state.brand_keyword_selection], cat=0, timeframe='today 3-m', geo=geo, gprop=search_type)
                            try:
                                st.session_state.pg_brand_keyword_trend[f"{st.session_state.brand_keyword_selection}-{st.session_state.searh_type}"] = pytrends_1.interest_over_time()
                            except Exception as e:
                                st.error(f"Error retrieving Interest Over Time data: {e}")
                                st.session_state.pg_brand_keyword_trend[f"{st.session_state.brand_keyword_selection}-{st.session_state.searh_type}"] = pd.DataFrame()
                        data_iot_keyword = st.session_state.pg_brand_keyword_trend.get(f"{st.session_state.brand_keyword_selection}-{st.session_state.searh_type}", pd.DataFrame())
                        if not data_iot_keyword.empty:
                            st.line_chart(data_iot_keyword.drop(columns = ['isPartial'], axis =1))
                            st.dataframe(data_iot_keyword.drop(columns = ['isPartial'], axis =1))
                        else:
                            st.write("No data available for the given parameters.")
                        if 'pg_summary_cache' not in st.session_state:
                            st.session_state.pg_summary_cache = {}
                
                        # Modified summary extraction function
                        def extract_news_summary(topic, time_posted):
                            utc_time = datetime.utcnow()
                            client = get_gemini_client()
                            
                            prompt = f"""You are an experienced journalist, who has 30 plus year of experience in providing enriching and true news 
                                  to viewers around the world. Given an article topic provided by the user, your task to fetch all the information regarding
                                  the article and summerize it crisp and clear for the user. Also understand the information in detailed and provide your view
                                  on whether the information has any potential impact on the CPG Industry. You must return the response in the output format.
                                
                                  Output Format:
                                  <summary>
                                  [The summary goes here]
                                  </summary>
                                  <impact_on_cpg_industry>
                                  [Your view on the impact on the CPG industry goes here]
                                  </impact_on_cpg_industry>
                                
                                  Instructions:
                                  1. Make sure to provide the response in the output format.
                                  2. Think step by step and approach the problem intelligently to come with the final response.
                                  3. If you think that the information does not have any relation or does not impact the CPG industry, then mention your view as 'Not Applicable'. 
                                
                                  Conversation Date: Today is {utc_time}
                                  Time when article was posted: {time_posted}
                                  User Article Topic: {topic}
                                
                                  Response:
                                  """
                            
                            response = client.models.generate_content(
                                 model='gemini-2.0-flash',
                                 contents=prompt,
                                 config={"tools": [{"google_search": {}}]},
                            )
                            return response.text

                        pg_keywords = [st.session_state.brand_keyword_selection]
                        # Check if we need to refresh news data
                        if pg_keywords != st.session_state.get('pg_news_keywords', []):
                            summary_dict = {}
                            for keyword in pg_keywords:
                                search = GoogleSerperAPIWrapper(type="news")
                                results = search.results(keyword)
                                news_data = {
                                    'Title': [n.get('title', '') for n in results.get('news', [])],
                                    'Link': [n.get('link', '') for n in results.get('news', [])],
                                    'Date': [n.get('date', '') for n in results.get('news', [])],
                                    'Source': [n.get('source', '') for n in results.get('news', [])]
                                }
                                summary_dict[keyword] = pd.DataFrame(news_data)
                            st.session_state.pg_news_summaries = summary_dict
                            st.session_state.pg_news_keywords = pg_keywords.copy()
                
                        # Display news and handle summaries
                        for keyword in pg_keywords:
                            st.subheader(f"News for: {keyword}")
                            if keyword in st.session_state.pg_news_summaries:

                                pg_df_news = st.session_state.pg_news_summaries[keyword]
                                
                                # Display news dataframe
                                st.dataframe(pg_df_news)
                                
                                # Article selection
                                pg_titles = pg_df_news['Title'].tolist()
                                pg_selected_title = st.selectbox(
                                    f"Select article to summarize ({keyword})", 
                                    pg_titles,
                                    key=f"select_pg_{hash(keyword)}"  # Unique key per keyword
                                )
                                
                                # Get selected article details
                                pg_selected_article = pg_df_news[pg_df_news['Title'] == pg_selected_title].iloc[0]
                                pg_cache_key = f"{keyword}|{pg_selected_title}"
                                if pg_cache_key in st.session_state.pg_summary_cache:
                                    if st.button("Clear Summary", key=f"clear_{hash(pg_cache_key)}"):
                                        del st.session_state.pg_summary_cache[pg_cache_key]
                                        temp_button = st.button(f"Generate Summary for '{pg_selected_title}'", 
                                           key=f"btn_pg_{hash(pg_cache_key)}")
                                        break
                                    # del st.session_state.active_article
                                
                                # Generate summary button
                                if st.button(f"Generate Summary for '{pg_selected_title}'", 
                                           key=f"btn_pg_{hash(pg_cache_key)}"):
                                    # Clear previous summary if any
                                    # if cache_key in st.session_state.summary_cache:
                                    #     del st.session_state.summary_cache[cache_key]
                                    
                                    # Store in session state to persist across reruns
                                    st.session_state.pg_active_article = {
                                        'key': pg_cache_key,
                                        'title': pg_selected_title,
                                        'time': pg_selected_article['Date'],
                                        'topic': pg_selected_article['Title']
                                    }
                
                                # Check if we have an active article to process
                                if 'pg_active_article' in st.session_state:
                                    pg_active = st.session_state.pg_active_article
                                    
                                    # Only process if it matches current keyword/article
                                    if pg_active['key'] == pg_cache_key:
                                        # if st.button("Clear Summary", key=f"clear_{hash(cache_key)}"):
                                        #         del st.session_state.summary_cache[cache_key]
                                        #         del st.session_state.active_article
                                            
                                        if pg_cache_key not in st.session_state.pg_summary_cache:
                                            with st.spinner("Generating summary for P&G news article (this may take 10-15 seconds)..."):
                                                try:
                                                    st.write(pg_active['topic'])
                                                    pg_raw_response = extract_news_summary(
                                                        pg_active['topic'], 
                                                        pg_active['time']
                                                    )
                                                    # Parse response
                                                    pg_summary = pg_raw_response.split("<summary>")[1].split("</summary>")[0].strip()
                                                    pg_impact = pg_raw_response.split("<impact_on_cpg_industry>")[1].split("</impact_on_cpg_industry>")[0].strip()
                                                    
                                                    # Store in cache
                                                    st.session_state.pg_summary_cache[pg_cache_key] = {
                                                        'summary': pg_summary,
                                                        'impact': pg_impact
                                                    }
                                                except Exception as e:
                                                    st.error(f"Error generating summary: {str(e)}")
                                                    st.session_state.pg_summary_cache[pg_cache_key] = {
                                                        'summary': "Error generating summary",
                                                        'impact': "Error analyzing impact"
                                                    }
                                        
                                        # Display cached results
                                        if pg_cache_key in st.session_state.pg_summary_cache:
                                            pg_cached = st.session_state.pg_summary_cache[pg_cache_key]
                                            
                                            st.subheader("Summary")
                                            st.write(pg_cached['summary'])
                                            
                                            st.subheader("Potential Implications")
                                            st.write(pg_cached['impact'])
                                            
                                            # Add clear button
                                            # if st.button("Clear Summary", key=f"clear_{hash(cache_key)}"):
                                            #     del st.session_state.summary_cache[cache_key]
                                            #     del st.session_state.active_article
                
                                st.markdown("---")
                    except Exception as e:
                        st.error(f"Error in product summary section: {str(e)}")