/**
 * useCESRestrictions.ts
 * 
 * Provides utilities for disabling dangerous operations in CES mode.
 * CES mode should allow viewing admin pages but prevent destructive actions.
 */

import { computed } from 'vue'
import { useCESMode } from './useCESMode'

export interface OperationRestriction {
  disabled: boolean
  tooltip: string | null
  reason: string | null
}

/**
 * List of dangerous operations that should be disabled in CES mode
 */
export const DANGEROUS_OPERATIONS = {
  // Service lifecycle
  START_SERVICE: 'start-service',
  STOP_SERVICE: 'stop-service',
  RESTART_SERVICE: 'restart-service',
  SUSPEND_SERVICE: 'suspend-service',
  
  // Model operations
  DELETE_MODEL: 'delete-model',
  UNLOAD_MODEL: 'unload-model',
  
  // Asset operations
  DELETE_ASSET: 'delete-asset',
  EDIT_ASSET: 'edit-asset',
  UPDATE_POLICY: 'update-policy',
  
  // System operations
  CLEAR_CACHE: 'clear-cache',
  RESTORE_SNAPSHOT: 'restore-snapshot',
  EXPORT_CONFIG: 'export-config',
  IMPORT_CONFIG: 'import-config',
  
  // Configuration
  SAVE_CONFIG: 'save-config',
  RESET_CONFIG: 'reset-config'
} as const

export function useCESRestrictions() {
  const { isCESMode } = useCESMode()

  /**
   * Check if an operation is allowed (not disabled by CES mode)
   */
  const isOperationAllowed = (operation: string): boolean => {
    if (!isCESMode.value) return true // All operations allowed in non-CES mode
    
    // Check if operation is in dangerous list
    return !Object.values(DANGEROUS_OPERATIONS).includes(operation as any)
  }

  /**
   * Get restriction details for an operation
   */
  const getOperationRestriction = (operation: string): OperationRestriction => {
    const disabled = !isOperationAllowed(operation)
    
    if (!disabled) {
      return {
        disabled: false,
        tooltip: null,
        reason: null
      }
    }

    return {
      disabled: true,
      tooltip: 'This operation is disabled in CES demo mode',
      reason: 'CES mode is active. Admin operations are read-only for demo safety.'
    }
  }

  /**
   * CES mode banner message
   */
  const cesBannerMessage = computed(() => {
    if (!isCESMode.value) return null
    return 'CES Demo Mode: Admin operations are read-only. Viewing and monitoring enabled; destructive actions disabled for demo safety.'
  })

  /**
   * Check if editing is allowed
   */
  const canEdit = computed(() => !isCESMode.value)

  /**
   * Check if deletion is allowed
   */
  const canDelete = computed(() => !isCESMode.value)

  /**
   * Check if service control is allowed
   */
  const canControlServices = computed(() => !isCESMode.value)

  return {
    isCESMode,
    isOperationAllowed,
    getOperationRestriction,
    cesBannerMessage,
    canEdit,
    canDelete,
    canControlServices,
    DANGEROUS_OPERATIONS
  }
}

