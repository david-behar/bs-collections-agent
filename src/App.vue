<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { API, type CaseDetail, type CaseSummary } from './Api'

const cases = ref<CaseSummary[]>([])
const casesLoading = ref(true)
const caseLoading = ref(false)
const errorMessage = ref('')
const activeCaseId = ref('')
const caseDetail = ref<CaseDetail | null>(null)
const activeAttachmentId = ref<string | null>(null)
const isEditing = ref(false)
const editedResponse = ref('')
const showRejectForm = ref(false)
const rejectComment = ref('')
const toastMessage = ref('')
const toastVisible = ref(false)
const toastTimer = ref<ReturnType<typeof setTimeout> | null>(null)

const activeCase = computed(() => cases.value.find((item) => item.case_id === activeCaseId.value) ?? null)
const attachments = computed(() => caseDetail.value?.attachments ?? [])
const activeAttachment = computed(() =>
  attachments.value.find((file) => file.type === activeAttachmentId.value) ?? null
)

const communicationParagraphs = computed(() => {
  const raw = caseDetail.value?.email_body ?? ''
  return raw
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
})

const loadCases = async () => {
  casesLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await API.listCases()
    cases.value = data.cases
    if (data.cases.length) {
      activeCaseId.value = data.cases[0].case_id
      await loadCaseDetail(activeCaseId.value)
    }
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Unable to load cases'
  } finally {
    casesLoading.value = false
  }
}

const loadCaseDetail = async (caseId: string) => {
  if (!caseId) return
  caseLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await API.getCase(caseId)
    caseDetail.value = data
    activeAttachmentId.value = data.attachments[0]?.type ?? null
    editedResponse.value = data.llm_output ?? ''
    isEditing.value = false
    showRejectForm.value = false
    rejectComment.value = ''
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Unable to load case details'
  } finally {
    caseLoading.value = false
  }
}

const selectCase = async (caseId: string) => {
  if (!caseId || caseId === activeCaseId.value) return
  activeCaseId.value = caseId
  await loadCaseDetail(caseId)
}

const selectAttachment = (docType: string) => {
  activeAttachmentId.value = docType
}

onMounted(loadCases)

watch(
  () => caseDetail.value?.llm_output,
  (val) => {
    if (!isEditing.value) {
      editedResponse.value = val ?? ''
    }
  },
  { immediate: true }
)

const triggerToast = (message: string) => {
  toastMessage.value = message
  toastVisible.value = true
  if (toastTimer.value) {
    clearTimeout(toastTimer.value)
  }
  toastTimer.value = setTimeout(() => {
    toastVisible.value = false
    toastTimer.value = null
  }, 3200)
}

const sendEmail = () => {
  const target = caseDetail.value?.company || 'customer'
  triggerToast(`Email sent to ${target}.`)
}

const startEditing = () => {
  if (!caseDetail.value) return
  editedResponse.value = caseDetail.value?.llm_output ?? ''
  isEditing.value = true
}

const saveEditedResponse = () => {
  if (!caseDetail.value) return
  caseDetail.value = { ...caseDetail.value, llm_output: editedResponse.value }
  isEditing.value = false
  triggerToast('Draft updated.')
}

const cancelEdit = () => {
  isEditing.value = false
  editedResponse.value = caseDetail.value?.llm_output ?? ''
}

const openRejectForm = () => {
  if (!caseDetail.value) return
  showRejectForm.value = true
}

const cancelReject = () => {
  showRejectForm.value = false
  rejectComment.value = ''
}

const submitReject = () => {
  if (!rejectComment.value.trim()) {
    triggerToast('Please add a short note before submitting.')
    return
  }
  showRejectForm.value = false
  rejectComment.value = ''
  triggerToast('Feedback saved for follow-up.')
}

onUnmounted(() => {
  if (toastTimer.value) {
    clearTimeout(toastTimer.value)
  }
})

const fallbackResponseHtml = '<p>AI response will appear here once it has been generated.</p>'
</script>

<template>
  <div class="app-shell">
    <header class="page-header">
      <div>
        <p class="eyebrow">Collections Agent</p>
        <h1>Dispute workspace</h1>
        <p class="subtitle">Review prior communication, finalize the response, and double-check supporting PDFs.</p>
      </div>
      <div class="badge">Demo data</div>
    </header>

    <section class="panel summary-panel">
      <div class="case-switcher">
        <label>Dispute cases</label>
        <div class="case-buttons">
          <button
            v-for="caseItem in cases"
            :key="caseItem.case_id"
            type="button"
            :class="{ active: caseItem.case_id === activeCaseId }"
            :disabled="casesLoading"
            @click="selectCase(caseItem.case_id)"
          >
            <strong>{{ caseItem.case_id }}</strong>
            <span>{{ caseItem.company || 'Unnamed company' }}</span>
            <small>{{ caseItem.email_excerpt || 'No description yet' }}</small>
          </button>
        </div>
        <p class="helper" v-if="casesLoading">Loading cases…</p>
      </div>
      <div class="summary-stat">
        <span class="label">Selected case</span>
        <strong>{{ activeCase?.case_id || '—' }}</strong>
      </div>
      <div class="summary-stat">
        <span class="label">Company</span>
        <strong>{{ activeCase?.company || '—' }}</strong>
      </div>
      <div class="summary-stat">
        <span class="label">Attachments</span>
        <strong>{{ activeCase?.attachments ?? attachments.length }}</strong>
      </div>
      <div class="summary-stat">
        <span class="label">Status</span>
        <strong>{{ caseLoading ? 'Loading…' : 'Ready' }}</strong>
        <p class="helper">Data refreshed live</p>
      </div>
    </section>

    <section v-if="errorMessage" class="panel state-card error">
      <p>{{ errorMessage }}</p>
      <button type="button" class="retry" @click="loadCases">Try again</button>
    </section>

    <section class="content-grid">
      <article class="panel communication-panel">
        <header>
          <div>
            <p class="eyebrow">Past communication</p>
            <h2>Customer notes</h2>
          </div>
          <span v-if="caseLoading">Loading…</span>
        </header>
        <div v-if="caseLoading" class="state-card inline">Fetching latest email threads…</div>
        <div class="communication-body" v-else-if="communicationParagraphs.length">
          <p v-for="paragraph in communicationParagraphs" :key="paragraph">{{ paragraph }}</p>
        </div>
        <p v-else class="empty-copy">No past communication captured for this case.</p>
      </article>

      <article class="panel response-panel">
        <header>
          <div>
            <p class="eyebrow">Proposed answer</p>
            <h2>AI-generated draft</h2>
          </div>
          <span v-if="caseDetail?.company">Target: {{ caseDetail.company }}</span>
        </header>
        <div class="action-bar">
          <button type="button" class="btn primary" :disabled="caseLoading || !caseDetail" @click="sendEmail">
            Send
          </button>
          <button
            type="button"
            class="btn secondary"
            :disabled="caseLoading || !caseDetail || isEditing"
            @click="startEditing"
          >
            Edit
          </button>
          <button
            type="button"
            class="btn ghost"
            :disabled="caseLoading || !caseDetail || showRejectForm"
            @click="openRejectForm"
          >
            Reject
          </button>
        </div>
        <div v-if="caseLoading" class="state-card inline">Loading the proposed response…</div>
        <template v-else>
          <div v-if="isEditing" class="editor-card">
            <label for="response-editor">Edit email body</label>
            <textarea id="response-editor" v-model="editedResponse" rows="10"></textarea>
            <div class="editor-actions">
              <button type="button" class="btn primary" @click="saveEditedResponse">Save draft</button>
              <button type="button" class="btn ghost" @click="cancelEdit">Cancel</button>
            </div>
          </div>
          <article v-else class="email-body" v-html="caseDetail?.llm_output || fallbackResponseHtml"></article>
        </template>
        <footer class="hint">HTML is rendered directly from the LLM output stored in the dataset.</footer>
        <div v-if="showRejectForm" class="reject-card">
          <label for="reject-reason">Why is this draft not acceptable?</label>
          <textarea id="reject-reason" v-model="rejectComment" rows="4" placeholder="Add quick feedback for the agent."></textarea>
          <div class="editor-actions">
            <button type="button" class="btn secondary" @click="submitReject">Submit</button>
            <button type="button" class="btn ghost" @click="cancelReject">Cancel</button>
          </div>
        </div>
      </article>
    </section>

    <section class="panel attachments-panel">
      <header>
        <div>
          <p class="eyebrow">Attachments</p>
          <h2>Supporting PDFs</h2>
        </div>
        <span>{{ attachments.length }} files</span>
      </header>
      <div v-if="caseLoading" class="state-card inline">Retrieving attachment links…</div>
      <template v-else>
        <div v-if="attachments.length" class="attachments-grid">
          <ul class="attachment-list">
            <li v-for="file in attachments" :key="file.type">
              <button type="button" :class="{ active: file.type === activeAttachmentId }" @click="selectAttachment(file.type)">
                <div>
                  <strong>{{ file.label }}</strong>
                  <p>{{ file.filename }}</p>
                </div>
                <small>{{ file.type.toUpperCase() }}</small>
              </button>
            </li>
          </ul>

          <div class="attachment-preview" v-if="activeAttachment">
            <div class="preview-label">Preview</div>
            <h3>{{ activeAttachment.label }}</h3>
            <p>{{ activeAttachment.filename }}</p>
            <iframe :src="activeAttachment.download_url" title="PDF preview" frameborder="0"></iframe>
            <a :href="activeAttachment.download_url" target="_blank" rel="noopener" class="open-link">Open in new tab</a>
          </div>
        </div>
        <p v-else class="empty-copy">No attachments are stored for this case.</p>
      </template>
    </section>
    <transition name="toast-fade">
      <div v-if="toastVisible" class="toast">{{ toastMessage }}</div>
    </transition>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  gap: 28px;
  color: var(--color-text);
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 32px 64px;
}

.app-shell strong {
  color: var(--color-text-strong);
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  background: var(--color-panel-elevated);
  border-radius: 24px;
  padding: 28px;
  border: 1px solid var(--color-border);
  box-shadow: 0 25px 50px rgba(1, 6, 22, 0.4);
  backdrop-filter: blur(18px);
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: 2rem;
  letter-spacing: -0.02em;
}

.subtitle {
  color: var(--color-text-muted);
  margin-top: 6px;
}

.badge {
  align-self: flex-start;
  border-radius: 999px;
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  font-size: 0.85rem;
  background: rgba(100, 233, 200, 0.12);
  color: var(--color-accent);
}

.panel {
  background: var(--color-panel-elevated);
  border: 1px solid var(--color-border);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 45px rgba(2, 8, 24, 0.35);
  backdrop-filter: blur(18px);
}

.summary-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.case-switcher {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-switcher label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.case-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.case-buttons button {
  flex: 1;
  min-width: 200px;
  border-radius: 16px;
  border: 1px solid var(--color-border);
  padding: 12px 16px;
  text-align: left;
  cursor: pointer;
  background: var(--color-background-mute);
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--color-text);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.case-buttons button:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.05);
}

.case-buttons button.active {
  border-color: var(--color-accent);
  background: rgba(100, 233, 200, 0.18);
}

.case-buttons small {
  color: var(--color-text-muted);
}

.summary-stat .label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.helper {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 4px 0 0;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.communication-panel header,
.response-panel header,
.attachments-panel header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: baseline;
}

.communication-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.communication-body p {
  margin: 0;
}

.email-body {
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 16px;
  min-height: 200px;
  color: var(--color-text);
}

.email-body :deep(strong) {
  color: var(--color-text-strong);
  font-weight: 600;
}

.email-body :deep(.header) {
  background: transparent !important;
  background-color: transparent !important;
}

.email-body :deep(.evidence-box) {
  background: transparent !important;
  background-color: transparent !important;
}

.hint {
  margin-top: 12px;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.attachments-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 16px 0 20px;
}

.btn {
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 10px 20px;
  font-weight: 600;
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--color-accent);
  color: #03231b;
  border-color: transparent;
}

.btn.primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.btn.secondary {
  background: rgba(122, 177, 255, 0.15);
  border-color: rgba(122, 177, 255, 0.6);
}

.btn.ghost {
  background: transparent;
}

.editor-card,
.reject-card {
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 16px;
  background: var(--color-background-mute);
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.editor-card label,
.reject-card label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.editor-card textarea,
.reject-card textarea {
  width: 100%;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  padding: 12px;
  background: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
  resize: vertical;
}

.editor-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.attachments-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.45fr) 1fr;
  gap: 18px;
}

.attachment-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attachment-list button {
  width: 100%;
  border-radius: 18px;
  border: 1px solid var(--color-border);
  padding: 16px;
  text-align: left;
  background: var(--color-background-mute);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--color-text);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.attachment-list button.active {
  border-color: var(--color-accent);
  background: rgba(100, 233, 200, 0.16);
}

.attachment-preview {
  border: 1px solid var(--color-border);
  border-radius: 20px;
  padding: 20px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--color-background-mute);
}

.preview-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-text-muted);
}

.attachment-preview iframe {
  flex: 1;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: #fff;
  width: 100%;
  min-height: 260px;
}

.open-link {
  text-align: right;
  font-weight: 600;
  color: var(--color-accent);
}

.state-card {
  border-radius: 18px;
  border: 1px dashed var(--color-border);
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.state-card.inline {
  width: 100%;
  text-align: center;
  justify-content: center;
}

.state-card.error {
  border-color: rgba(255, 139, 116, 0.5);
  color: var(--color-danger);
}

.retry {
  border: none;
  border-radius: 999px;
  padding: 8px 18px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
  cursor: pointer;
}

.empty-copy {
  color: var(--color-text-muted);
  margin: 0;
}

.toast {
  position: fixed;
  right: 32px;
  bottom: 32px;
  background: var(--color-panel-elevated);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 900px) {
  .app-shell {
    padding: 32px 20px 48px;
  }

  .page-header {
    flex-direction: column;
  }

  .case-buttons {
    flex-direction: column;
  }

  .attachments-grid {
    grid-template-columns: 1fr;
  }
}
</style>
