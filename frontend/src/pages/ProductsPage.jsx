import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';

function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [ordering, setOrdering] = useState('-created_at');

  useEffect(() => {
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (selectedCategory) params.set('category', selectedCategory);
    if (ordering) params.set('ordering', ordering);

    api.getProducts(params.toString())
      .then((data) => setProducts(data.results || data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, selectedCategory, ordering]);

  const renderStars = (rating) => {
    const full = Math.floor(rating);
    return '★'.repeat(full) + '☆'.repeat(5 - full);
  };

  return (
    <div className="section" style={{ paddingTop: '100px', minHeight: '100vh' }}>
      <div className="container fade-in">
        <div className="section-header" style={{ textAlign: 'left' }}>
          <h2>All Products</h2>
          <p>Browse our complete collection</p>
        </div>

        {/* Filters */}
        <div style={{
          display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-2xl)',
          flexWrap: 'wrap', alignItems: 'center'
        }}>
          <input
            type="text"
            className="form-control"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: '300px' }}
            id="search-input"
          />
          <select
            className="form-control"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ maxWidth: '200px' }}
            id="category-filter"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
          <select
            className="form-control"
            value={ordering}
            onChange={(e) => setOrdering(e.target.value)}
            style={{ maxWidth: '200px' }}
            id="sort-filter"
          >
            <option value="-created_at">Newest First</option>
            <option value="price">Price: Low to High</option>
            <option value="-price">Price: High to Low</option>
            <option value="-rating">Top Rated</option>
            <option value="name">Name A-Z</option>
          </select>
        </div>

        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🔍</div>
            <h3>No products found</h3>
            <p>Try adjusting your filters or search terms.</p>
          </div>
        ) : (
          <div className="product-grid">
            {products.map((product) => (
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
        )}
      </div>
    </div>
  );
}

export default ProductsPage;
