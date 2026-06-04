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
  // 保持 globalThis 修正
  globalThis.dispatchEvent(
    new CustomEvent(notificationEventName, {
      detail: { message, tone }
    })
  );
};

export const NotificationCenter = () => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  // 抽出過濾陣列的邏輯，最深層級只到第 4 層
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

      // 保持 globalThis 修正，並呼叫獨立函式
      globalThis.setTimeout(() => {
        removeNotification(id);
      }, 3600);
    };

    // 保持 globalThis 修正
    globalThis.addEventListener(notificationEventName, handleNotification);
    return () => globalThis.removeEventListener(notificationEventName, handleNotification);
  }, [removeNotification]); // 將 removeNotification 加入 dependencies

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
            // 共用精簡的函式
            onClick={() => removeNotification(notification.id)}
          >
            x
          </button>
        </div>
      ))}
    </div>
  );
};