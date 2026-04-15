import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

function HomePage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState(null);
  const [recLoading, setRecLoading] = useState(true);

  const normalizeList = (payload) => {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.results)) return payload.results;
    return [];
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [prodData, catData] = await Promise.allSettled([
          api.getProducts('page_size=300'),
          api.getCategories(),
        ]);
        if (prodData.status === 'fulfilled') setProducts(normalizeList(prodData.value));
        if (catData.status === 'fulfilled') setCategories(normalizeList(catData.value));
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    }
    fetchData();
  }, []);

  // Fetch personalized recommendations from DL engine
  useEffect(() => {
    async function fetchRecommendations() {
      try {
        const data = await api.getRecommendations();
        if (data && data.recommended_products && data.recommended_products.length > 0) {
          setRecommendations(data);
        }
      } catch (err) {
        console.debug('Recommendations not available:', err);
      } finally {
        setRecLoading(false);
      }
    }
    fetchRecommendations();
  }, []);

  const categoryIcons = {
    'Điện thoại': '📱', 'Laptop': '💻', 'Âm thanh': '🎧',
    'Quần': '👖', 'Áo': '👕', 'Giầy': '👟',
    'Đồ gia dụng': '🏠', 'Sách': '📚', 'Đồng hồ': '⌚',
    'Ô tô': '🚗', 'Mỹ phẩm': '💄', 'Túi xách': '👜',
  };

  const renderStars = (rating) => '★'.repeat(Math.floor(rating)) + '☆'.repeat(5 - Math.floor(rating));

  const productsByCategory = {};
  products.forEach((p) => {
    const cat = p.category_name || 'Khác';
    if (!productsByCategory[cat]) productsByCategory[cat] = [];
    productsByCategory[cat].push(p);
  });

  // Check if we have personalized recommendations (not just popular)
  const hasPersonalized = recommendations
    && recommendations.analysis
    && recommendations.analysis.type === 'personalized'
    && recommendations.recommended_products
    && recommendations.recommended_products.length > 0;

  return (
      <div className="homepage-layout">
        <aside className="categories-sidebar">
          <div className="sidebar-header">
            <h2>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight: 6, verticalAlign: 'middle'}}>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
              Danh mục
            </h2>
          </div>
          <div className="categories-vertical-list">
            {categories.map((cat) => (
              <Link to={`/products?category=${cat.id}`} key={cat.id} className="category-list-item">
                <span className="category-icon">{categoryIcons[cat.name] || '🛍️'}</span>
                <span className="category-name">{cat.name}</span>
                <span className="category-count">{cat.product_count || 0}</span>
              </Link>
            ))}
          </div>
        </aside>

        <main className="homepage-content">
          {/* Hero Banner */}
          <section className="hero-banner" id="hero-section">
            <div className="hero-banner-slide">
              <div className="hero-banner-content">
                <div className="hero-badge">🔥 FLASH SALE</div>
                <h1>Siêu Sale<br /><span className="gradient-text">Giảm đến 50%</span></h1>
                <p>Mua sắm ngay hàng ngàn sản phẩm chất lượng với giá ưu đãi cực sốc.</p>
                <div className="hero-actions">
                  <Link to="/products" className="btn btn-primary btn-lg" id="shop-now-button">Mua ngay →</Link>
                </div>
              </div>
              <div className="hero-banner-features">
                <div className="hero-feature">
                  <span className="hero-feature-icon">🚚</span>
                  <span>Miễn phí ship</span>
                </div>
                <div className="hero-feature">
                  <span className="hero-feature-icon">✅</span>
                  <span>Chính hãng 100%</span>
                </div>
                <div className="hero-feature">
                  <span className="hero-feature-icon">↩️</span>
                  <span>Đổi trả dễ dàng</span>
                </div>
                <div className="hero-feature">
                  <span className="hero-feature-icon">💳</span>
                  <span>Thanh toán an toàn</span>
                </div>
              </div>
            </div>
          </section>

          {/* Category Icons Row */}
          <section className="category-icons-section">
            {categories.slice(0, 10).map((cat) => (
              <Link to={`/products?category=${cat.id}`} key={cat.id} className="category-icon-card">
                <div className="category-icon-circle">
                  {categoryIcons[cat.name] || '🛍️'}
                </div>
                <span className="category-icon-label">{cat.name}</span>
              </Link>
            ))}
          </section>

          {/* ====== AI Personalized Recommendations ====== */}
          {hasPersonalized && (
            <section className="section recommendation-section" id="ai-recommendations">
              <div className="section-title-bar recommendation-title-bar">
                <h2>
                  <span className="section-title-icon ai-icon">🤖</span>
                  <span className="ai-title-text">Gợi ý cho bạn</span>
                  <span className="ai-badge">AI</span>
                </h2>
                <div className="recommendation-meta">
                  {recommendations.analysis.top_categories && recommendations.analysis.top_categories.length > 0 && (
                    <div className="rec-categories-tags">
                      {recommendations.analysis.top_categories.slice(0, 3).map((cat, i) => (
                        <span key={i} className="rec-category-tag">
                          {categoryIcons[cat] || '🏷️'} {cat}
                        </span>
                      ))}
                    </div>
                  )}
                  <span className="rec-info">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Dựa trên {recommendations.analysis.total_views} lượt xem
                  </span>
                </div>
              </div>

              {/* Category preference progress bars */}
              {recommendations.category_preferences && recommendations.category_preferences.length > 0 && (
                <div className="preference-indicators">
                  {recommendations.category_preferences.slice(0, 5).map((pref, i) => (
                    <div key={i} className="preference-bar-item">
                      <div className="preference-bar-label">
                        <span>{categoryIcons[pref.category_name] || '📦'} {pref.category_name}</span>
                        <span className="preference-bar-count">{pref.view_count} lượt xem</span>
                      </div>
                      <div className="preference-bar-track">
                        <div
                          className="preference-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(8, (pref.view_count / Math.max(1, recommendations.analysis.total_views)) * 100))}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="product-grid">
                {recommendations.recommended_products.map((product) => (
                  <Link to={`/products/${product.slug}`} key={product.id} className="product-card recommendation-card">
                    <div className="rec-badge-ai">AI Pick</div>
                    {product.discount_percent > 0 && <div className="product-card-badge">-{product.discount_percent}%</div>}
                    <div className="product-card-image">
                      <img src={product.image_url || `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`} alt={product.name}
                        onError={(e) => { e.target.onerror = null; e.target.src = `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`; }} />
                    </div>
                    <div className="product-card-body">
                      <h3 className="product-card-name">{product.name}</h3>
                      <div className="product-card-rating">
                        <span className="stars">{renderStars(product.rating)}</span>
                        <span>Đã bán {product.num_reviews}</span>
                      </div>
                      <div className="product-card-price">
                          <span className="current">{formatVND(product.price)}</span>
                          {product.compare_price && <span className="original">{formatVND(product.compare_price)}</span>}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Loading shimmer for recommendations */}
          {recLoading && (
            <section className="section recommendation-section recommendation-loading">
              <div className="section-title-bar recommendation-title-bar">
                <h2>
                  <span className="section-title-icon ai-icon">🤖</span>
                  <span className="ai-title-text">Đang phân tích...</span>
                  <span className="ai-badge pulse-badge">AI</span>
                </h2>
              </div>
              <div className="product-grid">
                {[1,2,3,4].map((i) => (
                  <div key={i} className="product-card shimmer-card">
                    <div className="shimmer-image"></div>
                    <div className="shimmer-body">
                      <div className="shimmer-line w75"></div>
                      <div className="shimmer-line w50"></div>
                      <div className="shimmer-line w60"></div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : (
            Object.entries(productsByCategory).map(([catName, catProducts]) => (
              <section className="section" key={catName}>
                <div className="section-title-bar">
                  <h2>
                    <span className="section-title-icon">{categoryIcons[catName] || '🛍️'}</span>
                    {catName}
                  </h2>
                  <Link to={`/products?category=${categories.find(c => c.name === catName)?.id || ''}`} className="section-view-all">Xem tất cả →</Link>
                </div>
                <div className="product-grid">
                  {catProducts.map((product) => (
                    <Link to={`/products/${product.slug}`} key={product.id} className="product-card">
                      {product.discount_percent > 0 && <div className="product-card-badge">-{product.discount_percent}%</div>}
                      <div className="product-card-image">
                        <img src={product.image_url || `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`} alt={product.name}
                          onError={(e) => { e.target.onerror = null; e.target.src = `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`; }} />
                      </div>
                      <div className="product-card-body">
                        <h3 className="product-card-name">{product.name}</h3>
                        <div className="product-card-rating">
                          <span className="stars">{renderStars(product.rating)}</span>
                          <span>Đã bán {product.num_reviews}</span>
                        </div>
                        <div className="product-card-price">
                            <span className="current">{formatVND(product.price)}</span>
                            {product.compare_price && <span className="original">{formatVND(product.compare_price)}</span>}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            ))
          )}
        </main>
      </div>
  );
}

export default HomePage;
