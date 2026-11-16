const STATUS_LABELS = {
  payment_pending: 'Payment pending',
  pending: 'Waiting for professional',
  accepted: 'Professional assigned',
  partially_assigned: 'Partially assigned',
  assigned: 'All professionals assigned',
  partially_completed: 'Partially completed',
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
