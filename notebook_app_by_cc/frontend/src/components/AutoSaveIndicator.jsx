export default function AutoSaveIndicator({ status }) {
  if (status === 'saving') {
    return <span className="text-xs text-gray-400">Saving...</span>
  }
  if (status === 'saved') {
    return <span className="text-xs text-green-500">Saved</span>
  }
  if (status === 'error') {
    return <span className="text-xs text-red-500">Save failed</span>
  }
  return null
}
