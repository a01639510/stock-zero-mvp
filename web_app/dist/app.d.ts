import { AppState, TabType } from './types';
declare function initializeApp(): void;
declare function switchTab(tabName: TabType): void;
declare function showError(message: string): void;
declare function showSuccess(message: string): void;
declare global {
    interface Window {
        appState: AppState;
        initializeApp: typeof initializeApp;
        switchTab: typeof switchTab;
        showError: typeof showError;
        showSuccess: typeof showSuccess;
    }
}
export {};
//# sourceMappingURL=app.d.ts.map