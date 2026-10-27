<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import CustomerHeader from '../components/CustomerHeader.vue'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isProfessional = user.role === 'professional'
const roleLabel = isProfessional ? 'Professional' : 'Customer'
const query = ref('')
const activeTopic = ref('all')
const status = reactive({ state: 'checking', revision: '', checkedAt: null })

const customerFaqs = [
  { topic: 'bookings', question: 'How does a booking work?', answer: 'Choose a service, confirm the address and schedule, then complete the payment step. Your request appears under My bookings while a matching professional accepts it.' },
  { topic: 'payments', question: 'How do I resume a pending payment?', answer: 'Open My bookings, find the booking marked Payment pending, and choose Resume payment. Your booking becomes visible to professionals only after payment is completed.' },
  { topic: 'bookings', question: 'Can I cancel a booking?', answer: 'You can cancel a request from My bookings before a professional is assigned. Once a professional accepts the job, contact support so the assignment can be reviewed safely.' },
  { topic: 'account', question: 'How do I manage my service address?', answer: 'Open My profile from the account menu to update your phone number, address, city, state, and PIN code. Always check the address shown before confirming a booking.' },
  { topic: 'jobs', question: 'How can I contact my assigned professional?', answer: 'When a professional accepts your booking, their contact details and assignment information appear in My bookings. Use those details only for the active service request.' },
  { topic: 'safety', question: 'How do I report a booking problem?', answer: 'Email or call support and include the booking number. For an immediate safety risk, move to a safe place and contact local emergency services first.' },
]

const professionalFaqs = [
  { topic: 'jobs', question: 'How do I accept and complete jobs?', answer: 'Available paid requests matching your trade and current city appear in My jobs. Accept one request at a time, complete the service, then use Mark completed to close the job.' },
  { topic: 'location', question: 'Why is location verification required?', answer: 'HomeServe uses your current GPS city to show relevant nearby bookings. Location must be verified again after a new sign-in or whenever you choose Detect again.' },
  { topic: 'earnings', question: 'How are earnings and commission calculated?', answer: 'Your earnings page shows completed work week by week. Each entry separates the service amount, the platform commission, and your professional share.' },
  { topic: 'account', question: 'What is needed for profile approval?', answer: 'Your service, experience, contact details, and address help the operations team review your application. Keep these details accurate in My profile.' },
  { topic: 'jobs', question: 'When should I contact a customer?', answer: 'Use the phone number attached to an accepted job only for arrival, access, or service coordination. Do not use customer details after the job is complete.' },
  { topic: 'payments', question: 'How do I report a job or payment issue?', answer: 'Email or call support with the job number and a concise description. Do not mark an unfinished service as completed to resolve a payment issue.' },
]

const faqs = isProfessional ? professionalFaqs : customerFaqs
const topics = computed(() => ['all', ...new Set(faqs.map((item) => item.topic))])
const filteredFaqs = computed(() => {
  const term = query.value.trim().toLowerCase()
  return faqs.filter((item) => {
    const matchesTopic = activeTopic.value === 'all' || item.topic === activeTopic.value
    const matchesQuery = !term || `${item.question} ${item.answer} ${item.topic}`.toLowerCase().includes(term)
    return matchesTopic && matchesQuery
  })
})

const quickActions = computed(() => isProfessional
  ? [
      { label: 'Open my jobs', detail: 'Review assignments and schedules', to: '/professional/jobs', mark: '01' },
      { label: 'Review earnings', detail: 'See payouts and commission', to: '/professional/earnings', mark: '02' },
      { label: 'Update my profile', detail: 'Keep approval details current', to: '/professional/profile', mark: '03' },
    ]
  : [
      { label: 'Open my bookings', detail: 'Track, pay, or review requests', to: '/customer/bookings', mark: '01' },
      { label: 'Book a service', detail: 'Find help for your home', to: '/customer/services', mark: '02' },
      { label: 'Update my address', detail: 'Manage your home profile', to: '/customer/profile', mark: '03' },
    ])

async function checkStatus() {
  status.state = 'checking'
  try {
    const response = await fetch('/api/health')
    const data = await response.json()
    if (!response.ok || data.status !== 'ok') throw new Error('Unavailable')
    status.state = 'online'
    status.revision = data.revision || ''
  } catch {
    status.state = navigator.onLine ? 'unavailable' : 'offline'
  } finally {
    status.checkedAt = new Date()
  }
}

onMounted(checkStatus)
</script>

<template>
  <div class="workbench" :class="isProfessional ? 'professional-workbench' : 'customer-workbench'">
    <ProfessionalHeader v-if="isProfessional" current="support" />
    <CustomerHeader v-else current="support" />

    <main class="workbench-content support-page">
      <header class="support-hero">
        <div>
          <p class="workbench-label">{{ roleLabel.toUpperCase() }} SUPPORT CENTRE</p>
          <h1>Help, right when<br />you need it.</h1>
        </div>
        <div class="support-hero__aside">
          <p>Find clear answers, take a quick action, or tell the HomeServe team what went wrong.</p>
          <label class="support-search">
            <span aria-hidden="true">⌕</span>
            <input v-model="query" type="search" placeholder="Search help articles" aria-label="Search help articles" />
            <button v-if="query" type="button" aria-label="Clear search" @click="query = ''">Clear</button>
          </label>
        </div>
      </header>

      <nav class="support-jump-nav" aria-label="Support page sections">
        <a href="#answers">FAQs</a><a href="#contact">Email or call</a><a href="#safety">Safety</a><a href="#policies">Policies</a><a href="#system">System status</a>
      </nav>

      <section class="support-quick-actions" aria-label="Quick actions">
        <RouterLink v-for="action in quickActions" :key="action.to" :to="action.to">
          <span>{{ action.mark }}</span><div><strong>{{ action.label }}</strong><small>{{ action.detail }}</small></div><b>↗</b>
        </RouterLink>
      </section>

      <section id="answers" class="support-section faq-section">
        <header class="support-section__heading">
          <div><p class="workbench-label">ANSWERS / {{ roleLabel.toUpperCase() }}</p><h2>Frequently asked<br />questions.</h2></div>
          <p>Guidance tailored to how you use HomeServe.</p>
        </header>
        <div class="support-topic-filters" aria-label="Filter frequently asked questions">
          <button v-for="topic in topics" :key="topic" type="button" :class="{ active: activeTopic === topic }" @click="activeTopic = topic">{{ topic }}</button>
        </div>
        <div v-if="filteredFaqs.length" class="support-faqs">
          <details v-for="(item, index) in filteredFaqs" :key="item.question">
            <summary><span>{{ String(index + 1).padStart(2, '0') }}</span><strong>{{ item.question }}</strong><b aria-hidden="true">+</b></summary>
            <p>{{ item.answer }}</p>
          </details>
        </div>
        <div v-else class="support-empty-search"><strong>No matching answers found.</strong><p>Try a different phrase, or email or call the support contacts below.</p><button type="button" @click="query = ''; activeTopic = 'all'">Show all answers</button></div>
      </section>

      <section id="contact" class="support-contact">
        <div class="support-contact__intro">
          <p class="workbench-label">CONTACT SUPPORT</p>
          <h2>Talk to<br />support.</h2>
          <p>Choose email for a detailed issue or call when you need a quicker conversation. Include your booking or job number when you have one.</p>
          <dl><div><dt>Signed in as</dt><dd>{{ user.email || 'Your HomeServe account' }}</dd></div><div><dt>Support for</dt><dd>{{ roleLabel }} account</dd></div></dl>
        </div>
        <div class="support-contact-options">
          <a href="mailto:care@homeserve.example?subject=HomeServe%20support">
            <span aria-hidden="true">@</span><div><small>EMAIL SUPPORT · DEMO</small><strong>care@homeserve.example</strong><p>Best for booking details, account questions, and payment concerns.</p></div><b>Open email ↗</b>
          </a>
          <a href="tel:+911800000000">
            <span aria-hidden="true">☎</span><div><small>CALL SUPPORT · DEMO</small><strong>+91 1800 000 000</strong><p>Available Monday–Saturday, 9:00 AM–6:00 PM IST.</p></div><b>Call now ↗</b>
          </a>
          <p>These are placeholder contact details for the project demonstration. Do not share passwords, OTPs, or full payment-card details.</p>
        </div>
      </section>

      <section id="safety" class="support-safety">
        <div><span aria-hidden="true">!</span><p class="workbench-label">URGENT SAFETY GUIDANCE</p><h2>Your safety comes first.</h2></div>
        <div><p>If you feel unsafe or there is an immediate risk to a person or property, move to a safe place and contact your local emergency services. Do not wait for HomeServe support.</p><ul><li>Do not share an OTP, password, or full payment-card details.</li><li>Keep service communication related to the active booking.</li><li>Email or call support for non-emergency safety concerns.</li></ul></div>
      </section>

      <section id="policies" class="support-section policy-section">
        <header class="support-section__heading"><div><p class="workbench-label">PLATFORM GUIDANCE</p><h2>Policies in<br />plain language.</h2></div><p>A quick guide to the standards that keep each service clear and respectful.</p></header>
        <div class="policy-grid">
          <article><span>01</span><h3>Cancellations & refunds</h3><p>Cancel unassigned requests from the bookings page. Assigned or completed service disputes need a support review. Any eligible refund follows the original payment route.</p></article>
          <article><span>02</span><h3>Privacy & account safety</h3><p>Use personal information only to arrange an active service. HomeServe will never ask for your password or OTP through a support request.</p></article>
          <article><span>03</span><h3>Respectful conduct</h3><p>Customers and professionals must communicate respectfully and provide a safe environment. Harassment, threats, discrimination, or fraud should be reported.</p></article>
        </div>
        <p class="policy-note">These summaries are practical guidance for this project experience and are not a substitute for complete production terms.</p>
      </section>

      <section id="system" class="support-system">
        <div><p class="workbench-label">HOME SERVE SYSTEM</p><h2>Platform status</h2><p>A live check of the service powering bookings and account data.</p></div>
        <div class="system-status-card" :class="`is-${status.state}`">
          <i></i><div><strong>{{ status.state === 'online' ? 'All systems operational' : status.state === 'checking' ? 'Checking platform status…' : status.state === 'offline' ? 'You appear to be offline' : 'Service check unavailable' }}</strong><small v-if="status.checkedAt">Checked {{ status.checkedAt.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' }) }}<template v-if="status.revision"> · revision {{ status.revision }}</template></small></div><button type="button" :disabled="status.state === 'checking'" @click="checkStatus">Check again</button>
        </div>
        <footer><span>HomeServe web app</span><span>Version 0.1.0</span></footer>
      </section>
    </main>
  </div>
</template>
