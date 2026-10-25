export function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

export function tokenIsExpired(token) {
  if (!token) return true
  try {
    const encodedPayload = token.split('.')[1]
    const normalizedPayload = encodedPayload.replace(/-/g, '+').replace(/_/g, '/')
    const paddedPayload = normalizedPayload.padEnd(Math.ceil(normalizedPayload.length / 4) * 4, '=')
    const payload = JSON.parse(atob(paddedPayload))
    return typeof payload.exp !== 'number' || payload.exp * 1000 <= Date.now()
  } catch {
    return true
  }
}

export async function redirectExpiredSession(router) {
  clearSession()
  await router.replace({ name: 'login', query: { expired: '1' } })
}
