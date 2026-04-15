import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import ProductsPage from './pages/ProductsPage.jsx';
import ProductDetailPage from './pages/ProductDetailPage.jsx';
import CartPage from './pages/CartPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';
import AdminPage from './pages/AdminPage.jsx';
import ChatWidget from './components/ChatWidget.jsx';
import api from './services/api.js';

function AppContent({ user, setUser, cartCount, setCartCount, authReady, handleLogout }) {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="app">
      {!isAdminRoute && <Navbar user={user} cartCount={cartCount} onLogout={handleLogout} />}
      <main className={isAdminRoute ? 'admin-main' : ''}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:slug" element={<ProductDetailPage setCartCount={setCartCount} />} />
          <Route path="/cart" element={<CartPage user={user} setCartCount={setCartCount} authReady={authReady} />} />
          <Route path="/orders" element={<OrdersPage user={user} authReady={authReady} />} />
          <Route path="/login" element={<LoginPage onLogin={(userData, token) => {
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(userData));
            setUser(userData);
          }} />} />
          <Route path="/register" element={<RegisterPage onLogin={(userData, token) => {
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(userData));
            setUser(userData);
          }} />} />
          <Route path="/admin" element={<AdminPage user={user} authReady={authReady} onLogout={handleLogout} />} />
        </Routes>
      </main>
      {!isAdminRoute && <Footer />}
      {!isAdminRoute && <ChatWidget />}
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [cartCount, setCartCount] = useState(0);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function bootstrapAuth() {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');

      if (token && savedUser) {
        try {
          const parsedUser = JSON.parse(savedUser);
          if (isMounted) setUser(parsedUser);

          try {
            const cart = await api.getCart();
            if (isMounted) setCartCount(cart?.total_items || 0);
          } catch {
            if (isMounted) setCartCount(0);
          }
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }

      if (isMounted) setAuthReady(true);
    }

    bootstrapAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCartCount(0);
  };

  return (
    <Router>
      <AppContent
        user={user}
        setUser={setUser}
        cartCount={cartCount}
        setCartCount={setCartCount}
        authReady={authReady}
        handleLogout={handleLogout}
      />
    </Router>
  );
}

export default App;
