from django.db import models
from django.contrib.auth.models import User
from bit import Key
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from bit import Key
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from bit import Key, PrivateKeyTestnet
from django.conf import settings
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from bit import Key, PrivateKeyTestnet
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_testnet = models.BooleanField(default=True)
    
    @classmethod
    def generate_wallet(cls, user):
        """Generate a new Bitcoin testnet wallet"""
        try:
            # Use Key for mainnet instead of PrivateKeyTestnet
            key = Key() if not settings.BITCOIN_TESTNET else PrivateKeyTestnet()
            
            wallet = cls.objects.create(
                user=user,
                address=key.address,
                private_key=key.to_wif(),
                is_testnet=settings.BITCOIN_TESTNET
            )
            return wallet
        except Exception as e:
            print(f"Error generating wallet: {str(e)}")
            raise

    def get_balance(self):
        """Get wallet balance in BTC with proper decimal handling"""
        try:
            key = PrivateKeyTestnet(self.private_key)
            balance = key.get_balance('btc')
            # Convert to proper decimal format
            from decimal import Decimal
            return Decimal(str(balance))
        except Exception as e:
            raise Exception(f"Error fetching balance: {str(e)}")

    def get_transactions(self):
        """Get transaction history"""
        try:
            key = PrivateKeyTestnet(self.private_key)
            return key.get_transactions()
        except Exception as e:
            print(f"Error fetching transactions: {str(e)}")
            return []

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    from_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='sent_transactions')
    to_address = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=18, decimal_places=8)  # Update decimal places
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tx_hash = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.amount} BTC from {self.from_wallet.user.username}"