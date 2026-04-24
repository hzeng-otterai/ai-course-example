import client from './client'

export const getNotebooks = () => client.get('/notebooks/')
export const getNotebook = (id) => client.get(`/notebooks/${id}/`)
export const createNotebook = (data) => client.post('/notebooks/', data)
export const updateNotebook = (id, data) => client.patch(`/notebooks/${id}/`, data)
export const deleteNotebook = (id) => client.delete(`/notebooks/${id}/`)
