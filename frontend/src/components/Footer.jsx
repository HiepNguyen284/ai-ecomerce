import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        {/* Trust badges */}
        <div className="footer-trust">
          <div className="footer-trust-item">
            <span className="footer-trust-icon">🚚</span>
            <div>
              <strong>Miễn phí vận chuyển</strong>
              <span>Đơn hàng từ 500.000₫</span>
            </div>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon">🔄</span>
            <div>
              <strong>Đổi trả miễn phí</strong>
              <span>Trong vòng 30 ngày</span>
            </div>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon">🛡️</span>
            <div>
              <strong>Bảo hành chính hãng</strong>
              <span>Sản phẩm chính hãng 100%</span>
            </div>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon">📞</span>
            <div>
              <strong>Hỗ trợ 24/7</strong>
              <span>Tư vấn miễn phí</span>
            </div>
          </div>
        </div>

        <div className="footer-grid">
          <div>
            <div className="footer-brand">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="24" height="24">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <path d="M16 10a4 4 0 0 1-8 0"></path>
              </svg>
              ShopVerse
            </div>
            <p>Điểm đến mua sắm cao cấp với bộ sưu tập sản phẩm chất lượng. Trải nghiệm mua sắm hiện đại với giao hàng nhanh chóng.</p>
            <div className="footer-social">
              <a href="#" className="footer-social-btn" title="Facebook">📘</a>
              <a href="#" className="footer-social-btn" title="Instagram">📷</a>
              <a href="#" className="footer-social-btn" title="YouTube">📺</a>
              <a href="#" className="footer-social-btn" title="TikTok">🎵</a>
            </div>
          </div>
          <div>
            <h4>Mua sắm</h4>
            <ul>
              <li><Link to="/products">Tất cả sản phẩm</Link></li>
              <li><Link to="/products?category=electronics">Điện tử</Link></li>
              <li><Link to="/products?category=clothing">Thời trang</Link></li>
              <li><Link to="/products?category=home">Gia dụng</Link></li>
            </ul>
          </div>
          <div>
            <h4>Tài khoản</h4>
            <ul>
              <li><Link to="/login">Đăng nhập</Link></li>
              <li><Link to="/register">Đăng ký</Link></li>
              <li><Link to="/orders">Đơn hàng</Link></li>
              <li><Link to="/cart">Giỏ hàng</Link></li>
            </ul>
          </div>
          <div>
            <h4>Hỗ trợ</h4>
            <ul>
              <li><a href="#">Trung tâm trợ giúp</a></li>
              <li><a href="#">Thông tin vận chuyển</a></li>
              <li><a href="#">Đổi trả hàng</a></li>
              <li><a href="#">Liên hệ</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 ShopVerse. Bảo lưu mọi quyền. Xây dựng với ♥ bằng kiến trúc microservices.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
