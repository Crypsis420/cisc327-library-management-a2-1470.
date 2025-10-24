"""
Payment Service Module - External Payment Gateway Integration
This module simulates integration with an external payment processing API.

For Assignment 3: You will learn to mock this service in their tests
since we cannot make actual payment API calls during testing.
"""

import requests
from typing import Dict, Tuple
import time


class PaymentGateway:
    """
    Simulates an external payment gateway API.
    In production, this would connect to services like Stripe, PayPal, etc.
    
    For testing purposes, you should MOCK this class to avoid:
    - Making actual API calls
    - Depending on external service availability
    - Incurring costs or rate limits
    """
    
    def __init__(self, api_key: str = "test_key_12345"):
        """
        Initialize payment gateway with API credentials.
        
        Args:
            api_key: API key for authentication (default is test key)
        """
        self.api_key = api_key
        self.base_url = "https://api.payment-gateway.example.com"
    
    def process_payment(self, patron_id: str, amount: float, description: str = "") -> Tuple[bool, str, str]:
        """
        Process a payment through the external gateway.
        
        WARNING: This makes an actual HTTP request to external service.
        You should MOCK this method in tests!
        
        Args:
            patron_id: 6-digit patron/customer ID
            amount: Payment amount in dollars
            description: Payment description
            
        Returns:
            tuple: (success: bool, transaction_id: str, message: str)
            
        Example:
            gateway = PaymentGateway()
            success, txn_id, msg = gateway.process_payment("123456", 10.50, "Late fees")
        """
        # Simulate API call delay
        time.sleep(0.5)
        
        # In a real implementation, this would make an HTTP request:
        # response = requests.post(
        #     f"{self.base_url}/charges",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     json={
        #         "customer_id": patron_id,
        #         "amount": amount,
        #         "currency": "usd",
        #         "description": description
        #     }
        # )
        
        # For this template, we simulate different scenarios based on amount
        # This allows testing without a real API
        
        if amount <= 0:
            return False, "", "Invalid amount: must be greater than 0"
        
        if amount > 1000:
            return False, "", "Payment declined: amount exceeds limit"
        
        if len(patron_id) != 6:
            return False, "", "Invalid patron ID format"
        
        # Simulate successful payment
        transaction_id = f"txn_{patron_id}_{int(time.time())}"
        return True, transaction_id, f"Payment of ${amount:.2f} processed successfully"
    
    def refund_payment(self, transaction_id: str, amount: float) -> Tuple[bool, str]:
        """
        Refund a previous payment.
        
        WARNING: This makes an actual HTTP request to external service.
        You should MOCK this method in tests!
        
        Args:
            transaction_id: Original transaction ID to refund
            amount: Amount to refund
            
        Returns:
            tuple: (success: bool, message: str)
        """
        time.sleep(0.5)
        
        if not transaction_id or not transaction_id.startswith("txn_"):
            return False, "Invalid transaction ID"
        
        if amount <= 0:
            return False, "Invalid refund amount"
        
        refund_id = f"refund_{transaction_id}_{int(time.time())}"
        return True, f"Refund of ${amount:.2f} processed successfully. Refund ID: {refund_id}"
    
    def verify_payment_status(self, transaction_id: str) -> Dict:
        """
        Check the status of a payment transaction.
        
        WARNING: This makes an actual HTTP request to external service.
        You should MOCK this method in tests!
        
        Args:
            transaction_id: Transaction ID to check
            
        Returns:
            dict: Payment status information
        """
        time.sleep(0.3)
        
        if not transaction_id or not transaction_id.startswith("txn_"):
            return {"status": "not_found", "message": "Transaction not found"}
        
        # Simulate status check
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": 10.50,
            "timestamp": time.time()
        }