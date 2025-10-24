from unittest.mock import Mock
from services import library_service
from services.payment_service import PaymentGateway

def test_pay_late_fees_success(mocker):
    # stubs
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 10, "title": "Dune", "isbn": "9"*13},
    )
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 6.50, "days_overdue": 10, "status": "Overdue"},
    )

    # mock gateway
    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_123", "Approved")

    ok, msg, txn = library_service.pay_late_fees("123456", 10, gateway)

    assert ok is True
    assert "success" in msg.lower() or "approved" in msg.lower()
    assert txn == "txn_123"

    gateway.process_payment.assert_called_once()
    gateway.process_payment.assert_called_with(
        patron_id="123456", amount=6.50, description="Late fees for 'Dune'"
    )


def test_pay_late_fees_declined(mocker):
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 3, "title": "Gatsby", "isbn": "9"*13},
    )
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 3.00, "days_overdue": 3, "status": "Overdue"},
    )

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (False, None, "card_declined")

    ok, msg, txn = library_service.pay_late_fees("123456", 3, gateway)

    assert ok is False
    assert txn is None
    assert "fail" in msg.lower() or "decline" in msg.lower()

    gateway.process_payment.assert_called_once()
    gateway.process_payment.assert_called_with(
        patron_id="123456", amount=3.00, description="Late fees for 'Gatsby'"
    )


def test_pay_late_fees_invalid_patron_skips_gateway(mocker):
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 7, "title": "Book", "isbn": "9"*13},
    )
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 5.00, "days_overdue": 5, "status": "Overdue"},
    )

    gateway = Mock(spec=PaymentGateway)

    ok, msg, txn = library_service.pay_late_fees("12a456", 7, gateway)

    assert ok is False
    assert txn is None
    gateway.process_payment.assert_not_called()


def test_pay_late_fees_zero_fee_skips_gateway(mocker):
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 12, "title": "Book", "isbn": "9"*13},
    )
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 0.00, "days_overdue": 0, "status": "Not overdue"},
    )

    gateway = Mock(spec=PaymentGateway)

    ok, msg, txn = library_service.pay_late_fees("123456", 12, gateway)

    assert ok is False
    assert txn is None
    gateway.process_payment.assert_not_called()


def test_pay_late_fees_gateway_exception(mocker):
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 5, "title": "Book", "isbn": "9"*13},
    )
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 7.25, "days_overdue": 9, "status": "Overdue"},
    )

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.side_effect = RuntimeError("network timeout")

    ok, msg, txn = library_service.pay_late_fees("123456", 5, gateway)

    assert ok is False
    assert txn is None

    gateway.process_payment.assert_called_once()
    gateway.process_payment.assert_called_with(
        patron_id="123456", amount=7.25, description="Late fees for 'Book'"
    )