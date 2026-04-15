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
    const contentType = response.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');

    let data = null;
    if (response.status !== 204) {
      if (isJson) {
        try {
          data = await response.json();
        } catch {
          data = null;
        }
      } else {
        data = await response.text();
      }
    }

    if (!response.ok) {
      const errorData = data && typeof data === 'object'
        ? data
        : { error: typeof data === 'string' && data ? data : 'Request failed' };
      throw { status: response.status, ...errorData };
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

  // Admin - Products
  async getAdminProducts(params = '') {
    return this.request(`${this.baseUrl}/products/admin/products/${params ? '?' + params : ''}`, {
      headers: this.getHeaders(true),
    });
  }

  async createAdminProduct(productData) {
    return this.request(`${this.baseUrl}/products/admin/products/`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(productData),
    });
  }

  async updateAdminProduct(productId, productData) {
    return this.request(`${this.baseUrl}/products/admin/products/${productId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(true),
      body: JSON.stringify(productData),
    });
  }

  async deleteAdminProduct(productId) {
    return this.request(`${this.baseUrl}/products/admin/products/${productId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(true),
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

  async clearCart() {
    return this.request(`${this.baseUrl}/cart/clear/`, {
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

  // Admin - Orders
  async getAdminOrders() {
    return this.request(`${this.baseUrl}/orders/admin/`, {
      headers: this.getHeaders(true),
    });
  }

  async updateAdminOrderStatus(orderId, status) {
    return this.request(`${this.baseUrl}/orders/admin/${orderId}/status/`, {
      method: 'PATCH',
      headers: this.getHeaders(true),
      body: JSON.stringify({ status }),
    });
  }

  // Admin - Users
  async getAdminUsers() {
    return this.request(`${this.baseUrl}/users/admin/users/`, {
      headers: this.getHeaders(true),
    });
  }

  async updateAdminUser(userId, userData) {
    return this.request(`${this.baseUrl}/users/admin/users/${userId}/`, {
      method: 'PATCH',
      headers: this.getHeaders(true),
      body: JSON.stringify(userData),
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

  // Chatbot
  async sendChatMessage(message, sessionId = '') {
    return this.request(`${this.baseUrl}/chatbot/chat/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  }

  async getChatSuggestions() {
    return this.request(`${this.baseUrl}/chatbot/suggestions/`, {
      headers: this.getHeaders(),
    });
  }

  async clearChatHistory(sessionId) {
    return this.request(`${this.baseUrl}/chatbot/clear/${sessionId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
  }
}

export default new ApiService();
