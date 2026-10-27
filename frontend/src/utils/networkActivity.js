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
      return await originalFetch(...arguments_)
    } finally {
      activeRequests = Math.max(0, activeRequests - 1)
      publishActivity()
    }
  }
}
