import numpy as np
import pandas as pd
import nltk
import pickle
from nltk.stem.porter import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import ast
import json
from supabase import create_client, Client

url: str = ("https://kpaxjjmelbqpllxenpxz.supabase.co")
key: str = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYXhqam1lbGJxcGxseGVucHh6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5MzA0NjQ5NCwiZXhwIjoyMDA4NjIyNDk0fQ.hGeExPN7h7gYiOILzPU57vSob9LC1UB-W2o6Z7WGLZs")
supabase: Client = create_client(url, key)

film = supabase.table("film").select("*").execute()
film_data = film.data

cast = supabase.table("cast").select("*").execute()
cast_data = cast.data

crew = supabase.table("crew").select("*").execute()
crew_data = crew.data

films = pd.DataFrame(film_data)
casts = pd.DataFrame(cast_data)
crews = pd.DataFrame(crew_data)

films_data = films.merge(casts, left_on='id', right_on='film_id', suffixes=('_film', '_cast'))
films_data = films_data.merge(crews, left_on='id', right_on='film_id', suffixes=('', '_crew'))

print(films_data)
