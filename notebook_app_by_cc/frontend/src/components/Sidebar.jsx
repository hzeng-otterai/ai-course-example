import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getNotebooks, getNotebook, createNotebook, deleteNotebook, updateNotebook } from '../api/notebooks'
import { createPage, deletePage } from '../api/pages'
import { useAuth } from '../contexts/AuthContext'

export default function Sidebar({ activeNotebookId, activePageId, onSelectPage }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [editingNotebook, setEditingNotebook] = useState(null)
  const [newNotebookTitle, setNewNotebookTitle] = useState('')
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 250)
    return () => clearTimeout(timer)
  }, [query])

  const { data: notebooks = [] } = useQuery({
    queryKey: ['notebooks', debouncedQuery],
    queryFn: () => getNotebooks(debouncedQuery ? { search: debouncedQuery } : undefined).then((r) => r.data),
  })

  const createNotebookMutation = useMutation({
    mutationFn: () => createNotebook({ title: 'New Notebook' }),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      navigate(`/notebooks/${data.id}`)
    },
  })

  const deleteNotebookMutation = useMutation({
    mutationFn: (id) => deleteNotebook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      navigate('/')
    },
  })

  const renameNotebookMutation = useMutation({
    mutationFn: ({ id, title }) => updateNotebook(id, { title }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notebooks'] }),
  })

  const createPageMutation = useMutation({
    mutationFn: (notebookId) => createPage(notebookId, { title: 'Untitled' }),
    onSuccess: ({ data }, notebookId) => {
      queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
      onSelectPage(data.id)
    },
  })

  const deletePageMutation = useMutation({
    mutationFn: (id) => deletePage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebook', activeNotebookId] })
      onSelectPage(null)
    },
  })

  const activeNotebook = notebooks.find((n) => n.id === Number(activeNotebookId))

  const { data: notebookDetail } = useQuery({
    queryKey: ['notebook', activeNotebookId],
    queryFn: () => getNotebook(activeNotebookId).then((r) => r.data),
    enabled: !!activeNotebookId,
  })

  const pages = notebookDetail?.pages ?? []

  const handleRenameNotebook = (nb) => {
    if (newNotebookTitle.trim() && newNotebookTitle !== nb.title) {
      renameNotebookMutation.mutate({ id: nb.id, title: newNotebookTitle.trim() })
    }
    setEditingNotebook(null)
  }

  return (
    <aside className="w-64 bg-gray-900 text-gray-200 flex flex-col h-screen flex-shrink-0">
      <div className="px-4 py-4 border-b border-gray-700">
        <span className="text-white font-semibold text-lg">Notebooks</span>
        <p className="text-gray-400 text-xs mt-0.5 truncate">{user?.username}</p>
      </div>

      <div className="px-3 py-2 border-b border-gray-700">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search notebooks..."
          className="w-full bg-gray-800 text-gray-200 text-sm rounded-lg px-3 py-1.5 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="px-3 pt-3 pb-1">
          <button
            onClick={() => createNotebookMutation.mutate()}
            className="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <span className="text-lg leading-none">+</span> New notebook
          </button>
        </div>

        {notebooks.length === 0 && debouncedQuery && (
          <p className="px-4 py-3 text-xs text-gray-500">No notebooks found.</p>
        )}

        {notebooks.map((nb) => (
          <div key={nb.id}>
            <div
              className={`flex items-center group px-3 py-0.5 mx-1 rounded-lg cursor-pointer ${
                nb.id === Number(activeNotebookId)
                  ? 'bg-gray-700 text-white'
                  : 'hover:bg-gray-800 text-gray-300'
              }`}
            >
              {editingNotebook === nb.id ? (
                <input
                  autoFocus
                  value={newNotebookTitle}
                  onChange={(e) => setNewNotebookTitle(e.target.value)}
                  onBlur={() => handleRenameNotebook(nb)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameNotebook(nb)
                    if (e.key === 'Escape') setEditingNotebook(null)
                  }}
                  className="flex-1 bg-transparent text-sm outline-none py-1.5"
                />
              ) : (
                <Link
                  to={`/notebooks/${nb.id}`}
                  className="flex-1 text-sm py-1.5 truncate"
                >
                  {nb.title}
                </Link>
              )}

              <div className="hidden group-hover:flex items-center gap-1 ml-1">
                <button
                  title="Rename"
                  onClick={() => { setEditingNotebook(nb.id); setNewNotebookTitle(nb.title) }}
                  className="p-1 text-gray-500 hover:text-gray-200"
                >
                  ✎
                </button>
                <button
                  title="Delete"
                  onClick={() => {
                    if (confirm(`Delete "${nb.title}"?`)) deleteNotebookMutation.mutate(nb.id)
                  }}
                  className="p-1 text-gray-500 hover:text-red-400"
                >
                  ✕
                </button>
              </div>
            </div>

            {nb.id === Number(activeNotebookId) && (
              <div className="ml-4 mt-1 mb-2 border-l border-gray-700 pl-3">
                {pages.map((pg) => (
                  <PageItem
                    key={pg.id}
                    page={pg}
                    active={pg.id === activePageId}
                    onSelect={() => onSelectPage(pg.id)}
                    onDelete={() => {
                      if (confirm(`Delete "${pg.title}"?`)) deletePageMutation.mutate(pg.id)
                    }}
                  />
                ))}
                <button
                  onClick={() => createPageMutation.mutate(nb.id)}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 py-1 mt-1"
                >
                  <span>+</span> New page
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="px-4 py-3 border-t border-gray-700">
        <button
          onClick={logout}
          className="text-xs text-gray-500 hover:text-gray-300"
        >
          Sign out
        </button>
      </div>
    </aside>
  )
}

function PageItem({ page, active, onSelect, onDelete }) {
  return (
    <div
      className={`flex items-center group rounded px-2 py-1 cursor-pointer text-sm ${
        active ? 'text-white bg-gray-700' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
      }`}
      onClick={onSelect}
    >
      <span className="flex-1 truncate">{page.title || 'Untitled'}</span>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete() }}
        className="hidden group-hover:block p-0.5 text-gray-600 hover:text-red-400"
        title="Delete page"
      >
        ✕
      </button>
    </div>
  )
}
