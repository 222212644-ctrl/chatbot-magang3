import { useState, useRef, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card } from "../components/ui/card";
import {
  Send,
  Bot,
  User,
  ExternalLink,
  AlertCircle,
  Search,
} from "lucide-react";

interface Message {
  id: string;
  type: "user" | "bot";
  content: string;
  links?: Array<{
    title: string;
    url: string;
    description: string;
    type?: string;
  }>;
  timestamp: Date;
  error?: boolean;
}

export default function Index() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "bot",
      content:
        "Halo! Saya AIDA (AI Data Assistant) dari BPS Kota Medan. Saya dapat membantu Anda mencari informasi dan data statistik yang tersedia di website BPS Kota Medan menggunakan AI dan web scraping real-time. Silakan ketik kata kunci yang Anda cari!",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue("");
    setIsTyping(true);

    try {
      const response = await fetch("/api/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: currentInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        content: data.response || "Maaf, tidak ada respons dari server.",
        links: data.links || [],
        timestamp: new Date(),
        error: !!data.error,
      };

      setMessages((prev) => [...prev, botResponse]);
      setIsConnected(true);
    } catch (error) {
      console.error("Error calling chatbot API:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        content:
          "Maaf, terjadi kesalahan koneksi. Pastikan server berjalan dan Python dependencies terinstall. Silakan coba lagi nanti.",
        timestamp: new Date(),
        error: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
      setIsConnected(false);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getMessageIcon = (message: Message) => {
    if (message.type === "user") {
      return <User className="w-3 h-3 sm:w-4 sm:h-4 text-white" />;
    }

    if (message.error) {
      return <AlertCircle className="w-3 h-3 sm:w-4 sm:h-4 text-white" />;
    }

    if (message.links && message.links.length > 0) {
      return <Search className="w-3 h-3 sm:w-4 sm:h-4 text-white" />;
    }

    return <Bot className="w-3 h-3 sm:w-4 sm:h-4 text-white" />;
  };

  const getMessageBubbleColor = (message: Message) => {
    if (message.type === "user") {
      return "bg-gray-600 text-white";
    }

    if (message.error) {
      return "bg-red-50 text-red-900 border border-red-200";
    }

    return "bg-bps-50 text-gray-900";
  };

  const getAvatarColor = (message: Message) => {
    if (message.type === "user") {
      return "bg-gray-600";
    }

    if (message.error) {
      return "bg-red-500";
    }

    return "bg-bps-600";
  };

  const getLinkTypeIcon = (type?: string) => {
    switch (type) {
      case "statistics":
        return "📊";
      case "publication":
        return "📄";
      case "navigation":
        return "🔗";
      default:
        return "📍";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-bps-50 to-bps-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-bps-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-bold text-gray-900">
                  AIDA
                </h1>
                <p className="text-xs sm:text-sm text-bps-600">
                  AI Data Assistant - BPS Kota Medan
                </p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
              ></div>
              <span
                className={`text-xs ${isConnected ? "text-green-600" : "text-red-600"}`}
              >
                {isConnected ? "Terhubung" : "Terputus"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <Card className="h-[calc(100vh-120px)] sm:h-[600px] flex flex-col bg-white shadow-lg">
          {/* Chat Header */}
          <div className="p-3 sm:p-4 border-b bg-bps-50">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-bps-600 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <h2 className="text-sm sm:text-base font-semibold text-gray-900">
                  AIDA Assistant
                </h2>
                <p className="text-xs sm:text-sm text-bps-600">
                  Pencarian real-time dengan AI & Web Scraping
                </p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2 sm:gap-3 ${
                  message.type === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div
                  className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center flex-shrink-0 ${getAvatarColor(message)}`}
                >
                  {getMessageIcon(message)}
                </div>
                <div
                  className={`max-w-[85%] sm:max-w-[80%] ${
                    message.type === "user" ? "text-right" : "text-left"
                  }`}
                >
                  <div
                    className={`p-2 sm:p-3 rounded-lg ${getMessageBubbleColor(message)}`}
                  >
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>
                    {message.links && message.links.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-medium text-gray-600">
                          Hasil pencarian ({message.links.length} link):
                        </p>
                        {message.links.map((link, index) => (
                          <div
                            key={index}
                            className="p-2 bg-white rounded border hover:shadow-sm transition-shadow"
                          >
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-start gap-2 hover:text-bps-600 transition-colors"
                            >
                              <span className="text-sm mt-0.5">
                                {getLinkTypeIcon(link.type)}
                              </span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1">
                                  <p className="font-medium text-sm truncate">
                                    {link.title}
                                  </p>
                                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                </div>
                                <p className="text-xs text-gray-600 mt-0.5">
                                  {link.description}
                                </p>
                                {link.type && (
                                  <span className="inline-block px-1.5 py-0.5 bg-bps-100 text-bps-700 text-xs rounded mt-1">
                                    {link.type}
                                  </span>
                                )}
                              </div>
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {message.timestamp.toLocaleTimeString("id-ID", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-2 sm:gap-3">
                <div className="w-6 h-6 sm:w-8 sm:h-8 bg-bps-600 rounded-full flex items-center justify-center">
                  <Search className="w-3 h-3 sm:w-4 sm:h-4 text-white animate-pulse" />
                </div>
                <div className="p-2 sm:p-3 bg-bps-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-bps-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-bps-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-bps-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">
                      Mencari dan menganalisis data...
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 sm:p-4 border-t">
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ketik kata kunci pencarian data (contoh: kemiskinan, penduduk, ekonomi)..."
                className="flex-1 text-sm"
                disabled={isTyping}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="bg-bps-600 hover:bg-bps-700 px-3"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Info Section */}
        <div className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-gray-600 px-2">
          <p>
            AIDA menggunakan AI dan web scraping real-time untuk mencari data
            dari website BPS Kota Medan
          </p>
          <p className="mt-1">
            Didukung oleh OpenAI/Ollama dan Python BeautifulSoup untuk hasil
            pencarian yang akurat
          </p>
        </div>
      </div>
    </div>
  );
}