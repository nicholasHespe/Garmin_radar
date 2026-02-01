from flask import Flask, request, jsonify
import math
import os
import sys
import threading

# Add current directory to path to import ftpscraper functions
sys.path.insert(0, '/app')

app = Flask(__name__)

# Track ongoing generation tasks to prevent duplicates
generation_locks = {}

# Australian BOM Radar Stations with coordinates
# Source: http://www.bom.gov.au/products/radar_transparencies.shtml
RADAR_STATIONS = {
    'IDR031': {'name': 'Gambier (Mount Gambier)', 'lat': -37.7476, 'lon': 140.7746},
    'IDR032': {'name': 'Bairnsdale', 'lat': -37.8871, 'lon': 147.5682},
    'IDR033': {'name': 'Morwell (Latrobe Valley)', 'lat': -38.2336, 'lon': 146.4114},
    'IDR034': {'name': 'Shepparton', 'lat': -36.3023, 'lon': 145.3886},
    'IDR038': {'name': 'Wollongong (Appin)', 'lat': -34.2629, 'lon': 150.8736},
    'IDR043': {'name': 'Mildura', 'lat': -34.2361, 'lon': 142.0861},
    'IDR044': {'name': 'Yarrawonga', 'lat': -36.0298, 'lon': 146.0396},
    'IDR063': {'name': 'Sydney (Terrey Hills)', 'lat': -33.7006, 'lon': 151.2100},
    'IDR064': {'name': 'Newcastle', 'lat': -32.7297, 'lon': 151.8331},
    'IDR065': {'name': 'Warragamba', 'lat': -33.9312, 'lon': 150.6065},
    'IDR066': {'name': 'Canberra (Captains Flat)', 'lat': -35.6614, 'lon': 149.5120},
    'IDR067': {'name': 'Wagga Wagga', 'lat': -35.1658, 'lon': 147.4594},
    'IDR068': {'name': 'Grafton', 'lat': -29.6217, 'lon': 152.9517},
    'IDR069': {'name': 'Namoi (Blackjack Mountain)', 'lat': -31.0244, 'lon': 150.1453},
    'IDR071': {'name': 'Brisbane (Marburg)', 'lat': -27.6080, 'lon': 152.5389},
    'IDR072': {'name': 'Cairns (Saddle Mountain)', 'lat': -17.1230, 'lon': 145.6808},
    'IDR073': {'name': 'Townsville (Hervey Range)', 'lat': -19.4128, 'lon': 146.5508},
    'IDR074': {'name': 'Mackay', 'lat': -21.1169, 'lon': 148.8786},
    'IDR075': {'name': 'Gladstone', 'lat': -23.8558, 'lon': 151.2622},
    'IDR076': {'name': 'Bowen', 'lat': -19.8861, 'lon': 148.0753},
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def find_nearest_radar(lat, lon):
    """Find the nearest radar station to given coordinates"""
    nearest_id = None
    nearest_distance = float('inf')

    for radar_id, info in RADAR_STATIONS.items():
        distance = haversine_distance(lat, lon, info['lat'], info['lon'])
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = radar_id

    return nearest_id, nearest_distance

@app.route('/api/location', methods=['GET'])
def receive_location():
    """Receive GPS coordinates from watch and return nearest radar station"""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))

        print(f'Received GPS coordinates: lat={lat}, lon={lon}')

        # Find nearest radar station
        radar_id, distance = find_nearest_radar(lat, lon)
        radar_info = RADAR_STATIONS[radar_id]

        print(f'Nearest radar: {radar_id} ({radar_info["name"]}) - {distance:.1f}km away')

        response = {
            'status': 'success',
            'radar_id': radar_id,
            'radar_name': radar_info['name'],
            'distance_km': round(distance, 1),
            'coordinates': {'lat': lat, 'lon': lon}
        }

        return jsonify(response), 200

    except (TypeError, ValueError) as e:
        print(f'Error parsing coordinates: {e}')
        return jsonify({'status': 'error', 'message': 'Invalid coordinates'}), 400
    except Exception as e:
        print(f'Error processing location: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check-images/<radar_id>', methods=['GET'])
def check_images(radar_id):
    """Check if images exist for a radar station"""
    try:
        # Validate radar_id
        if radar_id not in RADAR_STATIONS:
            return jsonify({'status': 'error', 'message': 'Invalid radar ID'}), 400

        # Check if all 7 images exist
        images_exist = []
        for i in range(7):
            image_path = f'/app/images/{radar_id}-{i}.png'
            images_exist.append(os.path.exists(image_path))

        all_exist = all(images_exist)

        return jsonify({
            'status': 'success',
            'radar_id': radar_id,
            'all_images_exist': all_exist,
            'images_exist': images_exist
        }), 200

    except Exception as e:
        print(f'Error checking images: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate/<radar_id>', methods=['POST'])
def generate_images(radar_id):
    """Trigger image generation for a radar station"""
    try:
        # Validate radar_id
        if radar_id not in RADAR_STATIONS:
            return jsonify({'status': 'error', 'message': 'Invalid radar ID'}), 400

        # Check if already generating
        if radar_id in generation_locks:
            return jsonify({
                'status': 'in_progress',
                'message': f'Images for {radar_id} are already being generated'
            }), 202

        # Check if images already exist
        all_exist = all(os.path.exists(f'/app/images/{radar_id}-{i}.png') for i in range(7))
        if all_exist:
            return jsonify({
                'status': 'success',
                'message': f'Images for {radar_id} already exist'
            }), 200

        # Start generation in background thread
        generation_locks[radar_id] = True

        def generate_in_background():
            try:
                # Import here to avoid module-level execution issues
                from ftpscraper import GenerateImagesForRadar
                success = GenerateImagesForRadar(radar_id, 7)
                print(f'Background generation for {radar_id}: {"success" if success else "failed"}')
            except Exception as e:
                print(f'Error in background generation for {radar_id}: {e}')
            finally:
                if radar_id in generation_locks:
                    del generation_locks[radar_id]

        thread = threading.Thread(target=generate_in_background)
        thread.daemon = True
        thread.start()

        return jsonify({
            'status': 'generating',
            'message': f'Started generating images for {radar_id}'
        }), 202

    except Exception as e:
        print(f'Error triggering generation: {e}')
        if radar_id in generation_locks:
            del generation_locks[radar_id]
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    print('Starting BetterWeather API server on port 5000...')
    app.run(host='0.0.0.0', port=5000, debug=False)
