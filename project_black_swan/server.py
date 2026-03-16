import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from api import run_simulation

class DashboardHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Prevent caching:
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/simulate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode('utf-8'))
                
                # Extract and parse arrays from comma separated strings if sent as such
                def parse_list(val, type_func):
                    if isinstance(val, list): return [type_func(v) for v in val]
                    if isinstance(val, str): return [type_func(v.strip()) for v in val.split(',')]
                    return [type_func(val)]
                
                densities = parse_list(params.get('densities', [0.1, 0.5, 1.0, 2.0, 5.0]), float)
                scales = parse_list(params.get('dimension_scales', [10, 50, 100, 250]), int)
                
                regions = int(params.get('regions', 20))
                scenarios = int(params.get('scenarios', 10))
                time_units = int(params.get('time_units', 12))
                initial_shock = float(params.get('initial_shock', 1000000.0))
                num_nodes = int(params.get('num_nodes', 500))
                
                print(f"Running simulation with: Scales={scales}, Densities={densities}")
                
                results = run_simulation(
                    densities, scales, regions, scenarios, time_units, initial_shock, num_nodes
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
            return
            
        self.send_response(404)
        self.end_headers()

def run_server(port=6001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("--------------------------------------------------")
    print(" CASCADE RISK ENGINE | Fracture Telemetry Dashboard")
    print(f" Running at http://localhost:{port}")
    print("--------------------------------------------------")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run_server()
