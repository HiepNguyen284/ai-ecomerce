import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

/* ─── helpers ──────────────────────────────────────────────────────── */
function getSessionId() {
  let sid = localStorage.getItem('chatbot_session_id');
  if (!sid) {
    sid = 'sess_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem('chatbot_session_id', sid);
  }
  return sid;
}

function formatPrice(price) {
  try {
    return Number(price).toLocaleString('vi-VN') + 'đ';
  } catch {
    return price;
  }
}

/* ─── Chat Widget Component ───────────────────────────────────────── */
export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showWelcome, setShowWelcome] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load suggestions
  useEffect(() => {
    if (isOpen && suggestions.length === 0) {
      fetch(`${API_BASE}/chatbot/suggestions/`)
        .then(r => r.json())
        .then(data => setSuggestions(data.suggestions || []))
        .catch(() => {
          setSuggestions([
            'Tư vấn laptop cho văn phòng',
            'Điện thoại chụp ảnh đẹp',
            'Tai nghe chống ồn tốt nhất',
          ]);
        });
    }
  }, [isOpen, suggestions.length]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;

    const userMessage = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setShowWelcome(false);
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/chatbot/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: getSessionId(),
          ...(conversationId && { conversation_id: conversationId }),
        }),
      });

      if (!resp.ok) throw new Error('Chat request failed');

      const data = await resp.json();
      setConversationId(data.conversation_id);

      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        products: data.products || [],
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Xin lỗi, mình đang gặp sự cố kỹ thuật. Bạn vui lòng thử lại sau nhé! 🙏',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (text) => {
    sendMessage(text);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const resetChat = () => {
    setMessages([]);
    setConversationId(null);
    setShowWelcome(true);
  };

  return (
    <>
      {/* Floating Button */}
      <button
        className={`chatbot-fab ${isOpen ? 'chatbot-fab--open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Mở trợ lý AI"
        id="chatbot-toggle"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 2C6.48 2 2 5.92 2 10.5c0 2.47 1.32 4.68 3.41 6.17L4 22l4.59-2.29C9.67 19.9 10.82 20 12 20c5.52 0 10-3.42 10-7.5S17.52 2 12 2z"/>
            <circle cx="8" cy="10.5" r="1" fill="currentColor"/>
            <circle cx="12" cy="10.5" r="1" fill="currentColor"/>
            <circle cx="16" cy="10.5" r="1" fill="currentColor"/>
          </svg>
        )}
        {!isOpen && <span className="chatbot-fab-pulse" />}
      </button>

      {/* Chat Window */}
      <div className={`chatbot-window ${isOpen ? 'chatbot-window--open' : ''}`} id="chatbot-window">
        {/* Header */}
        <div className="chatbot-header">
          <div className="chatbot-header-info">
            <div className="chatbot-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2C6.48 2 2 5.92 2 10.5c0 2.47 1.32 4.68 3.41 6.17L4 22l4.59-2.29C9.67 19.9 10.82 20 12 20c5.52 0 10-3.42 10-7.5S17.52 2 12 2z"/>
              </svg>
            </div>
            <div>
              <h3 className="chatbot-header-title">Trợ lý AI ShopEase</h3>
              <span className="chatbot-header-status">
                <span className="chatbot-status-dot" /> Sẵn sàng tư vấn
              </span>
            </div>
          </div>
          <div className="chatbot-header-actions">
            <button onClick={resetChat} className="chatbot-header-btn" title="Cuộc trò chuyện mới">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
              </svg>
            </button>
            <button onClick={() => setIsOpen(false)} className="chatbot-header-btn" title="Đóng">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="chatbot-messages">
          {showWelcome && messages.length === 0 && (
            <div className="chatbot-welcome">
              <div className="chatbot-welcome-icon">🛍️</div>
              <h4>Xin chào! 👋</h4>
              <p>Mình là trợ lý AI của ShopEase. Mình có thể giúp bạn tìm sản phẩm, so sánh giá, và tư vấn mua hàng.</p>
              {suggestions.length > 0 && (
                <div className="chatbot-suggestions">
                  <p className="chatbot-suggestions-label">Gợi ý cho bạn:</p>
                  <div className="chatbot-suggestion-chips">
                    {suggestions.slice(0, 6).map((s, i) => (
                      <button
                        key={i}
                        className="chatbot-chip"
                        onClick={() => handleSuggestion(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`chatbot-message chatbot-message--${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="chatbot-message-avatar">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2C6.48 2 2 5.92 2 10.5c0 2.47 1.32 4.68 3.41 6.17L4 22l4.59-2.29C9.67 19.9 10.82 20 12 20c5.52 0 10-3.42 10-7.5S17.52 2 12 2z"/>
                  </svg>
                </div>
              )}
              <div className="chatbot-message-content">
                <div
                  className="chatbot-message-text"
                  dangerouslySetInnerHTML={{
                    __html: msg.content
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\n/g, '<br/>')
                  }}
                />
                {/* Product Cards */}
                {msg.products && msg.products.length > 0 && (
                  <div className="chatbot-products">
                    {msg.products.map((p, i) => (
                      <a
                        key={i}
                        href={`/products/${p.slug}`}
                        className="chatbot-product-card"
                        target="_self"
                      >
                        <div className="chatbot-product-img">
                          {p.image_url ? (
                            <img src={p.image_url} alt={p.name} />
                          ) : (
                            <div className="chatbot-product-img-placeholder">📦</div>
                          )}
                        </div>
                        <div className="chatbot-product-info">
                          <span className="chatbot-product-name">{p.name}</span>
                          <span className="chatbot-product-price">{formatPrice(p.price)}</span>
                          <span className="chatbot-product-rating">
                            ⭐ {p.rating}/5
                            {p.is_in_stock ? (
                              <span className="chatbot-stock chatbot-stock--in">Còn hàng</span>
                            ) : (
                              <span className="chatbot-stock chatbot-stock--out">Hết hàng</span>
                            )}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chatbot-message chatbot-message--assistant">
              <div className="chatbot-message-avatar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2C6.48 2 2 5.92 2 10.5c0 2.47 1.32 4.68 3.41 6.17L4 22l4.59-2.29C9.67 19.9 10.82 20 12 20c5.52 0 10-3.42 10-7.5S17.52 2 12 2z"/>
                </svg>
              </div>
              <div className="chatbot-message-content">
                <div className="chatbot-typing">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form className="chatbot-input-area" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            className="chatbot-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi về sản phẩm..."
            disabled={loading}
            maxLength={2000}
            id="chatbot-input"
          />
          <button
            type="submit"
            className="chatbot-send-btn"
            disabled={!input.trim() || loading}
            id="chatbot-send"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>
    </>
  );
}
