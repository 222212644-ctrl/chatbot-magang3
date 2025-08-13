#!/bin/bash

echo "🚀 Setting up Ollama for BPS Medan AIDA Chatbot"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install from https://ollama.ai/"
    exit 1
fi

echo "✅ Ollama found"

# Start Ollama service
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for service to start
sleep 5

# Pull recommended models
echo "📥 Pulling recommended models..."

echo "Pulling llama3 (recommended for Indonesian)..."
ollama pull llama3

echo "Pulling mistral (alternative option)..."
ollama pull mistral

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update your .env file:"
echo "   - Comment out OPENAI_API_KEY"
echo "   - Uncomment OLLAMA_BASE_URL=http://localhost:11434/v1"
echo ""
echo "2. Update server/routes/chatbot.ts:"
echo "   - Change model from 'gpt-3.5-turbo' to 'llama3' or 'mistral'"
echo ""
echo "3. Restart your development server: pnpm dev"
echo ""
echo "🎉 Ollama is running in background (PID: $OLLAMA_PID)"
echo "💡 To stop Ollama: kill $OLLAMA_PID"
