/* ==========================================================================
   Переключатель языка RU ⇄ EN — клиентская часть
   Сама смена языка работает и без этого файла: это обычная POST-форма.
   Здесь только две поправки под HTMX-навигацию сайта.
   Куда положить: main/static/main/js/lang_switch.js (подключить в base.html с defer).
   ========================================================================== */
(function () {
  'use strict';

  const HTMX_HISTORY_KEY = 'htmx-history-cache';
  const LANGUAGE_COOKIE = 'django_language'; // settings.LANGUAGE_COOKIE_NAME

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

  document.addEventListener('submit', (event) => {
    const form = event.target.closest('[data-lang-switch]');
    if (!form) return;

    // 1. Шапка рендерится один раз при полной загрузке, а дальше страницы меняет HTMX
    //    (hx-get + hx-push-url). Значит, next из шаблона может указывать на страницу,
    //    с которой пользователь уже ушёл. Берём адрес, который сейчас в строке браузера.
    const next = form.querySelector('input[name="next"]');
    if (next) next.value = window.location.pathname + window.location.search;

    // 2. Для кнопки «Назад» HTMX хранит копии страниц в localStorage — они на старом
    //    языке. Чистим кэш: при промахе HTMX сам перезагрузит страницу
    //    (refreshOnHistoryMiss в base.html), и она придёт уже на новом языке.
    try {
      localStorage.removeItem(HTMX_HISTORY_KEY);
    } catch (error) {
      // localStorage бывает недоступен (приватный режим) — это не критично
    }
  });

  // 3. Браузер может вернуть страницу «Назад» целиком из своего кэша (bfcache),
  //    тогда она так и останется на старом языке. Сверяем <html lang> с cookie.
  window.addEventListener('pageshow', (event) => {
    const saved = getCookie(LANGUAGE_COOKIE);
    if (event.persisted && saved && saved !== document.documentElement.lang) {
      window.location.reload();
    }
  });
})();
