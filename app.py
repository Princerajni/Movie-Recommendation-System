import streamlit as st
import pandas as pd
import requests
import pickle
import ssl
import certifi
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load the processed data and similarity matrix
with open('movie_data.pkl', 'rb') as file:
    movies, cosine_sim = pickle.load(file)


# Function to get movie recommendations
def get_recommendations(title, cosine_sim=cosine_sim):
    idx = movies[movies['title'] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]  # Get top 10 similar movies
    movie_indices = [i[0] for i in sim_scores]
    return movies[['title', 'movie_id']].iloc[movie_indices]


# **Improved Fetch Movie Poster Function with SSL Fix & Retries**
def fetch_poster(movie_id):
    api_key = 'YOUR_TMDB_API_KEY'
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'

    # Setup retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    try:
        response = http.get(url, verify=certifi.where(), timeout=5)  # Timeout added
        response.raise_for_status()  # Raise error for bad responses
        data = response.json()
        poster_path = data.get('poster_path', '')

        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        return None  # If poster isn't available

    except requests.exceptions.SSLError as ssl_err:
        print(f"SSL Error: {ssl_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request Error: {req_err}")
        return None


# Streamlit UI
st.title("Movie Recommendation System")

selected_movie = st.selectbox("Select a movie:", movies['title'].values)

if st.button('Recommend'):
    recommendations = get_recommendations(selected_movie)
    st.write("Top 10 recommended movies:")

    # Create a 2x5 grid layout
    for i in range(0, 10, 5):  # Loop over rows (2 rows, 5 movies each)
        cols = st.columns(5)  # Create 5 columns for each row
        for col, j in zip(cols, range(i, i + 5)):
            if j < len(recommendations):
                movie_title = recommendations.iloc[j]['title']
                movie_id = recommendations.iloc[j]['movie_id']
                poster_url = fetch_poster(movie_id)
                with col:
                    if poster_url:
                        st.image(poster_url, width=130)
                    else:
                        st.write("Poster unavailable")
                    st.write(movie_title)