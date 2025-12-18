import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

// Pinia for state management
app.use(createPinia())

// Vue Router
app.use(router)

app.mount('#app')
