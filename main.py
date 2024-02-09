import requests
from bs4 import BeautifulSoup
import csv
from dotenv import load_dotenv
import os
import requests

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://letterboxd.com/fcbarcelona/list/movies-everyone-should-watch-at-least-once/detail/"

TMDB_HEADERS = {
    'Authorization': 'Bearer ' + TMDB_API_KEY,
    'accept': 'application/json'
}

all_films = []

def get_film_names(url):
    if "/detail/" not in url:
        url += "detail/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    film_details = soup.find_all("div", class_="film-detail-content")
    films = []
    for detail in film_details:
        film_name = detail.find('a').text
        film_year = detail.find('small', class_='metadata').find('a').text
        film_dict = dict(name=film_name, year=film_year)
        films.append(film_dict)
    return films

page_no = 1
while True:
    url = BASE_URL + "/page/" + str(page_no)
    film_names = get_film_names(url)
    all_films.extend(film_names)
    print(str(page_no) + " : " + str(len(film_names)))
    if len(film_names) == 0:
        break
    page_no += 1

def get_movie_info(movie_name, year):
    url = "https://api.themoviedb.org/3/search/movie"
    headers = TMDB_HEADERS
    params = {
        'include_adult': 'false',
        'language': 'en-US',
        'page': '1',
        'query': movie_name,
        'year': year
    }
    response = requests.get(url, headers=headers, params=params)
    response_json = response.json()
    results = response_json['results']
    if len(results) > 0:
        movie_id = results[0]['id']
        return movie_id
    return None

def get_movie_providers(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
    headers = TMDB_HEADERS
    response = requests.get(url, headers=headers)
    response_json = response.json()
    providers = response_json['results']
    if 'IN' in providers:
        providers_in_india = providers['IN']
        if 'flatrate' in providers_in_india:
            stream = providers_in_india['flatrate']
            provider_list = [provider['provider_name'] for provider in stream]
            return provider_list
    return []

providers_names = []

with open('movie_providers.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Film Name", "Year", "Providers"])
    for film in all_films:
        film_name = film['name']
        film_year = film['year']
        movie_id = get_movie_info(film_name, film_year)
        providers = get_movie_providers(movie_id)
        providers_names.extend(providers)
        providers_names = list(set(providers_names))
        writer.writerow([film_name, film_year, ', '.join(providers)])
        print(f"Added movie: {film_name} ({film_year})")

def filter_movies_by_provider(provider):
    parsed_provider_name = provider.replace(" ", "_")
    with open('movie_providers.csv', 'r') as input_file, open(f'movies_on_{parsed_provider_name}.csv', 'w', newline='') as output_file:
        reader = csv.reader(input_file)
        writer = csv.writer(output_file)
        writer.writerow(['Film Name', 'Year', 'Rank'])
        for i, row in enumerate(reader, start=1):
            providers = row[2].split(', ')
            if provider in providers:
                writer.writerow([row[0], row[1], i])

for provider in providers_names:
    filter_movies_by_provider(provider)
