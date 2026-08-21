export const ALLOWED_UPLOAD_EXTENSIONS = ['.md', '.txt', '.pdf', '.docx']
export const UPLOAD_ACCEPT = ALLOWED_UPLOAD_EXTENSIONS.join(',')

const MAX_FILE_SIZE = 10 * 1024 * 1024
const MAX_FILENAME_LENGTH = 255

export const validateUploadFile = (file) => {
  const filename = file?.name?.trim() || ''
  if (!filename) return '文件名不能为空'
  if (Array.from(filename).length > MAX_FILENAME_LENGTH) return '文件名不能超过 255 个字符'

  const dotIndex = filename.lastIndexOf('.')
  const extension = dotIndex >= 0 ? filename.slice(dotIndex).toLowerCase() : ''
  if (!ALLOWED_UPLOAD_EXTENSIONS.includes(extension)) {
    return `仅支持 ${ALLOWED_UPLOAD_EXTENSIONS.join('、')} 文件`
  }
  if (file.size === 0) return '文件内容不能为空'
  if (file.size > MAX_FILE_SIZE) return '文件大小不能超过 10MB'

  return null
}
