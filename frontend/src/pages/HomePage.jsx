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
    'Thời trang': '👕', 'Giày dép': '👟', 'Gia dụng': '🏠',
    'Nhà bếp': '🍳', 'Sách': '📚', 'Gaming': '🎮',
    'Đồng hồ': '⌚', 'Thể thao & Fitness': '🏋️', 'Làm đẹp': '💄',
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
            <h2>Danh mục sản phẩm</h2>
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
          <section className="hero" id="hero-section">
            <div className="hero-content">
              <div className="hero-badge">🚀 Bộ sưu tập mới 2026</div>
              <h1>Khám phá<br /><span className="gradient-text">Phong cách của bạn</span></h1>
              <p>Khám phá bộ sưu tập sản phẩm cao cấp với hơn 12 danh mục.</p>
              <div className="hero-actions">
                <Link to="/products" className="btn btn-primary btn-lg" id="shop-now-button">Mua sắm ngay →</Link>
                <Link to="/register" className="btn btn-secondary btn-lg" id="join-button">Đăng ký miễn phí</Link>
              </div>
            </div>
          </section>

          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : (
            Object.entries(productsByCategory).map(([catName, catProducts], idx) => (
              <section className="section" key={catName}
                style={{ background: idx % 2 === 0 ? 'var(--color-bg-secondary)' : 'transparent' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2xl)' }}>
                  <div>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                      <span>{categoryIcons[catName] || '🛍️'}</span> {catName}
                    </h2>
                    <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.95rem', marginTop: '4px' }}>{catProducts.length} sản phẩm</p>
                  </div>
                  <Link to={`/products?search=${encodeURIComponent(catName)}`} className="btn btn-secondary btn-sm">Xem tất cả →</Link>
                </div>
                <div className="product-grid">
                  {catProducts.map((product) => (
                    <Link to={`/products/${product.slug}`} key={product.id} className="product-card">
                      {product.discount_percent > 0 && <div className="product-card-badge">-{product.discount_percent}%</div>}
                      <div className="product-card-image">
                        <img src={product.image_url || `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`} alt={product.name} />
                      </div>
                      <div className="product-card-body">
                        <div className="product-card-category">{product.category_name}</div>
                        <h3 className="product-card-name">{product.name}</h3>
                        <div className="product-card-rating">
                          <span className="stars">{renderStars(product.rating)}</span>
                          <span>({product.num_reviews})</span>
                        </div>
                        <div className="product-card-footer">
                          <div className="product-card-price">
                              <span className="current">{formatVND(product.price)}</span>
                              {product.compare_price && <span className="original">{formatVND(product.compare_price)}</span>}
                          </div>
                          <button className="btn btn-primary btn-sm">Xem</button>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            ))
          )}

          <section className="section" id="cta-section">
            <div style={{ textAlign: 'center' }}>
              <h2 style={{ fontSize: '2.5rem', fontWeight: 900, marginBottom: 'var(--space-md)' }}>
                Sẵn sàng <span style={{ background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>mua sắm?</span>
              </h2>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', maxWidth: '500px', margin: '0 auto var(--space-xl)' }}>
                Tham gia cùng hàng ngàn khách hàng hài lòng và khám phá.
              </p>
              <Link to="/register" className="btn btn-accent btn-lg">Tạo tài khoản miễn phí →</Link>
            </div>
          </section>
        </main>
      </div>
  );
}

export default HomePage;
