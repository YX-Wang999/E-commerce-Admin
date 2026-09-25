<script setup>
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const pageTitle = computed(() =>
  authStore.user?.is_first_login ? t('login.firstLogin') : t('password.title'),
)

const rules = computed(() => {
  const validateConfirmPassword = (_rule, value, callback) => {
    if (value !== form.new_password) {
      callback(new Error(t('password.mismatch')))
      return
    }
    callback()
  }

  return {
    old_password: [{ required: true, message: t('password.oldRequired'), trigger: 'blur' }],
    new_password: [
      { required: true, message: t('password.newRequired'), trigger: 'blur' },
      { min: 8, message: t('password.minLength'), trigger: 'blur' },
    ],
    confirm_password: [
      { required: true, message: t('password.confirmRequired'), trigger: 'blur' },
      { validator: validateConfirmPassword, trigger: 'blur' },
    ],
  }
})

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    const isFirstLogin = authStore.user?.is_first_login
    if (isFirstLogin) {
      await authStore.fetchProfile()
      ElMessage.success(t('common.success'))
      router.push('/dashboard')
      return
    }
    ElMessage.success(t('password.success'))
    authStore.logout()
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-card shadow="never" class="change-password-card">
    <template #header>
      <span>{{ pageTitle }}</span>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 480px">
      <el-form-item :label="t('password.oldPassword')" prop="old_password">
        <el-input
          v-model="form.old_password"
          type="password"
          show-password
          :placeholder="t('password.oldRequired')"
        />
      </el-form-item>
      <el-form-item :label="t('password.newPassword')" prop="new_password">
        <el-input
          v-model="form.new_password"
          type="password"
          show-password
          :placeholder="t('password.newRequired')"
        />
      </el-form-item>
      <el-form-item :label="t('password.confirmPassword')" prop="confirm_password">
        <el-input
          v-model="form.confirm_password"
          type="password"
          show-password
          :placeholder="t('password.confirmRequired')"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">{{ t('password.submit') }}</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.change-password-card {
  max-width: 640px;
}
</style>
