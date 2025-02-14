from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, Transaction
from .forms import TransactionForm
from bit import Key
from bit.exceptions import InsufficientFunds
from decimal import Decimal

@login_required
def dashboard(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        try:
            wallet = Wallet.generate_wallet(request.user)
            messages.success(request, "New wallet generated successfully!")
        except Exception as e:
            messages.error(request, f"Error generating wallet: {str(e)}")
            return redirect('dashboard')
    
    try:
        balance = wallet.get_balance()
    except Exception as e:
        balance = 0
        messages.warning(request, str(e))

    # Fetch blockchain transactions
    blockchain_transactions = wallet.get_transactions()
    
    context = {
        'wallet': wallet,
        'balance': f"{balance:.8f}",  # Format to 8 decimal places
        'transactions': blockchain_transactions,
        'network': 'Testnet' if wallet.is_testnet else 'Mainnet'
    }
    return render(request, 'wallet/dashboard.html', context)

# In your Django views.py, add a simple test endpoint


@login_required
def send_transaction(request):
    wallet = Wallet.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                # Create transaction instance
                transaction = form.save(commit=False)
                transaction.from_wallet = wallet
                
                # Initialize the Bitcoin key
                key = Key(wallet.private_key)
                
                # Send the transaction
                tx_hash = key.send([
                    (transaction.to_address, transaction.amount, 'btc')
                ])
                
                # Update transaction status
                transaction.status = 'completed'
                transaction.tx_hash = tx_hash
                transaction.save()
                
                messages.success(request, "Transaction sent successfully!")
                return redirect('dashboard')
                
            except InsufficientFunds:
                messages.error(request, "Insufficient funds for transaction")
            except Exception as e:
                messages.error(request, f"Transaction failed: {str(e)}")
    else:
        form = TransactionForm()
    
    context = {
        'form': form,
        'wallet': wallet,
        'balance': wallet.get_balance()
    }
    return render(request, 'wallet/transaction.html', context)