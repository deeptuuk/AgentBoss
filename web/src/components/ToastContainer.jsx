export function ToastContainer({ toasts, onDismiss }) {
  if (!toasts.length) return null;

  return (
    <div class="toast-container" role="region" aria-label="Notifications">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          class={`toast ${toast.type === 'error' ? 'toast-error' : 'toast-success'}`}
          onClick={() => toast.type === 'error' && onDismiss(toast.id)}
        >
          <span>{toast.message}</span>
          {toast.type === 'error' && (
            <button class="toast-close-btn" onClick={() => onDismiss(toast.id)}>×</button>
          )}
        </div>
      ))}
    </div>
  );
}
