import React from 'react';
import { Navigate } from 'react-router-dom';
import { type User, type Role } from '../types/types';

interface RouteGuardProps {
  children: React.ReactNode;
  allowedRole?: Role;
}

export const RouteGuard = ({ children, allowedRole } : RouteGuardProps) => {
  const userData = localStorage.getItem('user');
  
  if (!userData) {
    alert('Please login first!');
    return <><Navigate to="/login" replace /></>;
  }

  const user: User = JSON.parse(userData);

  if (allowedRole && user.role !== allowedRole) {
    alert(`Permission denied! This page is only accessible to ${allowedRole}.`);
    return <><Navigate to="/" replace /></>;
  }

  return <>{children}</>;
};