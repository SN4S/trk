<template>
  <div class="login_container">
    <sidebar-logo />

    <form class="login_form" @submit.prevent="submit">
      <h1 class="login_title">Вхід</h1>

      <FormInput
        id="login_username"
        label="Логін"
        v-model="username"
        placeholder="username"
        autocomplete="username"
        :disabled="pending"
        required
      />

      <FormInput
        id="login_password"
        label="Пароль"
        v-model="password"
        type="password"
        placeholder="••••••••"
        autocomplete="current-password"
        :disabled="pending"
        required
      />

      <p v-if="error" class="login_error">{{ error }}</p>

      <FormButton type="submit" :disabled="pending">
        {{ pending ? 'Вхід…' : 'Увійти' }}
      </FormButton>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { login } = useAuth()

const username = ref('')
const password = ref('')
const pending = ref(false)
const error = ref<string | null>(null)

async function submit() {
  error.value = null
  pending.value = true
  try {
    await login({ username: username.value, password: password.value })
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Невірний логін або пароль'
  } finally {
    pending.value = false
  }
}
</script>

<style scoped>
.login_container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: var(--nav-bar-bg);
  gap: 1.5rem;
}

.login_form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 320px;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  background: var(--message-bg-color);
}

.login_title {
  font-size: 1.4rem;
  font-weight: 700;
  text-align: center;
  color: var(--message-text-color);
  margin-bottom: 0.25rem;
}

.login_error {
  font-size: 13px;
  color: var(--danger);
  text-align: center;
  padding: 4px 0;
}
</style>