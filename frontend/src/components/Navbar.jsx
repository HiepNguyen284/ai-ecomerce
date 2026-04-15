import { Link } from 'react-router-dom';

function Navbar({ user, cartCount, onLogout }) {
  return (
    <nav className="navbar" id="main-navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">✦ ShopVerse</Link>

        <ul className="navbar-nav">
          <li><Link to="/">Trang chủ</Link></li>
          <li><Link to="/products">Sản phẩm</Link></li>
          {user && <li><Link to="/orders">Đơn hàng</Link></li>}
          {user && user.is_staff && <li><Link to="/admin" style={{ color: 'var(--color-accent)' }}>⚙ Quản trị</Link></li>}
        </ul>

        <div className="navbar-actions">
          <Link to="/cart" className="btn-icon cart-button" title="Giỏ hàng" id="cart-button" aria-label="Giỏ hàng">
            <svg className="cart-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="9" cy="20" r="1"></circle>
              <circle cx="18" cy="20" r="1"></circle>
              <path d="M2 3h2l2.7 11.5a2 2 0 0 0 2 1.5h8.9a2 2 0 0 0 1.9-1.4L22 7H6"></path>
            </svg>
            {cartCount > 0 && <span className="cart-badge">{cartCount > 99 ? '99+' : cartCount}</span>}
          </Link>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                Xin chào, {user.first_name || user.username}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={onLogout} id="logout-button">
                Đăng xuất
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary btn-sm" id="login-button">
              Đăng nhập
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
