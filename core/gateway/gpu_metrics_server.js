/**
 * GPU Metrics Server - Host-only, no Python needed.
 * Runs nvidia-smi and exposes JSON on port 8083.
 * Use: node gpu_metrics_server.js
 */
const http = require('http');
const { execFile } = require('child_process');

const PORT = 8083;
const CORS = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };

// CSV columns: index, name, utilization.gpu, memory.used, memory.total, temperature.gpu
// GPU name can contain commas (e.g. "NVIDIA RTX 4090, 24 GB"), so take last 4 cols as numbers.
function parseNvidiaSmi(stdout) {
  const gpus = [];
  const lines = stdout.trim().split('\n').filter(Boolean);
  for (let i = 0; i < lines.length; i++) {
    const parts = lines[i].split(',').map((p) => p.trim());
    if (parts.length >= 6) {
      const last4 = parts.slice(-4);
      const util = parseFloat(last4[0]) || 0;
      const usedMb = parseFloat(last4[1]) || 0;
      const totalMb = parseFloat(last4[2]) || 1;
      const temp = parseFloat(last4[3]) || 0;
      const name = parts.slice(1, -4).join(', ').trim() || parts[1] || 'GPU';
      gpus.push({
        id: parseInt(parts[0], 10) || i,
        name,
        utilization: util,
        memory_used_mb: usedMb,
        memory_total_mb: totalMb,
        temperature: temp,
      });
    }
  }
  return gpus;
}

function runNvidiaSmi() {
  return new Promise((resolve, reject) => {
    execFile(
      'nvidia-smi',
      [
        '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu',
        '--format=csv,noheader,nounits',
      ],
      { timeout: 5000, maxBuffer: 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err) {
          reject(err.message || stderr || 'nvidia-smi failed');
          return;
        }
        try {
          resolve(parseNvidiaSmi(stdout));
        } catch (e) {
          reject(e.message);
        }
      }
    );
  });
}

const server = http.createServer(async (req, res) => {
  const path = (req.url || '/').split('?')[0];
  if (req.method === 'OPTIONS') {
    res.writeHead(200, { ...CORS, 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
    res.end();
    return;
  }
  if (path === '/health') {
    res.writeHead(200, CORS);
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }
  if (path !== '/gpu-metrics' && path !== '/') {
    res.writeHead(404, CORS);
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }
  try {
    const gpus = await runNvidiaSmi();
    res.writeHead(200, CORS);
    res.end(JSON.stringify({ timestamp: Date.now() / 1000, gpus }));
  } catch (e) {
    res.writeHead(500, CORS);
    res.end(JSON.stringify({ error: String(e.message || e) }));
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`GPU Metrics Server running on http://0.0.0.0:${PORT}`);
  console.log('Endpoints: /gpu-metrics, /health');
});
