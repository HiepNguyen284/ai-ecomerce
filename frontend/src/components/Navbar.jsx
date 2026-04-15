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
          <Link to="/cart" className="btn-icon" title="Giỏ hàng" id="cart-button" style={{ position: 'relative' }}>
            🛒 {cartCount > 0 && <span style={{
              position: 'absolute', top: '-4px', right: '-4px',
              background: 'var(--color-accent)', color: 'white',
              fontSize: '0.7rem', fontWeight: 700, borderRadius: '50%',
              width: '18px', height: '18px', display: 'flex',
              alignItems: 'center', justifyContent: 'center'
            }}>{cartCount}</span>}
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
