<template>
  <div class="flex flex-col h-full bg-zinc-950">
    <div class="px-3 py-2 border-b border-zinc-800 flex items-center justify-between">
      <span class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Posters</span>
      <span v-if="store.posters.length" class="text-xs text-zinc-600">{{ store.posters.length }}</span>
    </div>

    <!-- No movie selected -->
    <div v-if="!store.movieDetails && !store.loading.posters" class="flex-1 flex items-center justify-center">
      <div class="text-zinc-700 text-xs text-center px-4">Select a movie to browse posters</div>
    </div>

    <!-- Loading -->
    <div v-else-if="store.loading.posters" class="flex-1 flex items-center justify-center">
      <div class="text-zinc-600 text-xs">Loading posters…</div>
    </div>

    <!-- No posters -->
    <div v-else-if="store.posters.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-zinc-700 text-xs text-center px-4">No posters found on TMDB</div>
    </div>

    <!-- Poster grid -->
    <div v-else class="flex-1 overflow-y-auto p-2">
      <!-- Selected poster preview -->
      <div v-if="store.selectedPosterUrl" class="mb-2 rounded-lg overflow-hidden border-2 border-indigo-500">
        <img :src="store.selectedPosterUrl" class="w-full object-cover" alt="Selected poster" />
        <div class="bg-indigo-900/50 px-2 py-1 text-xs text-indigo-300 text-center">✓ Selected</div>
      </div>

      <!-- Poster thumbnails -->
      <div class="grid grid-cols-2 gap-1.5">
        <button
          v-for="(poster, idx) in store.posters"
          :key="idx"
          @click="selectPoster(poster)"
          class="relative rounded-md overflow-hidden border-2 transition-all duration-100 aspect-[2/3]"
          :class="isSelected(poster)
            ? 'border-indigo-500'
            : 'border-transparent hover:border-zinc-600'"
        >
          <img
            :src="poster.thumb"
            class="w-full h-full object-cover"
            :alt="`Poster ${idx + 1}`"
            loading="lazy"
          />
          <!-- Language badge for non-English posters -->
          <div v-if="poster.lang && poster.lang !== 'en'"
            class="absolute top-1 left-1 bg-black/70 text-zinc-300 text-xs px-1.5 py-0.5 rounded font-mono uppercase">
            {{ poster.lang }}
          </div>
          <div v-if="isSelected(poster)"
            class="absolute inset-0 bg-indigo-600/20 flex items-center justify-center">
            <span class="text-white text-lg">✓</span>
          </div>
        </button>
      </div>

      <!-- Clear poster option -->
      <button
        v-if="store.selectedPosterUrl"
        class="mt-2 w-full btn-ghost text-xs"
        @click="store.selectedPosterUrl = null"
      >✕ Don't download poster</button>
    </div>
  </div>
</template>

<script setup>
import { useMetaDenStore } from '../stores/metaden.js'
const store = useMetaDenStore()

function selectPoster(poster) {
  store.selectedPosterUrl = poster.full
}

function isSelected(poster) {
  return store.selectedPosterUrl === poster.full
}
</script>
