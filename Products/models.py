from django.db import models

class Product(models.Model):
    barcode = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    on_pack = models.BooleanField(default=False)
    sale_price = models.IntegerField()
    off_price = models.IntegerField()
    flag = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Product"

    def __str__(self):
        return f"{self.name} ({self.barcode})"


class PriceRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "PriceRecord"

    def __str__(self):
        return f"{self.product.name} - {self.price}"

class PriceChangeLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_logs")
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PriceChangeLog"

    def __str__(self):
        return f"{self.product.product_name} | {self.old_price} → {self.new_price}"