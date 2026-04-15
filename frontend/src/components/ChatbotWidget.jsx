import { useState, useRef, useEffect, useCallback } from 'react';
import api from '../services/api.js';

const BOT_AVATAR = '🤖';
const USER_AVATAR = '👤';

const DEFAULT_SUGGESTIONS = [
  '📱 Tư vấn điện thoại dưới 15 triệu',
  '💻 Laptop tốt nhất cho lập trình',
  '🎧 Tai nghe chống ồn nào tốt?',
  '👟 Giày thể thao giá rẻ',
  '⌚ So sánh Apple Watch và Galaxy Watch',
  '🎮 Máy chơi game cho gia đình',
];

function formatPrice(price) {
  try {
    const p = parseInt(price, 10);
    return p.toLocaleString('vi-VN') + '₫';
  } catch {
    return price;
  }
}

function parseMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/_(.*?)_/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');
  return html;
}

function ProductCard({ product }) {
  const discount = product.discount_percent || 0;
  const rating = parseFloat(product.rating) || 0;
  const fullStars = Math.floor(rating);

  return (
    <a
      href={`/products/${product.slug}`}
      className="chatbot-product-card"
      target="_blank"
      rel="noopener noreferrer"
    >
      <div className="chatbot-product-img">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} loading="lazy" />
        ) : (
          <div className="chatbot-product-placeholder">📦</div>
        )}
        {discount > 0 && <span className="chatbot-product-discount">-{discount}%</span>}
      </div>
      <div className="chatbot-product-info">
        <p className="chatbot-product-name">{product.name}</p>
        <div className="chatbot-product-price-row">
          <span className="chatbot-product-price">{formatPrice(product.price)}</span>
          {product.compare_price && (
            <span className="chatbot-product-compare">{formatPrice(product.compare_price)}</span>
          )}
        </div>
        <div className="chatbot-product-rating">
          <span className="chatbot-stars">{'★'.repeat(fullStars)}{'☆'.repeat(5 - fullStars)}</span>
          <span className="chatbot-rating-text">{rating}/5</span>
        </div>
      </div>
    </a>
  );
}

function ChatMessage({ msg }) {
  const isBot = msg.role === 'assistant';
  return (
    <div className={`chatbot-msg ${isBot ? 'chatbot-msg-bot' : 'chatbot-msg-user'}`}>
      <div className="chatbot-msg-avatar">{isBot ? BOT_AVATAR : USER_AVATAR}</div>
      <div className="chatbot-msg-bubble">
        <div
          className="chatbot-msg-text"
          dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }}
        />
        {isBot && msg.products && msg.products.length > 0 && (
          <div className="chatbot-products-grid">
            {msg.products.map((p, i) => (
              <ProductCard key={p.id || i} product={p} />
            ))}
          </div>
        )}
        <span className="chatbot-msg-time">
          {msg.time || new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

export default function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! 👋 Mình là trợ lý mua sắm ShopVN.\n\nMình có thể giúp bạn tìm kiếm và tư vấn sản phẩm. Hãy hỏi mình bất cứ điều gì! 🛍️',
      products: [],
      time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [hasUnread, setHasUnread] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatBodyRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Fetch suggestions on mount
  useEffect(() => {
    async function fetchSuggestions() {
      try {
        const data = await api.getChatSuggestions();
        if (data.suggestions) setSuggestions(data.suggestions);
      } catch {
        // Use defaults
      }
    }
    fetchSuggestions();
  }, []);

  const sendMessage = async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || isLoading) return;

    const now = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

    const userMsg = { role: 'user', content: trimmed, products: [], time: now };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setShowSuggestions(false);

    try {
      const data = await api.sendChatMessage(trimmed, sessionId);
      if (data.session_id) setSessionId(data.session_id);

      const botMsg = {
        role: 'assistant',
        content: data.response || 'Xin lỗi, mình không thể xử lý yêu cầu của bạn lúc này.',
        products: data.products || [],
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);

      if (!isOpen) setHasUnread(true);
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: '😅 Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.',
        products: [],
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) setHasUnread(false);
  };

  const handleClear = async () => {
    if (sessionId) {
      try {
        await api.clearChatHistory(sessionId);
      } catch { /* ok */ }
    }
    setSessionId('');
    setMessages([
      {
        role: 'assistant',
        content: 'Xin chào! 👋 Mình là trợ lý mua sắm ShopVN.\n\nMình có thể giúp bạn tìm kiếm và tư vấn sản phẩm. Hãy hỏi mình bất cứ điều gì! 🛍️',
        products: [],
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setShowSuggestions(true);
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        id="chatbot-fab"
        className={`chatbot-fab ${isOpen ? 'chatbot-fab-active' : ''}`}
        onClick={handleToggle}
        aria-label="Toggle chatbot"
      >
        <span className="chatbot-fab-icon">
          {isOpen ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          )}
        </span>
        {hasUnread && !isOpen && <span className="chatbot-fab-badge" />}
        <span className="chatbot-fab-pulse" />
      </button>

      {/* Chat Window */}
      <div className={`chatbot-window ${isOpen ? 'chatbot-window-open' : ''}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <div className="chatbot-header-avatar">🤖</div>
            <div className="chatbot-header-info">
              <h3>Trợ lý ShopVN</h3>
              <span className="chatbot-header-status">
                <span className="chatbot-status-dot" /> Trực tuyến
              </span>
            </div>
          </div>
          <div className="chatbot-header-actions">
            <button className="chatbot-header-btn" onClick={handleClear} title="Xóa cuộc trò chuyện">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
            <button className="chatbot-header-btn" onClick={handleToggle} title="Đóng">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="4 14 10 14 10 20" />
                <polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="chatbot-body" ref={chatBodyRef}>
          {messages.map((msg, i) => (
            <ChatMessage key={i} msg={msg} />
          ))}

          {isLoading && (
            <div className="chatbot-msg chatbot-msg-bot">
              <div className="chatbot-msg-avatar">{BOT_AVATAR}</div>
              <div className="chatbot-msg-bubble">
                <div className="chatbot-typing">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          {/* Suggestions */}
          {showSuggestions && messages.length <= 1 && (
            <div className="chatbot-suggestions">
              <p className="chatbot-suggestions-title">💡 Gợi ý cho bạn:</p>
              <div className="chatbot-suggestions-list">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    className="chatbot-suggestion-chip"
                    onClick={() => sendMessage(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chatbot-footer">
          <div className="chatbot-input-wrap">
            <input
              ref={inputRef}
              type="text"
              className="chatbot-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi về sản phẩm..."
              disabled={isLoading}
              maxLength={1000}
            />
            <button
              className="chatbot-send-btn"
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              aria-label="Gửi"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <p className="chatbot-powered">Powered by Gemini AI ✨</p>
        </div>
      </div>
    </>
  );
}
