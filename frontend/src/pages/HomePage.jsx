import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

function HomePage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

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
