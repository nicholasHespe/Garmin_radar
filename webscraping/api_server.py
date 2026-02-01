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
    'IDR011': {'name': 'Broadmeadows', 'lat': -37.691, 'lon': 144.946, 'scale': 2833.33},
    'IDR012': {'name': 'Broadmeadows', 'lat': -37.691, 'lon': 144.946, 'scale': 1416.67},
    'IDR013': {'name': 'Broadmeadows', 'lat': -37.691, 'lon': 144.946, 'scale': 708.33},
    'IDR014': {'name': 'Broadmeadows', 'lat': -37.691, 'lon': 144.946, 'scale': 354.17},
    'IDR021': {'name': 'Melbourne', 'lat': -37.852, 'lon': 144.752, 'scale': 2833.33},
    'IDR022': {'name': 'Melbourne', 'lat': -37.852, 'lon': 144.752, 'scale': 1416.67},
    'IDR023': {'name': 'Melbourne', 'lat': -37.852, 'lon': 144.752, 'scale': 708.33},
    'IDR024': {'name': 'Melbourne', 'lat': -37.852, 'lon': 144.752, 'scale': 354.17},
    'IDR031': {'name': 'Wollongong', 'lat': -34.2639, 'lon': 150.8739, 'scale': 2833.33},
    'IDR032': {'name': 'Wollongong', 'lat': -34.2639, 'lon': 150.8739, 'scale': 1416.67},
    'IDR033': {'name': 'Wollongong', 'lat': -34.2639, 'lon': 150.8739, 'scale': 708.33},
    'IDR034': {'name': 'Wollongong', 'lat': -34.2639, 'lon': 150.8739, 'scale': 354.17},
    'IDR041': {'name': 'Newcastle', 'lat': -32.7317, 'lon': 152.02499, 'scale': 2833.33},
    'IDR042': {'name': 'Newcastle', 'lat': -32.7317, 'lon': 152.02499, 'scale': 1416.67},
    'IDR043': {'name': 'Newcastle', 'lat': -32.7317, 'lon': 152.02499, 'scale': 708.33},
    'IDR044': {'name': 'Newcastle', 'lat': -32.7317, 'lon': 152.02499, 'scale': 354.17},
    'IDR061': {'name': 'Geraldton', 'lat': -28.8, 'lon': 114.7, 'scale': 2833.33},
    'IDR062': {'name': 'Geraldton', 'lat': -28.8, 'lon': 114.7, 'scale': 1416.67},
    'IDR063': {'name': 'Geraldton', 'lat': -28.8, 'lon': 114.7, 'scale': 708.33},
    'IDR064': {'name': 'Geraldton', 'lat': -28.8, 'lon': 114.7, 'scale': 354.17},
    'IDR071': {'name': 'Wyndham', 'lat': -15.453, 'lon': 128.119, 'scale': 2833.33},
    'IDR072': {'name': 'Wyndham', 'lat': -15.453, 'lon': 128.119, 'scale': 1416.67},
    'IDR073': {'name': 'Wyndham', 'lat': -15.453, 'lon': 128.119, 'scale': 708.33},
    'IDR081': {'name': 'Gympie', 'lat': -25.967, 'lon': 152.58299, 'scale': 2833.33},
    'IDR082': {'name': 'Gympie', 'lat': -25.967, 'lon': 152.58299, 'scale': 1416.67},
    'IDR083': {'name': 'Gympie', 'lat': -25.967, 'lon': 152.58299, 'scale': 708.33},
    'IDR084': {'name': 'Gympie', 'lat': -25.967, 'lon': 152.58299, 'scale': 354.17},
    'IDR101': {'name': 'Darwin Ap', 'lat': -12.425, 'lon': 130.89101, 'scale': 2833.33},
    'IDR102': {'name': 'Darwin Ap', 'lat': -12.425, 'lon': 130.89101, 'scale': 1416.67},
    'IDR103': {'name': 'Darwin Ap', 'lat': -12.425, 'lon': 130.89101, 'scale': 708.33},
    'IDR104': {'name': 'Darwin Ap', 'lat': -12.425, 'lon': 130.89101, 'scale': 354.17},
    'IDR1061': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 2833.33},
    'IDR1062': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 1416.67},
    'IDR1063': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 708.33},
    'IDR1064': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.5511, 'scale': 354.17},
    'IDR1071': {'name': 'Richmond', 'lat': -20.75178, 'lon': 143.14145, 'scale': 2833.33},
    'IDR1072': {'name': 'Richmond', 'lat': -20.75178, 'lon': 143.14145, 'scale': 1416.67},
    'IDR1073': {'name': 'Richmond', 'lat': -20.75178, 'lon': 143.14145, 'scale': 708.33},
    'IDR1074': {'name': 'Richmond', 'lat': -20.75178, 'lon': 143.14145, 'scale': 354.17},
    'IDR1081': {'name': 'Toowoomba', 'lat': -27.2743, 'lon': 151.9924, 'scale': 2833.33},
    'IDR1082': {'name': 'Toowoomba', 'lat': -27.2743, 'lon': 151.9924, 'scale': 1416.67},
    'IDR1083': {'name': 'Toowoomba', 'lat': -27.2743, 'lon': 151.9924, 'scale': 708.33},
    'IDR1084': {'name': 'Toowoomba', 'lat': -27.2743, 'lon': 151.9924, 'scale': 354.17},
    'IDR111': {'name': 'Adelaide Ap', 'lat': -34.95, 'lon': 138.533, 'scale': 2833.33},
    'IDR1111': {'name': 'Karratha', 'lat': -20.9924, 'lon': 116.8758, 'scale': 2833.33},
    'IDR1112': {'name': 'Karratha', 'lat': -20.9924, 'lon': 116.8758, 'scale': 1416.67},
    'IDR1113': {'name': 'Karratha', 'lat': -20.9924, 'lon': 116.8758, 'scale': 708.33},
    'IDR1114': {'name': 'Karratha', 'lat': -20.9924, 'lon': 116.8758, 'scale': 354.17},
    'IDR112': {'name': 'Adelaide Ap', 'lat': -34.95, 'lon': 138.533, 'scale': 1416.67},
    'IDR1121': {'name': 'Gove Ap', 'lat': -12.26898, 'lon': 136.82043, 'scale': 2833.33},
    'IDR1122': {'name': 'Gove Ap', 'lat': -12.26898, 'lon': 136.82043, 'scale': 1416.67},
    'IDR1123': {'name': 'Gove Ap', 'lat': -12.26898, 'lon': 136.82043, 'scale': 708.33},
    'IDR1124': {'name': 'Gove Ap', 'lat': -12.26898, 'lon': 136.82043, 'scale': 354.17},
    'IDR113': {'name': 'Adelaide Ap', 'lat': -34.95, 'lon': 138.533, 'scale': 708.33},
    'IDR114': {'name': 'Adelaide Ap', 'lat': -34.95, 'lon': 138.533, 'scale': 354.17},
    'IDR1141': {'name': 'Carnarvon', 'lat': -24.883, 'lon': 113.667, 'scale': 2833.33},
    'IDR1142': {'name': 'Carnarvon', 'lat': -24.883, 'lon': 113.667, 'scale': 1416.67},
    'IDR1143': {'name': 'Carnarvon', 'lat': -24.883, 'lon': 113.667, 'scale': 708.33},
    'IDR1144': {'name': 'Carnarvon', 'lat': -24.8883, 'lon': 113.66938, 'scale': 354.17},
    'IDR131': {'name': 'Sydney Ap', 'lat': -33.941, 'lon': 151.175, 'scale': 2833.33},
    'IDR132': {'name': 'Sydney Ap', 'lat': -33.941, 'lon': 151.175, 'scale': 1416.67},
    'IDR133': {'name': 'Sydney Ap', 'lat': -33.941, 'lon': 151.175, 'scale': 708.33},
    'IDR141': {'name': 'Mt Gambier', 'lat': -37.75, 'lon': 140.78, 'scale': 2833.33},
    'IDR142': {'name': 'Mt Gambier', 'lat': -37.75, 'lon': 140.78, 'scale': 1416.67},
    'IDR143': {'name': 'Mt Gambier', 'lat': -37.75, 'lon': 140.78, 'scale': 708.33},
    'IDR151': {'name': 'Dampier', 'lat': -20.65, 'lon': 116.687, 'scale': 2833.33},
    'IDR152': {'name': 'Dampier', 'lat': -20.65, 'lon': 116.687, 'scale': 1416.67},
    'IDR153': {'name': 'Dampier', 'lat': -20.65, 'lon': 116.687, 'scale': 708.33},
    'IDR154': {'name': 'Dampier', 'lat': -20.65, 'lon': 116.687, 'scale': 354.17},
    'IDR161': {'name': 'Port Hedland', 'lat': -20.3719, 'lon': 118.6317, 'scale': 2833.33},
    'IDR162': {'name': 'Port Hedland', 'lat': -20.3719, 'lon': 118.6317, 'scale': 1416.67},
    'IDR163': {'name': 'Port Hedland', 'lat': -20.3719, 'lon': 118.6317, 'scale': 708.33},
    'IDR171': {'name': 'Broome', 'lat': -17.945, 'lon': 122.225, 'scale': 2833.33},
    'IDR172': {'name': 'Broome', 'lat': -17.945, 'lon': 122.225, 'scale': 1416.67},
    'IDR173': {'name': 'Broome', 'lat': -17.945, 'lon': 122.225, 'scale': 708.33},
    'IDR174': {'name': 'Broome', 'lat': -17.945, 'lon': 122.225, 'scale': 354.17},
    'IDR191': {'name': 'Cairns', 'lat': -16.817, 'lon': 145.683, 'scale': 2833.33},
    'IDR192': {'name': 'Cairns', 'lat': -16.817, 'lon': 145.683, 'scale': 1416.67},
    'IDR193': {'name': 'Cairns', 'lat': -16.817, 'lon': 145.683, 'scale': 708.33},
    'IDR194': {'name': 'Cairns', 'lat': -16.817, 'lon': 145.683, 'scale': 354.17},
    'IDR221': {'name': 'Mackay', 'lat': -21.117, 'lon': 149.217, 'scale': 2833.33},
    'IDR222': {'name': 'Mackay', 'lat': -21.117, 'lon': 149.217, 'scale': 1416.67},
    'IDR223': {'name': 'Mackay', 'lat': -21.117, 'lon': 149.217, 'scale': 708.33},
    'IDR224': {'name': 'Mackay', 'lat': -21.1172, 'lon': 149.2169, 'scale': 354.17},
    'IDR231': {'name': 'Gladstone', 'lat': -23.85, 'lon': 151.267, 'scale': 2833.33},
    'IDR232': {'name': 'Gladstone', 'lat': -23.85, 'lon': 151.267, 'scale': 1416.67},
    'IDR233': {'name': 'Gladstone', 'lat': -23.85, 'lon': 151.267, 'scale': 708.33},
    'IDR241': {'name': 'Bowen', 'lat': -19.886, 'lon': 148.075, 'scale': 2833.33},
    'IDR242': {'name': 'Bowen', 'lat': -19.886, 'lon': 148.075, 'scale': 1416.67},
    'IDR243': {'name': 'Bowen', 'lat': -19.886, 'lon': 148.075, 'scale': 708.33},
    'IDR251': {'name': 'Alice Springs', 'lat': -23.817, 'lon': 133.89999, 'scale': 2833.33},
    'IDR252': {'name': 'Alice Springs', 'lat': -23.817, 'lon': 133.89999, 'scale': 1416.67},
    'IDR253': {'name': 'Alice Springs', 'lat': -23.817, 'lon': 133.89999, 'scale': 708.33},
    'IDR261': {'name': 'Perth Ap', 'lat': -31.933, 'lon': 115.967, 'scale': 2833.33},
    'IDR262': {'name': 'Perth Ap', 'lat': -31.933, 'lon': 115.967, 'scale': 1416.67},
    'IDR263': {'name': 'Perth Ap', 'lat': -31.933, 'lon': 115.967, 'scale': 708.33},
    'IDR264': {'name': 'Perth Ap', 'lat': -31.933, 'lon': 115.967, 'scale': 354.17},
    'IDR271': {'name': 'Woomera', 'lat': -31.157, 'lon': 136.80299, 'scale': 2833.33},
    'IDR272': {'name': 'Woomera', 'lat': -31.157, 'lon': 136.80299, 'scale': 1416.67},
    'IDR273': {'name': 'Woomera', 'lat': -31.157, 'lon': 136.80299, 'scale': 708.33},
    'IDR281': {'name': 'Grafton', 'lat': -29.622, 'lon': 152.951, 'scale': 2833.33},
    'IDR282': {'name': 'Grafton', 'lat': -29.622, 'lon': 152.951, 'scale': 1416.67},
    'IDR283': {'name': 'Grafton', 'lat': -29.622, 'lon': 152.951, 'scale': 708.33},
    'IDR291': {'name': 'Learmonth', 'lat': -22.104, 'lon': 113.998, 'scale': 2833.33},
    'IDR292': {'name': 'Learmonth', 'lat': -22.104, 'lon': 113.998, 'scale': 1416.67},
    'IDR293': {'name': 'Learmonth', 'lat': -22.104, 'lon': 113.998, 'scale': 708.33},
    'IDR311': {'name': 'Albany', 'lat': -34.95, 'lon': 117.8, 'scale': 2833.33},
    'IDR312': {'name': 'Albany', 'lat': -34.95, 'lon': 117.8, 'scale': 1416.67},
    'IDR313': {'name': 'Albany', 'lat': -34.95, 'lon': 117.8, 'scale': 708.33},
    'IDR314': {'name': 'Albany', 'lat': -34.95, 'lon': 117.8, 'scale': 354.17},
    'IDR321': {'name': 'Esperance', 'lat': -33.83, 'lon': 121.892, 'scale': 2833.33},
    'IDR322': {'name': 'Esperance', 'lat': -33.83, 'lon': 121.892, 'scale': 1416.67},
    'IDR323': {'name': 'Esperance', 'lat': -33.83, 'lon': 121.892, 'scale': 708.33},
    'IDR324': {'name': 'Esperance', 'lat': -33.83, 'lon': 121.892, 'scale': 354.17},
    'IDR331': {'name': 'Ceduna', 'lat': -32.131, 'lon': 133.69501, 'scale': 2833.33},
    'IDR332': {'name': 'Ceduna', 'lat': -32.131, 'lon': 133.69501, 'scale': 1416.67},
    'IDR333': {'name': 'Ceduna', 'lat': -32.131, 'lon': 133.69501, 'scale': 708.33},
    'IDR334': {'name': 'Ceduna', 'lat': -32.131, 'lon': 133.69501, 'scale': 354.17},
    'IDR361': {'name': 'Mornington Is', 'lat': -16.666, 'lon': 139.16701, 'scale': 2833.33},
    'IDR362': {'name': 'Mornington Is', 'lat': -16.666, 'lon': 139.16701, 'scale': 1416.67},
    'IDR363': {'name': 'Mornington Is', 'lat': -16.666, 'lon': 139.16701, 'scale': 708.33},
    'IDR371': {'name': 'Hobart', 'lat': -42.833, 'lon': 147.50999, 'scale': 2833.33},
    'IDR372': {'name': 'Hobart', 'lat': -42.833, 'lon': 147.50999, 'scale': 1416.67},
    'IDR373': {'name': 'Hobart', 'lat': -42.833, 'lon': 147.50999, 'scale': 708.33},
    'IDR381': {'name': 'Newdegate', 'lat': -33.097, 'lon': 119.0087, 'scale': 2833.33},
    'IDR382': {'name': 'Newdegate', 'lat': -33.097, 'lon': 119.0087, 'scale': 1416.67},
    'IDR383': {'name': 'Newdegate', 'lat': -33.097, 'lon': 119.0087, 'scale': 708.33},
    'IDR384': {'name': 'Newdegate', 'lat': -33.097, 'lon': 119.0087, 'scale': 354.17},
    'IDR391': {'name': 'Halls Creek', 'lat': -18.231, 'lon': 127.663, 'scale': 2833.33},
    'IDR392': {'name': 'Halls Creek', 'lat': -18.231, 'lon': 127.663, 'scale': 1416.67},
    'IDR393': {'name': 'Halls Creek', 'lat': -18.231, 'lon': 127.663, 'scale': 708.33},
    'IDR394': {'name': 'Halls Creek', 'lat': -18.231, 'lon': 127.663, 'scale': 354.17},
    'IDR401': {'name': 'Canberra', 'lat': -35.6628, 'lon': 149.5108, 'scale': 2833.33},
    'IDR402': {'name': 'Canberra', 'lat': -35.6628, 'lon': 149.5108, 'scale': 1416.67},
    'IDR403': {'name': 'Canberra', 'lat': -35.6628, 'lon': 149.5108, 'scale': 708.33},
    'IDR404': {'name': 'Canberra', 'lat': -35.6628, 'lon': 149.5108, 'scale': 354.17},
    'IDR411': {'name': 'Willis Is', 'lat': -16.3, 'lon': 149.983, 'scale': 2833.33},
    'IDR412': {'name': 'Willis Is', 'lat': -16.3, 'lon': 149.983, 'scale': 1416.67},
    'IDR413': {'name': 'Willis Is', 'lat': -16.3, 'lon': 149.983, 'scale': 708.33},
    'IDR421': {'name': 'Katherine', 'lat': -14.513, 'lon': 132.446, 'scale': 2833.33},
    'IDR422': {'name': 'Katherine', 'lat': -14.513, 'lon': 132.446, 'scale': 1416.67},
    'IDR423': {'name': 'Katherine', 'lat': -14.513, 'lon': 132.446, 'scale': 708.33},
    'IDR424': {'name': 'Katherine', 'lat': -14.513, 'lon': 132.446, 'scale': 354.17},
    'IDR431': {'name': 'Brisbane Ap', 'lat': -27.392, 'lon': 153.13, 'scale': 2833.33},
    'IDR432': {'name': 'Brisbane Ap', 'lat': -27.392, 'lon': 153.13, 'scale': 1416.67},
    'IDR433': {'name': 'Brisbane Ap', 'lat': -27.392, 'lon': 153.13, 'scale': 708.33},
    'IDR434': {'name': 'Brisbane Ap', 'lat': -27.392, 'lon': 153.13, 'scale': 354.17},
    'IDR441': {'name': 'Giles', 'lat': -25.03, 'lon': 128.3, 'scale': 2833.33},
    'IDR442': {'name': 'Giles', 'lat': -25.03, 'lon': 128.3, 'scale': 1416.67},
    'IDR443': {'name': 'Giles', 'lat': -25.03, 'lon': 128.3, 'scale': 708.33},
    'IDR461': {'name': 'Sellicks Hill', 'lat': -35.33, 'lon': 138.5, 'scale': 2833.33},
    'IDR462': {'name': 'Sellicks Hill', 'lat': -35.33, 'lon': 138.5, 'scale': 1416.67},
    'IDR463': {'name': 'Sellicks Hill', 'lat': -35.33, 'lon': 138.5, 'scale': 708.33},
    'IDR481': {'name': 'Kalgoorlie', 'lat': -30.7834, 'lon': 121.4549, 'scale': 2833.33},
    'IDR482': {'name': 'Kalgoorlie', 'lat': -30.785, 'lon': 121.452, 'scale': 1416.67},
    'IDR483': {'name': 'Kalgoorlie', 'lat': -30.785, 'lon': 121.452, 'scale': 708.33},
    'IDR484': {'name': 'Kalgoorlie', 'lat': -30.7834, 'lon': 121.4549, 'scale': 354.17},
    'IDR491': {'name': 'Yarrawonga', 'lat': -36.03, 'lon': 146.02299, 'scale': 2833.33},
    'IDR492': {'name': 'Yarrawonga', 'lat': -36.03, 'lon': 146.02299, 'scale': 1416.67},
    'IDR493': {'name': 'Yarrawonga', 'lat': -36.03, 'lon': 146.02299, 'scale': 708.33},
    'IDR494': {'name': 'Yarrawonga', 'lat': -36.03, 'lon': 146.02299, 'scale': 354.17},
    'IDR501': {'name': 'Marburg', 'lat': -27.608, 'lon': 152.539, 'scale': 2833.33},
    'IDR502': {'name': 'Marburg', 'lat': -27.608, 'lon': 152.539, 'scale': 1416.67},
    'IDR503': {'name': 'Marburg', 'lat': -27.608, 'lon': 152.539, 'scale': 708.33},
    'IDR504': {'name': 'Marburg', 'lat': -27.6063, 'lon': 152.5401, 'scale': 354.17},
    'IDR511': {'name': 'Melbourne Ap', 'lat': -37.667, 'lon': 144.83, 'scale': 2833.33},
    'IDR512': {'name': 'Melbourne Ap', 'lat': -37.667, 'lon': 144.83, 'scale': 1416.67},
    'IDR513': {'name': 'Melbourne Ap', 'lat': -37.667, 'lon': 144.83, 'scale': 708.33},
    'IDR514': {'name': 'Melbourne Ap', 'lat': -37.667, 'lon': 144.83, 'scale': 354.17},
    'IDR521': {'name': 'NW Tasmania', 'lat': -41.181, 'lon': 145.57899, 'scale': 2833.33},
    'IDR522': {'name': 'NW Tasmania', 'lat': -41.181, 'lon': 145.57899, 'scale': 1416.67},
    'IDR523': {'name': 'NW Tasmania', 'lat': -41.181, 'lon': 145.57899, 'scale': 708.33},
    'IDR524': {'name': 'NW Tasmania', 'lat': -41.181, 'lon': 145.57899, 'scale': 354.17},
    'IDR531': {'name': 'Moree', 'lat': -29.5, 'lon': 149.85001, 'scale': 2833.33},
    'IDR532': {'name': 'Moree', 'lat': -29.5, 'lon': 149.85001, 'scale': 1416.67},
    'IDR533': {'name': 'Moree', 'lat': -29.5, 'lon': 149.85001, 'scale': 708.33},
    'IDR551': {'name': 'Wagga Wagga', 'lat': -35.167, 'lon': 147.467, 'scale': 2833.33},
    'IDR552': {'name': 'Wagga Wagga', 'lat': -35.167, 'lon': 147.467, 'scale': 1416.67},
    'IDR553': {'name': 'Wagga Wagga', 'lat': -35.167, 'lon': 147.467, 'scale': 708.33},
    'IDR561': {'name': 'Longreach', 'lat': -23.43, 'lon': 144.28999, 'scale': 2833.33},
    'IDR562': {'name': 'Longreach', 'lat': -23.43, 'lon': 144.28999, 'scale': 1416.67},
    'IDR563': {'name': 'Longreach', 'lat': -23.43, 'lon': 144.28999, 'scale': 708.33},
    'IDR581': {'name': 'South Doodlakine', 'lat': -31.777, 'lon': 117.9529, 'scale': 2833.33},
    'IDR582': {'name': 'South Doodlakine', 'lat': -31.777, 'lon': 117.9529, 'scale': 1416.67},
    'IDR583': {'name': 'South Doodlakine', 'lat': -31.777, 'lon': 117.9529, 'scale': 708.33},
    'IDR584': {'name': 'South Doodlakine', 'lat': -31.777, 'lon': 117.9529, 'scale': 354.17},
    'IDR621': {'name': 'Norfolk Is', 'lat': -29.04, 'lon': 167.94, 'scale': 2833.33},
    'IDR622': {'name': 'Norfolk Is', 'lat': -29.04, 'lon': 167.94, 'scale': 1416.67},
    'IDR623': {'name': 'Norfolk Is', 'lat': -29.04, 'lon': 167.94, 'scale': 708.33},
    'IDR631': {'name': 'Darwin', 'lat': -12.457, 'lon': 130.925, 'scale': 2833.33},
    'IDR632': {'name': 'Darwin', 'lat': -12.457, 'lon': 130.925, 'scale': 1416.67},
    'IDR633': {'name': 'Darwin', 'lat': -12.457, 'lon': 130.925, 'scale': 708.33},
    'IDR634': {'name': 'Darwin', 'lat': -12.457, 'lon': 130.925, 'scale': 354.17},
    'IDR641': {'name': 'Adelaide', 'lat': -34.617, 'lon': 138.46899, 'scale': 2833.33},
    'IDR642': {'name': 'Adelaide', 'lat': -34.617, 'lon': 138.46899, 'scale': 1416.67},
    'IDR643': {'name': 'Adelaide', 'lat': -34.617, 'lon': 138.46899, 'scale': 708.33},
    'IDR644': {'name': 'Adelaide', 'lat': -34.617, 'lon': 138.46899, 'scale': 354.17},
    'IDR661': {'name': 'Brisbane', 'lat': -27.7181, 'lon': 153.24001, 'scale': 2833.33},
    'IDR662': {'name': 'Brisbane', 'lat': -27.7181, 'lon': 153.24001, 'scale': 1416.67},
    'IDR663': {'name': 'Brisbane', 'lat': -27.7181, 'lon': 153.24001, 'scale': 708.33},
    'IDR664': {'name': 'Brisbane', 'lat': -27.7181, 'lon': 153.24001, 'scale': 354.17},
    'IDR671': {'name': 'Warrego', 'lat': -26.44, 'lon': 147.3492, 'scale': 2833.33},
    'IDR672': {'name': 'Warrego', 'lat': -26.44, 'lon': 147.3492, 'scale': 1416.67},
    'IDR673': {'name': 'Warrego', 'lat': -26.44, 'lon': 147.3492, 'scale': 708.33},
    'IDR681': {'name': 'Bairnsdale', 'lat': -37.8876, 'lon': 147.5755, 'scale': 2833.33},
    'IDR682': {'name': 'Bairnsdale', 'lat': -37.8876, 'lon': 147.5755, 'scale': 1416.67},
    'IDR683': {'name': 'Bairnsdale', 'lat': -37.8876, 'lon': 147.5755, 'scale': 708.33},
    'IDR684': {'name': 'Bairnsdale', 'lat': -37.8876, 'lon': 147.5755, 'scale': 354.17},
    'IDR691': {'name': 'Namoi', 'lat': -31.024, 'lon': 150.1915, 'scale': 2833.33},
    'IDR692': {'name': 'Namoi', 'lat': -31.024, 'lon': 150.1915, 'scale': 1416.67},
    'IDR693': {'name': 'Namoi', 'lat': -31.024, 'lon': 150.1915, 'scale': 708.33},
    'IDR694': {'name': 'Namoi', 'lat': -31.024, 'lon': 150.1915, 'scale': 354.17},
    'IDR701': {'name': 'Perth', 'lat': -32.3917, 'lon': 115.8669, 'scale': 2833.33},
    'IDR702': {'name': 'Perth', 'lat': -32.3917, 'lon': 115.8669, 'scale': 1416.67},
    'IDR703': {'name': 'Perth', 'lat': -32.3917, 'lon': 115.8669, 'scale': 708.33},
    'IDR704': {'name': 'Perth', 'lat': -32.3917, 'lon': 115.8669, 'scale': 354.17},
    'IDR711': {'name': 'Sydney', 'lat': -33.7008, 'lon': 151.2095, 'scale': 2833.33},
    'IDR712': {'name': 'Sydney', 'lat': -33.7008, 'lon': 151.2095, 'scale': 1416.67},
    'IDR713': {'name': 'Sydney', 'lat': -33.7008, 'lon': 151.2095, 'scale': 708.33},
    'IDR714': {'name': 'Sydney', 'lat': -33.7008, 'lon': 151.2095, 'scale': 354.17},
    'IDR721': {'name': 'Emerald', 'lat': -23.5498, 'lon': 148.239, 'scale': 2833.33},
    'IDR722': {'name': 'Emerald', 'lat': -23.5498, 'lon': 148.239, 'scale': 1416.67},
    'IDR723': {'name': 'Emerald', 'lat': -23.5498, 'lon': 148.239, 'scale': 708.33},
    'IDR724': {'name': 'Emerald', 'lat': -23.5498, 'lon': 148.239, 'scale': 354.17},
    'IDR731': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 2833.33},
    'IDR732': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 1416.67},
    'IDR733': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.55099, 'scale': 708.33},
    'IDR734': {'name': 'Townsville', 'lat': -19.4196, 'lon': 146.5511, 'scale': 354.17},
    'IDR741': {'name': 'Greenvale', 'lat': -18.997, 'lon': 144.995, 'scale': 2833.33},
    'IDR742': {'name': 'Greenvale', 'lat': -18.997, 'lon': 144.995, 'scale': 1416.67},
    'IDR743': {'name': 'Greenvale', 'lat': -18.997, 'lon': 144.995, 'scale': 708.33},
    'IDR744': {'name': 'Greenvale', 'lat': -18.997, 'lon': 144.995, 'scale': 354.17},
    'IDR751': {'name': 'Mt Isa', 'lat': -20.7112, 'lon': 139.55499, 'scale': 2833.33},
    'IDR752': {'name': 'Mt Isa', 'lat': -20.7112, 'lon': 139.55499, 'scale': 1416.67},
    'IDR753': {'name': 'Mt Isa', 'lat': -20.7112, 'lon': 139.55499, 'scale': 708.33},
    'IDR754': {'name': 'Mt Isa', 'lat': -20.7112, 'lon': 139.55499, 'scale': 354.17},
    'IDR761': {'name': 'Mt Koonya', 'lat': -43.112, 'lon': 147.806, 'scale': 2833.33},
    'IDR762': {'name': 'Hobart Mt Koonya', 'lat': -43.112, 'lon': 147.806, 'scale': 1416.67},
    'IDR763': {'name': 'Hobart Mt Koonya', 'lat': -43.112, 'lon': 147.806, 'scale': 708.33},
    'IDR764': {'name': 'Hobart Mt Koonya', 'lat': -43.112, 'lon': 147.806, 'scale': 354.17},
    'IDR771': {'name': 'Arafura', 'lat': -11.649, 'lon': 133.38, 'scale': 2833.33},
    'IDR772': {'name': 'Arafura', 'lat': -11.649, 'lon': 133.38, 'scale': 1416.67},
    'IDR773': {'name': 'Arafura', 'lat': -11.649, 'lon': 133.38, 'scale': 708.33},
    'IDR774': {'name': 'Arafura', 'lat': -11.649, 'lon': 133.38, 'scale': 354.17},
    'IDR781': {'name': 'Weipa', 'lat': -12.671, 'lon': 141.922, 'scale': 2833.33},
    'IDR782': {'name': 'Weipa', 'lat': -12.671, 'lon': 141.922, 'scale': 1416.67},
    'IDR783': {'name': 'Weipa', 'lat': -12.671, 'lon': 141.922, 'scale': 708.33},
    'IDR784': {'name': 'Weipa', 'lat': -12.666, 'lon': 141.925, 'scale': 354.17},
    'IDR791': {'name': 'Watheroo', 'lat': -30.36, 'lon': 116.2922, 'scale': 2833.33},
    'IDR792': {'name': 'Watheroo', 'lat': -30.36, 'lon': 116.2922, 'scale': 1416.67},
    'IDR793': {'name': 'Watheroo', 'lat': -30.36, 'lon': 116.2922, 'scale': 708.33},
    'IDR794': {'name': 'Watheroo', 'lat': -30.36, 'lon': 116.2922, 'scale': 354.17},
    'IDR931': {'name': 'Brewarrina', 'lat': -29.9696, 'lon': 146.8129, 'scale': 2833.33},
    'IDR932': {'name': 'Brewarrina', 'lat': -29.9696, 'lon': 146.8129, 'scale': 1416.67},
    'IDR933': {'name': 'Brewarrina', 'lat': -29.9696, 'lon': 146.8129, 'scale': 708.33},
    'IDR934': {'name': 'Brewarrina', 'lat': -29.9696, 'lon': 146.8129, 'scale': 354.17},
    'IDR941': {'name': 'Hillston', 'lat': -33.5519, 'lon': 145.52859, 'scale': 2833.33},
    'IDR942': {'name': 'Hillston', 'lat': -33.5519, 'lon': 145.52859, 'scale': 1416.67},
    'IDR943': {'name': 'Hillston', 'lat': -33.5519, 'lon': 145.52859, 'scale': 708.33},
    'IDR944': {'name': 'Hillston', 'lat': -33.5519, 'lon': 145.52859, 'scale': 354.17},
    'IDR951': {'name': 'Rainbow', 'lat': -35.9975, 'lon': 142.01331, 'scale': 2833.33},
    'IDR952': {'name': 'Rainbow', 'lat': -35.9975, 'lon': 142.01331, 'scale': 1416.67},
    'IDR953': {'name': 'Rainbow', 'lat': -35.9975, 'lon': 142.01331, 'scale': 708.33},
    'IDR954': {'name': 'Rainbow', 'lat': -35.9975, 'lon': 142.01331, 'scale': 354.17},
    'IDR961': {'name': 'Yeoval', 'lat': -32.74442, 'lon': 148.7081, 'scale': 2833.33},
    'IDR962': {'name': 'Yeoval', 'lat': -32.74442, 'lon': 148.7081, 'scale': 1416.67},
    'IDR963': {'name': 'Yeoval', 'lat': -32.74442, 'lon': 148.7081, 'scale': 708.33},
    'IDR964': {'name': 'Yeoval', 'lat': -32.74442, 'lon': 148.7081, 'scale': 354.17},
    'IDR971': {'name': 'Mildura', 'lat': -34.2871, 'lon': 141.59821, 'scale': 2833.33},
    'IDR972': {'name': 'Mildura', 'lat': -34.2871, 'lon': 141.59821, 'scale': 1416.67},
    'IDR973': {'name': 'Mildura', 'lat': -34.2871, 'lon': 141.59821, 'scale': 708.33},
    'IDR974': {'name': 'Mildura', 'lat': -34.2871, 'lon': 141.59821, 'scale': 354.17},
    'IDR981': {'name': 'Taroom', 'lat': -25.696, 'lon': 149.89799, 'scale': 2833.33},
    'IDR982': {'name': 'Taroom', 'lat': -25.696, 'lon': 149.89799, 'scale': 1416.67},
    'IDR983': {'name': 'Taroom', 'lat': -25.696, 'lon': 149.89799, 'scale': 708.33},
    'IDR984': {'name': 'Taroom', 'lat': -25.696, 'lon': 149.89799, 'scale': 354.17},
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

@app.route('/images/<radar_id>-<int:index>.png', methods=['GET'])
def serve_image(radar_id, index):
    """Serve radar image, generating if it doesn't exist"""
    try:
        # Validate radar_id
        if radar_id not in RADAR_STATIONS:
            print(f'Invalid radar ID requested: {radar_id}', flush=True)
            return jsonify({'status': 'error', 'message': 'Invalid radar ID'}), 400

        # Validate index
        if index < 0 or index >= 7:
            print(f'Invalid image index requested: {index}', flush=True)
            return jsonify({'status': 'error', 'message': 'Invalid image index'}), 400

        image_path = f'/app/images/{radar_id}-{index}.png'

        # If image exists, serve it
        if os.path.exists(image_path):
            from flask import send_file
            print(f'Serving existing image: {radar_id}-{index}.png', flush=True)
            return send_file(image_path, mimetype='image/png')

        # Image doesn't exist - check if all images for this radar need generation
        print(f'Image {radar_id}-{index}.png not found, checking if generation needed...', flush=True)
        all_exist = all(os.path.exists(f'/app/images/{radar_id}-{i}.png') for i in range(7))

        if not all_exist and radar_id not in generation_locks:
            print(f'Starting synchronous generation for {radar_id}...', flush=True)
            generation_locks[radar_id] = True

            # Generate synchronously for first request
            try:
                from ftpscraper import GenerateImagesForRadar
                success = GenerateImagesForRadar(radar_id, 7)
                if success and os.path.exists(image_path):
                    print(f'Generated and serving {radar_id}-{index}.png', flush=True)
                    from flask import send_file
                    return send_file(image_path, mimetype='image/png')
                else:
                    print(f'Generation failed or image still missing for {radar_id}', flush=True)
                    return jsonify({'status': 'error', 'message': 'Image generation failed'}), 500
            except Exception as e:
                print(f'Error generating images for {radar_id}: {e}', flush=True)
                return jsonify({'status': 'error', 'message': str(e)}), 500
            finally:
                if radar_id in generation_locks:
                    del generation_locks[radar_id]
        elif radar_id in generation_locks:
            # Currently generating, ask client to retry
            print(f'Image {radar_id}-{index}.png still generating, returning 202', flush=True)
            return jsonify({'status': 'generating', 'message': 'Images are being generated, please retry'}), 202
        else:
            print(f'Image {radar_id}-{index}.png not found and cannot generate', flush=True)
            return jsonify({'status': 'error', 'message': 'Image not found'}), 404

    except Exception as e:
        print(f'Error serving image {radar_id}-{index}: {e}', flush=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    print('Starting BetterWeather API server on port 5000...')
    app.run(host='0.0.0.0', port=5000, debug=False)
