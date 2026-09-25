<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResponsive } from '@/composables/useResponsive'

const props = defineProps({
  /** @type {{ label: string, type?: string, onClick: Function, visible?: boolean, danger?: boolean }[]} */
  actions: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()
const { isCompactActions } = useResponsive()

const visibleActions = computed(() => props.actions.filter((item) => item.visible !== false))

function runAction(handler) {
  if (typeof handler === 'function') {
    handler()
  }
}
</script>

<template>
  <div class="table-actions">
    <template v-if="!isCompactActions">
      <span
        v-for="(action, index) in visibleActions"
        :key="index"
        class="table-actions__slot"
      >
        <el-button
          link
          :type="action.type || 'primary'"
          @click="runAction(action.onClick)"
        >
          {{ action.label }}
        </el-button>
      </span>
    </template>
    <template v-else-if="visibleActions.length">
      <span class="table-actions__slot">
        <el-button
          link
          :type="visibleActions[0].type || 'primary'"
          @click="runAction(visibleActions[0].onClick)"
        >
          {{ visibleActions[0].label }}
        </el-button>
      </span>
      <el-dropdown v-if="visibleActions.length > 1" trigger="click" class="table-actions__more">
        <el-button link type="primary">{{ t('common.more') }}</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="(action, index) in visibleActions.slice(1)"
              :key="index"
              @click="runAction(action.onClick)"
            >
              <span :class="{ 'is-danger': action.danger }">{{ action.label }}</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
  </div>
</template>

<style scoped>
.is-danger {
  color: var(--el-color-danger);
}
</style>
