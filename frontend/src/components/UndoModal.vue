<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="card w-full max-w-lg max-h-[75vh] flex flex-col shadow-2xl">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <h2 class="font-semibold text-zinc-100">History</h2>
        <button class="text-zinc-600 hover:text-zinc-300 text-lg" @click="$emit('close')">✕</button>
      </div>

      <div class="flex-1 overflow-y-auto">

        <!-- Last undoable action -->
        <div v-if="lastAction" class="px-5 py-4 border-b border-zinc-700">
          <div class="flex items-center justify-between gap-3">
            <div class="min-w-0">
              <div class="text-[10px] text-zinc-500 uppercase tracking-wide font-medium mb-1">Last Action</div>
              <div class="text-xs text-zinc-200">{{ lastAction.description }}</div>
              <div class="text-[10px] text-zinc-600 font-mono mt-0.5">{{ formatTime(lastAction.timestamp) }}</div>
            </div>
            <button class="btn-danger shrink-0 text-xs px-3 py-1.5" @click="doUndo">↩ Undo</button>
          </div>
        </div>
        <div v-else class="px-5 py-4 border-b border-zinc-700 text-zinc-600 text-xs">
          No actions to undo
        </div>

        <!-- History log -->
        <div class="px-5 py-3">
          <div class="text-[10px] text-zinc-500 uppercase tracking-wide font-medium mb-2">History</div>
          <div v-if="historyItems.length === 0" class="text-zinc-600 text-xs py-2">No history yet</div>
          <div v-else class="space-y-1">
            <div
              v-for="(item, idx) in historyItems"
              :key="idx"
              class="px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800"
            >
              <div class="text-xs text-zinc-400">{{ item.description }}</div>
              <div class="text-[10px] text-zinc-600 font-mono mt-0.5">{{ formatTime(item.timestamp) }}</div>
            </div>
          </div>
        </div>

      </div>

      <div class="flex justify-end px-5 py-4 border-t border-zinc-800">
        <button class="btn-ghost" @click="$emit('close')">Close</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMetaDenStore } from '../stores/metaden.js'
const emit = defineEmits(['close'])
const store = useMetaDenStore()

// Last item is the undoable action, everything before it is read-only history
const lastAction = computed(() => {
  const h = store.undoHistory
  return h.length ? h[h.length - 1] : null
})

const historyItems = computed(() => {
  const h = store.undoHistory
  return h.length > 1 ? [...h.slice(0, -1)].reverse() : []
})

async function doUndo() {
  await store.doUndo()
  await store.loadUndoHistory()
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
</script>
