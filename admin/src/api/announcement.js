import request from '@/utils/request'

export function getAnnouncementList(params) {
  return request.get('/announcements/', { params })
}

export function getAnnouncementDetail(id) {
  return request.get(`/announcements/${id}/`)
}

export function createAnnouncement(data) {
  return request.post('/announcements/', data)
}

export function updateAnnouncement(id, data) {
  return request.put(`/announcements/${id}/`, data)
}

export function deleteAnnouncement(id) {
  return request.delete(`/announcements/${id}/`)
}

export function publishAnnouncement(id) {
  return request.post(`/announcements/${id}/publish/`)
}

export function offlineAnnouncement(id) {
  return request.post(`/announcements/${id}/offline/`)
}

export function getAnnouncementBanners() {
  return request.get('/announcements/banners/')
}

export function getAnnouncementLatest(params) {
  return request.get('/announcements/latest/', { params })
}

export function getVisibleAnnouncements(params) {
  return request.get('/announcements/visible/', { params })
}
