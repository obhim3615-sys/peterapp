from rest_framework import serializers
from .models import *

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('name','account_num','ifsc')