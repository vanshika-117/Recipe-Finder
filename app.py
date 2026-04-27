import streamlit as st
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="🍲 Recipe Finder", layout="wide")

API_KEY = st.secrets["API_KEY"]

# ---------------- API FUNCTION ----------------
def get_recipes_from_api(query):
    url = "https://api.spoonacular.com/recipes/complexSearch"

    params = {
        "apiKey": API_KEY,
        "query": query,
        "number": 10,
        "addRecipeInformation": True
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("results", [])
    except:
        return []

# ---------------- SESSION STATE ----------------
if "favorites" not in st.session_state:
    st.session_state.favorites = []

# ---------------- UI ----------------
st.title("🍲 Recipe Finder Pro")

query = st.text_input("🔍 Search recipes (e.g., pasta, indian, chicken)")

if st.button("Find Recipes"):
    with st.spinner("Fetching recipes..."):
        recipes = get_recipes_from_api(query)

        if not recipes:
            st.error("No recipes found 😢")
        else:
            cols = st.columns(2)

            for i, recipe in enumerate(recipes):
                with cols[i % 2]:
                    st.image(recipe.get("image", ""), use_container_width=True)
                    st.subheader(recipe.get("title", "No Title"))

                    summary = recipe.get("summary", "")
                    if summary:
                        st.write(summary[:150] + "...")

                    if st.button(f"❤️ Save {recipe['id']}", key=recipe["id"]):
                        st.session_state.favorites.append(recipe)
                        st.success("Saved!")

                    st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.title("⭐ Favorites")

if st.session_state.favorites:
    for fav in st.session_state.favorites:
        st.sidebar.write("•", fav["title"])
else:
    st.sidebar.write("No favorites yet")
