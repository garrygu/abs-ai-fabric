<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDemoControlStore } from '@/stores/demoControlStore'

const demoControl = useDemoControlStore()

const selectedChallenge = ref<string | null>(null)
const showKiosk = ref(false)
const outputDisplayRef = ref<HTMLElement | null>(null)
const selectedPromptIndex = ref<number | null>(null) // Track which prompt was clicked

function handleShowKiosk() {
  showKiosk.value = true
}

onMounted(() => {
  window.addEventListener('show-prompt-kiosk', handleShowKiosk)
})

onUnmounted(() => {
  window.removeEventListener('show-prompt-kiosk', handleShowKiosk)
})

// Challenge definitions with prompt chips
const challenges = {
  'reasoning': {
    title: 'Reasoning Challenge',
    model: 'DeepSeek R1 70B',
    description: 'Conflicting constraints → recommendation',
    explanation: 'This model analyzes complex scenarios, identifies trade-offs, and provides reasoned recommendations.',
    exampleContext: 'Example scenario: Your company needs to launch a new AI-powered product within 6 months to stay competitive. You have a budget of $2M, but initial estimates show you need $3.5M. Additionally, the product must comply with GDPR, HIPAA, and SOC 2 requirements. The engineering team is already at 90% capacity. You also need to consider: market timing (competitor launching in 7 months), technical risk (using new AI frameworks), and stakeholder expectations (board wants quarterly revenue). What should you do?',
    prompts: [
      { text: 'Give the safest recommendation', hint: 'Get a conservative, risk-averse suggestion for this scenario' },
      { text: 'List key assumptions', hint: 'Identify what must be true for the analysis to hold (e.g., market conditions, resource availability)' },
      { text: 'What breaks if assumption #2 fails?', hint: 'Explore failure scenarios and dependencies (e.g., what if budget is cut?)' },
      { text: 'Second-order risks', hint: 'Find risks that arise from the initial risks (e.g., delayed launch → market share loss)' },
      { text: 'Compare trade-offs', hint: 'Weigh pros and cons of different approaches (e.g., fast launch vs. thorough testing)' },
      { text: 'Identify blind spots', hint: 'Discover what might be overlooked or missing (e.g., competitor response, supply chain)' }
    ]
  },
  'explanation': {
    title: 'Executive Explanation',
    model: 'LLaMA-3 70B',
    description: 'Explain it to a business leader',
    explanation: 'This model translates technical or complex information into clear, business-friendly language.',
    exampleContext: 'Example scenario: Your engineering team has proposed migrating from a monolithic architecture to microservices, implementing Kubernetes orchestration, and adopting a new AI model serving framework (vLLM). The technical team estimates 6 months and $500K. The CTO needs to explain this to the CEO and board, who are non-technical but care about: business impact, ROI, risks, timeline, and competitive advantage. How do you explain this decision?',
    prompts: [
      { text: 'Explain in simple terms', hint: 'Break down complex concepts (e.g., microservices, AI models) for non-technical audiences' },
      { text: 'What are the business implications?', hint: 'Focus on how this affects the business (e.g., cost, time, competitive advantage)' },
      { text: 'What\'s the bottom line?', hint: 'Get a concise summary of key outcomes (e.g., ROI, timeline, risk level)' },
      { text: 'What are the risks?', hint: 'Identify potential problems or downsides (e.g., technical debt, vendor lock-in)' },
      { text: 'What are the opportunities?', hint: 'Highlight potential benefits or advantages (e.g., scalability, innovation)' },
      { text: 'Make it actionable', hint: 'Provide concrete next steps or recommendations (e.g., approve budget, form team)' }
    ]
  },
  'compare': {
    title: 'Compare Two Options',
    model: 'Auto Orchestration',
    description: 'Pick model automatically',
    explanation: 'The system uses both models to provide reasoned analysis and clear explanation side-by-side.',
    exampleContext: 'Example scenario: Your company needs to deploy AI inference infrastructure for running 70B parameter models. Option A: Build in-house using on-premise workstations (like ABS Workstations) - $150K upfront, full control, air-gapped security, but requires IT team management. Option B: Use cloud GPU services (AWS/Azure) - pay-as-you-go (~$5K/month), managed service, but data leaves premises and ongoing costs scale with usage. You need to decide which approach fits your enterprise needs, compliance requirements, and long-term strategy.',
    prompts: [
      { text: 'Compare Option A vs Option B', hint: 'Get a detailed comparison of two choices (e.g., in-house vs. cloud, vendor A vs. vendor B)' },
      { text: 'What are the pros and cons?', hint: 'List advantages and disadvantages for each option' },
      { text: 'Which is more cost-effective?', hint: 'Analyze financial implications (e.g., upfront costs, long-term savings)' },
      { text: 'Which has lower risk?', hint: 'Evaluate risk levels (e.g., technical risk, business risk, compliance risk)' },
      { text: 'Recommend the best choice', hint: 'Get a clear recommendation with reasoning based on your priorities' },
      { text: 'What\'s the trade-off?', hint: 'Understand what you gain and lose with each option (e.g., control vs. convenience)' }
    ]
  },
  'summarize': {
    title: 'Summarize a Doc Snippet',
    model: 'RAG-lite',
    description: 'Extract key points',
    explanation: 'Extract and organize key information from documents or text.',
    exampleContext: 'Example scenario: You have a 50-page vendor contract for AI infrastructure services. The document includes: pricing tiers, SLA commitments, data residency requirements, termination clauses, liability limitations, IP ownership terms, support levels, and compliance certifications. You need to quickly understand the key terms, risks, and obligations before a meeting with legal and procurement in 30 minutes.',
    prompts: [
      { text: 'Summarize the main points', hint: 'Get a concise overview of the content (e.g., contract terms, proposal highlights)' },
      { text: 'What are the key takeaways?', hint: 'Identify the most important insights (e.g., critical clauses, main benefits)' },
      { text: 'Extract action items', hint: 'Find tasks or next steps mentioned (e.g., deliverables, approvals needed)' },
      { text: 'What are the risks mentioned?', hint: 'Identify any risks or concerns (e.g., liability, compliance issues)' },
      { text: 'Who are the stakeholders?', hint: 'List people or groups involved (e.g., parties, departments, decision-makers)' },
      { text: 'What are the deadlines?', hint: 'Find time-sensitive information (e.g., milestones, expiration dates)' }
    ]
  }
}

const currentChallenge = computed(() => {
  if (!selectedChallenge.value) return null
  return challenges[selectedChallenge.value as keyof typeof challenges]
})

function selectChallenge(challengeId: string) {
  // Clear previous prompt selection when switching challenges
  selectedPromptIndex.value = null
  // Clear previous output when switching challenges
  if (demoControl.modelOutput) {
    demoControl.modelOutput = null
  }
  // Select new challenge
  selectedChallenge.value = challengeId
}

function selectPrompt(promptText: string, index: number) {
  if (!selectedChallenge.value || demoControl.isProcessing) return
  
  const challenge = challenges[selectedChallenge.value as keyof typeof challenges]
  
  // Mark this prompt as selected for visual feedback
  selectedPromptIndex.value = index
  
  // Record activity - resets idle timer
  demoControl.recordActivity()
  
  // If a model is already running, just send the prompt to it
  if (demoControl.isActive) {
    demoControl.setChallenge(selectedChallenge.value, promptText)
    return
  }
  
  // Otherwise, activate the appropriate model for this challenge
  demoControl.setChallenge(selectedChallenge.value, promptText)
  
  // Only activate model if not already active
  if (!demoControl.isActive) {
    if (selectedChallenge.value === 'reasoning') {
      demoControl.activateModel('deepseek-r1-70b')
    } else if (selectedChallenge.value === 'explanation') {
      demoControl.activateModel('llama3-70b')
    } else if (selectedChallenge.value === 'compare') {
      demoControl.activateModel('dual')
    } else {
      demoControl.activateModel('llama3-70b')
    }
  }
}

// Watch for when processing completes to reset selected prompt
watch(() => demoControl.isProcessing, (isProcessing) => {
  if (!isProcessing && demoControl.modelOutput) {
    // Keep the selected prompt highlighted briefly, then reset
    setTimeout(() => {
      selectedPromptIndex.value = null
    }, 1000)
  }
})

// Watch for model output and scroll to it when ready
watch(() => demoControl.modelOutput, async (newOutput) => {
  if (newOutput) {
    // Wait for DOM update, then scroll to output
    await nextTick()
    if (outputDisplayRef.value) {
      // Scroll within the kiosk container
      const kioskContainer = outputDisplayRef.value.closest('.prompt-kiosk')
      if (kioskContainer) {
        // Calculate position relative to container
        const containerRect = kioskContainer.getBoundingClientRect()
        const elementRect = outputDisplayRef.value.getBoundingClientRect()
        const scrollTop = kioskContainer.scrollTop + (elementRect.top - containerRect.top) - 20 // 20px offset
        
        kioskContainer.scrollTo({
          top: scrollTop,
          behavior: 'smooth'
        })
      } else {
        // Fallback to standard scrollIntoView
        outputDisplayRef.value.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        })
      }
    }
  }
}, { immediate: false })

function clearSelection() {
  // Clear challenge selection but keep model active and kiosk open
  selectedChallenge.value = null
  selectedPromptIndex.value = null
  // Clear previous output when going back
  if (demoControl.modelOutput) {
    demoControl.modelOutput = null
  }
  // Don't clear the session - keep model running so user can try another challenge
  // Keep kiosk open to show challenge selection again
}

function closeKiosk() {
  // Fully close kiosk and clear session
  selectedChallenge.value = null
  selectedPromptIndex.value = null
  showKiosk.value = false
  demoControl.clearSession()
}
</script>

<template>
  <Transition name="fade">
    <div v-if="showKiosk || selectedChallenge" class="prompt-kiosk">
      <div class="kiosk-header">
        <div class="kiosk-title">Try It</div>
        <div class="kiosk-actions">
          <button v-if="selectedChallenge" class="kiosk-back" @click="clearSelection" title="Back to challenge selection">← Back</button>
          <button class="kiosk-close" @click="closeKiosk" title="Close and deactivate model">×</button>
        </div>
      </div>
      
      <div v-if="!selectedChallenge" class="challenge-selection">
        <div v-if="demoControl.isActive" class="active-model-notice">
          <span class="notice-icon">●</span>
          <span>Using active model: <strong>{{ demoControl.activeModel === 'deepseek-r1-70b' ? 'DeepSeek R1 70B' : demoControl.activeModel === 'llama3-70b' ? 'LLaMA-3 70B' : 'Dual 70B' }}</strong></span>
        </div>
        <div class="challenge-grid">
          <button
            v-for="(challenge, id) in challenges"
            :key="id"
            class="challenge-button"
            @click="selectChallenge(id)"
          >
            <div class="challenge-title">{{ challenge.title }}</div>
            <div class="challenge-model">{{ challenge.model }}</div>
            <div class="challenge-desc">{{ challenge.description }}</div>
          </button>
        </div>
      </div>
      
      <div v-else class="prompt-selection">
        <div class="selected-challenge-header">
          <div class="selected-challenge-title">{{ currentChallenge?.title }}</div>
          <div class="selected-challenge-model">
            {{ demoControl.isActive ? `Using: ${demoControl.activeModel === 'deepseek-r1-70b' ? 'DeepSeek R1 70B' : demoControl.activeModel === 'llama3-70b' ? 'LLaMA-3 70B' : 'Dual 70B'}` : currentChallenge?.model }}
          </div>
          <div v-if="currentChallenge?.explanation" class="challenge-explanation">
            {{ currentChallenge.explanation }}
          </div>
          <div v-if="currentChallenge?.exampleContext" class="challenge-example">
            <span class="example-label">Example scenario:</span>
            <span class="example-text">{{ currentChallenge.exampleContext }}</span>
          </div>
        </div>
        
        <div class="prompt-section">
          <div class="prompt-section-label">Choose a prompt to try:</div>
          <div class="prompt-chips">
            <button
              v-for="(prompt, index) in currentChallenge?.prompts"
              :key="index"
              class="prompt-chip"
              :class="{ 
                'prompt-chip--selected': selectedPromptIndex === index,
                'prompt-chip--processing': selectedPromptIndex === index && demoControl.isProcessing,
                'prompt-chip--disabled': demoControl.isProcessing
              }"
              :title="typeof prompt === 'object' ? prompt.hint : ''"
              :disabled="demoControl.isProcessing"
              @click="selectPrompt(typeof prompt === 'object' ? prompt.text : prompt, index)"
            >
              <div class="prompt-chip-content">
                <div class="prompt-chip-text">{{ typeof prompt === 'object' ? prompt.text : prompt }}</div>
                <div v-if="typeof prompt === 'object' && prompt.hint" class="prompt-chip-hint">{{ prompt.hint }}</div>
              </div>
              <div v-if="selectedPromptIndex === index && demoControl.isProcessing" class="prompt-chip-loading">
                <div class="chip-spinner"></div>
                <span>Processing...</span>
              </div>
            </button>
          </div>
        </div>
        
        <!-- Processing Indicator -->
        <Transition name="fade">
          <div v-if="demoControl.isProcessing" class="processing-indicator">
            <div class="processing-spinner"></div>
            <div class="processing-content">
              <div class="processing-text">Model is working...</div>
              <div class="processing-subtext">Analyzing your prompt and generating response</div>
            </div>
            <div class="processing-progress-bar">
              <div class="processing-progress-fill"></div>
            </div>
          </div>
        </Transition>
        
        <!-- Model Output Display -->
        <div 
          v-if="demoControl.modelOutput" 
          ref="outputDisplayRef"
          class="model-output-display"
        >
          <div class="output-header">Model Response:</div>
          <div v-if="demoControl.modelOutput.reasoned" class="output-content">
            <div class="output-label">Reasoned Output:</div>
            <div class="output-text">{{ demoControl.modelOutput.reasoned }}</div>
          </div>
          <div v-if="demoControl.modelOutput.explained" class="output-content">
            <div class="output-label">Executive Explanation:</div>
            <div class="output-text">{{ demoControl.modelOutput.explained }}</div>
          </div>
        </div>
        
        <!-- Session Timer -->
        <div v-if="demoControl.timeRemaining !== null && demoControl.timeRemaining > 0" class="session-timer">
          <span class="timer-label">Interactive session ends in:</span>
          <span class="timer-countdown">{{ demoControl.timeRemaining }}s</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.prompt-kiosk {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--abs-orange);
  border-radius: 16px;
  box-shadow: 0 0 60px rgba(249, 115, 22, 0.4), 0 8px 40px rgba(0, 0, 0, 0.5);
  z-index: 200;
  backdrop-filter: blur(20px);
  overflow-y: auto;
}

.kiosk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.kiosk-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kiosk-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kiosk-back {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.kiosk-back:hover {
  background: var(--abs-elevated);
  border-color: var(--abs-orange);
  color: var(--abs-orange);
}

.kiosk-close {
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  transition: all 0.3s ease;
}

.kiosk-close:hover {
  background: var(--abs-elevated);
  border-color: var(--abs-orange);
  color: var(--abs-orange);
}

.active-model-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--abs-orange);
}

.notice-icon {
  color: var(--status-success);
  font-size: 0.75rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.challenge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.challenge-button {
  padding: 24px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.3s ease;
}

.challenge-button:hover {
  background: var(--abs-card);
  border-color: var(--abs-orange);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.2);
}

.challenge-title {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.challenge-model {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--abs-orange);
  font-weight: 600;
  margin-bottom: 4px;
}

.challenge-desc {
  font-family: var(--font-body);
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.prompt-selection {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selected-challenge-header {
  text-align: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.selected-challenge-title {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.selected-challenge-model {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--abs-orange);
  font-weight: 600;
  margin-bottom: 8px;
}

.challenge-explanation {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
  margin-top: 8px;
  padding: 12px;
  background: rgba(249, 115, 22, 0.05);
  border-left: 3px solid var(--abs-orange);
  border-radius: 4px;
  line-height: 1.5;
}

.challenge-example {
  margin-top: 12px;
  padding: 14px 16px;
  background: rgba(99, 102, 241, 0.1);
  border-left: 3px solid var(--electric-indigo);
  border-radius: 6px;
  font-family: var(--font-body);
  font-size: 0.85rem;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

.example-label {
  color: var(--electric-indigo);
  font-weight: 600;
  display: block;
  margin-bottom: 6px;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.example-text {
  color: var(--text-secondary);
  font-style: normal;
  display: block;
}

.prompt-section {
  margin-top: 24px;
}

.prompt-section-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.processing-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  margin: 24px 0;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(249, 115, 22, 0.05));
  border: 2px solid rgba(249, 115, 22, 0.4);
  border-radius: 12px;
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.2);
}

.processing-indicator > .processing-spinner {
  align-self: center;
}

.processing-indicator > .processing-content {
  align-self: center;
  text-align: center;
}

.processing-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(249, 115, 22, 0.3);
  border-top-color: var(--abs-orange);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.processing-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
}

.processing-text {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--abs-orange);
  font-weight: 700;
}

.processing-subtext {
  font-family: var(--font-body);
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.processing-progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  margin-top: 16px;
  overflow: hidden;
}

.processing-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  border-radius: 2px;
  animation: progress-animation 3s ease-in-out infinite;
  width: 100%;
}

@keyframes progress-animation {
  0% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(100%);
  }
}

.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.prompt-chip {
  padding: 14px 18px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 200px;
  position: relative;
}

.prompt-chip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prompt-chip-text {
  font-weight: 600;
  color: var(--text-primary);
}

.prompt-chip-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
  line-height: 1.4;
}

.prompt-chip:hover:not(:disabled):not(.prompt-chip--processing) {
  background: var(--abs-orange);
  border-color: var(--abs-orange);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.prompt-chip:hover:not(:disabled):not(.prompt-chip--processing) .prompt-chip-text {
  color: white;
}

.prompt-chip:hover:not(:disabled):not(.prompt-chip--processing) .prompt-chip-hint {
  color: rgba(255, 255, 255, 0.9);
}

.prompt-chip--selected {
  background: rgba(249, 115, 22, 0.15);
  border-color: var(--abs-orange);
  border-width: 2px;
}

.prompt-chip--processing {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(249, 115, 22, 0.1));
  border-color: var(--abs-orange);
  border-width: 2px;
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.3);
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(249, 115, 22, 0.3);
  }
  50% {
    box-shadow: 0 0 25px rgba(249, 115, 22, 0.5);
  }
}

.prompt-chip--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.prompt-chip-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(249, 115, 22, 0.3);
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--abs-orange);
  font-weight: 600;
}

.chip-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(249, 115, 22, 0.3);
  border-top-color: var(--abs-orange);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.model-output-display {
  margin-top: 20px;
  padding: 20px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}

.output-header {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.output-content {
  margin-bottom: 16px;
}

.output-content:last-child {
  margin-bottom: 0;
}

.output-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--abs-orange);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.output-text {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.session-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  font-family: var(--font-label);
  font-size: 0.8rem;
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
  margin-top: 20px;
}

.timer-label {
  color: var(--text-muted);
  font-weight: 400;
}

.timer-countdown {
  font-family: var(--font-mono);
  color: var(--abs-orange);
  font-weight: 600;
  font-size: 0.9rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.95);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}
</style>

