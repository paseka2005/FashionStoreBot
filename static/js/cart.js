// cart.js - Модуль управления корзиной покупок для роскошного магазина VOGUE ÉLITE

class CartManager {
    constructor() {
        this.cartItems = [];
        this.cartKey = 'vogue_elite_cart';
        this.apiBase = '/api/cart';
        this.productCache = new Map();
        this.isInitialized = false;
        this.cartOpen = false;
        console.log('CartManager конструктор вызван');
    }

    // Инициализация корзины
    async init() {
        if (this.isInitialized) {
            console.log('CartManager уже инициализирован');
            return;
        }
        
        try {
            console.log('Инициализация CartManager...');
            await this.loadFromLocalStorage();
            this.setupEventListeners();
            this.setupCartNotifications();
            this.updateCartUI();
            this.addCartStyles();
            this.isInitialized = true;
            console.log('CartManager успешно инициализирован');
        } catch (error) {
            console.error('Ошибка инициализации CartManager:', error);
        }
    }

    // Загрузка корзины из LocalStorage
    async loadFromLocalStorage() {
        try {
            const savedCart = localStorage.getItem(this.cartKey);
            if (savedCart) {
                this.cartItems = JSON.parse(savedCart);
                console.log('Корзина загружена из LocalStorage, элементов:', this.cartItems.length);
            } else {
                console.log('Корзина в LocalStorage не найдена');
            }
        } catch (error) {
            console.error('Ошибка загрузки корзины из LocalStorage:', error);
            this.cartItems = [];
        }
    }

    // Сохранение корзины в LocalStorage
    saveToLocalStorage() {
        try {
            localStorage.setItem(this.cartKey, JSON.stringify(this.cartItems));
            console.log('Корзина сохранена в LocalStorage');
        } catch (error) {
            console.error('Ошибка сохранения корзины в LocalStorage:', error);
        }
    }

    // Добавление товара в корзину
    async addItem(productId, quantity = 1, options = {}) {
        console.log('Добавление товара в корзину:', productId, quantity, options);
        
        try {
            // Проверяем авторизацию
            const isAuthenticated = await this.checkAuth();
            if (!isAuthenticated) {
                this.showNotification('Для добавления в корзину необходимо войти в систему', 'warning');
                window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
                return false;
            }

            // Получаем информацию о товаре
            const product = await this.fetchProductDetails(productId);
            if (!product) {
                this.showNotification('Товар не найден', 'error');
                return false;
            }

            // Проверка наличия на складе
            if (product.stock < quantity) {
                this.showNotification(`Доступно только ${product.stock} шт. на складе`, 'warning');
                quantity = Math.min(quantity, product.stock);
                if (quantity <= 0) return false;
            }

            // Поиск существующего товара в корзине
            const existingItem = this.cartItems.find(item => 
                item.product_id == productId && 
                this.compareOptions(item.options, options)
            );

            if (existingItem) {
                // Увеличиваем количество
                const newQuantity = existingItem.quantity + quantity;
                if (newQuantity > product.stock) {
                    this.showNotification(`Нельзя добавить больше ${product.stock} шт.`, 'warning');
                    existingItem.quantity = product.stock;
                } else {
                    existingItem.quantity = newQuantity;
                }
                this.showNotification(`Количество товара обновлено: ${existingItem.quantity} шт.`, 'info');
            } else {
                // Добавляем новый товар
                const cartItem = {
                    id: this.generateId(),
                    product_id: productId,
                    product: {
                        id: product.id,
                        name: product.name,
                        price: product.price,
                        image_url: product.image_url || '/static/img/placeholder.jpg',
                        category: product.category,
                        stock: product.stock,
                        discount: product.discount || 0
                    },
                    quantity: quantity,
                    options: options,
                    added_at: new Date().toISOString(),
                    selected_size: options.size,
                    selected_color: options.color
                };

                this.cartItems.push(cartItem);
                this.showNotification('Товар добавлен в корзину!', 'success');
            }

            this.saveToLocalStorage();
            this.updateCartUI();
            
            // Анимация добавления
            this.playAddAnimation(productId);
            
            // Отправляем событие
            this.dispatchCartEvent('itemAdded', { product, quantity });
            
            return true;
        } catch (error) {
            console.error('Ошибка добавления товара:', error);
            this.showNotification('Ошибка добавления товара', 'error');
            return false;
        }
    }

    // Обновление количества товара
    async updateQuantity(itemId, newQuantity) {
        console.log('Обновление количества:', itemId, newQuantity);
        
        const item = this.cartItems.find(item => item.id === itemId);
        if (!item) {
            console.error('Элемент корзины не найден:', itemId);
            return false;
        }

        try {
            const product = await this.fetchProductDetails(item.product_id);
            if (!product) {
                this.showNotification('Информация о товаре не найдена', 'error');
                return false;
            }

            newQuantity = parseInt(newQuantity);
            if (isNaN(newQuantity) || newQuantity < 1) {
                newQuantity = 1;
            }

            if (newQuantity > product.stock) {
                this.showNotification(`Доступно только ${product.stock} шт. на складе`, 'warning');
                newQuantity = product.stock;
            }

            item.quantity = newQuantity;
            this.saveToLocalStorage();
            this.updateCartUI();

            this.showNotification(`Количество обновлено: ${newQuantity} шт.`, 'info');
            
            // Отправляем событие
            this.dispatchCartEvent('quantityUpdated', { itemId, newQuantity });
            
            return true;
        } catch (error) {
            console.error('Ошибка обновления количества:', error);
            this.showNotification('Ошибка обновления количества', 'error');
            return false;
        }
    }

    // Удаление товара из корзины
    async removeItem(itemId) {
        console.log('Удаление товара из корзины:', itemId);
        
        const itemIndex = this.cartItems.findIndex(item => item.id === itemId);
        if (itemIndex === -1) {
            console.error('Элемент корзины не найден для удаления:', itemId);
            return false;
        }

        const item = this.cartItems[itemIndex];
        
        // Анимация удаления
        this.playRemoveAnimation(itemId);

        // Удаляем после анимации
        setTimeout(() => {
            this.cartItems.splice(itemIndex, 1);
            this.saveToLocalStorage();
            this.updateCartUI();
            this.showNotification('Товар удален из корзины', 'info');
            
            // Отправляем событие
            this.dispatchCartEvent('itemRemoved', { itemId });
        }, 300);

        return true;
    }

    // Очистка корзины
    async clearCart() {
        console.log('Очистка корзины');
        
        if (this.cartItems.length === 0) {
            this.showNotification('Корзина уже пуста', 'info');
            return false;
        }

        if (!confirm('Вы уверены, что хотите очистить корзину?')) {
            return false;
        }

        // Анимация очистки
        this.playClearAnimation();

        setTimeout(() => {
            this.cartItems = [];
            this.saveToLocalStorage();
            this.updateCartUI();
            this.showNotification('Корзина очищена', 'info');
            
            // Отправляем событие
            this.dispatchCartEvent('cartCleared');
        }, this.cartItems.length * 100);

        return true;
    }

    // Получение информации о товаре
    async fetchProductDetails(productId) {
        console.log('Получение информации о товаре:', productId);
        
        // Сначала пробуем получить из кэша
        if (this.productCache.has(productId)) {
            const cached = this.productCache.get(productId);
            if (Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 минут
                console.log('Товар найден в кэше:', productId);
                return cached.data;
            }
        }

        try {
            // Запрашиваем с сервера
            console.log('Запрос товара с сервера:', productId);
            const response = await fetch(`/api/products/${productId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.product) {
                    this.productCache.set(productId, {
                        data: data.product,
                        timestamp: Date.now()
                    });
                    console.log('Товар получен с сервера:', productId);
                    return data.product;
                }
            }
        } catch (error) {
            console.error('Ошибка получения информации о товаре:', error);
        }

        // Возвращаем базовые данные из локальной корзины
        const cartItem = this.cartItems.find(item => item.product_id == productId);
        if (cartItem) {
            console.log('Товар найден в локальной корзине:', productId);
            return cartItem.product;
        }

        // Или минимальные данные
        console.log('Товар не найден, возвращаем базовые данные:', productId);
        return {
            id: productId,
            name: 'Товар',
            price: 1000,
            image_url: '/static/img/placeholder.jpg',
            category: 'Категория',
            stock: 10,
            discount: 0
        };
    }

    // Сравнение опций товара
    compareOptions(options1, options2) {
        const keys1 = Object.keys(options1 || {});
        const keys2 = Object.keys(options2 || {});
        
        if (keys1.length !== keys2.length) return false;
        
        for (let key of keys1) {
            if (options1[key] !== options2[key]) {
                return false;
            }
        }
        
        return true;
    }

    // Генерация уникального ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
    }

    // Обновление UI корзины
    updateCartUI() {
        console.log('Обновление UI корзины');
        this.updateCartCount();
        this.updateCartTotal();
        this.updateCartDropdown();
        this.updateCartPage();
    }

    // Обновление счетчика корзины
    updateCartCount() {
        const totalItems = this.getTotalItems();
        console.log('Обновление счетчика корзины:', totalItems);
        
        // Обновляем счетчики в шапке
        const cartCountElements = document.querySelectorAll('.cart-count, #cart-count, .mobile-cart-count');
        cartCountElements.forEach(element => {
            if (element) {
                element.textContent = totalItems;
                element.style.display = totalItems > 0 ? 'flex' : 'none';
            }
        });

        // Обновляем иконку корзины
        const cartIcon = document.querySelector('.cart-link, .header-cart, [href="/cart"]');
        if (cartIcon) {
            cartIcon.setAttribute('data-count', totalItems);
            if (totalItems > 0) {
                cartIcon.classList.add('has-items');
            } else {
                cartIcon.classList.remove('has-items');
            }
        }
    }

    // Обновление общей суммы
    updateCartTotal() {
        const total = this.getTotalPrice();
        console.log('Обновление общей суммы:', total);

        const totalElements = document.querySelectorAll('.cart-total, #cart-total');
        totalElements.forEach(element => {
            if (element) {
                if (element.tagName === 'INPUT') {
                    element.value = total.toFixed(2);
                } else {
                    element.textContent = `${this.formatPrice(total)} ₽`;
                }
            }
        });
    }

    // Обновление выпадающего списка корзины
    updateCartDropdown() {
        const dropdown = document.getElementById('cart-dropdown');
        if (!dropdown) {
            console.log('Выпадающий список корзины не найден');
            return;
        }

        if (this.cartItems.length === 0) {
            dropdown.innerHTML = `
                <div class="cart-dropdown-empty">
                    <i class="fas fa-shopping-cart" style="font-size: 48px; color: var(--text-tertiary); margin-bottom: 15px;"></i>
                    <p style="color: var(--text-secondary); margin-bottom: 20px;">Ваша корзина пуста</p>
                    <a href="/catalog" class="btn-view" style="display: inline-block; padding: 10px 20px; background: var(--gold); color: white; border-radius: var(--radius-lg); text-decoration: none;">Перейти в каталог</a>
                </div>
            `;
            return;
        }

        let itemsHTML = '';
        let subtotal = 0;

        this.cartItems.slice(0, 3).forEach(item => {
            const price = item.product.price * (1 - (item.product.discount || 0) / 100);
            const itemTotal = price * item.quantity;
            subtotal += itemTotal;

            itemsHTML += `
                <div class="cart-dropdown-item" data-item-id="${item.id}" style="
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    border-bottom: 1px solid var(--border-color);
                    transition: background 0.2s;
                ">
                    <div class="cart-dropdown-item-image" style="
                        width: 60px;
                        height: 60px;
                        margin-right: 15px;
                        flex-shrink: 0;
                    ">
                        <img src="${item.product.image_url}" 
                             alt="${item.product.name}"
                             style="width: 100%; height: 100%; object-fit: cover; border-radius: var(--radius-sm);"
                             onerror="this.src='/static/img/placeholder.jpg';"
                             loading="lazy">
                    </div>
                    <div class="cart-dropdown-item-info" style="flex: 1;">
                        <div class="cart-dropdown-item-name" style="
                            font-weight: 500;
                            margin-bottom: 5px;
                            font-size: 0.9rem;
                            color: var(--text-primary);
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        ">${item.product.name}</div>
                        <div class="cart-dropdown-item-details" style="
                            display: flex;
                            gap: 10px;
                            margin-bottom: 5px;
                            font-size: 0.8rem;
                            color: var(--text-secondary);
                        ">
                            ${item.selected_size ? `<span>Размер: ${item.selected_size}</span>` : ''}
                            ${item.selected_color ? `<span>Цвет: ${item.selected_color}</span>` : ''}
                        </div>
                        <div class="cart-dropdown-item-price" style="
                            font-weight: 600;
                            color: var(--gold);
                            font-size: 0.9rem;
                        ">${item.quantity} × ${this.formatPrice(price)} ₽</div>
                    </div>
                    <button class="cart-dropdown-item-remove" data-item-id="${item.id}" style="
                        background: none;
                        border: none;
                        color: var(--text-tertiary);
                        cursor: pointer;
                        padding: 5px;
                        margin-left: 10px;
                        transition: color 0.2s;
                    ">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        });

        const itemsCount = this.cartItems.length;
        const moreItems = itemsCount > 3 ? itemsCount - 3 : 0;

        dropdown.innerHTML = `
            <div class="cart-dropdown-header" style="
                padding: 20px 20px 15px;
                border-bottom: 1px solid var(--border-color);
            ">
                <h4 style="margin: 0; font-size: 1.1rem; color: var(--text-primary);">
                    Корзина (${itemsCount} ${this.getPluralForm(itemsCount, ['товар', 'товара', 'товаров'])})
                </h4>
            </div>
            <div class="cart-dropdown-items" style="max-height: 300px; overflow-y: auto;">
                ${itemsHTML}
            </div>
            ${moreItems > 0 ? `
                <div class="cart-dropdown-more" style="
                    padding: 15px 20px;
                    text-align: center;
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                    border-top: 1px solid var(--border-color);
                ">
                    И еще ${moreItems} ${this.getPluralForm(moreItems, ['товар', 'товара', 'товаров'])}...
                </div>
            ` : ''}
            <div class="cart-dropdown-footer" style="
                padding: 20px;
                border-top: 1px solid var(--border-color);
            ">
                <div class="cart-dropdown-subtotal" style="
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                    font-weight: 600;
                    color: var(--text-primary);
                ">
                    <span>Промежуточный итог:</span>
                    <span class="cart-dropdown-total">${this.formatPrice(subtotal)} ₽</span>
                </div>
                <div class="cart-dropdown-actions" style="
                    display: flex;
                    gap: 10px;
                ">
                    <a href="/cart" class="btn-view" style="
                        flex: 1;
                        padding: 12px;
                        background: var(--surface-bg);
                        color: var(--text-primary);
                        text-decoration: none;
                        border-radius: var(--radius-lg);
                        text-align: center;
                        transition: background 0.2s;
                    ">Перейти в корзину</a>
                    <a href="/checkout" class="btn-checkout" style="
                        flex: 1;
                        padding: 12px;
                        background: var(--gold);
                        color: white;
                        text-decoration: none;
                        border-radius: var(--radius-lg);
                        text-align: center;
                        transition: background 0.2s;
                    ">Оформить заказ</a>
                </div>
            </div>
        `;

        // Добавляем обработчики для кнопок удаления
        dropdown.querySelectorAll('.cart-dropdown-item-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const itemId = btn.dataset.itemId;
                this.removeItem(itemId);
            });
        });
        
        // Добавляем обработчики для ссылок
        dropdown.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeCartDropdown();
            });
        });
    }

    // Обновление страницы корзины
    updateCartPage() {
        const cartPage = document.querySelector('.cart-page, #cart-page');
        if (!cartPage) {
            return;
        }

        const cartItemsContainer = document.querySelector('.cart-items-list, #cart-items, .cart-items');
        if (!cartItemsContainer) {
            return;
        }

        if (this.cartItems.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="cart-empty" style="
                    text-align: center;
                    padding: 60px 20px;
                ">
                    <div class="cart-empty-icon" style="
                        font-size: 64px;
                        color: var(--text-tertiary);
                        margin-bottom: 20px;
                    ">
                        <i class="fas fa-shopping-cart"></i>
                    </div>
                    <h2 style="color: var(--text-primary); margin-bottom: 15px;">Ваша корзина пуста</h2>
                    <p style="color: var(--text-secondary); margin-bottom: 30px; max-width: 500px; margin-left: auto; margin-right: auto;">
                        Похоже, вы еще ничего не добавили в корзину. Посмотрите наши эксклюзивные коллекции!
                    </p>
                    <div class="cart-empty-actions">
                        <a href="/catalog" class="btn-primary" style="
                            display: inline-flex;
                            align-items: center;
                            gap: 10px;
                            padding: 15px 30px;
                            background: var(--gold);
                            color: white;
                            border-radius: var(--radius-lg);
                            text-decoration: none;
                            font-weight: 600;
                        ">
                            <i class="fas fa-shopping-bag"></i>
                            <span>Перейти в каталог</span>
                        </a>
                    </div>
                </div>
            `;
            return;
        }

        let itemsHTML = '';
        let subtotal = 0;

        this.cartItems.forEach(item => {
            const price = item.product.price * (1 - (item.product.discount || 0) / 100);
            const itemTotal = price * item.quantity;
            subtotal += itemTotal;

            itemsHTML += `
                <div class="cart-item" data-item-id="${item.id}" style="
                    display: grid;
                    grid-template-columns: 100px 2fr 150px 120px 120px 50px;
                    gap: 20px;
                    padding: 20px;
                    border-bottom: 1px solid var(--border-color);
                    align-items: center;
                    transition: background 0.2s;
                ">
                    <div class="cart-item-image" style="
                        width: 100px;
                        height: 100px;
                    ">
                        <img src="${item.product.image_url}" 
                             alt="${item.product.name}"
                             style="width: 100%; height: 100%; object-fit: cover; border-radius: var(--radius-md);"
                             onerror="this.src='/static/img/placeholder.jpg';"
                             loading="lazy">
                    </div>
                    <div class="cart-item-info">
                        <div class="cart-item-category" style="
                            font-size: 0.8rem;
                            color: var(--text-tertiary);
                            margin-bottom: 5px;
                            text-transform: uppercase;
                        ">${item.product.category}</div>
                        <h3 class="cart-item-name" style="
                            margin: 0 0 10px 0;
                            font-size: 1.1rem;
                            color: var(--text-primary);
                        ">
                            <a href="/product/${item.product_id}" style="
                                color: inherit;
                                text-decoration: none;
                                transition: color 0.2s;
                            ">${item.product.name}</a>
                        </h3>
                        <div class="cart-item-variants" style="
                            display: flex;
                            gap: 10px;
                            flex-wrap: wrap;
                        ">
                            ${item.selected_size ? `
                                <span class="variant-badge" style="
                                    padding: 4px 8px;
                                    background: var(--surface-bg);
                                    border-radius: var(--radius-sm);
                                    font-size: 0.8rem;
                                    color: var(--text-secondary);
                                ">
                                    <span class="variant-label" style="color: var(--text-tertiary);">Размер:</span>
                                    <span style="font-weight: 500;">${item.selected_size}</span>
                                </span>
                            ` : ''}
                            ${item.selected_color ? `
                                <span class="variant-badge" style="
                                    padding: 4px 8px;
                                    background: var(--surface-bg);
                                    border-radius: var(--radius-sm);
                                    font-size: 0.8rem;
                                    color: var(--text-secondary);
                                ">
                                    <span class="variant-label" style="color: var(--text-tertiary);">Цвет:</span>
                                    <span style="font-weight: 500;">${item.selected_color}</span>
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="cart-item-quantity">
                        <div class="quantity-controls" style="
                            display: flex;
                            align-items: center;
                            border: 1px solid var(--border-color);
                            border-radius: var(--radius-md);
                            overflow: hidden;
                            width: fit-content;
                        ">
                            <button class="quantity-btn decrease" data-item-id="${item.id}" data-delta="-1" style="
                                width: 36px;
                                height: 36px;
                                background: var(--surface-bg);
                                border: none;
                                cursor: pointer;
                                color: var(--text-primary);
                                transition: background 0.2s;
                            ">
                                <i class="fas fa-minus"></i>
                            </button>
                            <input type="number" 
                                   class="quantity-input" 
                                   value="${item.quantity}" 
                                   min="1" 
                                   max="${item.product.stock}"
                                   data-item-id="${item.id}"
                                   style="
                                    width: 50px;
                                    height: 36px;
                                    border: none;
                                    text-align: center;
                                    font-weight: 500;
                                    background: transparent;
                                    color: var(--text-primary);
                                   ">
                            <button class="quantity-btn increase" data-item-id="${item.id}" data-delta="1" style="
                                width: 36px;
                                height: 36px;
                                background: var(--surface-bg);
                                border: none;
                                cursor: pointer;
                                color: var(--text-primary);
                                transition: background 0.2s;
                            ">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="cart-item-price" style="
                        font-weight: 600;
                        color: var(--text-primary);
                        font-size: 1.1rem;
                    ">
                        ${this.formatPrice(price)} <span class="price-unit">₽</span>
                    </div>
                    <div class="cart-item-total" style="
                        font-weight: 700;
                        color: var(--gold);
                        font-size: 1.2rem;
                    ">
                        ${this.formatPrice(itemTotal)} ₽
                    </div>
                    <button class="cart-item-remove" data-item-id="${item.id}" style="
                        background: none;
                        border: none;
                        color: var(--text-tertiary);
                        cursor: pointer;
                        font-size: 1.1rem;
                        transition: color 0.2s;
                    ">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        });

        cartItemsContainer.innerHTML = itemsHTML;
        
        // Обновляем итоги
        const deliveryCost = subtotal >= 200000 ? 0 : 2000;
        const total = subtotal + deliveryCost;

        const subtotalEl = document.getElementById('subtotal');
        const deliveryCostEl = document.getElementById('delivery-cost');
        const totalAmountEl = document.getElementById('total-amount');
        
        if (subtotalEl) subtotalEl.textContent = `${this.formatPrice(subtotal)} ₽`;
        if (deliveryCostEl) deliveryCostEl.textContent = deliveryCost === 0 ? 'Бесплатно' : `${this.formatPrice(deliveryCost)} ₽`;
        if (totalAmountEl) totalAmountEl.textContent = `${this.formatPrice(total)} ₽`;

        // Обновляем заметку о бесплатной доставке
        const deliveryNote = document.querySelector('.delivery-note');
        if (deliveryNote && subtotal < 200000) {
            const needed = 200000 - subtotal;
            const strongEl = deliveryNote.querySelector('strong');
            if (strongEl) strongEl.textContent = `${this.formatPrice(needed)} ₽`;
            deliveryNote.style.display = 'flex';
        } else if (deliveryNote) {
            deliveryNote.style.display = 'none';
        }

        // Добавляем обработчики событий для новых элементов
        this.setupCartPageEventListeners();
    }

    // Настройка обработчиков событий на странице корзины
    setupCartPageEventListeners() {
        console.log('Настройка обработчиков событий страницы корзины');
        
        // Кнопки изменения количества
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const itemId = btn.dataset.itemId;
                const delta = parseInt(btn.dataset.delta || 0);
                
                if (itemId && delta) {
                    const item = this.cartItems.find(item => item.id === itemId);
                    if (item) {
                        const newQuantity = item.quantity + delta;
                        if (newQuantity >= 1 && newQuantity <= item.product.stock) {
                            this.updateQuantity(itemId, newQuantity);
                        }
                    }
                }
            });
        });

        // Прямое изменение количества через input
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const itemId = input.dataset.itemId;
                const value = parseInt(input.value);
                
                if (itemId && value >= 1) {
                    this.updateQuantity(itemId, value);
                }
            });
        });

        // Удаление товара
        document.querySelectorAll('.cart-item-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const itemId = btn.dataset.itemId;
                if (itemId) {
                    this.removeItem(itemId);
                }
            });
        });
    }

    // Настройка обработчиков событий
    setupEventListeners() {
        console.log('Настройка обработчиков событий корзины');
        
        // Добавление в корзину
        document.addEventListener('click', (e) => {
            const addToCartBtn = e.target.closest('.btn-add-cart, .add-to-cart, [data-action="add-to-cart"]');
            if (addToCartBtn) {
                e.preventDefault();
                const productId = addToCartBtn.dataset.productId || addToCartBtn.dataset.id;
                const quantity = parseInt(addToCartBtn.dataset.quantity || 1);
                
                // Получаем опции товара
                const size = addToCartBtn.dataset.size || '';
                const color = addToCartBtn.dataset.color || '';
                
                this.addItem(productId, quantity, { size, color });
            }
        });

        // Открытие/закрытие выпадающей корзины
        document.addEventListener('click', (e) => {
            const cartIcon = e.target.closest('.cart-link, .header-cart, [href="/cart"]');
            const cartDropdown = document.getElementById('cart-dropdown');
            
            if (cartIcon && cartDropdown) {
                e.preventDefault();
                e.stopPropagation();
                
                if (cartDropdown.style.display === 'block') {
                    this.closeCartDropdown();
                } else {
                    this.openCartDropdown();
                }
            } else if (cartDropdown && !cartDropdown.contains(e.target)) {
                // Закрываем корзину при клике вне ее
                this.closeCartDropdown();
            }
        });

        // Кнопки удаления в выпадающем меню
        document.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.cart-dropdown-item-remove');
            if (removeBtn) {
                e.preventDefault();
                e.stopPropagation();
                const itemId = removeBtn.dataset.itemId;
                if (itemId) {
                    this.removeItem(itemId);
                }
            }
        });

        // Кнопка очистки корзины
        document.addEventListener('click', (e) => {
            const clearBtn = e.target.closest('.clear-cart, [data-action="clear-cart"]');
            if (clearBtn) {
                e.preventDefault();
                this.clearCart();
            }
        });

        // Обработка переходов на страницу корзины
        document.addEventListener('click', (e) => {
            if (e.target.closest('[href="/cart"]') && !e.target.closest('.cart-dropdown')) {
                if (this.cartItems.length === 0) {
                    e.preventDefault();
                    this.showNotification('Корзина пуста', 'info');
                }
            }
        });
    }

    // Открытие выпадающей корзины
    openCartDropdown() {
        const cartDropdown = document.getElementById('cart-dropdown');
        if (!cartDropdown) {
            console.error('Элемент cart-dropdown не найден');
            return;
        }
        
        cartDropdown.style.display = 'block';
        cartDropdown.style.opacity = '0';
        cartDropdown.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            cartDropdown.style.opacity = '1';
            cartDropdown.style.transform = 'translateY(0)';
        }, 10);
        
        this.cartOpen = true;
        console.log('Выпадающая корзина открыта');
    }

    // Закрытие выпадающей корзины
    closeCartDropdown() {
        const cartDropdown = document.getElementById('cart-dropdown');
        if (!cartDropdown) return;
        
        cartDropdown.style.opacity = '0';
        cartDropdown.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            cartDropdown.style.display = 'none';
        }, 300);
        
        this.cartOpen = false;
        console.log('Выпадающая корзина закрыта');
    }

    // Настройка уведомлений о корзине
    setupCartNotifications() {
        document.addEventListener('cart:itemAdded', (e) => {
            const { product, quantity } = e.detail;
            this.showNotification(`${product.name} добавлен в корзину (${quantity} шт.)`, 'success');
        });

        document.addEventListener('cart:updated', () => {
            const totalItems = this.getTotalItems();
            if (totalItems > 0) {
                const totalPrice = this.getTotalPrice();
                this.showNotification(`Корзина обновлена: ${totalItems} товаров на сумму ${this.formatPrice(totalPrice)} ₽`, 'info');
            }
        });
    }

    // Диспатч событий корзины
    dispatchCartEvent(eventName, data = {}) {
        const event = new CustomEvent(`cart:${eventName}`, {
            detail: {
                cart: this,
                timestamp: Date.now(),
                ...data
            }
        });
        
        document.dispatchEvent(event);
    }

    // Показ уведомлений
    showNotification(message, type = 'info') {
        console.log(`Показать уведомление: ${message}, тип: ${type}`);
        
        const notification = document.createElement('div');
        notification.className = `cart-notification cart-notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: cartNotificationSlideIn 0.3s ease;
        `;

        const icon = this.getNotificationIcon(type);
        
        notification.innerHTML = `
            <i class="${icon}" style="font-size: 1.2rem;"></i>
            <span style="flex: 1;">${message}</span>
            <button class="cart-notification-close" style="background: none; border: none; color: white; cursor: pointer;">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        // Close button
        notification.querySelector('.cart-notification-close').addEventListener('click', () => {
            notification.style.animation = 'cartNotificationFadeOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        });

        // Auto hide after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'cartNotificationFadeOut 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 3000);
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

    // Получение иконки уведомления
    getNotificationIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // Анимация добавления товара
    playAddAnimation(productId) {
        const button = document.querySelector(`[data-product-id="${productId}"], [data-id="${productId}"]`);
        if (!button) {
            console.log('Кнопка товара не найдена для анимации:', productId);
            return;
        }

        const flyElement = document.createElement('div');
        flyElement.className = 'cart-fly-animation';
        flyElement.style.cssText = `
            position: fixed;
            width: 40px;
            height: 40px;
            background: #d4af37;
            border-radius: 50%;
            pointer-events: none;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
        `;
        flyElement.innerHTML = '<i class="fas fa-shopping-bag"></i>';

        const buttonRect = button.getBoundingClientRect();
        const cartIcon = document.querySelector('.cart-link, .header-cart, [href="/cart"]');
        const cartRect = cartIcon ? cartIcon.getBoundingClientRect() : { left: window.innerWidth - 100, top: 20 };

        flyElement.style.left = `${buttonRect.left + buttonRect.width / 2 - 20}px`;
        flyElement.style.top = `${buttonRect.top + buttonRect.height / 2 - 20}px`;

        document.body.appendChild(flyElement);

        requestAnimationFrame(() => {
            flyElement.style.transition = 'all 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
            flyElement.style.left = `${cartRect.left + 20}px`;
            flyElement.style.top = `${cartRect.top + 20}px`;
            flyElement.style.transform = 'scale(0.5)';
            flyElement.style.opacity = '0.5';
        });

        setTimeout(() => {
            flyElement.remove();
            
            if (cartIcon) {
                cartIcon.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    cartIcon.style.transform = 'scale(1)';
                }, 200);
            }
        }, 800);
    }

    // Анимация удаления товара
    playRemoveAnimation(itemId) {
        const item = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!item) return;

        item.style.transition = 'all 0.3s ease';
        item.style.opacity = '0';
        item.style.transform = 'translateX(-30px)';
        item.style.height = '0';
        item.style.margin = '0';
        item.style.padding = '0';
        item.style.border = 'none';
    }

    // Анимация очистки корзины
    playClearAnimation() {
        const items = document.querySelectorAll('.cart-item');
        items.forEach((item, index) => {
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '0';
                item.style.transform = 'translateX(-50px)';
                item.style.height = '0';
                item.style.margin = '0';
                item.style.padding = '0';
                item.style.border = 'none';
            }, index * 100);
        });
    }

    // Добавление стилей для корзины
    addCartStyles() {
        if (document.querySelector('#cart-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'cart-styles';
        style.textContent = `
            @keyframes cartNotificationSlideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes cartNotificationFadeOut {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(100%);
                }
            }
            
            .cart-link.has-items::after,
            .header-cart.has-items::after {
                content: attr(data-count);
                position: absolute;
                top: -5px;
                right: -5px;
                min-width: 18px;
                height: 18px;
                background: #ef4444;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                font-weight: bold;
                color: white;
                padding: 2px;
                animation: cartPulse 2s infinite;
            }
            
            @keyframes cartPulse {
                0% {
                    transform: scale(1);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.2);
                    opacity: 0.7;
                }
                100% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            
            #cart-dropdown {
                display: none;
                position: absolute;
                top: 100%;
                right: 0;
                width: 380px;
                background: var(--card-bg);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl);
                z-index: 1000;
                margin-top: 10px;
                transition: all 0.3s ease;
            }
            
            @media (max-width: 768px) {
                #cart-dropdown {
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    width: 100%;
                    max-width: 100%;
                    border-radius: 0;
                    margin: 0;
                }
            }
            
            .cart-dropdown-items::-webkit-scrollbar {
                width: 6px;
            }
            
            .cart-dropdown-items::-webkit-scrollbar-track {
                background: var(--surface-bg);
                border-radius: 3px;
            }
            
            .cart-dropdown-items::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: 3px;
            }
            
            .cart-dropdown-items::-webkit-scrollbar-thumb:hover {
                background: var(--text-tertiary);
            }
            
            .cart-dropdown-item:hover {
                background: var(--surface-bg);
            }
            
            .cart-dropdown-item-remove:hover {
                color: var(--error-color) !important;
            }
            
            .btn-view:hover {
                background: var(--tertiary-bg) !important;
            }
            
            .btn-checkout:hover {
                background: var(--gold-dark) !important;
            }
            
            .quantity-btn:hover {
                background: var(--tertiary-bg) !important;
            }
            
            .cart-item-remove:hover {
                color: var(--error-color) !important;
            }
            
            input[type="number"]::-webkit-inner-spin-button,
            input[type="number"]::-webkit-outer-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }
            
            input[type="number"] {
                -moz-appearance: textfield;
            }
            
            .cart-notification {
                font-family: inherit;
            }
            
            .cart-notification-success {
                background: #10b981;
            }
            
            .cart-notification-error {
                background: #ef4444;
            }
            
            .cart-notification-warning {
                background: #f59e0b;
            }
            
            .cart-notification-info {
                background: #d4af37;
            }
        `;
        document.head.appendChild(style);
        console.log('Стили корзины добавлены');
    }

    // Получение формы множественного числа
    getPluralForm(number, forms) {
        number = Math.abs(number) % 100;
        const remainder = number % 10;
        
        if (number > 10 && number < 20) return forms[2];
        if (remainder > 1 && remainder < 5) return forms[1];
        if (remainder === 1) return forms[0];
        return forms[2];
    }

    // Форматирование цены
    formatPrice(price) {
        if (!price) return '0';
        return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    }

    // Проверка авторизации
    async checkAuth() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();
            return data.is_authenticated || false;
        } catch (error) {
            console.error('Ошибка проверки авторизации:', error);
            return false;
        }
    }

    // Получение общего количества товаров
    getTotalItems() {
        return this.cartItems.reduce((sum, item) => sum + item.quantity, 0);
    }

    // Получение общей суммы
    getTotalPrice() {
        return this.cartItems.reduce((sum, item) => {
            const price = item.product.price * (1 - (item.product.discount || 0) / 100);
            return sum + (price * item.quantity);
        }, 0);
    }

    // Получение содержимого корзины
    getCartItems() {
        return [...this.cartItems];
    }

    // Проверка пустоты корзины
    isEmpty() {
        return this.cartItems.length === 0;
    }
}

// Инициализация корзины при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен, инициализация CartManager...');
    
    if (!window.cartManager) {
        window.cartManager = new CartManager();
        window.cartManager.init();
    }
    
    // Обновляем счетчик корзины при загрузке
    setTimeout(() => {
        if (window.cartManager) {
            window.cartManager.updateCartCount();
        }
    }, 1000);
    
    // Обработка ошибок изображений
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.src = '/static/img/placeholder.jpg';
        }
    }, true);
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CartManager;
}
