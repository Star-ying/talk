// ===================================================
// 🛡️ AuthManager - 全局认证管理器
// 功能：Cookie 操作、Token 管理、请求封装、登出处理
// 使用方式：在所有页面引入此脚本即可使用 AuthManager
// ===================================================

class AuthManager {
  /**
   * 设置 authToken Cookie
   * @param {string} token JWT Token
   * @param {boolean} isRememberMe 是否记住登录（7天有效期）
   */
  static setToken(token, isRememberMe = false) {
    const days = isRememberMe ? 7 : 0;
    let expires = '';
    if (days > 0) {
      const date = new Date();
      date.setTime(date.getTime() + days * 86400000); // 毫秒
      expires = `; expires=${date.toUTCString()}`;
    }

    // 安全设置：path=/, SameSite=Lax, Secure（生产环境必须 HTTPS）
    document.cookie = `authToken=${encodeURIComponent(token)}${expires}; path=/; SameSite=Lax; Secure`;
    
    // 标记已登录状态（用于快速判断）
    localStorage.setItem("isAuthenticated", "true");
  }

  /**
   * 获取当前 authToken
   * @returns {string|null}
   */
  static getToken() {
    return this.getCookie('authToken');
  }

  /**
   * 通用读取 Cookie
   * @param {string} name Cookie 名称
   * @returns {string|null}
   */
  static getCookie(name) {
    const nameEQ = name + "=";
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.startsWith(nameEQ)) {
        return decodeURIComponent(cookie.substring(nameEQ.length));
      }
    }
    return null;
  }

  /**
   * 清除认证信息（登出时调用）
   */
  static clearToken() {
    document.cookie = 'authToken=; Max-Age=0; path=/; SameSite=Lax; Secure';
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("account");
  }

  /**
   * 检查是否已登录
   * @returns {boolean}
   */
  static isAuthenticated() {
    return !!this.getToken() && localStorage.getItem("isAuthenticated") === "true";
  }

  /**
   * 封装 fetch 请求，自动携带 Authorization 头
   * @param {string} url 请求地址
   * @param {Object} options fetch 配置
   * @returns {Promise<Response>}
   */
  static async request(url, options = {}) {
    const token = this.getToken();
    if (!token) {
      throw new Error("未登录");
    }

    const config = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        ...options.headers
      }
    };

    try {
      const res = await fetch(url, config);

      if (res.status === 401) {
        this.handleUnauthorized();
        throw res;
      }

      return res;
    } catch (error) {
      if (error.message !== "未登录") {
        console.error("请求失败:", error);
      }
      throw error;
    }
  }

  /**
   * 处理未授权错误（登出 + 跳转）
   */
  static handleUnauthorized() {
    this.clearToken();
    alert("登录已过期，请重新登录");
    window.location.href = "/login";
  }

  /**
   * 登出操作（可绑定按钮）
   */
  static logout() {
    if (confirm("确定要退出登录吗？")) {
      this.clearToken();
      alert("已退出登录");
      window.location.href = "/login";
    }
  }
}

// 🔍 暴露为全局变量，供 HTML 页面使用
window.AuthManager = AuthManager;