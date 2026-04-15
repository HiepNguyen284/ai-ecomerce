import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';

function HomePage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [prodData, catData] = await Promise.allSettled([
          api.getProducts('page_size=50'),
          api.getCategories(),
        ]);
        if (prodData.status === 'fulfilled') {
          setProducts(prodData.value.results || prodData.value || []);
        }
        if (catData.status === 'fulfilled') {
          setCategories(catData.value || []);
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const categoryIcons = {
    'Smartphones': '📱', 'Laptops': '💻', 'Audio': '🎧',
    'Clothing': '👕', 'Shoes': '👟', 'Home Appliances': '🏠',
    'Kitchen': '🍳', 'Books': '📚', 'Gaming': '🎮',
    'Watches': '⌚', 'Sports & Fitness': '🏋️', 'Beauty & Care': '💄',
  };

  const renderStars = (rating) => {
    const full = Math.floor(rating);
    return '★'.repeat(full) + '☆'.repeat(5 - full);
  };

  // Group products by category
  const productsByCategory = {};
  products.forEach((p) => {
    const cat = p.category_name || 'Other';
    if (!productsByCategory[cat]) productsByCategory[cat] = [];
    productsByCategory[cat].push(p);
  });

  return (
    <>
      {/* Hero */}
      <section className="hero" id="hero-section">
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">🚀 New Collection 2026</div>
            <h1>
              Discover Your
              <br />
              <span className="gradient-text">Perfect Style</span>
            </h1>
            <p>
              Explore our curated collection of premium products across 12+ categories.
              From cutting-edge tech to timeless fashion — all in one place.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-primary btn-lg" id="shop-now-button">
                Shop Now →
              </Link>
              <Link to="/register" className="btn btn-secondary btn-lg" id="join-button">
                Join Free
              </Link>
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <h3>12+</h3>
                <p>Categories</p>
              </div>
              <div className="hero-stat">
                <h3>24+</h3>
                <p>Premium Products</p>
              </div>
              <div className="hero-stat">
                <h3>99%</h3>
                <p>Satisfaction Rate</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Grid */}
      <section className="section" id="categories-section">
        <div className="container">
          <div className="section-header">
            <h2>Shop by Category</h2>
            <p>Browse our 12 carefully curated categories</p>
          </div>
          <div className="categories-grid">
            {categories.map((cat) => (
              <Link to={`/products?category=${cat.id}`} key={cat.id} className="category-card">
                <div className="category-card-icon">
                  {categoryIcons[cat.name] || '🛍️'}
                </div>
                <h3>{cat.name}</h3>
                <p>{cat.product_count || 0} products</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Products by Category */}
      {loading ? (
        <div className="loading-spinner"><div className="spinner"></div></div>
      ) : (
        Object.entries(productsByCategory).map(([catName, catProducts], idx) => (
          <section
            className="section"
            key={catName}
            id={`category-${catName.toLowerCase().replace(/\s+/g, '-')}`}
            style={{ background: idx % 2 === 0 ? 'var(--color-bg-secondary)' : 'transparent' }}
          >
            <div className="container">
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', marginBottom: 'var(--space-2xl)',
              }}>
                <div>
                  <h2 style={{ fontSize: '1.6rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <span>{categoryIcons[catName] || '🛍️'}</span> {catName}
                  </h2>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.95rem', marginTop: '4px' }}>
                    {catProducts.length} products available
                  </p>
                </div>
                <Link to={`/products?search=${encodeURIComponent(catName)}`} className="btn btn-secondary btn-sm">
                  View All →
                </Link>
              </div>
              <div className="product-grid">
                {catProducts.map((product) => (
                  <Link to={`/products/${product.slug}`} key={product.id} className="product-card">
                    {product.discount_percent > 0 && (
                      <div className="product-card-badge">-{product.discount_percent}%</div>
                    )}
                    <div className="product-card-image">
                      <img src={product.image_url || `https://placehold.co/600x400/1a1a2e/eee?text=${encodeURIComponent(product.name)}`} alt={product.name} />
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
                          <span className="current">${product.price}</span>
                          {product.compare_price && (
                            <span className="original">${product.compare_price}</span>
                          )}
                        </div>
                        <button className="btn btn-primary btn-sm">View</button>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        ))
      )}

      {/* CTA */}
      <section className="section" id="cta-section">
        <div className="container" style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 900, marginBottom: 'var(--space-md)' }}>
            Ready to Start <span style={{
              background: 'var(--gradient-primary)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>Shopping?</span>
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', marginBottom: 'var(--space-xl)', maxWidth: '500px', margin: '0 auto var(--space-xl)' }}>
            Join thousands of satisfied customers and discover premium products at unbeatable prices.
          </p>
          <Link to="/register" className="btn btn-accent btn-lg">
            Create Free Account →
          </Link>
        </div>
      </section>
    </>
  );
}

export default HomePage;
