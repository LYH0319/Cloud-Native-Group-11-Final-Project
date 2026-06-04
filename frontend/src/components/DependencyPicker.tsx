import { useEffect, useState, useCallback } from 'react';
import './NotificationCenter.css';

export type NotificationTone = 'success' | 'info' | 'error';

interface AppNotification {
  id: number;
  message: string;
  tone: NotificationTone;
}

const notificationEventName = 'app-notification';

export const showNotification = (message: string, tone: NotificationTone = 'info') => {
  // 1. 替換 window 為 globalThis
  globalThis.dispatchEvent(
    new CustomEvent(notificationEventName, {
      detail: { message, tone }
    })
  );
};

export const NotificationCenter = () => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  const removeNotification = useCallback((idToRemove: number) => {
    setNotifications((current) => current.filter((item) => item.id !== idToRemove));
  }, []);

  useEffect(() => {
    const handleNotification = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string; tone?: NotificationTone }>).detail;
      if (!detail?.message) return;

      const id = Date.now();
      setNotifications((current) => [
        ...current,
        { id, message: detail.message || '', tone: detail.tone || 'info' }
      ]);

      // 2. 替換 window 為 globalThis
      globalThis.setTimeout(() => {
        removeNotification(id);
      }, 3600);
    };

    // 3 & 4. 替換 window 為 globalThis
    globalThis.addEventListener(notificationEventName, handleNotification);
    return () => globalThis.removeEventListener(notificationEventName, handleNotification);
  }, [removeNotification]); 

  if (notifications.length === 0) return null;

  return (
    <div className="notification-center" aria-live="polite" aria-atomic="true">
      {notifications.map((notification) => (
        <div
          className={`notification-toast notification-toast-${notification.tone}`}
          key={notification.id}
        >
          <span className="notification-dot" />
          <span>{notification.message}</span>
          <button
            type="button"
            className="notification-close"
            aria-label="Close notification"
            onClick={() => removeNotification(notification.id)}
          >
            x
          </button>
        </div>
      ))}
    </div>
  );
};