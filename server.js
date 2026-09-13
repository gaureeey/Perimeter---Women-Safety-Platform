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

const server = http.createServer((req, res) => {
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
        process.exit(0);
    } else {
        throw err;
    }
});

server.listen(PORT, () => {
    console.log(`\n======================================================`);
    console.log(`🛡️  PERIMETER Frontend Server is running!`);
    console.log(`🔗 Local URL: http://localhost:${PORT}/`);
    console.log(`📝 Register:   http://localhost:${PORT}/register.html`);
    console.log(`======================================================\n`);
});
