import { ref } from 'vue'

// 单用户场景不需要 Pinia，一个模块级 ref 足够
export const currentUser = ref(null)
export const bootstrapped = ref(false)

export function setUser(user) {
  currentUser.value = user
  bootstrapped.value = true
}

export function clearUser() {
  currentUser.value = null
  bootstrapped.value = true
}

export function isLoggedIn() {
  return currentUser.value !== null
}
