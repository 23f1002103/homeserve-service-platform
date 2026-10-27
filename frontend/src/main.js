import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { installNetworkActivityTracker } from './utils/networkActivity'
import './style.css'

installNetworkActivityTracker()
createApp(App).use(router).mount('#app')

