import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">✦ ShopVerse</div>
            <p>Your premium destination for the finest products. Experience shopping reimagined with curated collections and lightning-fast delivery.</p>
          </div>
          <div>
            <h4>Shop</h4>
            <ul>
              <li><Link to="/products">All Products</Link></li>
              <li><Link to="/products?category=electronics">Electronics</Link></li>
              <li><Link to="/products?category=clothing">Clothing</Link></li>
              <li><Link to="/products?category=home">Home & Kitchen</Link></li>
            </ul>
          </div>
          <div>
            <h4>Account</h4>
            <ul>
              <li><Link to="/login">Sign In</Link></li>
              <li><Link to="/register">Register</Link></li>
              <li><Link to="/orders">My Orders</Link></li>
              <li><Link to="/cart">Shopping Cart</Link></li>
            </ul>
          </div>
          <div>
            <h4>Support</h4>
            <ul>
              <li><a href="#">Help Center</a></li>
              <li><a href="#">Shipping Info</a></li>
              <li><a href="#">Returns</a></li>
              <li><a href="#">Contact Us</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 ShopVerse. All rights reserved. Built with ♥ using microservices.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
