<template>
  <div class="flex flex-col h-full">
    <!-- Empty state -->
    <div v-if="!store.selectedFile" class="flex-1 flex items-center justify-center text-center px-8">
      <div>
        <svg width="96" height="96" viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg" class="mx-auto mb-5 opacity-60">
          <!-- Clapboard body -->
          <rect x="8" y="28" width="80" height="60" rx="5" fill="#27272a" stroke="#52525b" stroke-width="2"/>
          <!-- Inner lines -->
          <line x1="8" y1="50" x2="88" y2="50" stroke="#3f3f46" stroke-width="1.5"/>
          <line x1="8" y1="65" x2="88" y2="65" stroke="#3f3f46" stroke-width="1.5"/>
          <!-- Text lines suggesting metadata -->
          <rect x="18" y="56" width="30" height="3" rx="1.5" fill="#52525b"/>
          <rect x="18" y="71" width="42" height="3" rx="1.5" fill="#52525b"/>
          <rect x="56" y="56" width="18" height="3" rx="1.5" fill="#52525b"/>
          <!-- Clapper top -->
          <rect x="8" y="16" width="80" height="16" rx="3" fill="#3f3f46" stroke="#52525b" stroke-width="2"/>
          <!-- Clapper stripes -->
          <clipPath id="clipClapper">
            <rect x="8" y="16" width="80" height="16" rx="3"/>
          </clipPath>
          <g clip-path="url(#clipClapper)">
            <rect x="8"  y="16" width="12" height="16" fill="#27272a"/>
            <rect x="20" y="16" width="12" height="16" fill="#a1a1aa"/>
            <rect x="32" y="16" width="12" height="16" fill="#27272a"/>
            <rect x="44" y="16" width="12" height="16" fill="#a1a1aa"/>
            <rect x="56" y="16" width="12" height="16" fill="#27272a"/>
            <rect x="68" y="16" width="12" height="16" fill="#a1a1aa"/>
            <rect x="80" y="16" width="12" height="16" fill="#27272a"/>
          </g>
          <!-- Hinge -->
          <rect x="14" y="13" width="6" height="6" rx="1" fill="#6366f1"/>
          <rect x="76" y="13" width="6" height="6" rx="1" fill="#6366f1"/>
        </svg>
        <div class="text-zinc-400 text-sm">Select a file from the list to begin renaming</div>
      </div>
    </div>

    <template v-else>
      <!-- File info bar -->
      <div class="px-4 py-2.5 border-b border-zinc-800 bg-zinc-900 shrink-0">
        <div class="flex items-center gap-2 text-xs">
          <span class="text-zinc-500">Original:</span>
          <span class="font-mono text-zinc-300 truncate">{{ store.selectedFile.name }}</span>
          <span class="ml-auto text-zinc-600 shrink-0">{{ formatSize(store.selectedFile.size) }}</span>
        </div>
      </div>

      <!-- Parts editor -->
      <div class="px-4 py-3 border-b border-zinc-800 shrink-0">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs text-zinc-500 font-medium">Search parts</span>
          <div class="flex-1" />
          <button class="btn-ghost text-xs" @click="store.doSearch()">
            <span v-if="store.loading.search" class="opacity-60">Searching…</span>
            <span v-else>↺ Search Again</span>
          </button>
        </div>
        <div class="flex flex-wrap gap-1.5 min-h-[2rem]">
          <div
            v-for="(part, idx) in store.fileParts"
            :key="idx"
            class="part-pill relative group"
          >
            <button
              @click="cyclePart(idx)"
              class="px-2.5 py-1 rounded-md text-xs font-medium font-mono transition-colors duration-100 border"
              :class="partClass(part.state)"
              :title="`Click to cycle state (${part.state})`"
            >{{ part.part }}</button>
            <span class="absolute -top-1 -right-1 w-3 h-3 rounded-full text-[8px] flex items-center justify-center hidden group-hover:flex"
              :class="stateIndicator(part.state)">
              {{ stateIcon(part.state) }}
            </span>
          </div>
        </div>
        <div class="mt-1.5 flex gap-4 text-[10px] text-zinc-600">
          <span><span class="inline-block w-2 h-2 rounded bg-indigo-700 mr-1"></span>search</span>
          <span><span class="inline-block w-2 h-2 rounded bg-amber-800 mr-1"></span>keep</span>
          <span><span class="inline-block w-2 h-2 rounded bg-zinc-700 mr-1"></span>remove</span>
        </div>
      </div>

      <!-- Search results -->
      <div class="px-4 py-3 border-b border-zinc-800 shrink-0">
        <div class="text-xs text-zinc-500 font-medium mb-2">Search results</div>
        <div v-if="store.loading.search" class="text-xs text-zinc-600">Searching IMDB…</div>
        <div v-else-if="!store.searchResults.length" class="text-xs text-zinc-600">No results found.</div>
        <div v-else class="flex gap-2 flex-wrap">
          <button
            v-for="m in store.searchResults"
            :key="m.tt"
            @click="store.selectMovie(m)"
            class="px-3 py-1.5 rounded-lg text-xs border transition-all duration-100"
            :class="isSelectedMovie(m)
              ? 'bg-indigo-700 border-indigo-500 text-white'
              : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500'"
          >
            {{ m.title }} <span class="text-zinc-400">({{ m.year }})</span>
          </button>
        </div>
      </div>

      <!-- Movie details -->
      <div v-if="store.movieDetails" class="px-4 py-3 border-b border-zinc-800 shrink-0 bg-zinc-900/50">
        <div v-if="store.loading.movie" class="text-xs text-zinc-600">Loading…</div>
        <div v-else class="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
          <div class="col-span-2 text-sm font-semibold text-zinc-100 mb-1">
            {{ store.movieDetails.title }}
            <span class="text-zinc-500 font-normal ml-1">({{ store.movieDetails.year }})</span>
            <span class="ml-2 text-zinc-600 font-mono text-xs">{{ store.movieDetails.tt }}</span>
          </div>
          <div v-if="store.movieDetails.rating" class="flex gap-2">
            <span class="text-zinc-600">Rating</span>
            <span class="text-amber-400">★ {{ (store.movieDetails.rating / 10).toFixed(1) }}</span>
          </div>
          <div v-if="store.movieDetails.director" class="flex gap-2 truncate">
            <span class="text-zinc-600 shrink-0">Director</span>
            <span class="text-zinc-300 truncate">{{ store.movieDetails.director }}</span>
          </div>
          <div v-if="store.movieDetails.genres" class="flex gap-2">
            <span class="text-zinc-600">Genre</span>
            <span class="text-zinc-300">{{ store.movieDetails.genres }}</span>
          </div>
          <div v-if="store.movieDetails.duration" class="flex gap-2">
            <span class="text-zinc-600">Duration</span>
            <span class="text-zinc-300">{{ store.movieDetails.duration }} min</span>
          </div>
          <div v-if="store.movieDetails.mpaa" class="flex gap-2">
            <span class="text-zinc-600">Rated</span>
            <span class="text-zinc-300">{{ store.movieDetails.mpaa }}</span>
          </div>
          <div v-if="store.movieDetails.star1" class="col-span-2 flex gap-2 truncate">
            <span class="text-zinc-600 shrink-0">Stars</span>
            <span class="text-zinc-300 truncate">{{ store.movieDetails.stars }}</span>
          </div>
          <div v-if="store.scanResolution" class="flex gap-2">
            <span class="text-zinc-600">Resolution</span>
            <span class="text-emerald-400 font-mono font-medium">{{ store.scanResolution }}</span>
          </div>
        </div>
      </div>

      <!-- New filename + actions -->
      <div class="px-4 py-3 mt-auto border-t border-zinc-800 shrink-0">
        <div class="text-xs text-zinc-500 mb-1.5 font-medium">New filename</div>
        <input
          v-model="store.newFilename"
          class="input w-full font-mono text-xs mb-3"
          placeholder="New filename will appear here…"
        />
        <div class="flex gap-2">
          <button
            class="btn-primary flex-1"
            :disabled="!store.newFilename || store.loading.rename"
            @click="store.doRename()"
          >
            <span v-if="store.loading.rename">Renaming…</span>
            <span v-else>✓ Rename</span>
          </button>
          <button class="btn-ghost" @click="store.doSkip()">Skip →</button>
          <button class="btn-danger" @click="store.doUndo()">↩ Undo</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useMetaDenStore } from '../stores/metaden.js'
const store = useMetaDenStore()

const STATES = ['part', 'keep', 'remove']

function cyclePart(idx) {
  const cur = store.fileParts[idx].state
  const next = STATES[(STATES.indexOf(cur) + 1) % STATES.length]
  store.updatePartState(idx, next)
}

function partClass(state) {
  return {
    part: 'bg-indigo-950 border-indigo-700 text-indigo-300 hover:border-indigo-500',
    keep: 'bg-amber-950 border-amber-700 text-amber-300 hover:border-amber-500',
    remove: 'bg-zinc-800 border-zinc-700 text-zinc-500 line-through hover:border-zinc-500',
  }[state] || ''
}

function stateIndicator(state) {
  return {
    part: 'bg-indigo-600',
    keep: 'bg-amber-600',
    remove: 'bg-zinc-600',
  }[state] || ''
}

function stateIcon(state) {
  return { part: '?', keep: '✓', remove: '×' }[state] || ''
}

function isSelectedMovie(m) {
  return store.selectedMovie?.tt === m.tt
}

function formatSize(bytes) {
  const mb = bytes / 1024 / 1024
  return mb > 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(0)} MB`
}
</script>
