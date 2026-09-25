export const HOME_CHANNEL_TABS = [
  { key: 'follow', labelKey: 'home.channelFollow', sticky: false },
  { key: 'recommend', labelKey: 'home.channelRecommend', sticky: true },
  { key: 'billionSubsidy', labelKey: 'home.billionSubsidy', sticky: false },
  { key: 'superDiscount', labelKey: 'home.superDiscountTitle', sticky: false },
  { key: 'seckill', labelKey: 'home.flashSale', sticky: false },
  { key: 'subsidy', labelKey: 'home.channelSubsidy', sticky: false },
  { key: 'newArrival', labelKey: 'home.newArrival', sticky: false },
  { key: 'liveStream', labelKey: 'home.liveStream', sticky: false },
  { key: 'freeShipping', labelKey: 'home.freeShipping', sticky: false },
  { key: 'more', labelKey: 'home.channelMore', sticky: false },
]

/** 参与首页横向滑动的频道（与 Tab 栏顺序一致） */
export const HOME_SWIPE_CHANNELS = HOME_CHANNEL_TABS

export function homeChannelIndex(key) {
  const index = HOME_SWIPE_CHANNELS.findIndex((tab) => tab.key === key)
  if (index >= 0) return index
  const recommendIndex = HOME_SWIPE_CHANNELS.findIndex((tab) => tab.key === 'recommend')
  return recommendIndex >= 0 ? recommendIndex : 0
}
