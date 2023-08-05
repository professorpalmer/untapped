import re
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates')

# Load environment variables
app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")

# Define Google Places API endpoints
PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_BASE_URL = "https://maps.googleapis.com/maps/api/place/details/json"

@app.route("/")
def index():
    return render_template("search.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        business_type = request.form["business_type"]
        radius_miles = request.form["radius"]
        radius_meters = float(radius_miles) * 1609.34
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        location = f"{latitude},{longitude}"
        places_data = get_places_data(business_type, location, radius_meters)
        print(places_data)
        businesses = []
        for result in places_data["results"]:
            details_data = get_details_data(result["place_id"])
            print(details_data)
            website = details_data["result"].get("website", "N/A")
            email = None
            if website != "N/A":
                email = extract_email_from_website(website)
            business = {
                "name": details_data["result"]["name"],
                "address": details_data["result"]["formatted_address"],
                "phone": details_data["result"].get("formatted_phone_number", "N/A"),
                "website": website,
                "email": email if email else "N/A"
            }
            businesses.append(business)

        return render_template("results.html", businesses=businesses)
    return render_template("search.html")

def get_places_data(business_type, location, radius):
    try:
        params = {
            "key": app.config["GOOGLE_MAPS_API_KEY"],
            "keyword": business_type,
            "location": location,
            "radius": radius
        }
        response = requests.get(PLACES_BASE_URL, params=params)
        return response.json()
    except Exception as e:
        print("Error getting places data:", e)
        return None



def get_details_data(place_id):
    try:
        params = {
            "key": app.config["GOOGLE_MAPS_API_KEY"],
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website"
        }
        response = requests.get(DETAILS_BASE_URL, params=params)
        return response.json()
    except Exception as e:
        print("Error getting details data:", e)
        return None

def extract_email_from_website(url):
    try:
        session = HTMLSession()
        response = session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return email.group(0) if email else None
    except Exception as e:
        print(f"Error extracting email from {url}: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True)
