import client from './client'
import axios from 'axios'

export const register = (data) => client.post('/auth/register/', data)
export const login = (data) => axios.post('/api/auth/login/', data)
export const getMe = () => client.get('/auth/me/')
