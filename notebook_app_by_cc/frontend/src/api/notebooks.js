import client from './client'

export const getNotebooks = (params) => client.get('/notebooks/', { params })
export const getNotebook = (id) => client.get(`/notebooks/${id}/`)
export const createNotebook = (data) => client.post('/notebooks/', data)
export const updateNotebook = (id, data) => client.patch(`/notebooks/${id}/`, data)
export const deleteNotebook = (id) => client.delete(`/notebooks/${id}/`)
