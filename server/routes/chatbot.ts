// server/routes/chatbot.ts
import { RequestHandler } from "express";
import { spawn } from "child_process";
import { OpenAI } from "openai";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface ChatbotQuery {
  message: string;
}

interface ChatbotResponse {
  response: string;
  links?: Array<{
    title: string;
    url: string;
    description: string;
    type?: string;
  }>;
  error?: string;
}

interface ScrapedResult {
  title: string;
  url: string;
  description: string;
  type: string;
}

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "ollama",
  baseURL: process.env.OPENAI_API_KEY
    ? undefined
    : process.env.OLLAMA_BASE_URL || "http://localhost:11434/v1",
});

class ChatbotService {
  private async runPythonScraper(keyword: string): Promise<ScrapedResult[]> {
    return new Promise((resolve) => {
      const scraperPath = path.join(__dirname, "../../scraper/bps_scraper.py");
      const pythonProcess = spawn("python", [scraperPath, keyword]);

      let output = "";
      let errorOutput = "";

      pythonProcess.stdout.on("data", (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on("data", (data) => {
        errorOutput += data.toString();
      });

      pythonProcess.on("close", () => {
        if (errorOutput) {
          console.error("Python scraper error:", errorOutput);
          return resolve([]);
        }
        try {
          const results = JSON.parse(output);
          resolve(Array.isArray(results) ? results : []);
        } catch (error) {
          console.error("Failed to parse scraper output:", error);
          resolve([]);
        }
      });

      pythonProcess.on("error", (error) => {
        console.error("Failed to spawn python process:", error);
        resolve([]);
      });
    });
  }

  private async getAIResponse(
    userMessage: string,
    scrapedResults: ScrapedResult[]
  ): Promise<string> {
    const prompt = this.buildPrompt(userMessage, scrapedResults);

    try {
      const completion = await openai.chat.completions.create({
        model: process.env.OPENAI_API_KEY ? "gpt-3.5-turbo" : "llama3",
        messages: [
          {
            role: "system",
            content: `Anda adalah AIDA, asisten resmi BPS Kota Medan. 
Jawab dengan bahasa Indonesia yang sopan, jelas, dan fokus pada data BPS Kota Medan. 
Jika ada link, jelaskan relevansinya secara singkat.`,
          },
          { role: "user", content: prompt },
        ],
        max_tokens: 500,
        temperature: 0.6,
      });

      return (
        completion.choices[0]?.message?.content ||
        "Maaf, saya tidak bisa memproses permintaan saat ini."
      );
    } catch (error) {
      console.error("AI error:", error);
      return "Maaf, sistem AI tidak tersedia saat ini. Namun berikut adalah hasil pencarian yang ditemukan.";
    }
  }

  private buildPrompt(userMessage: string, scrapedResults: ScrapedResult[]) {
    let prompt = `Pertanyaan pengguna: "${userMessage}"\n\n`;
    if (scrapedResults.length > 0) {
      prompt += "Hasil pencarian dari BPS Kota Medan:\n";
      scrapedResults.forEach((r, i) => {
        prompt += `${i + 1}. ${r.title}\n${r.description}\n${r.url}\n\n`;
      });
      prompt +=
        "Jelaskan relevansi hasil ini terhadap pertanyaan pengguna dan sertakan saran jika perlu.";
    } else {
      prompt +=
        "Tidak ada hasil ditemukan. Berikan saran kata kunci alternatif dan jenis data yang mungkin relevan di BPS Kota Medan.";
    }
    return prompt;
  }

  private extractKeywords(message: string): string[] {
    const mappings: Record<string, string[]> = {
      kemiskinan: ["kemiskinan", "miskin", "poverty", "garis kemiskinan"],
      penduduk: ["penduduk", "kependudukan", "demografi", "population"],
      ekonomi: ["ekonomi", "economy", "pdrb", "gdp"],
      industri: ["industri", "industry", "manufaktur", "produksi"],
      pertanian: ["pertanian", "agriculture", "perkebunan", "kehutanan"],
      pendidikan: ["pendidikan", "education", "sekolah", "universitas"],
      kesehatan: ["kesehatan", "health", "rumah sakit", "puskesmas"],
      perdagangan: ["perdagangan", "trade", "ekspor", "impor"],
      transportasi: ["transportasi", "angkutan", "kendaraan"],
      komunikasi: ["komunikasi", "telekomunikasi", "internet"],
      wisata: ["wisata", "tourism", "pariwisata"],
      inflasi: ["inflasi", "inflation", "harga", "ihk"],
    };

    const found: string[] = [];
    const lower = message.toLowerCase();
    for (const [key, variations] of Object.entries(mappings)) {
      if (variations.some((v) => lower.includes(v)) && !found.includes(key)) {
        found.push(key);
      }
    }
    return found;
  }

  private removeDuplicates(results: ScrapedResult[]) {
    const seen = new Set();
    return results.filter((r) => {
      if (seen.has(r.url)) return false;
      seen.add(r.url);
      return true;
    });
  }

  async processQuery(message: string): Promise<ChatbotResponse> {
    const keywords = this.extractKeywords(message);
    if (keywords.length === 0) {
      return {
        response:
          "Silakan berikan kata kunci yang lebih spesifik, misalnya: kemiskinan, penduduk, PDRB, pendidikan.",
        links: [
          {
            title: "BPS Kota Medan - Halaman Utama",
            url: "https://medankota.bps.go.id/",
            description: "Situs resmi Badan Pusat Statistik Kota Medan",
          },
        ],
      };
    }

    let allResults: ScrapedResult[] = [];
    for (const kw of keywords) {
      const results = await this.runPythonScraper(kw);
      allResults = [...allResults, ...results];
    }

    const uniqueResults = this.removeDuplicates(allResults);
    const aiResponse = await this.getAIResponse(message, uniqueResults);

    return {
      response: aiResponse,
      links: uniqueResults,
    };
  }
}

const chatbotService = new ChatbotService();

export const handleChatbotQuery: RequestHandler = async (req, res) => {
  try {
    const { message }: ChatbotQuery = req.body;
    if (!message) {
      return res.status(400).json({
        error: "Message is required",
        response: "Silakan masukkan pertanyaan Anda.",
      });
    }
    const result = await chatbotService.processQuery(message);
    res.json(result);
  } catch (error) {
    console.error("Chatbot query error:", error);
    res.status(500).json({
      error: "Internal server error",
      response: "Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti.",
    });
  }
};