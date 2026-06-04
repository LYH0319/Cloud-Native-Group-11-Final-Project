import React, { useEffect } from 'react';
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

  useEffect(() => {
    // 將所有副作用（發通知、清 LocalStorage）集中在 useEffect 處理
    if (!userData) {
      showNotification('Please login first!', 'error');
    } else if (permissionDenied) {
      localStorage.removeItem('user');
      showNotification(
        `Permission denied! This page is only accessible to ${allowedRole}.`,
        'error'
      );
    }
  }, [userData, allowedRole, permissionDenied]);

  // 如果未登入或權限不足，統一攔截並跳轉回首頁
  if (!userData || permissionDenied) {
    return <Navigate to="/" replace />;
  }

  // 檢查全數通過，正常渲染子元件
  return <>{children}</>;
};
