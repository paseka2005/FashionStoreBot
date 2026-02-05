// catalog.js - Продвинутый модуль каталога товаров для VOGUE ÉLITE

class CatalogManager {
    constructor() {
        this.products = [];
        this.filteredProducts = [];
        this.filters = {
            category: 'all',
            price: { min: 0, max: 100000 },
            brands: [],
            colors: [],
            sizes: [],
            specials: [],
            sort: 'newest',
            view: 'grid',
            gridSize: 2
        };
        this.currentPage = 1;
        this.productsPerPage = 12;
        this.totalPages = 1;
        this.isLoading = false;
        this.isMobile = window.innerWidth < 768;
        this.imageObserver = null;
        this.scrollObserver = null;
        this.virtualScrollEnabled = false;
        this.loadedImages = new Set();
        
        this.init();
    }

    // Инициализация каталога
    async init() {
        this.setupEventListeners();
        this.setupUI();
        this.setupIntersectionObserver();
        this.setupPerformanceMonitoring();
        
        await this.loadProducts();
        this.applyFilters();
        this.restoreState();
        
        // Инициализация Service Worker
        this.initServiceWorker();
        
        console.log('Модуль каталога инициализирован');
        
        // Замер производительности
        this.measurePerformance('init').end();
    }

    // Загрузка продуктов
    async loadProducts() {
        this.showLoading();
        
        try {
            const response = await fetch('/api/products');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.products = data.products || [];
                    this.trackEvent('products_loaded', {
                        count: this.products.length,
                        source: 'api'
                    });
                } else {
                    this.products = this.getDemoProducts();
                    this.trackEvent('products_loaded', {
                        count: this.products.length,
                        source: 'demo'
                    });
                }
            } else {
                this.products = this.getDemoProducts();
                this.trackEvent('products_loaded', {
                    count: this.products.length,
                    source: 'demo_fallback'
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки продуктов:', error);
            this.products = this.getDemoProducts();
            this.trackEvent('products_load_error', {
                error: error.message,
                source: 'demo_error'
            });
        }
        
        this.hideLoading();
        this.cacheProducts();
    }

    // Получение демо продуктов
    getDemoProducts() {
        const demoProducts = [];
        const categories = ['Платья', 'Костюмы', 'Блузы', 'Брюки'];
        const brands = ['Vogue', 'Dior', 'Chanel', 'Gucci'];
        const colors = ['черный', 'белый', 'красный', 'синий'];
        const sizes = ['XS', 'S', 'M', 'L'];
        
        for (let i = 0; i < 48; i++) {
            const product = {
                id: i + 1,
                name: `Товар ${i + 1}`,
                category: categories[i % 4],
                price: Math.floor(Math.random() * 5000) + 1000,
                discount: i % 5 === 0 ? 20 : i % 7 === 0 ? 15 : 0,
                image_url: `/static/img/products/product-${(i % 12) + 1}.jpg`,
                brand: brands[i % 4],
                color: colors[i % 4],
                size: sizes[i % 4],
                is_new: i < 12,
                is_exclusive: i % 10 === 0,
                is_limited: i % 15 === 0,
                stock: Math.floor(Math.random() * 50) + 5,
                rating: 4 + Math.random(),
                description: 'Эксклюзивный товар премиум-класса с высококачественными материалами и уникальным дизайном',
                created_at: new Date(Date.now() - i * 86400000).toISOString()
            };
            demoProducts.push(product);
        }
        
        return demoProducts;
    }

    // Кэширование продуктов
    cacheProducts() {
        try {
            const cacheData = {
                products: this.products,
                timestamp: Date.now()
            };
            localStorage.setItem('catalog_cache', JSON.stringify(cacheData));
            console.log('Продукты закэшированы');
        } catch (error) {
            console.error('Ошибка кэширования:', error);
        }
    }

    // Настройка UI
    setupUI() {
        this.createQuickViewModal();
        this.setupTooltips();
        this.setupProductCards();
        this.setupFiltersModal();
        this.addAnimations();
    }

    // Настройка обработчиков событий
    setupEventListeners() {
        // Фильтры категорий
        document.addEventListener('click', (event) => {
            const categoryItem = event.target.closest('.category-item');
            if (categoryItem) {
                event.preventDefault();
                const category = categoryItem.dataset.category || 'all';
                this.setFilter('category', category);
                this.trackEvent('category_filter', { category });
            }
        });

        // Фильтр цены
        const priceSlider = document.getElementById('range-min');
        const priceSliderMax = document.getElementById('range-max');
        if (priceSlider && priceSliderMax) {
            priceSlider.addEventListener('input', () => {
                this.updatePriceFilter();
            });
            priceSliderMax.addEventListener('input', () => {
                this.updatePriceFilter();
            });
        }

        // Фильтры брендов
        document.addEventListener('click', (event) => {
            const brandFilter = event.target.closest('.filter-item[data-filter="brand"]');
            if (brandFilter) {
                const brand = brandFilter.dataset.value;
                this.toggleFilter('brands', brand);
                this.trackEvent('brand_filter', { brand, action: 'toggle' });
            }
        });

        // Фильтры цветов
        document.addEventListener('click', (event) => {
            const colorItem = event.target.closest('.color-item');
            if (colorItem) {
                const color = colorItem.dataset.color || colorItem.style.backgroundColor;
                this.setFilter('colors', [color]);
                this.trackEvent('color_filter', { color });
            }
        });

        // Фильтры размеров
        document.addEventListener('click', (event) => {
            const sizeItem = event.target.closest('.size-item');
            if (sizeItem) {
                const size = sizeItem.textContent.trim();
                this.toggleFilter('sizes', size);
                this.trackEvent('size_filter', { size, action: 'toggle' });
            }
        });

        // Специальные фильтры
        document.addEventListener('click', (event) => {
            const specialFilter = event.target.closest('.filter-item[data-filter="special"]');
            if (specialFilter) {
                const special = specialFilter.dataset.value;
                this.toggleFilter('specials', special);
                this.trackEvent('special_filter', { special, action: 'toggle' });
            }
        });

        // Сортировка
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (event) => {
                this.setFilter('sort', event.target.value);
                this.trackEvent('sort', { method: event.target.value });
            });
        }

        // Вид отображения
        document.addEventListener('click', (event) => {
            const viewBtn = event.target.closest('.view-btn');
            if (viewBtn) {
                const view = viewBtn.dataset.view;
                this.setFilter('view', view);
                this.trackEvent('view_change', { view });
            }
        });

        // Размер сетки
        const gridSlider = document.getElementById('grid-size');
        if (gridSlider) {
            gridSlider.addEventListener('input', (event) => {
                this.setFilter('gridSize', parseInt(event.target.value));
                this.trackEvent('grid_size_change', { size: event.target.value });
            });
        }

        // Сброс фильтров
        document.addEventListener('click', (event) => {
            const clearBtn = event.target.closest('.clear-filters');
            if (clearBtn) {
                this.resetFilters();
                this.trackEvent('filters_reset');
            }
        });

        // Поиск
        const searchInput = document.getElementById('catalog-search');
        if (searchInput) {
            const searchHandler = this.debounce(() => {
                this.searchProducts(searchInput.value);
                this.trackEvent('search', { query: searchInput.value });
            }, 300);
            
            searchInput.addEventListener('input', searchHandler);
            searchInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    this.searchProducts(searchInput.value);
                    this.trackEvent('search_enter', { query: searchInput.value });
                }
            });
        }

        // Пагинация
        document.addEventListener('click', (event) => {
            // Клик по кнопкам страниц
            const pageBtn = event.target.closest('.page-btn');
            if (pageBtn && !pageBtn.classList.contains('disabled')) {
                event.preventDefault();
                const page = parseInt(pageBtn.dataset.page) || parseInt(pageBtn.textContent);
                if (page) {
                    this.goToPage(page);
                    this.trackEvent('pagination', { page });
                }
            }
            
            // Клик по кнопке "предыдущая страница"
            if (event.target.closest('#prev-page')) {
                event.preventDefault();
                this.goToPage(this.currentPage - 1);
                this.trackEvent('pagination_prev', { page: this.currentPage - 1 });
            }
            
            // Клик по кнопке "следующая страница"
            if (event.target.closest('#next-page')) {
                event.preventDefault();
                this.goToPage(this.currentPage + 1);
                this.trackEvent('pagination_next', { page: this.currentPage + 1 });
            }
        });

        // Быстрый просмотр
        document.addEventListener('click', (event) => {
            const quickViewBtn = event.target.closest('.quick-view-btn, .action-btn .fa-eye');
            if (quickViewBtn) {
                event.preventDefault();
                const productCard = quickViewBtn.closest('.product-card');
                const productId = productCard ? productCard.dataset.productId : null;
                if (productId) {
                    this.showQuickView(productId);
                    this.trackEvent('quick_view', { product_id: productId });
                }
            }
        });

        // Избранное
        document.addEventListener('click', (event) => {
            const wishlistBtn = event.target.closest('.wishlist-btn, .action-btn .fa-heart');
            if (wishlistBtn) {
                event.preventDefault();
                const productCard = wishlistBtn.closest('.product-card');
                const productId = productCard ? productCard.dataset.productId : null;
                if (productId) {
                    this.toggleWishlist(productId, wishlistBtn);
                }
            }
        });

        // Сравнение
        document.addEventListener('click', (event) => {
            const compareBtn = event.target.closest('.compare-btn, .action-btn .fa-exchange-alt');
            if (compareBtn) {
                event.preventDefault();
                const productCard = compareBtn.closest('.product-card');
                const productId = productCard ? productCard.dataset.productId : null;
                if (productId) {
                    this.toggleCompare(productId, compareBtn);
                }
            }
        });

        // Добавление в корзину
        document.addEventListener('click', (event) => {
            const addToCartBtn = event.target.closest('.btn-add-cart');
            if (addToCartBtn) {
                event.preventDefault();
                const productId = addToCartBtn.dataset.productId;
                if (productId) {
                    this.addToCart(productId, addToCartBtn);
                }
            }
        });

        // Мобильные фильтры
        document.addEventListener('click', (event) => {
            const mobileFiltersBtn = event.target.closest('#mobile-filters-btn');
            if (mobileFiltersBtn) {
                event.preventDefault();
                this.toggleMobileFilters();
                this.trackEvent('mobile_filters_toggle', { action: 'open' });
            }
        });

        // Закрытие модальных окон фильтров
        document.addEventListener('click', (event) => {
            const closeFiltersBtn = event.target.closest('#close-filters-btn');
            if (closeFiltersBtn) {
                this.hideMobileFilters();
                this.trackEvent('mobile_filters_toggle', { action: 'close' });
            }
            
            const applyFiltersBtn = event.target.closest('#apply-filters-btn');
            if (applyFiltersBtn) {
                this.applyFilters();
                this.hideMobileFilters();
                this.trackEvent('mobile_filters_apply');
            }
            
            const filtersModal = document.getElementById('filters-modal');
            if (filtersModal && event.target === filtersModal) {
                this.hideMobileFilters();
                this.trackEvent('mobile_filters_toggle', { action: 'close_backdrop' });
            }
        });

        // Ресайз окна
        window.addEventListener('resize', this.debounce(() => {
            this.isMobile = window.innerWidth < 768;
            this.updateResponsiveUI();
            this.trackEvent('window_resize', { width: window.innerWidth });
        }, 250));

        // Сохранение состояния перед закрытием
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });

        // Закрытие по Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const quickViewModal = document.getElementById('quick-view-modal');
                if (quickViewModal && quickViewModal.classList.contains('active')) {
                    this.hideQuickView();
                    this.trackEvent('quick_view_close', { method: 'escape' });
                }
                
                const filtersModal = document.getElementById('filters-modal');
                if (filtersModal && filtersModal.classList.contains('active')) {
                    this.hideMobileFilters();
                    this.trackEvent('mobile_filters_close', { method: 'escape' });
                }
            }
        });

        // Обработка оффлайн/онлайн состояния
        window.addEventListener('online', () => {
            this.showNotification('Соединение восстановлено', 'success');
            this.trackEvent('connection_restored');
        });

        window.addEventListener('offline', () => {
            this.showNotification('Вы находитесь в оффлайн режиме', 'warning');
            this.trackEvent('connection_lost');
        });
    }

    // Настройка Intersection Observer для ленивой загрузки
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                    }
                });
            }, {
                rootMargin: '100px 0px',
                threshold: 0.1
            });
        }
    }

    // Настройка производительности
    setupPerformanceMonitoring() {
        this.performanceMarks = new Map();
    }

    // Загрузка изображения с обработкой ошибок
    loadImage(img) {
        const src = img.dataset.src;
        if (!src || this.loadedImages.has(src)) {
            return;
        }
        
        const image = new Image();
        image.onload = () => {
            img.src = src;
            img.removeAttribute('data-src');
            this.loadedImages.add(src);
            this.imageObserver.unobserve(img);
        };
        
        image.onerror = () => {
            console.warn('Не удалось загрузить изображение:', src);
            img.src = '/static/img/placeholder.jpg';
            img.alt = 'Изображение недоступно';
            img.removeAttribute('data-src');
            this.imageObserver.unobserve(img);
        };
        
        image.src = src;
    }

    // Создание модального окна фильтров для мобильных устройств
    setupFiltersModal() {
        if (document.getElementById('filters-modal')) {
            return;
        }
        
        const modal = document.createElement('div');
        modal.id = 'filters-modal';
        modal.className = 'filters-modal';
        modal.setAttribute('aria-hidden', 'true');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'filters-modal-title');
        
        modal.innerHTML = `
            <div class="filters-modal-content">
                <div class="filters-modal-header">
                    <h3 id="filters-modal-title">Фильтры</h3>
                    <button class="filters-modal-close" id="close-filters-btn" aria-label="Закрыть фильтры">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="filters-modal-body" id="filters-modal-body">
                    <!-- Контент будет загружен динамически -->
                </div>
                <div class="filters-modal-footer">
                    <button class="btn-clear-filters" id="clear-filters-mobile" aria-label="Сбросить все фильтры">
                        <i class="fas fa-times"></i>
                        <span>Сбросить все</span>
                    </button>
                    <button class="btn-apply-filters" id="apply-filters-btn" aria-label="Применить фильтры">
                        <i class="fas fa-check"></i>
                        <span>Применить</span>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Обработчик сброса фильтров в модальном окне
        const clearBtn = document.getElementById('clear-filters-mobile');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.resetFilters();
                this.hideMobileFilters();
                this.trackEvent('filters_reset_mobile');
            });
        }
    }

    // Применение фильтров
    applyFilters() {
        const measurement = this.measurePerformance('applyFilters');
        
        // Копируем все продукты
        this.filteredProducts = [...this.products];
        
        // Фильтр по категории
        if (this.filters.category && this.filters.category !== 'all') {
            this.filteredProducts = this.filteredProducts.filter(
                product => product.category === this.filters.category
            );
        }
        
        // Фильтр по цене
        this.filteredProducts = this.filteredProducts.filter(
            product => {
                const price = parseFloat(product.price) || 0;
                return price >= this.filters.price.min && 
                       price <= this.filters.price.max;
            }
        );
        
        // Фильтр по брендам
        if (this.filters.brands.length > 0) {
            this.filteredProducts = this.filteredProducts.filter(
                product => this.filters.brands.includes(product.brand)
            );
        }
        
        // Фильтр по цветам
        if (this.filters.colors.length > 0) {
            this.filteredProducts = this.filteredProducts.filter(
                product => this.filters.colors.includes(product.color)
            );
        }
        
        // Фильтр по размерам
        if (this.filters.sizes.length > 0) {
            this.filteredProducts = this.filteredProducts.filter(
                product => this.filters.sizes.includes(product.size)
            );
        }
        
        // Фильтр по специальным признакам
        if (this.filters.specials.length > 0) {
            this.filteredProducts = this.filteredProducts.filter(product => {
                return this.filters.specials.some(special => {
                    if (special === 'new') {
                        return product.is_new;
                    }
                    if (special === 'sale') {
                        return product.discount > 0;
                    }
                    if (special === 'exclusive') {
                        return product.is_exclusive;
                    }
                    if (special === 'limited') {
                        return product.is_limited;
                    }
                    return false;
                });
            });
        }
        
        // Сортировка
        this.sortProducts();
        
        // Обновление пагинации
        this.updatePagination();
        
        // Обновление UI
        this.renderProducts();
        
        // Обновление статистики
        this.updateStats();
        
        // Сохранение фильтров
        this.saveFilters();
        
        // Обновление URL
        this.updateURL();
        
        // Префетч следующей страницы
        this.prefetchNextPage();
        
        // Трекинг
        this.trackEvent('filters_applied', {
            filters: this.filters,
            results_count: this.filteredProducts.length
        });
        
        measurement.end();
    }

    // Сортировка продуктов
    sortProducts() {
        const sortMethod = this.filters.sort || 'newest';
        
        switch (sortMethod) {
            case 'price-low':
                this.filteredProducts.sort((a, b) => {
                    const priceA = parseFloat(a.price) || 0;
                    const priceB = parseFloat(b.price) || 0;
                    const discountA = parseFloat(a.discount) || 0;
                    const discountB = parseFloat(b.discount) || 0;
                    
                    const finalPriceA = priceA * (1 - discountA / 100);
                    const finalPriceB = priceB * (1 - discountB / 100);
                    
                    return finalPriceA - finalPriceB;
                });
                break;
                
            case 'price-high':
                this.filteredProducts.sort((a, b) => {
                    const priceA = parseFloat(a.price) || 0;
                    const priceB = parseFloat(b.price) || 0;
                    const discountA = parseFloat(a.discount) || 0;
                    const discountB = parseFloat(b.discount) || 0;
                    
                    const finalPriceA = priceA * (1 - discountA / 100);
                    const finalPriceB = priceB * (1 - discountB / 100);
                    
                    return finalPriceB - finalPriceA;
                });
                break;
                
            case 'popular':
                this.filteredProducts.sort((a, b) => {
                    return (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0);
                });
                break;
                
            case 'discount':
                this.filteredProducts.sort((a, b) => {
                    return (parseFloat(b.discount) || 0) - (parseFloat(a.discount) || 0);
                });
                break;
                
            case 'rating':
                this.filteredProducts.sort((a, b) => {
                    return (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0);
                });
                break;
                
            case 'newest':
            default:
                this.filteredProducts.sort((a, b) => {
                    const dateA = new Date(a.created_at || 0);
                    const dateB = new Date(b.created_at || 0);
                    return dateB - dateA;
                });
                break;
        }
    }

    // Установка фильтра
    setFilter(filterName, value) {
        this.filters[filterName] = value;
        this.applyFilters();
    }

    // Переключение фильтра (для массивов)
    toggleFilter(filterName, value) {
        const filterArray = this.filters[filterName];
        const index = filterArray.indexOf(value);
        
        if (index === -1) {
            filterArray.push(value);
        } else {
            filterArray.splice(index, 1);
        }
        
        this.applyFilters();
    }

    // Обновление фильтра цены
    updatePriceFilter() {
        const minSlider = document.getElementById('range-min');
        const maxSlider = document.getElementById('range-max');
        const minPrice = document.getElementById('min-price');
        const maxPrice = document.getElementById('max-price');
        
        if (minSlider && maxSlider && minPrice && maxPrice) {
            this.filters.price = {
                min: parseInt(minSlider.value) || 0,
                max: parseInt(maxSlider.value) || 100000
            };
            
            minPrice.value = this.filters.price.min;
            maxPrice.value = this.filters.price.max;
            
            this.applyFilters();
        }
    }

    // Поиск продуктов
    searchProducts(query) {
        if (!query || !query.trim()) {
            this.applyFilters();
            return;
        }
        
        const searchTerms = query.toLowerCase().split(' ');
        
        this.filteredProducts = this.products.filter(product => {
            const searchText = `
                ${product.name || ''} 
                ${product.category || ''} 
                ${product.brand || ''} 
                ${product.color || ''} 
                ${product.description || ''}
            `.toLowerCase();
            
            return searchTerms.every(term => {
                return searchText.includes(term);
            });
        });
        
        this.sortProducts();
        this.updatePagination();
        this.renderProducts();
        this.updateStats();
        
        this.trackEvent('search_results', {
            query: query,
            results_count: this.filteredProducts.length
        });
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

    // Рендеринг продуктов
    renderProducts() {
        const measurement = this.measurePerformance('renderProducts');
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) {
            measurement.end();
            return;
        }
        
        productsGrid.innerHTML = '';
        
        const startIndex = (this.currentPage - 1) * this.productsPerPage;
        const endIndex = startIndex + this.productsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);
        
        if (pageProducts.length === 0) {
            this.showEmptyState();
            measurement.end();
            return;
        }
        
        const fragment = document.createDocumentFragment();
        
        pageProducts.forEach(product => {
            const productCard = this.createProductCard(product);
            fragment.appendChild(productCard);
        });
        
        productsGrid.appendChild(fragment);
        
        // Ленивая загрузка изображений
        const images = productsGrid.querySelectorAll('img[data-src]');
        images.forEach(img => {
            if (this.imageObserver) {
                this.imageObserver.observe(img);
            }
        });
        
        this.updateViewUI(this.filters.view);
        this.updateGridSize(this.filters.gridSize);
        
        measurement.end();
    }

    // Создание карточки продукта
    createProductCard(product) {
        const card = document.createElement('article');
        card.className = 'product-card';
        card.dataset.productId = product.id;
        card.setAttribute('role', 'article');
        card.setAttribute('aria-labelledby', `product-title-${product.id}`);
        
        const price = parseFloat(product.price) || 0;
        const discount = parseFloat(product.discount) || 0;
        const finalPrice = price * (1 - discount / 100);
        
        const badges = this.createProductBadges(product);
        const starRating = this.generateStarRating(product.rating || 0);
        
        let stockBadge = '';
        let stockAriaLabel = '';
        if (product.stock <= 5 && product.stock > 0) {
            stockBadge = '<div class="stock-badge">Осталось мало</div>';
            stockAriaLabel = 'Мало осталось';
        } else if (product.stock === 0) {
            stockBadge = '<div class="stock-badge out-of-stock">Нет в наличии</div>';
            stockAriaLabel = 'Нет в наличии';
        } else {
            stockAriaLabel = `В наличии, ${product.stock} штук`;
        }
        
        const description = product.description || '';
        const shortDescription = description.length > 100 ? description.substring(0, 100) + '...' : description;
        
        const formattedPrice = this.formatPrice(finalPrice);
        const formattedOriginalPrice = discount > 0 ? this.formatPrice(price) : '';
        
        card.innerHTML = `
            ${badges}
            <div class="product-image">
                <img data-src="${product.image_url || '/static/img/placeholder.jpg'}" 
                     src="/static/img/placeholder.jpg" 
                     alt="${product.name || 'Товар'}"
                     loading="lazy"
                     class="product-main-image"
                     aria-label="Изображение товара ${product.name}">
                <div class="product-actions" role="toolbar" aria-label="Действия с товаром">
                    <button class="action-btn wishlist-btn" 
                            title="В избранное"
                            aria-label="Добавить ${product.name} в избранное">
                        <i class="far fa-heart"></i>
                    </button>
                    <button class="action-btn quick-view-btn" 
                            title="Быстрый просмотр"
                            aria-label="Быстрый просмотр ${product.name}">
                        <i class="far fa-eye"></i>
                    </button>
                    <button class="action-btn compare-btn" 
                            title="Сравнить"
                            aria-label="Добавить ${product.name} к сравнению">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                </div>
                ${stockBadge}
                <div class="sr-only" aria-live="polite">${stockAriaLabel}</div>
            </div>
            <div class="product-info">
                <div class="product-category" aria-label="Категория: ${product.category || ''}">
                    ${product.category || ''}
                </div>
                <h3 class="product-title" id="product-title-${product.id}">
                    <a href="/product/${product.id}" aria-label="Подробнее о ${product.name}">
                        ${product.name || 'Товар'}
                    </a>
                </h3>
                <p class="product-description">${shortDescription}</p>
                
                <div class="product-meta">
                    <div class="product-price" aria-label="Цена: ${formattedPrice}${discount > 0 ? ', скидка ' + discount + ' процентов' : ''}">
                        ${discount > 0 ? `
                            <span class="current-price">${formattedPrice}</span>
                            <span class="original-price">${formattedOriginalPrice}</span>
                            <span class="discount">-${discount}%</span>
                            <div class="sr-only">Старая цена ${formattedOriginalPrice}, новая цена ${formattedPrice}, скидка ${discount}%</div>
                        ` : `
                            <span class="current-price">${formattedPrice}</span>
                        `}
                    </div>
                    
                    <div class="product-rating" aria-label="Рейтинг: ${product.rating ? product.rating.toFixed(1) : '0'} из 5 звёзд">
                        <div class="stars">
                            ${starRating}
                        </div>
                        <span class="sr-only">${product.rating ? product.rating.toFixed(1) : '0'} из 5 звёзд</span>
                    </div>
                </div>
                
                <div class="product-footer">
                    <button class="btn-add-cart" 
                            data-product-id="${product.id}"
                            aria-label="Добавить ${product.name} в корзину">
                        <i class="fas fa-shopping-bag"></i>
                        <span>В корзину</span>
                    </button>
                    <a href="/product/${product.id}" 
                       class="btn-view" 
                       title="Подробнее"
                       aria-label="Подробная информация о ${product.name}">
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        `;
        
        // Добавляем обработчик ошибок для изображения
        const img = card.querySelector('img');
        if (img) {
            img.onerror = () => {
                img.src = '/static/img/placeholder.jpg';
                img.alt = 'Изображение недоступно';
                img.removeAttribute('data-src');
            };
        }
        
        return card;
    }

    // Форматирование цены
    formatPrice(price) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(price);
    }

    // Создание бейджей продукта
    createProductBadges(product) {
        let badges = '';
        let badgesAriaLabel = '';
        const badgeLabels = [];
        
        if (product.is_new) {
            badges += '<span class="product-badge badge-new">Новинка</span>';
            badgeLabels.push('Новинка');
        }
        if (product.is_exclusive) {
            badges += '<span class="product-badge badge-exclusive">Эксклюзив</span>';
            badgeLabels.push('Эксклюзивный товар');
        }
        if (product.is_limited) {
            badges += '<span class="product-badge badge-limited">Лимитированная</span>';
            badgeLabels.push('Лимитированная серия');
        }
        if (product.discount > 0) {
            badges += `<span class="product-badge badge-sale">-${product.discount}%</span>`;
            badgeLabels.push(`Скидка ${product.discount}%`);
        }
        
        badgesAriaLabel = badgeLabels.join(', ');
        
        if (badges) {
            return `
                <div class="product-badges" aria-label="${badgesAriaLabel}">
                    ${badges}
                    <span class="sr-only">${badgesAriaLabel}</span>
                </div>
            `;
        }
        
        return '';
    }

    // Генерация рейтинга звездами
    generateStarRating(rating) {
        let stars = '';
        const numericRating = parseFloat(rating) || 0;
        const fullStars = Math.floor(numericRating);
        const hasHalfStar = (numericRating % 1) >= 0.5;
        
        for (let i = 1; i <= 5; i++) {
            if (i <= fullStars) {
                stars += '<i class="fas fa-star"></i>';
            } else if (i === fullStars + 1 && hasHalfStar) {
                stars += '<i class="fas fa-star-half-alt"></i>';
            } else {
                stars += '<i class="far fa-star"></i>';
            }
        }
        
        return stars;
    }

    // Обновление статистики
    updateStats() {
        const totalElement = document.querySelector('.catalog-stats strong');
        if (totalElement) {
            totalElement.textContent = this.filteredProducts.length.toString();
            totalElement.setAttribute('aria-live', 'polite');
        }
        
        // Обновляем описание для скринридеров
        const statsText = document.querySelector('.catalog-stats');
        if (statsText) {
            statsText.setAttribute('aria-label', `Найдено товаров: ${this.filteredProducts.length}`);
        }
    }

    // Обновление пагинации
    updatePagination() {
        this.totalPages = Math.ceil(this.filteredProducts.length / this.productsPerPage);
        if (this.totalPages === 0) {
            this.totalPages = 1;
        }
        this.currentPage = Math.min(this.currentPage, this.totalPages);
        
        const paginationContainer = document.querySelector('.catalog-pagination');
        if (!paginationContainer) {
            return;
        }
        
        paginationContainer.innerHTML = this.createPaginationHTML();
        paginationContainer.setAttribute('aria-label', 'Навигация по страницам');
    }

    // Создание HTML пагинации
    createPaginationHTML() {
        if (this.totalPages <= 1) {
            return '<span class="sr-only">Только одна страница</span>';
        }
        
        let html = '';
        const currentPageLabel = `Страница ${this.currentPage} из ${this.totalPages}`;
        
        // Кнопка "предыдущая"
        html += `
            <a href="#" 
               class="page-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
               id="prev-page"
               aria-label="Предыдущая страница"
               ${this.currentPage === 1 ? 'aria-disabled="true"' : ''}>
                <i class="fas fa-chevron-left"></i>
                <span class="sr-only">Предыдущая</span>
            </a>
        `;
        
        const maxVisible = this.isMobile ? 3 : 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        // Первая страница и многоточие
        if (startPage > 1) {
            html += `<a href="#" class="page-btn" data-page="1" aria-label="Страница 1">1</a>`;
            if (startPage > 2) {
                html += `<span class="page-btn disabled" aria-hidden="true">...</span>`;
            }
        }
        
        // Основные страницы
        for (let i = startPage; i <= endPage; i++) {
            const isCurrent = i === this.currentPage;
            html += `
                <a href="#" 
                   class="page-btn ${isCurrent ? 'active' : ''}" 
                   data-page="${i}"
                   aria-label="${isCurrent ? 'Текущая страница, ' : ''}Страница ${i}"
                   ${isCurrent ? 'aria-current="page"' : ''}>
                    ${i}
                </a>
            `;
        }
        
        // Последняя страница и многоточие
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += `<span class="page-btn disabled" aria-hidden="true">...</span>`;
            }
            html += `<a href="#" class="page-btn" data-page="${this.totalPages}" aria-label="Страница ${this.totalPages}">${this.totalPages}</a>`;
        }
        
        // Кнопка "следующая"
        html += `
            <a href="#" 
               class="page-btn ${this.currentPage === this.totalPages ? 'disabled' : ''}" 
               id="next-page"
               aria-label="Следующая страница"
               ${this.currentPage === this.totalPages ? 'aria-disabled="true"' : ''}>
                <i class="fas fa-chevron-right"></i>
                <span class="sr-only">Следующая</span>
            </a>
        `;
        
        return `<nav role="navigation" aria-label="${currentPageLabel}">${html}</nav>`;
    }

    // Переход на страницу
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        this.renderProducts();
        this.updatePagination();
        
        // Плавная прокрутка
        const catalogHeader = document.querySelector('.catalog-header');
        if (catalogHeader) {
            catalogHeader.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
        
        this.updateURL();
        
        // Фокус на пагинации для скринридеров
        setTimeout(() => {
            const activePage = document.querySelector('.page-btn.active');
            if (activePage) {
                activePage.focus();
            }
        }, 100);
    }

    // Обновление URL с параметрами
    updateURL() {
        const params = new URLSearchParams();
        
        if (this.filters.category !== 'all') {
            params.set('category', this.filters.category);
        }
        
        if (this.filters.price.min > 0 || this.filters.price.max < 100000) {
            params.set('price', `${this.filters.price.min}-${this.filters.price.max}`);
        }
        
        if (this.filters.brands.length > 0) {
            params.set('brands', this.filters.brands.join(','));
        }
        
        if (this.filters.sort !== 'newest') {
            params.set('sort', this.filters.sort);
        }
        
        if (this.currentPage > 1) {
            params.set('page', this.currentPage);
        }
        
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.replaceState({}, '', newUrl);
        
        this.trackEvent('url_updated', { url: newUrl });
    }

    // Префетч следующей страницы
    prefetchNextPage() {
        if (this.currentPage >= this.totalPages) return;
        
        const nextPageProducts = this.filteredProducts.slice(
            this.currentPage * this.productsPerPage,
            (this.currentPage + 1) * this.productsPerPage
        );
        
        nextPageProducts.forEach(product => {
            if (product.image_url && !this.loadedImages.has(product.image_url)) {
                const link = document.createElement('link');
                link.rel = 'prefetch';
                link.href = product.image_url;
                link.as = 'image';
                document.head.appendChild(link);
                
                // Удаляем через 30 секунд
                setTimeout(() => {
                    if (link.parentNode) {
                        link.remove();
                    }
                }, 30000);
            }
        });
    }

    // Показ пустого состояния
    showEmptyState() {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) {
            return;
        }
        
        productsGrid.innerHTML = `
            <div class="catalog-empty" role="alert" aria-live="assertive">
                <div class="catalog-empty-icon" aria-hidden="true">
                    <i class="fas fa-search"></i>
                </div>
                <h2>Товары не найдены</h2>
                <p>Попробуйте изменить параметры фильтрации или выбрать другую категорию</p>
                <button class="clear-filters" id="clear-filters-empty" aria-label="Сбросить все фильтры">
                    <i class="fas fa-times"></i>
                    <span>Сбросить все фильтры</span>
                </button>
            </div>
        `;
        
        const clearButton = document.getElementById('clear-filters-empty');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.resetFilters();
                this.trackEvent('filters_reset_empty');
            });
        }
        
        this.trackEvent('empty_state_shown');
    }

    // Показать загрузку
    showLoading() {
        this.isLoading = true;
        const productsGrid = document.getElementById('products-grid');
        if (productsGrid) {
            productsGrid.innerHTML = `
                <div class="catalog-loading" role="alert" aria-live="assertive" aria-busy="true">
                    <div class="loading-spinner" aria-hidden="true">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <p>Загрузка товаров...</p>
                    <span class="sr-only">Загрузка, пожалуйста подождите</span>
                </div>
            `;
        }
    }

    // Скрыть загрузку
    hideLoading() {
        this.isLoading = false;
        const loadingElement = document.querySelector('.catalog-loading');
        if (loadingElement) {
            loadingElement.setAttribute('aria-busy', 'false');
        }
    }

    // Создание модального окна быстрого просмотра
    createQuickViewModal() {
        if (document.getElementById('quick-view-modal')) {
            return;
        }
        
        const modal = document.createElement('div');
        modal.id = 'quick-view-modal';
        modal.className = 'quick-view-modal';
        modal.setAttribute('aria-hidden', 'true');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        modal.innerHTML = `
            <div class="quick-view-content">
                <button class="quick-view-close" aria-label="Закрыть быстрый просмотр">
                    <i class="fas fa-times"></i>
                </button>
                <div class="quick-view-body" id="quick-view-body">
                    <!-- Контент будет загружен динамически -->
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    // Показать быстрый просмотр
    async showQuickView(productId) {
        const product = this.products.find(p => p.id == productId);
        if (!product) {
            return;
        }
        
        const modal = document.getElementById('quick-view-modal');
        const body = document.getElementById('quick-view-body');
        
        if (!modal || !body) {
            return;
        }
        
        body.innerHTML = `
            <div class="quick-view-loading" aria-live="polite" aria-busy="true">
                <div class="loading-spinner" aria-hidden="true">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <span class="sr-only">Загрузка быстрого просмотра</span>
            </div>
        `;
        
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        // Фокус на модальном окне
        setTimeout(() => {
            modal.focus();
        }, 100);
        
        try {
            const response = await fetch('/api/products/' + productId);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.product) {
                    body.innerHTML = this.createQuickViewContent(data.product);
                } else {
                    body.innerHTML = this.createQuickViewContent(product);
                }
            } else {
                body.innerHTML = this.createQuickViewContent(product);
            }
            
            this.initQuickViewGallery();
            this.initQuickViewVariants();
            this.initQuickViewEvents();
        } catch (error) {
            console.error('Ошибка загрузки быстрого просмотра:', error);
            body.innerHTML = this.createQuickViewContent(product);
            this.trackEvent('quick_view_error', { error: error.message });
        }
    }

    // Создание контента для быстрого просмотра
    createQuickViewContent(product) {
        const price = parseFloat(product.price) || 0;
        const discount = parseFloat(product.discount) || 0;
        const finalPrice = price * (1 - discount / 100);
        const rating = parseFloat(product.rating) || 0;
        const stock = parseInt(product.stock) || 0;
        
        const formattedPrice = this.formatPrice(finalPrice);
        const formattedOriginalPrice = discount > 0 ? this.formatPrice(price) : '';
        
        let stockHtml = '';
        let stockAriaLabel = '';
        if (stock > 10) {
            stockHtml = `<span class="in-stock"><i class="fas fa-check-circle"></i> В наличии (${stock} шт.)</span>`;
            stockAriaLabel = `В наличии, ${stock} штук`;
        } else if (stock > 0) {
            stockHtml = `<span class="low-stock"><i class="fas fa-exclamation-circle"></i> Мало осталось (${stock} шт.)</span>`;
            stockAriaLabel = `Мало осталось, ${stock} штук`;
        } else {
            stockHtml = `<span class="out-of-stock"><i class="fas fa-times-circle"></i> Нет в наличии</span>`;
            stockAriaLabel = 'Нет в наличии';
        }
        
        return `
            <div class="quick-view-product">
                <div class="quick-view-gallery" aria-label="Галерея изображений товара">
                    <div class="quick-view-main-image">
                        <img src="${product.image_url || '/static/img/placeholder.jpg'}" 
                             alt="${product.name || 'Товар'}"
                             aria-label="Основное изображение товара ${product.name}">
                    </div>
                </div>
                
                <div class="quick-view-info">
                    <div class="quick-view-header">
                        <div class="quick-view-category" aria-label="Категория: ${product.category || ''}">
                            ${product.category || ''}
                        </div>
                        <h2 class="quick-view-title" id="quick-view-title">
                            ${product.name || 'Товар'}
                        </h2>
                        <div class="quick-view-rating" aria-label="Рейтинг: ${rating.toFixed(1)} из 5 звёзд">
                            ${this.generateStarRating(rating)}
                            <span class="rating-value">(${rating.toFixed(1)})</span>
                            <span class="sr-only">${rating.toFixed(1)} из 5 звёзд</span>
                        </div>
                    </div>
                    
                    <div class="quick-view-price" aria-label="Цена: ${formattedPrice}${discount > 0 ? ', скидка ' + discount + ' процентов' : ''}">
                        ${discount > 0 ? `
                            <div class="current-price">${formattedPrice}</div>
                            <div class="original-price">${formattedOriginalPrice}</div>
                            <div class="discount-badge">-${discount}%</div>
                            <div class="sr-only">Старая цена ${formattedOriginalPrice}, новая цена ${formattedPrice}, скидка ${discount}%</div>
                        ` : `
                            <div class="current-price">${formattedPrice}</div>
                        `}
                    </div>
                    
                    <div class="quick-view-description">
                        <p>${product.description || 'Описание товара отсутствует'}</p>
                    </div>
                    
                    <div class="quick-view-details" role="list" aria-label="Характеристики товара">
                        ${product.brand ? `<div role="listitem"><strong>Бренд:</strong> ${product.brand}</div>` : ''}
                        ${product.color ? `<div role="listitem"><strong>Цвет:</strong> ${product.color}</div>` : ''}
                        ${product.size ? `<div role="listitem"><strong>Размер:</strong> ${product.size}</div>` : ''}
                        ${product.material ? `<div role="listitem"><strong>Материал:</strong> ${product.material}</div>` : ''}
                    </div>
                    
                    <div class="quick-view-stock" aria-live="polite" aria-label="${stockAriaLabel}">
                        ${stockHtml}
                        <span class="sr-only">${stockAriaLabel}</span>
                    </div>
                    
                    <div class="quick-view-actions">
                        <div class="quantity-selector" aria-label="Количество">
                            <button class="quantity-btn decrease" aria-label="Уменьшить количество">
                                <i class="fas fa-minus"></i>
                            </button>
                            <input type="number" 
                                   class="quantity-input" 
                                   value="1" 
                                   min="1" 
                                   max="${stock}"
                                   aria-label="Количество товара">
                            <button class="quantity-btn increase" aria-label="Увеличить количество">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                        <button class="btn-add-to-cart" 
                                data-product-id="${product.id}"
                                ${stock <= 0 ? 'disabled aria-disabled="true"' : ''}
                                aria-label="Добавить ${product.name} в корзину">
                            <i class="fas fa-shopping-bag"></i>
                            <span>${stock > 0 ? 'Добавить в корзину' : 'Нет в наличии'}</span>
                        </button>
                        <button class="btn-wishlist" 
                                data-product-id="${product.id}"
                                aria-label="Добавить ${product.name} в избранное">
                            <i class="far fa-heart"></i>
                        </button>
                    </div>
                    
                    <div class="quick-view-footer">
                        <a href="/product/${product.id}" 
                           class="btn-view-details"
                           aria-label="Перейти к подробной информации о ${product.name}">
                            <i class="fas fa-external-link-alt"></i>
                            <span>Подробнее о товаре</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    // Инициализация галереи быстрого просмотра
    initQuickViewGallery() {
        const mainImage = document.querySelector('.quick-view-main-image img');
        if (mainImage) {
            mainImage.addEventListener('click', () => {
                this.openFullScreenImage(mainImage.src);
                this.trackEvent('image_fullscreen', { source: 'quick_view' });
            });
            
            // Добавляем обработчик ошибок
            mainImage.onerror = () => {
                mainImage.src = '/static/img/placeholder.jpg';
                mainImage.alt = 'Изображение недоступно';
            };
        }
    }

    // Инициализация вариантов в быстром просмотре
    initQuickViewVariants() {
        // Можно добавить логику для вариантов товара
    }

    // Инициализация событий быстрого просмотра
    initQuickViewEvents() {
        // Кнопка закрытия
        const closeBtn = document.querySelector('.quick-view-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideQuickView();
            });
            
            // Обработка нажатия Escape уже есть в общих обработчиках
        }
        
        // Добавление в корзину
        const addToCartBtn = document.querySelector('.btn-add-to-cart');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => {
                const productId = addToCartBtn.dataset.productId;
                if (productId) {
                    this.addToCart(productId, addToCartBtn);
                    this.trackEvent('add_to_cart_quick_view', { product_id: productId });
                }
            });
        }
        
        // Избранное
        const wishlistBtn = document.querySelector('.btn-wishlist');
        if (wishlistBtn) {
            wishlistBtn.addEventListener('click', () => {
                const productId = wishlistBtn.dataset.productId;
                if (productId) {
                    this.toggleWishlist(productId, wishlistBtn);
                    this.trackEvent('wishlist_quick_view', { product_id: productId });
                }
            });
        }
        
        // Управление количеством
        const decreaseBtn = document.querySelector('.quantity-btn.decrease');
        const increaseBtn = document.querySelector('.quantity-btn.increase');
        const quantityInput = document.querySelector('.quantity-input');
        
        if (decreaseBtn && quantityInput) {
            decreaseBtn.addEventListener('click', () => {
                let value = parseInt(quantityInput.value) || 1;
                if (value > 1) {
                    value--;
                    quantityInput.value = value;
                    this.trackEvent('quantity_decrease', { value });
                }
            });
        }
        
        if (increaseBtn && quantityInput) {
            increaseBtn.addEventListener('click', () => {
                const max = parseInt(quantityInput.max) || 99;
                let value = parseInt(quantityInput.value) || 1;
                if (value < max) {
                    value++;
                    quantityInput.value = value;
                    this.trackEvent('quantity_increase', { value });
                }
            });
        }
        
        if (quantityInput) {
            quantityInput.addEventListener('change', () => {
                let value = parseInt(quantityInput.value) || 1;
                const max = parseInt(quantityInput.max) || 99;
                const min = parseInt(quantityInput.min) || 1;
                
                if (value < min) value = min;
                if (value > max) value = max;
                
                quantityInput.value = value;
                this.trackEvent('quantity_change', { value });
            });
        }
        
        // Ловушка фокуса внутри модального окна
        const modal = document.getElementById('quick-view-modal');
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        if (firstFocusable) {
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstFocusable) {
                            e.preventDefault();
                            lastFocusable.focus();
                        }
                    } else {
                        if (document.activeElement === lastFocusable) {
                            e.preventDefault();
                            firstFocusable.focus();
                        }
                    }
                }
            });
        }
    }

    // Открытие полноэкранного изображения
    openFullScreenImage(src) {
        const fullscreen = document.createElement('div');
        fullscreen.className = 'fullscreen-image';
        fullscreen.setAttribute('role', 'dialog');
        fullscreen.setAttribute('aria-modal', 'true');
        fullscreen.setAttribute('aria-label', 'Полноэкранное изображение');
        
        fullscreen.innerHTML = `
            <div class="fullscreen-content">
                <button class="fullscreen-close" aria-label="Закрыть полноэкранный просмотр">
                    <i class="fas fa-times"></i>
                </button>
                <img src="${src}" alt="Полноэкранное изображение товара" loading="eager">
            </div>
        `;
        
        document.body.appendChild(fullscreen);
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            fullscreen.classList.add('active');
            fullscreen.focus();
        }, 10);
        
        const closeBtn = fullscreen.querySelector('.fullscreen-close');
        closeBtn.addEventListener('click', () => {
            this.closeFullScreenImage(fullscreen);
            this.trackEvent('fullscreen_close');
        });
        
        fullscreen.addEventListener('click', (event) => {
            if (event.target === fullscreen) {
                this.closeFullScreenImage(fullscreen);
                this.trackEvent('fullscreen_close_backdrop');
            }
        });
        
        // Закрытие по Escape
        fullscreen.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeFullScreenImage(fullscreen);
                this.trackEvent('fullscreen_close_escape');
            }
        });
        
        this.trackEvent('fullscreen_open');
    }

    // Закрытие полноэкранного изображения
    closeFullScreenImage(fullscreen) {
        fullscreen.classList.remove('active');
        setTimeout(() => {
            if (fullscreen.parentNode) {
                fullscreen.remove();
            }
            document.body.style.overflow = '';
        }, 300);
    }

    // Скрыть быстрый просмотр
    hideQuickView() {
        const modal = document.getElementById('quick-view-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
    }

    // Переключение мобильных фильтров
    toggleMobileFilters() {
        const modal = document.getElementById('filters-modal');
        if (!modal) {
            return;
        }
        
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        // Копируем содержимое фильтров
        const sidebar = document.querySelector('.catalog-sidebar');
        const filtersBody = document.getElementById('filters-modal-body');
        
        if (sidebar && filtersBody) {
            filtersBody.innerHTML = sidebar.innerHTML;
            
            // Переносим стили и скрипты
            filtersBody.querySelectorAll('.filter-group').forEach(group => {
                group.style.marginBottom = '20px';
            });
            
            // Добавляем доступность
            filtersBody.setAttribute('role', 'form');
            filtersBody.setAttribute('aria-label', 'Фильтры товаров');
            
            // Фокус на первом элементе
            setTimeout(() => {
                const firstFocusable = filtersBody.querySelector('button, input, select');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }, 100);
        }
    }

    // Скрыть мобильные фильтры
    hideMobileFilters() {
        const modal = document.getElementById('filters-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
    }

    // Настройка тултипов
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (event) => {
                const title = element.getAttribute('title');
                if (!title) {
                    return;
                }
                
                const tooltip = document.createElement('div');
                tooltip.className = 'custom-tooltip';
                tooltip.textContent = title;
                tooltip.setAttribute('role', 'tooltip');
                tooltip.setAttribute('aria-hidden', 'true');
                document.body.appendChild(tooltip);
                
                const rect = element.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();
                
                let left = rect.left + rect.width / 2;
                let top = rect.top - tooltipRect.height - 10;
                
                // Проверка на выход за границы экрана
                if (left < 10) left = 10;
                if (left + tooltipRect.width > window.innerWidth - 10) {
                    left = window.innerWidth - tooltipRect.width - 10;
                }
                if (top < 10) top = rect.bottom + 10;
                
                tooltip.style.left = `${left}px`;
                tooltip.style.top = `${top}px`;
                
                element.setAttribute('title', '');
                element.dataset.originalTitle = title;
                
                element.tooltip = tooltip;
            });
            
            element.addEventListener('mouseleave', () => {
                if (element.tooltip) {
                    element.tooltip.remove();
                    delete element.tooltip;
                }
                if (element.dataset.originalTitle) {
                    element.setAttribute('title', element.dataset.originalTitle);
                }
            });
            
            element.addEventListener('focus', () => {
                const title = element.getAttribute('title');
                if (title && !element.tooltip) {
                    // Создаем тултип для фокуса
                    const tooltip = document.createElement('div');
                    tooltip.className = 'custom-tooltip';
                    tooltip.textContent = title;
                    tooltip.setAttribute('role', 'tooltip');
                    tooltip.setAttribute('aria-live', 'polite');
                    document.body.appendChild(tooltip);
                    
                    const rect = element.getBoundingClientRect();
                    tooltip.style.left = `${rect.left + rect.width / 2}px`;
                    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
                    tooltip.style.transform = 'translateX(-50%)';
                    
                    element.tooltip = tooltip;
                }
            });
            
            element.addEventListener('blur', () => {
                if (element.tooltip) {
                    element.tooltip.remove();
                    delete element.tooltip;
                }
            });
        });
    }

    // Настройка карточек продуктов
    setupProductCards() {
        document.addEventListener('mouseover', (event) => {
            const productCard = event.target.closest('.product-card');
            if (productCard) {
                productCard.classList.add('hover');
            }
        });
        
        document.addEventListener('mouseout', (event) => {
            const productCard = event.target.closest('.product-card');
            if (productCard) {
                productCard.classList.remove('hover');
            }
        });
        
        // Keyboard navigation для карточек
        document.addEventListener('keydown', (event) => {
            const productCard = event.target.closest('.product-card');
            if (productCard && event.key === 'Enter' && !event.target.matches('button, a')) {
                event.preventDefault();
                const link = productCard.querySelector('.product-title a');
                if (link) {
                    link.click();
                }
            }
        });
    }

    // Обновление вида отображения
    updateViewUI(selectedView) {
        document.querySelectorAll('.view-btn').forEach(btn => {
            if (btn.dataset.view === selectedView) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');
            }
        });
        
        const productsGrid = document.getElementById('products-grid');
        if (productsGrid) {
            productsGrid.className = 'catalog-products-grid';
            productsGrid.classList.add(`${selectedView}-view`);
            productsGrid.setAttribute('aria-label', `Сетка товаров в виде ${selectedView === 'grid' ? 'сетки' : 'списка'}`);
        }
    }

    // Обновление размера сетки
    updateGridSize(size) {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) {
            return;
        }
        
        let minWidth;
        switch(size) {
            case 1:
                minWidth = 350;
                break;
            case 2:
                minWidth = 280;
                break;
            case 3:
                minWidth = 240;
                break;
            default:
                minWidth = 280;
        }
        
        productsGrid.style.gridTemplateColumns = `repeat(auto-fill, minmax(${minWidth}px, 1fr))`;
    }

    // Обновление адаптивного UI
    updateResponsiveUI() {
        if (this.isMobile) {
            this.updateGridSize(1);
        } else {
            this.updateGridSize(this.filters.gridSize);
        }
        
        // Обновляем виртуальный скроллинг
        if (this.virtualScrollEnabled) {
            this.updateVirtualScroll();
        }
    }

    // Настройка виртуального скроллинга
    setupVirtualScroll() {
        if (this.filteredProducts.length > 50) {
            this.virtualScrollEnabled = true;
            this.productsPerPage = 24; // Увеличиваем для виртуального скроллинга
            
            this.scrollObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && 
                        this.currentPage < this.totalPages && 
                        !this.isLoading) {
                        this.loadMoreProducts();
                    }
                });
            }, {
                root: null,
                rootMargin: '100px 0px',
                threshold: 0.1
            });
            
            const sentinel = document.createElement('div');
            sentinel.id = 'scroll-sentinel';
            sentinel.style.height = '1px';
            sentinel.style.width = '1px';
            document.body.appendChild(sentinel);
            this.scrollObserver.observe(sentinel);
        }
    }

    // Загрузка дополнительных продуктов
    async loadMoreProducts() {
        if (this.isLoading || this.currentPage >= this.totalPages) {
            return;
        }
        
        this.isLoading = true;
        this.currentPage++;
        
        const startIndex = (this.currentPage - 1) * this.productsPerPage;
        const endIndex = startIndex + this.productsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);
        
        const fragment = document.createDocumentFragment();
        pageProducts.forEach(product => {
            const productCard = this.createProductCard(product);
            fragment.appendChild(productCard);
        });
        
        const productsGrid = document.getElementById('products-grid');
        if (productsGrid) {
            productsGrid.appendChild(fragment);
            
            // Ленивая загрузка новых изображений
            const newImages = productsGrid.querySelectorAll('img[data-src]:not([src])');
            newImages.forEach(img => {
                if (this.imageObserver) {
                    this.imageObserver.observe(img);
                }
            });
        }
        
        this.isLoading = false;
        this.trackEvent('virtual_scroll_load', { page: this.currentPage });
    }

    // Обновление виртуального скроллинга
    updateVirtualScroll() {
        if (this.scrollObserver) {
            this.scrollObserver.disconnect();
        }
        this.setupVirtualScroll();
    }

    // Сброс всех фильтров
    resetFilters() {
        this.filters = {
            category: 'all',
            price: { min: 0, max: 100000 },
            brands: [],
            colors: [],
            sizes: [],
            specials: [],
            sort: 'newest',
            view: 'grid',
            gridSize: 2
        };
        
        // Сброс UI элементов
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.value = 'newest';
        }
        
        const gridSlider = document.getElementById('grid-size');
        if (gridSlider) {
            gridSlider.value = 2;
        }
        
        const minPrice = document.getElementById('min-price');
        const maxPrice = document.getElementById('max-price');
        if (minPrice && maxPrice) {
            minPrice.value = 0;
            maxPrice.value = 100000;
        }
        
        const minSlider = document.getElementById('range-min');
        const maxSlider = document.getElementById('range-max');
        if (minSlider && maxSlider) {
            minSlider.value = 0;
            maxSlider.value = 100000;
        }
        
        // Сброс чекбоксов
        document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.applyFilters();
        this.showNotification('Фильтры сброшены', 'info');
    }

    // Переключение избранного
    toggleWishlist(productId, button) {
        if (!button) return;
        
        const isActive = button.classList.contains('active');
        const icon = button.querySelector('i');
        
        if (!icon) {
            return;
        }
        
        if (isActive) {
            button.classList.remove('active');
            button.setAttribute('aria-pressed', 'false');
            icon.className = 'far fa-heart';
            this.showNotification('Удалено из избранного', 'info');
            this.trackEvent('wishlist_remove', { product_id: productId });
        } else {
            button.classList.add('active');
            button.setAttribute('aria-pressed', 'true');
            icon.className = 'fas fa-heart';
            this.showNotification('Добавлено в избранное', 'success');
            this.animateHeart(button);
            this.trackEvent('wishlist_add', { product_id: productId });
        }
        
        this.saveWishlistState(productId, !isActive);
    }

    // Переключение сравнения
    toggleCompare(productId, button) {
        if (!button) return;
        
        const isActive = button.classList.contains('active');
        const icon = button.querySelector('i');
        
        if (!icon) {
            return;
        }
        
        if (isActive) {
            button.classList.remove('active');
            button.setAttribute('aria-pressed', 'false');
            icon.style.color = '';
            this.showNotification('Удалено из сравнения', 'info');
            this.trackEvent('compare_remove', { product_id: productId });
        } else {
            button.classList.add('active');
            button.setAttribute('aria-pressed', 'true');
            icon.style.color = '#d4af37';
            this.showNotification('Добавлено к сравнению', 'success');
            this.trackEvent('compare_add', { product_id: productId });
        }
        
        this.saveCompareState(productId, !isActive);
    }

    // Добавление в корзину
    addToCart(productId, button) {
        const product = this.products.find(p => p.id == productId);
        if (!product) {
            return;
        }
        
        const originalHTML = button.innerHTML;
        const originalBackground = button.style.background;
        const originalDisabled = button.disabled;
        const originalAriaLabel = button.getAttribute('aria-label');
        
        button.innerHTML = `
            <i class="fas fa-check"></i>
            <span>Добавлено!</span>
        `;
        button.style.background = '#10b981';
        button.disabled = true;
        button.setAttribute('aria-label', 'Товар добавлен в корзину');
        
        this.showNotification(`${product.name} добавлен в корзину`, 'success');
        
        // Восстанавливаем состояние через 2 секунды
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = originalBackground;
            button.disabled = originalDisabled;
            if (originalAriaLabel) {
                button.setAttribute('aria-label', originalAriaLabel);
            }
        }, 2000);
        
        // Добавляем в корзину через глобальный объект, если он есть
        if (window.cart && typeof window.cart.addItem === 'function') {
            window.cart.addItem(productId, 1);
        }
        
        this.trackEvent('add_to_cart', {
            product_id: productId,
            product_name: product.name,
            product_price: product.price
        });
    }

    // Анимация сердца для избранного
    animateHeart(button) {
        const heart = button.querySelector('i');
        if (!heart) {
            return;
        }
        
        heart.style.transform = 'scale(1.5)';
        heart.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            heart.style.transform = 'scale(1)';
        }, 300);
    }

    // Сохранение состояния избранного
    saveWishlistState(productId, isInWishlist) {
        try {
            const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
            const index = wishlist.indexOf(productId);
            
            if (isInWishlist && index === -1) {
                wishlist.push(productId);
            } else if (!isInWishlist && index !== -1) {
                wishlist.splice(index, 1);
            }
            
            localStorage.setItem('wishlist', JSON.stringify(wishlist));
        } catch (error) {
            console.error('Ошибка сохранения избранного:', error);
        }
    }

    // Сохранение состояния сравнения
    saveCompareState(productId, isInCompare) {
        try {
            const compare = JSON.parse(localStorage.getItem('compare') || '[]');
            const index = compare.indexOf(productId);
            
            if (isInCompare && index === -1) {
                compare.push(productId);
            } else if (!isInCompare && index !== -1) {
                compare.splice(index, 1);
            }
            
            localStorage.setItem('compare', JSON.stringify(compare));
        } catch (error) {
            console.error('Ошибка сохранения сравнения:', error);
        }
    }

    // Сохранение фильтров
    saveFilters() {
        try {
            localStorage.setItem('catalog_filters', JSON.stringify(this.filters));
        } catch (error) {
            console.error('Ошибка сохранения фильтров:', error);
        }
    }

    // Сохранение состояния
    saveState() {
        this.saveFilters();
        
        // Сохраняем текущую страницу
        try {
            localStorage.setItem('catalog_current_page', this.currentPage.toString());
        } catch (error) {
            console.error('Ошибка сохранения текущей страницы:', error);
        }
    }

    // Восстановление состояния
    restoreState() {
        try {
            // Восстанавливаем фильтры
            const savedFilters = localStorage.getItem('catalog_filters');
            if (savedFilters) {
                this.filters = JSON.parse(savedFilters);
            }
            
            // Восстанавливаем текущую страницу
            const savedPage = localStorage.getItem('catalog_current_page');
            if (savedPage) {
                this.currentPage = parseInt(savedPage) || 1;
            }
            
            // Восстанавливаем избранное и сравнение
            this.restoreWishlistState();
            this.restoreCompareState();
            
            this.restoreUIState();
        } catch (error) {
            console.error('Ошибка восстановления состояния:', error);
        }
    }

    // Восстановление состояния избранного
    restoreWishlistState() {
        try {
            const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
            wishlist.forEach(productId => {
                const button = document.querySelector(`[data-product-id="${productId}"] .wishlist-btn`);
                if (button) {
                    button.classList.add('active');
                    const icon = button.querySelector('i');
                    if (icon) {
                        icon.className = 'fas fa-heart';
                    }
                }
            });
        } catch (error) {
            console.error('Ошибка восстановления избранного:', error);
        }
    }

    // Восстановление состояния сравнения
    restoreCompareState() {
        try {
            const compare = JSON.parse(localStorage.getItem('compare') || '[]');
            compare.forEach(productId => {
                const button = document.querySelector(`[data-product-id="${productId}"] .compare-btn`);
                if (button) {
                    button.classList.add('active');
                    const icon = button.querySelector('i');
                    if (icon) {
                        icon.style.color = '#d4af37';
                    }
                }
            });
        } catch (error) {
            console.error('Ошибка восстановления сравнения:', error);
        }
    }

    // Восстановление UI состояния
    restoreUIState() {
        if (this.filters.category) {
            this.updateCategoryUI(this.filters.category);
        }
        
        if (this.filters.view) {
            this.updateViewUI(this.filters.view);
        }
        
        if (this.filters.gridSize) {
            const gridSlider = document.getElementById('grid-size');
            if (gridSlider) {
                gridSlider.value = this.filters.gridSize;
                this.updateGridSize(this.filters.gridSize);
            }
        }
        
        if (this.filters.sort) {
            const sortSelect = document.getElementById('sort-select');
            if (sortSelect) {
                sortSelect.value = this.filters.sort;
            }
        }
        
        // Восстанавливаем значения фильтров цены
        const minPrice = document.getElementById('min-price');
        const maxPrice = document.getElementById('max-price');
        const minSlider = document.getElementById('range-min');
        const maxSlider = document.getElementById('range-max');
        
        if (minPrice && maxPrice && minSlider && maxSlider) {
            minPrice.value = this.filters.price.min;
            maxPrice.value = this.filters.price.max;
            minSlider.value = this.filters.price.min;
            maxSlider.value = this.filters.price.max;
        }
    }

    // Обновление UI категории
    updateCategoryUI(selectedCategory) {
        document.querySelectorAll('.category-item').forEach(item => {
            const category = item.dataset.category || 'all';
            if (category === selectedCategory) {
                item.classList.add('active');
                item.setAttribute('aria-current', 'page');
            } else {
                item.classList.remove('active');
                item.removeAttribute('aria-current');
            }
        });
    }

    // Показать уведомление
    showNotification(message, type = 'info') {
        if (window.VogueElite && window.VogueElite.showNotification) {
            window.VogueElite.showNotification(message, type);
            return;
        }
        
        const notification = document.createElement('div');
        notification.className = `catalog-notification notification-${type}`;
        notification.textContent = message;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'polite');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
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

    // Измерение производительности
    measurePerformance(methodName) {
        if (window.performance && performance.mark) {
            const startMark = `${methodName}-start`;
            const endMark = `${methodName}-end`;
            const measureName = `${methodName}-duration`;
            
            performance.mark(startMark);
            
            return {
                end: () => {
                    performance.mark(endMark);
                    performance.measure(measureName, startMark, endMark);
                    
                    const measures = performance.getEntriesByName(measureName);
                    if (measures[0]) {
                        console.log(`${methodName} заняло:`, measures[0].duration.toFixed(2), 'ms');
                        this.trackPerformance(methodName, measures[0].duration);
                    }
                }
            };
        }
        
        return { end: () => {} };
    }

    // Трекинг производительности
    trackPerformance(methodName, duration) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'timing_complete', {
                name: methodName,
                value: Math.round(duration),
                event_category: 'Performance'
            });
        }
    }

    // Трекинг событий
    trackEvent(eventName, data = {}) {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                ...data,
                page_path: window.location.pathname
            });
        }
        
        // Отправка на ваш сервер
        if (navigator.onLine) {
            fetch('/api/analytics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event: eventName,
                    ...data,
                    timestamp: Date.now(),
                    user_agent: navigator.userAgent,
                    screen_resolution: `${window.screen.width}x${window.screen.height}`
                })
            }).catch(() => {
                // Сохраняем для оффлайн отправки
                this.queueOfflineEvent(eventName, data);
            });
        } else {
            // Сохраняем для оффлайн отправки
            this.queueOfflineEvent(eventName, data);
        }
    }

    // Очередь оффлайн событий
    queueOfflineEvent(eventName, data) {
        try {
            const queue = JSON.parse(localStorage.getItem('analytics_queue') || '[]');
            queue.push({
                event: eventName,
                ...data,
                timestamp: Date.now()
            });
            
            // Ограничиваем очередь 100 событиями
            if (queue.length > 100) {
                queue.shift();
            }
            
            localStorage.setItem('analytics_queue', JSON.stringify(queue));
        } catch (error) {
            console.error('Ошибка сохранения оффлайн события:', error);
        }
    }

    // Отправка оффлайн событий
    sendOfflineEvents() {
        if (!navigator.onLine) {
            return;
        }
        
        try {
            const queue = JSON.parse(localStorage.getItem('analytics_queue') || '[]');
            if (queue.length === 0) {
                return;
            }
            
            // Отправляем все события
            queue.forEach(event => {
                fetch('/api/analytics', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(event)
                }).catch(() => {
                    // Если ошибка, оставляем в очереди
                });
            });
            
            // Очищаем очередь
            localStorage.removeItem('analytics_queue');
        } catch (error) {
            console.error('Ошибка отправки оффлайн событий:', error);
        }
    }

    // Инициализация Service Worker
    initServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw-catalog.js')
                .then((registration) => {
                    console.log('Service Worker зарегистрирован:', registration);
                    
                    // Проверяем обновления
                    if (registration.waiting) {
                        this.showServiceWorkerUpdate(registration);
                    }
                    
                    // Слушаем обновления
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.showServiceWorkerUpdate(registration);
                            }
                        });
                    });
                    
                    // Отправляем оффлайн события при восстановлении соединения
                    window.addEventListener('online', () => {
                        this.sendOfflineEvents();
                    });
                })
                .catch((error) => {
                    console.log('Ошибка регистрации Service Worker:', error);
                });
        }
    }

    // Показать уведомление об обновлении Service Worker
    showServiceWorkerUpdate(registration) {
        this.showNotification('Доступно обновление приложения', 'info');
        
        // Можно добавить кнопку для принудительного обновления
        const updateBtn = document.createElement('button');
        updateBtn.textContent = 'Обновить';
        updateBtn.onclick = () => {
            if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
            window.location.reload();
        };
        
        // Добавляем кнопку в уведомление или показываем отдельно
    }

    // Добавление CSS анимаций
    addAnimations() {
        if (document.getElementById('catalog-animations')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'catalog-animations';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes modalSlideIn {
                from {
                    transform: translateY(-50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .product-card {
                transition: all 0.3s ease;
                position: relative;
            }
            
            .product-card.hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(212, 175, 55, 0.2);
                z-index: 1;
            }
            
            .product-card:focus-within {
                outline: 2px solid #d4af37;
                outline-offset: 2px;
            }
            
            .quick-view-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .quick-view-modal.active {
                display: flex;
                opacity: 1;
                animation: fadeIn 0.3s ease;
            }
            
            .quick-view-content {
                background: white;
                max-width: 900px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                border-radius: 12px;
                position: relative;
                animation: modalSlideIn 0.3s ease;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            
            .filters-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9998;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .filters-modal.active {
                display: block;
                opacity: 1;
                animation: fadeIn 0.3s ease;
            }
            
            .filters-modal-content {
                position: absolute;
                top: 0;
                right: 0;
                width: 90%;
                max-width: 400px;
                height: 100%;
                background: white;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                overflow-y: auto;
            }
            
            .filters-modal.active .filters-modal-content {
                transform: translateX(0);
            }
            
            .fullscreen-image {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                z-index: 10000;
                display: none;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .fullscreen-image.active {
                display: flex;
                opacity: 1;
                animation: fadeIn 0.3s ease;
            }
            
            .fullscreen-content {
                position: relative;
                max-width: 90vw;
                max-height: 90vh;
            }
            
            .fullscreen-content img {
                max-width: 100%;
                max-height: 90vh;
                object-fit: contain;
            }
            
            .custom-tooltip {
                position: fixed;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10001;
                pointer-events: none;
                white-space: nowrap;
                animation: fadeIn 0.2s ease;
            }
            
            .catalog-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                animation: slideInRight 0.3s ease;
                max-width: 400px;
            }
            
            .loading-spinner {
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            /* Адаптивные стили */
            @media (max-width: 768px) {
                .quick-view-content {
                    width: 95%;
                    max-height: 95vh;
                }
                
                .filters-modal-content {
                    width: 100%;
                    max-width: none;
                }
            }
            
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Инициализация каталога при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, находимся ли мы на странице каталога
    if (document.querySelector('.catalog-page')) {
        const catalogManager = new CatalogManager();
        
        window.catalog = catalogManager;
        window.CatalogManager = CatalogManager;
        
        console.log('Модуль каталога инициализирован');
        
        // Отправляем оффлайн события при загрузке
        setTimeout(() => {
            catalogManager.sendOfflineEvents();
        }, 5000);
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CatalogManager;
}

// Service Worker для каталога
if ('serviceWorker' in navigator && window.location.pathname.includes('/catalog')) {
    navigator.serviceWorker.register('/sw-catalog.js')
        .then(() => console.log('Service Worker для каталога зарегистрирован'))
        .catch(err => console.log('Ошибка регистрации Service Worker:', err));
}
