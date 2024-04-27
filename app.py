from flask import Flask, render_template, request, jsonify
from pyproj import Proj, transform
import requests, re
from os import environ

app = Flask(__name__)
def verify_single_domain(link):
    pattern = r'^https?://([^/?]+)\.([^/?]+)(?:/|\?|$)'
    match = re.search(pattern, link)
    if match:
        return True
    else:
        raise ValueError("Link contains multiple domains")   

def decode_shorten_link(short_url: str):
    try:
        response = requests.get(short_url, allow_redirects=True)
        resolved_url = response.history[0].headers['Location']
        return resolved_url
    except requests.RequestException as e:
        return None 
    
def retrieve_coordinates_for_address(address: str):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key=<API_KEY>'
    try:
        response = requests.get(url)
        if('error_message' in response.json()):
            raise ValueError(response.json()['error_message'])
        
        results = response.json()['results']
        if(not len(results)):
            raise ValueError(f'Location is empty for address {address}')
        
        location_dict = results[0]['geometry']['location']
        if(not location_dict):
            raise ValueError(f'Location is empty for address {address}')
        
        return location_dict['lat'], location_dict['lng']
    except requests.RequestException as e:
        raise ValueError(e.response)

def extract_from_search_string(link: str):
    lat_start_index = link.find('/search/') + len('/search/')
    lon_start_index = link.find(',', lat_start_index) + 1
    lon_end_index = link.find('?', lon_start_index)
    latitude = float(link[lat_start_index:lon_start_index - 1])
    longitude = float(link[lon_start_index:lon_end_index])
    return latitude, longitude

def extract_from_place_string(link: str):
    start_index = link.find('@')
    comma_index = link.find(',', start_index)
    second_comma_index = link.find(',', comma_index + 1)
    latitude = float(link[start_index + 1:comma_index])
    longitude = float(link[comma_index + 1:second_comma_index])
    return latitude, longitude

def get_wgs83_coordinates(link: str):
    if(link.startswith('https://maps.app.goo.gl/')):
        link = decode_shorten_link(link)

    patternAddress = r'^https://(?:www\.)?maps\.google\.(?:[a-z]{2,3})(?:\.[a-z]{2})?\?(?:[^&]*&)?q=([^&]+)'
    searchAddressLink = re.search(patternAddress, link)
    if(searchAddressLink):
        if(searchAddressLink.group(1)):
            return retrieve_coordinates_for_address(searchAddressLink.group(1))
        else:
            raise ValueError(f'Link contains wrong encoding {link}')
        
    patternAddressWithPlace = r'^https://(?:www\.)?google\.(?:[a-z]{2,3})(?:\.[a-z]{2})?/maps/place/(?!.*@)([^/@]+)'
    searchAddressLink = re.search(patternAddressWithPlace, link)
    if(searchAddressLink):
        if(searchAddressLink.group(1)):
            return retrieve_coordinates_for_address(searchAddressLink.group(1))
        else:
            raise ValueError(f'Link contains wrong encoding {link}') 

    print(f'Decoded link {link}')

    patternSearch = r'^https://www\.google\.[a-z]{2,3}(\.[a-z]{2})?/maps/search/'
    patternPlace = r'^https://www\.google\.[a-z]{2,3}(\.[a-z]{2})?/maps/place/'
    if(not re.match(patternPlace, link) and not re.match(patternSearch, link)):
        raise ValueError("Not a google maps link") 
    
    try:
        if(re.match(patternSearch, link)):
            return extract_from_search_string(link)
        
        if(re.match(patternPlace, link)):
            return extract_from_place_string(link)
        
    except ValueError:
        raise ValueError(f"Cannot parse string {link}")
    
def select_projection(lon):
    utm_zone = int((lon + 180) / 6) + 1
    if(utm_zone >= 34 and utm_zone < 38):
        return 5528 + utm_zone
    raise ValueError("UTM Zone not supported for UCS-2000 conversion.")


def convert_coordinates(longitude, latitude, from_epsg, to_epsg):    
    in_proj = Proj(init=f'epsg:{from_epsg}')
    out_proj = Proj(init=f'epsg:{to_epsg}')
    x, y = transform(in_proj, out_proj, longitude, latitude)
    return x, y

@app.route('/map')
def indexMap():
    return render_template('indexMap.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(ValueError)
def handle_value_error(error):
    error_message = {'error': str(error)}
    return jsonify(error_message), 400

@app.route('/convert_coordinates', methods=['GET'])
def convert_coordinates_endpoint():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))

    from_epsg = 4326
    to_epsg = select_projection(longitude)
    converted_longitude, converted_latitude = convert_coordinates(longitude, latitude, from_epsg, to_epsg)
    
    return jsonify({
        'converted_x': int(converted_longitude),
        'converted_y': int(converted_latitude)
    })

@app.route('/extract_coordinates', methods=['GET'])
def extract_coordinates_endpoint():
    link = request.args.get('link')
    print(link)
    verify_single_domain(link)

    lat,lon = get_wgs83_coordinates(link)
    
    from_epsg = 4326
    to_epsg = select_projection(lon)
    converted_longitude, converted_latitude = convert_coordinates(lon, lat, from_epsg, to_epsg)
    
    return jsonify({
        'converted_x': int(converted_longitude),
        'converted_y': int(converted_latitude)
    })

port = int(environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)