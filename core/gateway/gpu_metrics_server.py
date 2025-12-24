"""
GPU Metrics Server - Lightweight proxy for real GPU stats
Runs on host (not Docker) to access nvidia-smi directly
"""
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import time

PORT = 8083

class GPUMetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/gpu-metrics' or path == '/':
            self.send_gpu_metrics()
        elif path == '/health':
            self.send_health()
        else:
            self.send_error(404, 'Not found')
    
    def send_gpu_metrics(self):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise Exception(f"nvidia-smi failed: {result.stderr}")
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpus.append({
                        "id": int(parts[0]),
                        "name": parts[1],
                        "utilization": float(parts[2]) if parts[2] else 0,
                        "memory_used_mb": float(parts[3]) if parts[3] else 0,
                        "memory_total_mb": float(parts[4]) if parts[4] else 1,
                        "temperature": float(parts[5]) if parts[5] else 0
                    })
            
            response = {
                "timestamp": time.time(),
                "gpus": gpus
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def send_health(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[GPU Metrics] {args[0]}")

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', PORT), GPUMetricsHandler)
    print(f"GPU Metrics Server running on http://0.0.0.0:{PORT}")
    print(f"Endpoints: /gpu-metrics, /health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
