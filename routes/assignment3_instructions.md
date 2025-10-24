# Assignment 3 - Mocking, Stubbing, and Code Coverage Testing

**Course:** CISC/CMPE-327 - Software Quality Assurance | **Total Marks:** 100 | **Due Date:** November 09, 2025

---

## 1. Assignment Overview

This assignment focuses on advanced testing techniques: stubbing and mocking for external dependencies, and aims to achieve at least 80%+ code coverage. 

To support this objective, you need to restructured the project into a modular architecture with a new `services/` folder. Move your `library_service.py` into the `services` folder. Next, from [`library_service.py`](https://github.com/anwardr/CISC327-CMPE327-F25/blob/feature/assignment3/services/library_service.py) (business logic) copy the two functions `pay_late_fees` and `refund_late_fee_payment` into your your `library_services.py`. Furthermore, copy the [`payment_service.py`](https://github.com/anwardr/CISC327-CMPE327-F25/blob/feature/assignment3/services/payment_service.py) (newly created, simulated external payment gateway) into the `services` folder. Please make sure to update the imports accordingly.

In the first part of this assignment, you will test two payment gateway functions that have been newly added to `library_service.py`: `pay_late_fees()` and `refund_late_fee_payment()`. These functions process library late fees and depend on the simulated `PaymentGateway` class in `payment_service.py`, which mimics a real external payment API (like Stripe or PayPal). Since you cannot call real payment services during testing, you must use mocking and stubbing techniques to test these functions in isolation. 

The second part of this assignment focuses on measuring and achieving at least 80% code coverage for your tests. The following provides further detail of this two tasks.

---

## 2. Tasks

### Task 2.1: Stubbing and Mocking

Write comprehensive unit tests for `pay_late_fees(patron_id, book_id, payment_gateway)` and `refund_late_fee_payment(transaction_id, amount, payment_gateway)` using both stubbing and mocking techniques ([Mocks vs Stubs explained](https://www.geeksforgeeks.org/software-testing/stubs-vs-mocks/)).

**Stubbing Requirements:** Use `mocker.patch()` to stub database functions `calculate_late_fee_for_book()` and `get_book_by_id()` with fake data. These stubs provide test data without verification since we only need their return values ([pytest-mock documentation](https://pytest-mock.readthedocs.io/)).

**Mocking Requirements:** Use `Mock(spec=PaymentGateway)` to mock the payment gateway's `process_payment()` and `refund_payment()` methods. Unlike stubs, mocks must be verified using `assert_called_once()`, `assert_called_with()`, and `assert_not_called()` to ensure correct parameters are passed ([unittest.mock docs](https://docs.python.org/3/library/unittest.mock.html) | [Real Python guide](https://realpython.com/python-mock-library/)).

**Required Test Scenarios:**

For `pay_late_fees()`: Test successful payment, payment declined by gateway, invalid patron ID (verify mock NOT called), zero late fees (verify mock NOT called), and network error exception handling.

For `refund_late_fee_payment()`: Test successful refund, invalid transaction ID rejection, and invalid refund amounts (negative, zero, exceeds $15 maximum).

### Task 2.2: Code Coverage Testing

Achieve 80%+ code coverage for the entire project using statement and branch coverage. Statement coverage measures executable lines run during tests. Branch coverage measures decision points (if/else, try/except) where both outcomes are tested.

You may use either `pytest-cov` or the `coverage` package to measure coverage. Run one of the following commands to generate coverage reports:

```bash
# Option 1: Using pytest-cov (recommended)
pytest --cov=services --cov-report=html --cov-report=term tests/

# Option 2: Using coverage package
coverage run -m pytest tests/
coverage report
coverage html
```

Use the HTML report (`htmlcov/index.html`) to identify uncovered lines (red) and partial branches (yellow). Iteratively write tests targeting uncovered code until reaching 80%+ overall project coverage. Focus on the `services/` folder and core business logic. Document any legitimately _uncovered_ files/lines with clear justification.

---

## 3. What to Submit

### Code Files
Push your code to your GitHub repository. Your repository must include the `tests/` directory containing `test_payment_mock_stub.py` with all your stub/mock tests. Files must run successfully with `pytest tests/`.

### Report: `A3_LastName_Last4Digit_StudentID.pdf`

This file should include the following sections:


**Section 1 - Student Information:** Name, student ID, submission date.

**Section 2 - Stubbing vs Mocking Explanation (200-300 words):** Define stubbing (fake implementations returning hard-coded values) and mocking (test doubles that verify interactions). Explain your strategy: which functions you stubbed, which you mocked, and why.

**Section 3 - Test Execution Instructions:** Provide complete commands for environment setup, running tests, generating coverage reports, and viewing results. All commands must be copy-paste ready.

**Section 4 - Test Cases Summary for the New Tests:** Create a table with columns: Test Function Name, Purpose, Stubs Used, Mocks Used, Verification Done. List all your test cases.

**Section 5 - Coverage Analysis:** Include initial and final coverage screenshots (try your best to show 80%+). Explain which code paths were initially uncovered, what tests you added to improve coverage, and any remaining uncovered lines. Report both statement and branch coverage percentages.

**Section 6 - Challenges and Solutions:** Describe problems encountered (mock setup issues, coverage difficulties, etc.) and how you solved them. Reflect on what you learned about mocking/stubbing.

**Section 7 - Screenshots:** Include (1) all tests passing (both positive and negative), (2) coverage terminal output.

---

## 4. Mark Distribution

| Criteria | Component | Marks | Details |
|----------|-----------|-------|---------|
| **Stubbing and Mocking (30 marks)** | Stubbing | 10 | Database functions properly stubbed with realistic test data |
| | Mocking | 10 | Payment gateway mocked correctly for all scenarios |
| | Mock Verification | 10 | Proper use of assert_called_once(), assert_not_called(), assert_called_with() |
| **Code Coverage Testing (50 marks)** | Coverage (80%+) | 30 | Statement and branch coverage ≥80% with screenshots |
| | Coverage Analysis | 20 | Thoughtful analysis of initial/final coverage and improvement strategy |
| **Report Quality (20 marks)** | Report Quality | 20 | Complete instructions, clear test documentation, professional presentation |
| | **Total** | **100** | |

---
## 6. Important Guidelines

**Never mock the functions you're testing** - only mock dependencies. Mocking `pay_late_fees()` while testing it provides no value. **Never modify `payment_service.py`** - treat it as an external library you cannot change. **Never make real database calls** - use stubs to return test data instead.

**Always stub database functions** when you only need return values. **Always mock the payment gateway** because you must verify correct parameters. **Always use descriptive test names**.

---

## 7. Submission

**Step 1 - Push to GitHub:** Push the entire project including the `tests/` directory to your GitHub repository. Ensure your repository is up to date with all commits.

**Step 2 - Submit to OnQ:** Submit via OnQ: (1) GitHub repository link, (2) PDF report named `A3_LastName_Last4Digit_StudentID.pdf` with embedded screenshots.