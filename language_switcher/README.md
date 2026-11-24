# Переключатель языка RU ⇄ EN

Кнопка **подключена**, сайт **переведён на русский**: шаги 1–7 выполнены.
Осталось только шаг 8 — названия и описания товаров и категорий из базы данных.

| Файл | Что это |
|---|---|
| `enf/main/templates/main/includes/lang_switch.html` | шаблон кнопки |
| `enf/main/static/main/css/lang_switch.css` | стили кнопки |
| `enf/main/static/main/js/lang_switch.js` | две поправки под HTMX |
| `enf/locale/ru/LC_MESSAGES/django.po` / `.mo` | переводы шаблонов и Python-кода (169 строк) |
| `enf/locale/ru/LC_MESSAGES/djangojs.po` / `.mo` | переводы строк из `app.js` (5 строк) |
| `language_switcher/demo.html` | превью без Django |

`demo.html` откройте двойным кликом в Chrome или Edge. Стили он берёт прямо из
`enf/main/static/main/css/`, поэтому папку `language_switcher` не переносите.

---

## Как это работает

Перевод в Django делится на три независимые части:

1. **Какой язык включить.** Это решает `LocaleMiddleware` на каждом запросе. Порядок такой:
   cookie `django_language` → заголовок браузера `Accept-Language` → `LANGUAGE_CODE` из settings.
2. **Что переводить.** В шаблонах и коде строки оборачиваются в `{% translate %}` / `gettext()`.
3. **Чем переводить.** Это файл `locale/ru/LC_MESSAGES/django.po`, в нём пары
   «английский оригинал → русский перевод». Из него собирается `django.mo`.

Кнопка отвечает только за пункт 1:

```
нажали RU/EN
   │  POST /i18n/setlang/   language=ru   next=/catalog/
   ▼
вьюха set_language (встроена в Django)
   │  Set-Cookie: django_language=ru
   │  302 → /catalog/
   ▼
GET /catalog/  →  LocaleMiddleware видит cookie  →  activate('ru')
   ▼
{% translate "Shop all" %}  →  «Все товары»   (из django.mo)
```

Почему кнопка устроена именно так:

- **Это обычная форма без `hx-post`.** Шапка и подвал лежат вне `#main-content`.
  Если сменить язык через HTMX, они останутся на старом языке. Нужна полная перезагрузка.
- **В форме есть `{% csrf_token %}`.** `set_language` принимает только POST, а POST в Django без токена
  получает 403.
- **`next` подставляет JS.** Шапка рендерится один раз, а дальше страницы меняет HTMX
  (`hx-get` + `hx-push-url`). Без JS `next` указывал бы на первую открытую страницу.
- **JS чистит `htmx-history-cache`.** HTMX хранит копии страниц для кнопки «Назад».
  После смены языка они устарели. Без кэша HTMX перезагрузит страницу сам
  (`refreshOnHistoryMiss` у вас уже включён в `base.html`).
- **Чужой адрес в `next` Django отбрасывает** и ведёт на `/`, так что редирект на чужой сайт невозможен.

---

## Что уже сделано (шаги 1–7)

1. **`enf/enf/settings.py`**: добавлена `LocaleMiddleware` (после Session, до Common).
   Заданы `LANGUAGE_CODE = 'ru'`, `LANGUAGES` (ru, en), `LOCALE_PATHS = [BASE_DIR / 'locale']`
   и `LANGUAGE_COOKIE_AGE` (выбор помнится год).
2. **`enf/enf/urls.py`**: добавлен `path('i18n/', include('django.conf.urls.i18n'))`, это встроенная вьюха `set_language`.
3. **`enf/main/templates/main/base.html`**: `<html lang="{{ LANGUAGE_CODE }}">` вместо `lang="en"`,
   подключены `lang_switch.css` и `lang_switch.js`.
4. **`header.html`**: кнопка стоит первой в `header__actions` (видна с 960px).
   **`mobile_menu.html`**: кнопка в `menu__secondary` перед корзиной.
5. **Тексты размечены**:
   - все шаблоны: `{% translate %}`, `{% blocktranslate %}`, подписи полей через `label=_("...")`;
   - формы (`users/forms.py`, `orders/forms.py`) — через `gettext_lazy`;
   - вьюхи (`cart/views.py`, `orders/views.py`) — через `gettext`, f-строки заменены на `%(name)s`;
   - статусы заказа (`orders/models.py`), их видно в истории заказов;
   - 5 строк в `app.js` — через `JavaScriptCatalog` (`/jsi18n/` в `urls.py` и `<script>` в `base.html`).
6. **gettext на этой машине не установлен**, поэтому `.po` и `.mo` собраны отдельным скриптом.
   Строки он извлекал тем же `templatize`, что и `makemessages`. Файлы стандартные: после установки
   gettext команды `makemessages` и `compilemessages` будут работать с ними как обычно.
7. **Переводы лежат в `enf/locale/ru/LC_MESSAGES/`**. Одно английское слово с разным смыслом
   разведено контекстом: `{% translate "Checkout" context "button" %}` → «Оформить заказ»,
   а заголовок страницы `{% translate "Checkout" %}` → «Оформление заказа».

Что получилось:
- весь интерфейс переключается: шапка, каталог, фильтры, товар, корзина, оформление, оплата, вход, профиль;
- переводятся и встроенные тексты Django: админка, ошибки форм, сообщения валидаторов паролей;
- даты и цены с `floatformat:"2g"` на русском выводятся в русском формате: `1 200,00` вместо `1,200.00`;
- английская версия не изменилась: все 32 проверенные страницы совпали со старыми шаблонами.

## Как переводить новые тексты (шаги 5–7)

Для всех текущих текстов это уже сделано. Когда добавите новый текст, повторите шаги ниже.

### Шаг 5. Пометить строки для перевода

**Шаблоны.** В начале каждого файла с текстом нужен `{% load i18n %}`. Он не наследуется
ни через `include`, ни через `extends`.

```django
{% load i18n %}

<a class="nav__link" ...>{% translate "Shop all" %}</a>
<a class="header__link" ...>{% translate "Log in" %}</a>
<button ...>{% translate "Cart" %} (<span data-cart-count>{{ cart_total_items }}</span>)</button>

{# в атрибутах #}
<input type="search" placeholder="{% translate 'Search' %}" aria-label="{% translate 'Search products' %}">

{# текст с переменной #}
{% blocktranslate with name=product.name %}{{ name }} added to cart{% endblocktranslate %}

{# числа: в русском три формы — «1 товар», «2 товара», «5 товаров» #}
{% blocktranslate count counter=cart_total_items %}{{ counter }} item{% plural %}{{ counter }} items{% endblocktranslate %}
```

**Python.** Во views используйте `gettext`, в `forms.py` и `models.py` — `gettext_lazy`.
Атрибуты классов вычисляются один раз при запуске сервера, когда языка ещё нет.
Ленивая версия переводит строку позже, в момент вывода.

```python
from django.utils.translation import gettext as _         # views.py
from django.utils.translation import gettext_lazy as _    # forms.py, models.py

# orders/forms.py
'placeholder': _('First Name'),

# cart/views.py: f-строка НЕ переведётся. makemessages её не видит,
# а готовая строка «Only 3 items available» не совпадёт ни с одним msgid
'error': f"Only {cart_item.product_size.stock} items available"           # так нельзя
'error': _('Only %(count)s items available') % {'count': cart_item.product_size.stock}   # так можно
```

**JavaScript.** Уже подключён `JavaScriptCatalog`, так что в `app.js` достаточно писать
`gettext('Текст')` или `interpolate(gettext('Only %(count)s left'), { count: n }, true)`. Как это подключено:

```python
# urls.py
from django.views.i18n import JavaScriptCatalog
path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
```

```django
<script src="{% url 'javascript-catalog' %}" defer></script>   {# перед app.js #}
```

Строки из JS собираются отдельной командой `makemessages -d djangojs` (см. шаг 7).

### Шаг 6. Установить gettext (один раз, только на Windows)

`makemessages` и `compilemessages` вызывают утилиты GNU gettext, а в Windows их нет.
Скачайте установщик с https://mlocati.github.io/articles/gettext-iconv-windows.html
(на этот сайт ссылается документация Django) и установите. Потом перезапустите терминал
и PyCharm и проверьте:

```bash
xgettext --version
```

### Шаг 7. Обновить и скомпилировать перевод

Команды запускаются из папки `enf` (там, где `manage.py`) с активированным venv:

```bash
python manage.py makemessages -l ru --ignore=venv
```

```bash
python manage.py makemessages -d djangojs -l ru --ignore=venv
```

`--ignore=venv` обязателен: venv лежит внутри `enf`, и без флага Django пройдётся
по всем библиотекам, включая сам Django.

Команды допишут новые строки в `enf/locale/ru/LC_MESSAGES/django.po` и `djangojs.po`,
готовые переводы сохранятся. Впишите переводы в пустые `msgstr`.
Для строк с числом Django копирует русские правила из своего каталога, и форм там
четыре: `[0]` — 1, 21, 31…; `[1]` — 2–4, 22–24…; `[2]` — 5–20, 25–30…; `[3]` — дробные.
Заполнять нужно все четыре.

```po
#: main/templates/main/includes/header.html:17
msgid "Shop all"
msgstr "Все товары"

#: main/templates/main/includes/header.html:31
msgid "Log in"
msgstr "Войти"

msgid "%(counter)s item"
msgid_plural "%(counter)s items"
msgstr[0] "%(counter)s товар"
msgstr[1] "%(counter)s товара"
msgstr[2] "%(counter)s товаров"
msgstr[3] "%(counter)s товара"
```

Соберите `.mo` (Django читает именно его):

```bash
python manage.py compilemessages --ignore=venv
```

Для английского отдельный файл не нужен: в шаблонах уже английский текст, он и есть оригинал (`msgid`).
Django читает только `.mo`. Поэтому после любой правки `.po` нужен `compilemessages`,
а для него — установленный gettext (шаг 6).

## Что осталось

### Шаг 8. Тексты из базы данных

`{% translate %}` переводит только тексты, которые заранее записаны в коде. Названия категорий,
товаров и описания (`Category.name`, `Product.name`, `Product.description`) лежат в базе,
поэтому для них нужны отдельные поля:

```python
from django.utils.translation import get_language


class Category(models.Model):
    name = models.CharField(max_length=100)                   # английское, как сейчас
    name_ru = models.CharField(max_length=100, blank=True)    # русское

    @property
    def title(self):
        if get_language() == 'ru' and self.name_ru:
            return self.name_ru
        return self.name
```

В шаблонах пишите `{{ category.title }}` вместо `{{ category.name }}`. Потом выполните
`makemigrations` и `migrate` и заполните русские названия в админке. То же самое делает
библиотека `django-modeltranslation`, но перед установкой проверьте, что она поддерживает Django 6.

---

## Как проверить

1. Запустите сервер и нажмите RU/EN. Страница должна перезагрузиться на другом языке.
2. Откройте F12 → Application → Cookies: там должна быть cookie `django_language` = `ru` или `en`.
3. Перейдите через меню в каталог (это HTMX-переход) и нажмите кнопку. Вы должны остаться в каталоге.
4. Нажмите «Назад». Предыдущие страницы тоже должны открыться на новом языке.
5. Сузьте окно до размера телефона. Русские тексты на 20–30% длиннее английских,
   поэтому проверьте, что шапка не разъехалась.

## Частые ошибки

| Симптом | Причина |
|---|---|
| Нажимаю кнопку, язык не меняется | Нет `LocaleMiddleware`, или она стоит не на своём месте (нужно после Session и до Common) |
| `NoReverseMatch ... 'set_language'` | Не добавлен `path('i18n/', include('django.conf.urls.i18n'))` |
| `Invalid block tag ... 'translate'` | В этом шаблоне нет `{% load i18n %}` |
| 403 CSRF при нажатии | Из формы пропал `{% csrf_token %}` |
| В `.po` перевод есть, а на сайте нет | Не выполнен `compilemessages`; строка помечена `#, fuzzy` (удалите эту пометку); перезапустите `runserver` |
| `makemessages` долго работает, `.po` огромный | Забыли `--ignore=venv` |
| `Can't find xgettext` / `Can't find msgfmt` | Не установлен gettext (шаг 6) |
| Строка с переменной не переводится | Используется f-строка, нужна подстановка `%(name)s` (шаг 5) |

## Другой вариант: язык в адресе (`/ru/...`, `/en/...`)

У Django есть `i18n_patterns`: язык записывается прямо в URL. Это лучше для поисковиков,
потому что обе версии индексируются отдельно. Но это меняет все адреса, а адреса Stripe
(webhook, success, cancel) придётся вынести из-под префикса. Для диплома проще вариант с cookie,
как сделано здесь. Кнопка от этого почти не меняется: `set_language` сам переведёт `next` на новый префикс.
