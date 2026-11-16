let installed = false
let activeRequests = 0

function publishActivity() {
  window.dispatchEvent(new CustomEvent('homeserve:network-activity', {
    detail: { activeRequests },
  }))
}

export function installNetworkActivityTracker() {
  if (installed) return
  installed = true
  const originalFetch = window.fetch.bind(window)

  window.fetch = async (...arguments_) => {
    activeRequests += 1
    publishActivity()
    try {
      const response = await originalFetch(...arguments_)
      const input = arguments_[0]
      const options = arguments_[1] || {}
      const method = String(options.method || input?.method || 'GET').toUpperCase()
      const url = String(input?.url || input || '')
      const isMutation = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method)
      const isSilentBackgroundUpdate = url.includes('/notifications/')

      if (response.ok && isMutation && !isSilentBackgroundUpdate) {
        const contentType = response.headers.get('content-type') || ''
        if (contentType.includes('application/json')) {
          response.clone().json().then((data) => {
            if (typeof data?.message === 'string' && data.message.trim()) {
              window.dispatchEvent(new CustomEvent('homeserve:toast', {
                detail: {
                  message: data.message.trim(),
                  title: method === 'DELETE' ? 'Removed successfully' : method === 'POST' ? 'Action completed' : 'Changes saved',
                  type: 'success',
                },
              }))
            }
          }).catch(() => {})
        }
      }
      return response
    } finally {
      activeRequests = Math.max(0, activeRequests - 1)
      publishActivity()
    }
  }
}
