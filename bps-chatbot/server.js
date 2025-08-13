const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');

const app = express();
app.use(cors());
app.use(bodyParser.json());

app.post('/chat', (req, res) => {
  const prompt = req.body.message || '';

  const ollama = spawn('ollama', ['run', 'llama3'], { stdio: ['pipe', 'pipe', 'inherit'] });
  ollama.stdin.write(prompt + '\n');
  ollama.stdin.end();

  let output = '';
  ollama.stdout.on('data', (data) => {
    output += data.toString();
  });

  ollama.on('close', () => {
    res.json({ reply: output.trim() });
  });
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Server berjalan di http://localhost:${PORT}`));