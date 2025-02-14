from rest_framework import serializers
from .models import Wallet, Transaction
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id',)

class WalletSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    balance = serializers.DecimalField(max_digits=18, decimal_places=8, read_only=True)
    
    class Meta:
        model = Wallet
        fields = ('address', 'balance', 'user', 'created_at')
        read_only_fields = ('address', 'balance', 'created_at')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Get balance from the wallet method
        try:
            data['balance'] = instance.get_balance()
        except Exception as e:
            data['balance'] = 0
        return data

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('to_address', 'amount', 'status', 'tx_hash', 'timestamp')
        read_only_fields = ('status', 'tx_hash', 'timestamp')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
