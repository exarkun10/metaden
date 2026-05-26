<template>
  <div class="flex flex-col h-full bg-zinc-950">
    <div class="px-3 py-2 border-b border-zinc-800 flex items-center justify-between shrink-0">
      <span class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Files</span>
      <div class="flex items-center gap-2">
        <button
          class="text-xs px-2 py-0.5 rounded transition-colors"
          :class="store.hideExtras ? 'bg-amber-900 text-amber-300' : 'bg-zinc-800 text-zinc-500'"
          @click="toggleExtras"
          title="Toggle extras folders"
        >extras</button>
        <span class="text-xs text-zinc-600">{{ store.totalFiles }}</span>
      </div>
    </div>

    <div v-if="store.loading.files" class="flex-1 flex items-center justify-center">
      <div class="text-zinc-600 text-sm">Loading…</div>
    </div>

    <!-- Subfolder browser -->
    <div v-else-if="!store.groups.length && store.subfolders.length" class="flex-1 overflow-y-auto py-2 px-2">
      <div class="text-xs text-zinc-600 px-1 mb-2">Select a folder to browse</div>
      <button
        v-for="folder in store.subfolders"
        :key="folder.path"
        @click="navigateToFolder(folder.path)"
        class="w-full text-left px-3 py-2.5 rounded-lg mb-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-600 transition-colors"
      >
        <div class="flex items-center gap-2">
          <span class="text-zinc-500 text-sm">📁</span>
          <span class="text-sm text-zinc-200 flex-1 truncate">{{ folder.name }}</span>
          <span v-if="folder.file_count" class="text-xs text-zinc-600 shrink-0">{{ folder.file_count }}</span>
        </div>
      </button>
    </div>

    <div v-else-if="!store.groups.length" class="flex-1 flex items-center justify-center px-4 text-center">
      <div>
        <div class="text-zinc-700 text-3xl mb-2">📁</div>
        <div class="text-zinc-500 text-xs">Open a folder to begin</div>
      </div>
    </div>

    <div v-else class="flex-1 overflow-y-auto py-1">
      <div v-for="group in store.groups" :key="group.group">

        <!-- Top-level group header (e.g. movies1, movies2) -->
        <button
          v-if="group.group"
          @click="toggleGroup(group.group)"
          class="w-full text-left px-3 py-1.5 flex items-center gap-2 hover:bg-zinc-900 transition-colors"
          :class="isGroupActive(group) ? 'bg-zinc-900' : ''"
        >
          <span class="text-zinc-600 text-xs transition-transform duration-150 shrink-0"
            :class="isExpanded(group.group) ? 'rotate-90' : ''">▶</span>
          <span class="text-xs font-semibold truncate flex-1 text-zinc-300">{{ group.group }}</span>
          <span class="text-xs text-zinc-700 shrink-0">{{ group.file_count }}</span>
        </button>

        <!-- Movies inside this group -->
        <div v-if="!group.group || isExpanded(group.group)">
          <div v-for="movie in group.movies" :key="movie.movie || 'root'">

            <!-- Movie subfolder header (e.g. Jaws (1975)) -->
            <button
              v-if="movie.movie"
              @click="handleMovieClick(movie)"
              class="w-full text-left flex items-center gap-2 hover:bg-zinc-800 transition-colors border-l-2 py-1.5 pr-3"
              :class="[
                isMovieActive(movie) ? 'bg-indigo-950 border-indigo-600' : 'border-transparent',
                group.group ? 'pl-6' : 'pl-3'
              ]"
            >
              <span class="text-zinc-700 text-xs transition-transform duration-150 shrink-0"
                :class="isMovieExpanded(movie.path) ? 'rotate-90' : ''">▶</span>
              <span class="text-xs font-medium truncate flex-1"
                :class="isMovieActive(movie) ? 'text-indigo-300' : 'text-zinc-300'">
                {{ movie.movie }}
              </span>
              <span v-if="movie.has_extras && !store.hideExtras"
                class="text-xs px-1 py-0.5 rounded bg-amber-900/40 text-amber-600 shrink-0 text-[10px]">+ex</span>
              <span class="text-xs text-zinc-700 shrink-0">{{ movie.file_count }}</span>
            </button>

            <!-- Files inside this movie folder -->
            <div v-if="!movie.movie || isMovieExpanded(movie.path)">

              <!-- Main files -->
              <button
                v-for="file in mainFiles(movie)"
                :key="file.path"
                @click="store.selectFile(file)"
                class="w-full text-left transition-colors duration-100 border-l-2 py-1.5 pr-3"
                :class="[
                  isSelected(file) ? 'bg-indigo-950 border-indigo-500' : 'hover:bg-zinc-900 border-transparent',
                  movie.movie ? (group.group ? 'pl-12' : 'pl-9') : (group.group ? 'pl-7' : 'pl-3'),
                ]"
              >
                <div class="flex items-start gap-2">
                  <span class="text-xs px-1.5 py-0.5 rounded font-mono shrink-0 mt-0.5" :class="extColor(file.extension)">
                    {{ file.extension }}
                  </span>
                  <span class="text-xs leading-relaxed break-all" :class="isSelected(file) ? 'text-zinc-100' : 'text-zinc-400'">
                    {{ file.name }}
                  </span>
                </div>
                <div class="text-xs text-zinc-700 mt-0.5 pl-8">{{ formatSize(file.size) }}</div>
              </button>

              <!-- Extras section -->
              <template v-if="!store.hideExtras && extrasFiles(movie).length">
                <div class="flex items-center gap-2 pr-3 py-0.5 mt-0.5"
                  :class="movie.movie ? (group.group ? 'pl-12' : 'pl-9') : (group.group ? 'pl-7' : 'pl-3')">
                  <div class="flex-1 border-t border-zinc-800/60"></div>
                  <span class="text-[10px] text-amber-700/60 italic shrink-0">extras</span>
                  <div class="flex-1 border-t border-zinc-800/60"></div>
                </div>
                <button
                  v-for="file in extrasFiles(movie)"
                  :key="file.path"
                  @click="store.selectFile(file)"
                  class="w-full text-left transition-colors duration-100 border-l-2 py-1 pr-3 opacity-50 hover:opacity-80"
                  :class="[
                    isSelected(file) ? 'bg-indigo-950 border-indigo-500 opacity-100' : 'border-transparent hover:bg-zinc-900',
                    movie.movie ? (group.group ? 'pl-14' : 'pl-11') : (group.group ? 'pl-9' : 'pl-5'),
                  ]"
                >
                  <div class="flex items-start gap-2">
                    <span class="text-xs px-1.5 py-0.5 rounded font-mono shrink-0 mt-0.5" :class="extColor(file.extension)">
                      {{ file.extension }}
                    </span>
                    <span class="text-xs leading-relaxed break-all text-zinc-500">{{ file.name }}</span>
                  </div>
                  <div class="text-xs text-zinc-700 mt-0.5 pl-8">{{ formatSize(file.size) }}</div>
                </button>
              </template>

            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMetaDenStore } from '../stores/metaden.js'
const store = useMetaDenStore()

const expandedGroups = ref(new Set())
const expandedMovies = ref(new Set())

function mainFiles(movie) { return movie.files.filter(f => !f.is_extras) }
function extrasFiles(movie) { return movie.files.filter(f => f.is_extras) }

function toggleGroup(name) {
  if (expandedGroups.value.has(name)) expandedGroups.value.delete(name)
  else expandedGroups.value.add(name)
  expandedGroups.value = new Set(expandedGroups.value)
}

function toggleMovie(path) {
  if (expandedMovies.value.has(path)) expandedMovies.value.delete(path)
  else expandedMovies.value.add(path)
  expandedMovies.value = new Set(expandedMovies.value)
}

function handleMovieClick(movie) {
  const wasExpanded = isMovieExpanded(movie.path)
  toggleMovie(movie.path)
  // Only auto-select main feature when opening, not closing
  if (!wasExpanded && movie.main_feature) {
    store.selectFile(movie.main_feature)
  }
}

function isExpanded(name) { return expandedGroups.value.has(name) }
function isMovieExpanded(path) { return expandedMovies.value.has(path) }
function isSelected(file) { return store.selectedFile?.path === file.path }
function isGroupActive(group) { return store.selectedFile && group.files?.some(f => f.path === store.selectedFile.path) }
function isMovieActive(movie) { return store.selectedFile && movie.files?.some(f => f.path === store.selectedFile.path) }

function navigateToFolder(path) {
  store.openFolder(path)
  store.rootMediaPath = store.rootMediaPath || path
}

function toggleExtras() {
  store.hideExtras = !store.hideExtras
  if (store.currentFolder) store.openFolder(store.currentFolder)
}

const extColor = ext => {
  const map = { mkv: 'bg-blue-900 text-blue-300', mp4: 'bg-green-900 text-green-300', avi: 'bg-yellow-900 text-yellow-300', mov: 'bg-purple-900 text-purple-300' }
  return map[ext] || 'bg-zinc-800 text-zinc-400'
}

const formatSize = bytes => {
  const mb = bytes / 1024 / 1024
  return mb > 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(0)} MB`
}
</script>
