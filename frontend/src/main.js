import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {createPersistedState} from "pinia-plugin-persistedstate";
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()
const persist = createPersistedState()

pinia.use(persist)
app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')