import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">✦ ShopVerse</div>
            <p>Điểm đến mua sắm cao cấp với bộ sưu tập sản phẩm chất lượng. Trải nghiệm mua sắm hiện đại với giao hàng nhanh chóng.</p>
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
