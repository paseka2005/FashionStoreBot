// main.js - Центральный модуль управления интернет-магазином VOGUE ÉLITE

// Проверка, не инициализировано ли приложение уже
if (window.VogueEliteAppInstance) {
    console.log('VOGUE ÉLITE приложение уже инициализировано');
} else {
    // Вспомогательные классы
    class NotificationManager {
        constructor() {
            this.container = null;
            this.queue = [];
            this.setup();
        }
        
        setup() {
            this.createContainer();
        }
        
        createContainer() {
            this.container = document.createElement('div');
            this.container.className = 'main-notifications-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(this.container);
        }
        
        show(message, type = 'info', duration = 5000) {
            const notification = this.createNotification(message, type);
            this.container.appendChild(notification);
            
            setTimeout(() => notification.classList.add('show'), 10);
            
            if (duration > 0) {
                setTimeout(() => this.hide(notification), duration);
            }
            
            return notification;
        }
        
        createNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `main-notification main-notification-${type}`;
            notification.innerHTML = `
                <div class="main-notification-icon">
                    <i class="${this.getIcon(type)}"></i>
                </div>
                <div class="main-notification-content">${message}</div>
                <button class="main-notification-close">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            notification.style.cssText = `
                background: ${this.getNotificationColor(type)};
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                gap: 12px;
                transform: translateX(100%);
                opacity: 0;
                transition: transform 0.3s ease, opacity 0.3s ease;
                max-width: 400px;
            `;
            
            notification.querySelector('.main-notification-close').addEventListener('click', () => {
                this.hide(notification);
            });
            
            return notification;
        }
        
        hide(notification) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
        
        getIcon(type) {
            const icons = {
                'success': 'fas fa-check-circle',
                'error': 'fas fa-exclamation-circle',
                'warning': 'fas fa-exclamation-triangle',
                'info': 'fas fa-info-circle'
            };
            return icons[type] || icons.info;
        }
        
        getNotificationColor(type) {
            const colors = {
                'success': '#10b981',
                'error': '#ef4444',
                'warning': '#f59e0b',
                'info': '#d4af37'
            };
            return colors[type] || colors.info;
        }
    }

    class UIManager {
        constructor() {
            this.components = new Map();
        }
        
        registerComponent(name, component) {
            this.components.set(name, component);
        }
        
        getComponent(name) {
            return this.components.get(name);
        }
        
        updateComponent(name, data) {
            const component = this.components.get(name);
            if (component && component.update) {
                component.update(data);
            }
        }
    }

    class AuthManager {
        constructor() {
            this.isAuthenticated = false;
            this.user = null;
        }
        
        async login(credentials) {
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(credentials)
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    this.isAuthenticated = true;
                    this.user = data.user;
                    return { success: true, data };
                } else {
                    return { success: false, error: data.message || 'Ошибка авторизации' };
                }
            } catch (error) {
                console.error('Ошибка входа:', error);
                return { success: false, error: 'Ошибка сети' };
            }
        }
        
        async logout() {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    this.isAuthenticated = false;
                    this.user = null;
                    return { success: true };
                } else {
                    return { success: false, error: data.message || 'Ошибка выхода' };
                }
            } catch (error) {
                console.error('Ошибка выхода:', error);
                return { success: false, error: 'Ошибка сети' };
            }
        }
        
        checkAuth() {
            return this.isAuthenticated;
        }
    }

    class AnalyticsManager {
        constructor() {
            this.events = [];
            this.isEnabled = true;
        }
        
        track(event, data) {
            if (!this.isEnabled) return;
            
            const eventData = {
                event,
                timestamp: Date.now(),
                data,
                url: window.location.href,
                userAgent: navigator.userAgent
            };
            
            this.events.push(eventData);
            this.sendToServer(eventData);
        }
        
        async sendToServer(eventData) {
            try {
                await fetch('/api/analytics/track', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(eventData)
                });
            } catch (error) {
                this.saveForLater(eventData);
            }
        }
        
        saveForLater(eventData) {
            const pending = JSON.parse(localStorage.getItem('analytics_pending') || '[]');
            pending.push(eventData);
            localStorage.setItem('analytics_pending', JSON.stringify(pending));
        }
    }

    // Основной класс приложения
    class VogueEliteApp {
        constructor() {
            this.config = {
                apiBase: '/api',
                siteName: 'VOGUE ÉLITE',
                currency: '₽',
                currencySymbol: '₽',
                language: 'ru',
                theme: 'dark-nude',
                debug: false,
                enableAjaxNavigation: false
            };
            
            this.modules = {
                cartManager: null,
                catalog: null,
                auth: null,
                notifications: null,
                analytics: null,
                ui: null
            };
            
            this.state = {
                user: null,
                cart: { items: [], total: 0 },
                wishlist: [],
                compare: [],
                notifications: [],
                preferences: {},
                session: {
                    id: this.generateSessionId(),
                    startTime: Date.now(),
                    pageViews: 0,
                    interactions: 0,
                    hiddenDuration: 0,
                    lastHiddenTime: null
                }
            };
            
            // Правильно привязываем методы
            this.handleScroll = this.handleScroll.bind(this);
            this.handleNavigation = this.handleNavigation.bind(this);
            this.handleFormSubmit = this.handleFormSubmit.bind(this);
            this.handleKeyDown = this.handleKeyDown.bind(this);
            this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
            this.handleResize = this.handleResize.bind(this);
            this.handleOnlineStatus = this.handleOnlineStatus.bind(this);
            this.handleOfflineStatus = this.handleOfflineStatus.bind(this);
            this.trackError = this.trackError.bind(this);
            this.toggleScrollToTopButton = this.toggleScrollToTopButton.bind(this);
            this.handleInfiniteScroll = this.handleInfiniteScroll.bind(this);
            this.applyParallaxEffects = this.applyParallaxEffects.bind(this);
            this.trackScrollDepth = this.trackScrollDepth.bind(this);
            
            this.init();
        }

        // Инициализация приложения
        async init() {
            console.log('🚀 Инициализация VOGUE ÉLITE приложения...');
            
            this.setConfigFromMeta();
            await this.initializeCoreModules();
            this.setupGlobalEventListeners();
            this.setupUIComponents();
            await this.loadUserData();
            this.setupAnalytics();
            this.startPeriodicTasks();
            
            this.dispatchEvent('app:initialized');
            console.log('✅ VOGUE ÉLITE успешно инициализирован');
        }

        // Установка конфигурации из meta тегов
        setConfigFromMeta() {
            const metaConfig = document.querySelector('meta[name="app-config"]');
            if (metaConfig) {
                try {
                    const config = JSON.parse(metaConfig.content);
                    Object.assign(this.config, config);
                } catch (error) {
                    console.error('Ошибка парсинга конфигурации:', error);
                }
            }
        }

        // Инициализация основных модулей
        async initializeCoreModules() {
            this.modules.notifications = new NotificationManager();
            this.modules.ui = new UIManager();
            this.modules.auth = new AuthManager();
            this.modules.analytics = new AnalyticsManager();
            
            // Используем существующий менеджер корзины если он есть
            if (window.cartManager) {
                this.modules.cartManager = window.cartManager;
            } else {
                await this.initializeBasicCart();
            }
            
            if (this.isCatalogPage()) {
                await this.initializeCatalog();
            }
        }

        // Инициализация базовой корзины
        async initializeBasicCart() {
            this.modules.cartManager = {
                items: [],
                total: 0,
                addItem: async (productId, quantity = 1, options = {}) => {
                    try {
                        const response = await fetch('/api/cart/add', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({
                                product_id: productId,
                                quantity: quantity,
                                size: options.size,
                                color: options.color
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.success) {
                            this.state.cart.items.push({
                                product_id: productId,
                                quantity: quantity,
                                ...options
                            });
                            this.state.cart.total = data.cart_total || this.state.cart.total;
                            this.updateCartUI();
                            this.showMainNotification('Товар добавлен в корзину', 'success');
                            return { success: true, data };
                        } else {
                            this.showMainNotification(data.message || 'Ошибка добавления в корзину', 'error');
                            return { success: false, error: data.message };
                        }
                    } catch (error) {
                        console.error('Ошибка добавления в корзину:', error);
                        this.showMainNotification('Ошибка сети', 'error');
                        return { success: false, error: 'Ошибка сети' };
                    }
                },
                updateQuantity: async (cartItemId, quantity) => {
                    try {
                        const response = await fetch('/api/cart/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({
                                cart_item_id: cartItemId,
                                quantity: quantity
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.success) {
                            // Обновляем локальное состояние
                            const item = this.state.cart.items.find(item => item.id === cartItemId);
                            if (item) {
                                item.quantity = quantity;
                            }
                            this.state.cart.total = data.total || this.state.cart.total;
                            this.updateCartUI();
                            return { success: true, data };
                        } else {
                            return { success: false, error: data.message };
                        }
                    } catch (error) {
                        console.error('Ошибка обновления корзины:', error);
                        return { success: false, error: 'Ошибка сети' };
                    }
                },
                removeItem: async (cartItemId) => {
                    try {
                        const response = await fetch(`/api/cart/remove/${cartItemId}`, {
                            method: 'DELETE',
                            headers: {
                                'Accept': 'application/json'
                            }
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.success) {
                            // Удаляем из локального состояния
                            this.state.cart.items = this.state.cart.items.filter(item => item.id !== cartItemId);
                            this.state.cart.total = data.total || this.state.cart.total;
                            this.updateCartUI();
                            this.showMainNotification('Товар удален из корзины', 'success');
                            return { success: true, data };
                        } else {
                            return { success: false, error: data.message };
                        }
                    } catch (error) {
                        console.error('Ошибка удаления из корзины:', error);
                        return { success: false, error: 'Ошибка сети' };
                    }
                },
                clearCart: () => {
                    this.state.cart.items = [];
                    this.state.cart.total = 0;
                    this.updateCartUI();
                },
                getTotalItems: () => this.state.cart.items.length,
                getTotalPrice: () => this.state.cart.total,
                getCartItems: () => [...this.state.cart.items]
            };
        }

        // Инициализация каталога
        async initializeCatalog() {
            try {
                // Базовая реализация каталога
                this.modules.catalog = {
                    currentPage: 1,
                    totalPages: 1,
                    isLoading: false,
                    products: [],
                    
                    loadProducts: async (params = {}) => {
                        try {
                            this.isLoading = true;
                            
                            const queryParams = new URLSearchParams(params).toString();
                            const response = await fetch(`/api/products?${queryParams}`, {
                                headers: {
                                    'Accept': 'application/json'
                                }
                            });
                            
                            const data = await response.json();
                            
                            if (response.ok && data.success) {
                                this.products = data.products || [];
                                this.totalPages = Math.ceil(data.total / (params.limit || 12));
                                return { success: true, data };
                            } else {
                                return { success: false, error: data.message };
                            }
                        } catch (error) {
                            console.error('Ошибка загрузки товаров:', error);
                            return { success: false, error: 'Ошибка сети' };
                        } finally {
                            this.isLoading = false;
                        }
                    },
                    
                    goToPage: function(page) {
                        this.currentPage = page;
                        this.loadProducts({ page: page, limit: 12 });
                    },
                    
                    updateResponsiveUI: function() {
                        // Обновление UI для адаптивности
                        const grid = document.querySelector('.products-grid');
                        if (grid) {
                            const isMobile = window.innerWidth < 768;
                            grid.style.gridTemplateColumns = isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)';
                        }
                    }
                };
            } catch (error) {
                console.error('Ошибка инициализации каталога:', error);
            }
        }

        // Загрузка пользовательских данных
        async loadUserData() {
            try {
                const response = await fetch(`${this.config.apiBase}/auth/check`, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        this.state.user = data.user;
                        this.state.isAuthenticated = data.is_authenticated;
                        this.updateUserUI();
                        
                        // Загружаем дополнительные данные только если пользователь авторизован
                        if (this.state.isAuthenticated && this.state.user) {
                            await this.loadWishlist();
                            await this.loadCompareList();
                            await this.loadUserPreferences();
                        }
                    }
                } else {
                    // Если не авторизован, получаем гостевые данные
                    const guestResponse = await fetch(`${this.config.apiBase}/auth/guest`, {
                        headers: {
                            'Accept': 'application/json'
                        }
                    });
                    
                    if (guestResponse.ok) {
                        const guestData = await guestResponse.json();
                        if (guestData.success) {
                            this.state.user = guestData.user;
                            this.state.isAuthenticated = guestData.is_authenticated;
                        }
                    }
                }
            } catch (error) {
                console.error('Ошибка загрузки пользовательских данных:', error);
                // Используем локальные данные
                this.loadUserPreferences();
            }
        }

        // Загрузка избранного
        async loadWishlist() {
            try {
                if (!this.state.user || !this.state.isAuthenticated) {
                    this.loadWishlistFromLocalStorage();
                    return;
                }
                
                const response = await fetch(`${this.config.apiBase}/wishlist`, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        this.state.wishlist = data.wishlist || [];
                        this.updateWishlistUI();
                    } else {
                        this.loadWishlistFromLocalStorage();
                    }
                } else {
                    this.loadWishlistFromLocalStorage();
                }
            } catch (error) {
                console.warn('Не удалось загрузить избранное, используется локальное хранилище:', error);
                this.loadWishlistFromLocalStorage();
            }
        }

        // Загрузка избранного из LocalStorage
        loadWishlistFromLocalStorage() {
            try {
                const savedWishlist = localStorage.getItem('wishlist');
                if (savedWishlist) {
                    this.state.wishlist = JSON.parse(savedWishlist);
                    this.updateWishlistUI();
                }
            } catch (error) {
                console.error('Ошибка загрузки избранного из LocalStorage:', error);
                this.state.wishlist = [];
                this.updateWishlistUI();
            }
        }

        // Загрузка списка сравнения
        async loadCompareList() {
            try {
                if (!this.state.user || !this.state.isAuthenticated) {
                    this.loadCompareListFromLocalStorage();
                    return;
                }
                
                const response = await fetch(`${this.config.apiBase}/compare`, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        this.state.compare = data.compare || [];
                        this.updateCompareUI();
                    } else {
                        this.loadCompareListFromLocalStorage();
                    }
                } else {
                    this.loadCompareListFromLocalStorage();
                }
            } catch (error) {
                console.warn('Не удалось загрузить список сравнения, используется локальное хранилище:', error);
                this.loadCompareListFromLocalStorage();
            }
        }

        // Загрузка списка сравнения из LocalStorage
        loadCompareListFromLocalStorage() {
            try {
                const savedCompare = localStorage.getItem('compare');
                if (savedCompare) {
                    this.state.compare = JSON.parse(savedCompare);
                    this.updateCompareUI();
                }
            } catch (error) {
                console.error('Ошибка загрузки списка сравнения из LocalStorage:', error);
                this.state.compare = [];
                this.updateCompareUI();
            }
        }

        // Загрузка пользовательских предпочтений
        async loadUserPreferences() {
            try {
                const savedPrefs = localStorage.getItem('user_preferences');
                if (savedPrefs) {
                    this.state.preferences = JSON.parse(savedPrefs);
                    this.applyUserPreferences();
                }
            } catch (error) {
                console.error('Ошибка загрузки предпочтений:', error);
            }
        }

        // Применение пользовательских предпочтений
        applyUserPreferences() {
            if (this.state.preferences.theme) {
                document.documentElement.setAttribute('data-theme', this.state.preferences.theme);
            }
            
            if (this.state.preferences.fontSize) {
                document.documentElement.style.fontSize = this.state.preferences.fontSize;
            }
            
            if (this.state.preferences.currency) {
                this.config.currency = this.state.preferences.currency;
                this.updateCurrencyDisplay();
            }
        }

        // Настройка глобальных обработчиков событий
        setupGlobalEventListeners() {
            document.addEventListener('click', this.handleNavigation);
            document.addEventListener('submit', this.handleFormSubmit);
            document.addEventListener('keydown', this.handleKeyDown);
            document.addEventListener('visibilitychange', this.handleVisibilityChange);
            
            window.addEventListener('online', this.handleOnlineStatus);
            window.addEventListener('offline', this.handleOfflineStatus);
            window.addEventListener('scroll', this.handleScroll);
            window.addEventListener('resize', this.handleResize);
            
            this.setupTouchEvents();
            this.setupGlobalErrorHandler();
        }

        // Обработка навигации
        handleNavigation(e) {
            const link = e.target.closest('a');
            if (!link) return;
            
            const href = link.getAttribute('href');
            const isExternal = link.target === '_blank' || link.rel === 'external';
            const isHashLink = href && href.startsWith('#');
            
            if (isExternal || isHashLink) return;
            
            if (href && href.includes('#')) {
                const anchor = href.split('#')[1];
                this.scrollToAnchor(anchor);
                return;
            }
            
            if (this.config.enableAjaxNavigation && href && !href.startsWith('http')) {
                e.preventDefault();
                this.navigateTo(href);
            }
            
            this.trackEvent('navigation', 'click', {
                href: href,
                text: link.textContent.trim()
            });
        }

        // Прокрутка к якорю
        scrollToAnchor(anchor) {
            const element = document.getElementById(anchor);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }

        // AJAX навигация
        async navigateTo(url) {
            try {
                this.showLoading();
                
                const response = await fetch(url);
                const html = await response.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                this.updatePageContent(doc);
                window.history.pushState({}, '', url);
                
                this.dispatchEvent('app:navigated', { url });
                
            } catch (error) {
                console.error('Ошибка навигации:', error);
                window.location.href = url;
            } finally {
                this.hideLoading();
            }
        }

        // Обновление контента страницы
        updatePageContent(newDoc) {
            const mainContent = document.querySelector('main');
            const newContent = newDoc.querySelector('main');
            
            if (mainContent && newContent) {
                mainContent.innerHTML = newContent.innerHTML;
            }
            
            document.title = newDoc.title;
            this.updateMetaTags(newDoc);
            this.initializePageComponents();
            window.scrollTo(0, 0);
        }

        // Обновление meta тегов
        updateMetaTags(newDoc) {
            const metaTags = ['description', 'keywords', 'author', 'viewport'];
            metaTags.forEach(name => {
                const newTag = newDoc.querySelector(`meta[name="${name}"]`);
                const existingTag = document.querySelector(`meta[name="${name}"]`);
                
                if (newTag && existingTag) {
                    existingTag.setAttribute('content', newTag.getAttribute('content'));
                }
            });
        }

        // Инициализация компонентов страницы
        initializePageComponents() {
            // Переинициализируем компоненты после AJAX навигации
            this.setupUIComponents();
            
            if (this.isCatalogPage() && !this.modules.catalog) {
                this.initializeCatalog();
            }
        }

        // Обработка отправки форм
        handleFormSubmit(e) {
            const form = e.target.closest('form');
            if (!form) return;
            
            const isAjaxForm = form.classList.contains('ajax-form') || 
                              form.dataset.ajax === 'true';
            
            if (isAjaxForm) {
                e.preventDefault();
                this.submitFormAjax(form);
            }
            
            this.trackEvent('form', 'submit', {
                formId: form.id || 'unknown',
                action: form.action
            });
        }

        // AJAX отправка формы
        async submitFormAjax(form) {
            try {
                const submitBtn = form.querySelector('[type="submit"]');
                const originalText = submitBtn ? submitBtn.innerHTML : null;
                
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обработка...';
                    submitBtn.disabled = true;
                }
                
                const formData = new FormData(form);
                const isMultipart = form.enctype === 'multipart/form-data';
                
                const response = await fetch(form.action, {
                    method: form.method,
                    body: isMultipart ? formData : new URLSearchParams(formData),
                    headers: isMultipart ? {} : {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    if (result.success) {
                        this.showMainNotification(result.message || 'Успешно!', 'success');
                        
                        if (result.redirect) {
                            setTimeout(() => {
                                window.location.href = result.redirect;
                            }, 1500);
                        }
                        
                        if (result.resetForm) {
                            form.reset();
                        }
                        
                        if (result.updateUI) {
                            this.updateUIComponents(result.data);
                        }
                        
                    } else {
                        this.showMainNotification(result.message || 'Ошибка!', 'error');
                        
                        if (result.errors) {
                            this.showFormErrors(form, result.errors);
                        }
                    }
                } else {
                    this.showMainNotification(result.message || 'Ошибка сервера!', 'error');
                }
                
            } catch (error) {
                console.error('Ошибка отправки формы:', error);
                this.showMainNotification('Ошибка соединения', 'error');
            } finally {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn && originalText) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }
        }

        // Показ ошибок формы
        showFormErrors(form, errors) {
            // Очищаем предыдущие ошибки
            form.querySelectorAll('.error-message').forEach(el => el.remove());
            
            // Показываем новые ошибки
            Object.entries(errors).forEach(([field, message]) => {
                const input = form.querySelector(`[name="${field}"]`);
                if (input) {
                    const errorEl = document.createElement('div');
                    errorEl.className = 'error-message';
                    errorEl.textContent = message;
                    errorEl.style.color = '#ef4444';
                    errorEl.style.fontSize = '0.875rem';
                    errorEl.style.marginTop = '5px';
                    
                    input.parentNode.appendChild(errorEl);
                }
            });
        }

        // Обработка нажатия клавиш
        handleKeyDown(e) {
            switch(e.key) {
                case 'Escape':
                    this.closeAllModals();
                    break;
                    
                case '/':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.focusSearch();
                    }
                    break;
                    
                case 's':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.savePageState();
                    }
                    break;
            }
            
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        }

        // Обработка Tab навигации
        handleTabNavigation(e) {
            const focusableElements = document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }

        // Обработка изменения видимости страницы
        handleVisibilityChange() {
            if (document.hidden) {
                this.dispatchEvent('app:pageHidden');
                this.state.session.lastHiddenTime = Date.now();
            } else {
                this.dispatchEvent('app:pageVisible');
                
                if (this.state.session.lastHiddenTime) {
                    this.state.session.hiddenDuration += Date.now() - this.state.session.lastHiddenTime;
                }
            }
        }

        // Обработка онлайн статуса
        handleOnlineStatus() {
            this.showMainNotification('Соединение восстановлено', 'success');
            this.dispatchEvent('app:online');
            this.syncOfflineData();
        }

        handleOfflineStatus() {
            this.showMainNotification('Вы offline. Некоторые функции ограничены', 'warning');
            this.dispatchEvent('app:offline');
        }

        // Обработка прокрутки
        handleScroll() {
            const scrollPosition = window.pageYOffset;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            this.toggleScrollToTopButton(scrollPosition);
            
            if (scrollPosition + windowHeight >= documentHeight - 100) {
                this.handleInfiniteScroll();
            }
            
            this.applyParallaxEffects(scrollPosition);
            this.trackScrollDepth(scrollPosition, documentHeight);
        }

        // Переключение кнопки "Наверх"
        toggleScrollToTopButton(scrollPosition) {
            const scrollToTopBtn = document.getElementById('scroll-to-top');
            if (scrollToTopBtn) {
                if (scrollPosition > 300) {
                    scrollToTopBtn.style.display = 'flex';
                } else {
                    scrollToTopBtn.style.display = 'none';
                }
            }
        }

        // Обработка бесконечного скролла
        handleInfiniteScroll() {
            if (this.isCatalogPage() && this.modules.catalog && !this.modules.catalog.isLoading) {
                if (this.modules.catalog.currentPage < this.modules.catalog.totalPages) {
                    this.modules.catalog.goToPage(this.modules.catalog.currentPage + 1);
                }
            }
        }

        // Применение параллакс эффектов
        applyParallaxEffects(scrollPosition) {
            document.querySelectorAll('[data-parallax]').forEach(element => {
                const speed = parseFloat(element.dataset.parallax) || 0.5;
                const yPos = -(scrollPosition * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });
        }

        // Отслеживание глубины прокрутки
        trackScrollDepth(scrollPosition, documentHeight) {
            const percentages = [25, 50, 75, 90];
            percentages.forEach(percent => {
                const threshold = (documentHeight * percent) / 100;
                if (scrollPosition >= threshold && !this.state.session[`scroll_${percent}`]) {
                    this.state.session[`scroll_${percent}`] = true;
                    this.trackEvent('scroll', `reached_${percent}%`, {
                        position: scrollPosition,
                        percentage: percent
                    });
                }
            });
        }

        // Обработка ресайза окна
        handleResize() {
            this.dispatchEvent('app:resize', {
                width: window.innerWidth,
                height: window.innerHeight,
                isMobile: window.innerWidth < 768
            });
            
            this.updateResponsiveComponents();
        }

        // Обновление адаптивных компонентов
        updateResponsiveComponents() {
            // Обновляем сетку каталога
            if (this.modules.catalog) {
                this.modules.catalog.updateResponsiveUI();
            }
            
            // Обновляем мобильное меню
            const mobileMenu = document.querySelector('.mobile-menu');
            if (mobileMenu && window.innerWidth >= 768) {
                mobileMenu.classList.remove('active');
            }
        }

        // Настройка тач событий
        setupTouchEvents() {
            let lastTouchEnd = 0;
            document.addEventListener('touchend', (e) => {
                const now = Date.now();
                if (now - lastTouchEnd <= 300) {
                    e.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
        }

        // Настройка UI компонентов
        setupUIComponents() {
            this.initializeModals();
            this.initializeDropdowns();
            this.initializeTabs();
            this.initializeAccordions();
            this.initializeSliders();
            this.initializeTooltips();
            this.initializeLazyLoad();
            this.initializeAnimations();
            this.initializeScrollToTop();
        }

        // Инициализация модальных окон
        initializeModals() {
            document.querySelectorAll('[data-modal]').forEach(trigger => {
                trigger.addEventListener('click', (e) => {
                    e.preventDefault();
                    const modalId = trigger.dataset.modal;
                    this.openModal(modalId);
                });
            });
            
            document.querySelectorAll('.modal').forEach(modal => {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        this.closeModal(modal.id);
                    }
                });
            });
            
            document.querySelectorAll('.modal-close').forEach(closeBtn => {
                closeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const modal = closeBtn.closest('.modal');
                    if (modal) {
                        this.closeModal(modal.id);
                    }
                });
            });
        }

        // Открытие модального окна
        openModal(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            const focusElement = modal.querySelector('input, button, [tabindex]');
            if (focusElement) {
                setTimeout(() => focusElement.focus(), 100);
            }
            
            this.dispatchEvent('modal:opened', { modalId });
        }

        // Закрытие модального окна
        closeModal(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;
            
            modal.classList.remove('active');
            document.body.style.overflow = '';
            
            this.dispatchEvent('modal:closed', { modalId });
        }

        // Закрытие всех модальных окон
        closeAllModals() {
            document.querySelectorAll('.modal.active').forEach(modal => {
                this.closeModal(modal.id);
            });
        }

        // Инициализация выпадающих меню
        initializeDropdowns() {
            document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const dropdown = toggle.closest('.dropdown');
                    const isActive = dropdown.classList.contains('active');
                    
                    document.querySelectorAll('.dropdown.active').forEach(d => {
                        if (d !== dropdown) {
                            d.classList.remove('active');
                        }
                    });
                    
                    dropdown.classList.toggle('active', !isActive);
                });
            });
            
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.dropdown')) {
                    document.querySelectorAll('.dropdown.active').forEach(dropdown => {
                        dropdown.classList.remove('active');
                    });
                }
            });
            
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    document.querySelectorAll('.dropdown.active').forEach(dropdown => {
                        dropdown.classList.remove('active');
                    });
                }
            });
        }

        // Инициализация табов
        initializeTabs() {
            document.querySelectorAll('.tab-btn').forEach(tab => {
                tab.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    const tabId = tab.dataset.tab;
                    const tabsContainer = tab.closest('.tabs');
                    
                    if (!tabId || !tabsContainer) return;
                    
                    tabsContainer.querySelectorAll('.tab-btn').forEach(t => {
                        t.classList.remove('active');
                    });
                    
                    tab.classList.add('active');
                    
                    tabsContainer.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    const tabContent = document.getElementById(`${tabId}-content`);
                    if (tabContent) {
                        tabContent.classList.add('active');
                    }
                    
                    this.dispatchEvent('tabs:changed', { tabId });
                });
            });
        }

        // Инициализация аккордеонов
        initializeAccordions() {
            document.querySelectorAll('.accordion-header').forEach(header => {
                header.addEventListener('click', () => {
                    const accordion = header.closest('.accordion');
                    const isActive = accordion.classList.contains('active');
                    
                    if (accordion.dataset.single) {
                        document.querySelectorAll('.accordion.active').forEach(acc => {
                            if (acc !== accordion) {
                                acc.classList.remove('active');
                            }
                        });
                    }
                    
                    accordion.classList.toggle('active', !isActive);
                    
                    const content = accordion.querySelector('.accordion-content');
                    if (content) {
                        if (!isActive) {
                            content.style.maxHeight = content.scrollHeight + 'px';
                        } else {
                            content.style.maxHeight = '0';
                        }
                    }
                });
            });
        }

        // Инициализация слайдеров
        initializeSliders() {
            document.querySelectorAll('.slider').forEach(slider => {
                const slides = slider.querySelectorAll('.slide');
                const prevBtn = slider.querySelector('.slider-prev');
                const nextBtn = slider.querySelector('.slider-next');
                const dots = slider.querySelectorAll('.slider-dot');
                
                let currentSlide = 0;
                const totalSlides = slides.length;
                
                const goToSlide = (index) => {
                    currentSlide = (index + totalSlides) % totalSlides;
                    
                    slides.forEach((slide, i) => {
                        slide.classList.toggle('active', i === currentSlide);
                    });
                    
                    dots.forEach((dot, i) => {
                        dot.classList.toggle('active', i === currentSlide);
                    });
                    
                    slider.style.transform = `translateX(-${currentSlide * 100}%)`;
                };
                
                if (prevBtn) {
                    prevBtn.addEventListener('click', () => goToSlide(currentSlide - 1));
                }
                
                if (nextBtn) {
                    nextBtn.addEventListener('click', () => goToSlide(currentSlide + 1));
                }
                
                dots.forEach((dot, index) => {
                    dot.addEventListener('click', () => goToSlide(index));
                });
                
                if (slider.dataset.autoplay === 'true') {
                    setInterval(() => {
                        goToSlide(currentSlide + 1);
                    }, parseInt(slider.dataset.interval || 5000));
                }
            });
        }

        // Инициализация тултипов
        initializeTooltips() {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.style.cssText = `
                position: fixed;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 14px;
                z-index: 9999;
                display: none;
                pointer-events: none;
                max-width: 200px;
                white-space: nowrap;
            `;
            document.body.appendChild(tooltip);
            
            document.querySelectorAll('[data-tooltip]').forEach(element => {
                const text = element.getAttribute('data-tooltip');
                if (!text) return;
                
                element.addEventListener('mouseenter', (e) => {
                    tooltip.textContent = text;
                    tooltip.style.display = 'block';
                    
                    const rect = element.getBoundingClientRect();
                    tooltip.style.left = `${rect.left + rect.width / 2}px`;
                    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
                    tooltip.style.transform = 'translateX(-50%)';
                });
                
                element.addEventListener('mouseleave', () => {
                    tooltip.style.display = 'none';
                });
            });
        }

        // Инициализация ленивой загрузки
        initializeLazyLoad() {
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            const src = img.dataset.src;
                            
                            if (src) {
                                img.src = src;
                                img.removeAttribute('data-src');
                            }
                            
                            imageObserver.unobserve(img);
                        }
                    });
                });
                
                document.querySelectorAll('img[data-src]').forEach(img => {
                    imageObserver.observe(img);
                });
            }
        }

        // Инициализация анимаций
        initializeAnimations() {
            if ('IntersectionObserver' in window) {
                const animationObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('animate');
                        }
                    });
                }, {
                    threshold: 0.1
                });
                
                document.querySelectorAll('.animate-on-scroll').forEach(element => {
                    animationObserver.observe(element);
                });
            }
        }

        // Инициализация кнопки "Наверх"
        initializeScrollToTop() {
            let scrollToTopBtn = document.getElementById('scroll-to-top');
            
            if (!scrollToTopBtn) {
                scrollToTopBtn = document.createElement('button');
                scrollToTopBtn.id = 'scroll-to-top';
                scrollToTopBtn.className = 'scroll-to-top';
                scrollToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
                scrollToTopBtn.style.cssText = `
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    width: 50px;
                    height: 50px;
                    background: #d4af37;
                    color: white;
                    border: none;
                    border-radius: 50%;
                    display: none;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    z-index: 1000;
                    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
                    transition: all 0.3s ease;
                `;
                
                document.body.appendChild(scrollToTopBtn);
                
                scrollToTopBtn.addEventListener('click', () => {
                    window.scrollTo({
                        top: 0,
                        behavior: 'smooth'
                    });
                });
                
                scrollToTopBtn.addEventListener('mouseenter', () => {
                    scrollToTopBtn.style.transform = 'scale(1.1)';
                    scrollToTopBtn.style.boxShadow = '0 6px 20px rgba(212, 175, 55, 0.4)';
                });
                
                scrollToTopBtn.addEventListener('mouseleave', () => {
                    scrollToTopBtn.style.transform = 'scale(1)';
                    scrollToTopBtn.style.boxShadow = '0 4px 12px rgba(212, 175, 55, 0.3)';
                });
            }
        }

        // Обновление UI корзины
        updateCartUI() {
            if (!this.modules.cartManager) return;
            
            const totalItems = this.modules.cartManager.getTotalItems();
            const totalPrice = this.modules.cartManager.getTotalPrice();
            
            document.querySelectorAll('.cart-count').forEach(element => {
                element.textContent = totalItems;
                element.style.display = totalItems > 0 ? 'flex' : 'none';
            });
            
            document.querySelectorAll('.cart-total').forEach(element => {
                element.textContent = `${this.formatPrice(totalPrice)}`;
            });
            
            document.querySelectorAll('.cart-icon').forEach(icon => {
                if (totalItems > 0) {
                    icon.classList.add('has-items');
                } else {
                    icon.classList.remove('has-items');
                }
            });
        }

        // Обновление UI пользователя
        updateUserUI() {
            if (!this.state.user) return;
            
            document.querySelectorAll('.user-greeting').forEach(element => {
                element.textContent = `Добро пожаловать, ${this.state.user.first_name}!`;
            });
            
            document.querySelectorAll('.user-name').forEach(element => {
                element.textContent = `${this.state.user.first_name} ${this.state.user.last_name || ''}`;
            });
            
            document.querySelectorAll('.user-avatar').forEach(avatar => {
                if (this.state.user.avatar_url) {
                    avatar.style.backgroundImage = `url(${this.state.user.avatar_url})`;
                }
            });
        }

        // Обновление UI избранного
        updateWishlistUI() {
            const wishlistCount = this.state.wishlist.length;
            
            document.querySelectorAll('.wishlist-count').forEach(element => {
                element.textContent = wishlistCount;
                element.style.display = wishlistCount > 0 ? 'flex' : 'none';
            });
        }

        // Обновление UI сравнения
        updateCompareUI() {
            const compareCount = this.state.compare.length;
            
            document.querySelectorAll('.compare-count').forEach(element => {
                element.textContent = compareCount;
                element.style.display = compareCount > 0 ? 'flex' : 'none';
            });
        }

        // Обновление отображения валюты
        updateCurrencyDisplay() {
            document.querySelectorAll('[data-currency]').forEach(element => {
                const value = parseFloat(element.dataset.value || element.textContent);
                if (!isNaN(value)) {
                    element.textContent = this.formatPrice(value);
                }
            });
        }

        // Настройка аналитики
        setupAnalytics() {
            this.trackPageView();
            this.setupEventTracking();
            this.setupErrorTracking();
        }

        // Отслеживание просмотра страницы
        trackPageView() {
            const pageData = {
                url: window.location.href,
                path: window.location.pathname,
                title: document.title,
                referrer: document.referrer,
                timestamp: Date.now(),
                sessionId: this.state.session.id
            };
            
            this.sendAnalyticsEvent('page_view', pageData);
            this.state.session.pageViews++;
        }

        // Отслеживание событий
        setupEventTracking() {
            document.addEventListener('click', (e) => {
                const button = e.target.closest('button, .btn, [role="button"]');
                if (button) {
                    this.trackEvent('button', 'click', {
                        text: button.textContent.trim(),
                        id: button.id,
                        class: button.className,
                        href: button.getAttribute('href')
                    });
                }
            });
        }

        // Отслеживание события
        trackEvent(category, action, data) {
            this.sendAnalyticsEvent(`${category}_${action}`, data);
        }

        // Отправка события в аналитику
        async sendAnalyticsEvent(eventName, data) {
            const eventData = {
                event: eventName,
                timestamp: Date.now(),
                session: this.state.session,
                user: this.state.user ? {
                    id: this.state.user.id,
                    email: this.state.user.email
                } : null,
                page: {
                    url: window.location.href,
                    title: document.title,
                    referrer: document.referrer
                },
                device: {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    platform: navigator.platform,
                    screen: {
                        width: window.screen.width,
                        height: window.screen.height
                    },
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                },
                data: data
            };
            
            if (this.config.debug) {
                console.log('Analytics Event:', eventData);
            }
            
            try {
                await fetch(`${this.config.apiBase}/analytics/track`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(eventData)
                });
            } catch (error) {
                console.error('Ошибка отправки аналитики:', error);
            }
        }

        // Отслеживание ошибок
        setupErrorTracking() {
            window.addEventListener('error', (e) => {
                this.trackError('JavaScript Error', {
                    message: e.message,
                    filename: e.filename,
                    lineno: e.lineno,
                    colno: e.colno,
                    stack: e.error?.stack
                });
            });
            
            window.addEventListener('unhandledrejection', (e) => {
                this.trackError('Unhandled Promise Rejection', {
                    reason: e.reason?.toString(),
                    stack: e.reason?.stack
                });
            });
        }

        // Трекинг ошибок
        trackError(type, data) {
            this.sendAnalyticsEvent(`error_${type}`, data);
        }

        // Глобальный обработчик ошибок
        setupGlobalErrorHandler() {
            window.onerror = (message, source, lineno, colno, error) => {
                this.trackError('Global Error', {
                    message,
                    source,
                    lineno,
                    colno,
                    stack: error?.stack
                });
                
                if (!this.config.debug) {
                    this.showMainNotification('Произошла ошибка. Попробуйте обновить страницу.', 'error');
                }
                
                return false;
            };
        }

        // Запуск периодических задач
        startPeriodicTasks() {
            setInterval(() => {
                this.state.session.duration = Date.now() - this.state.session.startTime;
            }, 60000);
            
            setInterval(() => {
                this.autoSave();
            }, 30000);
            
            if (this.state.user) {
                setInterval(() => {
                    this.checkForNotifications();
                }, 60000);
            }
            
            setInterval(() => {
                this.syncData();
            }, 120000);
        }

        // Автосохранение
        autoSave() {
            const saveData = {
                cart: this.modules.cartManager ? this.modules.cartManager.getCartItems() : [],
                wishlist: this.state.wishlist,
                compare: this.state.compare,
                preferences: this.state.preferences,
                timestamp: Date.now()
            };
            
            try {
                localStorage.setItem('autosave', JSON.stringify(saveData));
            } catch (error) {
                console.error('Ошибка автосохранения:', error);
            }
        }

        // Проверка новых уведомлений
        async checkForNotifications() {
            try {
                const response = await fetch(`${this.config.apiBase}/notifications/unread`, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.notifications.length > 0) {
                        this.showNewNotifications(data.notifications);
                    }
                }
            } catch (error) {
                // Игнорируем ошибки при проверке уведомлений
            }
        }

        // Синхронизация данных
        async syncData() {
            // Сохраняем корзину
            localStorage.setItem('cart', JSON.stringify(this.state.cart));
            
            // Сохраняем избранное
            localStorage.setItem('wishlist', JSON.stringify(this.state.wishlist));
            
            // Сохраняем сравнение
            localStorage.setItem('compare', JSON.stringify(this.state.compare));
        }

        // Синхронизация оффлайн данных
        async syncOfflineData() {
            const offlineActions = JSON.parse(localStorage.getItem('offline_actions') || '[]');
            
            if (offlineActions.length > 0) {
                this.showMainNotification('Синхронизация оффлайн данных...', 'info');
                
                for (const action of offlineActions) {
                    try {
                        await fetch(action.url, action.options);
                    } catch (error) {
                        console.error('Ошибка синхронизации:', error);
                    }
                }
                
                localStorage.removeItem('offline_actions');
                this.showMainNotification('Синхронизация завершена', 'success');
            }
        }

        // Показать новые уведомления
        showNewNotifications(notifications) {
            notifications.forEach(notification => {
                this.showMainNotification(notification.message, notification.type || 'info');
            });
            
            const notificationCount = document.querySelector('.notification-count');
            if (notificationCount) {
                const currentCount = parseInt(notificationCount.textContent) || 0;
                notificationCount.textContent = currentCount + notifications.length;
                notificationCount.style.display = 'flex';
            }
        }

        // Показать уведомление приложения
        showMainNotification(message, type = 'info') {
            if (this.modules.notifications) {
                this.modules.notifications.show(message, type);
            } else {
                const notification = document.createElement('div');
                notification.className = `main-notification main-notification-${type}`;
                notification.innerHTML = `
                    <div class="main-notification-content">
                        <i class="${this.getNotificationIcon(type)}"></i>
                        <span>${message}</span>
                        <button class="main-notification-close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${this.getNotificationColor(type)};
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    z-index: 9999;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    animation: slideInRight 0.3s ease;
                `;
                
                document.body.appendChild(notification);
                
                setTimeout(() => notification.classList.add('show'), 10);
                
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                }, 5000);
                
                notification.querySelector('.main-notification-close').addEventListener('click', () => {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                });
            }
        }

        // Получение иконки для уведомления
        getNotificationIcon(type) {
            const icons = {
                'success': 'fas fa-check-circle',
                'error': 'fas fa-exclamation-circle',
                'warning': 'fas fa-exclamation-triangle',
                'info': 'fas fa-info-circle'
            };
            return icons[type] || icons.info;
        }

        // Получение цвета уведомления
        getNotificationColor(type) {
            const colors = {
                'success': '#10b981',
                'error': '#ef4444',
                'warning': '#f59e0b',
                'info': '#d4af37'
            };
            return colors[type] || colors.info;
        }

        // Диспатч событий
        dispatchEvent(eventName, data = {}) {
            const event = new CustomEvent(eventName, {
                detail: {
                    app: this,
                    timestamp: Date.now(),
                    ...data
                }
            });
            
            document.dispatchEvent(event);
            
            if (this.config.debug) {
                console.log(`Event: ${eventName}`, data);
            }
        }

        // Генерация ID сессии
        generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        // Проверка типа страницы
        isCatalogPage() {
            return document.querySelector('.catalog-page') !== null ||
                   window.location.pathname.includes('/catalog');
        }

        // Фокус на поиск
        focusSearch() {
            const searchInput = document.querySelector('.search-input, input[type="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Сохранение состояния страницы
        savePageState() {
            const state = {
                scrollPosition: window.pageYOffset,
                activeModals: Array.from(document.querySelectorAll('.modal.active')).map(m => m.id),
                activeDropdowns: Array.from(document.querySelectorAll('.dropdown.active')).map(d => d.id),
                formData: this.collectFormData()
            };
            
            sessionStorage.setItem('pageState', JSON.stringify(state));
            this.showMainNotification('Состояние страницы сохранено', 'info');
        }

        // Восстановление состояния страницы
        restorePageState() {
            const savedState = sessionStorage.getItem('pageState');
            if (savedState) {
                const state = JSON.parse(savedState);
                
                window.scrollTo(0, state.scrollPosition || 0);
                
                state.activeModals.forEach(modalId => this.openModal(modalId));
                
                this.showMainNotification('Состояние страницы восстановлено', 'info');
            }
        }

        // Сбор данных форм
        collectFormData() {
            const formData = {};
            document.querySelectorAll('form').forEach(form => {
                const data = new FormData(form);
                const formObject = {};
                for (let [key, value] of data.entries()) {
                    formObject[key] = value;
                }
                formData[form.id || 'form_' + Date.now()] = formObject;
            });
            return formData;
        }

        // Обновление UI компонентов
        updateUIComponents(data) {
            // Реализация обновления UI
        }

        // Показать индикатор загрузки
        showLoading(message = 'Загрузка...') {
            let loader = document.getElementById('global-loader');
            
            if (!loader) {
                loader = document.createElement('div');
                loader.id = 'global-loader';
                loader.className = 'global-loader';
                loader.innerHTML = `
                    <div class="loader-content">
                        <div class="loader-spinner">
                            <i class="fas fa-spinner fa-spin"></i>
                        </div>
                        <div class="loader-text">${message}</div>
                    </div>
                `;
                
                loader.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 99999;
                `;
                
                document.body.appendChild(loader);
            }
            
            loader.style.display = 'flex';
        }

        // Скрыть индикатор загрузки
        hideLoading() {
            const loader = document.getElementById('global-loader');
            if (loader) {
                loader.style.display = 'none';
            }
        }

        // Получение позиции элемента
        getElementPosition(element) {
            const rect = element.getBoundingClientRect();
            return {
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height
            };
        }

        // Утилиты

        // Форматирование цены
        formatPrice(amount) {
            if (amount === undefined || amount === null) return '0 ₽';
            return new Intl.NumberFormat('ru-RU', {
                style: 'currency',
                currency: 'RUB',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
                currencyDisplay: 'symbol'
            }).format(amount).replace('RUB', '₽');
        }

        // Форматирование даты
        formatDate(date, format = 'long') {
            if (!date) return '';
            
            const dateObj = new Date(date);
            if (isNaN(dateObj.getTime())) return '';
            
            const options = {
                year: 'numeric',
                month: format === 'short' ? 'short' : 'long',
                day: 'numeric'
            };
            
            if (format === 'long') {
                options.hour = '2-digit';
                options.minute = '2-digit';
            }
            
            return dateObj.toLocaleDateString('ru-RU', options);
        }

        // Дебаунс функция
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }

        // Троттлинг функция
        throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }

        // Копирование в буфер обмена
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showMainNotification('Скопировано в буфер обмена', 'success');
                return true;
            } catch (error) {
                console.error('Ошибка копирования:', error);
                
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                this.showMainNotification('Скопировано в буфер обмена', 'success');
                return true;
            }
        }

        // Получение параметров URL
        getUrlParams() {
            const params = new URLSearchParams(window.location.search);
            const result = {};
            for (const [key, value] of params) {
                result[key] = value;
            }
            return result;
        }

        // Установка параметров URL
        setUrlParams(params) {
            const url = new URL(window.location);
            Object.entries(params).forEach(([key, value]) => {
                url.searchParams.set(key, value);
            });
            window.history.pushState({}, '', url);
        }

        // Валидация email
        validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        }

        // Проверка сильного пароля
        isStrongPassword(password) {
            const minLength = 8;
            const hasUpperCase = /[A-Z]/.test(password);
            const hasLowerCase = /[a-z]/.test(password);
            const hasNumbers = /\d/.test(password);
            const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
            
            return password.length >= minLength && 
                   hasUpperCase && 
                   hasLowerCase && 
                   hasNumbers && 
                   hasSpecialChar;
        }

        // Анимация элемента
        animateElement(element, animation, duration = 300) {
            element.style.animation = `${animation} ${duration}ms ease`;
            
            setTimeout(() => {
                element.style.animation = '';
            }, duration);
        }

        // Плавная прокрутка к элементу
        smoothScrollTo(element, offset = 0) {
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;
            
            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }

        // Удаление обработчиков событий
        removeEventListeners() {
            // Очищаем все обработчики
            window.removeEventListener('scroll', this.handleScroll);
            window.removeEventListener('resize', this.handleResize);
            window.removeEventListener('online', this.handleOnlineStatus);
            window.removeEventListener('offline', this.handleOfflineStatus);
            
            document.removeEventListener('click', this.handleNavigation);
            document.removeEventListener('submit', this.handleFormSubmit);
            document.removeEventListener('keydown', this.handleKeyDown);
            document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        }

        // Очистка интервалов
        clearAllIntervals() {
            // Получаем максимальный ID интервала
            const intervalId = window.setInterval(() => {}, 0);
            while (intervalId--) {
                window.clearInterval(intervalId);
            }
        }

        // Завершение работы приложения
        destroy() {
            this.autoSave();
            this.clearAllIntervals();
            this.removeEventListeners();
            this.dispatchEvent('app:destroyed');
            console.log('VOGUE ÉLITE приложение завершено');
        }
    }

    // Инициализация приложения при загрузке страницы
    document.addEventListener('DOMContentLoaded', () => {
        // Создаем глобальный объект приложения
        window.VogueEliteAppInstance = new VogueEliteApp();
        
        console.log('🎉 VOGUE ÉLITE приложение готово!');
    });

    // Обработка завершения работы
    window.addEventListener('beforeunload', (e) => {
        if (window.VogueEliteAppInstance) {
            window.VogueEliteAppInstance.destroy();
        }
    });

    // Экспорт классов для использования в других файлах
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { VogueEliteApp, NotificationManager, UIManager, AuthManager, AnalyticsManager };
    }
}
