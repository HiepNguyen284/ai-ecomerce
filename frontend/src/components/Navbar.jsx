import { Link } from 'react-router-dom';

function Navbar({ user, cartCount, onLogout }) {
  return (
    <nav className="navbar" id="main-navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">✦ ShopVerse</Link>

        <ul className="navbar-nav">
          <li><Link to="/">Home</Link></li>
          <li><Link to="/products">Products</Link></li>
          {user && <li><Link to="/orders">Orders</Link></li>}
        </ul>

        <div className="navbar-actions">
          <Link to="/cart" className="btn-icon" title="Cart" id="cart-button">
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
                Hi, {user.first_name || user.username}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={onLogout} id="logout-button">
                Logout
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary btn-sm" id="login-button">
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
