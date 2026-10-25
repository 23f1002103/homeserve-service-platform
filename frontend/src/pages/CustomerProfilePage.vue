<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CustomerHeader from '../components/CustomerHeader.vue'

const route = useRoute()
const router = useRouter()
const profile = ref(null)
const editing = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive({ phone_number: '', address: '', city: '', state: '', pin_code: '' })

async function loadProfile() {
  try {
    const response = await fetch('/api/customer/profile', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not load profile')
    profile.value = data.profile
    Object.assign(form, data.profile)
    if (route.query.complete === '1' || data.profile.profile_complete === false) {
      editing.value = true
    }
  } catch (error) { errorMessage.value = error.message }
}

async function saveProfile() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await fetch('/api/customer/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify(form),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.message || 'Could not update profile')
    await loadProfile()
    const savedUser = JSON.parse(localStorage.getItem('user') || '{}')
    savedUser.profile_complete = true
    localStorage.setItem('user', JSON.stringify(savedUser))
    editing.value = false
    successMessage.value = data.message
    const nextPath = typeof route.query.next === 'string' ? route.query.next : ''
    if (nextPath.startsWith('/customer/') && nextPath !== '/customer/profile') {
      await router.push(nextPath)
    }
  } catch (error) { errorMessage.value = error.message }
  finally { saving.value = false }
}

function cancelEdit() { Object.assign(form, profile.value); editing.value = false; errorMessage.value = '' }
onMounted(loadProfile)
</script>

<template>
  <div class="workbench customer-workbench"><CustomerHeader current="profile" /><main class="workbench-content role-section-page">
    <header class="role-section-heading"><div><p class="workbench-label">HOME PROFILE</p><h1>Your account and<br />service address.</h1></div><p>This address will help prefill future booking requests.</p></header>
    <p v-if="route.query.reason === 'booking'" class="profile-completion-note">Your booking is waiting. Add your contact and address details once, then we’ll take you back to the service you selected. Your phone number is shared only with the professional who accepts your job.</p>
    <p v-else-if="route.query.complete === '1' || profile?.profile_complete === false" class="profile-completion-note">Complete these details before booking a service. You can still browse your dashboard and services before doing this.</p>
    <p v-if="errorMessage" class="dashboard-alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="profile-success">{{ successMessage }}</p>
    <section v-if="profile" class="detail-sheet customer-detail-sheet">
      <div class="detail-sheet__title"><span>{{ profile.username.charAt(0).toUpperCase() }}</span><h2>{{ profile.username }}</h2><p>HomeServe customer</p><button v-if="!editing" @click="editing = true">Edit profile</button></div>
      <form v-if="editing" class="profile-edit-form" @submit.prevent="saveProfile">
        <label>Phone number<input v-model="form.phone_number" type="tel" autocomplete="tel" minlength="7" maxlength="20" required /></label>
        <label class="profile-form-wide">Address<input v-model="form.address" required /></label>
        <label>City<input v-model="form.city" required /></label>
        <label>State<input v-model="form.state" required /></label>
        <label>PIN code<input v-model="form.pin_code" required /></label>
        <div class="profile-form-actions"><button type="button" @click="cancelEdit">Cancel</button><button type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save changes' }}</button></div>
      </form>
      <dl v-else><div><dt>Email</dt><dd>{{ profile.email }}</dd></div><div><dt>Phone</dt><dd>{{ profile.phone_number || 'Not provided' }}</dd></div><div><dt>Address</dt><dd>{{ profile.address }}</dd></div><div><dt>City</dt><dd>{{ profile.city }}</dd></div><div><dt>State</dt><dd>{{ profile.state }}</dd></div><div><dt>PIN code</dt><dd>{{ profile.pin_code }}</dd></div></dl>
    </section>
  </main></div>
</template>
