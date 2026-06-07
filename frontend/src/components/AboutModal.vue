<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="card w-full max-w-lg shadow-2xl">

      <div class="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <h2 class="font-semibold text-zinc-100">About MetaDen</h2>
        <button class="text-zinc-600 hover:text-zinc-300 text-lg" @click="$emit('close')">✕</button>
      </div>

      <div class="p-6 space-y-5">

        <!-- Logo + version -->
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-xl bg-indigo-600 flex items-center justify-center text-2xl font-bold text-white shrink-0">M</div>
          <div>
            <div class="text-lg font-semibold text-zinc-100">MetaDen</div>
            <div class="text-sm text-zinc-500">v{{ version }} — Self-hosted movie file renamer</div>
            <div class="text-xs text-zinc-600 mt-0.5">Built for Unraid · Docker · MIT License</div>
          </div>
        </div>

        <!-- Description -->
        <p class="text-sm text-zinc-400 leading-relaxed">
          MetaDen scans your media library, searches IMDB for metadata, downloads posters from TMDB,
          and renames your files using a configurable format. Runs as a single Docker container.
        </p>

        <!-- Origins -->
        <div class="bg-zinc-800/50 border border-zinc-700 rounded-lg px-4 py-3 space-y-1">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Origins</div>
          <p class="text-xs text-zinc-400 leading-relaxed">
            Inspired by <span class="text-zinc-200">Zeeb</span>, originally created by
            <span class="text-zinc-200">slaingod</span> — a desktop application built on Adobe AIR and ActionScript.
            MetaDen is a ground-up reimplementation using modern technologies: FastAPI, Vue 3, Tailwind CSS, and Docker.
          </p>
        </div>

        <!-- Links -->
        <div class="space-y-2">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Links</div>
          <div class="flex flex-col gap-2">
            <a href="https://github.com/exarkun10/metaden" target="_blank"
              class="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
              github.com/exarkun10/metaden
            </a>
            <a href="https://hub.docker.com/r/exarkun10/metaden" target="_blank"
              class="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.186.186 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288z"/></svg>
              hub.docker.com/r/exarkun10/metaden
            </a>
          </div>
        </div>

        <!-- License -->
        <div class="bg-zinc-800/30 border border-zinc-800 rounded-lg px-4 py-3">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">License</div>
          <p class="text-xs text-zinc-500 leading-relaxed">
            MIT License — Copyright © 2026 exarkun10. Free to use, modify, and distribute with attribution.
          </p>
        </div>

      </div>

      <div class="px-5 py-4 border-t border-zinc-800">
        <button class="btn-ghost w-full text-sm" @click="$emit('close')">Close</button>
      </div>

    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])
const version = '1.0'
</script>
