const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getToken() {
    return localStorage.getItem('token');
  }

  getHeaders(auth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth) {
      const token = this.getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, ...data };
    }
    return data;
  }

  // Auth
  async register(userData) {
    return this.request(`${this.baseUrl}/users/register/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(userData),
    });
  }

  async login(credentials) {
    return this.request(`${this.baseUrl}/users/login/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(credentials),
    });
  }

  async getProfile() {
    return this.request(`${this.baseUrl}/users/profile/`, {
      headers: this.getHeaders(true),
    });
  }

  // Products
  async getProducts(params = '') {
    return this.request(`${this.baseUrl}/products/${params ? '?' + params : ''}`, {
      headers: this.getHeaders(),
    });
  }

  async getProduct(slug) {
    return this.request(`${this.baseUrl}/products/${slug}/`, {
      headers: this.getHeaders(),
    });
  }

  async getCategories() {
    return this.request(`${this.baseUrl}/products/categories/`, {
      headers: this.getHeaders(),
    });
  }

  // Cart
  async getCart() {
    return this.request(`${this.baseUrl}/cart/`, {
      headers: this.getHeaders(true),
    });
  }

  async addToCart(productId, quantity = 1) {
    return this.request(`${this.baseUrl}/cart/add/`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  }

  async updateCartItem(itemId, quantity) {
    return this.request(`${this.baseUrl}/cart/items/${itemId}/`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify({ quantity }),
    });
  }

  async removeCartItem(itemId) {
    return this.request(`${this.baseUrl}/cart/items/${itemId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(true),
    });
  }

  // Orders
  async getOrders() {
    return this.request(`${this.baseUrl}/orders/`, {
      headers: this.getHeaders(true),
    });
  }

  async createOrder(orderData) {
    return this.request(`${this.baseUrl}/orders/create/`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(orderData),
    });
  }

  async getOrder(orderId) {
    return this.request(`${this.baseUrl}/orders/${orderId}/`, {
      headers: this.getHeaders(true),
    });
  }

  // Payments
  async createPayment(paymentData) {
    return this.request(`${this.baseUrl}/payments/create/`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(paymentData),
    });
  }

  async getPayments() {
    return this.request(`${this.baseUrl}/payments/`, {
      headers: this.getHeaders(true),
    });
  }
}

export default new ApiService();
