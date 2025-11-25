from django.db import models

class Product(models.Model):
    barcode = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    on_pack = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    off_price = models.DecimalField(max_digits=10, decimal_places=2)
    flag = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} ({self.barcode})"


class PriceRecord(models.Model):
    barcode = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.barcode} - {self.price}"

class PriceChangeLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_logs")
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} | {self.old_price} → {self.new_price}"