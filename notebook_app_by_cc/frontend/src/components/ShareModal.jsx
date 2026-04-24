import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createShare, revokeShare } from '../api/pages'

export default function ShareModal({ page, notebookId, onClose }) {
  const queryClient = useQueryClient()
  const [copied, setCopied] = useState(false)

  const shareUrl = page.share_token
    ? `${window.location.origin}/shared/${page.share_token}`
    : null

  const shareMutation = useMutation({
    mutationFn: () => createShare(page.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
      queryClient.invalidateQueries({ queryKey: ['page', page.id] })
    },
  })

  const revokeMutation = useMutation({
    mutationFn: () => revokeShare(page.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
      queryClient.invalidateQueries({ queryKey: ['page', page.id] })
    },
  })

  const copyLink = () => {
    navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Share page</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Anyone with the link can view this page without signing in.
        </p>

        {shareUrl ? (
          <>
            <div className="flex gap-2 mb-4">
              <input
                readOnly
                value={shareUrl}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700"
              />
              <button
                onClick={copyLink}
                className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap"
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <button
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
              className="text-sm text-red-500 hover:text-red-700 disabled:opacity-50"
            >
              {revokeMutation.isPending ? 'Revoking...' : 'Revoke link'}
            </button>
          </>
        ) : (
          <button
            onClick={() => shareMutation.mutate()}
            disabled={shareMutation.isPending}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors"
          >
            {shareMutation.isPending ? 'Generating...' : 'Generate share link'}
          </button>
        )}
      </div>
    </div>
  )
}
