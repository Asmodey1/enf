from django.db import models
from django.utils.text import slugify


def unique_slug(instance, value):
    """Уникальный slug для категории или товара.

    slugify() выбрасывает кириллицу: для «Куртки» получилась бы пустая строка, и ссылка на
    категорию перестала бы строиться. Поэтому подставляем запасное имя и номер при совпадении.
    """
    base = (slugify(value) or instance._meta.model_name)[:90]
    slug, number = base, 2
    while type(instance).objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f'{base}-{number}'
        number += 1
    return slug


class Category(models.Model):
    name = models.CharField(max_length=100)
    # SlugField пропускает только латиницу, цифры, «-» и «_»: со slug вроде «кожаные куртки»
    # не строилась ссылка на категорию, и падали все страницы с меню
    slug = models.SlugField(max_length=100, unique=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20)


    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE,
                                related_name='product_sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)


    class Meta:
        # Один размер у товара — одна строка с остатком, иначе на странице товара размер был бы дважды
        constraints = [
            models.UniqueConstraint(fields=['product', 'size'], name='unique_product_size'),
        ]


    def __str__(self):
        return f"{self.size.name} ({self.stock} in stock) for {self.product.name}"


class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='products')
    color = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='media/products/main/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='images')
    image = models.ImageField(upload_to='media/products/extra/')
