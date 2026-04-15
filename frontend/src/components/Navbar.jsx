import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

function Navbar({ user, cartCount, onLogout }) {
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) {
      navigate(`/products?search=${encodeURIComponent(search.trim())}`);
    }
  };

  return (
    <nav className="navbar" id="main-navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>
          ShopVerse
        </Link>

        <form className="navbar-search" onSubmit={handleSearch}>
          <input 
            type="text" 
            placeholder="Tìm kiếm sản phẩm, thương hiệu..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </button>
        </form>

        <div className="navbar-actions">
          {user && <Link to="/orders">Đơn hàng</Link>}
          {user && user.is_staff && <Link to="/admin">⚙ Quản trị</Link>}
          
          <Link to="/cart" className="cart-button" title="Giỏ hàng" id="cart-button" aria-label="Giỏ hàng">
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="9" cy="20" r="1"></circle>
              <circle cx="18" cy="20" r="1"></circle>
              <path d="M2 3h2l2.7 11.5a2 2 0 0 0 2 1.5h8.9a2 2 0 0 0 1.9-1.4L22 7H6"></path>
            </svg>
            {cartCount > 0 && <span className="cart-badge">{cartCount > 99 ? '99+' : cartCount}</span>}
          </Link>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.9rem' }}>
                Chào, {user.first_name || user.username}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={onLogout} id="logout-button" style={{ border: 'none', background: 'transparent', color: 'white', fontWeight: 400, padding: 0 }}>
                Đăng xuất
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-secondary btn-sm" id="login-button" style={{ fontWeight: 500, color: 'var(--color-primary)' }}>
              Đăng nhập
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
