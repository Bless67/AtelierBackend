from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import *
from api.serializers import *


class ProductListView(APIView):
    def get(self, request):
        product = Product.objects.all()
        product_serializer = ProductSerializer(product, many=True)
        return Response(product_serializer.data, status=status.HTTP_200_OK)


class ProductView(APIView):
    def post(self, request, pk):
        name = request.data.get('name')
        description = request.data.get('description')
