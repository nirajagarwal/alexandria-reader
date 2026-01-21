/* =============================================================================
   Alexandria Press - State Module
   ============================================================================= */

export const state = {
    currentBook: null,
    currentEntries: [],
    currentEntry: null,
    isMenuOpen: false
};

export const cache = {
    books: {}
};

/**
 * Reset navigation state (keep cache)
 */
export function resetNavState() {
    state.currentBook = null;
    state.currentEntries = [];
    state.currentEntry = null;
    state.isMenuOpen = false;
}
