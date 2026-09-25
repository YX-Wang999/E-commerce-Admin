<template>
  <div class="auth-page">
    <div class="auth-card">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background: #f5f6fa;
}
.auth-card {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 14px;
  padding: 36px 32px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  overflow: visible;
  box-sizing: border-box;
}
.auth-card :deep(.auth-form) {
  margin: 0;
}
.auth-card :deep(.auth-form .van-cell) {
  padding-left: 0;
  padding-right: 0;
  overflow: visible;
}
.auth-card :deep(.auth-form .van-field__label) {
  width: 88px;
  margin-right: 14px;
  flex: none;
  text-align: right;
  color: #646566;
}
.auth-card :deep(.auth-form .van-field__body) {
  flex: 1;
  min-width: 0;
}
.auth-card :deep(.auth-form .van-field__control) {
  text-align: left;
  min-width: 0;
}
.auth-card :deep(.auth-form .auth-phone-field),
.auth-card :deep(.auth-form .van-field--phone) {
  display: block;
  overflow: visible;
}
.auth-card :deep(.auth-form .auth-phone-field .van-field__label),
.auth-card :deep(.auth-form .van-field--phone .van-field__label) {
  width: auto;
  margin-right: 0;
  margin-bottom: 8px;
  text-align: left;
}
.auth-card :deep(.auth-form .auth-phone-field .van-field__value),
.auth-card :deep(.auth-form .van-field--phone .van-field__value) {
  width: 100%;
  min-width: 0;
  overflow: visible;
}
.auth-card :deep(.auth-form .auth-phone-field .van-field__body),
.auth-card :deep(.auth-form .van-field--phone .van-field__body) {
  width: 100%;
  min-width: 0;
}
</style>
