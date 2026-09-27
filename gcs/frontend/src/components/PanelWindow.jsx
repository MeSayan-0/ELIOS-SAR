export default function PanelWindow({
  id,
  title,
  children,
  onClose,
  isFullscreen = false,
  onToggleFullscreen,
}) {
  return (
    <div
      className={`panel-window ${
        isFullscreen ? "panel-window-fullscreen" : ""
      }`}
    >
      <div className="panel-window-header">
        <div className="panel-window-drag panel-drag-handle">
          <span className="panel-window-grip" title="Drag panel">⋮⋮</span>
          <span className="panel-window-title">{title}</span>
        </div>

        <div className="panel-window-actions">
          {onToggleFullscreen && (
            <button
              type="button"
              className="panel-action-btn panel-action-maximize"
              onClick={() => onToggleFullscreen(id)}
              aria-label={
                isFullscreen ? `Restore ${title}` : `Maximize ${title}`
              }
              title={isFullscreen ? "Restore panel" : "Maximize panel"}
            >
              {isFullscreen ? "❐" : "□"}
            </button>
          )}

          {onClose && (
            <button
              type="button"
              className="panel-action-btn panel-action-close"
              onClick={() => onClose(id)}
              aria-label={`Close ${title}`}
              title="Close panel"
            >
              ×
            </button>
          )}
        </div>
      </div>

      <div className="panel-window-content">{children}</div>
    </div>
  );
}
