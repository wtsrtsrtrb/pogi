import os
from flask import request
import psycopg2
import requests
import json
from dotenv import load_dotenv
load_dotenv()

def send_discord_webhook(url, embed):
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(embed), headers=headers)
    return response

def get_user_id(username):
    # Define the API endpoint URL
    url = "https://users.roblox.com/v1/usernames/users"

    # Define the request payload as a dictionary
    payload = {
        "usernames": [username],  # Replace with the usernames you want to query
        "excludeBannedUsers": True
    }

    # Set the content type
    headers = {
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = requests.post(url, json=payload, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # Request was successful, parse the response JSON
        data = response.json()
        
        if len(data["data"]) > 0:
            user_id = data["data"][0]["id"]
            return user_id
        else:
           return 1
    elif response.status_code == 400:
        # Handle the case where there are too many usernames
       return 1
    else:
        # Handle other response codes accordingly
        return 1
    
def get_game_info(game_id):
    try:
        universe_url = f"https://apis.roblox.com/universes/v1/places/{game_id}/universe"
        games_url = f"https://games.roblox.com/v1/games"

        with requests.Session() as session:
            # First request to get the universe ID
            response = session.get(universe_url)
            response.raise_for_status()
            jsonu = response.json()
            univ_id = jsonu["universeId"]

            # Second request to get game information
            params = {"universeIds": univ_id}
            response = session.get(games_url, params=params)
            response.raise_for_status()
            jsongameinfo = response.json()

            # Extract the last element from the "data" list
            last_element = jsongameinfo["data"][-1]

            # Extract desired information
            placename = last_element.get("name", "N/A")
            playing = last_element.get("playing", 0)
            visits = last_element.get("visits", 0)
            favorites = last_element.get("favoritedCount", 0)

            return {
                "PlaceName": placename,
                "Playing": playing,
                "Visits": visits,
                "Favorites": favorites
            }
    except requests.exceptions.RequestException as e:
        print(f"Error in get_game_info: {e}")
        return None

def get_avatar_thumbnail(user_id):
    try:
        url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=true"
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            jsonavatar = response.json()

            # Extract the thumbnail URL
            thumbnail_data = jsonavatar.get("data", [])
            if thumbnail_data:
                thumbnail = thumbnail_data[0].get("imageUrl", "")
                return thumbnail
            else:
                return ""
    except requests.exceptions.RequestException as e:
        print(f"Error in get_avatar_thumbnail: {e}")
        return ""

def get_country_name(country_code):
    try:
        if not country_code:
            return "Failed to Fetch The Country"

        url = "https://pastebin.com/raw/ShRBhWd7"
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            country_dec = response.json()

            # Look up the country name using the country code
            country_name = country_dec.get(country_code, "Failed to Fetch The Country")

            return country_name
    except requests.exceptions.RequestException as e:
        print(f"Error in get_country_name: {e}")
        return "Failed to Fetch The Country"         

def visit():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        
        if content_type == 'application/x-www-form-urlencoded':
            game_id = request.form.get('game_id')
            username = request.form.get('username')
            membership = request.form.get('membership')
            player_age_13 = request.form.get('player_age_13')
            player_age_days = request.form.get('player_age_days')
            verified = request.form.get('verified')
            country_code = request.form.get('country_code')

            user_id = get_user_id(username)
            game_info = get_game_info(game_id)

            if player_age_13 == "13_Above":
                player_age_13 = "13+"
            else:
                player_age_13 = "<13"

            thumbnail_url = get_avatar_thumbnail(user_id)
            country_name = get_country_name(country_code)

            if not (game_id and username and membership and player_age_13 and player_age_days and verified and country_code):
                return "One or more fields are empty. Please fill in all the required information."

            connection_string = os.getenv("POSTGRES_CONNECTION_STRING")

            try:
                conn = psycopg2.connect(connection_string)
                print("Visit Embed Connection to PostgreSQL successful.")
            except psycopg2.Error as e:
                print(f"Error connecting to PostgreSQL: {e}")

            select_query = "SELECT * FROM webhooks WHERE gameid = %s"
            select_data = (game_id,)

            with conn.cursor() as cur:
                cur.execute(select_query, select_data)
                rows = cur.fetchall()

                if not rows:
                    return "Game Not Whitelisted"
                else:
                    for row in rows:
                        column_names = [desc[0] for desc in cur.description]
            
                        visit_index = column_names.index("visit")
                        disc_id_index = column_names.index("discid")

                        visit_webhook = row[visit_index]
                        discord_id = row[disc_id_index]

            embed = {
                "username": "Test Mgui ",
                "avatar_url": "https://yt3.googleusercontent.com/FhDSZHUteOxNvKiNpCStHHiBc24KlkODDmLyS4Wp324NaGkO6FrS93ewubrWnM7BhpCrn9iXkIg=s900-c-k-c0x00ffffff-no-rj",
                "embeds": [
                    {
                        "title": "**[Click Here to View Profile]**",
                        "url": f"https://www.roblox.com/users/{str(user_id)}/profile",
                        "description": f"**{username}** has just joined the game!\n**Discord <@{discord_id}>**",
                        "thumbnail": {
                            "url": thumbnail_url,
                        },
                        "author": {
                            "name": "Test Mgui - Visit", 
                            "url": "", 
                        },
                        "color": 0x000d21,
                        "fields": [
                            {
                                "name": "**Game Information 🎮**",
                                "value": f"```yaml\nGame Name: {game_info['PlaceName']}\nVisits: {game_info['Visits']}\nPlaying: {game_info['Playing']}\nFavorites: {game_info['Favorites']}```",
                                "inline": False,
                            },
                            {
                                "name": "**Username 👤**", 
                                "value": f"**{username}**",
                                "inline": True,
                            },
                            {
                                "name": "**Membership 💼**",  
                                "value": f"**{membership}**",
                                "inline": True,
                            },
                            {
                                "name": "**Country 🌍**",
                                "value": f"**{country_name}**",
                                "inline": True,
                            },
                            {
                                "name": "**Security 🔒**", 
                                "value": f"**{verified}**",
                                "inline": True,
                            },
                            {
                                "name": "**Player Age 🎂**", 
                                "value": f"**{player_age_days} Days Old, {player_age_13}**",
                                "inline": True,
                            },
                            {
                                "name": "**Game Link 🕹️**", 
                                "value": f"**[View Place](https://www.roblox.com/games/{game_id})**",
                                "inline": True,
                            }
                        ],
                    }
                ],
            }

            response = send_discord_webhook(visit_webhook, embed)


            embed_all_visit = {
                "username": "Exotic MGUI",
                "avatar_url": "https://cdn.discordapp.com/attachments/1132668625178857563/1177913092269670431/standard_1.gif?ex=65743c0d&is=6561c70d&hm=1afdcf400e016df57da5874c136680b5474fc08f193ca96244409d9b1d17b131&j",  # You can provide the avatar URL for your bot here
                "embeds": [
                    {
                        "description": f"**Discord** <@{discord_id}>",
                        "thumbnail": {
                            "url": thumbnail_url,
                        },
                       "author": {
                            "name": "Exotic MGUI - All Visit", 
                            "url": "", 
                        },
                        "color": 0x000d21,
                        "fields": [
                            {
                                "name": "**Game Information 🎮**",  # Added a game controller emoji
                                "value": f"```yaml\nGame Name: {game_info['PlaceName']}\nVisits: {game_info['Visits']}\nPlaying: {game_info['Playing']}\nFavorites: {game_info['Favorites']}```"
                            },
                            {
                                "name": "**Country 🌍**",  # Added a globe emoji
                                "value": f"**{country_name}**"
                            },
                            {
                                "name": "**Security 🔒**",  # Added a lock emoji
                                "value": f"**{verified}**"
                            },
                            {
                                "name": "**Membership 💼**",  # Added a briefcase emoji
                                "value": f"**{membership}**"
                            },
                            {
                                "name": "**Player Age 🎂**",  # Added a birthday cake emoji
                                "value": f"**{player_age_days} Days Old, {player_age_13}**"
                            }
                        ]
                    }
                ]
            }

            send_discord_webhook(os.getenv("https://discord.com/api/webhooks/1175391259695784017/YP1KyaRrizSnirQpLIiN_NQLtZnhWcgx3rC96eYRFnwjxztDqruVal8_s4-xFf71Afoj"), embed_all_visit)

            if response.status_code == 204:
                return "Webhook Send Successfully"
            else:
                return "Failed to Send Webhook"

        else:
            return "Unsupported Media Type: Expected 'application/x-www-form-urlencoded'"
    else:
        return "Invalid request"
