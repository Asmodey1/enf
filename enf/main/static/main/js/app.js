/* ==========================================================================
   ENFANTS RICHES DÉPRIMÉS — клиентская логика
   HTMX делает запросы и подменяет HTML, а здесь только то, что нужно вокруг:
   CSRF, выезжающие панели, счётчик корзины, уведомления и мелочи интерфейса.
   Все обработчики висят на document, поэтому работают и для контента,
   который HTMX подгрузил позже.
   ========================================================================== */
(function () {
  'use strict';

  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const root = document.documentElement;

  /* ---------- Переводы ---------- */
  // gettext() и interpolate() даёт /jsi18n/ (JavaScriptCatalog Django, подключён в base.html),
  // строки для перевода лежат в locale/ru/LC_MESSAGES/djangojs.po.
  // Если скрипт не загрузился — показываем текст как есть, без перевода
  const gettext = window.gettext || ((text) => text);
  const interpolate = window.interpolate
    || ((text, values) => text.replace(/%\((\w+)\)s/g, (match, key) => values[key]));

  /* ---------- CSRF и параметры запросов ---------- */
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function csrfToken() {
    // После входа Django меняет токен, поэтому берём свежий из cookie при каждом запросе
    const meta = qs('meta[name="csrf-token"]');
    return getCookie('csrftoken') || (meta ? meta.content : '');
  }

  document.addEventListener('htmx:configRequest', (event) => {
    const detail = event.detail;

    if (detail.verb !== 'get') {
      detail.headers['X-CSRFToken'] = csrfToken();
    }

    // Пустые поля фильтров и поиска не тащим в адресную строку
    const elt = detail.elt;
    if (detail.verb === 'get' && elt instanceof Element && elt.closest('[data-clean-params]')) {
      Object.keys(detail.parameters).forEach((key) => {
        if (detail.parameters[key] === '') delete detail.parameters[key];
      });
    }
  });

  /* ---------- Выезжающие панели ---------- */
  let lastFocused = null;

  function syncScrollLock() {
    root.classList.toggle('is-locked', Boolean(qs('.drawer.is-open')));
  }

  function openDrawer(drawer) {
    if (typeof drawer === 'string') drawer = document.getElementById(drawer);
    if (!drawer || drawer.classList.contains('is-open')) return;

    qsa('.drawer.is-open').forEach((open) => closeDrawer(open, false));
    lastFocused = document.activeElement;
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    syncScrollLock();

    const panel = qs('.drawer__panel', drawer);
    if (panel) panel.focus({ preventScroll: true });
  }

  function closeDrawer(drawer, restoreFocus = true) {
    if (!drawer || !drawer.classList.contains('is-open')) return;

    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    syncScrollLock();

    if (restoreFocus && lastFocused && document.contains(lastFocused)) {
      lastFocused.focus({ preventScroll: true });
    }
  }

  function closeAllDrawers() {
    qsa('.drawer.is-open').forEach((drawer) => closeDrawer(drawer, false));
    syncScrollLock();
  }

  /* ---------- Корзина ---------- */
  function openCart() {
    const drawer = document.getElementById('cart-drawer');
    if (!drawer) return;
    openDrawer(drawer);
    htmx.ajax('GET', drawer.dataset.cartUrl, { target: '#cart-content', swap: 'innerHTML' });
  }

  function updateCartCount(count) {
    qsa('[data-cart-count]').forEach((el) => {
      el.textContent = count;
    });
  }

  /* ---------- Уведомления ---------- */
  function hideToast(toast) {
    toast.classList.remove('is-visible');
    setTimeout(() => toast.remove(), 400);
  }

  function showToast(message, type) {
    const stack = document.getElementById('toasts');
    if (!stack) return;

    const toast = document.createElement('div');
    toast.className = 'toast' + (type ? ' toast--' + type : '');
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.textContent = message;
    stack.appendChild(toast);

    void toast.offsetWidth; // перерисовка, чтобы сработала анимация появления
    toast.classList.add('is-visible');
    setTimeout(() => hideToast(toast), 3200);
  }

  window.showToast = showToast;

  /* ---------- Клики и клавиатура ---------- */
  document.addEventListener('click', (event) => {
    const cartTrigger = event.target.closest('[data-cart-open]');
    if (cartTrigger) {
      event.preventDefault();
      openCart();
      return;
    }

    const opener = event.target.closest('[data-drawer-open]');
    if (opener) {
      event.preventDefault();
      openDrawer(opener.dataset.drawerOpen);
      return;
    }

    const closer = event.target.closest('[data-drawer-close]');
    if (closer) {
      event.preventDefault();
      closeDrawer(closer.closest('.drawer'));
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;

    if (event.target.id === 'search-input') {
      const reset = qs('[data-search-reset]');
      if (reset) reset.click();
      return;
    }
    closeAllDrawers();
  });

  /* ---------- Активный пункт навигации ---------- */
  function updateActiveNav() {
    // Страница товара подсвечивает свою категорию через data-active-nav
    const hint = qs('#main-content [data-active-nav]');
    const activePath = hint ? hint.dataset.activeNav : window.location.pathname;

    qsa('[data-nav-link]').forEach((link) => {
      link.classList.toggle('is-active', link.getAttribute('href') === activePath);
    });
  }

  /* ---------- События HTMX ---------- */
  document.addEventListener('htmx:afterSwap', (event) => {
    const target = event.detail.target;

    if (target.id === 'cart-content') {
      const cart = qs('[data-cart-total]', target);
      if (cart) updateCartCount(cart.dataset.cartTotal);
    }

    // Пришло содержимое для панели (корзина, фильтры) — показываем её
    if (target.hasAttribute('data-drawer-content')) {
      openDrawer(target.closest('.drawer'));
    }

    if (target.id === 'main-content') {
      closeAllDrawers();
      window.scrollTo(0, 0);
    }

    if (target.id === 'search-wrapper') {
      const input = qs('input', target);
      if (input) {
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
      }
    }
  });

  document.addEventListener('htmx:afterSettle', (event) => {
    if (event.detail.target.id === 'main-content') updateActiveNav();
  });

  document.addEventListener('htmx:historyRestore', () => {
    closeAllDrawers();
    updateActiveNav();
  });

  // В кэш истории не должны попасть открытые панели
  document.addEventListener('htmx:beforeHistorySave', () => {
    qsa('#main-content .drawer.is-open').forEach((drawer) => {
      drawer.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
    });
  });

  // Блокируем кнопку отправки, пока идёт запрос, — чтобы не создать заказ дважды
  document.addEventListener('htmx:beforeRequest', (event) => {
    const form = event.detail.elt;
    if (form.tagName !== 'FORM') return;

    qsa('button[type="submit"]', form).forEach((button) => {
      if (button.disabled) return;
      button.disabled = true;
      button.classList.add('is-loading');
    });
  });

  document.addEventListener('htmx:afterRequest', (event) => {
    const form = event.detail.elt;
    if (form.tagName !== 'FORM') return;
    // Уходим на страницу оплаты — кнопку не разблокируем
    if (event.detail.xhr && event.detail.xhr.getResponseHeader('HX-Redirect')) return;

    qsa('button.is-loading', form).forEach((button) => {
      button.disabled = false;
      button.classList.remove('is-loading');
    });
  });

  document.addEventListener('htmx:responseError', (event) => {
    let message = gettext('Something went wrong. Please try again.');
    try {
      const data = JSON.parse(event.detail.xhr.responseText);
      if (data.error) message = data.error;
    } catch (error) {
      // ответ не JSON — оставляем общее сообщение
    }
    showToast(message, 'error');
  });

  document.addEventListener('htmx:sendError', () => {
    showToast(gettext('No connection. Please check your network.'), 'error');
  });

  /* ---------- Страница товара: выбор размера ---------- */
  let sizeWarnedAt = 0;

  document.addEventListener('change', (event) => {
    const radio = event.target.closest('input[name="size_id"]');
    if (!radio) return;

    const form = radio.closest('form');
    const label = qs('[data-size-label]', form);
    const hint = qs('[data-size-hint]', form);
    const stock = Number(radio.dataset.stock);

    form.classList.remove('is-invalid');
    if (label) label.textContent = radio.dataset.sizeName;
    if (hint) hint.textContent = stock > 0 && stock <= 3 ? interpolate(gettext('Only %(count)s left'), { count: stock }, true) : '';
  });

  // Вместо системной подсказки браузера — своё сообщение, если размер не выбран
  document.addEventListener('invalid', (event) => {
    if (event.target.name !== 'size_id') return;
    event.preventDefault();

    const form = event.target.closest('form');
    form.classList.remove('is-invalid');
    void form.offsetWidth; // перезапуск анимации «встряхивания»
    form.classList.add('is-invalid');

    if (Date.now() - sizeWarnedAt > 600) {
      showToast(gettext('Please select a size'));
      sizeWarnedAt = Date.now();
    }
  }, true);

  /* ---------- Регистрация: совпадение паролей ---------- */
  document.addEventListener('input', (event) => {
    if (event.target.id !== 'id_password1' && event.target.id !== 'id_password2') return;

    const password = document.getElementById('id_password1');
    const confirm = document.getElementById('id_password2');
    if (!password || !confirm) return;

    const mismatch = confirm.value && password.value !== confirm.value;
    confirm.setCustomValidity(mismatch ? gettext('Passwords do not match') : '');
  });

  /* ---------- Старт ---------- */
  function init() {
    updateActiveNav();
    qsa('#toasts .toast').forEach((toast) => setTimeout(() => hideToast(toast), 4000));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
