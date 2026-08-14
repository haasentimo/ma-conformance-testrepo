"""Reminders for the invoices that have not been paid.

The dunning run walks the open items once a week. It reads what has actually
arrived rather than what the invoice says, because a payment that landed on the
clearing account is money the depot has — sending a reminder for it is how a
depot loses a business customer.
"""

import depot.core.ports
import depot.billing.repository.invoice_query

FIRST_REMINDER_TEMPLATE: str = "invoice.reminder.first"
SECOND_REMINDER_TEMPLATE: str = "invoice.reminder.second"
FINAL_NOTICE_TEMPLATE: str = "invoice.notice.final"

REMINDER_TEMPLATES: tuple[str, ...] = (
    FIRST_REMINDER_TEMPLATE,
    SECOND_REMINDER_TEMPLATE,
    FINAL_NOTICE_TEMPLATE,
)
QUIET_PERIOD_SECONDS: float = 7 * 86400.0


class DunningService:
    """Decides which open items get a reminder, and which one."""

    def __init__(
        self,
        payments: depot.billing.repository.invoice_query.InvoiceQuery,
        notifier: depot.core.ports.NotificationSender,
    ) -> None:
        self.payments: depot.billing.repository.invoice_query.InvoiceQuery = payments
        self.notifier: depot.core.ports.NotificationSender = notifier

    def template_for(self, reminders_sent: int) -> str:
        """Report which letter goes out after that many reminders."""
        if reminders_sent >= len(REMINDER_TEMPLATES):
            return FINAL_NOTICE_TEMPLATE
        return REMINDER_TEMPLATES[reminders_sent]

    def is_quiet(self, invoice_number: str, now_epoch: float) -> bool:
        """Report whether money arrived recently enough to hold the reminder."""
        last = self.payments.last_payment_at(invoice_number)
        return last is not None and now_epoch - last < QUIET_PERIOD_SECONDS

    def should_remind(
        self, invoice_number: str, gross_cents: int, now_epoch: float
    ) -> bool:
        """Report whether an open item earns a reminder today."""
        if self.is_quiet(invoice_number, now_epoch):
            return False
        return self.payments.settled_cents(invoice_number) < gross_cents

    def remind(
        self,
        invoice_number: str,
        recipient: str,
        gross_cents: int,
        reminders_sent: int,
        now_epoch: float,
    ) -> bool:
        """Send the reminder that is due and report whether one went out."""
        if not self.should_remind(invoice_number, gross_cents, now_epoch):
            return False
        open_cents = gross_cents - self.payments.settled_cents(invoice_number)
        return self.notifier.send(
            recipient,
            self.template_for(reminders_sent),
            {"number": invoice_number, "open": str(open_cents)},
        )

    def unmatched_cents(self) -> int:
        """Report how much money the bookkeeping still has to assign by hand."""
        return self.payments.unmatched_cents()
