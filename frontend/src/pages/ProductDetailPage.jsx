import { useParams, useNavigate, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

function ProductDetailPage({ setCartCount }) {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [relatedProducts, setRelatedProducts] = useState([]);

  useEffect(() => {
    setLoading(true);
    setQuantity(1);
    setMessage('');
    setError('');
    setRelatedProducts([]);
    api.getProduct(slug).then((data) => {
      setProduct(data);
      // Track this product view for AI recommendations
      if (data && data.id) {
        api.trackProductView(data.id);
      }
    }).catch(() => setError('Không tìm thấy sản phẩm.')).finally(() => setLoading(false));

    // Fetch related products
    api.getRelatedProducts(slug)
      .then((data) => setRelatedProducts(Array.isArray(data) ? data : []))
      .catch(() => setRelatedProducts([]));
  }, [slug]);

  const handleAddToCart = async () => {
    if (!localStorage.getItem('token')) { navigate('/login'); return; }
    try {
      const cart = await api.addToCart(product.id, quantity);
      setCartCount(cart.total_items || 0);
      setMessage('Đã thêm vào giỏ hàng!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.error || 'Không thể thêm vào giỏ hàng.');
      setTimeout(() => setError(''), 3000);
    }
  };

  const renderStars = (r) => '★'.repeat(Math.floor(r)) + '☆'.repeat(5 - Math.floor(r));

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  if (!product) return <div className="empty-state" style={{ paddingTop: '150px' }}><h3>Không tìm thấy sản phẩm</h3></div>;

  return (
    <div className="product-detail-page">
      <div className="container">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/">Trang chủ</Link>
          <span className="breadcrumb-sep">/</span>
          <Link to="/products">Sản phẩm</Link>
          <span className="breadcrumb-sep">/</span>
          <span>{product.name}</span>
        </div>

        <div className="product-detail-card">
          <div className="product-detail-grid">
            {/* Image */}
            <div className="product-detail-image">
              <img src={product.image_url || `https://placehold.co/600x600/f8fafc/334155?text=${encodeURIComponent(product.name)}`}
                alt={product.name} />
              {product.discount_percent > 0 && (
                <div className="product-detail-discount">-{product.discount_percent}%</div>
              )}
            </div>

            {/* Info */}
            <div className="product-detail-info">
              {product.category?.name && (
                <div className="product-detail-category">{product.category.name}</div>
              )}
              <h1 className="product-detail-name">{product.name}</h1>
              
              <div className="product-detail-meta">
                <div className="product-detail-rating">
                  <span className="stars">{renderStars(product.rating)}</span>
                  <span className="rating-text">{product.rating}</span>
                </div>
                <span className="product-detail-divider">|</span>
                <span className="product-detail-reviews">{product.num_reviews} đánh giá</span>
                <span className="product-detail-divider">|</span>
                <span className="product-detail-sold">Đã bán {product.num_reviews}</span>
              </div>

              <div className="product-detail-price-box">
                <span className="product-detail-price">{formatVND(product.price)}</span>
                {product.compare_price && (
                  <>
                    <span className="product-detail-compare">{formatVND(product.compare_price)}</span>
                    {product.discount_percent > 0 && (
                      <span className="product-detail-save">Tiết kiệm {product.discount_percent}%</span>
                    )}
                  </>
                )}
              </div>

              <div className="product-detail-desc">
                <h3>Mô tả sản phẩm</h3>
                <p>{product.description}</p>
              </div>

              <div className={`product-detail-stock ${product.is_in_stock ? 'in-stock' : 'out-stock'}`}>
                {product.is_in_stock ? `✓ Còn hàng (${product.stock} sản phẩm)` : '✕ Hết hàng'}
              </div>

              {message && <div className="alert alert-success">{message}</div>}
              {error && <div className="alert alert-error">{error}</div>}

              <div className="product-detail-actions">
                <div className="product-detail-qty">
                  <span>Số lượng</span>
                  <div className="quantity-control">
                    <button onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</button>
                    <span>{quantity}</span>
                    <button onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}>+</button>
                  </div>
                </div>
                <div className="product-detail-btns">
                  <button className="btn btn-primary btn-lg" style={{ flex: 1 }} onClick={handleAddToCart}
                    disabled={!product.is_in_stock} id="add-to-cart-button">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" style={{marginRight: 8, verticalAlign: 'middle'}}>
                      <circle cx="9" cy="20" r="1"></circle>
                      <circle cx="18" cy="20" r="1"></circle>
                      <path d="M2 3h2l2.7 11.5a2 2 0 0 0 2 1.5h8.9a2 2 0 0 0 1.9-1.4L22 7H6"></path>
                    </svg>
                    Thêm vào giỏ hàng
                  </button>
                </div>
              </div>

              {/* Trust badges */}
              <div className="product-detail-trust">
                <div className="trust-item">🚚 Miễn phí vận chuyển</div>
                <div className="trust-item">🔄 Đổi trả 30 ngày</div>
                <div className="trust-item">🛡️ Bảo hành chính hãng</div>
              </div>
            </div>
          </div>
        </div>

        {/* Related Products Section */}
        {relatedProducts.length > 0 && (
          <div className="related-products-section">
            <div className="related-products-header">
              <h2 className="related-products-title">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 8, verticalAlign: 'middle' }}>
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                Sản phẩm liên quan
              </h2>
              <span className="related-products-count">{relatedProducts.length} sản phẩm cùng danh mục</span>
            </div>
            <div className="related-products-grid">
              {relatedProducts.map((rp) => (
                <Link to={`/products/${rp.slug}`} key={rp.id} className="product-card" id={`related-${rp.id}`}>
                  {rp.discount_percent > 0 && (
                    <div className="product-card-badge">-{rp.discount_percent}%</div>
                  )}
                  <div className="product-card-image">
                    <img src={rp.image_url || `https://placehold.co/300x300/f8fafc/334155?text=${encodeURIComponent(rp.name)}`}
                      alt={rp.name} loading="lazy" />
                  </div>
                  <div className="product-card-body">
                    <div className="product-card-category">{rp.category_name}</div>
                    <h3 className="product-card-name">{rp.name}</h3>
                    <div className="product-card-rating">
                      <span className="stars">{'★'.repeat(Math.floor(rp.rating))}</span>
                      <span className="rating-value">{rp.rating}</span>
                      <span className="sold-count">Đã bán {rp.num_reviews}</span>
                    </div>
                    <div className="product-card-price">
                      <span className="current">{formatVND(rp.price)}</span>
                      {rp.compare_price && (
                        <span className="original">{formatVND(rp.compare_price)}</span>
                      )}
                    </div>
                    <div className={`product-card-stock ${rp.is_in_stock ? 'in-stock' : 'out-stock'}`}>
                      {rp.is_in_stock ? '✓ Còn hàng' : '✕ Hết hàng'}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProductDetailPage;
