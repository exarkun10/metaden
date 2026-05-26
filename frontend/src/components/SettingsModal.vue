<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="closeWithConfirm">
    <div class="card w-full max-w-2xl shadow-2xl">

      <div class="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <h2 class="font-semibold text-zinc-100">Settings</h2>
        <div class="flex items-center gap-3">
          <span v-if="isDirty" class="text-xs text-amber-500 italic">unsaved changes</span>
          <button class="text-zinc-600 hover:text-zinc-300 text-lg" @click="closeWithConfirm">✕</button>
        </div>
      </div>

      <div ref="scrollContainer" class="overflow-y-auto p-5 space-y-6 max-h-[75vh]">

        <!-- Unsaved changes banner -->
        <div v-if="isDirty" class="bg-indigo-950 border border-indigo-700 rounded-lg px-3 py-2 text-xs text-indigo-300 flex items-center gap-2">
          <span>●</span> Unsaved changes — scroll down to save, or close to auto-save
        </div>

        <!-- Rename format -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Rename Format</h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-zinc-400 block mb-1">Default format</label>
              <input v-model="local.rename_format" class="input w-full font-mono text-xs" @input="markDirty" />
            </div>
            <div class="flex flex-wrap gap-1.5 text-xs">
              <span v-for="t in tokens" :key="t" class="font-mono bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-400 cursor-pointer hover:bg-zinc-700"
                @click="insertToken(t)">{{ t }}</span>
            </div>
            <div class="text-xs text-zinc-600">Click a token to insert it at cursor, or type it directly.</div>

            <!-- AKA — behind advanced toggle -->
            <div>
              <button @click="showAka = !showAka"
                class="text-xs text-zinc-600 hover:text-zinc-400 flex items-center gap-1 transition-colors">
                <span :class="showAka ? 'rotate-90' : ''" class="inline-block transition-transform">▶</span>
                Advanced — AKA format
              </button>
              <div v-if="showAka" class="mt-3 space-y-3 pl-3 border-l border-zinc-700">
                <div class="flex items-center gap-3">
                  <div @click="local.use_aka_format = !local.use_aka_format; markDirty()"
                    class="w-9 h-5 rounded-full transition-colors duration-200 relative cursor-pointer shrink-0"
                    :class="local.use_aka_format ? 'bg-indigo-600' : 'bg-zinc-700'">
                    <div class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200"
                      :class="local.use_aka_format ? 'translate-x-4' : 'translate-x-0.5'" />
                  </div>
                  <span class="text-sm text-zinc-300">Enable AKA format</span>
                </div>
                <div v-if="local.use_aka_format">
                  <label class="text-xs text-zinc-400 block mb-1">AKA format string</label>
                  <input v-model="local.rename_aka_format" class="input w-full font-mono text-xs" @input="markDirty" />
                  <div class="text-xs text-zinc-600 mt-1">Used when a movie has a known alternate title. If disabled, default format is always used.</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Options -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Options</h3>
          <div class="space-y-2">
            <label v-for="(label, key) in booleans" :key="key" class="flex items-center gap-3 cursor-pointer group">
              <div @click="toggleBoolean(key)"
                class="w-9 h-5 rounded-full transition-colors duration-200 relative cursor-pointer shrink-0"
                :class="local[key] ? 'bg-indigo-600' : 'bg-zinc-700'">
                <div class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200"
                  :class="local[key] ? 'translate-x-4' : 'translate-x-0.5'" />
              </div>
              <span class="text-sm text-zinc-300 group-hover:text-zinc-100 transition-colors leading-snug">{{ label }}</span>
            </label>
          </div>
        </section>

        <!-- Resolution scanning info -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Resolution Scanning</h3>
          <div class="bg-zinc-800/50 border border-zinc-700 rounded-lg px-3 py-2.5 text-xs text-zinc-400 leading-relaxed space-y-1">
            <p>When enabled, MetaDen uses ffprobe to read the actual video resolution from the file header when you select a file and populates <span class="font-mono text-zinc-300 bg-zinc-700 px-1 rounded">&lt;scanres&gt;</span> in the filename.</p>
            <p class="text-zinc-600">No transcoding — reads metadata only, ~100ms per file. If disabled, <span class="font-mono">&lt;scanres&gt;</span> is silently removed from the output filename.</p>
          </div>
        </section>

        <!-- Movie extensions -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Movie Extensions</h3>
          <input v-model="extensionsStr" class="input w-full text-xs font-mono" placeholder="mkv,mp4,avi,..." @input="markDirty" />
          <div class="text-xs text-zinc-600 mt-1">Comma-separated list of extensions to scan</div>
        </section>

        <!-- Separators -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Separators</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-zinc-400 block mb-1">Saved part separator</label>
              <input v-model="local.saved_part_separator" class="input w-full font-mono text-xs" maxlength="5" @input="markDirty" />
            </div>
            <div>
              <label class="text-xs text-zinc-400 block mb-1">Replace title spaces with</label>
              <input v-model="local.replace_spaces_with" class="input w-full font-mono text-xs" maxlength="5" placeholder="(leave blank to keep spaces)" @input="markDirty" />
            </div>
          </div>
        </section>

        <!-- Recent folders -->
        <section>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Recent Folders</h3>
          <div v-if="!local.recently_used_folders?.length" class="text-xs text-zinc-600">No recent folders.</div>
          <div v-else class="space-y-1 mb-3">
            <div v-for="(f, idx) in local.recently_used_folders" :key="f"
              class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-zinc-800 border border-zinc-700">
              <span class="text-xs font-mono text-zinc-300 flex-1 truncate">{{ f }}</span>
              <button @click="removeRecent(idx)" class="text-zinc-600 hover:text-red-400 text-xs shrink-0">✕</button>
            </div>
          </div>
          <button v-if="local.recently_used_folders?.length" @click="clearRecents"
            class="btn-danger text-xs w-full">Clear All Recent Folders</button>
        </section>

        <!-- Actions -->
        <div class="space-y-2 pt-2 border-t border-zinc-800">
<button class="btn-primary w-full" @click="save">Save Settings</button>
          <button class="btn-ghost w-full text-xs" @click="confirmReset = true; scrollToBottom()">Restore to Defaults</button>
        </div>

        <!-- Unsaved changes confirm -->
        <div v-if="showUnsavedConfirm" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div class="card w-full max-w-sm shadow-2xl p-6 space-y-4">
            <div class="text-sm font-medium text-zinc-100">Save changes before closing?</div>
            <div class="text-xs text-zinc-400">You have unsaved changes in Settings.</div>
            <div class="flex gap-2">
              <button class="btn-primary flex-1 text-xs" @click="saveAndClose">Save & Close</button>
              <button class="btn-ghost flex-1 text-xs" @click="discardAndClose">Discard</button>
            </div>
            <button class="text-xs text-zinc-600 hover:text-zinc-400 w-full text-center" @click="showUnsavedConfirm = false">Cancel — keep editing</button>
          </div>
        </div>

        <!-- Restore confirm -->
        <div v-if="confirmReset" class="bg-red-950 border border-red-800 rounded-lg p-4 space-y-3">
          <div class="text-sm text-red-200 font-medium">Restore all settings to defaults?</div>
          <div class="text-xs text-red-400">This will reset your rename format, options, and extensions. Recent folders will be kept.</div>
          <div class="flex gap-2">
            <button class="btn-danger flex-1 text-xs" @click="restoreDefaults">Yes, restore defaults</button>
            <button class="btn-ghost flex-1 text-xs" @click="confirmReset = false">Cancel</button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useMetaDenStore } from '../stores/metaden.js'
const emit = defineEmits(['close'])
const store = useMetaDenStore()

const local = ref({ ...store.config, recently_used_folders: [...(store.config.recently_used_folders || [])] })
const showAka = ref(false)
const confirmReset = ref(false)
const isDirty = ref(false)
const showUnsavedConfirm = ref(false)
const formatInputRef = ref(null)
const scrollContainer = ref(null)

function scrollToBottom() {
  setTimeout(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  }, 50)
}

// On open: if scan_resolution is already enabled but <scanres> is missing from format, add it
if (local.value.scan_resolution && !local.value.rename_format?.includes('<scanres>')) {
  local.value.rename_format = (local.value.rename_format || '').replace(/\.?$/, '') + '.<scanres>'
}

function markDirty() { isDirty.value = true }

const booleans = {
  download_posters: 'Download posters',
  create_url_file: 'Create .url file',
  rename_folder: 'Also rename containing folder',
  scan_resolution: 'Scan file for resolution — uses ffprobe to detect and populate <scanres>',
  remove_the: 'Remove "The" from title',
  swap_the: 'Swap "The" to end (e.g. "Matrix, The")',
}

const tokens = ['<title>', '<year>', '<imdb>', '<rating>', '<rating100>', '<scanres>', '<directors>', '<genres>', '<stars>']

const extensionsStr = computed({
  get: () => (local.value.movie_extensions || []).join(','),
  set: v => { local.value.movie_extensions = v.split(',').map(s => s.trim()).filter(Boolean); markDirty() }
})

function insertToken(token) {
  local.value.rename_format = (local.value.rename_format || '') + token
  markDirty()
}

function toggleBoolean(key) {
  local.value[key] = !local.value[key]
  markDirty()
  if (key === 'scan_resolution') {
    if (local.value.scan_resolution) {
      if (!local.value.rename_format?.includes('<scanres>')) {
        local.value.rename_format = (local.value.rename_format || '').replace(/\.?$/, '') + '.<scanres>'
      }
    } else {
      local.value.rename_format = (local.value.rename_format || '')
        .replace(/\.?<scanres>/g, '')
        .replace(/\.{2,}/g, '.')
        .replace(/\.$/, '')
    }
  }
}

function removeRecent(idx) {
  local.value.recently_used_folders.splice(idx, 1)
  markDirty()
}

function clearRecents() {
  local.value.recently_used_folders = []
  markDirty()
}

const DEFAULT_CONFIG = {
  rename_format: '<title> (<year>).<imdb>',
  rename_aka_format: '<aka> (<title>) (<year>).<imdb>',
  download_posters: true,
  create_url_file: true,
  rename_folder: false,
  scan_resolution: false,
  remove_the: false,
  swap_the: false,
  replace_spaces_with: '',
  saved_part_separator: '.',
  movie_extensions: ['mkv','avi','wmv','mp4','m4v','mov','ts','m2ts','ogm','mpg','mpeg','flv','iso'],
}

function restoreDefaults() {
  const recent = local.value.recently_used_folders
  Object.assign(local.value, DEFAULT_CONFIG)
  local.value.recently_used_folders = recent
  confirmReset.value = false
  markDirty()
}

async function save() {
  await store.saveConfig(local.value)
  isDirty.value = false
}

function closeWithConfirm() {
  if (isDirty.value) {
    showUnsavedConfirm.value = true
  } else {
    emit('close')
  }
}

async function saveAndClose() {
  await store.saveConfig(local.value)
  isDirty.value = false
  emit('close')
}

function discardAndClose() {
  isDirty.value = false
  showUnsavedConfirm.value = false
  emit('close')
}
</script>
