const http = require('http');
const dct = require('dct');
const math = require('mathjs');

const hostname = '127.0.0.1';
const port = 3000;

// 2D DCT using row-column method with 'dct' library
function dct2d(matrix) {
  const rows = matrix.length;
  const cols = matrix[0].length;

  // Apply 1D DCT to each row
  let temp_matrix = matrix.map(row => dct.transform(row));

  // Transpose the matrix to apply DCT to columns
  temp_matrix = math.transpose(temp_matrix);

  // Apply 1D DCT to each new row (original columns)
  temp_matrix = temp_matrix.map(col => dct(col));

  // Transpose back to original orientation
  return math.transpose(temp_matrix);
}

// 2D IDCT using row-column method with 'dct' library
function idct2d(matrix) {
  const rows = matrix.length;
  const cols = matrix[0].length;

  // Apply 1D IDCT to each row
  let temp_matrix = matrix.map(row => dct.inverse(row));

  // Transpose the matrix to apply IDCT to columns
  temp_matrix = math.transpose(temp_matrix);

  // Apply 1D IDCT to each new row (original columns)
  temp_matrix = temp_matrix.map(col => dct.inverse(col));

  // Transpose back to original orientation
  return math.transpose(temp_matrix);
}

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'POST' && req.url === '/dct') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const { data, rows, cols } = JSON.parse(body);
        const result = dct2d(data);
        res.statusCode = 200;
        res.end(JSON.stringify({ result }));
      } catch (error) {
        console.error(`Error in /dct: ${error.message}`);
        res.statusCode = 400;
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  } else if (req.method === 'POST' && req.url === '/idct') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const { data, rows, cols } = JSON.parse(body);
        const result = idct2d(data);
        res.statusCode = 200;
        res.end(JSON.stringify({ result }));
      } catch (error) {
        console.error(`Error in /idct: ${error.message}`);
        res.statusCode = 400;
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  } else if (req.method === 'GET' && req.url === '/') {
    res.statusCode = 200;
    res.end(JSON.stringify({ status: 'ok' }));
  } else {
    res.statusCode = 404;
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

server.listen(port, hostname, () => {
  console.log(`JavaScript DCT server running at http://${hostname}:${port}/`);
});