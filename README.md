# BPS Medan AIDA Chatbot

Chatbot AI untuk pencarian data statistik BPS Kota Medan menggunakan OpenAI/Ollama dan web scraping real-time.

## Features

- 🤖 **AI-Powered**: Menggunakan OpenAI GPT atau Ollama untuk respons cerdas
- 🕷️ **Web Scraping**: Scraping real-time website BPS Medan untuk data terkini
- 💬 **Interactive Chat**: Interface chat yang responsif dan user-friendly
- 🔍 **Smart Search**: Pencarian berdasarkan kata kunci dengan mapping otomatis
- 📊 **Data Links**: Menampilkan link langsung ke data BPS yang relevan

## Prerequisites

1. **Node.js** (v18 atau lebih tinggi)
2. **Python** (v3.8 atau lebih tinggi)
3. **pnpm** (package manager)
4. **OpenAI API Key** atau **Ollama** yang terinstall

## Installation & Setup

### 1. Clone dan Install Dependencies

```bash
# Clone repository
git clone <repository-url>
cd bps-medan-chatbot

# Install Node.js dependencies
pnpm install

# Install Python dependencies
cd scraper
pip install -r requirements.txt
cd ..
```

### 2. Environment Configuration

Buat file `.env` dari template:

```bash
cp .env.example .env
```

Edit file `.env`:

```env
# Untuk menggunakan OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# ATAU untuk menggunakan Ollama (komentari OPENAI_API_KEY di atas)
# OLLAMA_BASE_URL=http://localhost:11434/v1

NODE_ENV=development
PORT=8080
PING_MESSAGE=BPS Medan AIDA Server is running!
```

### 3. Setup OpenAI atau Ollama

#### Option A: Menggunakan OpenAI

1. Daftar di [OpenAI Platform](https://platform.openai.com/)
2. Buat API key
3. Masukkan API key ke `.env`

#### Option B: Menggunakan Ollama (Local AI)

1. Install Ollama dari [ollama.ai](https://ollama.ai/)
2. Pull model yang diinginkan:
   ```bash
   ollama pull llama3
   # atau
   ollama pull mistral
   ```
3. Jalankan Ollama:
   ```bash
   ollama serve
   ```
4. Update backend code untuk menggunakan model Ollama (ganti `gpt-3.5-turbo` dengan `llama3`)

### 4. Test Python Scraper

Test scraper secara manual:

```bash
cd scraper
python bps_scraper.py "kemiskinan"
python bps_scraper.py "penduduk"
```

## Running the Application

### Development Mode

```bash
# Start development server
pnpm dev
```

Server akan berjalan di `http://localhost:8080`

### Production Mode

```bash
# Build aplikasi
pnpm build

# Start production server
pnpm start
```

## Project Structure

```
project/
├── client/                 # React frontend
│   ├── pages/Index.tsx    # Main chatbot page
│   └── components/ui/     # UI components
├── server/                # Express backend
│   ├── routes/chatbot.ts  # Chatbot API endpoint
│   └── index.ts          # Server configuration
├── scraper/              # Python web scraper
│   ├── bps_scraper.py   # Main scraper script
│   └── requirements.txt  # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## API Endpoints

### POST `/api/chatbot`

Request:

```json
{
  "message": "kemiskinan di medan"
}
```

Response:

```json
{
  "response": "AI generated response...",
  "links": [
    {
      "title": "Data Kemiskinan Kota Medan 2023",
      "url": "https://medankota.bps.go.id/statistics-table/subject-563",
      "description": "Statistik kemiskinan di Kota Medan tahun 2023",
      "type": "statistics"
    }
  ]
}
```

## Supported Keywords

Chatbot dapat mengenali berbagai kata kunci:

- **Kemiskinan**: kemiskinan, miskin, poverty, garis kemiskinan
- **Penduduk**: penduduk, kependudukan, demografi, population
- **Ekonomi**: ekonomi, pdrb, gdp, pertumbuhan ekonomi
- **Industri**: industri, manufaktur, produksi, pabrik
- **Pertanian**: pertanian, perkebunan, kehutanan, perikanan
- **Pendidikan**: pendidikan, sekolah, universitas
- **Kesehatan**: kesehatan, rumah sakit, puskesmas
- **Dan lainnya...**

## Troubleshooting

### Python Error

```bash
# Pastikan Python dependencies terinstall
cd scraper
pip install -r requirements.txt

# Test scraper
python bps_scraper.py "test"
```

### OpenAI API Error

- Pastikan API key valid dan memiliki kredit
- Cek limit rate API

### Ollama Error

- Pastikan Ollama service berjalan: `ollama serve`
- Pastikan model sudah di-pull: `ollama pull llama3`

### Network Error

- Pastikan koneksi internet stabil
- Website BPS mungkin sedang maintenance

## Development

### Adding New Keywords

Edit file `server/routes/chatbot.ts` pada bagian `keywordMappings`.

### Improving Scraper

Edit file `scraper/bps_scraper.py` untuk menambah target scraping baru.

### Custom AI Prompts

Modifikasi method `buildPrompt` di `server/routes/chatbot.ts`.

## Contributing

1. Fork repository
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Create Pull Request

## License

MIT License

## Support

Untuk bantuan teknis, silakan buat issue di repository ini.
