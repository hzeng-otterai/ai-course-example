import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getNotebooks, createNotebook } from '../api/notebooks'

export default function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: notebooks = [], isLoading } = useQuery({
    queryKey: ['notebooks'],
    queryFn: () => getNotebooks().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => createNotebook({ title: 'New Notebook' }),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      navigate(`/notebooks/${data.id}`)
    },
  })

  useEffect(() => {
    if (!isLoading && notebooks.length > 0) {
      navigate(`/notebooks/${notebooks[0].id}`, { replace: true })
    }
  }, [isLoading, notebooks])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>
    )
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center">
        <div className="text-5xl mb-4">📓</div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">No notebooks yet</h1>
        <p className="text-gray-500 mb-6">Create your first notebook to get started.</p>
        <button
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {createMutation.isPending ? 'Creating...' : 'Create notebook'}
        </button>
      </div>
    </div>
  )
}
