import { useEffect, useRef, useCallback, useState } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { updatePage } from '../api/pages'
import AutoSaveIndicator from './AutoSaveIndicator'

const TOOLBAR_BUTTONS = [
  { label: 'B', title: 'Bold', action: (e) => e.chain().focus().toggleBold().run(), active: (e) => e.isActive('bold') },
  { label: 'I', title: 'Italic', action: (e) => e.chain().focus().toggleItalic().run(), active: (e) => e.isActive('italic') },
  { label: 'S', title: 'Strike', action: (e) => e.chain().focus().toggleStrike().run(), active: (e) => e.isActive('strike') },
  { label: 'H1', title: 'Heading 1', action: (e) => e.chain().focus().toggleHeading({ level: 1 }).run(), active: (e) => e.isActive('heading', { level: 1 }) },
  { label: 'H2', title: 'Heading 2', action: (e) => e.chain().focus().toggleHeading({ level: 2 }).run(), active: (e) => e.isActive('heading', { level: 2 }) },
  { label: 'H3', title: 'Heading 3', action: (e) => e.chain().focus().toggleHeading({ level: 3 }).run(), active: (e) => e.isActive('heading', { level: 3 }) },
  { label: '•', title: 'Bullet list', action: (e) => e.chain().focus().toggleBulletList().run(), active: (e) => e.isActive('bulletList') },
  { label: '1.', title: 'Ordered list', action: (e) => e.chain().focus().toggleOrderedList().run(), active: (e) => e.isActive('orderedList') },
  { label: '❝', title: 'Blockquote', action: (e) => e.chain().focus().toggleBlockquote().run(), active: (e) => e.isActive('blockquote') },
  { label: '<>', title: 'Code block', action: (e) => e.chain().focus().toggleCodeBlock().run(), active: (e) => e.isActive('codeBlock') },
  { label: '—', title: 'Horizontal rule', action: (e) => e.chain().focus().setHorizontalRule().run(), active: () => false },
  { label: '↩', title: 'Undo', action: (e) => e.chain().focus().undo().run(), active: () => false },
  { label: '↪', title: 'Redo', action: (e) => e.chain().focus().redo().run(), active: () => false },
]

export default function PageEditor({ page }) {
  const [saveStatus, setSaveStatus] = useState(null)
  const saveTimer = useRef(null)

  const save = useCallback(
    async (content) => {
      setSaveStatus('saving')
      try {
        await updatePage(page.id, { content })
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus(null), 2000)
      } catch {
        setSaveStatus('error')
      }
    },
    [page.id]
  )

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: 'Start writing...' }),
    ],
    content: page.content && Object.keys(page.content).length > 0 ? page.content : '',
    onUpdate: ({ editor }) => {
      clearTimeout(saveTimer.current)
      saveTimer.current = setTimeout(() => {
        save(editor.getJSON())
      }, 1000)
    },
  })

  useEffect(() => {
    if (editor && page) {
      const newContent = page.content && Object.keys(page.content).length > 0 ? page.content : ''
      if (JSON.stringify(editor.getJSON()) !== JSON.stringify(newContent)) {
        editor.commands.setContent(newContent, false)
      }
    }
  }, [page.id])

  useEffect(() => () => clearTimeout(saveTimer.current), [])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-100 bg-gray-50 flex-wrap">
        {TOOLBAR_BUTTONS.map((btn) => (
          <button
            key={btn.title}
            title={btn.title}
            onClick={() => btn.action(editor)}
            className={`px-2 py-1 rounded text-sm font-mono transition-colors ${
              editor && btn.active(editor)
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
          >
            {btn.label}
          </button>
        ))}
        <div className="ml-auto">
          <AutoSaveIndicator status={saveStatus} />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        <EditorContent editor={editor} className="tiptap prose max-w-none min-h-full" />
      </div>
    </div>
  )
}
