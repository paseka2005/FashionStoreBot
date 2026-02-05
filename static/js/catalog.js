// catalog.js - Исправленный модуль каталога товаров для VOGUE ÉLITE

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
        
        // Сохраняем контекст для событий
        this.debouncedSearch = this.debounce(this.searchProducts.bind(this), 300);
        this.debouncedResize = this.debounce(this.handleResize.bind(this), 250);
        
        this.init();
    }

    // Инициализация каталога
    async init() {
        console.log('CatalogManager: Инициализация...');
        
        // Сначала проверяем существование необходимых элементов
        if (!this.checkRequiredElements()) {
            console.error('CatalogManager: Не найдены необходимые элементы DOM');
            return;
        }
        
        this.setupEventListeners();
        this.setupUI();
        
        // Загружаем продукты
        await this.loadProducts();
        
        // Применяем фильтры и рендерим
        this.applyFilters();
        
        console.log('CatalogManager: Инициализация завершена');
    }

    // Проверка необходимых элементов
    checkRequiredElements() {
        const requiredElements = [
            'products-grid',
            'catalog-sidebar',
            'sort-select'
        ];
        
        for (const elementId of requiredElements) {
            if (!document.getElementById(elementId)) {
                console.error(`Элемент с ID "${elementId}" не найден`);
                return false;
            }
        }
        
        return true;
    }

    // Настройка обработчиков событий
    setupEventListeners() {
        console.log('CatalogManager: Настройка обработчиков событий...');
        
        // Категории
        document.addEventListener('click', (event) => {
            const categoryItem = event.target.closest('.category-item');
            if (categoryItem && !categoryItem.classList.contains('active')) {
                event.preventDefault();
                const category = categoryItem.dataset.category || 'all';
                this.setFilter('category', category);
                this.updateCategoryUI(category);
            }
        });

        // Цена
        const minPriceInput = document.getElementById('min-price');
        const maxPriceInput = document.getElementById('max-price');
        const rangeMin = document.getElementById('range-min');
        const rangeMax = document.getElementById('range-max');
        
        if (minPriceInput && maxPriceInput) {
            const priceUpdate = () => {
                this.filters.price = {
                    min: parseInt(minPriceInput.value) || 0,
                    max: parseInt(maxPriceInput.value) || 100000
                };
                this.applyFilters();
            };
            
            minPriceInput.addEventListener('change', priceUpdate);
            maxPriceInput.addEventListener('change', priceUpdate);
        }
        
        if (rangeMin && rangeMax) {
            const rangeUpdate = () => {
                this.filters.price = {
                    min: parseInt(rangeMin.value) || 0,
                    max: parseInt(rangeMax.value) || 100000
                };
                if (minPriceInput) minPriceInput.value = this.filters.price.min;
                if (maxPriceInput) maxPriceInput.value = this.filters.price.max;
                this.applyFilters();
            };
            
            rangeMin.addEventListener('input', rangeUpdate);
            rangeMax.addEventListener('input', rangeUpdate);
        }

        // Бренды
        document.addEventListener('click', (event) => {
            const brandFilter = event.target.closest('.filter-item[data-filter="brand"]');
            if (brandFilter) {
                const brand = brandFilter.dataset.value;
                const checkbox = brandFilter.querySelector('.filter-checkbox');
                
                if (checkbox) {
                    checkbox.classList.toggle('checked');
                    this.toggleFilter('brands', brand);
                }
            }
        });

        // Цвета
        document.addEventListener('click', (event) => {
            const colorItem = event.target.closest('.color-item');
            if (colorItem) {
                colorItem.classList.toggle('active');
                const color = colorItem.dataset.color;
                
                if (colorItem.classList.contains('active')) {
                    if (!this.filters.colors.includes(color)) {
                        this.filters.colors.push(color);
                    }
                } else {
                    const index = this.filters.colors.indexOf(color);
                    if (index > -1) {
                        this.filters.colors.splice(index, 1);
                    }
                }
                this.applyFilters();
            }
        });

        // Размеры
        document.addEventListener('click', (event) => {
            const sizeItem = event.target.closest('.size-item');
            if (sizeItem) {
                sizeItem.classList.toggle('active');
                const size = sizeItem.dataset.size;
                
                if (sizeItem.classList.contains('active')) {
                    if (!this.filters.sizes.includes(size)) {
                        this.filters.sizes.push(size);
                    }
                } else {
                    const index = this.filters.sizes.indexOf(size);
                    if (index > -1) {
                        this.filters.sizes.splice(index, 1);
                    }
                }
                this.applyFilters();
            }
        });

        // Специальные фильтры
        document.addEventListener('click', (event) => {
            const specialFilter = event.target.closest('.filter-item[data-filter="special"]');
            if (specialFilter) {
                const special = specialFilter.dataset.value;
                const checkbox = specialFilter.querySelector('.filter-checkbox');
                
                if (checkbox) {
                    checkbox.classList.toggle('checked');
                    this.toggleFilter('specials', special);
                }
            }
        });

        // Сортировка
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (event) => {
                this.setFilter('sort', event.target.value);
            });
        }

        // Вид отображения
        document.addEventListener('click', (event) => {
            const viewBtn = event.target.closest('.view-btn');
            if (viewBtn && !viewBtn.classList.contains('active')) {
                const view = viewBtn.dataset.view;
                this.setFilter('view', view);
                this.updateViewUI(view);
            }
        });

        // Размер сетки
        const gridSlider = document.getElementById('grid-size');
        if (gridSlider) {
            gridSlider.addEventListener('input', (event) => {
                this.setFilter('gridSize', parseInt(event.target.value));
                this.updateGridSize(parseInt(event.target.value));
            });
        }

        // Сброс фильтров
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }

        // Поиск
        const searchInput = document.getElementById('catalog-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.debouncedSearch(searchInput.value);
            });
        }

        // Пагинация
        document.addEventListener('click', (event) => {
            const pageBtn = event.target.closest('.page-btn');
            if (pageBtn && !pageBtn.classList.contains('disabled')) {
                event.preventDefault();
                const page = parseInt(pageBtn.dataset.page) || parseInt(pageBtn.textContent);
                if (page) {
                    this.goToPage(page);
                }
            }
        });

        // Быстрый просмотр
        document.addEventListener('click', (event) => {
            const quickViewBtn = event.target.closest('.quick-view-btn');
            if (quickViewBtn) {
                event.preventDefault();
                const productCard = quickViewBtn.closest('.product-card');
                const productId = productCard ? productCard.dataset.productId : null;
                if (productId) {
                    this.showQuickView(productId);
                }
            }
        });

        // Избранное
        document.addEventListener('click', (event) => {
            const wishlistBtn = event.target.closest('.wishlist-btn');
            if (wishlistBtn) {
                event.preventDefault();
                const productCard = wishlistBtn.closest('.product-card');
                const productId = productCard ? productCard.dataset.productId : null;
                if (productId) {
                    this.toggleWishlist(productId, wishlistBtn);
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
        const mobileFiltersBtn = document.getElementById('mobile-filters-btn');
        if (mobileFiltersBtn) {
            mobileFiltersBtn.addEventListener('click', () => {
                const sidebar = document.getElementById('catalog-sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('mobile-visible');
                }
            });
        }

        // Ресайз окна
        window.addEventListener('resize', this.debouncedResize);

        // Закрытие по Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const sidebar = document.getElementById('catalog-sidebar');
                if (sidebar && sidebar.classList.contains('mobile-visible')) {
                    sidebar.classList.remove('mobile-visible');
                }
                
                const modal = document.getElementById('quick-view-modal');
                if (modal && modal.style.display === 'block') {
                    this.hideQuickView();
                }
            }
        });

        console.log('CatalogManager: Обработчики событий настроены');
    }

    // Настройка UI
    setupUI() {
        this.createQuickViewModal();
        this.updateViewUI(this.filters.view);
        this.updateGridSize(this.filters.gridSize);
    }

    // Загрузка продуктов
    async loadProducts() {
        console.log('CatalogManager: Загрузка продуктов...');
        this.showLoading();
        
        try {
            // Сначала пытаемся загрузить с сервера
            const response = await fetch('/api/products');
            
            if (response.ok) {
                const data = await response.json();
                console.log('CatalogManager: Получены данные с сервера', data);
                
                if (data.success && data.products) {
                    this.products = data.products;
                    console.log(`CatalogManager: Загружено ${this.products.length} продуктов`);
                } else {
                    // Если сервер вернул ошибку, используем демо-данные
                    this.products = this.getDemoProducts();
                    console.log('CatalogManager: Используются демо-данные');
                }
            } else {
                // Если запрос не удался, используем демо-данные
                this.products = this.getDemoProducts();
                console.log('CatalogManager: Используются демо-данные (ошибка сети)');
            }
        } catch (error) {
            // Если произошла ошибка, используем демо-данные
            console.error('CatalogManager: Ошибка загрузки продуктов:', error);
            this.products = this.getDemoProducts();
            console.log('CatalogManager: Используются демо-данные (исключение)');
        }
        
        // Обновляем статистику категорий
        this.updateCategoryCounts();
        
        this.hideLoading();
    }

    // Получение демо продуктов
    getDemoProducts() {
        const demoProducts = [];
        const categories = ['Платья', 'Костюмы', 'Блузы', 'Брюки', 'Юбки', 'Куртки', 'Пальто', 'Обувь', 'Сумки', 'Украшения'];
        const brands = ['Vogue', 'Dior', 'Chanel', 'Gucci', 'Prada', 'Versace', 'Armani', 'Hermès', 'Louis Vuitton', 'Balenciaga'];
        const colors = ['черный', 'белый', 'красный', 'синий', 'зеленый', 'золотой', 'серебряный', 'фиолетовый', 'розовый', 'коричневый'];
        const sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
        
        for (let i = 0; i < 48; i++) {
            const product = {
                id: i + 1,
                name: `Товар ${i + 1}`,
                category: categories[i % categories.length],
                price: Math.floor(Math.random() * 5000) + 1000,
                discount: i % 5 === 0 ? 20 : i % 7 === 0 ? 15 : 0,
                image_url: `/static/img/products/product-${(i % 12) + 1}.jpg`,
                brand: brands[i % brands.length],
                color: colors[i % colors.length],
                size: sizes[i % sizes.length],
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

    // Обновление счетчиков категорий
    updateCategoryCounts() {
        // Обновляем счетчик "Все товары"
        const allCountElement = document.getElementById('all-count');
        if (allCountElement) {
            allCountElement.textContent = this.products.length.toString();
        }
        
        // Обновляем счетчики специальных фильтров
        const newCount = this.products.filter(p => p.is_new).length;
        const saleCount = this.products.filter(p => p.discount > 0).length;
        const exclusiveCount = this.products.filter(p => p.is_exclusive).length;
        const limitedCount = this.products.filter(p => p.is_limited).length;
        
        const newCountElement = document.getElementById('new-count');
        const saleCountElement = document.getElementById('sale-count');
        const exclusiveCountElement = document.getElementById('exclusive-count');
        const limitedCountElement = document.getElementById('limited-count');
        
        if (newCountElement) newCountElement.textContent = newCount.toString();
        if (saleCountElement) saleCountElement.textContent = saleCount.toString();
        if (exclusiveCountElement) exclusiveCountElement.textContent = exclusiveCount.toString();
        if (limitedCountElement) limitedCountElement.textContent = limitedCount.toString();
    }

    // Применение фильтров
    applyFilters() {
        if (this.isLoading) return;
        
        console.log('CatalogManager: Применение фильтров...');
        
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
                    if (special === 'new') return product.is_new;
                    if (special === 'sale') return product.discount > 0;
                    if (special === 'exclusive') return product.is_exclusive;
                    if (special === 'limited') return product.is_limited;
                    return false;
                });
            });
        }
        
        // Сортировка
        this.sortProducts();
        
        // Обновление пагинации
        this.updatePagination();
        
        // Рендеринг продуктов
        this.renderProducts();
        
        // Обновление статистики
        this.updateStats();
        
        console.log(`CatalogManager: Фильтры применены. Найдено: ${this.filteredProducts.length} товаров`);
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
            case 'rating':
                this.filteredProducts.sort((a, b) => {
                    return (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0);
                });
                break;
                
            case 'discount':
                this.filteredProducts.sort((a, b) => {
                    return (parseFloat(b.discount) || 0) - (parseFloat(a.discount) || 0);
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

    // Поиск продуктов
    searchProducts(query) {
        if (!query || !query.trim()) {
            this.applyFilters();
            return;
        }
        
        const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 0);
        
        this.filteredProducts = this.products.filter(product => {
            const searchText = `
                ${product.name || ''} 
                ${product.category || ''} 
                ${product.brand || ''} 
                ${product.color || ''} 
                ${product.description || ''}
            `.toLowerCase();
            
            return searchTerms.every(term => searchText.includes(term));
        });
        
        this.sortProducts();
        this.updatePagination();
        this.renderProducts();
        this.updateStats();
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
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) {
            console.error('CatalogManager: Не найден элемент products-grid');
            return;
        }
        
        // Очищаем сетку
        productsGrid.innerHTML = '';
        
        // Если нет товаров после фильтрации
        if (this.filteredProducts.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Рассчитываем какие товары показывать на текущей странице
        const startIndex = (this.currentPage - 1) * this.productsPerPage;
        const endIndex = startIndex + this.productsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);
        
        // Создаем фрагмент для эффективного добавления
        const fragment = document.createDocumentFragment();
        
        pageProducts.forEach(product => {
            const productCard = this.createProductCard(product);
            fragment.appendChild(productCard);
        });
        
        // Добавляем все карточки за один раз
        productsGrid.appendChild(fragment);
        
        // Обновляем UI вида
        this.updateViewUI(this.filters.view);
    }

    // Создание карточки продукта
    createProductCard(product) {
        const card = document.createElement('article');
        card.className = 'product-card';
        card.dataset.productId = product.id;
        
        const price = parseFloat(product.price) || 0;
        const discount = parseFloat(product.discount) || 0;
        const finalPrice = price * (1 - discount / 100);
        
        const badges = this.createProductBadges(product);
        const starRating = this.generateStarRating(product.rating || 0);
        
        let stockBadge = '';
        if (product.stock <= 5 && product.stock > 0) {
            stockBadge = '<div class="stock-badge">Осталось мало</div>';
        } else if (product.stock === 0) {
            stockBadge = '<div class="stock-badge out-of-stock">Нет в наличии</div>';
        }
        
        const description = product.description || '';
        const shortDescription = description.length > 100 ? 
            description.substring(0, 100) + '...' : description;
        
        const formattedPrice = this.formatPrice(finalPrice);
        const formattedOriginalPrice = discount > 0 ? this.formatPrice(price) : '';
        
        card.innerHTML = `
            ${badges}
            <div class="product-image">
                <img src="${product.image_url || '/static/img/placeholder.jpg'}" 
                     alt="${product.name || 'Товар'}"
                     loading="lazy"
                     class="product-main-image"
                     onerror="this.src='/static/img/placeholder.jpg'">
                <div class="product-actions">
                    <button class="action-btn wishlist-btn" title="В избранное">
                        <i class="far fa-heart"></i>
                    </button>
                    <button class="action-btn quick-view-btn" title="Быстрый просмотр">
                        <i class="far fa-eye"></i>
                    </button>
                </div>
                ${stockBadge}
            </div>
            <div class="product-info">
                <div class="product-category">${product.category || ''}</div>
                <h3 class="product-title">
                    <a href="/product/${product.id}">${product.name || 'Товар'}</a>
                </h3>
                <p class="product-description">${shortDescription}</p>
                
                <div class="product-meta">
                    <div class="product-price">
                        ${discount > 0 ? `
                            <span class="current-price">${formattedPrice}</span>
                            <span class="original-price">${formattedOriginalPrice}</span>
                        ` : `
                            <span class="current-price">${formattedPrice}</span>
                        `}
                    </div>
                    
                    <div class="product-rating">
                        <div class="stars">${starRating}</div>
                    </div>
                </div>
                
                <div class="product-footer">
                    <button class="btn-add-cart" data-product-id="${product.id}">
                        <i class="fas fa-shopping-bag"></i>
                        <span>В корзину</span>
                    </button>
                    <a href="/product/${product.id}" class="btn-view" title="Подробнее">
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        `;
        
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
        
        if (product.is_new) {
            badges += '<span class="product-badge badge-new">Новинка</span>';
        }
        if (product.is_exclusive) {
            badges += '<span class="product-badge badge-exclusive">Эксклюзив</span>';
        }
        if (product.is_limited) {
            badges += '<span class="product-badge badge-limited">Лимитированная</span>';
        }
        if (product.discount > 0) {
            badges += `<span class="product-badge badge-sale">-${product.discount}%</span>`;
        }
        
        if (badges) {
            return `<div class="product-badges">${badges}</div>`;
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
        const productsCount = document.getElementById('products-count');
        const currentCategory = document.getElementById('current-category');
        const currentPageElement = document.getElementById('current-page');
        const totalPagesElement = document.getElementById('total-pages');
        
        if (productsCount) {
            productsCount.textContent = this.filteredProducts.length.toString();
        }
        
        if (currentCategory) {
            currentCategory.textContent = this.filters.category === 'all' ? 'Все' : this.filters.category;
        }
        
        if (currentPageElement) {
            currentPageElement.textContent = this.currentPage.toString();
        }
        
        if (totalPagesElement) {
            totalPagesElement.textContent = this.totalPages.toString();
        }
    }

    // Обновление пагинации
    updatePagination() {
        this.totalPages = Math.ceil(this.filteredProducts.length / this.productsPerPage);
        if (this.totalPages === 0) this.totalPages = 1;
        this.currentPage = Math.min(this.currentPage, this.totalPages);
        
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;
        
        paginationContainer.innerHTML = this.createPaginationHTML();
    }

    // Создание HTML пагинации
    createPaginationHTML() {
        if (this.totalPages <= 1) {
            return '';
        }
        
        let html = '';
        
        // Кнопка "предыдущая"
        html += `
            <a href="#" class="page-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
               ${this.currentPage === 1 ? '' : 'data-page="' + (this.currentPage - 1) + '"'}>
                <i class="fas fa-chevron-left"></i>
            </a>
        `;
        
        // Номера страниц
        const maxVisible = this.isMobile ? 3 : 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        // Первая страница и многоточие
        if (startPage > 1) {
            html += `<a href="#" class="page-btn" data-page="1">1</a>`;
            if (startPage > 2) {
                html += `<span class="page-btn disabled">...</span>`;
            }
        }
        
        // Основные страницы
        for (let i = startPage; i <= endPage; i++) {
            const isCurrent = i === this.currentPage;
            html += `
                <a href="#" class="page-btn ${isCurrent ? 'active' : ''}" data-page="${i}">
                    ${i}
                </a>
            `;
        }
        
        // Последняя страница и многоточие
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += `<span class="page-btn disabled">...</span>`;
            }
            html += `<a href="#" class="page-btn" data-page="${this.totalPages}">${this.totalPages}</a>`;
        }
        
        // Кнопка "следующая"
        html += `
            <a href="#" class="page-btn ${this.currentPage === this.totalPages ? 'disabled' : ''}" 
               ${this.currentPage === this.totalPages ? '' : 'data-page="' + (this.currentPage + 1) + '"'}>
                <i class="fas fa-chevron-right"></i>
            </a>
        `;
        
        return html;
    }

    // Переход на страницу
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        this.renderProducts();
        this.updatePagination();
        this.updateStats();
        
        // Плавная прокрутка к началу каталога
        const catalogHeader = document.querySelector('.catalog-header');
        if (catalogHeader) {
            catalogHeader.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    // Показ пустого состояния
    showEmptyState() {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) return;
        
        productsGrid.innerHTML = `
            <div class="catalog-empty">
                <div class="catalog-empty-icon">
                    <i class="fas fa-search"></i>
                </div>
                <h2>Товары не найдены</h2>
                <p>Попробуйте изменить параметры фильтрации или выбрать другую категорию</p>
                <button class="clear-filters" id="clear-filters-empty">
                    <i class="fas fa-times"></i>
                    <span>Сбросить все фильтры</span>
                </button>
            </div>
        `;
        
        const clearButton = document.getElementById('clear-filters-empty');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.resetFilters();
            });
        }
    }

    // Показать загрузку
    showLoading() {
        this.isLoading = true;
        const productsGrid = document.getElementById('products-grid');
        if (productsGrid) {
            productsGrid.innerHTML = `
                <div class="catalog-loading">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <p>Загрузка товаров...</p>
                </div>
            `;
        }
    }

    // Скрыть загрузку
    hideLoading() {
        this.isLoading = false;
    }

    // Создание модального окна быстрого просмотра
    createQuickViewModal() {
        if (document.getElementById('quick-view-modal')) return;
        
        const modal = document.createElement('div');
        modal.id = 'quick-view-modal';
        modal.className = 'quick-view-modal';
        modal.style.display = 'none';
        
        modal.innerHTML = `
            <div class="quick-view-content">
                <button class="quick-view-close" id="quick-view-close-modal">
                    <i class="fas fa-times"></i>
                </button>
                <div class="quick-view-body" id="quick-view-body">
                    <!-- Контент будет загружен динамически -->
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Обработчик закрытия
        const closeBtn = modal.querySelector('#quick-view-close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideQuickView();
            });
        }
        
        // Закрытие по клику вне модального окна
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.hideQuickView();
            }
        });
    }

    // Показать быстрый просмотр
    async showQuickView(productId) {
        const product = this.products.find(p => p.id == productId);
        if (!product) return;
        
        const modal = document.getElementById('quick-view-modal');
        const body = document.getElementById('quick-view-body');
        
        if (!modal || !body) return;
        
        body.innerHTML = `
            <div class="quick-view-loading">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <span>Загрузка...</span>
            </div>
        `;
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Простой контент для быстрого просмотра
        const price = parseFloat(product.price) || 0;
        const discount = parseFloat(product.discount) || 0;
        const finalPrice = price * (1 - discount / 100);
        
        const formattedPrice = this.formatPrice(finalPrice);
        const formattedOriginalPrice = discount > 0 ? this.formatPrice(price) : '';
        
        body.innerHTML = `
            <div class="quick-view-product">
                <div class="quick-view-gallery">
                    <div class="quick-view-main-image">
                        <img src="${product.image_url || '/static/img/placeholder.jpg'}" 
                             alt="${product.name || 'Товар'}"
                             onerror="this.src='/static/img/placeholder.jpg'">
                    </div>
                </div>
                
                <div class="quick-view-info">
                    <div class="quick-view-header">
                        <div class="quick-view-category">${product.category || ''}</div>
                        <h2 class="quick-view-title">${product.name || 'Товар'}</h2>
                        <div class="quick-view-rating">
                            ${this.generateStarRating(product.rating || 0)}
                            <span class="rating-value">(${(product.rating || 0).toFixed(1)})</span>
                        </div>
                    </div>
                    
                    <div class="quick-view-price">
                        ${discount > 0 ? `
                            <div class="current-price">${formattedPrice}</div>
                            <div class="original-price">${formattedOriginalPrice}</div>
                            <div class="discount-badge">-${discount}%</div>
                        ` : `
                            <div class="current-price">${formattedPrice}</div>
                        `}
                    </div>
                    
                    <div class="quick-view-description">
                        <p>${product.description || 'Описание товара отсутствует'}</p>
                    </div>
                    
                    <div class="quick-view-details">
                        ${product.brand ? `<div><strong>Бренд:</strong> ${product.brand}</div>` : ''}
                        ${product.color ? `<div><strong>Цвет:</strong> ${product.color}</div>` : ''}
                        ${product.size ? `<div><strong>Размер:</strong> ${product.size}</div>` : ''}
                    </div>
                    
                    <div class="quick-view-actions">
                        <button class="btn-add-to-cart" data-product-id="${product.id}">
                            <i class="fas fa-shopping-bag"></i>
                            <span>Добавить в корзину</span>
                        </button>
                    </div>
                    
                    <div class="quick-view-footer">
                        <a href="/product/${product.id}" class="btn-view-details">
                            <i class="fas fa-external-link-alt"></i>
                            <span>Подробнее о товаре</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        // Обработчик добавления в корзину
        const addToCartBtn = body.querySelector('.btn-add-to-cart');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => {
                this.addToCart(productId, addToCartBtn);
            });
        }
    }

    // Скрыть быстрый просмотр
    hideQuickView() {
        const modal = document.getElementById('quick-view-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    // Обновление вида отображения
    updateViewUI(selectedView) {
        document.querySelectorAll('.view-btn').forEach(btn => {
            if (btn.dataset.view === selectedView) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        const productsGrid = document.getElementById('products-grid');
        if (productsGrid) {
            productsGrid.className = 'catalog-products-grid';
            if (selectedView === 'list') {
                productsGrid.classList.add('list-view');
            }
        }
    }

    // Обновление размера сетки
    updateGridSize(size) {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) return;
        
        if (size === 1) {
            productsGrid.classList.add('compact');
        } else {
            productsGrid.classList.remove('compact');
        }
    }

    // Обновление UI категории
    updateCategoryUI(selectedCategory) {
        document.querySelectorAll('.category-item').forEach(item => {
            const category = item.dataset.category || 'all';
            if (category === selectedCategory) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // Обработчик ресайза
    handleResize() {
        this.isMobile = window.innerWidth < 768;
        this.updatePagination();
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
        if (sortSelect) sortSelect.value = 'newest';
        
        const gridSlider = document.getElementById('grid-size');
        if (gridSlider) gridSlider.value = 2;
        
        const minPrice = document.getElementById('min-price');
        const maxPrice = document.getElementById('max-price');
        const rangeMin = document.getElementById('range-min');
        const rangeMax = document.getElementById('range-max');
        
        if (minPrice) minPrice.value = 0;
        if (maxPrice) maxPrice.value = 100000;
        if (rangeMin) rangeMin.value = 0;
        if (rangeMax) rangeMax.value = 100000;
        
        // Сброс чекбоксов
        document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.classList.remove('checked');
        });
        
        // Сброс цветов
        document.querySelectorAll('.color-item').forEach(color => {
            color.classList.remove('active');
        });
        
        // Сброс размеров
        document.querySelectorAll('.size-item').forEach(size => {
            size.classList.remove('active');
        });
        
        // Сброс категорий
        document.querySelectorAll('.category-item').forEach(cat => {
            if (cat.dataset.category === 'all') {
                cat.classList.add('active');
            } else {
                cat.classList.remove('active');
            }
        });
        
        // Сброс вида
        this.updateViewUI('grid');
        this.updateGridSize(2);
        
        this.applyFilters();
        this.showNotification('Фильтры сброшены');
    }

    // Переключение избранного
    toggleWishlist(productId, button) {
        if (!button) return;
        
        const icon = button.querySelector('i');
        if (!icon) return;
        
        const isActive = button.classList.contains('active');
        
        if (isActive) {
            button.classList.remove('active');
            icon.className = 'far fa-heart';
            this.showNotification('Удалено из избранного');
        } else {
            button.classList.add('active');
            icon.className = 'fas fa-heart';
            this.showNotification('Добавлено в избранное');
        }
    }

    // Добавление в корзину
    addToCart(productId, button) {
        const product = this.products.find(p => p.id == productId);
        if (!product) return;
        
        const originalHTML = button.innerHTML;
        const originalText = button.querySelector('span').textContent;
        
        button.innerHTML = `
            <i class="fas fa-check"></i>
            <span>Добавлено!</span>
        `;
        button.disabled = true;
        
        this.showNotification(`${product.name} добавлен в корзину`);
        
        // Восстанавливаем состояние через 2 секунды
        setTimeout(() => {
            button.innerHTML = `
                <i class="fas fa-shopping-bag"></i>
                <span>${originalText}</span>
            `;
            button.disabled = false;
        }, 2000);
        
        // Добавляем в корзину через глобальный объект, если он есть
        if (window.cart && typeof window.cart.addItem === 'function') {
            window.cart.addItem(productId, 1);
        }
    }

    // Показать уведомление
    showNotification(message, type = 'success') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = 'catalog-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#d4af37'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        // Удаляем через 3 секунды
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
        
        // Добавляем стили для анимации, если их нет
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
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
            `;
            document.head.appendChild(style);
        }
    }
}

// Инициализация каталога при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM загружен, инициализация каталога...');
    
    // Проверяем, находимся ли мы на странице каталога
    if (document.querySelector('.catalog-page') || document.getElementById('products-grid')) {
        try {
            const catalogManager = new CatalogManager();
            window.catalog = catalogManager;
            console.log('Каталог успешно инициализирован');
        } catch (error) {
            console.error('Ошибка инициализации каталога:', error);
        }
    }
});

// Добавляем обработку ошибок для изображений
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('error', (event) => {
        if (event.target.tagName === 'IMG' && event.target.classList.contains('product-main-image')) {
            event.target.src = '/static/img/placeholder.jpg';
            event.target.alt = 'Изображение недоступно';
        }
    }, true);
});
