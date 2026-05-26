<template>
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="card w-full max-w-lg max-h-[70vh] flex flex-col shadow-2xl">
      <div class="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <h2 class="font-semibold text-zinc-100">Undo History</h2>
        <button class="text-zinc-600 hover:text-zinc-300 text-lg" @click="$emit('close')">✕</button>
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        <div v-if="!store.undoHistory.length" class="text-zinc-600 text-sm text-center py-8">
          No actions to undo
        </div>
        <div v-else class="space-y-1">
          <div
            v-for="(item, idx) in [...store.undoHistory].reverse()"
            :key="idx"
            class="px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800"
          >
            <div class="text-xs text-zinc-300">{{ item.description }}</div>
            <div class="text-xs text-zinc-600 font-mono mt-0.5">{{ formatTime(item.timestamp) }}</div>
          </div>
        </div>
      </div>

      <div class="flex gap-2 px-5 py-4 border-t border-zinc-800">
        <button class="btn-danger flex-1" @click="doUndo" :disabled="!store.undoHistory.length">
          ↩ Undo Last Action
        </button>
        <button class="btn-ghost" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useMetaDenStore } from '../stores/metaden.js'
const emit = defineEmits(['close'])
const store = useMetaDenStore()

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
