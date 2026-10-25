<script setup>
import { onMounted, reactive, ref } from 'vue'
import ProfessionalHeader from '../components/ProfessionalHeader.vue'

const profile = ref(null)
const editing = ref(false)
const saving = ref(false)
const photoInput = ref(null)
const photoBusy = ref(false)
const photoVersion = ref(Date.now())
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive({ phone_number: '', experience_years: null, address: '', city: '', state: '', pin_code: '' })

async function loadProfile() {
  try {
    const response = await fetch('/api/professional/profile', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load profile')
    profile.value = data.profile
    Object.assign(form, data.profile)
  } catch (error) { errorMessage.value = error.message }
}

async function saveProfile() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  const payload = { ...form, experience_years: form.experience_years === '' ? null : Number(form.experience_years) }
  try {
    const response = await fetch('/api/professional/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify(payload),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update profile')
    await loadProfile()
    editing.value = false
    successMessage.value = data.message
  } catch (error) { errorMessage.value = error.message }
  finally { saving.value = false }
}

function cancelEdit() { Object.assign(form, profile.value); editing.value = false; errorMessage.value = '' }

async function uploadPhoto(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  errorMessage.value = ''
  successMessage.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    errorMessage.value = 'Choose a JPEG, PNG, or WebP image'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    errorMessage.value = 'Profile photo must be 2 MB or smaller'
    return
  }

  photoBusy.value = true
  try {
    const body = new FormData()
    body.append('photo', file)
    const response = await fetch('/api/professional/profile/photo', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body,
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not upload profile photo')
    await loadProfile()
    photoVersion.value = Date.now()
    successMessage.value = data.message
  } catch (error) { errorMessage.value = error.message }
  finally { photoBusy.value = false }
}

async function removePhoto() {
  errorMessage.value = ''
  successMessage.value = ''
  photoBusy.value = true
  try {
    const response = await fetch('/api/professional/profile/photo', {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not remove profile photo')
    await loadProfile()
    successMessage.value = data.message
  } catch (error) { errorMessage.value = error.message }
  finally { photoBusy.value = false }
}
onMounted(loadProfile)
</script>

<template>
  <div class="workbench professional-workbench"><ProfessionalHeader current="profile" /><main class="workbench-content role-section-page">
    <header class="role-section-heading"><div><p class="workbench-label">WORK PROFILE</p><h1>Your professional<br />identity.</h1></div><p>This information helps HomeServe match you with suitable service requests.</p></header>
    <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
    <section v-if="profile" class="detail-sheet professional-detail-sheet">
      <div class="detail-sheet__title">
        <span class="professional-profile-photo"><img v-if="profile.profile_image_url" :src="`${profile.profile_image_url}?v=${photoVersion}`" alt="Your professional profile" /><template v-else>{{ profile.username.charAt(0).toUpperCase() }}</template></span>
        <input ref="photoInput" class="profile-photo-input" type="file" accept="image/jpeg,image/png,image/webp" @change="uploadPhoto" />
        <div class="profile-photo-actions"><button type="button" :disabled="photoBusy" @click="photoInput?.click()">{{ photoBusy ? 'Working…' : profile.profile_image_url ? 'Replace photo' : 'Add profile photo' }}</button><button v-if="profile.profile_image_url" type="button" :disabled="photoBusy" @click="removePhoto">Remove</button></div>
        <small class="profile-photo-help">JPEG, PNG or WebP · maximum 2 MB</small>
        <h2>{{ profile.username }}</h2><p>{{ profile.service }}</p><div class="professional-rating"><strong>{{ profile.average_rating ?? 'New' }}</strong><small>{{ profile.review_count ? `★ from ${profile.review_count} review${profile.review_count === 1 ? '' : 's'}` : 'No customer ratings yet' }}</small></div><button v-if="!editing" @click="editing = true">Edit profile</button>
      </div>
      <form v-if="editing" class="profile-edit-form" @submit.prevent="saveProfile">
        <label>Phone number<input v-model="form.phone_number" type="tel" /></label>
        <label>Years of experience<input v-model="form.experience_years" type="number" min="0" /></label>
        <label class="profile-form-wide">Address<input v-model="form.address" required /></label>
        <label>City<input v-model="form.city" required /></label>
        <label>State<input v-model="form.state" required /></label>
        <label>PIN code<input v-model="form.pin_code" required /></label>
        <div class="profile-form-actions"><button type="button" @click="cancelEdit">Cancel</button><button type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save changes' }}</button></div>
      </form>
      <dl v-else><div><dt>Customer rating</dt><dd>{{ profile.average_rating ? `${profile.average_rating} / 5 (${profile.review_count} reviews)` : 'No ratings yet' }}</dd></div><div><dt>Email</dt><dd>{{ profile.email }}</dd></div><div><dt>Phone</dt><dd>{{ profile.phone_number || 'Not provided' }}</dd></div><div><dt>Experience</dt><dd>{{ profile.experience_years ?? 'Not provided' }}<span v-if="profile.experience_years"> years</span></dd></div><div><dt>Address</dt><dd>{{ profile.address }}</dd></div><div><dt>City and state</dt><dd>{{ profile.city }}, {{ profile.state }}</dd></div><div><dt>PIN code</dt><dd>{{ profile.pin_code }}</dd></div><div><dt>Status</dt><dd class="detail-status">{{ profile.approval_status }}</dd></div></dl>
    </section>
    <RouterLink class="profile-earnings-link" to="/professional/earnings"><span>₹</span><div><strong>View earnings</strong><small>Open your week-by-week payout ledger</small></div><b>→</b></RouterLink>
  </main></div>
</template>
