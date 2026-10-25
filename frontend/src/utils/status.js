const STATUS_LABELS = {
  payment_pending: 'Payment pending',
  pending: 'Waiting for professional',
  accepted: 'Professional assigned',
  completed: 'Service completed',
  cancelled: 'Cancelled',
  available: 'Available',
  approved: 'Approved',
  blocked: 'Blocked',
}

export function statusLabel(status) {
  if (!status) return 'Unknown'
  return STATUS_LABELS[status] || status.replaceAll('_', ' ')
}
