from unittest.mock import Mock
from services import library_service
from services.payment_service import PaymentGateway

def test_refund_success_calls_gateway_with_correct_args():
    gateway = Mock(spec=PaymentGateway)
    # assume refund returns (success, message)
    gateway.refund_payment.return_value = (True, "Refunded")

    ok, msg = library_service.refund_late_fee_payment("txn_abc", 4.00, gateway)

    assert ok is True
    assert "refund" in msg.lower() or "success" in msg.lower()
    gateway.refund_payment.assert_called_once()
    gateway.refund_payment.assert_called_with("txn_abc", 4.00)


def test_refund_invalid_transaction_id_skips_gateway():
    gateway = Mock(spec=PaymentGateway)

    ok, msg = library_service.refund_late_fee_payment("", 5.00, gateway)

    assert ok is False
    gateway.refund_payment.assert_not_called()


def test_refund_invalid_amount_zero_skips_gateway():
    gateway = Mock(spec=PaymentGateway)

    ok, msg = library_service.refund_late_fee_payment("txn_abc", 0.00, gateway)

    assert ok is False
    gateway.refund_payment.assert_not_called()


def test_refund_invalid_amount_negative_skips_gateway():
    gateway = Mock(spec=PaymentGateway)

    ok, msg = library_service.refund_late_fee_payment("txn_abc", -1.00, gateway)

    assert ok is False
    gateway.refund_payment.assert_not_called()


def test_refund_invalid_amount_exceeds_cap_skips_gateway():
    # Assumes refund cannot exceed $15.00.
    gateway = Mock(spec=PaymentGateway)

    ok, msg = library_service.refund_late_fee_payment("txn_abc", 15.01, gateway)

    assert ok is False
    gateway.refund_payment.assert_not_called()