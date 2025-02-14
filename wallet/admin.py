from django.contrib import admin
from .models import Wallet, Transaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'created_at']
    readonly_fields = ['address', 'private_key', 'created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['from_wallet', 'to_address', 'amount', 'status', 'timestamp']
    readonly_fields = ['tx_hash', 'timestamp']