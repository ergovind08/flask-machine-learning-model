from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load data and models
try:
    df = pickle.load(open('data/restaurants.pkl', 'rb'))
    unique_cuisines_df = pickle.load(open('data/Cuisine.pkl', 'rb'))
except Exception as e:
    print(f"Error loading data files: {e}")

unique_cuisines_list = unique_cuisines_df['Cuisine'].tolist()

# Ensure correct types for the DataFrame columns
df['AverageCost'] = pd.to_numeric(df['AverageCost'], errors='coerce')
df['IsHomeDelivery'] = pd.to_numeric(df['IsHomeDelivery'], errors='coerce')
df['Delivery Ratings'] = pd.to_numeric(df['Delivery Ratings'], errors='coerce')
df['Dinner Ratings'] = pd.to_numeric(df['Dinner Ratings'], errors='coerce')
df['isVegOnly'] = pd.to_numeric(df['isVegOnly'], errors='coerce')
df['isIndoorSeating'] = pd.to_numeric(df['isIndoorSeating'], errors='coerce')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cuisines', methods=['GET'])
def cuisines():
    return jsonify(unique_cuisines_list)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        preferred_cuisines = data['preferred_cuisines']
        budget = int(data['budget'])
        min_rating = float(data['min_rating'])
        veg_choice = data['veg_choice']
        order_choice = data['order_choice']

        print(f"Received request data: {data}")

        recommendations = recommend_restaurants(df, preferred_cuisines, budget, min_rating, veg_choice, order_choice)

        if recommendations is not None and not recommendations.empty:
            return jsonify(recommendations.to_dict(orient='records'))
        else:
            return jsonify([])
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def recommend_restaurants(df, preferred_cuisines, budget, min_rating, veg_choice, order_choice):
    try:
        # Apply filters
        if veg_choice == "Yes":
            df = df[df['isVegOnly'] == 1]
        elif veg_choice == "No":
            df = df[df['isVegOnly'] == 0]

        if order_choice == "Seating":
            df_filtered = df[(df['AverageCost'] <= budget) & (df['isIndoorSeating'] == 1) & (df['Dinner Ratings'] >= min_rating)]
        elif order_choice == "Order":
            df_filtered = df[(df['AverageCost'] <= budget) & (df['IsHomeDelivery'] == 1) & (df['Delivery Ratings'] >= min_rating)]
        else:
            df_filtered = df[(df['AverageCost'] <= budget) & (df['Dinner Ratings'] >= min_rating)]

        if df_filtered.empty:
            return None

        # Filter by preferred cuisines
        df_filtered['Cuisine'] = df_filtered['Cuisines'].apply(lambda x: ' '.join(cuisine.lower() for cuisine in str(x).split(', ')))
        df_filtered['Cuisine'] = df_filtered['Cuisine'].str.lower()
        df_filtered = df_filtered[df_filtered['Cuisine'].apply(lambda x: any(cuisine.lower() in x for cuisine in preferred_cuisines))]

        if df_filtered.empty:
            return None

        # Compute cosine similarity
        count = CountVectorizer(stop_words='english')
        count_matrix = count.fit_transform(df_filtered['Cuisine'])
        cosine_sim = cosine_similarity(count_matrix, count_matrix)

        df_filtered = df_filtered.reset_index()

        if df_filtered.empty:
            return None

        # Get recommendations
        df_filtered['Unique_ID'] = range(1, len(df_filtered) + 1)
        df_filtered['Unique_ID'] = df_filtered['Unique_ID'].astype(int)

        def get_recommendations(unique_id, cosine_sim=cosine_sim):
            try:
                idx = int(unique_id - 1)

                if idx >= len(cosine_sim):
                    return None

                sim_scores = cosine_sim[idx]
                threshold = np.mean(sim_scores)

                if any(score > threshold for score in sim_scores):
                    sim_scores_with_indices = list(enumerate(sim_scores))
                    sim_scores_with_indices = sorted(sim_scores_with_indices, key=lambda x: x[1], reverse=True)
                    sim_scores_with_indices = sim_scores_with_indices[1:11]
                    restaurant_indices = [i[0] for i in sim_scores_with_indices]

                    return df_filtered[['Name', 'URL', 'Full_Address', 'AverageCost', 'Cuisines']].iloc[restaurant_indices]
                else:
                    return None
            except Exception as e:
                print(f"Error in get_recommendations: {str(e)}")
                print(traceback.format_exc())
                return None

        # Check if df_filtered is empty before accessing it
        if df_filtered.empty:
            return None

        recommendations = get_recommendations(df_filtered['Unique_ID'].iloc[0])

        return recommendations
    except Exception as e:
        print(f"Error in recommend_restaurants: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == '__main__':
    app.run(debug=True)
