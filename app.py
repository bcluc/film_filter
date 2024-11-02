from flask import Flask, request, jsonify
import pickle
from flasgger import Swagger

# Load data and similarity model from pickle files
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Initialize Flask app
app = Flask(__name__)
swagger = Swagger(app)  # Initialize Swagger

# Recommendation function for titles only
def recommend(movie):
    if movie not in movies['id'].values:
        return []  # Return an empty list if the movie is not found
    index = movies[movies['id'] == movie].index[0]
    movie_list = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])[1:6]
    return [movies.iloc[i[0]].title for i in movie_list]

# Extended recommendation function with details
def recommend_with_details(movie):
    if movie not in movies['id'].values:
        return []
    index = movies[movies['id'] == movie].index[0]
    movie_list = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])[1:6]
    
    # Return details like movie_id, title, and tags
    recommendations = [
        {
            'movie_id': movies.iloc[i[0]].id,
            'title': movies.iloc[i[0]].title,
            'poster_path': movies.iloc[i[0]].poster_path
        }
        for i in movie_list
    ]
    return recommendations

@app.route('/movies', methods=['GET'])
def get_all_movies():
    """
    Get All Movies
    ---
    description: Get a list of all available movie titles
    responses:
      200:
        description: A list of movie titles
        schema:
          type: object
          properties:
            movies:
              type: array
              items:
                type: string
    """
    all_titles = movies['title'].tolist()
    return jsonify({'movies': all_titles})

@app.route('/movie-details', methods=['GET'])
def movie_details():
    """
    Get Movie Details
    ---
    parameters:
      - name: movie_id
        in: query
        type: string
        required: true
        description: The id of the movie to retrieve details for
    responses:
      200:
        description: Detailed information about the movie
        schema:
          type: object
          properties:
            movie_id:
              type: integer
            title:
              type: string
            tags:
              type: string
      404:
        description: Movie not found
    """
    movie_title = request.args.get('movie')
    movie = movies[movies['id'] == movie_title]
    
    if movie.empty:
        return jsonify({'error': 'Movie not found'}), 404

    movie_data = {
        'movie_id': movie.iloc[0].id,
        'title': movie.iloc[0].title,
        'poster_path': movies.iloc[0].poster_path
    }
    return jsonify(movie_data)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    ---
    description: Check if the server is running
    responses:
      200:
        description: Server is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "Healthy"
    """
    return jsonify({'status': 'Healthy'}), 200
# Run the app
if __name__ == '__main__':
    app.run(debug=True)