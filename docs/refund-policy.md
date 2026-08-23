# Refund Policy

## Purpose

This policy defines when a standalone refund may be issued.

A standalone refund is different from an order cancellation. Cancellation is used to stop fulfilment before shipment and includes any required payment reversal. A standalone refund is used when cancellation is no longer the appropriate action.

## Supported Refund Scenarios

A standalone refund may be considered only in the following scenarios:

1. The shipment is confirmed as `lost`.
2. A delivered item is reported as damaged.

A customer asking for a refund does not by itself make the order eligible.

A normally delivered order is not refundable under a general return-window policy in the scope of this project.

## Lost Shipments

A shipment is eligible for refund consideration only when trusted shipment data reports its status as `lost`.

A shipment that is merely late or past its estimated delivery date must not be treated as lost.

A shipment that is still `in_transit` is not automatically eligible for a refund.

A confirmed lost shipment may be refunded up to the remaining refundable amount for the order.

If the refund amount is greater than $100, human approval is required.

If the refund amount is $100 or less, the refund may proceed without human approval after normal business validation succeeds.

## Damaged Items

A damaged-item refund may be considered only when the order or shipment has been delivered and the customer reports that the item arrived damaged.

All damaged-item refunds require human approval, regardless of refund amount.

A damaged-item refund must not be issued if the required human approval is rejected or missing.

For the current scope, the customer's report is sufficient to raise a damaged-item claim. Photo evidence, warehouse inspection, and fraud assessment are outside this policy.

## Refund Amount

A refund must not exceed the remaining refundable amount for the order.

The refundable amount must be calculated before a refund is issued.

## Duplicate Refund Protection

A refund must never be issued twice for the same approved resolution.

Repeated or retried refund requests must not create duplicate refunds.

## Relationship to Cancellation

If an order has not shipped and is eligible for cancellation, the support agent should propose `cancel`, not `refund`.

Any payment that must be returned because of cancellation is handled by the cancellation operation itself.

## Examples

- A shipment marked `lost` with an $80 refundable amount may be refunded without human approval.
- A shipment marked `lost` with a $150 refundable amount requires human approval.
- A delivered damaged item with a $40 refundable amount requires human approval.
- A delivered damaged item with a $150 refundable amount requires human approval.
- A paid order that has not shipped should be cancelled rather than refunded directly.
- A shipment that is late but still `in_transit` is not automatically refundable.
- A normally delivered, non-damaged order is not refundable under this project's policy.
