<script setup>
defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
  limit: {
    type: Number,
    default: 3,
  },
})
</script>

<template>
  <div v-if="tags.length" class="promo-tags">
    <span
      v-for="tag in tags.slice(0, limit)"
      :key="tag.code"
      class="promo-tag"
      :style="{ background: tag.color, color: tag.text_color }"
    >
      <span v-if="tag.icon" class="promo-tag__icon">{{ tag.icon }}</span>
      {{ tag.name }}
    </span>
  </div>
</template>

<style scoped>
.promo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.promo-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 100%;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  line-height: 1.5;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.promo-tag__icon {
  font-size: 10px;
  line-height: 1;
}
</style>
