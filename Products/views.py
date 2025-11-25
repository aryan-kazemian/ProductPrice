from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import polars as pl
from .models import Product, PriceRecord, PriceChangeLog
from .serializers import PriceRecordUploadSerializer

from django.db import transaction

class PriceRecordUploadAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PriceRecordUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data['file']

        try:
            df = pl.read_excel(uploaded_file.read())
        except Exception as e:
            return Response({"error": f"Invalid XLSX file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if df.shape[1] != 2:
            return Response(
                {"error": "The file must have exactly 2 columns: barcode and price."},
                status=status.HTTP_400_BAD_REQUEST
            )

        df.columns = ['barcode', 'price']

        empty_rows = df.filter(pl.col("barcode").is_null() | pl.col("price").is_null())
        if empty_rows.height > 0:
            return Response(
                {"error": f"Empty cells found in rows: {empty_rows.height}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        errors = []
        price_records_to_create = []
        price_records_to_update = []

        barcodes = [str(x).strip() for x in df['barcode'].to_list()]
        products = {p.barcode: p for p in Product.objects.filter(barcode__in=barcodes)}

        existing_records = {
            pr.product.barcode: pr
            for pr in PriceRecord.objects.select_related('product').filter(product__barcode__in=barcodes)
            if pr.product
        }

        for idx, row in enumerate(df.rows()):
            barcode = str(row[0]).strip()
            product = products.get(barcode)
            if not product:
                continue

            try:
                price = int(float(row[1]))
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Price '{row[1]}' is not a valid number.")
                continue

            if barcode in existing_records:
                existing_records[barcode].price = price
                price_records_to_update.append(existing_records[barcode])
            else:
                price_records_to_create.append(
                    PriceRecord(product=product, price=price)
                )

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if price_records_to_update:
                PriceRecord.objects.bulk_update(price_records_to_update, ['price'])
            if price_records_to_create:
                PriceRecord.objects.bulk_create(price_records_to_create)

            sync_price_records()

        return Response(
            {
                "message": f"{len(price_records_to_create) + len(price_records_to_update)} "
                           f"PriceRecord items uploaded and product prices updated successfully."
            },
            status=status.HTTP_201_CREATED
        )


def sync_price_records():
    price_records = PriceRecord.objects.select_related('product').all()

    logs_to_create = []
    products_to_update = []

    for pr in price_records:
        product = pr.product
        if not product:
            continue

        price = pr.price

        if price < product.sale_price:
            print(
                f"[PRICE TOO LOW] {product.name} ({product.barcode}) | "
                f"PriceRecord: {price} | Product sale_price: {product.sale_price} → Cannot reduce."
            )
            continue
        elif price == product.sale_price:
            print(f"[NO CHANGE] {product.name} ({product.barcode}) | Price unchanged at {price}.")
            continue

        old_price = product.sale_price
        new_price = price

        if not product.on_pack:
            product.sale_price = new_price
        if product.on_pack:
            product.flag = True

        products_to_update.append(product)

        logs_to_create.append(
            PriceChangeLog(
                product=product,
                old_price=old_price,
                new_price=new_price
            )
        )

    if products_to_update:
        Product.objects.bulk_update(products_to_update, ['sale_price', 'flag', 'updated_at'])

    if logs_to_create:
        PriceChangeLog.objects.bulk_create(logs_to_create)
