from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
from decimal import Decimal

from .models import Product, PriceRecord, PriceChangeLog
from .serializers import PriceRecordUploadSerializer

class PriceRecordUploadAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PriceRecordUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            return Response({"error": f"Invalid XLSX file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if df.shape[1] != 2:
            return Response({"error": "The file must have exactly 2 columns: barcode and price."},
                            status=status.HTTP_400_BAD_REQUEST)

        df.columns = ['barcode', 'price']

        empty_rows = df[df['barcode'].isna() | df['price'].isna()]
        if not empty_rows.empty:
            return Response({"error": f"Empty cells found in rows: {list(empty_rows.index + 1)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        errors = []
        price_records_to_create = []
        price_records_to_update = []

        existing_records = {pr.barcode: pr for pr in PriceRecord.objects.all()}

        for idx, row in df.iterrows():
            barcode = str(row['barcode']).strip()
            try:
                price = float(row['price'])
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Price '{row['price']}' is not a valid number.")
                continue

            if barcode in existing_records:
                existing_records[barcode].price = price
                price_records_to_update.append(existing_records[barcode])
            else:
                price_records_to_create.append(
                    PriceRecord(barcode=barcode, price=price)
                )

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if price_records_to_update:
            PriceRecord.objects.bulk_update(price_records_to_update, ['price'])
        if price_records_to_create:
            PriceRecord.objects.bulk_create(price_records_to_create)

        sync_price_records()

        return Response(
            {
                "message": f"{len(price_records_to_create) + len(price_records_to_update)} PriceRecord items uploaded and product prices updated successfully."},
            status=status.HTTP_201_CREATED
        )

def sync_price_records():
    products_qs = Product.objects.all()
    products_dict = {p.barcode: p for p in products_qs}

    price_records = PriceRecord.objects.all()

    logs_to_create = []
    products_to_update = []

    for pr in price_records:
        barcode = pr.barcode
        price = Decimal(str(pr.price))
        product = products_dict.get(barcode)

        if not product:
            print(f"[NO MATCH] No product found for barcode: {barcode}. Ignoring.")
            continue

        if price < product.sale_price:
            print(
                f"[PRICE TOO LOW] {product.product_name} ({barcode}) | "
                f"PriceRecord: {price} | Product sale_price: {product.sale_price} → Cannot reduce."
            )
            continue
        elif price == product.sale_price:
            print(f"[NO CHANGE] {product.product_name} ({barcode}) | Price unchanged at {price}.")
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