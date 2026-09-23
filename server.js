const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8080;
const PUBLIC_DIR = path.join(__dirname, 'frontend');

const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.mp4': 'video/mp4',
    '.webm': 'video/webm'
};

const { spawn } = require('child_process');

function findPythonExe() {
    const candidates = [
        path.join(process.env.LOCALAPPDATA || '', 'Python', 'bin', 'python.exe'),
        path.join(process.env.LOCALAPPDATA || '', 'Python', 'pythoncore-3.14-64', 'python.exe'),
        'python',
        'py'
    ];
    for (const c of candidates) {
        if (c.includes('\\') && fs.existsSync(c)) {
            return c;
        }
    }
    return 'python';
}

function checkAndStartBackend() {
    const req = http.get('http://127.0.0.1:8000/api/v1/health', (res) => {
        if (res.statusCode === 200) {
            console.log('⚡ PERIMETER FastAPI Backend is active on port 8000.');
        }
    });
    req.on('error', () => {
        console.log('🚀 Port 8000 backend not detected. Auto-starting FastAPI backend...');
        const pyExe = findPythonExe();
        const backendDir = path.join(__dirname, 'backend');
        const child = spawn(pyExe, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
            cwd: backendDir,
            stdio: 'inherit',
            shell: true
        });
        child.on('error', (err) => {
            console.warn('⚠️ Could not auto-start backend automatically:', err.message);
            console.log('👉 Please start the backend manually with: npm run backend');
        });
    });
}

const server = http.createServer((req, res) => {
    // Transparently proxy /api/ requests to port 8000
    if (req.url.startsWith('/api/') || req.url.startsWith('/docs') || req.url.startsWith('/openapi.json')) {
        const proxyReq = http.request({
            hostname: '127.0.0.1',
            port: 8000,
            path: req.url,
            method: req.method,
            headers: req.headers
        }, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res);
        });

        proxyReq.on('error', () => {
            res.writeHead(502, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                detail: 'PERIMETER Backend (port 8000) not reachable. Please start with "npm run backend".'
            }));
        });

        req.pipe(proxyReq);
        return;
    }

    let cleanUrl = req.url.split('?')[0];
    if (cleanUrl === '/' || cleanUrl === '') {
        cleanUrl = '/index.html';
    }

    // First try frontend subdirectory
    let filePath = path.join(PUBLIC_DIR, cleanUrl);
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        // Fallback to project root directory
        filePath = path.join(__dirname, cleanUrl);
    }

    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
    } else {
        res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`<h2>404 Not Found</h2><p>Resource ${cleanUrl} not found.</p><p><a href="/register.html">Go to Registration / Platform</a></p>`);
    }
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.log(`\n⚠️  Port ${PORT} is already in use (the server is already running!).`);
        console.log(`🔗 Access it at: http://localhost:${PORT}/register.html\n`);
        checkAndStartBackend();
        process.exit(0);
    } else {
        throw err;
    }
});

server.listen(PORT, () => {
    console.log(`\n======================================================`);
    console.log(`🛡️  PERIMETER Unified Platform Server is running!`);
    console.log(`🔗 Frontend:   http://localhost:${PORT}/`);
    console.log(`📝 Register:   http://localhost:${PORT}/register.html`);
    console.log(`⚡ API Proxy:  http://localhost:${PORT}/api/v1/`);
    console.log(`📡 Backend:    http://127.0.0.1:8000/docs`);
    console.log(`======================================================\n`);
    checkAndStartBackend();
});
