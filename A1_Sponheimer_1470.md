Karim Sponheimer
20301470
Group number: 4

| Function| Status | What is missing | Num Tests | Test Summary |
|---|---|---|---|---|
| `add_book_to_catalog(title, author, isbn, total_copies)` | Partial | Doesnt enforce that the isbn is a digit, only that its 13 char| 6 | Checks valid addition, duplicate isbn, empty title/author, author >100 characters, positive# of copies. |
| `borrow_book_by_patron(patron_id, book_id)` | Partial | Borrow limit should be `>= 5` (max 5).| 4 | Tests invalid patron, correct # available, unavailable book and limit patron to 5 books, this test should fail but passes because of incorrect code. |
| `return_book_by_patron(patron_id, book_id)` | Complete | |4 | tests validates inputs, ensures patron actually borowed book, records return date and availability and computes late fees. |
| `calculate_late_fee_for_book(patron_id, book_id)` | Complete | | 4 | Tests correct late fee is calculated for different time ranges.
| `search_books_in_catalog(search_term, search_type)` | Partial | Error Message when incomplete ISBN doesnt give user correct instructions| 4 | Tets title partial match and author partial match, ISBN exact match and invalid type. 
| `get_patron_status_report(patron_id)` | Partial | doesnt have checkout history.| 
| `get_patron_status_report(patron_id)` | Complete | checkout history added| 2 | Tests invalid patron ID, correct borrow list, fees, and history shown in table. |

Notes: Needed to creat the conftest.py file as I was getting a pytest discovery error in my visual studio code and was looking for a fix.
        Helper functions are created in order to test how actual functions will interact with data from DB that I dont actaully have such as overdue books.
