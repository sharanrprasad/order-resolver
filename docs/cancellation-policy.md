# Cancellation Policy

## Purpose

This policy defines when an order may be cancelled and how payment is handled when a cancellation succeeds.

## When an Order Can Be Cancelled

An order may be cancelled only before shipment has started.

Cancellation is allowed when the order status is:

- `pending`
- `paid`
- `processing`

Cancellation is not allowed when the order status is:

- `shipped`
- `delivered`
- `cancelled`

If shipment information exists, cancellation must also be refused when the shipment status is:

- `shipped`
- `in_transit`
- `delivered`
- `lost`

## Payment Handling

If payment has already been captured, any required refund or payment reversal is handled as part of the cancellation operation.

For an eligible cancellation request, the support agent should propose only `cancel`. It should not propose a separate `refund` for the same order cancellation.

## Repeated Cancellation Requests

An order that is already cancelled must not be cancelled again.

Repeated or retried cancellation requests must not create duplicate payment reversals or refunds.

## Examples

- A `pending` order may be cancelled.
- A `paid` order that has not shipped may be cancelled. Any required payment return is handled by the cancellation operation.
- A `processing` order that has not shipped may be cancelled.
- A `shipped` order cannot be cancelled.
- An `in_transit` shipment cannot be cancelled.
- A `delivered` order cannot be cancelled.
- A shipment marked `lost` cannot be cancelled.
