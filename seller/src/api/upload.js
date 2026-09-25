import request from '@/utils/request'

export function uploadImage(file, scope = 'products') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scope', scope)
  return request.post('/upload/image/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
