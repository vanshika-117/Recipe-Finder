import streamlit as st
import requests
import mysql.connector
import json
import os

# ---------------- DB CONNECTION ----------------
def get_db():
    return mysql.connector.connect(
       host=st.secrets["MYSQLHOST"],
       port=int(st.secrets["MYSQLPORT"]),
       user=st.secrets["MYSQLUSER"],
       password=st.secrets["MYSQLPASSWORD"],
       database=st.secrets["MYSQLDATABASE"]
    )

# ---------------- SAVE TO DB ----------------
def save_recipe(recipe):
    conn = get_db()
    cursor = conn.cursor()

    query = """
    INSERT IGNORE INTO recipes (id, title, cuisine, image, ingredients, instructions, source, youtube)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(query, (
        recipe["id"],
        recipe["title"],
        recipe["cuisine"],
        recipe["image"],
        json.dumps(recipe["ingredients"]),
        json.dumps(recipe["instructions"]),
        recipe["source"],
        recipe["youtube"]
    ))

    conn.commit()
    cursor.close()
    conn.close()

# ---------------- GET FROM DB ----------------
def get_recipes_from_db(cuisine):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM recipes WHERE cuisine=%s LIMIT 20", (cuisine,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    recipes = []
    for r in rows:
        recipes.append({
            "id": r["id"],
            "title": r["title"],
            "image": r["image"],
            "ingredients": json.loads(r["ingredients"]),
            "instructions": json.loads(r["instructions"]),
            "source": r["source"],
            "youtube": r["youtube"]
        })

    return recipes

# ---------------- FETCH FROM API ----------------
def fetch_from_api(cuisine):
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={cuisine}"
        data = requests.get(url).json()

        meals = data.get("meals", [])
        recipes = []

        for meal in meals[:10]:
            detail_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal['idMeal']}"
            detail = requests.get(detail_url).json()["meals"][0]

            ingredients = []
            for i in range(1, 21):
                ing = detail.get(f"strIngredient{i}")
                measure = detail.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{measure} {ing}".strip())

            instructions = detail.get("strInstructions", "").split(". ")

            recipe = {
                "id": meal["idMeal"],
                "title": meal["strMeal"],
                "image": meal["strMealThumb"],
                "cuisine": cuisine,
                "ingredients": ingredients,
                "instructions": instructions,
                "source": detail.get("strSource"),
                "youtube": detail.get("strYoutube")
            }

            save_recipe(recipe)  # save in DB
            recipes.append(recipe)

        return recipes

    except Exception as e:
        return []

# ---------------- MAIN SEARCH FUNCTION ----------------
def get_recipes(cuisine):
    # 1️⃣ Try DB first
    db_data = get_recipes_from_db(cuisine)

    if db_data:
        return db_data

    # 2️⃣ If DB empty → call API
    return fetch_from_api(cuisine)

# ---------------- UI ----------------
st.title("🍴 Recipe Finder (DB Powered)")

cuisine = st.selectbox("Select Cuisine", [
    "Indian", "Italian", "Chinese", "Mexican", "American","Korean","Thai","French","Japanese"
])

if st.button("Find Recipes"):
    with st.spinner("Loading..."):
        recipes = get_recipes(cuisine)

        if not recipes:
            st.error("No recipes found")
        else:
            for r in recipes:
                st.subheader(r["title"])
                st.image(r["image"])

                with st.expander("Ingredients"):
                    for ing in r["ingredients"]:
                        st.write(f"• {ing}")

                with st.expander("Instructions"):
                    for i, step in enumerate(r["instructions"], 1):
                        if step.strip():
                            st.write(f"Step {i}: {step}")

                if r.get("youtube"):
                    st.video(r["youtube"])

                if r.get("source"):
                    st.markdown(f"[View Full Recipe]({r['source']})")

                st.divider()
