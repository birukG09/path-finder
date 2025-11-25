import heapq
import math
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

class CityGraph:
    def __init__(self):
        self.graph = {
            'Meskel Square': {'Bole': 5, 'Piazza': 4, 'Megenagna': 3},
            'Bole': {'Meskel Square': 5, 'Airport': 3, 'Bole Michael': 4},
            'Piazza': {'Meskel Square': 4, 'Arada': 2, 'Merkato': 3},
            'Megenagna': {'Meskel Square': 3, 'CMC': 4, 'Bole Michael': 5},
            'Airport': {'Bole': 3},
            'Bole Michael': {'Bole': 4, 'Megenagna': 5, 'CMC': 3},
            'Arada': {'Piazza': 2, 'Merkato': 2},
            'Merkato': {'Piazza': 3, 'Arada': 2, 'CMC': 4},
            'CMC': {'Megenagna': 4, 'Bole Michael': 3, 'Merkato': 4}
        }

        self.road_conditions = {
            ('Meskel Square', 'Bole'): 'good',
            ('Meskel Square', 'Piazza'): 'good', 
            ('Meskel Square', 'Megenagna'): 'moderate',
            ('Bole', 'Airport'): 'good',
            ('Bole', 'Bole Michael'): 'good',
            ('Piazza', 'Arada'): 'poor',
            ('Piazza', 'Merkato'): 'moderate',
            ('Megenagna', 'CMC'): 'good',
            ('Megenagna', 'Bole Michael'): 'moderate',
            ('Arada', 'Merkato'): 'poor',
            ('Merkato', 'CMC'): 'moderate',
            ('Bole Michael', 'CMC'): 'good'
        }

        self.coordinates = {
            'Meskel Square': {'lat': 9.0107, 'lng': 38.7613},
            'Bole': {'lat': 8.9950, 'lng': 38.7900},
            'Piazza': {'lat': 9.0330, 'lng': 38.7469},
            'Megenagna': {'lat': 9.0180, 'lng': 38.7850},
            'Airport': {'lat': 8.9789, 'lng': 38.7997},
            'Bole Michael': {'lat': 9.0050, 'lng': 38.7750},
            'Arada': {'lat': 9.0380, 'lng': 38.7380},
            'Merkato': {'lat': 9.0300, 'lng': 38.7200},
            'CMC': {'lat': 9.0250, 'lng': 38.7600}
        }

        self._make_bidirectional()

    def _make_bidirectional(self):
        reverse_graph = {}
        for node, neighbors in self.graph.items():
            for neighbor, cost in neighbors.items():
                if neighbor not in reverse_graph:
                    reverse_graph[neighbor] = {}
                reverse_graph[neighbor][node] = cost

        for node, neighbors in reverse_graph.items():
            if node not in self.graph:
                self.graph[node] = {}
            self.graph[node].update(neighbors)

    def get_locations(self):
        return list(self.graph.keys())

    def get_location_data(self):
        return [
            {
                'name': location,
                'lat': self.coordinates[location]['lat'],
                'lng': self.coordinates[location]['lng']
            }
            for location in self.get_locations()
        ]

    def get_edges(self):
        edges = []
        seen = set()
        for node, neighbors in self.graph.items():
            for neighbor, distance in neighbors.items():
                edge_key = tuple(sorted([node, neighbor]))
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({
                        'from': node,
                        'to': neighbor,
                        'distance': distance
                    })
        return edges

    def uniform_cost_search(self, start, goal):
        frontier = []
        heapq.heappush(frontier, (0, start, [start]))
        explored = {}
        optimal_paths = []
        min_cost = float('inf')

        while frontier:
            cost, current, path = heapq.heappop(frontier)
            if current in explored and explored[current] < cost:
                continue
            explored[current] = cost

            if current == goal:
                if cost < min_cost:
                    min_cost = cost
                    optimal_paths = [path]
                elif cost == min_cost:
                    optimal_paths.append(path)
                continue

            for neighbor, edge_cost in self.graph[current].items():
                new_cost = cost + edge_cost
                new_path = path + [neighbor]
                if neighbor not in explored or new_cost < explored[neighbor]:
                    heapq.heappush(frontier, (new_cost, neighbor, new_path))

        return optimal_paths, min_cost if optimal_paths else (None, float('inf'))

    def depth_first_search(self, start, goal):
        stack = [(start, [start], 0)]
        explored = set()
        all_paths = []

        while stack:
            current, path, cost = stack.pop()
            
            if current in explored:
                continue
            explored.add(current)

            if current == goal:
                all_paths.append((path, cost))
                continue

            for neighbor, edge_cost in sorted(self.graph[current].items(), reverse=True):
                if neighbor not in explored:
                    new_path = path + [neighbor]
                    new_cost = cost + edge_cost
                    stack.append((neighbor, new_path, new_cost))

        if all_paths:
            min_cost = min(path_cost for _, path_cost in all_paths)
            optimal_paths = [path for path, path_cost in all_paths if path_cost == min_cost]
            return optimal_paths, min_cost
        
        return None, float('inf')

    def _heuristic(self, node1, node2):
        lat1, lng1 = self.coordinates[node1]['lat'], self.coordinates[node1]['lng']
        lat2, lng2 = self.coordinates[node2]['lat'], self.coordinates[node2]['lng']
        
        lat_diff = (lat2 - lat1) * 111
        lng_diff = (lng2 - lng1) * 111 * math.cos(math.radians((lat1 + lat2) / 2))
        
        return math.sqrt(lat_diff**2 + lng_diff**2)

    def a_star_search(self, start, goal):
        frontier = []
        heapq.heappush(frontier, (0, 0, start, [start]))
        explored = {}
        optimal_paths = []
        min_cost = float('inf')

        while frontier:
            f_cost, g_cost, current, path = heapq.heappop(frontier)
            
            if current in explored and explored[current] < g_cost:
                continue
            explored[current] = g_cost

            if current == goal:
                if g_cost < min_cost:
                    min_cost = g_cost
                    optimal_paths = [path]
                elif g_cost == min_cost:
                    optimal_paths.append(path)
                continue

            for neighbor, edge_cost in self.graph[current].items():
                new_g_cost = g_cost + edge_cost
                new_path = path + [neighbor]
                
                if neighbor not in explored or new_g_cost < explored[neighbor]:
                    h_cost = self._heuristic(neighbor, goal)
                    new_f_cost = new_g_cost + h_cost
                    heapq.heappush(frontier, (new_f_cost, new_g_cost, neighbor, new_path))

        return optimal_paths, min_cost if optimal_paths else (None, float('inf'))

    def check_road_condition(self, location1, location2):
        key1 = (location1, location2)
        key2 = (location2, location1)
        if key1 in self.road_conditions:
            return self.road_conditions[key1]
        elif key2 in self.road_conditions:
            return self.road_conditions[key2]
        else:
            return 'unknown'

    def check_traffic_level(self, location):
        traffic_hotspots = ['Meskel Square', 'Megenagna', 'Bole Michael', 'Piazza']
        if location in traffic_hotspots:
            return 'high'
        return 'moderate'

graph = CityGraph()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/locations')
def get_locations():
    return jsonify({
        'locations': graph.get_location_data(),
        'edges': graph.get_edges()
    })

@app.route('/api/findpath', methods=['POST'])
def find_path():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    start = data.get('start')
    goal = data.get('goal')
    algorithm = data.get('algorithm', 'ucs')

    if not start or not goal:
        return jsonify({'error': 'Start and goal locations are required'}), 400

    if start == goal:
        return jsonify({'error': 'You are already at your destination'}), 400

    if start not in graph.get_locations():
        return jsonify({'error': f'Unknown starting location: {start}'}), 400

    if goal not in graph.get_locations():
        return jsonify({'error': f'Unknown goal location: {goal}'}), 400

    warnings = []
    
    road_condition = graph.check_road_condition(start, goal)
    if road_condition == 'poor':
        warnings.append(f'Road condition between {start} and {goal} is poor')
    
    traffic_level = graph.check_traffic_level(start)
    if traffic_level == 'high':
        warnings.append(f'High traffic expected at {start}')

    if algorithm == 'dfs':
        optimal_paths, cost = graph.depth_first_search(start, goal)
    elif algorithm == 'astar':
        optimal_paths, cost = graph.a_star_search(start, goal)
    else:
        optimal_paths, cost = graph.uniform_cost_search(start, goal)

    if not optimal_paths or cost == float('inf'):
        return jsonify({'error': 'No path found'}), 404

    path_data = []
    for path in optimal_paths:
        path_coords = [
            {
                'name': loc,
                'lat': graph.coordinates[loc]['lat'],
                'lng': graph.coordinates[loc]['lng']
            }
            for loc in path
        ]
        path_data.append(path_coords)

    return jsonify({
        'paths': path_data,
        'cost': cost,
        'warnings': warnings,
        'numPaths': len(optimal_paths),
        'algorithm': algorithm.upper()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
