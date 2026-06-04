import { useEffect, useState } from 'react';
import './NotificationCenter.css';

export type NotificationTone = 'success' | 'info' | 'error';

interface AppNotification {
  id: number;
  message: string;
  tone: NotificationTone;
}

const notificationEventName = 'app-notification';

export const showNotification = (message: string, tone: NotificationTone = 'info') => {
  window.dispatchEvent(
    new CustomEvent(notificationEventName, {
      detail: { message, tone }
    })
  );
};

export const NotificationCenter = () => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  useEffect(() => {
    const handleNotification = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string; tone?: NotificationTone }>).detail;
      if (!detail?.message) return;

      const id = Date.now();
      setNotifications((current) => [
        ...current,
        { id, message: detail.message || '', tone: detail.tone || 'info' }
      ]);

      window.setTimeout(() => {
        setNotifications((current) => current.filter((item) => item.id !== id));
      }, 3600);
    };

    window.addEventListener(notificationEventName, handleNotification);
    return () => window.removeEventListener(notificationEventName, handleNotification);
  }, []);

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
            onClick={() =>
              setNotifications((current) => current.filter((item) => item.id !== notification.id))
            }
          >
            x
          </button>
        </div>
      ))}
    </div>
  );
};
