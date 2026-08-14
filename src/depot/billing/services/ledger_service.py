"""Postings from the invoices into the depot's ledger.

Every raised invoice becomes two entries — receivable against revenue — and
every settlement two more. The booking date is not the moment the software gets
round to it: a posting belongs to the day the business event happened, which is
why the clock is handed in rather than read here.
"""

import depot.core.ports
import depot.billing.repository.invoice_repo

ACCOUNT_RECEIVABLE: str = "1400"
ACCOUNT_REVENUE: str = "8400"
ACCOUNT_VAT: str = "1776"
ACCOUNT_BANK: str = "1200"


class LedgerService:
    """Turns invoices and settlements into ledger entries."""

    def __init__(
        self, invoices: depot.billing.repository.invoice_repo.InvoiceRepository
    ) -> None:
        self.invoices: depot.billing.repository.invoice_repo.InvoiceRepository = (
            invoices
        )
        self._entries: list[str] = []

    def post_invoice(self, number: str, clock: depot.core.ports.Clock) -> str:
        """Post a raised invoice and return the booking day it went on."""
        invoice = self.invoices.get(number)
        if invoice is None:
            return ""
        day = clock.today_iso()
        self.record(day, ACCOUNT_RECEIVABLE, ACCOUNT_REVENUE, invoice.net_cents)
        self.record(day, ACCOUNT_RECEIVABLE, ACCOUNT_VAT, invoice.vat_cents())
        return day

    def post_settlement(self, number: str, amount_cents: int, day: str) -> str:
        """Post an incoming payment and return the booking day it went on.

        A settlement is booked on the value date the bank statement carries,
        not on the day the batch happens to be read: money that arrived on a
        Friday belongs in that week even if the run only sees it on Monday.
        """
        if amount_cents <= 0 or not day or self.invoices.get(number) is None:
            return ""
        self.record(day, ACCOUNT_BANK, ACCOUNT_RECEIVABLE, amount_cents)
        return day

    def record(self, day: str, debit: str, credit: str, amount_cents: int) -> None:
        """Write one entry into the journal, skipping empty amounts."""
        if amount_cents == 0:
            return
        self._entries.append(f"{day} {debit} {credit} {amount_cents}")

    def journal(self) -> list[str]:
        """List the entries written so far, in the order they were posted."""
        return list(self._entries)

    def balance_cents(self, account: str) -> int:
        """Report the balance of one account across the journal."""
        total = 0
        for entry in self._entries:
            debit, credit, amount = entry.split(" ")[1:]
            if debit == account:
                total += int(amount)
            elif credit == account:
                total -= int(amount)
        return total

    def receivable_cents(self) -> int:
        """Report what the ledger says the depot is owed."""
        return self.balance_cents(ACCOUNT_RECEIVABLE)
