# wallet/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .permissions import IsWalletOwner
from ..models import Wallet, Transaction
from ..serializers import WalletSerializer, TransactionSerializer
from bit import PrivateKeyTestnet
import logging

logger = logging.getLogger(__name__)

# Custom throttle classes
class TransactionRateThrottle(UserRateThrottle):
    rate = '5/minute'

class BalanceRateThrottle(UserRateThrottle):
    rate = '10/minute'

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]  # Remove IsWalletOwner for creation
    throttle_classes = [UserRateThrottle]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Check if user already has a wallet
        existing_wallet = Wallet.objects.filter(user=request.user).first()
        if existing_wallet:
            return Response(
                {"error": "User already has a wallet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Generate new wallet
            wallet = Wallet.generate_wallet(request.user)
            serializer = self.get_serializer(wallet)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Wallet creation failed: {str(e)}")
            return Response(
                {"error": "Failed to create wallet"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsWalletOwner]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'], throttle_classes=[TransactionRateThrottle])
    def send_transaction(self, request, pk=None):
        wallet = self.get_object()
        serializer = TransactionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Get current balance
                balance = wallet.get_balance()
                amount = serializer.validated_data['amount']
                
                if balance < amount:
                    return Response(
                        {"error": "Insufficient funds"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create and execute transaction
                transaction = Transaction.objects.create(
                    from_wallet=wallet,
                    to_address=serializer.validated_data['to_address'],
                    amount=amount
                )
                
                # Execute the transaction
                key = PrivateKeyTestnet(wallet.private_key)
                tx_hash = key.send([
                    (transaction.to_address, amount, 'btc')
                ])
                
                transaction.tx_hash = tx_hash
                transaction.status = 'completed'
                transaction.save()
                
                return Response(
                    TransactionSerializer(transaction).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"Transaction failed: {str(e)}")
                return Response(
                    {"error": f"Transaction failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # In your Django views.py, add a simple test endpoint
    
    @method_decorator(never_cache)
    @action(detail=True, methods=['get'], throttle_classes=[BalanceRateThrottle])
    def balance(self, request, pk=None):
        wallet = self.get_object()
        try:
            balance = wallet.get_balance()
            return Response({'balance': balance})
        except Exception as e:
            logger.error(f"Balance fetch failed: {str(e)}")
            return Response(
                {"error": f"Could not fetch balance: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], throttle_classes=[BalanceRateThrottle])
    def transactions(self, request, pk=None):
        wallet = self.get_object()
        transactions = Transaction.objects.filter(from_wallet=wallet).order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def test(self, request):

        
        return Response({"status": "API is working"}, status=status.HTTP_200_OK)
