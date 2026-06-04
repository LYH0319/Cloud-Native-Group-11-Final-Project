import React from 'react';
import { Navigate } from 'react-router-dom';
import { type Role } from '../types/types';
import { getStoredUser } from '../api';
import { showNotification } from './NotificationCenter';

interface RouteGuardProps {
  children: React.ReactNode;
  allowedRole?: Role;
}

export const RouteGuard = ({ children, allowedRole }: RouteGuardProps) => {
  const userData = getStoredUser();
  const permissionDenied = Boolean(userData && allowedRole && userData.role !== allowedRole);
  const notificationMessage = !userData
    ? 'Please login first!'
    : permissionDenied
      ? `Permission denied! This page is only accessible to ${allowedRole}.`
      : '';

  React.useEffect(() => {
    if (notificationMessage) {
      showNotification(notificationMessage, 'error');
    }
  }, [notificationMessage]);

  if (!userData) {
    return (
      <>
        <Navigate to="/" replace />
      </>
    );
  }

  if (permissionDenied) {
    localStorage.removeItem('user');
    return (
      <>
        <Navigate to="/" replace />
      </>
    );
  }

  return <>{children}</>;
};
