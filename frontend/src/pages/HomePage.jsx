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
              <section className="section" key={catName}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{categoryIcons[catName] || '🛍️'}</span> {catName}
                  </h2>
                  <Link to={`/products?search=${encodeURIComponent(catName)}`} style={{ color: 'var(--color-primary)', fontSize: '0.9rem', marginRight: '16px' }}>Xem tất cả →</Link>
                </div>
                <div className="product-grid">
                  {catProducts.map((product) => (
                    <Link to={`/products/${product.slug}`} key={product.id} className="product-card">
                      {product.discount_percent > 0 && <div className="product-card-badge">-{product.discount_percent}%</div>}
                      <div className="product-card-image">
                        <img src={product.image_url || `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`} alt={product.name} />
                      </div>
                      <div className="product-card-body">
                        <h3 className="product-card-name">{product.name}</h3>
                        <div className="product-card-rating">
                          <span className="stars">{renderStars(product.rating)}</span>
                          <span>(Đã bán {product.num_reviews})</span>
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

          <section className="section" id="cta-section" style={{ background: 'white', padding: '40px', borderRadius: '4px', textAlign: 'center', marginTop: '20px' }}>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 500, marginBottom: '10px' }}>
              Trải nghiệm mua sắm tuyệt vời cùng ShopVerse
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
              Tìm kiếm sản phẩm ưng ý với mức giá siêu ưu đãi ngay hôm nay.
            </p>
            <Link to="/register" className="btn btn-primary btn-lg" style={{ padding: '12px 30px', fontSize: '1.1rem' }}>Tham gia ngay</Link>
          </section>
        </main>
      </div>
  );
}

export default HomePage;
