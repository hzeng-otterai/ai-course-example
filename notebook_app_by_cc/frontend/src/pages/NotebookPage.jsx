import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getNotebook, updateNotebook } from '../api/notebooks'
import { getPage, updatePage } from '../api/pages'
import Sidebar from '../components/Sidebar'
import PageEditor from '../components/PageEditor'
import ShareModal from '../components/ShareModal'

export default function NotebookPage() {
  const { id: notebookId } = useParams()
  const queryClient = useQueryClient()
  const [activePageId, setActivePageId] = useState(null)
  const [showShare, setShowShare] = useState(false)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleInput, setTitleInput] = useState('')

  const { data: notebook } = useQuery({
    queryKey: ['notebook', notebookId],
    queryFn: () => getNotebook(notebookId).then((r) => r.data),
  })

  const { data: activePage } = useQuery({
    queryKey: ['page', activePageId],
    queryFn: () => getPage(activePageId).then((r) => r.data),
    enabled: !!activePageId,
  })

  useEffect(() => {
    if (notebook?.pages?.length > 0 && !activePageId) {
      setActivePageId(notebook.pages[0].id)
    }
  }, [notebook])

  useEffect(() => {
    setActivePageId(null)
  }, [notebookId])

  const renameMutation = useMutation({
    mutationFn: (title) => updateNotebook(notebookId, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
    },
  })

  const renamePage = useMutation({
    mutationFn: ({ id, title }) => updatePage(id, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
      queryClient.invalidateQueries({ queryKey: ['page', activePageId] })
    },
  })

  const handleRenameNotebook = () => {
    if (titleInput.trim() && titleInput !== notebook?.title) {
      renameMutation.mutate(titleInput.trim())
    }
    setEditingTitle(false)
  }

  const handlePageTitleKeyDown = (e, page) => {
    if (e.key === 'Enter') {
      renamePage.mutate({ id: page.id, title: e.target.value })
      e.target.blur()
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        activeNotebookId={notebookId}
        activePageId={activePageId}
        onSelectPage={setActivePageId}
      />

      <main className="flex-1 flex flex-col min-w-0 bg-white">
        {activePage ? (
          <>
            <header className="flex items-center gap-3 px-6 py-3 border-b border-gray-100">
              {editingTitle ? (
                <input
                  autoFocus
                  value={titleInput}
                  onChange={(e) => setTitleInput(e.target.value)}
                  onBlur={handleRenameNotebook}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleRenameNotebook(); if (e.key === 'Escape') setEditingTitle(false) }}
                  className="text-sm font-medium text-gray-700 border-b border-indigo-400 outline-none px-1"
                />
              ) : (
                <button
                  onClick={() => { setEditingTitle(true); setTitleInput(notebook?.title ?? '') }}
                  className="text-sm text-gray-500 hover:text-gray-800"
                  title="Rename notebook"
                >
                  {notebook?.title}
                </button>
              )}
              <span className="text-gray-300">/</span>
              <input
                key={activePage.id}
                defaultValue={activePage.title}
                onKeyDown={(e) => handlePageTitleKeyDown(e, activePage)}
                onBlur={(e) => renamePage.mutate({ id: activePage.id, title: e.target.value })}
                className="text-sm font-semibold text-gray-800 outline-none border-b border-transparent focus:border-indigo-400 px-1"
              />
              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => setShowShare(true)}
                  className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                  {activePage.share_token ? 'Shared' : 'Share'}
                </button>
              </div>
            </header>

            <div className="flex-1 overflow-hidden">
              <PageEditor key={activePage.id} page={activePage} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-4xl mb-3">📄</div>
              <p className="text-sm">Select a page or create one in the sidebar</p>
            </div>
          </div>
        )}
      </main>

      {showShare && activePage && (
        <ShareModal
          page={activePage}
          notebookId={notebookId}
          onClose={() => { setShowShare(false); queryClient.invalidateQueries({ queryKey: ['page', activePageId] }) }}
        />
      )}
    </div>
  )
}
