<template>
  <div class="contact-info">
    <h3 class="contact-info__title">Get in Touch</h3>
    
    <div class="contact-info__items">
      <div class="contact-info__item">
        <div class="contact-info__icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
        </div>
        <div class="contact-info__content">
          <div class="contact-info__label">Email</div>
          <a href="mailto:architectteam@newegg.com" class="contact-info__value contact-info__value--link">
            architectteam@newegg.com
          </a>
        </div>
      </div>

      <div class="contact-info__item">
        <div class="contact-info__icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
        </div>
        <div class="contact-info__content">
          <div class="contact-info__label">Phone</div>
          <a href="tel:+18003822088" class="contact-info__value contact-info__value--link">
            (800) 382-2088
          </a>
        </div>
      </div>

      <div class="contact-info__item">
        <div class="contact-info__icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
        </div>
        <div class="contact-info__content">
          <div class="contact-info__label">Location</div>
          <div class="contact-info__value">
            21688 Gateway Center Dr #300<br>
            Diamond Bar, CA 91765
          </div>
          <div class="contact-info__note">Built and supported locally</div>
        </div>
      </div>
    </div>

    <div class="contact-info__actions">
      <a 
        href="https://absworkstation.com/contact?utm_source=console&utm_campaign=offline" 
        class="contact-info__button contact-info__button--primary"
        target="_blank"
        rel="noopener noreferrer"
      >
        View on Newegg
      </a>
      <a 
        href="https://absworkstation.com/contact?utm_source=console&utm_campaign=offline" 
        class="contact-info__button contact-info__button--secondary"
        target="_blank"
        rel="noopener noreferrer"
      >
        Get Quote
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
// No props needed - this is a static contact info component
</script>

<style scoped>
.contact-info {
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  max-width: 500px;
  margin: 0 auto;
}

.contact-info__title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px;
  text-align: center;
}

.contact-info__items {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.contact-info__item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.contact-info__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.1);
  border-radius: 8px;
}

.contact-info__content {
  flex: 1;
  min-width: 0;
}

.contact-info__label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}

.contact-info__value {
  font-size: 0.9375rem;
  color: var(--text-primary);
  line-height: 1.5;
}

.contact-info__value--link {
  color: var(--electric-indigo);
  text-decoration: none;
  transition: color 0.2s;
}

.contact-info__value--link:hover {
  color: var(--electric-indigo-hover);
  text-decoration: underline;
}

.contact-info__note {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 4px;
  font-style: italic;
}

.contact-info__actions {
  display: flex;
  gap: 12px;
}

.contact-info__button {
  flex: 1;
  padding: 12px 20px;
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-block;
}

.contact-info__button--primary {
  background: var(--electric-indigo);
  color: white;
  border: none;
}

.contact-info__button--primary:hover {
  background: var(--electric-indigo-hover);
  transform: translateY(-1px);
}

.contact-info__button--secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.contact-info__button--secondary:hover {
  border-color: var(--electric-indigo);
  color: var(--electric-indigo);
}

/* Compact variant for inline use */
.contact-info--compact {
  padding: 24px;
  max-width: 100%;
}

.contact-info--compact .contact-info__title {
  font-size: 1.25rem;
  margin-bottom: 20px;
}

.contact-info--compact .contact-info__items {
  gap: 20px;
  margin-bottom: 24px;
}

.contact-info--compact .contact-info__icon {
  width: 32px;
  height: 32px;
}

.contact-info--compact .contact-info__label {
  font-size: 0.7rem;
}

.contact-info--compact .contact-info__value {
  font-size: 0.875rem;
}
</style>

