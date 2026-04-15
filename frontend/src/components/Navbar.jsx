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

  const handleLogoutClick = () => {
    onLogout();
    navigate('/');
  };

  return (
    <>
      {/* Top bar */}
      <div className="top-bar">
        <div className="container top-bar-inner">
          <div className="top-bar-left">
          </div>
          <div className="top-bar-right">
            {user ? (
              <>
                <span>Xin chào, <strong>{user.username || user.first_name}</strong></span>
                <span className="top-bar-divider">|</span>
                <button className="top-bar-link" onClick={handleLogoutClick}>Đăng xuất</button>
              </>
            ) : (
              <>
                <Link to="/login" className="top-bar-link">Đăng nhập</Link>
                <span className="top-bar-divider">|</span>
                <Link to="/register" className="top-bar-link">Đăng ký</Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main navbar */}
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
            <Link to="/" className="navbar-action-item" title="Trang chủ">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
              <span>Trang chủ</span>
            </Link>

            {user && (
              <Link to="/orders" className="navbar-action-item" title="Đơn hàng">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                <span>Đơn hàng</span>
              </Link>
            )}
            
            <Link to="/cart" className="navbar-action-item cart-button" title="Giỏ hàng" id="cart-button" aria-label="Giỏ hàng">
              <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="9" cy="20" r="1"></circle>
                <circle cx="18" cy="20" r="1"></circle>
                <path d="M2 3h2l2.7 11.5a2 2 0 0 0 2 1.5h8.9a2 2 0 0 0 1.9-1.4L22 7H6"></path>
              </svg>
              <span>Giỏ hàng</span>
              {cartCount > 0 && <span className="cart-badge">{cartCount > 99 ? '99+' : cartCount}</span>}
            </Link>
          </div>
        </div>
      </nav>
    </>
  );
}

export default Navbar;
