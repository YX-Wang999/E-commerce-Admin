<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  footerBadges,
  footerFeatures,
  footerLegalLinks,
  footerLinkColumns,
} from '@/config/footer'

const { t } = useI18n()

const currentYear = new Date().getFullYear()

const hasFeatures = computed(() => footerFeatures.length > 0)
const hasLinkColumns = computed(() => footerLinkColumns.length > 0)
const hasLegalLinks = computed(() => footerLegalLinks.length > 0)
</script>

<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <!-- 服务亮点：多 / 快 / 好 / 省 — 后续在 config/footer.js 中配置 -->
      <section v-if="hasFeatures" class="footer-section footer-features">
        <div
          v-for="item in footerFeatures"
          :key="item.id"
          class="feature-item"
        >
          <span class="feature-icon">{{ item.icon }}</span>
          <div class="feature-text">
            <strong>{{ item.title }}</strong>
            <span>{{ item.desc }}</span>
          </div>
        </div>
      </section>

      <!-- 导航链接列 — 后续在 config/footer.js 中配置 -->
      <section v-if="hasLinkColumns" class="footer-section footer-links">
        <div
          v-for="column in footerLinkColumns"
          :key="column.id"
          class="link-column"
        >
          <h4 class="link-column-title">{{ column.title }}</h4>
          <a
            v-for="link in column.links"
            :key="link.href"
            :href="link.href"
            class="link-item"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ link.label }}
          </a>
        </div>
      </section>

      <!-- 备案 / 法律链接 — 后续在 config/footer.js 中配置 -->
      <section v-if="hasLegalLinks" class="footer-section footer-legal">
        <a
          v-for="link in footerLegalLinks"
          :key="link.href"
          :href="link.href"
          class="legal-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ link.label }}
        </a>
      </section>

      <!-- 底部认证标识（8 个） -->
      <section class="footer-section footer-badges" :aria-label="t('footer.badgesTitle')">
        <a
          v-for="badge in footerBadges"
          :key="badge.id"
          :href="badge.href"
          class="footer-badge"
          :class="`footer-badge--${badge.id}`"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span class="badge-icon" aria-hidden="true">
            <svg v-if="badge.id === 'trusted'" viewBox="0 0 48 48" class="badge-svg">
              <circle cx="24" cy="24" r="22" fill="#fff5f0" stroke="#e1251b" stroke-width="2" />
              <path d="M24 8l4 8h9l-7 6 3 9-9-5-9 5 3-9-7-6h9z" fill="#e1251b" />
            </svg>
            <svg v-else-if="badge.id === 'cyberPolice'" viewBox="0 0 48 48" class="badge-svg">
              <rect x="6" y="10" width="36" height="28" rx="4" fill="#1677ff" />
              <circle cx="24" cy="22" r="8" fill="#fff" />
              <path d="M24 18v8M20 22h8" stroke="#1677ff" stroke-width="2" />
            </svg>
            <svg v-else-if="badge.id === 'integrity'" viewBox="0 0 48 48" class="badge-svg">
              <circle cx="24" cy="24" r="20" fill="#fff0f0" stroke="#e1251b" stroke-width="2" />
              <text x="24" y="29" text-anchor="middle" fill="#e1251b" font-size="14" font-weight="700">诚</text>
            </svg>
            <svg v-else-if="badge.id === 'harmfulReport'" viewBox="0 0 48 48" class="badge-svg">
              <path d="M24 4l18 8v12c0 11-8 18-18 20C14 42 6 35 6 24V12z" fill="#1677ff" />
              <path d="M22 16h4v12h-4zM22 32h4v4h-4z" fill="#fff" />
            </svg>
            <svg v-else-if="badge.id === 'reportApp'" viewBox="0 0 48 48" class="badge-svg">
              <rect x="10" y="6" width="28" height="36" rx="4" fill="#e1251b" />
              <path d="M24 16v14M18 26l6 6 6-6" stroke="#fff" stroke-width="2" fill="none" />
            </svg>
            <svg v-else-if="badge.id === 'antiPorn'" viewBox="0 0 48 48" class="badge-svg">
              <rect x="4" y="12" width="40" height="24" rx="3" fill="#c81623" />
              <text x="24" y="28" text-anchor="middle" fill="#fff" font-size="11" font-weight="700">扫黄打非</text>
            </svg>
            <svg v-else-if="badge.id === 'accessibility'" viewBox="0 0 48 48" class="badge-svg">
              <circle cx="24" cy="14" r="5" fill="#1677ff" />
              <path d="M14 22h20M24 19v16M18 35l6-6 6 6" stroke="#1677ff" stroke-width="2" fill="none" />
            </svg>
            <svg v-else viewBox="0 0 48 48" class="badge-svg">
              <rect x="8" y="8" width="32" height="32" rx="4" fill="#f0f5ff" stroke="#1677ff" stroke-width="2" />
              <path d="M16 24h16M24 16v16" stroke="#1677ff" stroke-width="2" />
            </svg>
          </span>
          <span class="badge-label">{{ t(badge.labelKey) }}</span>
        </a>
      </section>

      <div class="footer-copyright">
        {{ t('footer.copyright', { year: currentYear }) }}
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: auto;
  background: #eaeaea;
  border-top: 1px solid #ddd;
  color: #666;
  font-size: 12px;
}

.footer-inner {
  max-width: 1190px;
  margin: 0 auto;
  padding: 24px 16px 20px;
}

.footer-section + .footer-section {
  margin-top: 20px;
}

.footer-features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-icon {
  font-size: 28px;
  color: #e1251b;
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-text strong {
  font-size: 16px;
  color: #333;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.link-column-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.link-item {
  display: block;
  margin-bottom: 6px;
  color: #666;
  text-decoration: none;
}

.link-item:hover {
  color: #e1251b;
}

.footer-legal {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ddd;
}

.legal-link {
  color: #666;
  text-decoration: none;
}

.legal-link:hover {
  color: #e1251b;
}

.footer-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: flex-start;
  gap: 12px 16px;
  padding: 8px 0 16px;
}

.footer-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 110px;
  text-decoration: none;
  color: #666;
  transition: opacity 0.2s;
}

.footer-badge:hover {
  opacity: 0.85;
}

.badge-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 40px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 2px;
}

.badge-svg {
  width: 36px;
  height: 36px;
}

.badge-label {
  text-align: center;
  line-height: 1.35;
  font-size: 11px;
  color: #888;
  white-space: pre-line;
}

.footer-copyright {
  text-align: center;
  color: #999;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .footer-features {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-badge {
    width: calc(50% - 8px);
  }
}
</style>
