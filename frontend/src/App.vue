<template>
  <div class="h-screen flex flex-col overflow-hidden bg-zinc-950">
    <!-- Top Bar -->
    <header class="flex items-center gap-3 px-4 py-2.5 border-b border-zinc-800 bg-zinc-900 shrink-0">
      <div class="flex items-center gap-2">
        <img src="/metaden-logo256.png" class="w-7 h-7 rounded-lg" alt="MetaDen" />
        <span class="font-semibold text-zinc-100 tracking-tight">MetaDen</span>
        <span class="text-zinc-600 text-xs">v1.0</span>
      </div>

      <div class="flex-1 flex items-center gap-2 max-w-xl">
        <!-- Back button -->
        <button
          v-if="canGoBack"
          @click="goBack"
          class="btn-ghost text-xs px-2 shrink-0"
          title="Go up one folder"
        >←</button>
        <input
          v-model="folderInput"
          @keydown.enter="openFolder(folderInput)"
          class="input flex-1 text-xs font-mono"
          placeholder="/path/to/movies"
        />
        <button class="btn-primary text-xs" @click="openFolder(folderInput)">Open</button>

      </div>

      <!-- Recent folders -->
      <div v-if="store.config.recently_used_folders?.length" class="relative">
        <button class="btn-ghost text-xs" @click="showRecent = !showRecent">Recent ▾</button>
        <div v-if="showRecent" class="absolute top-full left-0 mt-1 w-80 card z-50 py-1 shadow-xl">
          <button
            v-for="f in store.config.recently_used_folders"
            :key="f"
            class="w-full text-left px-3 py-1.5 text-xs font-mono text-zinc-300 hover:bg-zinc-800 truncate block"
            @click="openFolder(f); showRecent = false"
          >{{ f }}</button>
        </div>
      </div>

      <div class="flex-1" />

      <label class="flex items-center gap-1.5 cursor-pointer select-none">
        <div @click="store.hideRenamed = !store.hideRenamed; store.currentFolder && store.openFolder(store.currentFolder)"
          class="w-8 h-4 rounded-full transition-colors duration-200 relative cursor-pointer"
          :class="store.hideRenamed ? 'bg-indigo-600' : 'bg-zinc-700'">
          <div class="absolute top-0.5 w-3 h-3 bg-white rounded-full shadow transition-transform duration-200"
            :class="store.hideRenamed ? 'translate-x-4' : 'translate-x-0.5'" />
        </div>
        <span class="text-xs text-zinc-400">Hide renamed</span>
      </label>
      <button class="btn-ghost text-xs" @click="store.showUndo = true; store.loadUndoHistory()">Undo History</button>
      <button class="btn-ghost text-xs" @click="store.showSettings = true">⚙ Settings</button>
      <button class="btn-ghost text-xs" @click="showAbout = true">ℹ About</button>
    </header>

    <!-- Main layout -->
    <div class="flex flex-1 overflow-hidden" ref="mainLayout">
      <!-- Left: File list (resizable) -->
      <div :style="{ width: fileListWidth + 'px' }" class="shrink-0 border-r border-zinc-800 overflow-hidden">
        <FileList class="h-full" />
      </div>

      <!-- Resize handle -->
      <div
        class="w-1.5 shrink-0 cursor-col-resize hover:bg-indigo-600/50 active:bg-indigo-600 transition-colors bg-transparent border-r border-zinc-800"
        @mousedown="startResize"
      />

      <!-- Center: Rename panel -->
      <RenamePanel class="flex-1 overflow-hidden" />

      <!-- Right: Movie info + posters -->
      <MoviePanel class="w-72 shrink-0 border-l border-zinc-800" />
    </div>

    <!-- Notification toast -->
    <Transition name="toast">
      <div
        v-if="store.notification"
        class="fixed bottom-4 right-4 z-50 px-4 py-2.5 rounded-lg text-sm font-medium shadow-xl"
        :class="{
          'bg-green-800 text-green-100': store.notification.type === 'success',
          'bg-red-800 text-red-100': store.notification.type === 'error',
          'bg-zinc-700 text-zinc-100': store.notification.type === 'info',
        }"
      >{{ store.notification.message }}</div>
    </Transition>

    <!-- Settings modal -->
    <SettingsModal v-if="store.showSettings" @close="store.showSettings = false" />

    <!-- About modal -->
    <AboutModal v-if="showAbout" @close="showAbout = false" />

    <!-- Undo modal -->
    <UndoModal v-if="store.showUndo" @close="store.showUndo = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useMetaDenStore } from './stores/metaden.js'
import FileList from './components/FileList.vue'
import RenamePanel from './components/RenamePanel.vue'
import MoviePanel from './components/MoviePanel.vue'
import SettingsModal from './components/SettingsModal.vue'
import AboutModal from './components/AboutModal.vue'
import UndoModal from './components/UndoModal.vue'

const store = useMetaDenStore()
const folderInput = ref('')
const showRecent = ref(false)
const showAbout = ref(false)

// Keep folderInput in sync when navigating from FileList
watch(() => store.currentFolder, (val) => {
  if (val) folderInput.value = val
})

const fileListWidth = ref(380)

async function openFolder(path) {
  if (!path) return
  folderInput.value = path
  await store.openFolder(path)
  folderInput.value = store.currentFolder

}

const canGoBack = computed(() => {
  if (!store.currentFolder || !store.rootMediaPath) return false
  return store.currentFolder !== store.rootMediaPath &&
         store.currentFolder.startsWith(store.rootMediaPath + '/')
})

function goBack() {
  const parts = store.currentFolder.split('/')
  parts.pop()
  const parent = parts.join('/') || '/'
  openFolder(parent)
}
const isResizing = ref(false)

function startResize(e) {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = fileListWidth.value

  function onMove(e) {
    const delta = e.clientX - startX
    fileListWidth.value = Math.max(200, Math.min(600, startWidth + delta))
  }

  function onUp() {
    isResizing.value = false
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

onMounted(async () => {
  await store.loadConfig()
  if (store.config.last_folder) {
    folderInput.value = store.config.last_folder
  }
  store.rootMediaPath = '/media'  // always the container mount point
  await store.autoScan()
  if (store.currentFolder) {
    folderInput.value = store.currentFolder
  }
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
