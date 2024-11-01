import numpy as np
import pandas as pd
import nltk
import pickle
import re
from nltk.stem.porter import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import ast
import json
import kagglehub
import warnings
from tabulate import tabulate
from supabase import create_client, Client
from huggingface_hub import hf_hub_download

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
# CONNECT TO DTB
url: str = ("https://kpaxjjmelbqpllxenpxz.supabase.co")
key: str = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYXhqam1lbGJxcGxseGVucHh6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5MzA0NjQ5NCwiZXhwIjoyMDA4NjIyNDk0fQ.hGeExPN7h7gYiOILzPU57vSob9LC1UB-W2o6Z7WGLZs")
supabase: Client = create_client(url, key)

# DOWNLOAD VNESE STOP WORDS || USE FOR FIRST INITIALIZE
# hf_hub_download(repo_id="tpha4308/keyword-extraction-viet", filename="vietnamese-stopwords-dash.txt", local_dir="./stop_words")

# COLLECT DATA
film = supabase.table("film").select("*").execute()
film_data = film.data

cast = supabase.table("cast").select("*").execute()
cast_data = cast.data

crew = supabase.table("crew").select("*").execute()
crew_data = crew.data

person = supabase.table("person").select("*").execute()
person_data = person.data

film_genre = supabase.table("film_genre").select("*").execute()
film_genre_data = film_genre.data

genre = supabase.table("genre").select("*").execute()
genre_data = genre.data

films = pd.DataFrame(film_data)
casts = pd.DataFrame(cast_data)
crews = pd.DataFrame(crew_data)
people = pd.DataFrame(person_data)
genres = pd.DataFrame(genre_data)
film_genres = pd.DataFrame(film_genre_data)

# MERGE TABLES
genres_data = film_genres.merge(genres, left_on='genre_id', how='outer', right_on='id', suffixes=('_film_genre', '_genre'))
crews_data = crews.merge(people, left_on='person_id', how='outer', right_on='id', suffixes=('_crew', '_person'))
films_data = films.merge(casts, left_on='id', how='outer', right_on='film_id', suffixes=('_film', '_cast'))
films_data = films_data.merge(crews_data, left_on='id', how='outer', right_on='film_id', suffixes=('', '_crew')).fillna('NAN')
films_data = films_data.merge(genres_data, left_on='id', how='outer', right_on='film_id', suffixes=('', '_genre')).fillna('NAN')

# CLEAN AND CHOOSE WHICH COLUMN TO DISPLAY
data_set = films_data[['id','name','overview','name_genre','search_context','character','name_crew']]
data_set = data_set.groupby('id').agg(lambda x: list(set(x))).reset_index()
data_set.rename(columns={'name_crew': 'crew', 'character': 'cast', 'name': 'title', 'name_genre': 'genres'}, inplace=True)

def refactor(values):
    return [i.replace(" /", ",") if isinstance(i, str) else i for i in values]

def collapse(values):
    return [i.replace("_", " ") if isinstance(i, str) else i for i in values]

def split_phrases(values):
    return [i.split(", ") if isinstance(i, str) else i for i in values]

data_set['cast'] = data_set['cast'].apply(collapse)
data_set['crew'] = data_set['crew'].apply(collapse)
data_set['genres'] = data_set['genres'].apply(collapse)
data_set['search_context'] = data_set['search_context'].apply(refactor)
data_set['search_context'] = data_set['search_context'].apply(collapse)
data_set['search_context'] = data_set['search_context'].apply(split_phrases).explode()
data_set['overview'] = data_set['overview'].astype(str).apply(lambda x: x.replace("['","").replace("']",""))
data_set['title'] = data_set['title'].astype(str).apply(lambda x: x.replace("['","").replace("']",""))


# MERGE NEEDED INFORMATION INTO 'TAGS' COLUMN
data_set['overview'] = data_set['overview'].apply(lambda x: x.split())
data_set['tags'] = data_set['overview'] + data_set['genres'] + data_set['search_context'] + data_set['cast'] + data_set['crew']
# print(tabulate(data_set[['title','search_context']]))

new = data_set.drop(columns=['overview', 'genres', 'search_context', 'cast', 'crew'])
new['tags'] = new['tags'].apply(lambda x: " ".join(x))

# ADD STOP WORDS -> SIMPLIFY TAGS
# Load custom stop words from a txt file
with open('./stop_words/vietnamese-stopwords-dash.txt', 'r') as f:
    custom_stop_words = f.read().split('\n')

custom_stop_words = [word.strip().replace('_', ' ') for word in custom_stop_words]
cv = CountVectorizer(max_features=5000, stop_words=custom_stop_words)
vector = cv.fit_transform(new['tags']).toarray()

ps = PorterStemmer()
def stem(text):
    return " ".join([ps.stem(word) for word in text.split()])
new['tags'] = new['tags'].apply(stem)

# BUILDING RECOMMEND SYSTEMs
similarity = cosine_similarity(vector)

def recommend(movie):
    index = new[new['title'] == movie].index[0]
    movie_list = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommendations = [new.iloc[i[0]].title for i in movie_list[1:6]]
    return recommendations

pickle.dump(new, open('movie_list.pkl', 'wb'))
pickle.dump(similarity, open('similarity.pkl', 'wb'))

