import React from 'react';
import { Navigate } from 'react-router-dom';
import { type User, type Role } from '../types/types';
import { getStoredUser } from '../api';

interface RouteGuardProps {
  children: React.ReactNode;
  allowedRole?: Role;
}

export const RouteGuard = ({ children, allowedRole }: RouteGuardProps) => {
  const userData = getStoredUser();

  if (!userData) {
    alert('Please login first!');
    return (
      <>
        <Navigate to="/" replace />
      </>
    );
  }

  const user: User = userData;

  if (allowedRole && user.role !== allowedRole) {
    alert(`Permission denied! This page is only accessible to ${allowedRole}.`);
    localStorage.removeItem('user');
    return (
      <>
        <Navigate to="/" replace />
      </>
    );
  }

  return <>{children}</>;
};
