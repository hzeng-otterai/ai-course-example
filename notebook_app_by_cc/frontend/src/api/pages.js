import client from './client'

export const getPages = (notebookId) => client.get(`/notebooks/${notebookId}/pages/`)
export const createPage = (notebookId, data) => client.post(`/notebooks/${notebookId}/pages/`, data)
export const getPage = (id) => client.get(`/pages/${id}/`)
export const updatePage = (id, data) => client.patch(`/pages/${id}/`, data)
export const deletePage = (id) => client.delete(`/pages/${id}/`)
export const createShare = (id) => client.post(`/pages/${id}/share/`)
export const revokeShare = (id) => client.delete(`/pages/${id}/share/`)
export const getSharedPage = (token) => client.get(`/shared/${token}/`)
