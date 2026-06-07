import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const useMetaDenStore = defineStore('metaden', () => {
  // ── State ──────────────────────────────────────────────────────────────────
  const currentFolder = ref('')
  const files = ref([])
  const selectedFile = ref(null)
  const fileParts = ref([])
  const foundTT = ref(null)
  const foundYear = ref(null)

  const searchResults = ref([])
  const selectedMovie = ref(null)
  const movieDetails = ref(null)
  const posters = ref([])
  const selectedPosterUrl = ref(null)

  const newFilename = ref('')
  const config = ref({})
  const groups = ref([])
  const totalFiles = ref(0)
  const hideExtras = ref(false)
  const loading = ref({ files: false, search: false, movie: false, rename: false, posters: false, subtitles: false, subtitleDownload: null })

  // Subtitle state
  const subtitleResults = ref([])
  const subtitleSearchTerm = ref('')
  const subtitleSearched = ref(false)
  const notification = ref(null)
  const showSettings = ref(false)
  const showUndo = ref(false)
  const undoHistory = ref([])
  const hideRenamed = ref(true)
  const scanResolution = ref('')
  const subfolders = ref([])
  const rootMediaPath = ref('')

  // ── Actions ────────────────────────────────────────────────────────────────
  async function loadConfig() {
    const { data } = await api.get('/config')
    config.value = data
  }

  async function autoScan() {
    try {
      const { data } = await api.get('/media-path')
      if (data.media_path) {
        await openFolder(data.media_path)
        return
      }
    } catch (e) {}
    if (config.value.last_folder) {
      await openFolder(config.value.last_folder)
    }
  }

  async function saveConfig(updates) {
    await api.post('/config', { config: updates })
    await loadConfig()
    notify('Settings saved', 'success')
  }

  async function openFolder(folder) {
    loading.value.files = true
    try {
      const [filesRes, foldersRes] = await Promise.all([
        api.get('/files', { params: { folder, recursive: false, hide_renamed: hideRenamed.value, hide_extras: hideExtras.value } }),
        api.get('/folders', { params: { path: folder } }),
      ])
      currentFolder.value = folder
      groups.value = filesRes.data.groups || []
      totalFiles.value = filesRes.data.total_files || 0
      files.value = (filesRes.data.groups || []).flatMap(g => g.files)
      subfolders.value = foldersRes.data.folders || []
      selectedFile.value = null
      fileParts.value = []
      searchResults.value = []
      selectedMovie.value = null
      movieDetails.value = null
      posters.value = []
      newFilename.value = ''
      // save recently used
      const recent = config.value.recently_used_folders || []
      if (!recent.includes(folder)) {
        recent.unshift(folder)
        if (recent.length > 10) recent.pop()
        await saveConfig({ recently_used_folders: recent, last_folder: folder })
      }
    } catch (e) {
      notify(e.response?.data?.detail || 'Could not open folder', 'error')
    } finally {
      loading.value.files = false
    }
  }

  async function selectFile(file) {
    selectedFile.value = file
    selectedMovie.value = null
    movieDetails.value = null
    posters.value = []
    selectedPosterUrl.value = null
    newFilename.value = ''
    searchResults.value = []
    subtitleResults.value = []
    subtitleSearchTerm.value = ''
    subtitleSearched.value = false

    // Parse the filename
    const { data } = await api.get('/parse', { params: { path: file.path } })
    fileParts.value = data.parts
    foundTT.value = data.tt
    foundYear.value = data.year

    // Auto-search first
    await doSearch()

    // Reload config fresh before checking scan_resolution
    await loadConfig()

    // Probe resolution after search so refreshPreview gets the scanres value
    scanResolution.value = ''
    if (config.value.scan_resolution) {
      try {
        const { data: probeData } = await api.get('/probe', { params: { path: file.path } })
        scanResolution.value = probeData.label || ''
        // Re-run preview with the now-populated scanres
        await refreshPreview()
      } catch (e) {}
    }
  }

  async function doSearch(customQuery = null) {
    loading.value.search = true
    searchResults.value = []
    try {
      let query = customQuery
      if (!query) {
        query = fileParts.value
          .filter(p => p.state === 'part')
          .map(p => p.part)
          .join(' ')
      }
      if (!query.trim()) return
      const { data } = await api.get('/search', { params: { query } })
      searchResults.value = data.results
      if (data.results.length > 0) {
        await selectMovie(data.results[0])
      }
    } catch (e) {
      notify('Search failed', 'error')
    } finally {
      loading.value.search = false
    }
  }

  async function selectMovie(movie) {
    selectedMovie.value = movie
    loading.value.movie = true
    try {
      const { data } = await api.get(`/movie/${movie.tt}`)
      movieDetails.value = data
      selectedMovie.value = data
      await refreshPreview()
      await loadPosters(movie.tt)
    } catch (e) {
      notify('Could not load movie details', 'error')
    } finally {
      loading.value.movie = false
    }
  }

  async function loadPosters(tt) {
    loading.value.posters = true
    posters.value = []
    try {
      const { data } = await api.get(`/posters/${tt}`)
      posters.value = data.posters
      if (data.posters.length > 0) {
        selectedPosterUrl.value = data.posters[0].full
      }
    } catch (e) {
      // silently fail
    } finally {
      loading.value.posters = false
    }
  }

  async function refreshPreview() {
    if (!selectedFile.value || !movieDetails.value) return
    try {
      const movieWithRes = { ...movieDetails.value, scanres: scanResolution.value }
      const { data } = await api.post('/preview-rename', {
        original_path: selectedFile.value.path,
        movie: movieWithRes,
        parts: [],
        use_aka: config.value.use_aka_format || false,
      })
      newFilename.value = data.new_name
    } catch (e) {
      // ignore
    }
  }

  async function doRename() {
    if (!selectedFile.value || !newFilename.value) return
    loading.value.rename = true
    try {
      // Build folder name = new filename stem (without extension)
      const folderName = newFilename.value.replace(/\.[^.]+$/, '')
      // Get original folder name for release_info.txt
      const originalPath = selectedFile.value.path
      const pathParts = originalPath.split('/')
      const originalFolderName = pathParts.length > 2 ? pathParts[pathParts.length - 2] : ''
      await api.post('/rename', {
        original_path: selectedFile.value.path,
        new_name: newFilename.value,
        poster_url: selectedPosterUrl.value,
        create_url_file: config.value.create_url_file,
        movie_tt: movieDetails.value?.tt,
        folder_name: folderName,
        original_folder_name: originalFolderName,
      })
      notify(`Renamed to ${newFilename.value}`, 'success')
      // Refresh the folder to get updated paths
      await openFolder(currentFolder.value)
      // Auto-search subtitles if key is configured
      if (subtitlesAvailable.value) {
        await doSubtitleSearch()
      }
    } catch (e) {
      notify(e.response?.data?.detail || 'Rename failed', 'error')
    } finally {
      loading.value.rename = false
    }
  }

  async function doSkip() {
    if (!selectedFile.value) return
    const idx = files.value.findIndex(f => f.path === selectedFile.value.path)
    if (idx < files.value.length - 1) {
      await selectFile(files.value[idx + 1])
    }
  }

  async function doUndo() {
    try {
      const { data } = await api.post('/undo')
      notify(`Undone: ${data.description}`, 'success')
      await openFolder(currentFolder.value)
    } catch (e) {
      notify(e.response?.data?.detail || 'Undo failed', 'error')
    }
  }

  async function loadUndoHistory() {
    const { data } = await api.get('/undo-history')
    undoHistory.value = data.history
  }

  function updatePartState(idx, state) {
    const part = fileParts.value[idx]
    const wasSearch = part.state === 'part'
    part.state = state

    // Auto-add to release groups if manually removed and not already a known noise word
    if (state === 'remove' && wasSearch) {
      const term = part.part.toUpperCase()
      const cfg = config.value
      const allKnown = [
        ...(cfg.noise_codecs  || []),
        ...(cfg.noise_sources || []),
        ...(cfg.noise_audio   || []),
        ...(cfg.noise_groups  || []),
      ].map(t => t.toUpperCase())

      const isYear = /^(19|20)\d{2}$/.test(term)
      const isRes  = /^(4K|2160P?|1080P?|720P?|480P?|576P?|8K|UHD|HD|FHD|QHD)$/.test(term)

      if (!allKnown.includes(term) && !isYear && !isRes) {
        const groups = [...(cfg.noise_groups || []), term]
        saveConfig({ ...cfg, noise_groups: groups })
        notify('🔇 "' + part.part + '" added to Release Groups', 'info')
      }
    }

    refreshPreview()
  }

  async function doSubtitleSearch() {
    if (!selectedFile.value) return
    loading.value.subtitles = true
    subtitleResults.value = []
    subtitleSearched.value = false
    try {
      const folder = selectedFile.value.path.split('/').slice(0, -1).join('/')
      const lang = config.value.subtitle_language || 'en'
      const { data } = await api.get('/subtitles/search', { params: { folder, language: lang } })
      subtitleResults.value = data.results
      subtitleSearchTerm.value = data.search_term
      subtitleSearched.value = true
    } catch (e) {
      notify(e.response?.data?.detail || 'Subtitle search failed', 'error')
    } finally {
      loading.value.subtitles = false
    }
  }

  async function doSubtitleDownload(sub) {
    if (!selectedFile.value || !movieDetails.value) return
    loading.value.subtitleDownload = sub.file_id
    try {
      const folder = selectedFile.value.path.split('/').slice(0, -1).join('/')
      // Build movie stem from current filename (strip extension)
      const stem = selectedFile.value.name.replace(/\.[^.]+$/, '')
      const { data } = await api.post('/subtitles/download', {
        folder,
        file_id: sub.file_id,
        movie_stem: stem,
        language: sub.language,
        match_type: sub.match_type,
        release_name: sub.release,
      })
      notify(`Downloaded: ${data.filename}`, 'success')
    } catch (e) {
      notify(e.response?.data?.detail || 'Subtitle download failed', 'error')
    } finally {
      loading.value.subtitleDownload = null
    }
  }

  function notify(message, type = 'info') {
    notification.value = { message, type }
    setTimeout(() => { notification.value = null }, 3500)
  }

  // ── Computed ───────────────────────────────────────────────────────────────
  const searchQuery = computed(() =>
    fileParts.value.filter(p => p.state === 'part').map(p => p.part).join(' ')
  )

  const subtitlesAvailable = computed(() => !!config.value.has_opensubtitles_key)

  return {
    currentFolder, files, selectedFile, fileParts, foundTT, foundYear,
    searchResults, selectedMovie, movieDetails, posters, selectedPosterUrl,
    newFilename, config, loading, notification, showSettings, showUndo, undoHistory,
    searchQuery, hideRenamed, groups, totalFiles, hideExtras, scanResolution, subfolders, rootMediaPath,
    loadConfig, saveConfig, openFolder, autoScan, selectFile, doSearch, selectMovie,
    refreshPreview, doRename, doSkip, doUndo, updatePartState, notify,
    loadUndoHistory, doSubtitleSearch, doSubtitleDownload,
    subtitleResults, subtitleSearchTerm, subtitleSearched, subtitlesAvailable,
  }
})
