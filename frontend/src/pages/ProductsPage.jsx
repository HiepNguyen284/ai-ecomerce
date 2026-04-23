import { Link, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [ordering, setOrdering] = useState('-created_at');
  const [aiRecs, setAiRecs] = useState([]);

  const normalizeList = (payload) => {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.results)) return payload.results;
    return [];
  };

  useEffect(() => {
    api.getCategories().then((data) => setCategories(normalizeList(data))).catch(console.error);
  }, []);

  // Fetch AI recommendations
  useEffect(() => {
    fetch(`${API_BASE}/ai/recommendations/products/?limit=8`)
      .then(r => r.json())
      .then(data => setAiRecs(data.recommendations || []))
      .catch(() => setAiRecs([]));
  }, []);

  // Sync URL params → state when URL changes (e.g. navigating from HomePage)
  useEffect(() => {
    const urlCat = searchParams.get('category') || '';
    const urlSearch = searchParams.get('search') || '';
    if (urlCat !== selectedCategory) setSelectedCategory(urlCat);
    if (urlSearch !== search) setSearch(urlSearch);
  }, [searchParams]);

  // Sync state → URL when filters change
  useEffect(() => {
    const newParams = new URLSearchParams();
    if (selectedCategory) newParams.set('category', selectedCategory);
    if (search) newParams.set('search', search);
    setSearchParams(newParams, { replace: true });
  }, [selectedCategory, search]);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set('page_size', '300');
    if (search) params.set('search', search);
    if (selectedCategory) params.set('category', selectedCategory);
    if (ordering) params.set('ordering', ordering);
    api.getProducts(params.toString())
      .then((data) => setProducts(normalizeList(data)))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, selectedCategory, ordering]);

  const renderStars = (r) => '★'.repeat(Math.floor(r)) + '☆'.repeat(5 - Math.floor(r));

  return (
    <div className="products-page">
      <div className="container">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/">Trang chủ</Link>
          <span className="breadcrumb-sep">/</span>
          <span>Tất cả sản phẩm</span>
        </div>

        {/* ── AI Recommendations Banner ── */}
        {aiRecs.length > 0 && (
          <div className="ai-rec-section" id="ai-recommendations">
            <div className="ai-rec-header">
              <span className="ai-rec-badge">🧠 AI Gợi ý</span>
              <h3>Sản phẩm phổ biến nhất — Dựa trên Knowledge Graph</h3>
            </div>
            <div className="ai-rec-scroll">
              {aiRecs.map((rec, i) => (
                <Link to={`/products/${rec.slug || rec.id}`} key={rec.id} className="ai-rec-card">
                  <div className="ai-rec-rank">#{i + 1}</div>
                  <div className="ai-rec-info">
                    <span className="ai-rec-name">{rec.name}</span>
                    <span className="ai-rec-cat">{rec.category_name}</span>
                    <span className="ai-rec-stats">
                      🛒 {rec.buyers} mua · 👁 {rec.viewers} xem
                    </span>
                  </div>
                  {rec.price > 0 && (
                    <span className="ai-rec-price">{formatVND(rec.price)}</span>
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}

        <div className="products-layout">
          {/* Sidebar Filters */}
          <aside className="products-filter-sidebar">
            <div className="filter-section">
              <h3 className="filter-title">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
                Bộ lọc
              </h3>
            </div>
            <div className="filter-section">
              <h4>Danh mục</h4>
              <div className="filter-options">
                <label className={`filter-option ${!selectedCategory ? 'filter-option--active' : ''}`}>
                  <input type="radio" name="category" value="" checked={!selectedCategory} onChange={() => setSelectedCategory('')} />
                  Tất cả
                </label>
                {categories.map((cat) => (
                  <label key={cat.id} className={`filter-option ${selectedCategory === String(cat.id) ? 'filter-option--active' : ''}`}>
                    <input type="radio" name="category" value={cat.id} checked={selectedCategory === String(cat.id)} onChange={(e) => setSelectedCategory(e.target.value)} />
                    {cat.name}
                  </label>
                ))}
              </div>
            </div>
            <div className="filter-section">
              <h4>Sắp xếp theo</h4>
              <div className="filter-options">
                {[
                  { value: '-created_at', label: 'Mới nhất' },
                  { value: 'price', label: 'Giá: Thấp → Cao' },
                  { value: '-price', label: 'Giá: Cao → Thấp' },
                  { value: '-rating', label: 'Đánh giá cao nhất' },
                  { value: 'name', label: 'Tên A-Z' },
                ].map((opt) => (
                  <label key={opt.value} className={`filter-option ${ordering === opt.value ? 'filter-option--active' : ''}`}>
                    <input type="radio" name="ordering" value={opt.value} checked={ordering === opt.value} onChange={(e) => setOrdering(e.target.value)} />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>
          </aside>

          {/* Products Content */}
          <div className="products-content">
            <div className="products-toolbar">
              <div className="products-toolbar-left">
                <h1>Tất cả sản phẩm</h1>
                <span className="products-count">{products.length} sản phẩm</span>
              </div>
              <div className="products-toolbar-right">
                <div className="search-box">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <input type="text" placeholder="Tìm kiếm sản phẩm..."
                    value={search} onChange={(e) => setSearch(e.target.value)} id="search-input" />
                </div>
              </div>
            </div>
            
            {loading ? (
              <div className="loading-spinner"><div className="spinner"></div></div>
            ) : products.length === 0 ? (
              <div className="empty-state">
                <div className="icon">🔍</div>
                <h3>Không tìm thấy sản phẩm</h3>
                <p>Thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm.</p>
              </div>
            ) : (
              <div className="product-grid">
                {products.map((product) => (
                  <Link to={`/products/${product.slug}`} key={product.id} className="product-card">
                    {product.discount_percent > 0 && <div className="product-card-badge">-{product.discount_percent}%</div>}
                    <div className="product-card-image">
                      <img src={product.image_url || `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`} alt={product.name}
                        onError={(e) => { e.target.onerror = null; e.target.src = `https://placehold.co/600x400/f8fafc/334155?text=${encodeURIComponent(product.name)}`; }} />
                    </div>
                    <div className="product-card-body">
                      <div className="product-card-category">{product.category_name}</div>
                      <h3 className="product-card-name">{product.name}</h3>
                      <div className="product-card-rating">
                        <span className="stars">{renderStars(product.rating)}</span>
                        <span>({product.num_reviews})</span>
                      </div>
                      <div className="product-card-price">
                        <span className="current">{formatVND(product.price)}</span>
                        {product.compare_price && <span className="original">{formatVND(product.compare_price)}</span>}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductsPage;

