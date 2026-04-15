import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';

function ProductDetailPage({ setCartCount }) {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.getProduct(slug)
      .then(setProduct)
      .catch(() => setError('Product not found.'))
      .finally(() => setLoading(false));
  }, [slug]);

  const handleAddToCart = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    try {
      const cart = await api.addToCart(product.id, quantity);
      setCartCount(cart.total_items || 0);
      setMessage('Added to cart successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.error || 'Failed to add to cart.');
      setTimeout(() => setError(''), 3000);
    }
  };

  const renderStars = (rating) => {
    const full = Math.floor(rating);
    return '★'.repeat(full) + '☆'.repeat(5 - full);
  };

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  if (!product) return <div className="empty-state" style={{ paddingTop: '150px' }}><h3>Product not found</h3></div>;

  return (
    <div className="section" style={{ paddingTop: '100px', minHeight: '100vh' }}>
      <div className="container fade-in">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3xl)', alignItems: 'start' }}>
          {/* Image */}
          <div style={{
            borderRadius: 'var(--radius-xl)',
            overflow: 'hidden',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
          }}>
            <img
              src={product.image_url || `https://placehold.co/600x600/1a1a2e/eee?text=${encodeURIComponent(product.name)}`}
              alt={product.name}
              style={{ width: '100%', height: '500px', objectFit: 'cover' }}
            />
          </div>

          {/* Info */}
          <div>
            <div className="product-card-category" style={{ fontSize: '0.85rem', marginBottom: 'var(--space-sm)' }}>
              {product.category?.name}
            </div>

            <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 'var(--space-md)' }}>
              {product.name}
            </h1>

            <div className="product-card-rating" style={{ fontSize: '1rem', marginBottom: 'var(--space-lg)' }}>
              <span className="stars">{renderStars(product.rating)}</span>
              <span>{product.rating} ({product.num_reviews} reviews)</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
              <span style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--color-text-bright)' }}>
                ${product.price}
              </span>
              {product.compare_price && (
                <>
                  <span style={{ fontSize: '1.2rem', color: 'var(--color-text-muted)', textDecoration: 'line-through' }}>
                    ${product.compare_price}
                  </span>
                  {product.discount_percent > 0 && (
                    <span style={{
                      padding: '0.3rem 0.8rem',
                      background: 'rgba(255, 71, 87, 0.15)',
                      color: 'var(--color-danger)',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                    }}>
                      Save {product.discount_percent}%
                    </span>
                  )}
                </>
              )}
            </div>

            <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.8, marginBottom: 'var(--space-xl)' }}>
              {product.description}
            </p>

            <div style={{
              padding: 'var(--space-md) var(--space-lg)',
              background: product.is_in_stock ? 'rgba(0, 201, 167, 0.08)' : 'rgba(255, 71, 87, 0.08)',
              border: `1px solid ${product.is_in_stock ? 'rgba(0, 201, 167, 0.2)' : 'rgba(255, 71, 87, 0.2)'}`,
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--space-xl)',
              fontSize: '0.9rem',
              fontWeight: 600,
              color: product.is_in_stock ? 'var(--color-success)' : 'var(--color-danger)',
            }}>
              {product.is_in_stock ? `✓ In Stock (${product.stock} available)` : '✕ Out of Stock'}
            </div>

            {message && <div className="alert alert-success">{message}</div>}
            {error && <div className="alert alert-error">{error}</div>}

            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'center' }}>
              <div className="quantity-control">
                <button onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</button>
                <span>{quantity}</span>
                <button onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}>+</button>
              </div>
              <button
                className="btn btn-primary btn-lg"
                style={{ flex: 1 }}
                onClick={handleAddToCart}
                disabled={!product.is_in_stock}
                id="add-to-cart-button"
              >
                🛒 Add to Cart
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductDetailPage;
