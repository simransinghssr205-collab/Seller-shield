// Tiny static server. No npm install needed.
// Run from the Frontend folder:  node server.js
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;

const TYPES = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "text/javascript",
};

http
  .createServer((req, res) => {
    const urlPath = req.url === "/" ? "/index.html" : req.url.split("?")[0];
    const filePath = path.join(__dirname, path.normalize(urlPath));

    // Stay inside the Frontend folder.
    if (!filePath.startsWith(__dirname)) {
      res.writeHead(403);
      return res.end("Forbidden");
    }

    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(404);
        return res.end("Not found");
      }
      const type = TYPES[path.extname(filePath)] || "text/plain";
      res.writeHead(200, { "Content-Type": type });
      res.end(content);
    });
  })
  .listen(PORT, () => {
    console.log(`Frontend running at http://localhost:${PORT}`);
  });