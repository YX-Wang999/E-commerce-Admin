<script setup>
import { getConfirmState, rejectConfirm, resolveConfirm } from '@/utils/confirmDialog'

const state = getConfirmState()

function onCancel() {
  rejectConfirm()
}

function onConfirm() {
  resolveConfirm()
}
</script>

<template>
  <van-dialog
    v-model:show="state.show"
    class="app-confirm-dialog"
    :show-confirm-button="false"
    :show-cancel-button="false"
    teleport="body"
    :close-on-click-overlay="false"
  >
    <div class="app-confirm-dialog__body" :class="{ 'app-confirm-dialog__body--solo': !state.title }">
      <div v-if="state.title" class="app-confirm-dialog__title">
        {{ state.title }}
      </div>
      <div v-if="state.message" class="app-confirm-dialog__message">
        {{ state.message }}
      </div>
    </div>

    <template #footer>
      <div class="app-confirm-dialog__footer">
        <button type="button" class="app-confirm-dialog__btn app-confirm-dialog__btn--cancel" @click="onCancel">
          {{ state.cancelText }}
        </button>
        <button type="button" class="app-confirm-dialog__btn app-confirm-dialog__btn--confirm" @click="onConfirm">
          {{ state.confirmText }}
        </button>
      </div>
    </template>
  </van-dialog>
</template>

<style scoped>
.app-confirm-dialog__body {
  padding: 26px 24px 8px;
  text-align: center;
}

.app-confirm-dialog__title {
  color: #323233;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5;
}

.app-confirm-dialog__message {
  margin-top: 12px;
  color: #646566;
  font-size: 14px;
  line-height: 1.6;
}

.app-confirm-dialog__body--solo .app-confirm-dialog__message {
  margin-top: 0;
}

.app-confirm-dialog__footer {
  display: flex;
  border-top: 1px solid #ebedf0;
}

.app-confirm-dialog__btn {
  flex: 1;
  height: 48px;
  margin: 0;
  border: 0;
  background: #fff;
  font-size: 16px;
  line-height: 48px;
  cursor: pointer;
}

.app-confirm-dialog__btn--cancel {
  color: #646566;
}

.app-confirm-dialog__btn--confirm {
  color: #ee0a24;
  border-left: 1px solid #ebedf0;
}

.app-confirm-dialog__btn:active {
  background: #f2f3f5;
}
</style>
