import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { getSharedPage } from '../api/pages'

function ReadOnlyEditor({ content }) {
  const editor = useEditor({
    extensions: [StarterKit],
    content: content && Object.keys(content).length > 0 ? content : '',
    editable: false,
  })

  return <EditorContent editor={editor} className="tiptap prose max-w-none" />
}

export default function SharedPageView() {
  const { token } = useParams()

  const { data: page, isLoading, isError } = useQuery({
    queryKey: ['shared', token],
    queryFn: () => getSharedPage(token).then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-gray-400">Loading...</div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-5xl mb-4">🔒</div>
          <h1 className="text-xl font-semibold text-gray-700 mb-2">Link not found</h1>
          <p className="text-gray-500 mb-4 text-sm">This link may have expired or been revoked.</p>
          <Link to="/login" className="text-indigo-600 hover:underline text-sm">
            Sign in to Notebooks
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="mb-2 text-xs text-gray-400 uppercase tracking-wide">
          {page.notebook_title}
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{page.title}</h1>
        <p className="text-xs text-gray-400 mb-8">
          Last updated {new Date(page.updated_at).toLocaleDateString()}
        </p>
        <ReadOnlyEditor content={page.content} />
      </div>

      <footer className="text-center py-8 border-t border-gray-100 mt-16">
        <Link to="/register" className="text-sm text-indigo-600 hover:underline">
          Create your own notebook →
        </Link>
      </footer>
    </div>
  )
}
